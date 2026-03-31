"""
Priority Score Calculator
=========================

Calculates or validates priority_score fields in UseCase_Bracket.yaml files
based on RICE-inspired formula:

  priority_score = business_value_weight * reach_weight * confidence * 100
                   / implementation_effort_weight

Weights:
  business_value:  high=3, medium=2, low=1
  reach:           organization=3, division=2, team=1
  effort:          low=1, medium=2, high=3

Usage:
  python tooling/priority_calculator.py                # Show scores for all use cases
  python tooling/priority_calculator.py --update        # Write calculated scores back to YAML
  python tooling/priority_calculator.py --json          # JSON output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


VALUE_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
REACH_WEIGHTS = {"organization": 3, "division": 2, "team": 1}
EFFORT_WEIGHTS = {"low": 1, "medium": 2, "high": 3}


def calculate_priority_score(prioritization: Dict[str, Any]) -> Optional[int]:
    """Calculate priority score from prioritization fields using RICE-inspired formula."""
    bv = prioritization.get("business_value")
    effort = prioritization.get("implementation_effort")
    confidence = prioritization.get("confidence")
    reach = prioritization.get("reach")

    if not all([bv, effort, confidence is not None, reach]):
        return None

    bv_w = VALUE_WEIGHTS.get(bv, 0)
    reach_w = REACH_WEIGHTS.get(reach, 0)
    effort_w = EFFORT_WEIGHTS.get(effort, 1)

    raw = (bv_w * reach_w * confidence) / effort_w
    # Normalize: max raw = 3*3*1.0/1 = 9, min raw = 1*1*0/3 = 0
    normalized = min(100, max(1, round(raw / 9 * 100)))
    return normalized


def scan_brackets(repo_root: Path) -> List[Dict[str, Any]]:
    """Scan all UseCase_Bracket.yaml files and compute priority scores."""
    results = []
    usecases_dir = repo_root / "core" / "usecases"

    for bracket_path in sorted(usecases_dir.rglob("UseCase_Bracket.yaml")):
        if "templates" in bracket_path.parts:
            continue

        with open(bracket_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        uc_id = data.get("id", "unknown")
        title = data.get("title", "")
        prio = data.get("prioritization")
        readiness = data.get("readiness")

        result = {
            "id": uc_id,
            "title": title,
            "path": str(bracket_path.relative_to(repo_root)),
            "has_prioritization": prio is not None,
            "has_readiness": readiness is not None,
        }

        if prio:
            calculated = calculate_priority_score(prio)
            current = prio.get("priority_score")
            result["current_score"] = current
            result["calculated_score"] = calculated
            result["score_matches"] = current == calculated
            result["business_value"] = prio.get("business_value")
            result["implementation_effort"] = prio.get("implementation_effort")
            result["confidence"] = prio.get("confidence")
            result["reach"] = prio.get("reach")

        if readiness:
            result["overall_readiness"] = readiness.get("overall_readiness")

        results.append(result)

    return results


def update_brackets(repo_root: Path, results: List[Dict[str, Any]]) -> int:
    """Write calculated priority_score back to YAML files."""
    updated = 0
    for r in results:
        if not r.get("has_prioritization") or r.get("score_matches", True):
            continue

        bracket_path = repo_root / r["path"]
        with open(bracket_path, encoding="utf-8") as f:
            content = f.read()

        old_score = r["current_score"]
        new_score = r["calculated_score"]

        if old_score is not None:
            content = content.replace(
                f"priority_score: {old_score}",
                f"priority_score: {new_score}",
            )
        else:
            content = content.replace(
                "priority_score: null",
                f"priority_score: {new_score}",
            )

        with open(bracket_path, "w", encoding="utf-8") as f:
            f.write(content)

        updated += 1
        print(f"  Updated {r['id']}: {old_score} -> {new_score}")

    return updated


def print_table(results: List[Dict[str, Any]]) -> None:
    """Print priority ranking table."""
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[91m"
    RESET = "\033[0m"

    scored = [r for r in results if r.get("has_prioritization")]
    scored.sort(key=lambda x: x.get("calculated_score") or 0, reverse=True)

    print(f"\n{BOLD}{'=' * 80}")
    print(f"  Use Case Priority Ranking")
    print(f"{'=' * 80}{RESET}\n")
    print(f"  {'ID':<12} {'Score':>5}  {'Value':<8} {'Effort':<8} {'Conf':>5}  {'Reach':<13} {'Readiness':<10} {'Title'}")
    print(f"  {'-' * 78}")

    for r in scored:
        readiness = r.get("overall_readiness", "n/a")
        color = GREEN if readiness == "green" else YELLOW if readiness == "amber" else RED if readiness == "red" else RESET
        score = r.get("calculated_score", 0)
        print(
            f"  {r['id']:<12} {score:>5}  "
            f"{r.get('business_value', 'n/a'):<8} "
            f"{r.get('implementation_effort', 'n/a'):<8} "
            f"{r.get('confidence', 0):>5.2f}  "
            f"{r.get('reach', 'n/a'):<13} "
            f"{color}{readiness:<10}{RESET} "
            f"{r['title']}"
        )

    without = [r for r in results if not r.get("has_prioritization")]
    if without:
        print(f"\n  {BOLD}Without prioritization:{RESET}")
        for r in without:
            print(f"    {r['id']}: {r['title']}")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Priority Score Calculator")
    parser.add_argument("--update", action="store_true", help="Write calculated scores back to YAML")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--root", type=str, help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.root) if args.root else _repo_root()
    results = scan_brackets(repo_root)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.update:
        updated = update_brackets(repo_root, results)
        print(f"\n{updated} file(s) updated.")
        if updated > 0:
            print_table(scan_brackets(repo_root))
    else:
        print_table(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
