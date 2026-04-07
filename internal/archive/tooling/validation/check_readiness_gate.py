"""
Readiness Gate Check
====================

Warns when use cases with overall_readiness 'red' have subscribed action codes,
indicating the use case is being implemented despite not being ready.

Also warns about use cases missing prioritization or readiness blocks entirely.

Exit codes:
  0 - All checks pass (or only warnings)
  1 - Blocking issues found (--fail-on-red flag)

Usage:
  python tooling/validation/check_readiness_gate.py
  python tooling/validation/check_readiness_gate.py --fail-on-red
  python tooling/validation/check_readiness_gate.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_readiness(repo_root: Path) -> Dict[str, Any]:
    """Check readiness gate across all use case brackets."""
    usecases_dir = repo_root / "core" / "usecases"

    findings: List[Dict[str, Any]] = []
    total = 0
    red_with_actions = 0
    missing_blocks = 0

    for bracket_path in sorted(usecases_dir.rglob("UseCase_Bracket.yaml")):
        if "templates" in bracket_path.parts:
            continue

        try:
            data = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        uc_id = data.get("id", bracket_path.parent.name)
        total += 1

        readiness = data.get("readiness")
        prioritization = data.get("prioritization")
        action_codes = data.get("orchestration", {}).get("action_code_ids", [])

        # Check 1: Missing blocks
        if readiness is None or prioritization is None:
            missing_blocks += 1
            missing_parts = []
            if prioritization is None:
                missing_parts.append("prioritization")
            if readiness is None:
                missing_parts.append("readiness")
            findings.append({
                "id": uc_id,
                "level": "info",
                "message": f"Missing {' and '.join(missing_parts)} block(s)",
                "path": str(bracket_path.relative_to(repo_root)),
            })
            continue

        overall = readiness.get("overall_readiness")

        # Check 2: Red readiness with action codes = actively being implemented despite not ready
        if overall == "red" and len(action_codes) > 0:
            red_with_actions += 1
            findings.append({
                "id": uc_id,
                "level": "warning",
                "message": f"Readiness is RED but {len(action_codes)} action codes are subscribed. "
                           f"Consider pausing implementation until prerequisites are met.",
                "path": str(bracket_path.relative_to(repo_root)),
                "details": {
                    "overall_readiness": overall,
                    "data_availability": readiness.get("data_availability"),
                    "org_capability": readiness.get("org_capability"),
                    "stakeholder_alignment": readiness.get("stakeholder_alignment"),
                    "action_code_ids": action_codes,
                },
            })

        # Check 3: Amber readiness with low confidence = risky implementation
        confidence = (prioritization or {}).get("confidence", 1.0)
        if overall == "amber" and confidence < 0.5:
            findings.append({
                "id": uc_id,
                "level": "info",
                "message": f"Readiness is AMBER with low confidence ({confidence:.0%}). "
                           f"Consider validating assumptions before proceeding.",
                "path": str(bracket_path.relative_to(repo_root)),
            })

    return {
        "check": "readiness_gate",
        "total_use_cases": total,
        "red_with_actions": red_with_actions,
        "missing_blocks": missing_blocks,
        "findings": findings,
        "status": "fail" if red_with_actions > 0 else "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Readiness Gate Check")
    parser.add_argument("--fail-on-red", action="store_true",
                        help="Exit with code 1 if any red-readiness use case has action codes")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--root", type=str, help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.root) if args.root else _repo_root()
    results = check_readiness(repo_root)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        BOLD = "\033[1m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[91m"
        RESET = "\033[0m"

        print(f"\n{BOLD}Readiness Gate Check{RESET}")
        print(f"  {results['total_use_cases']} use cases scanned\n")

        for f in results["findings"]:
            if f["level"] == "warning":
                print(f"  {RED}[WARN]{RESET}  {f['id']}: {f['message']}")
            else:
                print(f"  {YELLOW}[INFO]{RESET}  {f['id']}: {f['message']}")

        if not results["findings"]:
            print(f"  {GREEN}[PASS]{RESET}  No readiness gate issues found.")

        print()

    if args.fail_on_red and results["red_with_actions"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
