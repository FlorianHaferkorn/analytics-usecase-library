"""Tests for the BC-CHART-10 evidence-sort validator (knock-out structural rule).

Covers the pure classifier and a coverage regression guard (governed worst-first
evidence ordering may only increase, never regress) — mirrors test_kpi_context.py.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_evidence_sort import check_bracket, classify_evidence

REPO = Path(__file__).resolve().parents[2]

# Baseline coverage: evidence tables that declare a valid worst-first sort + Top-N.
# COM-002 is the pilot (2026-07-11). This guard only ratchets up — coverage must
# never drop below the baseline. Raise it as the K7-style rollout clears the backlog.
_BASELINE_COVERED = 1


def test_valid_ordering():
    ok, _ = classify_evidence({
        "evidence_columns": ["sku", "margin.gm.vs_plan.pct"],
        "evidence_sort": {"column": "margin.gm.vs_plan.pct", "direction": "asc"},
        "evidence_top_n": 20,
    })
    assert ok is True


def test_missing_sort_is_invalid():
    ok, reason = classify_evidence({"evidence_columns": ["sku"]})
    assert ok is False and "evidence_sort" in reason


def test_sort_column_must_be_in_evidence_columns():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "margin.gm.pct"],
        "evidence_sort": {"column": "not.a.column", "direction": "asc"},
        "evidence_top_n": 20,
    })
    assert ok is False and "not one of evidence_columns" in reason


def test_bad_direction_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "margin.gm.pct"],
        "evidence_sort": {"column": "margin.gm.pct", "direction": "sideways"},
        "evidence_top_n": 20,
    })
    assert ok is False and "direction" in reason


def test_missing_or_bad_top_n_is_invalid():
    base = {
        "evidence_columns": ["sku", "margin.gm.pct"],
        "evidence_sort": {"column": "margin.gm.pct", "direction": "desc"},
    }
    assert classify_evidence(base)[0] is False                      # missing
    assert classify_evidence({**base, "evidence_top_n": 0})[0] is False   # < 1
    assert classify_evidence({**base, "evidence_top_n": True})[0] is False  # bool, not int


def test_no_evidence_table_is_not_applicable():
    assert classify_evidence(None) == (None, "")
    assert classify_evidence({}) == (None, "")


def test_coverage_does_not_regress():
    covered = sum(
        1 for b in REPO.glob("core/usecases/**/UseCase_Bracket.yaml")
        if check_bracket(b)[0] is True
    )
    assert covered >= _BASELINE_COVERED, (
        f"BC-CHART-10 evidence-sort coverage dropped below baseline "
        f"({covered} < {_BASELINE_COVERED})"
    )
