"""Tests for the concrete Anthropic LLM-judge backend (K6 §9, render-only half).

The backend is opt-in: with no ANTHROPIC_MODEL / ANTHROPIC_API_KEY it must gracefully
degrade to abstention so live coverage never changes. The render provider + composite
wiring are tested with a mock model (no key, no network).
"""
from __future__ import annotations

from tooling.report_quality.judge import JudgeContext
from tooling.report_quality.llm_backend import (
    build_composite_judge, build_llm_judge, dir_render_provider, make_complete,
)


def test_make_complete_is_none_without_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert make_complete() is None   # no fabrication path without credentials


def test_make_complete_is_none_with_partial_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "some-model")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert make_complete() is None   # model but no key → still None


def test_dir_render_provider_reads_per_rule_then_shared(tmp_path):
    (tmp_path / "BC-COLOR-01.txt").write_text("per-rule evidence", encoding="utf-8")
    (tmp_path / "_report.html").write_text("<shared report>", encoding="utf-8")
    provide = dir_render_provider(tmp_path)
    assert provide("BC-COLOR-01") == "per-rule evidence"   # per-rule wins
    assert provide("BC-CHART-03") == "<shared report>"     # falls back to shared
    assert provide("BC-NOTHERE") == "<shared report>"      # shared covers everything


def test_dir_render_provider_none_when_empty(tmp_path):
    assert dir_render_provider(tmp_path)("BC-COLOR-01") is None


def test_dir_render_provider_falls_back_to_rendered_html(tmp_path):
    # No per-rule / _report file, but rendered *.html present → suite-wide blob,
    # <script> stripped, CSS kept.
    (tmp_path / "COM-001.html").write_text(
        "<style>.x{color:red}</style><body>sales</body><script>doStuff()</script>", encoding="utf-8")
    (tmp_path / "FIN-001.html").write_text("<body>cash</body>", encoding="utf-8")
    blob = dir_render_provider(tmp_path)("BC-COLOR-01")
    assert "sales" in blob and "cash" in blob              # both reports included
    assert "color:red" in blob                             # CSS kept (colour signal)
    assert "doStuff" not in blob                           # <script> stripped


def test_build_llm_judge_abstains_without_model(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    (tmp_path / "_report.html").write_text("<render>", encoding="utf-8")
    j = build_llm_judge(tmp_path)   # render present, but no model → abstain
    assert j.evaluate("BC-COLOR-01", JudgeContext()).score is None


def test_composite_still_scores_spec_heuristic_without_model(tmp_path, monkeypatch):
    # The composite must keep scoring the spec-decidable rules even with no LLM wired,
    # so wiring the backend never regresses live coverage.
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    comp = build_composite_judge(tmp_path)
    assert comp.evaluate("BC-NARR-03", JudgeContext()).method == "spec_heuristic"
    assert comp.evaluate("BC-COLOR-01", JudgeContext()).score is None   # render-only abstains
