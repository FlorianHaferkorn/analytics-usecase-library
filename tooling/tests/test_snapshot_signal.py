"""Tests for ADR-0017 D2 value-verification (snapshot_signal — reuse of refcalc/Wirkungs-Loop)."""
from __future__ import annotations

from tooling.storyline import snapshot_signal
from tooling.storyline.score_insights import rank_storyline


def test_covered_use_cases_include_reference_data():
    covered = snapshot_signal.covered_use_cases()
    # I-4.1 reference data exists at least for these two (grows as reference data grows)
    assert "COM-001" in covered
    assert "SCM-002" in covered


def test_covered_use_case_returns_value_map():
    m = snapshot_signal.value_verified_map("COM-001")
    assert m is not None and isinstance(m, dict)
    # a covered use case has at least one KPI with a real computed value
    assert any(v is True for v in m.values())


def test_uncovered_use_case_is_uncomputed_not_false():
    # a use case with no reference data must be None (UNCOMPUTED), never a fabricated False-map
    assert snapshot_signal.value_verified_map("ZZ-999") is None


def test_value_verification_is_additive_never_downgrades():
    """The additive flag must not change score/verified gate — an uncovered UC keeps its headline."""
    story = {
        "use_case": "X",
        "causal_thread": None,
        "actions": [],
        "pages": [{"id": "p1", "visuals": [
            {"seq": 1, "kpi_id": "k1", "question": "Q?", "answer": "a few lanes drag OTIF",
             "so_what": "focus the worst lanes", "visual_type": "bar_chart_horizontal"},
        ]}],
    }
    exists, has_ref = {"k1"}, {"k1"}
    base = rank_storyline(story, exists, has_ref, value_verified=None)
    withvv = rank_storyline(story, exists, has_ref, value_verified={"k1": True})
    # score + verified identical; only the additive flag differs
    assert base["headline"]["score"] == withvv["headline"]["score"]
    assert base["headline"]["verified"] == withvv["headline"]["verified"] is True
    assert base["headline"]["value_verified"] is None          # UNCOMPUTED, not False
    assert withvv["headline"]["value_verified"] is True


def test_value_verified_breaks_ties_only():
    """Two equally-scored verified findings: the value-verified one wins the headline tie."""
    story = {
        "use_case": "X", "causal_thread": None, "actions": [],
        "pages": [{"id": "p1", "visuals": [
            {"seq": 1, "kpi_id": "k1", "question": "Q1?", "answer": "steady",
             "so_what": "", "visual_type": "card"},
            {"seq": 2, "kpi_id": "k2", "question": "Q2?", "answer": "steady",
             "so_what": "", "visual_type": "card"},
        ]}],
    }
    exists, has_ref = {"k1", "k2"}, {"k1", "k2"}
    r = rank_storyline(story, exists, has_ref, value_verified={"k1": False, "k2": True})
    # equal scores → the one with a real computed value leads
    assert r["headline"]["kpi_id"] == "k2"
