"""Tests for the Boutique-Craft judge harness (K6 §9, judge half).

The spec-heuristic judge is deterministic, so it's tested directly; the render-only
rules must abstain (never fabricate a verdict).
"""
from __future__ import annotations

from tooling.report_quality.judge import (
    JudgeContext, SpecHeuristicJudge, Verdict, judge_rules, load_rubric, run_judges,
)


def test_judge_rules_are_the_check_judge_ones():
    rules = judge_rules(load_rubric())
    ids = {r["id"] for r in rules}
    assert "BC-NARR-03" in ids and "BC-COLOR-01" in ids
    assert all(r["check"] == "judge" for r in rules)


def test_spec_heuristic_scores_narr_03():
    v = SpecHeuristicJudge().evaluate("BC-NARR-03", JudgeContext())
    assert v.score == 1.0 and v.method == "spec_heuristic"


def test_render_only_rules_abstain_not_fabricate():
    j = SpecHeuristicJudge()
    for rid in ("BC-COLOR-01", "BC-CHART-03", "BC-LAYOUT-03"):
        v = j.evaluate(rid, JudgeContext())
        assert v.score is None and v.method == "abstain", rid


def test_narr_03_breaks_when_so_what_missing(tmp_path):
    # a synthetic corpus with a message but no so_what → chain broken
    (tmp_path / "core/usecases/x").mkdir(parents=True)
    (tmp_path / "core/usecases/x/UseCase_Bracket.yaml").write_text(
        "id: X\nux_layout_rules:\n  page_1_summary:\n    component_30s:\n"
        "    - slot_id: Main_1\n      message: 'GM fell 12% vs plan'\n",
        encoding="utf-8",
    )
    v = SpecHeuristicJudge().evaluate("BC-NARR-03", JudgeContext(repo=tmp_path))
    assert v.score == 0.0 and "so-what" in v.rationale


def test_run_judges_covers_all_and_keeps_abstentions():
    verdicts = run_judges(load_rubric(), JudgeContext(), SpecHeuristicJudge())
    assert len(verdicts) == len(judge_rules(load_rubric()))
    assert any(v.score is not None for v in verdicts.values())   # ≥1 decided
    assert any(v.score is None for v in verdicts.values())       # ≥1 honest abstain


def test_verdict_shape():
    v = Verdict("BC-X", 0.5, "spec_heuristic", "partial")
    assert (v.rule_id, v.score, v.method) == ("BC-X", 0.5, "spec_heuristic")
