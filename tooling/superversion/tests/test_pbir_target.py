"""Tests for the PBIR report target adapter (task I-3.3).

Gate per the DoD: the emitted report passes Microsoft's official
``powerbi-report-author validate`` with **0 errors** (the I-3.3 ``check_pbir``
gate) — skipped only when the CLI is not installed. Always-on structural checks
mirror the validator's hard rules (every visual carries a ``queryState`` with
its required roles), plus determinism and a parse round-trip through Meridian's
vendored ``pbir_parser``.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tooling.superversion import _meridian_vendor
from tooling.superversion.canonical_contract import (
    CanonicalModel,
    ReportModel,
    ReportPage,
    SemanticModel,
    Visual,
)
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.e2e_smoke import _decode_process_output, _executable_command
from tooling.superversion.targets import base
from tooling.superversion.targets import pbir  # noqa: F401 — registers the "pbir" adapter

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
CURATED_REPORTS = [
    COM001,
    REPO / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml",
    REPO / "core/usecases/core/OPS-001_Operations_Performance/UseCase_Bracket.yaml",
    REPO / "core/usecases/core/XD-004_Executive_Action_Governance/UseCase_Bracket.yaml",
]
CLI = "powerbi-report-author"


@pytest.fixture
def model() -> CanonicalModel:
    return from_bracket_file(COM001, KPIS)


def test_pbir_adapter_registered():
    assert "pbir" in base.available()
    assert base.get("pbir").fmt == "pbir"


def test_emit_file_layout(model):
    out = pbir.emit(model)
    base_dir = f"{model.report.name}.Report"
    assert f"{base_dir}/definition.pbir" in out
    assert f"{base_dir}/definition/version.json" in out
    assert f"{base_dir}/definition/report.json" in out
    assert f"{base_dir}/definition/pages/pages.json" in out
    for page in model.report.pages:
        assert f"{base_dir}/definition/pages/{page.name}/page.json" in out
        for v in page.visuals:
            assert f"{base_dir}/definition/pages/{page.name}/visuals/{v.visual_id}/visual.json" in out
    # All emitted files are valid JSON ending in a trailing newline (Invariant I2).
    for content in out.values():
        assert content.endswith("\n")
        json.loads(content)


def test_emit_is_deterministic(model):
    assert pbir.emit(model) == pbir.emit(model)


def test_format_version_constants(model):
    out = pbir.emit(model)
    defpbir = json.loads(out[f"{model.report.name}.Report/definition.pbir"])
    assert defpbir["version"] == "4.0"
    version = json.loads(out[f"{model.report.name}.Report/definition/version.json"])
    assert version["version"] == "2.0.0"


def test_report_uses_official_base_theme_and_interaction_defaults(model):
    out = pbir.emit(model)
    report = json.loads(out[f"{model.report.name}.Report/definition/report.json"])
    assert report["themeCollection"]["baseTheme"]["name"] == "CY25SU10"
    assert report["settings"]["useEnhancedTooltips"] is True
    assert report["settings"]["defaultDrillFilterOtherVisuals"] is True


def test_native_visual_formatting_carries_meaning_not_decoration(model):
    out = pbir.emit(model)
    visuals = {
        json.loads(content)["name"]: json.loads(content)["visual"]
        for path, content in out.items()
        if path.endswith("/visual.json")
    }

    card = visuals["KPI_Cards"]
    assert card["objects"]["layout"][0]["properties"]["columnCount"]["expr"]["Literal"]["Value"] == "1L"

    chart = visuals["Main_1"]
    assert chart["visualContainerObjects"]["title"][0]["properties"]["show"]["expr"]["Literal"]["Value"] == "true"

    slicer = visuals["Slicer_Date"]
    assert slicer["objects"]["data"][0]["properties"]["mode"]["expr"]["Literal"]["Value"] == "'Dropdown'"

    table = visuals["Detail_Matrix"]
    grid = table["objects"]["grid"][0]["properties"]
    assert grid["gridVertical"]["expr"]["Literal"]["Value"] == "false"
    assert grid["rowPadding"]["expr"]["Literal"]["Value"] == "8L"


def test_every_data_visual_has_querystate_with_projections(model):
    """The validator errors on a visual without queryState (PBIR_QUERY_STATE_MISSING)
    or with an empty required role; assert the structure that prevents both."""
    out = pbir.emit(model)
    visual_files = [c for path, c in out.items() if path.endswith("/visual.json")]
    assert visual_files
    for content in visual_files:
        vj = json.loads(content)
        if vj["visual"]["visualType"] == "textbox":
            assert "query" not in vj["visual"]
            continue
        query_state = vj["visual"]["query"]["queryState"]
        assert query_state, "queryState must be non-empty"
        for role, body in query_state.items():
            assert body["projections"], f"role {role} has no projection"


@pytest.mark.skipif(shutil.which(CLI) is None, reason="powerbi-report-author CLI not installed")
def test_official_validator_zero_errors(model, tmp_path):
    """I-3.3 gate: the official MS validator reports 0 errors on the emitted report."""
    base.render("pbir", model, tmp_path)
    report_dir = tmp_path / f"{model.report.name}.Report"
    cli_path = shutil.which(CLI)
    assert cli_path is not None
    proc = subprocess.run(
        _executable_command(cli_path, "validate", str(report_dir), "--no-schema", "--format", "json"),
        capture_output=True, timeout=120,
    )
    data = json.loads(_decode_process_output(proc.stdout))["data"]
    assert data["errorCount"] == 0, json.dumps(data.get("diagnostics"), indent=2)


def test_parse_roundtrip_with_vendored_parser(model, tmp_path):
    """Emitted PBIR parses back through Meridian's real pbir_parser: page names and
    visual ids/types survive the round trip."""
    try:
        parser = _meridian_vendor._load_module(
            "_mer_pbir_roundtrip",
            _meridian_vendor.VENDOR_DIR / "core/pbi_engine/parsers/pbir_parser.py",
        )
    except Exception:
        pytest.skip("vendored pbir_parser not loadable")

    base.render("pbir", model, tmp_path)
    parsed = parser.parse_report(tmp_path / f"{model.report.name}.Report")
    assert {p.name for p in parsed.pages} == {p.name for p in model.report.pages}
    src_ids = {v.visual_id for p in model.report.pages for v in p.visuals}
    rt_ids = {v.visual_id for p in parsed.pages for v in p.visuals}
    assert rt_ids == src_ids


def test_hitl_placeholder_for_missing_dimension():
    """A chart with no canonical dimension gets a deterministic HITL Category
    placeholder (PBIR analogue of TMDL's BLANK()/HITL) and records the gap —
    never invents business data."""
    chart = Visual(visual_id="v_chart", visual_type="line_chart",
                   bound_measures=["Revenue"])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[chart])]),
    )
    out = pbir.emit(sm)
    vj = json.loads(out["R.Report/definition/pages/P1/visuals/v_chart/visual.json"])
    qs = vj["visual"]["query"]["queryState"]
    assert "Category" in qs and "Y" in qs
    cat = qs["Category"]["projections"][0]["field"]["Column"]["Expression"]["SourceRef"]["Entity"]
    assert cat == "_HITL"
    assert any("Category" in g and "v_chart" in g for g in pbir.hitl_gaps(sm))


def test_qualified_category_binds_declared_entity_and_property():
    chart = Visual(visual_id="v_chart", visual_type="line_chart",
                   bound_measures=["Revenue"], rows=["dim_date.CalendarYearMonth"])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[chart])]),
    )
    out = pbir.emit(sm)
    visual = json.loads(out["R.Report/definition/pages/P1/visuals/v_chart/visual.json"])
    column = visual["visual"]["query"]["queryState"]["Category"]["projections"][0]["field"]["Column"]
    assert column["Expression"]["SourceRef"]["Entity"] == "dim_date"
    assert column["Property"] == "CalendarYearMonth"


def test_qualified_slicer_binds_declared_entity_and_property():
    slicer = Visual(visual_id="slicer", visual_type="slicer",
                    slicer_field="dim_org.Region")
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[slicer])]),
    )
    visual = json.loads(
        pbir.emit(sm)["R.Report/definition/pages/P1/visuals/slicer/visual.json"]
    )
    column = visual["visual"]["query"]["queryState"]["Values"]["projections"][0]["field"]["Column"]
    assert column["Expression"]["SourceRef"]["Entity"] == "dim_org"
    assert column["Property"] == "Region"
    assert pbir.hitl_gaps(sm) == []


def test_unqualified_dimension_is_never_a_silent_hitl_placeholder():
    table = Visual(visual_id="detail", visual_type="table",
                   rows=["region"], bound_measures=["Revenue"])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[table])]),
    )
    assert any("unqualified field 'region'" in gap for gap in pbir.hitl_gaps(sm))


@pytest.mark.parametrize("bracket", CURATED_REPORTS, ids=lambda path: path.parent.name)
def test_curated_reports_have_no_connector_hitl_gaps(bracket):
    curated = from_bracket_file(bracket, KPIS)
    assert pbir.hitl_gaps(curated) == []


def test_exception_table_combines_declared_dimension_and_measure():
    queue = Visual(visual_id="exceptions", visual_type="exception_table",
                   bound_measures=["Unplanned Downtime %"], rows=["dim_asset.AssetName"])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[queue])]),
    )
    out = pbir.emit(sm)
    visual = json.loads(out["R.Report/definition/pages/P1/visuals/exceptions/visual.json"])
    assert visual["visual"]["visualType"] == "tableEx"
    projections = visual["visual"]["query"]["queryState"]["Values"]["projections"]
    assert "Column" in projections[0]["field"]
    assert "Measure" in projections[1]["field"]


def test_action_panel_is_native_textbox_with_governed_content():
    panel = Visual(
        visual_id="ActionPanel",
        visual_type="action_panel",
        title="C-M2.1 — Correct price leakage\nOwner: commercial lead",
    )
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[panel])]),
    )
    out = pbir.emit(sm)
    visual = json.loads(out["R.Report/definition/pages/P1/visuals/ActionPanel/visual.json"])
    assert visual["visual"]["visualType"] == "textbox"
    assert "query" not in visual["visual"]
    runs = visual["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"]
    assert "C-M2.1" in runs[0]["value"]
    assert not pbir.hitl_gaps(sm)


def test_measure_only_role_gets_measure_kind_placeholder():
    """An empty Measure-only role must get a Measure (not Column) placeholder, or
    the validator errors with PBIR_ROLE_KIND_MISMATCH."""
    card = Visual(visual_id="v_card", visual_type="card", bound_measures=[])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[card])]),
    )
    out = pbir.emit(sm)
    vj = json.loads(out["R.Report/definition/pages/P1/visuals/v_card/visual.json"])
    data_proj = vj["visual"]["query"]["queryState"]["Data"]["projections"][0]
    assert "Measure" in data_proj["field"]


def test_maxperrole_overflow_is_dropped_and_recorded():
    """waterfallChart.Y has maxPerRole 1; surplus measures are dropped (validator
    enforces PBIR_ROLE_MAX_EXCEEDED) and the loss is recorded as a gap."""
    wf = Visual(visual_id="v_wf", visual_type="waterfall",
                bound_measures=["A", "B", "C"])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[wf])]),
    )
    out = pbir.emit(sm)
    vj = json.loads(out["R.Report/definition/pages/P1/visuals/v_wf/visual.json"])
    assert len(vj["visual"]["query"]["queryState"]["Y"]["projections"]) == 1
    assert any("max 1 exceeded" in g for g in pbir.hitl_gaps(sm))


def test_governed_pvm_idiom_binds_single_supporting_measure(model):
    bridge = next(
        visual
        for page in model.report.pages
        for visual in page.visuals
        if visual.visual_id == "Main_2"
    )
    assert bridge.visual_type == "waterfall_chart"
    assert bridge.bound_measures == ["PVM Bridge Value"]
    helper = [
        measure
        for table in model.semantic.tables
        for measure in table.measures
        if measure.name == "PVM Bridge Value"
    ]
    assert len(helper) == 1
    helper_dsl = json.loads(helper[0].expressions["dsl"])
    assert helper_dsl["op"] == "selector_switch"
    assert any(case["value"]["name"] == "Plan Sales Amount" for case in helper_dsl["cases"])
    assert not any("Main_2" in gap and "max 1 exceeded" in gap for gap in pbir.hitl_gaps(model))


def test_unknown_visual_type_falls_back_and_is_recorded():
    odd = Visual(visual_id="v_x", visual_type="hologram3d", bound_measures=["M"])
    sm = CanonicalModel(
        semantic=SemanticModel(name="S"),
        report=ReportModel(name="R", pages=[ReportPage(name="P1", visuals=[odd])]),
    )
    out = pbir.emit(sm)
    vj = json.loads(out["R.Report/definition/pages/P1/visuals/v_x/visual.json"])
    assert vj["visual"]["visualType"] == "cardVisual"
    assert any("unknown visual_type" in g for g in pbir.hitl_gaps(sm))
