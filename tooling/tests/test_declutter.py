"""Tests for BC-CHART-04 (declutter) + BC-CHART-05 (reference-line advisory).

BC-CHART-04: a chart visual must carry no decorative chrome (background fill, shadow,
gradient, 3D). BC-CHART-05 is advisory — the reference-line emit is render-gated, so the
reporter only lists comparison exhibits, it never gates.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_declutter import chartjunk, check_report
from tooling.validation.check_reference_lines import comparisons_needing_reference

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"


def _chart(objects):
    return {"visual": {"visualType": "clusteredBarChart", "objects": objects}}


def _shown(v):
    return {"properties": {"show": {"expr": {"Literal": {"Value": v}}}}}


def test_background_fill_is_chartjunk():
    assert chartjunk(_chart({"background": [_shown("true")]})) == ["background"]


def test_shadow_object_is_chartjunk():
    assert "dropShadow" in chartjunk(_chart({"dropShadow": [_shown("true")]}))


def test_clean_chart_has_no_chartjunk():
    assert chartjunk(_chart({"categoryAxis": [{"properties": {}}], "dataLabels": [_shown("true")]})) == []


def test_table_gridlines_are_not_chart_chartjunk():
    # tableEx is not a chart type — its grid object is legitimate table formatting
    table = {"visual": {"visualType": "tableEx", "objects": {"grid": [_shown("true")]}}}
    assert chartjunk(table) == []


def test_committed_dist_charts_are_decluttered():
    reports = sorted(_DIST.glob("*.Report"))
    assert reports, "no dist reports found"
    junk = [(r.name, v) for r in reports for v in check_report(r)]
    assert junk == [], f"chartjunk committed: {junk}"


# ── BC-CHART-05 advisory ─────────────────────────────────────────────────────

def test_reference_advisory_lists_line_comparisons_not_waterfalls():
    needing = comparisons_needing_reference()
    # OPS-001 line vs_target exhibits need a reference line ...
    assert ("OPS-001", "Main_1", "vs_target") in needing
    # ... but a waterfall (intrinsic deviation) never appears
    assert not any(bid == "COM-002" and slot == "Main_2" for bid, slot, _ in needing)
