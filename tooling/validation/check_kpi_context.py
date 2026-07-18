#!/usr/bin/env python3
"""
check_kpi_context.py — Boutique rubric BC-NARR-04 structural validator (advisory)

Enforces "every prominent number carries context" (Boutique-Craft-Rubric BC-NARR-04):
the 3-second hero KPI card (component_3s) should declare a governed comparison
(vs plan / PY / target) or an explicit target — so the reader never sees a bare number.
BC-NARR-04 is `major` (not a knock-out): missing context is advisory and feeds the
boutique scorecard; it is not a hard block. The coverage regression guard
(tooling/tests/test_kpi_context.py) prevents coverage from dropping.

This is the third structural rubric rule wired into the gate (after BC-NARR-01 and
BC-CHART-01). Clearing the backlog is a curated rollout (choose the comparison whose
delta measure actually exists per KPI) — see KONZEPT §12; it dovetails with K4
(benchmark grounding adds the third comparison axis, vs. benchmark).

Usage:
    python tooling/validation/check_kpi_context.py            # all use cases
    python tooling/validation/check_kpi_context.py COM-002     # single use case
    python tooling/validation/check_kpi_context.py --strict    # missing context = exit 1

Exit codes:
    0 — always (advisory), unless --strict and a hero card lacks context
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]


def has_context(card: Optional[dict[str, Any]]) -> bool:
    """True if a KPI card declares governed context (comparison / target / status).

    Pure function — unit-tested in tooling/tests/test_kpi_context.py.
    """
    if not isinstance(card, dict):
        return False
    return bool(
        card.get("comparison")
        or card.get("target_value") is not None
        or card.get("status_logic")
    )


def hero_card(bracket: dict[str, Any]) -> Optional[dict[str, Any]]:
    page = (bracket.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {}
    c3 = page.get("component_3s")
    return c3 if isinstance(c3, dict) and c3.get("kpi_id") else None


def check_bracket(path: Path) -> Optional[bool]:
    """Return True (hero has context) / False (missing) / None (no hero card)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    card = hero_card(data)
    if card is None:
        return None
    return has_context(card)


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-NARR-04 KPI-context validator")
    parser.add_argument("use_case_id", nargs="?", help="Validate a single use case by ID substring")
    parser.add_argument("--strict", action="store_true", help="Missing hero context = exit 1")
    args = parser.parse_args()

    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    if args.use_case_id:
        brackets = [b for b in brackets if args.use_case_id.lower() in str(b).lower()]
        if not brackets:
            print(f"No UseCase_Bracket.yaml found matching '{args.use_case_id}'", file=sys.stderr)
            return 1

    covered = missing = 0
    for b in brackets:
        res = check_bracket(b)
        if res is None:
            continue
        if res:
            covered += 1
        else:
            missing += 1
            print(f"    ⚠ {b.parent.name.split('_')[0]}: hero KPI card has no governed context "
                  f"(comparison/target) — BC-NARR-04")

    total = covered + missing
    print(f"\nBC-NARR-04: {covered}/{total} hero KPI cards carry context, {missing} advisory.")
    if args.strict and missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
