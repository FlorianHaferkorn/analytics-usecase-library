"""Capacity floor + procurement recommendation (tooling/superversion/capacity.py).

The doctrine under test is "state what is missing rather than assume a value". Most of
these cases therefore assert on `unknowns` and on the *absence* of a floor, not on a
number — a recommendation that silently defaults is the failure mode this module exists
to prevent.
"""
from __future__ import annotations

import pytest

from tooling.superversion.capacity import (
    FREE_VIEWER_MIN_SKU,
    RESERVATION_BREAKEVEN_HOURS_PER_WEEK,
    licence_breakeven,
    procurement,
    recommend,
    sizing_floor,
    split,
)


def _bp(sizing=None, capacity_sku=None, domains=0):
    platform = {"stack": "fabric", "ownership_boundaries": []}
    if sizing is not None:
        platform["sizing"] = sizing
    if capacity_sku:
        platform["capacity_sku"] = capacity_sku
    return {
        "schema_version": "0.1.0",
        "platform": platform,
        "mesh": {"domains": [{"name": f"d{i}"} for i in range(domains)]},
    }


# --- nothing declared: no floor, everything surfaced --------------------------------

def test_no_sizing_yields_no_floor_and_names_every_gap():
    out = recommend(_bp())
    assert out["recommended_floor"] is None
    assert out["assigned_sku"] is None
    assert "verdict" in out
    joined = " ".join(out["unknowns"])
    for field in ("largest_model_gb", "largest_table_rows_millions", "viewers",
                  "operating_hours_per_week", "chargeback_per_use_case"):
        assert field in joined, f"{field} not reported as missing"


def test_partial_sizing_still_reports_the_rest_as_unknown():
    out = recommend(_bp({"largest_model_gb": 2}))
    assert out["recommended_floor"] == "F2"
    assert any("largest_table_rows_millions" in u for u in out["unknowns"])


# --- sizing floor -------------------------------------------------------------------

@pytest.mark.parametrize("model_gb,expected", [
    (1, "F2"),    # 3 GB covers it, smallest SKU wins
    (3, "F2"),    # exactly at the F2..F8 ceiling
    (3.5, "F16"), # first jump — F4 and F8 buy nothing here
    (5, "F16"),
    (10, "F32"),
    (25, "F64"),
])
def test_model_size_drives_the_floor(model_gb, expected):
    floor, _, _ = sizing_floor({"largest_model_gb": model_gb})
    assert floor == expected


def test_f4_to_f8_buys_no_model_headroom():
    """The single most common misconception in these conversations."""
    for gb in (3.5, 4, 5):
        floor, _, _ = sizing_floor({"largest_model_gb": gb})
        assert floor == "F16", "F8 must never be the answer to a model-size problem"


def test_direct_lake_rows_drive_the_floor():
    floor, _, _ = sizing_floor({"largest_table_rows_millions": 800})
    assert floor == "F64"


def test_floor_is_the_maximum_over_all_drivers():
    floor, _, _ = sizing_floor({"largest_model_gb": 1, "largest_table_rows_millions": 800})
    assert floor == "F64"


def test_model_beyond_every_sku_is_reported_not_capped():
    floor, reasons, _ = sizing_floor({"largest_model_gb": 5000})
    assert floor is None
    assert any("exceeds every F-SKU" in r for r in reasons)


# --- procurement --------------------------------------------------------------------

def test_procurement_needs_operating_hours():
    out = procurement({})
    assert out["model"] is None
    assert "operating_hours_per_week" in out["unknown"]


@pytest.mark.parametrize("hours,model", [
    (168, "reservation"),
    (RESERVATION_BREAKEVEN_HOURS_PER_WEEK, "reservation"),
    (RESERVATION_BREAKEVEN_HOURS_PER_WEEK - 1, "pay-as-you-go"),
    (75, "pay-as-you-go"),
])
def test_procurement_follows_the_breakeven(hours, model):
    assert procurement({"operating_hours_per_week": hours})["model"] == model


def test_reservation_names_the_pause_conflict():
    out = procurement({"operating_hours_per_week": 168})
    assert "pausing" in out["caveat"]
    assert "3x" in out["term"]


def test_payg_names_the_runbook_and_the_missed_runs():
    out = procurement({"operating_hours_per_week": 40})
    assert "runbook" in out["requires"]
    assert "not caught up" in out["requires"]


# --- split --------------------------------------------------------------------------

def test_split_needs_the_chargeback_answer():
    assert split({}, 2)["capacities"] is None


def test_chargeback_forces_separate_capacities():
    assert split({"chargeback_per_use_case": True}, 2)["capacities"] == 2


def test_no_chargeback_prefers_one_capacity():
    assert split({"chargeback_per_use_case": False}, 3)["capacities"] == 1


def test_stages_split_production_from_non_production():
    """D-596: prod and non-prod on separate capacities, consolidated within."""
    out = split({"chargeback_per_use_case": False}, 3, ["dev", "test", "prod"])
    assert out["stage_groups"] == ["prod", "non_prod"]
    assert out["capacities"] == 2 and out["per_group"] == {"prod": 1, "non_prod": 1}


def test_chargeback_multiplies_per_stage_group():
    out = split({"chargeback_per_use_case": True}, 2, ["dev", "prod"])
    assert out["capacities"] == 4


def test_unstaged_blueprint_has_one_stage_group():
    assert split({"chargeback_per_use_case": False}, 1, None)["stage_groups"] == ["prod"]


def test_tier1_is_an_option_not_part_of_the_count():
    out = split({"chargeback_per_use_case": False}, 1, ["dev", "prod"], ["WS [Prod]"])
    assert out["capacities"] == 2
    assert out["tier1_option"]["workspaces"] == ["WS [Prod]"]


def test_recommend_reads_stages_and_planning_sessions_as_question():
    bp = {"platform": {"sizing": {"chargeback_per_use_case": False},
                       "planning": {"enabled": True}},
          "governance": {"stages": ["dev", "test", "prod"]},
          "mesh": {"domains": [{"name": "D", "workspaces": []}]}}
    out = recommend(bp)
    assert out["split"]["capacities"] == 2
    assert any("planning" in u for u in out["unknowns"])
    assert any("Fabric Planning" in q for q in out["customer_questions"])
    assert "planning" not in out                       # no load without the customer's numbers


def test_recommend_computes_planning_load_from_sessions():
    bp = {"platform": {"sizing": {}, "capacity_sku": "F64",
                       "planning": {"enabled": True,
                                    "sessions": {"planner": 1, "stakeholder": 0, "viewer": 0}}}}
    out = recommend(bp)
    assert out["planning"]["cu_hours_per_session_window"] == 847
    assert out["planning"]["sku"] == "F64"


# --- licence break-even -------------------------------------------------------------

def test_licence_breakeven_without_prices_returns_the_formula_not_a_number():
    out = licence_breakeven("F8", None)
    assert out["viewers"] is None
    assert "formula" in out
    assert out["missing"]


def test_licence_breakeven_with_prices_is_computed():
    out = licence_breakeven("F8", {"capacity_cu_year": 1146, "pro_licence_user_year": 168})
    # (64 - 8) CU * 1146 = 64,176 / 168 = exactly 382 -> break-even, F64 wins from 383 on.
    # Several hundred viewers, not a handful: the jump to F64 is far larger than intuition
    # suggests, which is why this is computed rather than asserted in a conversation.
    assert out["viewers"] == 383
    assert out["prices_are_inputs"] is True


def test_licence_breakeven_not_applicable_at_or_above_f64():
    assert licence_breakeven(FREE_VIEWER_MIN_SKU, None)["applicable"] is False


# --- conflict detection -------------------------------------------------------------

def test_assigned_below_derived_floor_is_flagged():
    out = recommend(_bp({"largest_model_gb": 8}, capacity_sku="F4"))
    assert "conflict" in out
    assert "F4" in out["conflict"] and "F32" in out["conflict"]


def test_assigned_above_floor_is_not_flagged():
    out = recommend(_bp({"largest_model_gb": 1}, capacity_sku="F64"))
    assert "conflict" not in out


# --- determinism --------------------------------------------------------------------

def test_recommendation_is_deterministic():
    bp = _bp({"largest_model_gb": 4, "operating_hours_per_week": 168,
              "chargeback_per_use_case": True, "viewers": 50}, domains=2)
    assert recommend(bp) == recommend(bp)


def test_copilot_minimum_is_f2_not_f64():
    """SIG-2609-010 (D-686): Copilot and data agents need a paid F2+, F64 is licensing only."""
    out = recommend(_bp())
    cop = out["copilot"]
    assert cop["min_sku"] == "F2"
    assert "F2" in cop["statement"] and "no reason to buy F64" in cop["statement"]
    assert any("copilot-enable-fabric" in s for s in cop["sources"])
    # same figure as the byte-identical Meridian mirror
    from tooling.superversion._dataarch_vendor import load_module
    assert load_module("capacity_recommend")._FEATURE_MIN == cop["min_sku"]
