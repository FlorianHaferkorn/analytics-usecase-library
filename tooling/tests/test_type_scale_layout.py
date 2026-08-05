"""Tests for BC-TYPE-03 (type hierarchy), BC-LAYOUT-04 (zone density) + BC-TYPE-02 advisory.

BC-TYPE-03: the hero kpi_value must be ≥2× each secondary role. BC-LAYOUT-04: ≤7 elements
pro Summary-Zone. BC-TYPE-02 ist seit 05.08.2026 ein echtes Gate (Schriftwahl statt
Render-Verifikation).
"""
from __future__ import annotations

from tooling.validation.check_type_scale import hierarchy_violations, check_scale
from tooling.validation.check_zone_density import summary_zone_count, check_registry
from tooling.validation.check_tabular_numerals import violations as tabular_violations


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


# ── BC-TYPE-02 ───────────────────────────────────────────────────────────────

def test_no_numeric_surface_uses_proportional_figures():
    """Zahlen, die nicht untereinander stehen, kann man senkrecht nicht vergleichen.

    Bis 05.08.2026 war das ein advisory-Reporter mit der Begruendung, Power BI biete
    keinen Umschalter fuer Tabellenziffern. Das stimmt — nur folgt daraus das
    Gegenteil: wenn die Eigenschaft fehlt, IST die Schriftwahl die Regel, und die
    steht im Theme. Gemessen (Selawik-UFOs, von Microsoft als metrisch kompatibel zu
    Segoe UI gefuehrt): Regular und Bold tabular, LIGHT proportional.
    """
    v = tabular_violations()
    assert v == [], "Zahlenflaeche mit proportionalen Ziffern:\n" + "\n".join(f"    {x}" for x in v)
