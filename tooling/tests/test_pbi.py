"""Tests for products/fabric/powerbi/tooling/pbi.py (Epic D).

D1 — inspect: report pages/visuals/bindings + model tables/measures over real dist/.
D2 — set: dotted-path setter, wildcard bulk-set (dry-run/apply), and the H7 guard /
     binding-invariance that keeps a bulk-set from ever touching queryState.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from products.fabric.powerbi.tooling.pbi import (
    bulk_set,
    inspect_model,
    inspect_report,
    set_in,
    visual_bindings,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DIST = _REPO_ROOT / "products" / "fabric" / "powerbi" / "dist"
_COM_REPORT = _DIST / "COM-001_Sales_Performance.Report"
_COM_MODEL = _DIST / "Commercial.SemanticModel"


# ---------------------------------------------------------------------------
# D1 — inspect
# ---------------------------------------------------------------------------

def test_inspect_model_lists_measures_and_columns():
    model = inspect_model(_COM_MODEL)
    assert "Net Sales Amount" in model["measures"]
    assert "Gross Margin %" in model["measures"]
    assert model["relationship_count"] == 21
    dim_org = next(t for t in model["tables"] if t["name"] == "dim_org")
    # OrgKey is a hidden surrogate key (Epic C)
    org_key = next(c for c in dim_org["columns"] if c["name"] == "OrgKey")
    assert org_key["hidden"] is True


def test_inspect_report_reproduces_tree_and_bindings():
    rep = inspect_report(_COM_REPORT)
    assert rep["report"] == "COM-001_Sales_Performance.Report"
    page_names = {p["name"] for p in rep["pages"]}
    assert {"Page_COM001_Overview", "Page_COM001_Detail"} <= page_names
    overview = next(p for p in rep["pages"] if p["name"] == "Page_COM001_Overview")
    kpi = next(v for v in overview["visuals"] if v["name"] == "KPI_Cards")
    assert kpi["type"] == "cardVisual"
    assert "Measure:Net Sales Amount" in kpi["bindings"]["Data"]


def test_visual_bindings_extracts_measures_and_columns():
    vjson = {
        "visual": {"query": {"queryState": {
            "Y": {"projections": [
                {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Sales"}}},
            ]},
            "Category": {"projections": [
                {"field": {"Column": {"Expression": {"SourceRef": {"Entity": "dim_date"}}, "Property": "Month"}}},
            ]},
        }}}
    }
    b = visual_bindings(vjson)
    assert b["Y"] == ["Measure:Sales"]
    assert b["Category"] == ["Column:dim_date.Month"]


# ---------------------------------------------------------------------------
# D2 — set_in (dotted path)
# ---------------------------------------------------------------------------

def test_set_in_creates_intermediates_and_list_indices():
    obj: dict = {}
    set_in(obj, "visual.objects.legend[0].properties.show", True)
    assert obj == {"visual": {"objects": {"legend": [{"properties": {"show": True}}]}}}


def test_set_in_overwrites_existing():
    obj = {"a": {"b": 1}}
    set_in(obj, "a.b", 2)
    assert obj["a"]["b"] == 2


# ---------------------------------------------------------------------------
# D2 — bulk_set
# ---------------------------------------------------------------------------

def _seed_report(root: Path) -> Path:
    rdir = root / "COM-X.Report"
    pdir = rdir / "definition" / "pages" / "Page_X"
    (pdir / "visuals" / "V1").mkdir(parents=True)
    (rdir / "definition" / "pages" / "pages.json").write_text(
        json.dumps({"pageOrder": ["Page_X"], "activePageName": "Page_X"}), encoding="utf-8")
    (pdir / "page.json").write_text(json.dumps({"name": "Page_X", "displayName": "X"}), encoding="utf-8")
    (pdir / "visuals" / "V1" / "visual.json").write_text(json.dumps({
        "name": "V1",
        "position": {"x": 0, "y": 0, "width": 10, "height": 10},
        "visual": {
            "visualType": "lineChart",
            "query": {"queryState": {"Y": {"projections": [
                {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Sales"}}}
            ]}}},
        },
    }), encoding="utf-8")
    return rdir


def test_bulk_set_dry_run_does_not_write(tmp_path):
    rdir = _seed_report(tmp_path)
    before = (rdir / "definition" / "pages" / "Page_X" / "visuals" / "V1" / "visual.json").read_text()
    changed = bulk_set(tmp_path, "visual.objects.legend[0].properties.show", True, type_glob="lineChart")
    assert changed == ["COM-X.Report/Page_X/V1"]
    after = (rdir / "definition" / "pages" / "Page_X" / "visuals" / "V1" / "visual.json").read_text()
    assert before == after  # dry-run wrote nothing


def test_bulk_set_apply_writes_and_leaves_bindings_intact(tmp_path):
    """The H7-invariance proof: a bulk-set sets the format property but the visual's
    queryState (bindings) is byte-for-byte unchanged."""
    rdir = _seed_report(tmp_path)
    vfile = rdir / "definition" / "pages" / "Page_X" / "visuals" / "V1" / "visual.json"
    before_query = copy.deepcopy(json.loads(vfile.read_text())["visual"]["query"])

    changed = bulk_set(tmp_path, "visual.objects.legend[0].properties.show", True,
                       type_glob="lineChart", apply=True)
    assert changed == ["COM-X.Report/Page_X/V1"]
    after = json.loads(vfile.read_text())
    assert after["visual"]["objects"]["legend"][0]["properties"]["show"] is True   # set
    assert after["visual"]["query"] == before_query                                # bindings untouched


def test_bulk_set_type_filter(tmp_path):
    _seed_report(tmp_path)
    # no barChart visuals -> nothing matches
    assert bulk_set(tmp_path, "visual.objects.x[0].properties.y", 1, type_glob="barChart") == []


def test_bulk_set_refuses_bindings(tmp_path):
    _seed_report(tmp_path)
    with pytest.raises(ValueError, match="H7-protected"):
        bulk_set(tmp_path, "visual.query.queryState.Y", 1)
