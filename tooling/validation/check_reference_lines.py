#!/usr/bin/env python3
"""
check_reference_lines.py — Boutique rubric BC-CHART-05 ADVISORY reporter

BC-CHART-05 asks for "a reference line/band for target, threshold or prior period wherever
a comparison exists" (Craft-Core §5.4). The *intent* is governed — every comparison
exhibit declares its reference basis via `comparison` (vs_target / vs_plan / vs_py). But
the rendered reference-line PBIR object is NOT part of the proven corpus (0 occurrences in
products/fabric/powerbi/dist; same emit-gating as the topN visual filter behind BC-CHART-10
and the hero-card reference line). So this rule cannot be a passing structural gate without
a Windows/Fabric or powerbi-report-author render to verify the object shape.

This reporter is therefore ADVISORY: it lists the comparison exhibits that WOULD carry a
reference line once the emit shape is verified, and never gates (no --strict exit 1). It
marks the honest render boundary rather than faking coverage. Waterfall/variance exhibits
are excluded — they show the deviation intrinsically, no separate reference line needed.

Usage:
    python tooling/validation/check_reference_lines.py     # advisory list (always exit 0)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
_USECASES = REPO / "core/usecases"

# Deviation is intrinsic to these — the bars ARE the gap, no reference line needed.
_INTRINSIC_DEVIATION = {"waterfall", "variance_bar", "stacked_bar"}


def comparisons_needing_reference() -> list[tuple[str, str, str]]:
    """Return [(bracket_id, slot_id, comparison), ...] — comparison exhibits on a
    line/bar chart that would render a reference line/band. Pure — unit-tested."""
    out: list[tuple[str, str, str]] = []
    for path in sorted(_USECASES.glob("**/UseCase_Bracket.yaml")):
        bracket = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        bid = bracket.get("id", path.parent.name)
        page = ((bracket.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {})
        for ex in page.get("component_30s") or []:
            if not isinstance(ex, dict):
                continue
            if ex.get("comparison") and ex.get("visual_type") not in _INTRINSIC_DEVIATION:
                out.append((bid, ex.get("slot_id", "?"), ex["comparison"]))
    return out


def main() -> int:
    needing = comparisons_needing_reference()
    print("BC-CHART-05 (ADVISORY — reference-line emit is render-gated, unverified in corpus):")
    for bid, slot, comp in needing:
        print(f"    · {bid}/{slot}: {comp} → would carry a reference line/band once the "
              f"PBIR shape is render-verified")
    print(f"\n{len(needing)} comparison exhibit(s) await a governed reference-line emit "
          f"(Windows/Fabric or powerbi-report-author). Advisory only — never gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
