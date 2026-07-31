#!/usr/bin/env bash
# Consolidated local validation — substitute for GitHub Actions during known
# Actions-minutes outages (see CLAUDE.md "GitHub-Actions-CI —
# bekannte Usage-Limit-Bedingung"). Runs every CI-equivalent check that is
# runnable on Linux/macOS in one pass, reporting all results instead of
# stopping at the first failure — mirrors how independent CI jobs each
# report separately, so one red check doesn't hide the others.
#
# Known gap: the Windows-only Stage-1/Fabric quality-gate PowerShell scripts
# (tooling/run_stage1_checks.ps1, tooling/quality/run_quality_gate.ps1)
# cannot run here. During an Actions outage these need either a Windows
# environment or manual maintainer verification before merge.
#
# Known local-only caveat: the Playwright e2e check needs an installed
# Chromium build matching the pinned @playwright/test version. If your local
# browser cache is stale (error: "Executable doesn't exist at
# .../chromium_headless_shell-<version>"), run `npx playwright install
# chromium` inside studio/ once. Real CI always installs a matching browser
# (`npx playwright install --with-deps chromium`), so this only affects
# local runs with a pre-existing, out-of-date browser cache.
#
# Usage: bash tooling/run_local_ci_check.sh   (run from repo root)

set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PASS=0
FAIL=0
FAILED_NAMES=()

run_check() {
  local name="$1"
  shift
  echo ""
  echo "==> ${name}"
  if "$@"; then
    echo "--- PASS: ${name}"
    PASS=$((PASS + 1))
  else
    echo "--- FAIL: ${name}"
    FAIL=$((FAIL + 1))
    FAILED_NAMES+=("${name}")
  fi
}

# --- Workflow-Validitaet ------------------------------------------------
# ZUERST, und zwar aus einem gemessenen Grund: eine ungueltige Workflow-Datei erzeugt bei
# GitHub NULL Jobs und meldet `conclusion=failure` — exakt wie ein Runner-Ausfall. Solange
# ein Usage-Limit-Fenster offen ist, gilt jeder rote Lauf als erklaert, und ein echter Defekt
# versteckt sich dahinter. Am 31.07.2026 war genau das der Fall (source-updates.yml, 30 rote
# Laeufe seit dem 29.07.). Diese Frage beantwortet man lokal in Sekunden.
run_check "Workflow-Dateien (check_workflows.py)" \
  python3 scripts/check_workflows.py

# --- Drift gate -------------------------------------------------------
run_check "Drift gate (check_index.py --strict)" \
  python3 scripts/check_index.py --strict

# --- Meridian mirror ----------------------------------------------------
# Not --strict: the vendored subtree's local integrity is checked unconditionally (a hand
# edit exits 1 either way), while the cross-repo diff is advisory and soft-skips without a
# Meridian checkout — this script must stay runnable on its own.
run_check "Meridian mirror (check_dataarch_mirror.py)" \
  python3 scripts/check_dataarch_mirror.py

# --- Python test suite --------------------------------------------------
run_check "Pytest suite (tooling/superversion, tooling/tests, products)" \
  python3 -m pytest tooling/superversion tooling/tests products -q

# --- Fabric bindings validator ------------------------------------------
run_check "Fabric bindings validator (validate_bindings.py --strict)" \
  python3 products/fabric/powerbi/tooling/validate_bindings.py \
    --dist-dir products/fabric/powerbi/dist --strict

# --- Showcase Delta-table consistency -----------------------------------
# Catches renamed/orphaned parquet vs. _delta_log active-add mismatch that
# makes fn_DeltaCurrentFiles return a columnless table (Desktop then crashes
# in Table.get_Islands()). See scripts/check_showcase_delta.py.
run_check "Showcase Delta-table consistency (active files present on disk)" \
  python3 scripts/check_showcase_delta.py

# --- Data-model best practices (Kimball hygiene, blocking) ---------------
# Contract + gold: no missing grain, no dangling ref, no non-conformed dimension,
# referential integrity holds. Catches the modelling-defect classes (multi-grain,
# degenerate key, non-conformed dim) that structural contract validation misses.
run_check "Data-model best-practice gate (check_data_model.py)" \
  python3 tooling/validation/check_data_model.py

# --- Boutique rubric: BC-NARR-01 exhibit titles (K6) --------------------
run_check "Boutique rubric BC-NARR-01 (exhibit titles are statements, not labels)" \
  python3 tooling/validation/check_exhibit_message.py

# --- Boutique rubric: BC-CHART-01 mixed-scale (K6) ----------------------
run_check "Boutique rubric BC-CHART-01 (no mixed scale on one axis)" \
  python3 tooling/validation/check_mixed_scale.py

# --- Boutique rubric: BC-NARR-04 KPI context (K6, advisory) -------------
# Advisory scorecard signal (2/17 hero cards carry governed context); clearing the
# rest is a curated rollout (KONZEPT §12). Coverage regression-guarded in pytest.
run_check "Boutique rubric BC-NARR-04 (hero KPI has context — advisory)" \
  python3 tooling/validation/check_kpi_context.py

# --- KPI ↔ external-standard alignment integrity (standards program) ----
# Every governed KPI carries a standard_ref (SCOR/IFRS/ISO 22400/ISO 20000/IFRS 15…)
# with alignment + drift note; audits under core/kpi_catalog/standards/. Hard gate on
# structural integrity (well-formed entries, controlled standard vocabulary); the
# duplicate/consolidation sensor is advisory + regression-guarded in pytest.
run_check "KPI↔standard alignment integrity (standard_ref, --strict structural)" \
  python3 tooling/validation/check_standard_ref.py --strict

# --- Use-case narrative & standards-grounding quality (base for reports) -
# Use cases are the source the report/story generators read, so their quality caps the
# deliverable's. Hard gate: every page states a decision_question, every 30s message is a
# conclusion (not a chart label), every factsheet is standards-grounded on its strategic KPI.
run_check "Use-case narrative & standards-grounding quality (--strict)" \
  python3 tooling/validation/check_usecase_quality.py --strict

# --- Use-case storyline structure (deriver base for reports/stories) -----
# The storyline (derive_storyline.py) is what the report/story generators render. Hard gate:
# every page has a decision spine, every 30s visual answers a stated `question`, page-1→page-2
# handoff holds, and the generated docs/architecture/use_case_storylines.md stays in sync.
run_check "Use-case storyline structure + storyboard in sync (--strict)" \
  python3 tooling/validation/check_storyline.py --strict

# --- Boutique rubric: BC-CHART-10 evidence sort (K6, blocking) ----------
# Knock-out rule, fully rolled out (2026-07-11): all 17 evidence tables declare a
# governed worst-first sort + explicit Top-N. Hard gate (--strict) — 0 violations
# enforced. Coverage regression-guarded in pytest (covered ≥ 17).
# BC-CHART-10 re-layered onto R2.1 sort_by/top_n (loving-einstein merge 2026-07-16).
run_check "Boutique rubric BC-CHART-10 (evidence table worst-first + Top-N)" \
  python3 tooling/validation/check_evidence_sort.py --strict

# --- Content-Grounding §6.3: benchmark provenance (K4, blocking) ---------
# Every benchmark ("what good looks like") must reference a real KPI (Golden Thread)
# and cite a dated public source via a governed source_type — no fabricated industry
# numbers. Registry is small + fully grounded, so run hard (--strict).
run_check "Content-Grounding §6.3 (benchmarks grounded + provenance)" \
  python3 tooling/validation/check_benchmarks.py --strict

# --- Boutique rubric: BC-BRAND-01 custom theme (K6, blocking) -----------
# Knock-out: every report must register a composed custom theme, never the renderer
# default. All 17 dist reports pass, so run hard (--strict).
run_check "Boutique rubric BC-BRAND-01 (composed custom theme, never default)" \
  python3 tooling/validation/check_custom_theme.py --strict

# --- Boutique rubric: BC-CHART-08 forbidden chart types (K6, blocking) --
# Reuses the existing ForbiddenVisualTypes invariant: no pie/donut/gauge/treemap in
# any dist report. All 17 clean, so run hard (--strict).
run_check "Boutique rubric BC-CHART-08 (no forbidden chart types)" \
  python3 tooling/validation/check_forbidden_charts.py --strict

# --- Boutique-Craft Scorecard (K6 §9, advisory report) ------------------
# Aggregates the wired structural rules into the rubric's weighted score + knock-out
# status, and reports honest coverage (judge rules pending). Advisory — the artifact
# is the value; --strict would block on a scored knock-out failure.
run_check "Boutique-Craft Scorecard (K6 §9 — rubric rollup, advisory)" \
  python3 tooling/report_quality/boutique_scorecard.py

# --- PBI quality tools CLI ----------------------------------------------
run_check "PBI quality-tools CLI (validate --summary)" \
  python3 -c "
import sys
sys.path.insert(0, 'packages/pbi_quality_tools')
from pbi_quality_tools.cli import main
raise SystemExit(main(['validate', '--summary']))
"

# --- Health scorecard -----------------------------------------------------
run_check "Health scorecard (H1-H9)" \
  python3 tooling/health_scorecard.py

# --- Studio: typecheck, unit, e2e ----------------------------------------
if [ -d studio ]; then
  run_check "Studio typecheck (tsc --noEmit)" \
    bash -c "cd studio && npx tsc --noEmit -p tsconfig.json"

  run_check "Studio unit tests (vitest)" \
    bash -c "cd studio && npm test"

  run_check "Studio Playwright e2e (playwright.ci.config.ts)" \
    bash -c "cd studio && [ -f .env.local ] || echo 'AUTH_SECRET=ci-only-not-a-real-secret' > .env.local; npx playwright test --config=playwright.ci.config.ts"
else
  echo ""
  echo "==> Studio checks skipped (studio/ not found)"
fi

# --- Summary --------------------------------------------------------------
echo ""
echo "========================================"
echo "Local CI summary: ${PASS} passed, ${FAIL} failed"
if [ "${FAIL}" -gt 0 ]; then
  echo "Failed checks:"
  for n in "${FAILED_NAMES[@]}"; do
    echo "  - ${n}"
  done
fi
echo ""
echo "NOT covered by this script (Windows-only, verify manually or on Windows):"
echo "  - tooling/run_stage1_checks.ps1"
echo "  - tooling/quality/run_quality_gate.ps1"
echo "========================================"

if [ "${FAIL}" -gt 0 ]; then
  exit 1
fi
exit 0
