"""eval.wirkung — Action → KPI-Snapshot-Delta → Attribution (task I-8.2, ADR-0009).

Deterministic, honest effect-tracking for the Wirkungs-Loop. Given an ActionEvent (which
references a governed action-code's ``outcome_kpis``) and two KPI snapshots (t0 = before,
t1 = after the impact window), compute an AttributionRecord per outcome-KPI.

Honesty (ADR-0009 / Ehrlichkeit v3), enforced here:
  - **missing ≠ zero**: a missing snapshot value → status ``uncomputed``, never a 0 effect.
  - **association ≠ causation**: ``before_after`` carries an explicit "temporal coincidence,
    not causal" note; ``diff_in_diff``/``holdout`` need a control and return ``uncomputed``
    (geplant) when none is supplied — never silently degrade to before/after.
  - **deterministic**: pure functions; same snapshots → same records (no clock/IO/RNG).

Snapshots come from the **governed** KPI computation (`refcalc` over reference data), so the
loop never re-defines KPI meaning (Golden Thread). The store/UI surfacing is I-8.2-followup.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from tooling.superversion.eval import refcalc, refdata

Method = Literal["before_after", "diff_in_diff", "holdout"]
Status = Literal["computed", "uncomputed"]

# KPI value at a point in time; None = not measured (UNCOMPUTED, never assumed 0).
KpiSnapshot = dict[str, Optional[float]]


@dataclass(frozen=True)
class ActionEvent:
    """A triggered action instance referencing a governed action-code."""
    action_code_id: str
    outcome_kpis: list[str]
    scope: str = ""


@dataclass(frozen=True)
class AttributionRecord:
    action_code_id: str
    kpi_id: str
    method: Method
    status: Status
    t0: Optional[float] = None
    t1: Optional[float] = None
    delta: Optional[float] = None
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "action_code_id": self.action_code_id, "kpi_id": self.kpi_id,
            "method": self.method, "status": self.status,
            "t0": self.t0, "t1": self.t1, "delta": self.delta, "note": self.note,
        }


def snapshot_via_refcalc(use_case: str) -> KpiSnapshot:
    """A KPI snapshot computed from governed reference data via `refcalc` (one source of truth)."""
    exp = refdata.load_expectations(use_case)
    dataset = refdata.load_dataset(exp.dataset)
    snap: KpiSnapshot = {}
    for kpi in exp.kpis:
        if kpi.kpi_id:
            snap[kpi.kpi_id] = refcalc.recompute(kpi.formula, dataset.rows)
    return snap


def _attribute_one(
    action_id: str, kpi: str, method: Method,
    t0: KpiSnapshot, t1: KpiSnapshot,
    control_t0: Optional[KpiSnapshot], control_t1: Optional[KpiSnapshot],
) -> AttributionRecord:
    v0, v1 = t0.get(kpi), t1.get(kpi)
    base = dict(action_code_id=action_id, kpi_id=kpi, method=method)
    if v0 is None or v1 is None:
        miss = "t0" if v0 is None else "t1"
        return AttributionRecord(**base, status="uncomputed", t0=v0, t1=v1,
                                 note=f"UNCOMPUTED: {miss} snapshot missing (missing ≠ zero)")

    if method == "before_after":
        return AttributionRecord(**base, status="computed", t0=v0, t1=v1, delta=v1 - v0,
                                 note="temporal coincidence, not causal (no control segment)")

    # diff_in_diff / holdout both need a control segment.
    if control_t1 is None or (method == "diff_in_diff" and control_t0 is None):
        return AttributionRecord(**base, status="uncomputed", t0=v0, t1=v1,
                                 note=f"UNCOMPUTED: {method} needs a control segment (geplant)")
    c1 = control_t1.get(kpi)
    if c1 is None or (method == "diff_in_diff" and control_t0.get(kpi) is None):  # type: ignore[union-attr]
        return AttributionRecord(**base, status="uncomputed", t0=v0, t1=v1,
                                 note=f"UNCOMPUTED: control snapshot missing for {kpi}")
    if method == "diff_in_diff":
        c0 = control_t0.get(kpi)  # type: ignore[union-attr]
        delta = (v1 - v0) - (c1 - c0)  # type: ignore[operator]
        return AttributionRecord(**base, status="computed", t0=v0, t1=v1, delta=delta,
                                 note="difference-in-differences vs control")
    # holdout: treated minus untreated (holdout) level at t1.
    return AttributionRecord(**base, status="computed", t0=v0, t1=v1, delta=v1 - c1,
                             note="holdout: treated minus control at t1")


def attribute(
    action: ActionEvent, t0: KpiSnapshot, t1: KpiSnapshot, *,
    method: Method = "before_after",
    control_t0: Optional[KpiSnapshot] = None, control_t1: Optional[KpiSnapshot] = None,
) -> list[AttributionRecord]:
    """Attribute the KPI effect of one action across its outcome_kpis (deterministic)."""
    return [
        _attribute_one(action.action_code_id, kpi, method, t0, t1, control_t0, control_t1)
        for kpi in action.outcome_kpis
    ]
