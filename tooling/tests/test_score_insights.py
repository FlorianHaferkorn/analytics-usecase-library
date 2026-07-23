"""Tests for the Stage-1 deterministic insight scorer (ADR-0017 seam)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

from tooling.storyline.score_insights import (
    DeterministicScorer,
    InsightScore,
    _grounding_maps,
    rank_storyline,
)

REPO = Path(__file__).resolve().parents[2]


def _ds():
    spec = importlib.util.spec_from_file_location(
        "derive_storyline", REPO / "tooling/storyline/derive_storyline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_score_math_and_gate():
    s = InsightScore(depth=1.0, specificity=1.0, actionability=1.0, grounding=1.0)
    assert s.total == 1.0 and s.verified
    ungrounded = InsightScore(depth=1.0, specificity=1.0, actionability=1.0, grounding=0.0)
    assert not ungrounded.verified          # no grounding ⇒ cannot lead
    assert ungrounded.total < 1.0


def test_deterministic_scorer_signals():
    sc = DeterministicScorer()
    ctx = {"kpi_exists": {"x.y"}, "kpi_has_ref": {"x.y"},
           "causal_thread": {"driver": "x.y", "target": "z"}, "has_actions": True}
    strong = sc.score({"kpi_id": "x.y", "visual_type": "waterfall",
                       "answer": "OTIF is dragging, driven by on-time not in-full, concentrated in a few lanes",
                       "so_what": "Prioritise the worst lanes"}, ctx)
    weak = sc.score({"kpi_id": "not.a.kpi", "visual_type": "trend_line",
                     "answer": "Sales over time", "so_what": ""}, ctx)
    assert strong.total > weak.total
    assert strong.grounding == 1.0 and strong.verified
    assert weak.grounding == 0.0 and not weak.verified   # unknown KPI ⇒ unverified


def test_decomposition_without_catalog_kpi_is_partially_grounded():
    sc = DeterministicScorer()
    ctx = {"kpi_exists": set(), "kpi_has_ref": set(), "causal_thread": None, "has_actions": False}
    none_kpi = sc.score({"kpi_id": None, "visual_type": "waterfall", "answer": "bridge", "so_what": ""}, ctx)
    measure_name = sc.score({"kpi_id": "PVM Bridge Value", "visual_type": "waterfall",
                             "answer": "bridge", "so_what": ""}, ctx)
    assert none_kpi.grounding == measure_name.grounding == 0.3   # consistent governed-decomposition credit


def test_every_use_case_gets_a_verified_headline():
    ds = _ds()
    kpi_domains, kpi_keys, action_related = ds._kpi_domains(), ds._kpi_keys(), ds._action_related()
    exists, has_ref = _grounding_maps()
    without_headline = []
    for b in ds.load_brackets(None):
        s = ds.build_storyline(yaml.safe_load(b.read_text(encoding="utf-8")) or {},
                               kpi_domains, kpi_keys, action_related)
        r = rank_storyline(s, exists, has_ref)
        if r["headline"] is None:
            without_headline.append(r["use_case"])
        else:
            assert r["headline"]["verified"], f"{r['use_case']} headline not verified"
    # every use case has at least one grounded finding to lead with
    assert not without_headline, f"use cases with no verified headline: {without_headline}"
