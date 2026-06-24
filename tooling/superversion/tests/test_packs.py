"""Tests for the tool-specific domain packs (task I-5.4).

DoD: ≥1 pack per platform (Official-First); API-dependent checks surfaced as
'geplant' (no silent drop); generic rules remain (disabling a pack = rollback);
per-pack test.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Column,
    Measure,
    ReportModel,
    SemanticModel,
    Table,
)
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import packs
from tooling.superversion.layer_tools.packs import base, cli

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
PACK_IDS = {"unity_catalog", "purview", "dbt"}


def _model():
    return from_bracket_file(COM001, KPIS)


def test_one_pack_per_platform_registered():
    assert PACK_IDS <= set(packs.available())
    platforms = {base.get(p).platform for p in PACK_IDS}
    assert len(platforms) == 3  # distinct platform per pack


@pytest.mark.parametrize("pid", sorted(PACK_IDS))
def test_pack_standalone_smoke(pid):
    report = packs.evaluate(pid, _model())
    assert report.pack_id == pid
    assert report.status == "active"
    assert report.ok  # packs emit warn/info, not errors


@pytest.mark.parametrize("pid", sorted(PACK_IDS))
def test_pack_deterministic(pid):
    m = _model()
    assert packs.evaluate(pid, m).findings == packs.evaluate(pid, m).findings


@pytest.mark.parametrize("pid", sorted(PACK_IDS))
def test_planned_checks_surfaced_not_dropped(pid):
    """Every pack must surface its API-dependent checks as PACK_PLANNED (no silent caps)."""
    pack = base.get(pid)
    assert pack.planned, f"pack '{pid}' declares no planned checks"
    planned = [f for f in packs.evaluate(pid, _model()).findings if f.code == "PACK_PLANNED"]
    assert len(planned) == len(pack.planned)


def test_unity_catalog_flags_naming_and_untyped():
    m = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[
            Table(name="FactSales", columns=[Column(name="amount")]),  # bad case + untyped
        ]),
        report=ReportModel(name="R"),
    )
    codes = {f.code for f in packs.evaluate("unity_catalog", m).findings}
    assert "UC_TABLE_NAMING" in codes
    assert "UC_COLUMN_TYPED" in codes
    # clean model: no naming/typing findings
    m2 = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[
            Table(name="fact_sales", columns=[Column(name="amount", data_type="decimal")]),
        ]),
        report=ReportModel(name="R"),
    )
    codes2 = {f.code for f in packs.evaluate("unity_catalog", m2).findings}
    assert "UC_TABLE_NAMING" not in codes2 and "UC_COLUMN_TYPED" not in codes2


def test_purview_flags_undescribed():
    m = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[
            Table(name="t", measures=[Measure(name="M")]),  # no descriptions
        ]),
        report=ReportModel(name="R"),
    )
    codes = {f.code for f in packs.evaluate("purview", m).findings}
    assert "PURVIEW_TABLE_DESCRIBED" in codes
    assert "PURVIEW_MEASURE_DESCRIBED" in codes


def test_dbt_flags_unlayered_models():
    m = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[Table(name="sales"), Table(name="stg_raw")]),
        report=ReportModel(name="R"),
    )
    findings = packs.evaluate("dbt", m).findings
    naming = [f for f in findings if f.code == "DBT_MODEL_NAMING"]
    assert len(naming) == 1 and "sales" in naming[0].detail  # only the unlayered one


def test_disabled_pack_rollback():
    real = base.get("dbt")
    base.register(base.Pack(id="dbt", platform="dbt", label="x", status="disabled"), replace=True)
    try:
        report = packs.evaluate("dbt", _model())
        assert report.status == "disabled" and report.findings == []
    finally:
        base.register(real, replace=True)  # restore the real pack for other tests


def test_unknown_pack_raises():
    with pytest.raises(KeyError):
        packs.evaluate("nope", _model())


def test_cli_all_green(capsys):
    assert cli.main(["all", str(COM001)]) == 0
    out = capsys.readouterr().out
    assert "unity_catalog" in out and "purview" in out and "dbt" in out
    assert "PACK_PLANNED" in out  # planned checks are visible in the CLI


def test_cli_missing_bracket():
    assert cli.main(["dbt", str(REPO / "nope.yaml")]) == 1
