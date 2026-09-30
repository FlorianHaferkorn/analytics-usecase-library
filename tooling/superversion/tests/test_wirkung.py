"""Tests for the Wirkungs-Loop effect-tracking engine (I-8.2, ADR-0009).

Covers the honesty invariants (missing≠zero; association≠causation; control required
for diff_in_diff/holdout), determinism, snapshots-from-governed-refcalc, and the
DoD: for 1 action the KPI effect is traceably attributed.
"""
from __future__ import annotations

from tooling.superversion.eval import refdata
from tooling.superversion.eval.wirkung import (
    ActionEvent,
    attribute,
    snapshot_via_refcalc,
)


def test_before_after_delta_is_labeled_non_causal():
    a = ActionEvent("X-1", ["k.a"])
    [rec] = attribute(a, {"k.a": 100.0}, {"k.a": 130.0})
    assert rec.status == "computed"
    assert rec.delta == 30.0
    assert "not causal" in rec.note


def test_missing_snapshot_is_uncomputed_not_zero():
    a = ActionEvent("X-1", ["k.a"])
    [rec] = attribute(a, {"k.a": 100.0}, {})  # t1 missing
    assert rec.status == "uncomputed"
    assert rec.delta is None  # NOT 0.0
    assert "missing" in rec.note.lower()


def test_diff_in_diff_needs_control_else_uncomputed():
    a = ActionEvent("X-1", ["k.a"])
    [no_ctrl] = attribute(a, {"k.a": 100.0}, {"k.a": 130.0}, method="diff_in_diff")
    assert no_ctrl.status == "uncomputed" and "control" in no_ctrl.note

    [rec] = attribute(
        a, {"k.a": 100.0}, {"k.a": 130.0}, method="diff_in_diff",
        control_t0={"k.a": 100.0}, control_t1={"k.a": 110.0},
    )
    # treated +30, control +10 → attributed +20
    assert rec.status == "computed" and rec.delta == 20.0


def test_holdout_needs_control_t1():
    a = ActionEvent("X-1", ["k.a"])
    [u] = attribute(a, {"k.a": 100.0}, {"k.a": 130.0}, method="holdout")
    assert u.status == "uncomputed"
    [rec] = attribute(a, {"k.a": 100.0}, {"k.a": 130.0}, method="holdout", control_t1={"k.a": 115.0})
    assert rec.status == "computed" and rec.delta == 15.0  # 130 - 115


def test_deterministic():
    a = ActionEvent("X-1", ["k.a", "k.b"])
    t0, t1 = {"k.a": 1.0, "k.b": 2.0}, {"k.a": 3.0, "k.b": 2.0}
    assert [r.to_dict() for r in attribute(a, t0, t1)] == [r.to_dict() for r in attribute(a, t0, t1)]


def test_snapshot_via_refcalc_matches_governed_values():
    # Snapshot is computed from governed reference data — equals the checked-in expected values.
    uc = "COM-001"
    snap = snapshot_via_refcalc(uc)
    exp = refdata.load_expectations(uc)
    for kpi in exp.kpis:
        if kpi.kpi_id:
            assert abs(snap[kpi.kpi_id] - kpi.value) <= max(kpi.tolerance, 1e-9)


def test_one_action_effect_traceably_attributed():
    """DoD: for 1 action the KPI effect is traceably attributed (end-to-end on governed data)."""
    t0 = snapshot_via_refcalc("COM-001")
    kpi = "KPI-COM-005"
    assert kpi in t0 and t0[kpi] is not None
    # A later snapshot where the action moved the KPI by +10%.
    t1 = dict(t0)
    t1[kpi] = t0[kpi] * 1.10

    action = ActionEvent("COM-ACT-DEMO", [kpi], scope="all")
    [rec] = attribute(action, t0, t1)
    assert rec.status == "computed"
    assert abs(rec.delta - (t0[kpi] * 0.10)) < 1e-6
    assert rec.action_code_id == "COM-ACT-DEMO" and rec.kpi_id == kpi
