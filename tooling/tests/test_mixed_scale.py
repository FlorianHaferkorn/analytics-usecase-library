"""Tests for the BC-CHART-01 mixed-scale validator (structural rubric rule, knock-out).

Covers the pure classifiers and the repo-wide gate (regression guard for the R1.4
mixed-scale bug: no chart exhibit may bind ≥2 unit types to one axis).
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_mixed_scale import classify_exhibit, check_bracket, unit_class

REPO = Path(__file__).resolve().parents[2]


def test_unit_class_buckets():
    assert unit_class("% (1 decimal)") == "PCT"
    assert unit_class("EUR (2 decimals)") == "CUR"
    assert unit_class("EUR per unit") == "CUR"
    assert unit_class("days") == "DAYS"
    assert unit_class("count") == "COUNT"
    assert unit_class("index") == "INDEX"
    assert unit_class(None) is None
    assert unit_class("") is None


def test_mixed_pct_and_eur_is_flagged():
    ex = {"visual_type": "bar_chart", "kpi_ids": ["margin.gm.pct", "margin.gm.amount"]}
    mixed, reason = classify_exhibit(ex)
    assert mixed is True
    assert "BC-CHART-01" in reason


def test_same_unit_not_flagged():
    ex = {"visual_type": "waterfall", "kpi_ids": ["margin.gm.amount", "sales.pvm.price_effect.amount"]}
    assert classify_exhibit(ex)[0] is False


def test_single_measure_not_flagged():
    assert classify_exhibit({"visual_type": "bar_chart", "kpi_id": "margin.gm.pct"})[0] is False


def test_card_and_table_skipped():
    card = {"visual_type": "kpi_card", "kpi_ids": ["margin.gm.pct", "margin.gm.amount"]}
    table = {"visual_type": "table_with_databars", "kpi_ids": ["margin.gm.pct", "margin.gm.amount"]}
    assert classify_exhibit(card)[0] is False
    assert classify_exhibit(table)[0] is False


def test_com002_pilot_is_single_scale():
    bracket = REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml"
    _, violations, _ = check_bracket(bracket)
    assert violations == 0


# Frozen BC-CHART-01 backlog (2026-07-10): 8 pre-existing mixed-scale exhibits — the
# R1.4 founding bug was only fixed on COM-002. Fixing these is a curated analytical cut
# (choose the slot's single coherent measure/unit, per use case). Until then this set is
# FROZEN: the gate blocks any NEW mixed-scale and a fix must shrink the set + this list.
_KNOWN_MIXED = {
    ("COM-003", "Main_2"),
    ("FIN-001", "Main_2"),
    ("OPS-002", "bar_chart"),
    ("OPS-003", "bar_chart"),
    ("SCM-002", "bar_chart"),
    ("SCM-003", "bar_chart"),
    ("XD-001", "bar_chart"),
    ("XD-003", "Main_3"),
}


def _current_offenders():
    import yaml
    offenders = set()
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        data = yaml.safe_load(b.read_text(encoding="utf-8")) or {}
        ux = data.get("ux_layout_rules", {}) or {}
        uc = b.parent.name.split("_")[0]
        for pk in ("page_1_summary", "page_2_execution"):
            for ex in (ux.get(pk, {}) or {}).get("component_30s", []) or []:
                if isinstance(ex, dict) and classify_exhibit(ex)[0]:
                    offenders.add((uc, ex.get("slot_id") or ex.get("visual_type")))
    return offenders


def test_no_new_mixed_scale_beyond_frozen_backlog():
    """Regression guard: no mixed-scale exhibit may exist beyond the frozen backlog."""
    new = _current_offenders() - _KNOWN_MIXED
    assert not new, f"NEW BC-CHART-01 mixed-scale violations (not in frozen backlog): {new}"


def test_frozen_backlog_has_not_silently_grown_or_been_fixed():
    """Keep the frozen set honest: if it shrinks (a fix) or grows, update _KNOWN_MIXED."""
    assert _current_offenders() == _KNOWN_MIXED, (
        "BC-CHART-01 backlog changed — update _KNOWN_MIXED (and the ledger) to match."
    )
