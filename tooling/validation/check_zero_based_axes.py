#!/usr/bin/env python3
"""
check_zero_based_axes.py — Boutique rubric BC-CHART-09 structural validator

Enforces "zero-based axes for bars; no undisclosed truncation" (Boutique-Craft-Rubric
BC-CHART-09, Craft-Core §5.4). A bar/column chart whose value axis starts at a non-zero
value distorts the area-to-value mapping — the reader compares bar *lengths*, so a
truncated baseline exaggerates differences. Checkable from the committed PBIR (no render):
each bar/column visual must not declare a non-zero `valueAxis.start`.

Like BC-CHART-08 (forbidden charts), this is a *verification* rule — it reads the emitted
visual.json objects, needs no unverified emit, and locks the generator's clean output in
(a regression guard: nothing may commit a truncated bar axis).

Usage:
    python tooling/validation/check_zero_based_axes.py            # all dist reports
    python tooling/validation/check_zero_based_axes.py --strict   # any truncated axis = exit 1

Exit codes:
    0 — no truncated bar axes (else 1 when --strict)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"

# Bar/column families where length encodes value → the baseline must be zero.
_BAR_TYPES = {
    "barChart", "clusteredBarChart", "stackedBarChart", "hundredPercentStackedBarChart",
    "columnChart", "clusteredColumnChart", "stackedColumnChart",
    "hundredPercentStackedColumnChart",
}

_NUM = re.compile(r"^-?\d+(?:\.\d+)?")


def _literal_number(prop: dict) -> float | None:
    """Extract the numeric value from a PBIR object property literal (e.g. '50D' → 50.0)."""
    try:
        val = prop["expr"]["Literal"]["Value"]
    except (KeyError, TypeError):
        return None
    m = _NUM.match(str(val))
    return float(m.group()) if m else None


def truncated_axis_start(visual: dict) -> float | None:
    """Return the non-zero value-axis start of a bar/column visual, else None.

    None means compliant (zero-based or no explicit start). Pure — unit-tested.
    """
    v = visual.get("visual", visual) if isinstance(visual, dict) else {}
    if v.get("visualType") not in _BAR_TYPES:
        return None
    for block in (v.get("objects") or {}).get("valueAxis", []) or []:
        start = ((block or {}).get("properties") or {}).get("start")
        if isinstance(start, dict):
            num = _literal_number(start)
            if num is not None and num != 0.0:
                return num
    return None


def check_report(report_dir: Path) -> list[tuple[str, float]]:
    """Return [(visual_rel_path, non_zero_start), ...] for one .Report directory."""
    out: list[tuple[str, float]] = []
    for vj in sorted(report_dir.glob("definition/pages/*/visuals/*/visual.json")):
        try:
            data = json.loads(vj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        start = truncated_axis_start(data)
        if start is not None:
            out.append((f"{vj.parent.parent.parent.name}/{vj.parent.name}", start))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-CHART-09 zero-based bar-axis validator")
    parser.add_argument("--strict", action="store_true", help="Any truncated bar axis = exit 1")
    args = parser.parse_args()

    reports = sorted(_DIST.glob("*.Report")) if _DIST.is_dir() else []
    violations = 0
    for r in reports:
        for vpath, start in check_report(r):
            violations += 1
            print(f"    ⚠ {r.name}/{vpath}: bar value-axis start={start} ≠ 0 (truncated) — BC-CHART-09")

    print(f"\nBC-CHART-09: {len(reports)} reports scanned, {violations} truncated bar axis(es).")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
