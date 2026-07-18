"""Tests for the BC-CHART-02 deviation-as-deviation validator.

A plan/PY variance drawn as absolute bars makes the reader subtract two totals by eye;
it must be a waterfall/variance bar (the delta itself). vs_target and line/waterfall are
exempt. Pure logic is unit-tested; a guard keeps the committed brackets clean.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tooling.validation.check_deviation_display import exhibit_violations, check_registry

REPO = Path(__file__).resolve().parents[2]


def _bracket(*exhibits):
    return {"ux_layout_rules": {"page_1_summary": {"component_30s": list(exhibits)}}}


def test_plan_variance_as_bar_is_flagged():
    v = exhibit_violations(_bracket(
        {"slot_id": "Main_2", "comparison": "vs_plan", "visual_type": "bar_chart"}))
    assert v == [("Main_2", "vs_plan", "bar_chart")]


def test_py_variance_as_column_is_flagged():
    v = exhibit_violations(_bracket(
        {"slot_id": "M", "comparison": "vs_py", "visual_type": "column_chart"}))
    assert len(v) == 1


def test_waterfall_and_variance_are_exempt():
    assert exhibit_violations(_bracket(
        {"slot_id": "M", "comparison": "vs_plan", "visual_type": "waterfall"})) == []


def test_vs_target_is_exempt():
    # a target is naturally a reference line/band, not two absolute bars
    assert exhibit_violations(_bracket(
        {"slot_id": "M", "comparison": "vs_target", "visual_type": "bar_chart"})) == []


def test_trend_line_is_exempt():
    assert exhibit_violations(_bracket(
        {"slot_id": "M", "comparison": "vs_plan", "visual_type": "trend_line"})) == []


def test_committed_brackets_show_variance_as_variance():
    assert check_registry() == [], f"plan/PY variances drawn as absolute bars: {check_registry()}"


def test_fin001_ocf_gap_is_a_waterfall():
    """FIN-001 Main_2's message is about the OCF-vs-Plan shortfall — it must render the
    gap as a waterfall, not absolute actual/plan bars."""
    fin = yaml.safe_load(
        (REPO / "core/usecases/core/FIN-001_Cash_Liquidity_Performance/UseCase_Bracket.yaml").read_text())
    main2 = next(e for e in fin["ux_layout_rules"]["page_1_summary"]["component_30s"]
                 if e["slot_id"] == "Main_2")
    assert main2["comparison"] == "vs_plan" and main2["visual_type"] == "waterfall"
