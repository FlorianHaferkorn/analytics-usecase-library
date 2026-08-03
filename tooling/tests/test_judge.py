"""Tests for the Boutique-Craft judge harness (K6 §9, judge half).

The spec-heuristic judge is deterministic, so it's tested directly; the render-only
rules must abstain (never fabricate a verdict).
"""
from __future__ import annotations

from tooling.report_quality.judge import (
    JudgeContext, SpecHeuristicJudge, Verdict, judge_rules, load_rubric, run_judges,
)


def test_judge_rules_are_the_check_judge_ones():
    """Judge-Menge = `judge` **und** `both`.

    `both` kam am 03.08.2026 dazu, fuer zwei Regeln, die als `judge` deklariert waren,
    deren Urteil die Scorecard aber still verwarf, weil ein Validator verdrahtet war.
    Waere `both` hier nicht aufgenommen worden, haette die Aufwertung genau das
    bewirkt, was sie beheben soll: ein Urteil, das niemand einholt.
    """
    from tooling.report_quality.judge import JUDGE_KINDS

    rules = judge_rules(load_rubric())
    ids = {r["id"] for r in rules}
    assert "BC-NARR-03" in ids and "BC-COLOR-01" in ids
    assert {"BC-NARR-01", "BC-BRAND-02"} <= ids, "die `both`-Regeln fehlen in der Judge-Menge"
    assert all(r["check"] in JUDGE_KINDS for r in rules)


def test_spec_heuristic_scores_narr_03():
    v = SpecHeuristicJudge().evaluate("BC-NARR-03", JudgeContext())
    assert v.score == 1.0 and v.method == "spec_heuristic"


def test_spec_heuristic_scores_layout_03_hero_insight():
    """The hero-insight pattern is spec-decidable: every summary page leads with a
    single-lead component_3s hero, so the heuristic scores (never abstains)."""
    v = SpecHeuristicJudge().evaluate("BC-LAYOUT-03", JudgeContext())
    assert v.score == 1.0 and v.method == "spec_heuristic"


def test_layout_03_breaks_on_flat_hierarchy(tmp_path):
    # a page with no component_3s hero → flat hierarchy → fail
    (tmp_path / "core/usecases/x").mkdir(parents=True)
    (tmp_path / "core/usecases/x/UseCase_Bracket.yaml").write_text(
        "id: X\nux_layout_rules:\n  page_1_summary:\n    component_30s:\n"
        "    - slot_id: Main_1\n      message: 'GM fell 12% vs plan'\n",
        encoding="utf-8",
    )
    v = SpecHeuristicJudge().evaluate("BC-LAYOUT-03", JudgeContext(repo=tmp_path))
    assert v.score == 0.0 and "flat" in v.rationale


def test_render_only_rules_abstain_not_fabricate():
    j = SpecHeuristicJudge()
    for rid in ("BC-COLOR-01", "BC-CHART-03", "BC-CHART-06"):
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


# ── LLM backend seam (render-only half) ──────────────────────────────────────
from tooling.report_quality.judge import (  # noqa: E402
    LLMJudge, CompositeJudge, build_judge_prompt, parse_verdict, _rule_meta,
)


def test_prompt_builder_is_deterministic_and_complete():
    p = build_judge_prompt(_rule_meta("BC-COLOR-01"), "<render>")
    assert "BC-COLOR-01" in p and "SCORE:" in p and "<render>" in p
    assert build_judge_prompt(_rule_meta("BC-COLOR-01"), "<render>") == p  # deterministic


def test_parse_verdict_valid_and_malformed():
    assert parse_verdict("BC-X", "SCORE: 1.0\nRATIONALE: clean").score == 1.0
    assert parse_verdict("BC-X", "SCORE: 0.5").score == 0.5
    assert parse_verdict("BC-X", "no score here").score is None       # malformed → abstain
    assert parse_verdict("BC-X", "SCORE: 0.7").score is None          # off-scale → abstain


def test_llm_judge_abstains_without_model_or_render():
    assert LLMJudge().evaluate("BC-COLOR-01", JudgeContext()).score is None
    # model but no render → still abstain (never guesses)
    assert LLMJudge(complete=lambda p: "SCORE: 1.0").evaluate("BC-COLOR-01", JudgeContext()).score is None


def test_llm_judge_scores_with_mock_model_and_render():
    v = LLMJudge(complete=lambda p: "SCORE: 0.5\nRATIONALE: partial",
                 render_provider=lambda rid: "<a rendered page>").evaluate("BC-COLOR-01", JudgeContext())
    assert v.score == 0.5 and v.method == "llm"


def test_composite_prefers_spec_heuristic_then_llm():
    comp = CompositeJudge([SpecHeuristicJudge(),
                           LLMJudge(complete=lambda p: "SCORE: 1.0\nRATIONALE: ok",
                                    render_provider=lambda rid: "<render>")])
    assert comp.evaluate("BC-NARR-03", JudgeContext()).method == "spec_heuristic"  # cheap wins
    assert comp.evaluate("BC-COLOR-01", JudgeContext()).method == "llm"            # falls through
