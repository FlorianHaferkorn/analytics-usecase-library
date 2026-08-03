"""Tests for the Boutique-Craft scorecard (K6 §9).

The validator runner is injected, so the scoring math is tested deterministically
without shelling out to the real gates.
"""
from __future__ import annotations

from tooling.report_quality.boutique_scorecard import load_rubric, score, wired


def _all_pass(*_a, **_k):
    return True


def _all_fail(*_a, **_k):
    return False


def test_only_wired_rules_are_scored():
    card = score(run_validator=_all_pass)
    scored = {r["id"] for r in card["rules"] if r["score"] is not None}
    WIRED = wired()
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
    # the scored knock-outs (BC-NARR-01/CHART-01/CHART-10/BRAND-01)
    assert set(card["knockouts_failed"]) == {"BC-CHART-01", "BC-CHART-10", "BC-NARR-01", "BC-BRAND-01"}


def test_coverage_is_partial_and_not_certifiable():
    card = score(run_validator=_all_pass)
    assert 0 < card["coverage_pct"] < 100          # only a subset of the 100-pt rubric
    assert card["certifiable"] is False            # judge rules pending → cannot certify


def test_global_weights_sum_to_100():
    card = score(run_validator=_all_pass)
    assert abs(sum(r["global_weight"] for r in card["rules"]) - 100.0) < 0.01


# ── Regression guard: the LIVE scorecard (real validators) must not degrade ──
# Ratchets boutique quality at the aggregate level — a change that breaks a wired
# rule, drops coverage, or fails a knock-out re-fires here. Raise the floors as
# more rules are wired; never lower them.
_MIN_SCORED_RULES = 15         # 13 structural + BC-NARR-03 + BC-LAYOUT-03 via spec-heuristic judge
_MIN_COVERAGE_PCT = 54.4


def test_live_scorecard_does_not_regress():
    from tooling.report_quality.judge import SpecHeuristicJudge
    card = score(judge=SpecHeuristicJudge())  # real validators + spec-heuristic judge
    assert card["scored_rules"] >= _MIN_SCORED_RULES, card["scored_rules"]
    assert card["coverage_pct"] >= _MIN_COVERAGE_PCT, card["coverage_pct"]
    # every scored rule currently passes on ALUCA — no silent breakage
    assert card["structural_score_pct"] == 100.0, card["structural_score_pct"]
    assert card["knockouts_failed"] == [], card["knockouts_failed"]
