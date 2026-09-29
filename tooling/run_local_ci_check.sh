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

# --- Semantic Model gegen Gold-Daten (Ledger A-24, blocking) -------------
# Jede sourceColumn der dist-Modelle steht in der Gold-Tabelle, die ihre Partition
# liest, oder in tooling/validation/model_vs_gold_allowlist.yaml. Exit 2 = Gold fehlt
# ("nicht geprueft"), nie gruen.
run_check "Semantic Model gegen Gold-Daten (check_model_vs_gold.py --strict)" \
  python3 tooling/validation/check_model_vs_gold.py --strict

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

# --- Superversion-Gates (die vier, die der CI-Job NACH dem pytest faehrt) -----
# Der pytest-Lauf oben deckt `tooling/superversion/` ab — der CI-Job faehrt danach aber noch
# vier eigenstaendige Gates. Sie fehlten hier, also war „lokal gruen" fuer diesen Job
# unvollstaendig. Gemessen am 31.07.2026 beim Handdurchlauf der CI-Jobs.
run_check "Superversion pins (check_superversion_pins.py)" \
  python3 scripts/check_superversion_pins.py

run_check "Superversion Golden Thread" \
  python3 -m tooling.superversion.golden_thread

run_check "Superversion value gate (COM-001)" \
  python3 -m tooling.superversion.eval.value_gate COM-001

run_check "Superversion comp gate" \
  python3 -m tooling.superversion.eval.comp_gate

# --- Linux-Generierung (pwsh) — der Job, der hier bisher komplett fehlte -------
# `linux-generation.yml` baut die Ontologie-Registry, das IR und generiert daraus die
# TMDL-Measures ueber PowerShell. Ohne pwsh im PATH wird sauber uebersprungen (mit Grund),
# statt so zu tun, als sei der Job geprueft. Mit pwsh laufen dieselben vier Assertions wie
# im CI — inklusive der wichtigsten: die Generierung darf `dist/` nicht anfassen.
if command -v pwsh >/dev/null 2>&1; then
  run_check "Ontologie-Registry (registry_builder.py)" \
    python3 tooling/ontology/registry_builder.py

  run_check "IR-Build mit Measure-Overlay (build_ir.py)" \
    python3 tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog \
      --fabric-overlay products/fabric/powerbi/specs/fabric_measure_overlay.yaml \
      --out ir_v1.json

  run_check "TMDL-Measure-Generierung auf Linux (pwsh) + Assertions" \
    bash -c '
      set -e
      rm -rf scratch_gen && mkdir -p scratch_gen
      pwsh -c "./tooling/generator/generate_tmdl_measures.ps1 -IRPath ir_v1.json \
        -UseCase COM-001,COM-002,COM-003,COM-004 -TargetTablesDir scratch_gen -OverwriteExisting"
      test -s scratch_gen/_Measures.tmdl
      grep -q "measure '"'"'Gross Margin %'"'"' = DIVIDE" scratch_gen/_Measures.tmdl
      grep -q "measure '"'"'Net Sales Amount'"'"' = SUM" scratch_gen/_Measures.tmdl
      git diff --quiet -- products/fabric/powerbi/dist
      rm -rf scratch_gen ir_v1.json'
else
  echo ""
  echo "==> Linux-Generierung uebersprungen — pwsh nicht im PATH."
  echo "    Installation: https://learn.microsoft.com/powershell/scripting/install/install-ubuntu"
  echo "    (der CI-Job laeuft auf ubuntu-latest mit vorinstalliertem pwsh)"
fi

# --- Stage 1 (pwsh) — bisher als „Windows-only" gefuehrt ----------------------
# Das war eine Annahme, kein Befund. Am 01.08.2026 gemessen: `pwsh` 7.4.6 faehrt
# `tooling/run_stage1_checks.ps1` unter Linux komplett durch (20 Checks, rc=0), Pfade
# inklusive. Damit ist der einzige CI-Job geschlossen, der hier nie lief — und genau in ihm
# steckten die fuenf Schema-Verstoesse, die im PR-Lauf rot wurden.
#
# Zwei Vorbedingungen, beide gemessen und beide still, wenn man sie uebersieht:
#   * `check_schema_validation.ps1` ist ein NODE-Validator. Ohne `npm ci` in
#     tooling/validation macht er einen Soft-Skip mit rc=0 — er meldet Erfolg, ohne geprueft
#     zu haben. Deshalb wird hier vorher geprueft, ob er ueberhaupt pruefen KANN.
#   * `check_validate_data_contracts.ps1` braucht das Modul `powershell-yaml`; fehlt es, sagt
#     das Skript selbst „SKIPPED, not passed". Sein Python-Delegat deckt dieselbe Logik ab und
#     laeuft deshalb unten separat.
if command -v pwsh >/dev/null 2>&1; then
  if [ ! -x tooling/validation/node_modules/.bin/markdownlint-cli2 ]; then
    echo ""
    echo "==> HINWEIS: tooling/validation/node_modules fehlt — der Schema- und der"
    echo "    Markdownlint-Check machen dann einen Soft-Skip MIT rc=0 (melden also Erfolg,"
    echo "    ohne zu pruefen). Einmalig schliessen mit: npm ci --prefix tooling/validation"
  fi
  run_check "Stage 1 komplett (run_stage1_checks.ps1 unter pwsh)" \
    pwsh -NoProfile -File tooling/run_stage1_checks.ps1

  run_check "Data contracts (Python-Delegat von check_validate_data_contracts.ps1)" \
    python3 tooling/validation/check_validate_data_contracts.py --root .
else
  echo ""
  echo "==> Stage 1 uebersprungen — pwsh nicht im PATH (NICHT geprueft, nicht bestanden)."
  echo "    Installation: https://learn.microsoft.com/powershell/scripting/install/install-ubuntu"
fi

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
echo "NOT covered by this script — pruefen, nicht annehmen:"
echo "  - tooling/quality/run_quality_gate.ps1 (Fabric-Validierung; braucht Fabric-Zugang)"
echo "  - Studio-Visual-Regression (Baselines auf Windows aufgenommen, -win32-Dateinamen)"
echo "  - Playwright e2e schlaegt fehl, wenn der Chromium-Build des Containers vom Pin des"
echo "    Projekts abweicht ('Executable doesn't exist at .../chromium_headless_shell-<n>')."
echo "    Das ist eine Umgebungs-, keine Code-Aussage — nicht als roten Test verbuchen."
echo "  - tooling/run_stage1_checks.ps1 laeuft oben MIT, sofern pwsh im PATH ist."
echo "========================================"

if [ "${FAIL}" -gt 0 ]; then
  exit 1
fi
exit 0
