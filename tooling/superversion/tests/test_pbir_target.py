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
from tooling.superversion.targets import base
from tooling.superversion.targets import pbir  # noqa: F401 — registers the "pbir" adapter

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
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


def test_every_visual_has_querystate_with_projections(model):
    """The validator errors on a visual without queryState (PBIR_QUERY_STATE_MISSING)
    or with an empty required role; assert the structure that prevents both."""
    out = pbir.emit(model)
    visual_files = [c for path, c in out.items() if path.endswith("/visual.json")]
    assert visual_files
    for content in visual_files:
        vj = json.loads(content)
        query_state = vj["visual"]["query"]["queryState"]
        assert query_state, "queryState must be non-empty"
        for role, body in query_state.items():
            assert body["projections"], f"role {role} has no projection"


@pytest.mark.skipif(shutil.which(CLI) is None, reason="powerbi-report-author CLI not installed")
def test_official_validator_zero_errors(model, tmp_path):
    """I-3.3 gate: the official MS validator reports 0 errors on the emitted report."""
    base.render("pbir", model, tmp_path)
    report_dir = tmp_path / f"{model.report.name}.Report"
    proc = subprocess.run(
        [CLI, "validate", str(report_dir), "--no-schema", "--format", "json"],
        capture_output=True, text=True, timeout=120,
    )
    data = json.loads(proc.stdout)["data"]
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
