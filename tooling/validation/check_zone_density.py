#!/usr/bin/env python3
"""
check_zone_density.py — Boutique rubric BC-LAYOUT-04 structural validator

BC-LAYOUT-04: "no metric overload — ≤7 KPIs/elements per zone" (Craft-Core §5.1). A zone
crammed with >7 elements defeats the 3-/30-/300-second hierarchy — the eye can't triage.
Decidable from the governed bracket: the summary page's 3-second zone is the hero card
(component_3s) + the 30-second exhibits (component_30s); their combined count must stay
≤7 so the page reads at a glance.

Usage:
    python tooling/validation/check_zone_density.py            # all brackets
    python tooling/validation/check_zone_density.py --strict   # any overloaded zone = exit 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
_USECASES = REPO / "core/usecases"
_MAX_PER_ZONE = 7


def summary_zone_count(bracket: dict) -> int:
    """Elements in the summary page zone: the hero card + the 30-second exhibits. Pure."""
    page = ((bracket.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {})
    hero = 1 if page.get("component_3s") else 0
    c30 = page.get("component_30s") or []
    return hero + (len(c30) if isinstance(c30, list) else 0)


def check_registry() -> list[tuple[str, int]]:
    """Return [(bracket_id, count), ...] for summary zones with > _MAX_PER_ZONE elements."""
    out: list[tuple[str, int]] = []
    for path in sorted(_USECASES.glob("**/UseCase_Bracket.yaml")):
        bracket = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        n = summary_zone_count(bracket)
        if n > _MAX_PER_ZONE:
            out.append((bracket.get("id", path.parent.name), n))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-LAYOUT-04 zone-density validator")
    parser.add_argument("--strict", action="store_true", help="Any zone > 7 elements = exit 1")
    args = parser.parse_args()

    violations = check_registry()
    for bid, n in violations:
        print(f"    ⚠ {bid}: summary zone has {n} elements (> {_MAX_PER_ZONE}) — BC-LAYOUT-04")
    print(f"\nBC-LAYOUT-04: {len(violations)} overloaded zone(s) (max {_MAX_PER_ZONE}/zone).")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
