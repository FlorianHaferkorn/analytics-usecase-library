"""
OSS stack validation runner — mirrors products/fabric/powerbi/tooling/run_fabric_checks.ps1.

Runs all OSS-specific checks and writes a telemetry entry.

Usage (from repo root):
    python products/oss/tooling/run_oss_checks.py
    python products/oss/tooling/run_oss_checks.py --bracket core/usecases/core/COM-001/UseCase_Bracket.yaml
    python products/oss/tooling/run_oss_checks.py --json

Exit codes:
    0 — all checks passed
    1 — one or more checks failed

Status: STUB — add OSS-specific output validation checks as adapters are implemented.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="OSS stack validation runner")
    parser.add_argument("--bracket", type=Path)
    parser.add_argument("--json",    action="store_true")
    args = parser.parse_args()

    start = time.time()
    results = []

    # --- Shared: preflight checks ---
    from tooling.generator_core.preflight.validator import PreflightValidator
    validator = PreflightValidator(
        kpi_catalog_root=Path("core/kpi_catalog"),
        action_codes_root=Path("core/action_codes"),
    )
    if args.bracket:
        reports = [validator.run(args.bracket)]
    else:
        brackets = list(Path("core/usecases/core").rglob("UseCase_Bracket.yaml"))
        reports = validator.run_all(brackets)

    for report in reports:
        results.append({
            "check": "preflight",
            "use_case": report.use_case_id,
            "passed": report.passed,
            "errors": report.errors,
            "warnings": report.warnings,
        })

    # --- OSS-specific checks (add here as adapters are implemented) ---
    # TODO: validate_metabase_export(...)
    # TODO: validate_grafana_export(...)
    # TODO: validate_superset_export(...)

    # --- Telemetry ---
    from tooling.generator_core.intelligence.telemetry import TelemetryCollector
    tc = TelemetryCollector()
    all_errors = [e for r in results for e in r.get("errors", [])]
    run = tc.start_run(use_case_id="oss_checks", domain="OSS", adapter="oss")
    tc.complete_run(
        run_id=run["run_id"],
        overall_status="pass" if not all_errors else "fail",
        files_generated=0,
        errors=all_errors,
        warnings=[w for r in results for w in r.get("warnings", [])],
    )

    duration = round((time.time() - start) * 1000)
    all_passed = all(r["passed"] for r in results)

    if args.json:
        print(json.dumps({
            "passed": all_passed,
            "duration_ms": duration,
            "results": results,
        }, indent=2))
    else:
        status = "PASS" if all_passed else "FAIL"
        print(f"OSS checks: {status} ({duration}ms)")
        for r in results:
            icon = "✓" if r["passed"] else "✗"
            print(f"  {icon} {r['use_case']} ({r['check']})")
            for e in r.get("errors", []):
                print(f"      ERROR {e}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
