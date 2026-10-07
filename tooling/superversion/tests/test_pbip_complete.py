"""A complete, openable PBIP for SCM-002 (contract binding + TMDL item frame, 07.10.2026).

Before: the Superversion chain wrote four measure-only TMDL files (no `definition.pbism`,
no `model.tmdl`/`database.tmdl`, no dimensions, no relationships, no partitions) and the
report carried four HITL placeholders. These tests pin what the data contract and the
governed idiom library can answer — and that what they cannot answer stays a visible,
reasoned placeholder instead of an invented field.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tooling.superversion import _meridian_vendor, contract_binding, e2e_smoke
from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Measure,
    ReportModel,
    ReportPage,
    SemanticModel,
    Table,
    Visual,
)
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base, pbir, tmdl  # noqa: F401 — registers adapters

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
SCM002 = REPO / "core/usecases/core/SCM-002_Supply_Reliability_OTIF/UseCase_Bracket.yaml"
NAME = "SCM-002_Supply_Reliability_OTIF"

EXPECTED_FILES = {
    f"{NAME}.SemanticModel/.platform",
    f"{NAME}.SemanticModel/definition.pbism",
    f"{NAME}.SemanticModel/definition/database.tmdl",
    f"{NAME}.SemanticModel/definition/model.tmdl",
    f"{NAME}.SemanticModel/definition/relationships.tmdl",
    *(f"{NAME}.SemanticModel/definition/tables/{t}.tmdl" for t in (
        "_Measures", "fact_fulfillment", "fact_stockout", "fact_warehouse",
        "dim_date", "dim_org", "dim_product", "dim_lane")),
    f"{NAME}.Report/.platform",
    f"{NAME}.Report/definition.pbir",
    f"{NAME}.Report/StaticResources/SharedResources/BaseThemes/CY26SU10.json",
    f"{NAME}.Report/definition/version.json",
    f"{NAME}.Report/definition/report.json",
    f"{NAME}.Report/definition/pages/pages.json",
    f"{NAME}.Report/definition/pages/page_1_summary/page.json",
    f"{NAME}.Report/definition/pages/page_2_execution/page.json",
    *(f"{NAME}.Report/definition/pages/page_1_summary/visuals/{v}/visual.json"
      for v in ("KPI_Cards", "Main_1", "Main_2", "Slicer_Date")),
    *(f"{NAME}.Report/definition/pages/page_2_execution/visuals/{v}/visual.json"
      for v in ("Detail_Matrix", "Slicer_Pane")),
}


@pytest.fixture(scope="module")
def bound():
    model = from_bracket_file(SCM002, KPIS)
    return contract_binding.bind_bracket_file(model, SCM002)


def _emit_all(model: CanonicalModel) -> dict[str, str]:
    return {**base.get("tmdl").emit(model), **base.get("pbir").emit(model)}


def test_scm002_emits_the_complete_file_list(bound):
    model, _ = bound
    assert set(_emit_all(model)) == EXPECTED_FILES


def test_scm002_star_schema_from_the_contract(bound):
    model, _ = bound
    sm = model.semantic
    rels = {(r.from_table, r.from_column, r.to_table, r.to_column) for r in sm.relationships}
    assert len(rels) == 9
    assert ("fact_fulfillment", "LaneKey", "dim_lane", "LaneKey") in rels
    # target_state key: not delivered, so no dimension and no relationship
    assert not any(r.to_table == "dim_carrier_lane" for r in sm.relationships)
    assert contract_binding.dangling_references(model) == []


def test_scm002_measure_column_name_clash_moves_to_measures(bound):
    model, findings = bound
    tables = {t.name: t for t in model.semantic.tables}
    assert "Penalty Amount" in {m.name for m in tables["_Measures"].measures}
    assert "Penalty Amount" not in {m.name for m in tables["fact_fulfillment"].measures}
    assert any(f.kind == "moved" and "Penalty Amount" in f.detail for f in findings)


def test_scm002_only_the_unanswerable_placeholders_remain(bound):
    """Before: 4 HITL placeholders. Main_1's time axis comes from the line idiom
    (category type `date`) + the only date column; `customer` is the only dimension
    column of that name (dim_org.Customer). `lane` (no such column — dim_carrier_lane
    is target_state) and the Slicer_Pane field (the manifest governs none) stay."""
    model, findings = bound
    gaps = pbir.hitl_gaps(model)
    assert len(gaps) == 2, gaps
    assert any("'lane'" in g for g in gaps)
    assert any("Slicer_Pane" in g for g in gaps)
    resolved = [f.detail for f in findings if f.kind == "resolved"]
    assert any("Main_1" in d and "dim_date.Date" in d for d in resolved)
    assert any("'customer' → dim_org.Customer" in d for d in resolved)
    # the conformed-dimension deviation is reported, not silently absorbed
    assert any(f.kind == "widened" and "dim_org.OrgName" in f.detail for f in findings)


def test_scm002_every_report_field_resolves_in_the_model(bound, tmp_path):
    model, _ = bound
    base.render("pbir", model, tmp_path)
    dangling, placeholders = e2e_smoke.unresolved_bindings(model, tmp_path / f"{NAME}.Report")
    assert dangling == []
    assert placeholders == 2


def test_scm002_full_model_round_trips_through_the_vendored_parser(bound, tmp_path):
    model, _ = bound
    base.render("tmdl", model, tmp_path)
    parser = _meridian_vendor._load_module(
        "_pbip_complete_parser", _meridian_vendor.VENDOR_DIR / "core/pbi_engine/parsers/tmdl_parser.py")
    parsed = parser.parse_model(tmp_path / f"{NAME}.SemanticModel")
    assert len(parsed.tables) == 8
    assert len(parsed.relationships) == 9
    assert parsed.compatibility_level == 1702
    assert all(t.has_partition for t in parsed.tables)


def test_scm002_emission_is_byte_identical_twice():
    first = _emit_all(contract_binding.bind_bracket_file(from_bracket_file(SCM002, KPIS), SCM002)[0])
    second = _emit_all(contract_binding.bind_bracket_file(from_bracket_file(SCM002, KPIS), SCM002)[0])
    assert first == second


@pytest.mark.skipif(shutil.which("powerbi-report-author") is None,
                    reason="official powerbi-report-author CLI not installed")
def test_scm002_report_passes_the_official_validator(bound, tmp_path):
    model, _ = bound
    base.render("pbir", model, tmp_path)
    proc = subprocess.run(
        [shutil.which("powerbi-report-author"), "validate", str(tmp_path / f"{NAME}.Report"),
         "--no-schema", "--format", "json"], capture_output=True, text=True, timeout=120)
    assert json.loads(proc.stdout)["data"]["errorCount"] == 0


# --- binding rules on a synthetic contract -------------------------------------------- #

_CONTRACT = textwrap.dedent("""\
    domain: test
    dimension:
      - name: dim_a
        columns:
          - {name: AKey, type: int, role: key}
          - {name: Region, type: text}
          - {name: Day, type: date}
      - name: dim_b
        columns:
          - {name: BKey, type: int, role: key}
          - {name: Region, type: text}
      - name: dim_future
        columns:
          - {name: FKey, type: int, role: key}
    fact:
      - name: fact_t
        columns:
          - {name: AKey, type: int, ref: dim_a}
          - {name: BKey, type: int, ref: dim_b}
          - {name: FKey, type: int, ref: dim_future, target_state: true}
          - {name: Amount, type: currency, agg: sum}
    """)


def _synthetic(fields: list[str], visual_type: str = "table") -> CanonicalModel:
    return CanonicalModel(
        semantic=SemanticModel(name="T", tables=[
            Table(name="fact_t", measures=[Measure(name="Amount"), Measure(name="Total")])]),
        report=ReportModel(name="T", pages=[ReportPage(name="p", visuals=[
            Visual(visual_id="v", visual_type=visual_type, columns=list(fields))])]),
    )


def test_ambiguous_unqualified_field_stays_a_gap(tmp_path):
    path = tmp_path / "test.yaml"
    path.write_text(_CONTRACT, encoding="utf-8")
    model, findings = contract_binding.bind(_synthetic(["region"]), path)
    assert model.report.pages[0].visuals[0].columns == ["region"]
    assert any(f.kind == "gap" and "ambiguous" in f.detail for f in findings)
    # target_state key → no dimension, no relationship
    assert {t.name for t in model.semantic.tables} == {"fact_t", "dim_a", "dim_b", "_Measures"}
    assert any(f.kind == "gap" and "target_state" in f.detail for f in findings)


def test_date_axis_only_for_date_idioms(tmp_path):
    path = tmp_path / "test.yaml"
    path.write_text(_CONTRACT, encoding="utf-8")
    line, _ = contract_binding.bind(_synthetic([], "line_chart"), path)
    assert line.report.pages[0].visuals[0].columns == ["dim_a.Day"]
    bar, findings = contract_binding.bind(_synthetic([], "bar_chart"), path)
    assert bar.report.pages[0].visuals[0].columns == []   # a ranking's category is a choice


def test_binding_does_not_mutate_its_input(tmp_path):
    path = tmp_path / "test.yaml"
    path.write_text(_CONTRACT, encoding="utf-8")
    src = _synthetic(["region"])
    contract_binding.bind(src, path)
    assert [t.name for t in src.semantic.tables] == ["fact_t"]
    assert src.semantic.tables[0].columns == []
