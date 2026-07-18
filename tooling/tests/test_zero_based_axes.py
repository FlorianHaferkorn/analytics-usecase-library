"""Tests for the BC-CHART-09 zero-based bar-axis validator.

Truncated bar axes exaggerate differences (length encodes value), so a bar/column
visual must not declare a non-zero valueAxis.start. Pure logic is unit-tested; a guard
keeps the committed dist free of truncated axes.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_zero_based_axes import truncated_axis_start, check_report

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"


def _bar(start_literal=None):
    obj = {}
    if start_literal is not None:
        obj = {"valueAxis": [{"properties": {"start": {"expr": {"Literal": {"Value": start_literal}}}}}]}
    return {"visual": {"visualType": "clusteredBarChart", "objects": obj}}


def test_non_zero_start_is_truncated():
    assert truncated_axis_start(_bar("50D")) == 50.0


def test_zero_start_is_compliant():
    assert truncated_axis_start(_bar("0D")) is None


def test_no_explicit_start_is_compliant():
    assert truncated_axis_start(_bar()) is None


def test_non_bar_visual_is_ignored():
    line = {"visual": {"visualType": "lineChart",
                       "objects": {"valueAxis": [{"properties": {"start": {"expr": {"Literal": {"Value": "50D"}}}}}]}}}
    assert truncated_axis_start(line) is None   # line charts may legitimately start non-zero


def test_committed_dist_has_no_truncated_bar_axes():
    reports = sorted(_DIST.glob("*.Report"))
    assert reports, "no dist reports found"
    offenders = [(r.name, v) for r in reports for v in check_report(r)]
    assert offenders == [], f"truncated bar axes committed: {offenders}"
