"""Tests for the COMP*-DSGVO compliance gate (task I-4.4).

DoD: a PII use case (personal_data: true) whose model has no row-level security
turns the gate red; PII WITH RLS passes; a missing classification is an advisory
WARN, not a failure; the --warn rollback downgrades.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    ReportModel,
    Role,
    RoleTablePermission,
    SemanticModel,
)
from tooling.superversion.eval import comp_gate
from tooling.superversion.from_aluca import from_bracket_file

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
XD002 = REPO / "core/usecases/core/XD-002_Resource_Utilization/UseCase_Bracket.yaml"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"


def _model(*, with_rls: bool) -> CanonicalModel:
    roles = []
    if with_rls:
        roles = [Role(name="org_role",
                      table_permissions=[RoleTablePermission(table="fact_sales",
                                                             filter_expression="[Region] = USERPRINCIPALNAME()")])]
    return CanonicalModel(
        semantic=SemanticModel(name="M", roles=roles),
        report=ReportModel(name="R"),
    )


def test_pii_without_rls_fails():
    dp = {"personal_data": True, "personal_data_categories": ["performance_data"]}
    findings = comp_gate.check_compliance("XD-002", dp, _model(with_rls=False))
    assert any(f.kind == comp_gate.KIND_PII_NO_RLS for f in findings)
    with pytest.raises(comp_gate.CompGateError):
        comp_gate.assert_compliance("XD-002", dp, _model(with_rls=False))


def test_pii_with_rls_passes():
    dp = {"personal_data": True, "personal_data_categories": ["performance_data"]}
    findings = comp_gate.assert_compliance("XD-002", dp, _model(with_rls=True))
    assert not findings


def test_no_pii_passes():
    dp = {"personal_data": False}
    assert comp_gate.assert_compliance("COM-001", dp, _model(with_rls=False)) == []


def test_unclassified_is_warn_not_fail():
    findings = comp_gate.assert_compliance("X", {}, _model(with_rls=False))  # no personal_data key
    assert findings and findings[0].kind == comp_gate.KIND_UNCLASSIFIED
    assert findings[0].severity() == "warn"


def test_warn_only_rollback_downgrades():
    dp = {"personal_data": True}
    # no raise under warn_only, even though PII-without-RLS would be an error
    findings = comp_gate.assert_compliance("XD-002", dp, _model(with_rls=False), warn_only=True)
    assert any(f.kind == comp_gate.KIND_PII_NO_RLS for f in findings)


def test_real_xd002_pii_without_rls_is_red():
    """XD-002 declares personal_data: true; its governance roles carry no RLS
    filter → the gate must go red on the real generated model."""
    dp = comp_gate.load_data_protection(XD002)
    assert dp and dp.get("personal_data") is True
    model = from_bracket_file(XD002, KPIS)
    assert not comp_gate.model_has_rls(model)
    with pytest.raises(comp_gate.CompGateError):
        comp_gate.assert_compliance("XD-002", dp, model)


def test_real_com001_no_pii_is_green():
    dp = comp_gate.load_data_protection(COM001)
    assert dp and dp.get("personal_data") is False
    model = from_bracket_file(COM001, KPIS)
    assert comp_gate.assert_compliance("COM-001", dp, model) == []


def test_cli_green_over_gated_ucs(capsys):
    """All gated universal UCs are personal_data: false → gate is green in CI."""
    assert comp_gate.main([]) == 0
    assert "no error-severity findings" in capsys.readouterr().out
