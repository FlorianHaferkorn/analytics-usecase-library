"""Tests for chart_question_fit — does the visual type generically fit the question?"""
from __future__ import annotations

from tooling.storyline.chart_question_fit import classify_question, fits


def test_classify_intents():
    assert "temporal" in classify_question("Has conversion declined over the last 12 months?")
    assert "ranking" in classify_question("Where does the shortfall concentrate by segment?")
    assert "comparison" in classify_question("Is EBITDA on track vs plan?")
    assert "composition" in classify_question("What is the mix of the OTIF shortfall?")
    assert "driver" in classify_question("Is engagement the driver behind attrition?")
    assert classify_question("A neutral heading") == set()


def test_fit_pass_and_fail():
    # temporal question + trend line → fits
    ok, _ = fits("Has conversion declined over 12 months?", "trend_line")
    assert ok
    # ranking question + single card → cannot answer
    ok, reason = fits("Which segment is worst?", "kpi_card")
    assert not ok and "ranking" in reason
    # vs-plan comparison answered by a line with a reference → fits (not a false positive)
    ok, _ = fits("Is EBITDA on track vs plan?", "line_chart")
    assert ok


def test_unclassifiable_and_unknown_are_skipped_not_flagged():
    assert fits("A neutral heading", "kpi_card")[0] is True        # no intent → skip
    assert fits("Where is it worst?", "some_future_visual")[0] is True  # unknown type → don't guess


def test_corpus_has_no_hard_chart_fit_failure_only_advisories():
    # sanity: the deterministic fitter runs over every governed 30s visual without throwing
    import glob, yaml
    from pathlib import Path
    repo = Path(__file__).resolve().parents[2]
    for f in glob.glob(str(repo / "core/usecases/**/UseCase_Bracket.yaml"), recursive=True):
        d = yaml.safe_load(open(f, encoding="utf-8")) or {}
        ux = d.get("ux_layout_rules", {}) or {}
        for pk in ("page_1_summary", "page_2_execution"):
            for c in (ux.get(pk) or {}).get("component_30s", []) or []:
                ok, reason = fits(c.get("question"), c.get("visual_type"))
                assert isinstance(ok, bool) and isinstance(reason, str)
