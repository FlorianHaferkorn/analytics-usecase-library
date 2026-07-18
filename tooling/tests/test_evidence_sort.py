"""Tests for the BC-CHART-10 evidence-sort validator (knock-out structural rule).

Covers the pure classifier and a coverage regression guard (governed worst-first
evidence ordering may only increase, never regress) — mirrors test_kpi_context.py.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_evidence_sort import check_bracket, classify_evidence

REPO = Path(__file__).resolve().parents[2]

# Baseline coverage: evidence tables that declare a valid worst-first sort + Top-N.
# Full rollout 2026-07-11 — all 17 evidence tables governed (COM-002 pilot + 16
# backlog). This guard only ratchets up — coverage must never drop below the baseline.
_BASELINE_COVERED = 17


def test_valid_ordering():
    # R2.1 canonical fields: sort_by {measure, direction} + top_n (ascending/descending).
    ok, _ = classify_evidence({
        "evidence_columns": ["sku", "margin.gm.vs_plan.pct"],
        "sort_by": {"measure": "margin.gm.vs_plan.pct", "direction": "ascending"},
        "top_n": 20,
    })
    assert ok is True


def test_missing_sort_is_invalid():
    ok, reason = classify_evidence({"evidence_columns": ["sku"]})
    assert ok is False and "sort_by" in reason


def test_missing_measure_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "margin.gm.pct"],
        "sort_by": {"direction": "ascending"},
        "top_n": 20,
    })
    assert ok is False and "measure" in reason


def test_bad_direction_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "margin.gm.pct"],
        "sort_by": {"measure": "margin.gm.pct", "direction": "sideways"},
        "top_n": 20,
    })
    assert ok is False and "direction" in reason


def test_missing_or_bad_top_n_is_invalid():
    base = {
        "evidence_columns": ["sku", "margin.gm.pct"],
        "sort_by": {"measure": "margin.gm.pct", "direction": "descending"},
    }
    assert classify_evidence(base)[0] is False                      # missing
    assert classify_evidence({**base, "top_n": 0})[0] is False   # < 1
    assert classify_evidence({**base, "top_n": True})[0] is False  # bool, not int


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
