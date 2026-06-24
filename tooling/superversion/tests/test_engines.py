"""Tests for the gov/eng/arch engine seam + Beta engines (task I-5.3).

DoD: each engine has a standalone smoke (runs against a bare CanonicalModel) and
integrates via the registry; thin engines are labeled Beta (never 'ready'); an
engine can be disabled (rollback).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Measure,
    Relationship,
    ReportModel,
    Role,
    SemanticModel,
    Table,
)
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import engines
from tooling.superversion.layer_tools.engines import base, cli

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
ENGINE_IDS = {"gov", "dataarch", "dataeng"}


def _model():
    return from_bracket_file(COM001, KPIS)


def test_three_engines_registered_and_beta():
    assert ENGINE_IDS <= set(engines.available())
    for eid in ENGINE_IDS:
        assert base.get(eid).status == "beta", "Beta stubs must never be labeled ready (Ehrlichkeit v3)"


@pytest.mark.parametrize("eid", sorted(ENGINE_IDS))
def test_engine_standalone_smoke(eid):
    """Each engine runs against a bare model and returns a well-formed report."""
    report = engines.run(eid, _model(), "ingest")
    assert report.engine_id == eid
    assert report.status == "beta"
    assert report.ok  # Beta engines emit warn/info, not errors
    assert isinstance(report.findings, list)


@pytest.mark.parametrize("eid", sorted(ENGINE_IDS))
def test_engine_deterministic(eid):
    m = _model()
    r1, r2 = engines.run(eid, m, "ingest"), engines.run(eid, m, "ingest")
    assert r1.findings == r2.findings


def test_gov_flags_undocumented_and_missing_roles():
    m = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[Table(name="f", measures=[Measure(name="M")])]),
        report=ReportModel(name="R"),
    )
    codes = {f.code for f in engines.run("gov", m, "ingest").findings}
    assert "GOV_MEASURE_UNDOCUMENTED" in codes
    assert "GOV_NO_ROLES" in codes


def test_gov_greenfield_mode_adds_finding():
    m = CanonicalModel(semantic=SemanticModel(name="S", roles=[Role(name="r")]),
                       report=ReportModel(name="R"))
    codes = {f.code for f in engines.run("gov", m, "greenfield").findings}
    assert "GOV_GREENFIELD" in codes


def test_dataarch_flags_no_relationships_and_naming():
    m = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[Table(name="sales"), Table(name="dates")]),
        report=ReportModel(name="R"),
    )
    codes = {f.code for f in engines.run("dataarch", m, "ingest").findings}
    assert "ARCH_NO_RELATIONSHIPS" in codes
    assert "ARCH_TABLE_NAMING" in codes
    # With a relationship present, the no-relationships warning disappears.
    m2 = CanonicalModel(
        semantic=SemanticModel(name="S",
                               tables=[Table(name="fact_a"), Table(name="dim_b")],
                               relationships=[Relationship("fact_a", "b_id", "dim_b", "id")]),
        report=ReportModel(name="R"),
    )
    codes2 = {f.code for f in engines.run("dataarch", m2, "ingest").findings}
    assert "ARCH_NO_RELATIONSHIPS" not in codes2
    assert "ARCH_TABLE_NAMING" not in codes2


def test_dataeng_is_explicit_stub():
    codes = {f.code for f in engines.run("dataeng", _model(), "ingest").findings}
    assert "ENG_STUB" in codes


def test_disabled_engine_rollback():
    base.register(base.EngineAdapter(id="gov", label="x", run=lambda c, m: [], status="disabled"),
                  replace=True)
    try:
        report = engines.run("gov", _model(), "ingest")
        assert report.status == "disabled" and report.findings == []
    finally:
        # restore the real gov engine so other tests are unaffected
        from tooling.superversion.layer_tools.engines import gov_engine
        base.register(base.EngineAdapter(id="gov", label="Governance audit (Beta)",
                                         run=gov_engine.run, status="beta"), replace=True)


def test_unsupported_mode_raises():
    with pytest.raises(base.EngineContractError):
        engines.run("gov", _model(), "nonsense")  # type: ignore[arg-type]


def test_cli_all_green(capsys):
    assert cli.main(["all", str(COM001)]) == 0
    out = capsys.readouterr().out
    assert "gov [beta]" in out and "dataarch [beta]" in out and "dataeng [beta]" in out


def test_cli_missing_bracket():
    assert cli.main(["gov", str(REPO / "nope.yaml")]) == 1
