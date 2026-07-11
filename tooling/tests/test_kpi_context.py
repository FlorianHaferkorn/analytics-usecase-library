"""Tests for the BC-NARR-04 KPI-context validator (advisory structural rubric rule).

Covers the pure classifier and a coverage regression guard (governed hero-card context
may only increase, never regress).
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_kpi_context import check_bracket, has_context

REPO = Path(__file__).resolve().parents[2]

# Baseline coverage: all 17 hero KPI cards declare governed context (comparison +
# status_logic) as of the 2026-07-10 rollout. This guard only ratchets up — coverage
# must never drop below the baseline.
_BASELINE_COVERED = 17


def test_has_context_true_cases():
    assert has_context({"comparison": "vs_plan"})
    assert has_context({"target_value": 0.42})
    assert has_context({"status_logic": "higher_is_better"})


def test_has_context_false_cases():
    assert not has_context({})
    assert not has_context({"kpi_id": "x", "visual_type": "kpi_card"})
    assert not has_context(None)


def test_coverage_does_not_regress():
    covered = sum(1 for b in REPO.glob("core/usecases/**/UseCase_Bracket.yaml") if check_bracket(b) is True)
    assert covered >= _BASELINE_COVERED, (
        f"BC-NARR-04 hero-card context coverage dropped below baseline "
        f"({covered} < {_BASELINE_COVERED})"
    )
