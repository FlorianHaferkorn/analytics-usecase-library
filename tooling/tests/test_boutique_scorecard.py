"""Tests for the Boutique-Craft scorecard (K6 §9).

The validator runner is injected, so the scoring math is tested deterministically
without shelling out to the real gates.
"""
from __future__ import annotations

from tooling.report_quality.boutique_scorecard import WIRED, load_rubric, score


def _all_pass(*_a, **_k):
    return True


def _all_fail(*_a, **_k):
    return False


def test_only_wired_rules_are_scored():
    card = score(run_validator=_all_pass)
    scored = {r["id"] for r in card["rules"] if r["score"] is not None}
    assert scored == set(WIRED)
    assert card["scored_rules"] == len(WIRED)
    assert card["total_rules"] == sum(len(d["rules"]) for d in load_rubric()["dimensions"])


def test_all_pass_gives_full_subset_score():
    card = score(run_validator=_all_pass)
    assert card["structural_score_pct"] == 100.0
    assert card["knockouts_failed"] == []


def test_failing_knockout_is_surfaced():
    card = score(run_validator=_all_fail)
    assert card["structural_score_pct"] == 0.0
    # BC-CHART-01, BC-CHART-10, BC-NARR-01 are the scored knock-outs
    assert set(card["knockouts_failed"]) == {"BC-CHART-01", "BC-CHART-10", "BC-NARR-01"}


def test_coverage_is_partial_and_not_certifiable():
    card = score(run_validator=_all_pass)
    assert 0 < card["coverage_pct"] < 100          # only a subset of the 100-pt rubric
    assert card["certifiable"] is False            # judge rules pending → cannot certify


def test_global_weights_sum_to_100():
    card = score(run_validator=_all_pass)
    assert abs(sum(r["global_weight"] for r in card["rules"]) - 100.0) < 0.01
