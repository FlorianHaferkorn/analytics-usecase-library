"""Tests for the shared quality-scoring honesty contract (#3 unification)."""
from __future__ import annotations

from tooling.quality.verification_seam import ABSTAIN, is_abstain


def test_abstain_is_none_and_distinct_from_zero():
    assert ABSTAIN is None
    assert is_abstain(ABSTAIN)
    assert is_abstain(None)
    # a real 0.0 is a DECISION (fails / no grounding), never an abstention
    assert not is_abstain(0.0)
    assert not is_abstain(1.0)


def test_both_seams_import_the_same_sentinel():
    # score_insights (generation-side) and judge (QA-side) must use the ONE shared sentinel,
    # so the never-fabricate rule has a single definition.
    from tooling.storyline import score_insights
    from tooling.report_quality import judge
    assert score_insights.ABSTAIN is ABSTAIN
    assert judge.ABSTAIN is ABSTAIN


def test_score_insights_abstains_headline_when_nothing_verifies():
    from tooling.storyline.score_insights import rank_storyline
    story = {"use_case": "X", "causal_thread": None, "actions": [],
             "pages": [{"id": "p1", "visuals": [
                 {"seq": 1, "kpi_id": None, "question": "Q?", "answer": "steady",
                  "so_what": "", "visual_type": "card"}]}]}
    # kpi_id None + not a decomposition visual ⇒ grounding 0 ⇒ no verified finding ⇒ ABSTAIN
    r = rank_storyline(story, exists=set(), has_ref=set())
    assert r["headline"] is ABSTAIN
