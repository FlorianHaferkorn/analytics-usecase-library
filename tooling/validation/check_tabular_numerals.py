#!/usr/bin/env python3
"""
check_tabular_numerals.py — Boutique rubric BC-TYPE-02 ADVISORY reporter

BC-TYPE-02: "tabular (monospaced) numerals in every vertically-compared number column"
(Craft-Core §5.2) — so digits line up and the eye can compare down a column. Governance
declares the intent (typography.yaml → font_family.numerals: tabular), but a per-column
tabular-numeral toggle is NOT part of the proven PBIR corpus (0 occurrences across the
theme + visuals; Power BI exposes no verified font-variant-numeric object for tableEx/
pivotTable columns). So — like BC-CHART-05's reference line — this cannot be a passing
structural gate without a Windows/Fabric render to verify the emit.

This reporter is ADVISORY: it lists the table/matrix visuals whose numeric columns WOULD
carry tabular numerals once the emit is verified, and never gates. The governed font (DIN,
display) already ships tabular numerals for callout values; the open item is table columns.

Usage:
    python tooling/validation/check_tabular_numerals.py     # advisory list (always exit 0)
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_TABLE_TYPES = {"tableEx", "pivotTable"}


def tables_awaiting_tabular() -> list[str]:
    """Return table/matrix visual paths that don't declare a tabular-numeral setting."""
    out: list[str] = []
    for vj in sorted(_DIST.glob("*.Report/definition/pages/*/visuals/*/visual.json")):
        try:
            v = json.loads(vj.read_text(encoding="utf-8")).get("visual", {})
        except (json.JSONDecodeError, OSError):
            continue
        if v.get("visualType") in _TABLE_TYPES:
            blob = json.dumps(v).lower()
            if not any(tok in blob for tok in ("tabular", "tnum", "fontvariantnumeric")):
                out.append(f"{vj.parent.parent.parent.name}/{vj.parent.name}")
    return out


def main() -> int:
    tables = tables_awaiting_tabular()
    print("BC-TYPE-02 (ADVISORY — tabular numerals for number columns are render-gated):")
    for t in tables:
        print(f"    · {t}: numeric columns would set tabular numerals once the PBIR shape is verified")
    print(f"\n{len(tables)} table/matrix visual(s) await a governed tabular-numeral emit "
          f"(Windows/Fabric or powerbi-report-author). Advisory only — never gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
