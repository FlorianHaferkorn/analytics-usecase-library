"""Tests for check_usecase_quality — use-case narrative & standards-grounding bars.

Guards the whole use-case corpus: every page states a decision, every 30s message is a
conclusion (not a chart label), every factsheet is standards-grounded on its strategic KPI.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_usecase_quality import check_bracket
from tooling.validation.check_exhibit_message import classify_message

REPO = Path(__file__).resolve().parents[2]


def test_message_rule_reuses_bc_narr_01_owner():
    # BC-NARR-01 is owned by check_exhibit_message; check_usecase_quality must not re-implement it.
    # Confirm the shared classifier is the one deciding label vs. conclusion.
    assert classify_message("Revenue by region")[0] is False              # bare label → rejected
    assert classify_message("On-time delivery is dragging OTIF below target")[0] is True  # conclusion
    # and check_usecase_quality no longer ships a parallel heuristic
    import tooling.validation.check_usecase_quality as m
    assert not hasattr(m, "is_label_message"), "parallel label heuristic must be gone (reuse the owner)"


def test_corpus_is_clean():
    violations: list[str] = []
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        violations += check_bracket(b)
    assert not violations, "use-case quality violations:\n" + "\n".join(violations)
