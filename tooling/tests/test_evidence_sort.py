"""Tests for the BC-CHART-10 evidence-sort validator (knock-out structural rule).

Covers the pure classifier and a coverage regression guard (governed worst-first
evidence ordering may only increase, never regress) — mirrors test_kpi_context.py.
"""
from __future__ import annotations

from pathlib import Path

import datetime as dt

from tooling.validation.check_evidence_sort import (
    ausnahme_veraltet,
    check_bracket,
    classify_evidence,
)

REPO = Path(__file__).resolve().parents[2]

# Baseline coverage: evidence tables that declare a valid worst-first sort + Top-N.
# Full rollout 2026-07-11 — all 17 evidence tables governed (COM-002 pilot + 16
# backlog). This guard only ratchets up — coverage must never drop below the baseline.
_BASELINE_COVERED = 17


def test_valid_ordering():
    # R2.1 canonical fields: sort_by {measure, direction} + top_n (ascending/descending).
    ok, _ = classify_evidence({
        "evidence_columns": ["sku", "KPI-FIN-017"],
        "sort_by": {"measure": "KPI-FIN-017", "direction": "ascending"},
        "top_n": 20,
    })
    assert ok is True


def test_missing_sort_is_invalid():
    ok, reason = classify_evidence({"evidence_columns": ["sku"]})
    assert ok is False and "sort_by" in reason


def test_missing_measure_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "KPI-COM-013"],
        "sort_by": {"direction": "ascending"},
        "top_n": 20,
    })
    assert ok is False and "measure" in reason


def test_bad_direction_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "KPI-COM-013"],
        "sort_by": {"measure": "KPI-COM-013", "direction": "sideways"},
        "top_n": 20,
    })
    assert ok is False and "direction" in reason


def test_missing_or_bad_top_n_is_invalid():
    base = {
        "evidence_columns": ["sku", "KPI-COM-013"],
        "sort_by": {"measure": "KPI-COM-013", "direction": "descending"},
    }
    assert classify_evidence(base)[0] is False                      # missing
    assert classify_evidence({**base, "top_n": 0})[0] is False   # < 1
    assert classify_evidence({**base, "top_n": True})[0] is False  # bool, not int


_SORT = {"measure": "KPI-SVC-009", "direction": "descending"}


def _ausnahme(klasse: str = "kleine_koernung", zeilen: int = 32) -> dict:
    return {"klasse": klasse, "gemessene_zeilen": zeilen, "gemessen_am": "2026-10-24",
            "quelle": "fact_workforce_management (Gold, pandas)"}


def test_ausnahme_kleine_koernung_is_valid():
    # ADR-0027: a measured small grain replaces top_n.
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": _ausnahme()})[0] is True


def test_ausnahme_kleine_koernung_over_limit_is_invalid():
    ok, reason = classify_evidence({"sort_by": _SORT, "top_n_ausnahme": _ausnahme(zeilen=51)})
    assert ok is False and "50" in reason


def test_ausnahme_matrix_only_for_matrix():
    c300 = {"sort_by": _SORT, "top_n_ausnahme": _ausnahme("matrix_zwischensummen", 40)}
    assert classify_evidence(c300)[0] is False                               # default table
    assert classify_evidence({**c300, "visual_type": "matrix"})[0] is True


def test_ausnahme_and_top_n_together_is_invalid():
    ok, reason = classify_evidence({"sort_by": _SORT, "top_n": 20, "top_n_ausnahme": _ausnahme()})
    assert ok is False and "both" in reason


def test_ausnahme_incomplete_or_unknown_class_is_invalid():
    unvollstaendig = {k: v for k, v in _ausnahme().items() if k != "quelle"}
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": unvollstaendig})[0] is False
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": _ausnahme("gross")})[0] is False
    falsches_datum = {**_ausnahme(), "gemessen_am": "24.10.2026"}
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": falsches_datum})[0] is False


def test_ausnahme_still_needs_sort():
    assert classify_evidence({"top_n_ausnahme": _ausnahme()})[0] is False


def test_ausnahme_veraltet_warns_after_180_days():
    c300 = {"sort_by": _SORT, "top_n_ausnahme": _ausnahme()}
    assert ausnahme_veraltet(c300, heute=dt.date(2027, 4, 22)) is None      # 180 Tage
    assert "181" in (ausnahme_veraltet(c300, heute=dt.date(2027, 4, 23)) or "")
    assert ausnahme_veraltet({"sort_by": _SORT, "top_n": 20}) is None


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
