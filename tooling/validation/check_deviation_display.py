#!/usr/bin/env python3
"""
check_deviation_display.py — Boutique rubric BC-CHART-02 structural validator

Enforces "show deviation as deviation" (Boutique-Craft-Rubric BC-CHART-02, IBCS): when a
30-second exhibit compares against Plan or Prior-Year, the reader wants the *gap*, not two
absolute bars to subtract in their head. A plan/PY variance rendered as clustered/absolute
bars fails; a waterfall/variance bar (the delta itself) passes. Decidable from the governed
bracket spec — an exhibit with `comparison ∈ {vs_plan, vs_py}` and an absolute bar
`visual_type` is the anti-pattern.

`vs_target` is exempt: a target is naturally a reference line/band (BC-CHART-05), so a bar
or line with a target overlay is not "two absolute bars". Trend/line/waterfall are exempt.

Usage:
    python tooling/validation/check_deviation_display.py            # all brackets
    python tooling/validation/check_deviation_display.py --strict   # any violation = exit 1

Exit codes:
    0 — every plan/PY variance is shown as a variance (else 1 when --strict)
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

# Comparisons whose meaning IS a delta between two totals — best shown as the delta.
_VARIANCE_COMPARISONS = {"vs_plan", "vs_py"}
# Absolute-bar visual types: length encodes each total → the reader subtracts by eye.
_ABSOLUTE_BARS = {"bar_chart", "column_chart", "clustered_bar", "stacked_bar"}


def exhibit_violations(bracket: dict) -> list[tuple[str, str, str]]:
    """Return [(slot_id, comparison, visual_type), ...] for plan/PY variances drawn as
    absolute bars. Pure — unit-tested."""
    page = ((bracket.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {})
    out: list[tuple[str, str, str]] = []
    for ex in page.get("component_30s") or []:
        if not isinstance(ex, dict):
            continue
        comp = ex.get("comparison")
        vt = ex.get("visual_type")
        if comp in _VARIANCE_COMPARISONS and vt in _ABSOLUTE_BARS:
            out.append((ex.get("slot_id", "?"), comp, vt))
    return out


def check_registry() -> list[tuple[str, str]]:
    """Return [(bracket_id, violation), ...] across all use-case brackets."""
    out: list[tuple[str, str]] = []
    for path in sorted(_USECASES.glob("**/UseCase_Bracket.yaml")):
        bracket = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        bid = bracket.get("id", path.parent.name)
        for slot, comp, vt in exhibit_violations(bracket):
            out.append((bid, f"{slot}: {comp} shown as '{vt}' (absolute pairs) — "
                             f"use a waterfall/variance bar (BC-CHART-02)"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-CHART-02 deviation-as-deviation validator")
    parser.add_argument("--strict", action="store_true", help="Any violation = exit 1")
    args = parser.parse_args()

    violations = check_registry()
    for bid, err in violations:
        print(f"    ⚠ {bid}: {err}")
    print(f"\nBC-CHART-02: {len(violations)} plan/PY variance(s) drawn as absolute bars.")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
