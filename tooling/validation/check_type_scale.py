#!/usr/bin/env python3
"""
check_type_scale.py — Boutique rubric BC-TYPE-03 structural validator

BC-TYPE-03: "hero value ≥ 2× the size of secondary values on the same card" (Craft-Core
§5.2). The 3-second hero number must dominate — a flat card where the value and its label
are near-equal reads as a table cell, not a headline. Decidable from the governed type
scale (core/templates/page_templates/tokens/typography.yaml → scale): the kpi_value role
(hero) must be ≥ 2× each secondary role that shares the KPI card (kpi_delta, kpi_label).

Uses the strictest test — hero MIN pt ≥ 2× secondary MAX pt — so the ratio holds across
the whole size range, not just the best case.

Usage:
    python tooling/validation/check_type_scale.py            # check the governed scale
    python tooling/validation/check_type_scale.py --strict   # ratio < 2 = exit 1
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
_TYPOGRAPHY = REPO / "core/templates/page_templates/tokens/typography.yaml"

_HERO_ROLE = "kpi_value"
_SECONDARY_ROLES = ("kpi_delta", "kpi_label")   # values that share the KPI card
_MIN_RATIO = 2.0


def hierarchy_violations(scale: dict) -> list[str]:
    """Return violation strings where the hero is not ≥2× a secondary. Pure — tested."""
    hero = scale.get(_HERO_ROLE, {}) or {}
    hero_min = hero.get("size_min_pt")
    out: list[str] = []
    if not isinstance(hero_min, (int, float)):
        return [f"{_HERO_ROLE} has no size_min_pt"]
    for role in _SECONDARY_ROLES:
        sec = scale.get(role, {}) or {}
        sec_max = sec.get("size_max_pt")
        if isinstance(sec_max, (int, float)) and sec_max > 0:
            ratio = hero_min / sec_max
            if ratio < _MIN_RATIO:
                out.append(f"{_HERO_ROLE} {hero_min}pt is only {ratio:.2f}× {role} {sec_max}pt (need ≥2×)")
    return out


def check_scale() -> list[str]:
    data = yaml.safe_load(_TYPOGRAPHY.read_text(encoding="utf-8")) or {}
    return hierarchy_violations(data.get("scale", {}) or {})


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-TYPE-03 hero-value type-hierarchy validator")
    parser.add_argument("--strict", action="store_true", help="Hero < 2× secondary = exit 1")
    args = parser.parse_args()

    violations = check_scale()
    for v in violations:
        print(f"    ⚠ {v} — BC-TYPE-03")
    print(f"\nBC-TYPE-03: {len(violations)} hero/secondary ratio violation(s).")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
