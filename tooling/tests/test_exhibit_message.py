"""Tests for the BC-NARR-01 exhibit-message validator (K2).

Covers the pure classifier `classify_message` and the COM-002 pilot, which must
carry statement-style messages on every 30-second exhibit.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.validation.check_exhibit_message import check_bracket, classify_message

REPO = Path(__file__).resolve().parents[2]


# ── Statements (pass) ────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "msg",
    [
        "Price concessions, not volume, explain the GM gap",
        "Gross Margin fell 12% vs plan",
        "GM% is concentrated below target in a few org units",
        "Deckungsbeitrag liegt unter Plan — Preis ist der Treiber",
        "Revenue is off track — down 8% on prior year",
    ],
)
def test_statements_pass(msg: str) -> None:
    status, _ = classify_message(msg)
    assert status is True


# ── Labels (fail — BC-NARR-01 violation) ─────────────────────────────────────
@pytest.mark.parametrize(
    "msg",
    [
        "Gross Margin by Region",
        "Revenue by Month",
        "GM by Product Category",
        "Sales by Channel",
    ],
)
def test_labels_fail(msg: str) -> None:
    status, reason = classify_message(msg)
    assert status is False
    assert "BC-NARR-01" in reason


# ── Absent / weak (advisory) ─────────────────────────────────────────────────
@pytest.mark.parametrize("msg", [None, "", "   "])
def test_missing_is_advisory(msg) -> None:
    status, _ = classify_message(msg)
    assert status is None


def test_weak_message_is_advisory() -> None:
    # No comparison / quantity / verb signal and not a "X by Y" label.
    status, _ = classify_message("Commercial overview panel")
    assert status is None


def test_statement_containing_by_is_not_a_label() -> None:
    # "by" appears but the sentence has real structure + a verb signal.
    status, _ = classify_message("GM was eroded by price, not volume")
    assert status is True


# ── Pilot: COM-002 must pass BC-NARR-01 on every exhibit ─────────────────────
def test_com002_pilot_all_exhibits_are_statements() -> None:
    bracket = REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml"
    assert bracket.exists()
    passed, warned, failed, _ = check_bracket(bracket)
    assert failed == 0
    assert warned == 0
    assert passed >= 3  # Main_1, Main_2, Main_3


# ── K6 gate: BC-NARR-01 knock-out enforced repo-wide ─────────────────────────
def test_no_label_titles_across_all_brackets():
    """Gate: no governed exhibit message may read as a label (BC-NARR-01 knock-out).

    Missing messages are advisory (not authored yet), but a message that IS a label
    is a hard violation anywhere in the library — this is what wires the rubric rule
    into the test gate so titles-as-labels can never regress (K6).
    """
    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    assert brackets, "no UseCase_Bracket.yaml files found"
    offenders = []
    for b in brackets:
        _, _, failed, lines = check_bracket(b)
        if failed:
            offenders.append((b.relative_to(REPO), lines))
    assert not offenders, f"BC-NARR-01 label-title violations: {offenders}"
