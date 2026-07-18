"""Tests for BC-TYPE-03 (type hierarchy), BC-LAYOUT-04 (zone density) + BC-TYPE-02 advisory.

BC-TYPE-03: the hero kpi_value must be ≥2× each secondary role. BC-LAYOUT-04: ≤7 elements
per summary zone. BC-TYPE-02 is advisory (tabular numerals render-gated).
"""
from __future__ import annotations

from tooling.validation.check_type_scale import hierarchy_violations, check_scale
from tooling.validation.check_zone_density import summary_zone_count, check_registry
from tooling.validation.check_tabular_numerals import tables_awaiting_tabular


# ── BC-TYPE-03 ───────────────────────────────────────────────────────────────

def test_hero_at_least_twice_secondary_passes():
    scale = {"kpi_value": {"size_min_pt": 28}, "kpi_delta": {"size_max_pt": 14},
             "kpi_label": {"size_max_pt": 11}}
    assert hierarchy_violations(scale) == []


def test_flat_hero_is_flagged():
    scale = {"kpi_value": {"size_min_pt": 16}, "kpi_label": {"size_max_pt": 12}}
    assert hierarchy_violations(scale)   # 16 / 12 = 1.33× < 2×


def test_committed_scale_has_dominant_hero():
    assert check_scale() == [], f"type hierarchy too flat: {check_scale()}"


# ── BC-LAYOUT-04 ─────────────────────────────────────────────────────────────

def test_zone_count_sums_hero_and_exhibits():
    b = {"ux_layout_rules": {"page_1_summary": {
        "component_3s": {"kpi_id": "x"},
        "component_30s": [{"slot_id": "a"}, {"slot_id": "b"}]}}}
    assert summary_zone_count(b) == 3


def test_overloaded_zone_is_flagged():
    b = {"ux_layout_rules": {"page_1_summary": {
        "component_3s": {"kpi_id": "x"},
        "component_30s": [{"slot_id": str(i)} for i in range(8)]}}}
    assert summary_zone_count(b) == 9   # > 7


def test_committed_brackets_are_within_zone_budget():
    assert check_registry() == [], f"overloaded zones: {check_registry()}"


# ── BC-TYPE-02 advisory ──────────────────────────────────────────────────────

def test_tabular_numeral_advisory_lists_tables_but_never_gates():
    # advisory only — it reports tables awaiting the render-gated emit, and the list is
    # a plain report (the committed tables don't declare tabular numerals yet)
    tables = tables_awaiting_tabular()
    assert isinstance(tables, list)   # never raises / never gates
