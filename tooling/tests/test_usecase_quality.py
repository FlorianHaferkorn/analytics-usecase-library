"""Tests for check_usecase_quality — use-case narrative & standards-grounding bars.

Guards the whole use-case corpus: every page states a decision, every 30s message is a
conclusion (not a chart label), every factsheet is standards-grounded on its strategic KPI.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_usecase_quality import check_bracket, is_label_message

REPO = Path(__file__).resolve().parents[2]


def test_label_heuristic():
    # label-style (describe the visual) → rejected
    assert is_label_message("Cash balance trend over time.")
    assert is_label_message("OEE trend vs. target.")
    assert is_label_message("Net sales growth vs. last year, trended.")
    assert is_label_message("")
    assert is_label_message(None)
    # conclusions → accepted
    assert not is_label_message("On-time delivery is the component dragging OTIF below target, not in-full")
    assert not is_label_message("Cash balance is drifting down toward its safety-margin threshold")
    # decomposition-orientation line (em dash) → allowed
    assert not is_label_message("In-full rate and stockout impact — the two OTIF components beyond timeliness.")


def test_corpus_is_clean():
    violations: list[str] = []
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        violations += check_bracket(b)
    assert not violations, "use-case quality violations:\n" + "\n".join(violations)
