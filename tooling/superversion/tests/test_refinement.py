"""Tests for the Wirkungs-Loop Refinement-Trigger (I-8.3, ADR-0009 §5).

Feedback = reviewable proposals only (never auto-mutate). Honesty: no proposal from
uncomputed/unscalable records; before_after stays association-not-causation.
"""
from __future__ import annotations

from tooling.superversion.eval.refinement import derive_refinements
from tooling.superversion.eval.wirkung import AttributionRecord


def _rec(delta, t0, status="computed", kpi="k.a"):
    return AttributionRecord(
        action_code_id="X-1", kpi_id=kpi, method="before_after", status=status,
        t0=t0, t1=(None if t0 is None or delta is None else t0 + delta), delta=delta,
    )


def test_near_zero_delta_triggers_no_effect_review():
    [p] = derive_refinements([_rec(0.5, 100.0)])  # rel = 0.5%
    assert p.trigger == "no_effect"
    assert p.status == "pending_review"  # proposal only, never applied
    assert "prüfen" in p.rationale


def test_large_delta_triggers_material_effect():
    [p] = derive_refinements([_rec(25.0, 100.0)])  # rel = 25%
    assert p.trigger == "material_effect"
    assert "Kausalität" in p.rationale  # explicitly asks to verify causality


def test_moderate_delta_yields_no_proposal():
    assert derive_refinements([_rec(5.0, 100.0)]) == []  # rel = 5% (between 1% and 10%)


def test_uncomputed_record_yields_no_proposal():
    # missing ≠ trigger: an UNCOMPUTED effect produces no ontology signal.
    assert derive_refinements([_rec(None, 100.0, status="uncomputed")]) == []


def test_zero_baseline_yields_no_proposal():
    # cannot scale a relative change off a 0 baseline → no proposal (honest).
    assert derive_refinements([_rec(5.0, 0.0)]) == []


def test_deterministic_and_multi():
    recs = [_rec(0.2, 100.0, kpi="k.a"), _rec(50.0, 100.0, kpi="k.b"), _rec(5.0, 100.0, kpi="k.c")]
    r1 = [p.to_dict() for p in derive_refinements(recs)]
    r2 = [p.to_dict() for p in derive_refinements(recs)]
    assert r1 == r2
    assert {p["kpi_id"] for p in r1} == {"k.a", "k.b"}  # k.c moderate → no proposal
