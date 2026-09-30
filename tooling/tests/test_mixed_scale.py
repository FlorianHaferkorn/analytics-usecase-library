"""Tests for the BC-CHART-01 mixed-scale validator (structural rubric rule, knock-out).

Covers the pure classifiers and the repo-wide gate (regression guard for the R1.4
mixed-scale bug: no chart exhibit may bind ≥2 unit types to one axis).
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_mixed_scale import classify_exhibit, check_bracket, unit_class

REPO = Path(__file__).resolve().parents[2]


def test_unit_class_buckets():
    assert unit_class("% (1 decimal)") == "PCT"
    assert unit_class("EUR (2 decimals)") == "CUR"
    assert unit_class("EUR per unit") == "CUR"
    assert unit_class("days") == "DAYS"
    assert unit_class("count") == "COUNT"
    assert unit_class("index") == "INDEX"
    assert unit_class(None) is None
    assert unit_class("") is None


def test_mixed_pct_and_eur_is_flagged():
    ex = {"visual_type": "bar_chart", "kpi_ids": ["KPI-COM-013", "KPI-COM-019"]}
    mixed, reason = classify_exhibit(ex)
    assert mixed is True
    assert "BC-CHART-01" in reason


def test_same_unit_not_flagged():
    ex = {"visual_type": "waterfall", "kpi_ids": ["KPI-COM-019", "KPI-COM-010"]}
    assert classify_exhibit(ex)[0] is False


def test_single_measure_not_flagged():
    assert classify_exhibit({"visual_type": "bar_chart", "kpi_id": "KPI-COM-013"})[0] is False


def test_card_and_table_skipped():
    card = {"visual_type": "kpi_card", "kpi_ids": ["KPI-COM-013", "KPI-COM-019"]}
    table = {"visual_type": "table_with_databars", "kpi_ids": ["KPI-COM-013", "KPI-COM-019"]}
    assert classify_exhibit(card)[0] is False
    assert classify_exhibit(table)[0] is False


def test_com002_pilot_is_single_scale():
    bracket = REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml"
    _, violations, _ = check_bracket(bracket)
    assert violations == 0


def test_no_mixed_scale_across_all_brackets():
    """Gate: BC-CHART-01 knock-out enforced repo-wide — 0 mixed-scale exhibits.

    The founding-bug backlog (8 exhibits) was fixed 2026-07-10 by reducing each to a
    single-measure ranking; this test now holds the whole library at zero.
    """
    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    assert brackets
    offenders = []
    for b in brackets:
        _, violations, lines = check_bracket(b)
        if violations:
            offenders.append((b.relative_to(REPO), lines))
    assert not offenders, f"BC-CHART-01 mixed-scale violations: {offenders}"
