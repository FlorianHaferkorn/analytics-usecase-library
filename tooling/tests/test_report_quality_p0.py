from __future__ import annotations

import json
from pathlib import Path

from report_quality.content_validator import check_text, extract_texts
from report_quality.cli import validate
from report_quality.dax_reference_validator import parse_semantic_models, validate_report_measure_references
from report_quality.schema_validator import resolve_schema_url, validate_against_schema
from report_quality.self_heal import self_heal
from report_quality.structural_validator import PageSize, ReportSpec, VisualWithinPage, check_report


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _minimal_report(root: Path) -> Path:
    report = root / "COM-001_Test.Report"
    _write_json(report / "definition/pages/pages.json", {"pageOrder": ["Page_COM001_Overview"]})
    _write_json(
        report / "definition/pages/Page_COM001_Overview/page.json",
        {"name": "Page_COM001_Overview", "displayName": "Overview", "width": 1920, "height": 1080},
    )
    for name, vtype in {
        "KPI_Cards": "cardVisual",
        "Main_1": "lineChart",
        "Main_2": "clusteredBarChart",
        "Slicer_Date": "slicer",
    }.items():
        _write_json(
            report / f"definition/pages/Page_COM001_Overview/visuals/{name}/visual.json",
            {
                "name": name,
                "position": {"x": 10, "y": 10, "width": 100, "height": 80},
                "visual": {
                    "visualType": vtype,
                    "visualContainerObjects": {
                        "title": [
                            {
                                "properties": {
                                    "text": {"expr": {"Literal": {"Value": "'Net Sales Trend'"}}}
                                }
                            }
                        ]
                    },
                },
            },
        )
    return report


def test_schema_url_rewrite():
    original = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
    assert resolve_schema_url(original).startswith("https://raw.githubusercontent.com/microsoft/json-schemas/main/")


def test_validate_against_schema_reports_json_pointer():
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    assert validate_against_schema({"x": "bad"}, schema)[0][0] == "/x"


def test_structural_report_passes_minimal_report(tmp_path: Path):
    report = _minimal_report(tmp_path)
    assert check_report(report) == []


def test_structural_bounds_detects_out_of_bounds(tmp_path: Path):
    report = _minimal_report(tmp_path)
    visual = report / "definition/pages/Page_COM001_Overview/visuals/Main_1/visual.json"
    data = json.loads(visual.read_text())
    data["position"]["x"] = 2000
    visual.write_text(json.dumps(data))
    violations = check_report(report, ReportSpec([VisualWithinPage()]))
    assert len(violations) == 1
    assert violations[0].check == "visual:bounds"


def test_structural_bounds_uses_canonical_page_size_when_dimensions_missing(tmp_path: Path):
    report = _minimal_report(tmp_path)
    page = report / "definition/pages/Page_COM001_Overview/page.json"
    data = json.loads(page.read_text())
    del data["width"]
    del data["height"]
    page.write_text(json.dumps(data))
    visual = report / "definition/pages/Page_COM001_Overview/visuals/Main_1/visual.json"
    vdata = json.loads(visual.read_text())
    vdata["position"] = {"x": 1500, "y": 10, "width": 100, "height": 80}
    visual.write_text(json.dumps(vdata))
    violations = check_report(report, ReportSpec([VisualWithinPage()]))
    assert violations == []


def test_self_heal_fixes_page_size(tmp_path: Path):
    report = _minimal_report(tmp_path)
    page = report / "definition/pages/Page_COM001_Overview/page.json"
    data = json.loads(page.read_text())
    data["height"] = 999
    page.write_text(json.dumps(data))
    result = self_heal(report, ReportSpec([PageSize(width=1920, height=1080)]))
    assert result.success
    assert json.loads(page.read_text())["height"] == 1080


def test_content_validator_detects_placeholder_and_mixed_language():
    assert check_text("TODO {{title}}")
    assert any("Mixed" in finding for finding in check_text("The action und die Empfehlung is ready"))


def test_extract_texts_reads_visual_title():
    visual = {
        "visual": {
            "visualContainerObjects": {
                "title": [{"properties": {"text": {"expr": {"Literal": {"Value": "'A Title'"}}}}}]
            }
        }
    }
    assert extract_texts(visual) == [("visualContainerObjects.title[0].text", "A Title")]


def test_dax_reference_merges_measures_across_models(tmp_path: Path):
    for model_name, measure in (("Commercial.SemanticModel", "Net Sales"), ("Finance.SemanticModel", "Cash Balance")):
        tmdl = tmp_path / model_name / "definition/tables/_Measures.tmdl"
        tmdl.parent.mkdir(parents=True)
        tmdl.write_text(f"table _Measures\n\tmeasure '{measure}' = 1\n", encoding="utf-8")
    symbols = parse_semantic_models(tmp_path)
    assert {"Net Sales", "Cash Balance"} <= symbols.measure_names


def test_dax_reference_flags_missing_visual_measure(tmp_path: Path):
    report = _minimal_report(tmp_path)
    tmdl = tmp_path / "Commercial.SemanticModel/definition/tables/_Measures.tmdl"
    tmdl.parent.mkdir(parents=True)
    tmdl.write_text("table _Measures\n\tmeasure 'Net Sales' = 1\n", encoding="utf-8")
    visual = report / "definition/pages/Page_COM001_Overview/visuals/Main_1/visual.json"
    data = json.loads(visual.read_text())
    data["visual"]["query"] = {"queryState": {"Y": {"projections": [{"field": {"Measure": {"Property": "Missing"}}}]}}}
    visual.write_text(json.dumps(data), encoding="utf-8")
    violations = validate_report_measure_references(tmp_path)
    assert len(violations) == 1
    assert violations[0].actual == "Missing"


def test_validate_single_report_includes_measure_reference_check(tmp_path: Path):
    dist = tmp_path / "dist"
    report = _minimal_report(dist)
    tmdl = dist / "Commercial.SemanticModel/definition/tables/_Measures.tmdl"
    tmdl.parent.mkdir(parents=True)
    tmdl.write_text("table _Measures\n\tmeasure 'Net Sales' = 1\n", encoding="utf-8")
    visual = report / "definition/pages/Page_COM001_Overview/visuals/Main_1/visual.json"
    data = json.loads(visual.read_text())
    data["visual"]["query"] = {"queryState": {"Y": {"projections": [{"field": {"Measure": {"Property": "Missing"}}}]}}}
    visual.write_text(json.dumps(data), encoding="utf-8")
    violations = validate(report)
    assert any(v.check == "dax-reference:missing-measure" and v.actual == "Missing" for v in violations)
