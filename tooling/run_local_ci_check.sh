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

# --- Drift gate -------------------------------------------------------
run_check "Drift gate (check_index.py --strict)" \
  python3 scripts/check_index.py --strict

# --- Python test suite --------------------------------------------------
run_check "Pytest suite (tooling/superversion, tooling/tests, products)" \
  python3 -m pytest tooling/superversion tooling/tests products -q

# --- Fabric bindings validator ------------------------------------------
run_check "Fabric bindings validator (validate_bindings.py --strict)" \
  python3 products/fabric/powerbi/tooling/validate_bindings.py \
    --dist-dir products/fabric/powerbi/dist --strict

# --- Boutique rubric: BC-NARR-01 exhibit titles (K6) --------------------
run_check "Boutique rubric BC-NARR-01 (exhibit titles are statements, not labels)" \
  python3 tooling/validation/check_exhibit_message.py

# --- Boutique rubric: BC-CHART-01 mixed-scale (K6) ----------------------
# Advisory: 8 pre-existing mixed-scale exhibits are a documented backlog (KONZEPT §12).
# NEW violations are blocked by the pytest regression guard (test_mixed_scale.py).
run_check "Boutique rubric BC-CHART-01 (mixed-scale — advisory, 8 known backlog)" \
  python3 tooling/validation/check_mixed_scale.py --exit-zero

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
