#!/usr/bin/env python3
"""
check_forbidden_charts.py — Boutique rubric BC-CHART-08 gate (chart type fits the message)

"Chart type fits the message; forbidden expressive types barred" (Boutique-Craft-Rubric
BC-CHART-08, Craft-Core §5.4 / IBCS). Pie / donut / gauge / treemap distort or decorate
instead of comparing — a boutique report never ships them. Since 02.10.2026 the invariant
also carries IBCS 2.0 EX 2.1-2.5 (funnel, radar, spaghetti lines, traffic lights) with the
catalogue page as source; an exception declared per PBIR annotation `ibcs.ausnahme` is an
`info` finding and does not count here. Since 07.10.2026 it also bars the visual types Microsoft
has deprecated (map / filledMap -> azureMap, qnaVisual -> Copilot, card / multiRowCard ->
cardVisual; see structural_validator.DEPRECATED_VISUAL_TYPES).

Tool-Reuse: this is a thin CLI over the EXISTING `ForbiddenVisualTypes` invariant in
tooling/report_quality/structural_validator.py — the forbidden set and the PBIR walk
live there, this only runs it over the committed dist and maps the result onto the
Boutique-Scorecard (so BC-CHART-08 is machine-scored, not left to the judge). Note the
bracket schema's visual_type enum already bars these types at authoring time; this
verifies the *rendered* PBIR carries none.

Usage:
    python tooling/validation/check_forbidden_charts.py            # all dist reports
    python tooling/validation/check_forbidden_charts.py --strict   # any forbidden type = exit 1

Exit codes:
    0 — no forbidden visual types (else 1 when --strict)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tooling.report_quality.structural_validator import (  # noqa: E402
    ForbiddenVisualTypes, ReportSpec, check_report,
)

_DIST = REPO / "products/fabric/powerbi/dist"
_SPEC = ReportSpec(invariants=[ForbiddenVisualTypes()])


def forbidden_in(report_dir: Path) -> list[str]:
    """Return the forbidden-type violations for one .Report (reuses the invariant).

    `info` findings (declared IBCS exception, or a line count that only the data decides)
    are not violations of BC-CHART-08 and stay out of this list.
    """
    return [v.actual for v in check_report(report_dir, _SPEC) if v.severity != "info"]


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-CHART-08 forbidden-chart-type gate")
    parser.add_argument("--strict", action="store_true", help="Any forbidden type = exit 1")
    args = parser.parse_args()

    reports = sorted(_DIST.glob("*.Report")) if _DIST.is_dir() else []
    clean = bad = 0
    for r in reports:
        hits = forbidden_in(r)
        if hits:
            bad += 1
            print(f"    ⚠ {r.name}: forbidden visual type(s) {sorted(set(hits))} — BC-CHART-08")
        else:
            clean += 1

    total = clean + bad
    print(f"\nBC-CHART-08: {clean}/{total} reports free of forbidden chart types, {bad} with.")
    if args.strict and bad:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
