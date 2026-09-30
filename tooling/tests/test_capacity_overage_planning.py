"""Capacity overage and Fabric Planning figures (tooling/superversion/capacity.py).

Grounding: learn.microsoft.com, read 2026-09-29 —
enterprise/capacity-overage-overview (CU-hour table, 3x rate, < 1/3 guidance, quota = /24,
5-minute evaluation), enterprise/enable-capacity-overage (on by default, 25 % default
threshold) and iq/plan/resources/billing-fabric-plan (847/168/37 CU hours per 30-day
session, 730 h, 30 % buffer). Literal Learn values are asserted here on purpose: the table
in capacity.py must be checked against the published numbers, not against itself.
"""
from __future__ import annotations

import pytest

from tooling.superversion.capacity import (
    CU,
    CU_HOURS_PER_DAY,
    OVERAGE_DEFAULT_THRESHOLD_PCT,
    OVERAGE_PRICE_MULTIPLIER,
    PLANNING_SESSION_CU_HOURS,
    PLANNING_SESSION_HOURS,
    SKU_ORDER,
    overage_profile,
    planning_load,
    recommend,
)

# Learn capacity-overage-overview, "Capacity overage thresholds" table (F2..F8192;
# F4096/F8192 read 2026-09-30).
_LEARN_CU_HOURS_PER_DAY = {
    "F2": 48, "F4": 96, "F8": 192, "F16": 384, "F32": 768, "F64": 1536,
    "F128": 3072, "F256": 6144, "F512": 12288, "F1024": 24576, "F2048": 49152,
    "F4096": 98304, "F8192": 196608,
}


def test_daily_cu_hours_match_learn_table_and_cu_times_24():
    assert CU_HOURS_PER_DAY == _LEARN_CU_HOURS_PER_DAY
    # Second, independent source inside the module: the CU table.
    assert all(CU_HOURS_PER_DAY[s] == CU[s] * 24 for s in SKU_ORDER)


def test_sku_ladder_matches_mirrored_meridian_f_skus():
    """Peer check (Meridian D-604): ALUCA's own SKU ladder and the vendored
    ``capacity_recommend.F_SKUS`` (what ``provisioning: create`` may create) name the same
    13 F-SKUs in the same order, so neither side can drift to a SKU the other lacks."""
    from tooling.superversion._dataarch_vendor import available, load_module

    if not available():
        pytest.skip("Meridian mirror unavailable")
    f_skus = load_module("capacity_recommend").F_SKUS
    assert tuple(SKU_ORDER) == tuple(f_skus)
    assert len(SKU_ORDER) == 13


def test_overage_constants_match_learn():
    assert OVERAGE_PRICE_MULTIPLIER == 3
    assert OVERAGE_DEFAULT_THRESHOLD_PCT == 25


def test_undecided_threshold_shows_microsoft_default_and_asks_customer():
    out = overage_profile("F64")
    assert out["cu_hours_per_day"] == 1536
    assert out["threshold_cu_hours"] == 384          # 25 % of 1,536
    assert out["threshold_source"] == "microsoft_default"
    assert out["recommended_max_threshold_cu_hours"] == 512
    assert out["quota_cu_required"] == 16            # 384 / 24
    assert out["above_recommended_max"] is False
    assert "customer_question" in out
    assert "switch it off" in out["customer_question"]
    assert "384" in out["customer_question"]


def test_customer_threshold_uses_learn_quota_example_and_drops_question():
    # Learn: "a 48 CU hour threshold adds 2 CUs to your quota".
    out = overage_profile("F2", threshold_cu_hours=48)
    assert out["quota_cu_required"] == 2
    assert out["threshold_source"] == "customer"
    assert "customer_question" not in out
    assert out["above_recommended_max"] is True      # 48 > 48 / 3


def test_max_cost_is_derived_threshold_times_three_times_payg():
    out = overage_profile("F2", payg_usd_per_cu_hour=0.18)
    assert out["max_cost_per_day_usd"] == pytest.approx(12 * 3 * 0.18)
    assert out["evidence"] == "derived"
    assert "5 minutes" in out["caveat"]
    assert "exceed" in out["caveat"]


def test_no_price_means_formula_not_number():
    out = overage_profile("F8")
    assert "max_cost_per_day_usd" not in out
    assert "x 3 x payg_usd_per_cu_hour" in out["max_cost_per_day_formula"]


def test_unknown_sku_is_rejected():
    with pytest.raises(KeyError):
        overage_profile("F3")


def _bp(sizing=None, capacity_sku=None):
    platform = {"stack": "fabric", "ownership_boundaries": []}
    if sizing is not None:
        platform["sizing"] = sizing
    if capacity_sku:
        platform["capacity_sku"] = capacity_sku
    return {"schema_version": "0.1.0", "platform": platform, "mesh": {"domains": []}}


def test_recommend_raises_overage_question_for_assigned_sku():
    out = recommend(_bp(capacity_sku="F8"))
    assert out["overage"]["sku"] == "F8"
    assert out["overage"]["threshold_cu_hours"] == 48
    assert out["customer_questions"] == [out["overage"]["customer_question"]]


def test_recommend_uses_floor_when_nothing_assigned():
    out = recommend(_bp(sizing={"largest_model_gb": 4}))
    assert out["recommended_floor"] == "F16"
    assert out["overage"]["sku"] == "F16"


def test_recommend_without_sku_or_floor_has_no_overage_block():
    out = recommend(_bp())
    assert "overage" not in out
    assert "customer_questions" not in out


def test_recommend_passes_payg_price_through():
    out = recommend(_bp(capacity_sku="F2"), prices={"payg_usd_per_cu_hour": 0.2})
    assert out["overage"]["max_cost_per_day_usd"] == pytest.approx(12 * 3 * 0.2)


# --- Fabric Planning -----------------------------------------------------------------

def test_planning_session_rates_match_learn():
    assert PLANNING_SESSION_CU_HOURS == {"planner": 847, "stakeholder": 168, "viewer": 37}
    assert PLANNING_SESSION_HOURS == 730


def test_planning_load_sums_sessions_and_checks_buffer():
    sessions = {"planner": 2, "stakeholder": 10, "viewer": 50}
    out = planning_load(sessions, "F8")
    assert out["cu_hours_per_session_window"] == 2 * 847 + 10 * 168 + 50 * 37  # 5,224
    assert out["average_cu"] == pytest.approx(5224 / 730, abs=0.01)
    assert out["share_of_capacity_pct"] == pytest.approx(89.5, abs=0.1)     # of 8 x 730
    assert out["fits_with_buffer"] is False
    assert planning_load(sessions, "F16")["fits_with_buffer"] is True
    assert "automation jobs" in out["not_included"]


def test_planning_load_without_sku_reports_load_only():
    out = planning_load({"viewer": 10})
    assert out["cu_hours_per_session_window"] == 370
    assert "share_of_capacity_pct" not in out


def test_planning_rejects_unknown_role():
    with pytest.raises(ValueError):
        planning_load({"approver": 1})


def test_skill_names_the_overage_and_planning_figures():
    """The skill must quote the same figures the module computes with (drift guard)."""
    from pathlib import Path

    skill = (Path(__file__).resolve().parents[2] / "docs" / "agent" / "skills"
             / "recommend-fabric-capacity.md").read_text(encoding="utf-8")
    assert "R8" in skill and "overage off, or threshold X" in skill
    assert f"{OVERAGE_PRICE_MULTIPLIER}× the PAYG rate" in skill
    assert f"**{OVERAGE_DEFAULT_THRESHOLD_PCT} %**" in skill
    for role, cu_h in PLANNING_SESSION_CU_HOURS.items():
        assert f"{role.capitalize()} {cu_h}" in skill
