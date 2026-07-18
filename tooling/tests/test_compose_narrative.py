"""Tests for ADR-0017 Stage-2 composition (D3 template shapes + D4 fallback)."""
from __future__ import annotations

from pathlib import Path

from tooling.storyline.compose_narrative import check_drift, compose, compose_all, select_shape

REPO = Path(__file__).resolve().parents[2]

_VALID_SHAPES = {"driver_lever", "concentration", "trajectory_vs_plan", "verdict", "fallback"}


def test_shape_selection():
    story_driver = {"causal_thread": {"driver": "a", "target": "b"}, "actions": ["X-1"]}
    assert select_shape({"dims": {"depth": 0.7, "specificity": 0.2}, "answer": "x"}, story_driver) == "driver_lever"
    assert select_shape({"dims": {"depth": 0.1, "specificity": 0.6}, "answer": "x"}, {}) == "concentration"
    assert select_shape({"dims": {"depth": 0.1, "specificity": 0.1}, "answer": "below target now"}, {}) == "trajectory_vs_plan"
    assert select_shape({"dims": {"depth": 0.1, "specificity": 0.1}, "answer": "steady"}, {}) == "verdict"
    assert select_shape(None, {}) == "fallback"


def test_fallback_uses_static_big_idea():
    story = {"use_case": "X", "strategic_kpi": "k", "pages": [], "actions": []}
    ranked = {"headline": None, "pages": []}
    r = compose(story, ranked, {"k": "K"}, static_big_idea="Human-curated floor.")
    assert r["shape"] == "fallback" and r["fallback_used"] and r["big_idea"] == "Human-curated floor."
    # no static → UNCOMPUTED marker, never a fabricated claim
    r2 = compose(story, ranked, {"k": "K"}, static_big_idea=None)
    assert "UNCOMPUTED" in r2["big_idea"] and not r2["verified"]


def test_drift_check_reconciles_with_static_field_never_writes():
    """#4 reconciliation: compose proposes; the bracket big_idea stays the single rendered source."""
    rows = check_drift(None)
    assert len(rows) >= 17
    valid = {"agree", "drift", "fallback", "missing"}
    for r in rows:
        assert r["status"] in valid
        # a 'drift' row must actually differ; 'agree' must actually match — the check must be real
        if r["status"] == "drift":
            assert r["composed"].strip() != (r["static"] or "").strip()
        if r["status"] == "agree":
            assert r["composed"].strip() == r["static"].strip()


def test_every_use_case_composes_a_big_idea():
    results = compose_all(None)
    assert len(results) >= 17
    for r in results:
        assert r["shape"] in _VALID_SHAPES
        assert r["big_idea"] and isinstance(r["big_idea"], str)
        # a verified compose must cite the finding it was built from (traceability)
        if r["verified"]:
            assert r["source"] and r["source"]["kpi_id"] is not None or r["source"] is not None
