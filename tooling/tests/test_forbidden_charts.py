"""Tests for the BC-CHART-08 forbidden-chart-type gate.

Thin CLI over the existing ForbiddenVisualTypes invariant — tests the reuse wiring and
guards that the committed dist ships no pie/donut/gauge/treemap.
"""
from __future__ import annotations

import json
from pathlib import Path

from tooling.validation.check_forbidden_charts import forbidden_in
import pytest

from tooling.report_quality.structural_validator import DEPRECATED_VISUAL_TYPES, ForbiddenVisualTypes

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"


def _report_with_visual(tmp_path: Path, visual_type: str) -> Path:
    rep = tmp_path / "UC-TEST.Report" / "definition" / "pages" / "P" / "visuals" / "v"
    rep.mkdir(parents=True)
    (rep / "visual.json").write_text(json.dumps({
        "name": "v", "position": {"x": 0, "y": 0, "width": 100, "height": 100},
        "visual": {"visualType": visual_type},
    }), encoding="utf-8")
    page = tmp_path / "UC-TEST.Report" / "definition" / "pages" / "P"
    (page / "page.json").write_text(json.dumps({"name": "P", "width": 1280, "height": 720}), encoding="utf-8")
    (tmp_path / "UC-TEST.Report" / "definition" / "pages" / "pages.json").write_text(
        json.dumps({"pageOrder": ["P"]}), encoding="utf-8")
    (tmp_path / "UC-TEST.Report" / "definition.pbir").write_text(json.dumps({"version": "4.0"}), encoding="utf-8")
    return tmp_path / "UC-TEST.Report"


def test_pie_chart_is_flagged(tmp_path):
    hits = forbidden_in(_report_with_visual(tmp_path, "pieChart"))
    assert "pieChart" in hits


def test_bar_chart_is_clean(tmp_path):
    assert forbidden_in(_report_with_visual(tmp_path, "clusteredColumnChart")) == []


def test_forbidden_set_is_the_governed_one():
    # the reuse guarantee: the forbidden set lives in the invariant, not here
    # (IBCS 2.0 EX 2.1-2.3 since 02.10.2026: funnel added; radar/custom gauges by substring)
    # (07.10.2026: plus the Microsoft-deprecated types, D-683 Meridian)
    assert ForbiddenVisualTypes().forbidden == {
        "pieChart", "donutChart", "gauge", "treemap", "funnel",
        "map", "filledMap", "qnaVisual", "card", "multiRowCard",
    }


def test_declared_exception_is_not_a_violation(tmp_path):
    rep = _report_with_visual(tmp_path, "gauge")
    vj = next(rep.rglob("visual.json"))
    body = json.loads(vj.read_text(encoding="utf-8"))
    body["annotations"] = [{"name": "ibcs.ausnahme", "value": "EX 2.2: Leitstand"}]
    vj.write_text(json.dumps(body), encoding="utf-8")
    assert forbidden_in(rep) == []
    # Gegenprobe: ohne Annotation zaehlt der Tacho
    body.pop("annotations")
    vj.write_text(json.dumps(body), encoding="utf-8")
    assert forbidden_in(rep) == ["gauge"]


@pytest.mark.parametrize("visual_type,replacement", [
    ("filledMap", "azureMap"),
    ("map", "azureMap"),
    ("qnaVisual", "Copilot"),
    ("card", "cardVisual"),
    ("multiRowCard", "cardVisual"),
])
def test_deprecated_visual_type_is_flagged_with_replacement(tmp_path, visual_type, replacement):
    hits = forbidden_in(_report_with_visual(tmp_path, visual_type))
    assert hits == [visual_type]
    assert replacement in DEPRECATED_VISUAL_TYPES[visual_type]


@pytest.mark.parametrize("visual_type", ["cardVisual", "azureMap"])
def test_replacement_visual_type_is_clean(tmp_path, visual_type):
    assert forbidden_in(_report_with_visual(tmp_path, visual_type)) == []


def test_deprecated_list_mirrors_the_scaffold_validator():
    # Paketgrenze: products/ und tooling/ halten je eine Kopie; diese Gleichheit ist die Kopplung.
    import sys
    sys.path.insert(0, str(REPO / "products/fabric/powerbi/tooling"))
    from page_scaffold_generator import visual_validator as vv
    assert vv._DEPRECATED_PBI_TYPES == DEPRECATED_VISUAL_TYPES


def test_committed_dist_has_no_forbidden_types():
    reports = sorted(_DIST.glob("*.Report"))
    assert reports, "no dist reports found"
    offenders = {r.name: forbidden_in(r) for r in reports if forbidden_in(r)}
    assert offenders == {}, f"forbidden chart types present: {offenders}"
