"""
Unit tests for proposal costing cost engine.
Run from product root: py -m pytest tests/ -v
Or from repo root: py -m pytest products/proposal_costing/tests/ -v
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure tooling is on path when running from tests/
_product_root = Path(__file__).resolve().parent.parent
_tooling = _product_root / "tooling"
if str(_tooling) not in sys.path:
    sys.path.insert(0, str(_tooling))

import pytest
from cost_engine import (
    compute,
    compute_projection,
    fill_template,
    format_breakdown_capacity,
    format_breakdown_license,
    format_building_blocks_table,
    format_milestones_table,
    load_cost_drivers,
    load_product_packages,
    load_proposal_defaults,
    load_projection,
    load_role_allocation,
    load_scenarios,
)


def test_load_cost_drivers():
    drivers = load_cost_drivers(_product_root)
    assert "fabric_capacity" in drivers
    assert "power_bi_licenses" in drivers
    assert "onelake_storage" in drivers
    assert drivers["onelake_storage"].get("usd_per_gb_month") == 0.023
    skus = [e["sku"] for e in drivers["fabric_capacity"]]
    assert "F2" in skus and "F64" in skus and "F2048" in skus
    pro = next(e for e in drivers["power_bi_licenses"] if e["id"] == "pro")
    assert pro["price_usd_per_month"] == 14
    ppu = next(e for e in drivers["power_bi_licenses"] if e["id"] == "ppu")
    assert ppu["price_usd_per_month"] == 24


def test_load_scenarios():
    scenarios = load_scenarios(_product_root)
    assert "scenarios" in scenarios
    for sid in ("enterprise", "compact", "power_bi_only", "compact_with_fabric"):
        assert sid in scenarios["scenarios"]


def test_compute_compact():
    # Default region West Europe (proposal_defaults): 0.22 USD per CU hour x 730 h (Azure Retail
    # Prices API, 01.10.2026). F2 321.20 + F4 642.40 + F8 1284.80 = 2248.40; 3 Pro = 42.
    # Until 01.10.2026 every region was priced at the US table (1839.60) - 22 % too low for Europe.
    result = compute("compact", product_root=_product_root)
    expected_capacity = 321.20 + 642.40 + 1284.80
    expected_license = 3 * 14
    assert result["capacity_month"] == pytest.approx(expected_capacity)
    assert result["license_month"] == pytest.approx(expected_license)
    assert result["total_month"] == pytest.approx(expected_capacity + expected_license)
    assert result["total_year"] == pytest.approx(result["total_month"] * 12)
    assert result["scenario_id"] == "compact"
    assert result["pro_users"] == 3
    assert result["ppu_users"] == 0
    assert len(result["capacity_breakdown"]) == 3
    assert len(result["license_breakdown"]) == 2
    assert result["pricing_mode"] == "Pay-as-you-go"
    assert "viewer" in result["viewer_note"].lower() or result["viewer_note"] == ""
    assert result["prod_sku"] == "F8"
    assert "scope_in" in result and "scope_out" in result
    assert "valid_from" in result and "quote_valid_until" in result
    # Building blocks (no FTE => implementation/maintenance 0)
    assert "building_blocks" in result
    ids = [b["id"] for b in result["building_blocks"]]
    assert ids == ["fabric_capacity", "power_bi", "onelake_storage", "implementation", "maintenance"]
    for b in result["building_blocks"]:
        assert "label" in b and "usd_per_month" in b and "usd_per_year" in b
    assert result["building_blocks"][0]["usd_per_month"] == pytest.approx(expected_capacity)
    assert result["building_blocks"][3]["usd_per_year"] == 0
    assert result["building_blocks"][4]["usd_per_year"] == 0


def test_compute_power_bi_only():
    result = compute("power_bi_only", product_root=_product_root)
    assert result["capacity_month"] == 0
    assert result["license_month"] == 10 * 24  # default_ppu_users 10
    assert result["pro_users"] == 0
    assert result["ppu_users"] == 10


def test_compute_with_overrides():
    result2 = compute(
        "compact",
        overrides={"capacities": {"prod": "F64"}, "pro_users": 5},
        product_root=_product_root,
    )
    # West Europe: F2 + F4 + F64 = 321.20 + 642.40 + 10278.40 = 11242; 5 Pro = 70
    expected_cap = 321.20 + 642.40 + 10278.40
    expected_lic = 5 * 14
    assert result2["capacity_month"] == expected_cap
    assert result2["license_month"] == expected_lic
    assert result2["pro_users"] == 5
    assert any(r["sku"] == "F64" for r in result2["capacity_breakdown"])


def test_compute_unknown_scenario():
    with pytest.raises(ValueError, match="Unknown scenario"):
        compute("invalid_scenario", product_root=_product_root)


def test_scenario_skus_in_catalog():
    """All SKUs referenced in scenarios exist in cost_drivers.yaml."""
    drivers = load_cost_drivers(_product_root)
    scenarios = load_scenarios(_product_root)
    valid_skus = {e["sku"] for e in drivers["fabric_capacity"]}
    for sid, scenario in scenarios["scenarios"].items():
        caps = scenario.get("capacities") or {}
        for env, sku in caps.items():
            assert sku in valid_skus, f"Scenario {sid} env {env}: unknown SKU {sku}"


def test_fill_template():
    result = {
        "scenario_id": "compact",
        "capacity_month": 100.5,
        "license_month": 42.0,
        "total_month": 142.5,
        "total_year": 1710.0,
        "capacity_breakdown": [{"environment": "dev", "sku": "F2", "usd_per_month": 100.5}],
        "license_breakdown": [
            {"license": "pro", "users": 3, "usd_per_month": 42.0},
            {"license": "ppu", "users": 0, "usd_per_month": 0.0},
        ],
    }
    t = "Scenario: {{ scenario_id }} | Total/year: {{ total_year }}"
    out = fill_template(result, t)
    assert out == "Scenario: compact | Total/year: 1710.00"
    t2 = "Cap: {{ capacity_breakdown }}"
    out2 = fill_template(result, t2)
    assert "dev" in out2 and "F2" in out2


def test_format_breakdown_capacity_empty():
    assert format_breakdown_capacity([]) == "—"


def test_format_breakdown_license_only_pro():
    assert "PRO" in format_breakdown_license([{"license": "pro", "users": 2, "usd_per_month": 28.0}])


def test_compute_reservation():
    result_payg = compute("compact", product_root=_product_root, use_reservation=False)
    result_res = compute("compact", product_root=_product_root, use_reservation=True)
    assert result_res["pricing_mode"] == "1-year reservation (~41% savings)"
    assert result_res["capacity_month"] < result_payg["capacity_month"]
    assert result_res["total_year"] < result_payg["total_year"]


def test_viewer_note_below_f64():
    result = compute("compact", product_root=_product_root)  # prod F8
    assert result["prod_sku"] == "F8"
    assert "F64" in result["viewer_note"] or "viewer" in result["viewer_note"].lower()
    assert "Pro" in result["viewer_note"] or "pro" in result["viewer_note"].lower()


def test_viewer_note_f64_plus():
    result = compute(
        "compact",
        overrides={"capacities": {"prod": "F64"}},
        product_root=_product_root,
    )
    assert result["prod_sku"] == "F64"
    assert "F64" in result["viewer_note"] or "Free" in result["viewer_note"]


def test_compute_storage_gb():
    result = compute("compact", product_root=_product_root, storage_gb=500)
    # West Europe OneLake hot: 500 * 0.024 = 12.00 USD/mo
    assert result["storage_month"] == pytest.approx(12.00)
    assert result["storage_breakdown"] is not None
    assert result["storage_breakdown"]["gb"] == 500
    assert result["total_month"] == pytest.approx(2248.40 + 42 + 12.00)
    assert result["total_year"] == pytest.approx(result["total_month"] * 12)


def test_load_proposal_defaults():
    defaults = load_proposal_defaults(_product_root)
    assert "scope_in" in defaults
    assert "scope_out" in defaults
    assert "viewer_note_below_f64" in defaults
    assert "default_quote_valid_days" in defaults


def test_fill_template_new_placeholders():
    result = compute("compact", product_root=_product_root)
    t = "{{ pricing_mode }} | {{ valid_from }} | {{ quote_valid_until }}"
    out = fill_template(result, t)
    assert "{{ pricing_mode }}" not in out
    assert "{{ valid_from }}" not in out
    assert "Pay-as-you-go" in out
    assert result["valid_from"] in out
    assert result["quote_valid_until"] in out


def test_compute_implementation_maintenance_fte():
    """Implementation and maintenance from cost_drivers rates; no magic numbers in code."""
    result = compute(
        "compact",
        product_root=_product_root,
        implementation_fte=2.0,
        implementation_months=6.0,
        maintenance_fte=0.5,
    )
    # Rates from cost_drivers.yaml: 15000 per FTE-month, 120000 per FTE-year
    assert result["implementation_one_time"] == pytest.approx(2.0 * 6.0 * 15000)
    assert result["maintenance_year"] == pytest.approx(0.5 * 120000)
    assert result["implementation_fte"] == 2.0
    assert result["implementation_months"] == 6.0
    assert result["maintenance_fte"] == 0.5
    blocks = {b["id"]: b for b in result["building_blocks"]}
    assert blocks["implementation"]["usd_per_year"] == pytest.approx(2.0 * 6.0 * 15000)
    assert blocks["maintenance"]["usd_per_year"] == pytest.approx(0.5 * 120000)


def test_load_role_allocation_empty_when_no_file():
    """Without role_allocation.yaml (only .example exists), allocations are empty."""
    data = load_role_allocation(_product_root)
    assert data["roles_source"] == "core"
    assert data["allocations"] == []


def test_load_role_allocation_from_example():
    """Load role allocation from example file; structure and counts from YAML."""
    data = load_role_allocation(_product_root, path_override="model/role_allocation.yaml.example")
    assert data["roles_source"] == "core"
    assert len(data["allocations"]) == 4
    assert all("role_id" in a and "fte" in a and "phase" in a for a in data["allocations"])


def test_compute_with_role_allocation_derives_fte():
    """When role_allocation_path points to example, implementation_fte and maintenance_fte are derived from allocations."""
    result = compute(
        "compact",
        product_root=_product_root,
        role_allocation_path="model/role_allocation.yaml.example",
    )
    # Example: 0.5+0.3 impl, 0.2+0.1 maint
    assert result["implementation_fte"] == pytest.approx(0.8)
    assert result["maintenance_fte"] == pytest.approx(0.3)
    assert len(result["role_breakdown"]) == 4
    assert result["implementation_one_time"] == pytest.approx(0.8 * (result["implementation_months"] or 0) * 15000)
    assert result["maintenance_year"] == pytest.approx(0.3 * 120000)


def test_load_projection():
    proj = load_projection(_product_root)
    assert "horizons" in proj
    assert "tco_years" in proj
    assert len(proj["horizons"]) >= 1
    assert 3 in proj["tco_years"] and 5 in proj["tco_years"]


def test_compute_projection_returns_horizons_and_tco():
    out = compute_projection("compact", product_root=_product_root)
    assert "horizons" in out
    assert "tco_by_years" in out
    assert "tco_by_year" in out
    assert len(out["horizons"]) == 3  # year1, year2_3, year4_5
    assert out["tco_by_years"].keys() >= {3, 5}
    for h in out["horizons"]:
        assert "id" in h and "label" in h and "total_year" in h and "breakdown" in h


def test_tco_sum_equals_cumulative_by_year():
    """TCO for N years equals sum of tco_by_year rows for year <= N."""
    out = compute_projection("compact", product_root=_product_root)
    by_year = out["tco_by_year"]
    tco_3 = out["tco_by_years"].get(3)
    tco_5 = out["tco_by_years"].get(5)
    assert tco_3 is not None and tco_5 is not None
    sum_3 = sum(r["total"] for r in by_year if r["year"] <= 3)
    sum_5 = sum(r["total"] for r in by_year if r["year"] <= 5)
    assert tco_3 == pytest.approx(sum_3)
    assert tco_5 == pytest.approx(sum_5)


def test_reproducibility_same_inputs_same_output():
    """Same scenario and overrides produce the same result (deterministic)."""
    r1 = compute("compact", overrides={"pro_users": 5}, product_root=_product_root)
    r2 = compute("compact", overrides={"pro_users": 5}, product_root=_product_root)
    assert r1["total_year"] == r2["total_year"]
    assert r1["capacity_month"] == r2["capacity_month"]
    assert r1["license_month"] == r2["license_month"]


def test_compute_includes_tco_rfp_fields():
    """compute() returns sensitivity_note, customer_contributions, implementation_milestones_table; building_blocks have category."""
    result = compute("compact", product_root=_product_root)
    assert "sensitivity_note" in result
    assert "customer_contributions" in result
    assert "implementation_milestones_table" in result
    assert result["sensitivity_note"] != ""
    assert "Änderungen" in result["sensitivity_note"] or "TCO" in result["sensitivity_note"]
    assert "Ansprechpartner" in result["customer_contributions"] or "Kick-off" in result["customer_contributions"]
    assert "Phase" in result["implementation_milestones_table"] and "Deliverable" in result["implementation_milestones_table"]
    for b in result["building_blocks"]:
        assert "category" in b
        assert b["category"] in ("Acquisition", "Operating", "")


def test_format_building_blocks_table_with_category():
    """With category present, table has Kategorie column."""
    blocks = [
        {"id": "a", "label": "A", "category": "Operating", "usd_per_month": 10.0, "usd_per_year": 120.0},
        {"id": "b", "label": "B", "category": "Acquisition", "usd_per_month": 0.0, "usd_per_year": 500.0},
    ]
    out = format_building_blocks_table(blocks)
    assert "Kategorie" in out
    assert "Operating" in out
    assert "Acquisition" in out
    assert "| A |" in out and "| B |" in out


def test_format_milestones_table():
    """format_milestones_table returns Markdown table or — when empty."""
    assert format_milestones_table([]) == "—"
    assert format_milestones_table(None) == "—"
    milestones = [
        {"phase": "P1", "deliverable": "D1", "duration": "W1-2"},
        {"phase": "P2", "deliverable": "D2", "duration": "W3-4"},
    ]
    out = format_milestones_table(milestones)
    assert "Phase" in out and "Deliverable" in out and "Dauer" in out
    assert "P1" in out and "D1" in out and "W1-2" in out


def test_fill_template_tco_rfp_placeholders():
    """fill_template replaces sensitivity_note, customer_contributions, implementation_milestones_table; missing -> —."""
    result = compute("compact", product_root=_product_root)
    t = "S: {{ sensitivity_note }} | C: {{ customer_contributions }} | M: {{ implementation_milestones_table }}"
    out = fill_template(result, t)
    assert "{{ sensitivity_note }}" not in out
    assert "{{ customer_contributions }}" not in out
    assert "{{ implementation_milestones_table }}" not in out
    assert result["sensitivity_note"] in out or "—" not in out  # we have content
    # Missing keys in result should yield —
    minimal = {"scenario_id": "x"}
    out2 = fill_template(minimal, "S: {{ sensitivity_note }} | C: {{ customer_contributions }}")
    assert "—" in out2


def test_load_product_packages():
    """load_product_packages returns dict package_id -> package; empty if file missing."""
    packages = load_product_packages(_product_root)
    assert isinstance(packages, dict)
    assert "starter" in packages
    assert "professional" in packages
    assert packages["starter"]["scenario_id"] == "compact"
    assert packages["starter"].get("implementation_fixed_usd") == 60000
    assert packages["professional"].get("implementation_fte") == 2


def test_compute_with_package_fixed():
    """Package with implementation_fixed_usd uses fixed implementation and maintenance."""
    result = compute("compact", product_root=_product_root, package_id="starter")
    assert result["scenario_id"] == "compact"
    assert result["package_id"] == "starter"
    assert result["package_name"] == "Starter"
    assert result["implementation_one_time"] == 60000
    assert result["maintenance_year"] == 24000
    assert result["capacity_month"] > 0
    assert result["license_month"] > 0


def test_compute_with_package_fte():
    """Package with implementation_fte uses cost_drivers rates."""
    result = compute("compact", product_root=_product_root, package_id="professional")
    assert result["package_id"] == "professional"
    assert result["package_name"] == "Professional"
    assert result["implementation_fte"] == 2
    assert result["implementation_months"] == 6
    assert result["maintenance_fte"] == 0.5
    assert result["implementation_one_time"] == pytest.approx(2 * 6 * 15000)
    assert result["maintenance_year"] == pytest.approx(0.5 * 120000)


def test_compute_unknown_package():
    with pytest.raises(ValueError, match="Unknown package"):
        compute("compact", product_root=_product_root, package_id="nonexistent")


def test_compute_projection_with_package():
    out = compute_projection("compact", product_root=_product_root, package_id="starter", tco_years_list=[3, 5])
    assert out["horizons"]
    first = out["horizons"][0]["breakdown"]
    assert first["package_id"] == "starter"
    assert first["implementation_one_time"] == 60000
    assert 3 in out["tco_by_years"] and 5 in out["tco_by_years"]


def test_fill_template_package_customer_offer():
    """fill_template replaces package_name, customer_name, offer_date."""
    result = compute("compact", product_root=_product_root, package_id="starter")
    result["customer_name"] = "Test Corp"
    result["offer_date"] = "2025-02-15"
    t = "P: {{ package_name }} | C: {{ customer_name }} | D: {{ offer_date }}"
    out = fill_template(result, t)
    assert "Starter" in out
    assert "Test Corp" in out
    assert "2025-02-15" in out
    assert "{{ package_name }}" not in out
    minimal = {"scenario_id": "x"}
    out2 = fill_template(minimal, "P: {{ package_name }} | C: {{ customer_name }}")
    assert "—" in out2


# --- Capacity overage and Fabric Planning (FabCon EU 2026, W1.1 / W4.7) --------------
# Learn facts live in tooling/superversion/capacity.py; these tests check the costing
# lines built on them. All cost figures are derived (threshold x 3 x PAYG), not measured.

from cost_engine import (  # noqa: E402
    compute_overage,
    compute_planning,
    format_overage,
    payg_usd_per_cu_hour,
)


def test_payg_per_cu_hour_derived_from_monthly_price():
    drivers = load_cost_drivers(_product_root)
    # 262.80 USD/month for F2 = 2 CU x 730 h x 0.18 USD
    assert payg_usd_per_cu_hour(drivers, "F2") == pytest.approx(0.18)
    assert payg_usd_per_cu_hour(drivers, "F64") == pytest.approx(0.18)


def test_overage_default_is_open_question_with_derived_daily_max():
    drivers = load_cost_drivers(_product_root)
    ov = compute_overage(drivers, "F8")
    assert ov["enabled"] is True
    assert ov["threshold_source"] == "microsoft_default"
    assert ov["threshold_cu_hours"] == 48            # 25 % of 192
    assert ov["max_usd_per_day"] == pytest.approx(48 * 3 * 0.18)
    assert ov["evidence"] == "derived"
    assert ov["customer_question"]


def test_overage_customer_threshold_and_switch_off():
    drivers = load_cost_drivers(_product_root)
    ov = compute_overage(drivers, "F8", threshold_cu_hours=20)
    assert ov["threshold_source"] == "customer"
    assert ov["customer_question"] is None
    assert ov["max_usd_per_day"] == pytest.approx(20 * 3 * 0.18)
    off = compute_overage(drivers, "F8", enabled=False)
    assert off["enabled"] is False and off["max_usd_per_day"] == 0.0


def test_compute_carries_overage_line_and_customer_question():
    r = compute("compact", product_root=_product_root)
    assert r["overage"]["sku"] == r["prod_sku"]
    assert r["customer_questions"] and "overage" in r["customer_questions"][0].lower()
    decided = compute("compact", {"overage_threshold_cu_hours": 10}, product_root=_product_root)
    assert decided["customer_questions"] == []
    # The overage line never changes the platform total: it is a contingent cost.
    assert decided["total_month"] == r["total_month"]


def test_compute_without_prod_capacity_has_no_overage():
    r = compute("power_bi_only", product_root=_product_root)
    assert r["overage"] is None
    assert r["customer_questions"] == []


def test_template_shows_overage_formula_and_caveat():
    r = compute("compact", product_root=_product_root)
    text = fill_template(r, "{{ overage }}\n{{ customer_questions }}")
    assert "threshold × 3 × PAYG price per CU hour" in text
    assert "derived, not measured" in text
    assert "5 minutes" in text
    assert "{{" not in text
    assert format_overage(None) == "—"


def test_planning_sessions_as_capacity_share_not_added_to_total():
    drivers = load_cost_drivers(_product_root)
    pl = compute_planning(drivers, {"planner": 1, "stakeholder": 5}, "F8")
    assert pl["cu_hours_per_session_window"] == 847 + 5 * 168
    assert pl["usd_equivalent_per_session_window"] == pytest.approx(1687 * 0.18, abs=0.01)
    assert pl["included_in_capacity_total"] is True
    base = compute("compact", product_root=_product_root)
    with_plan = compute("compact", {"planning_sessions": {"planner": 1}}, product_root=_product_root)
    assert with_plan["planning"]["sessions"] == {"planner": 1}
    assert with_plan["total_month"] == base["total_month"]
    text = fill_template(with_plan, "{{ planning }}")
    assert "847 CU hours per 730 h" in text



def test_regional_capacity_price_uses_the_retail_rate():
    """F2 in eastus is the SKU table price; germanywestcentral is 0.22 USD per CU hour."""
    import cost_engine as ce
    drivers = load_cost_drivers()
    us, source = ce.capacity_price_per_month(drivers, "F2", region="East US")
    assert round(us, 2) == 262.80 and source == "region:eastus"
    de, _ = ce.capacity_price_per_month(drivers, "F64", region="germanywestcentral")
    assert round(de, 2) == round(64 * 0.22 * 730, 2)
    eur, _ = ce.capacity_price_per_month(drivers, "F64", region="Germany West Central", currency="EUR")
    assert round(eur, 2) == round(64 * 0.1936 * 730, 2)


def test_unknown_region_falls_back_to_usd_table_only():
    import cost_engine as ce
    drivers = load_cost_drivers()
    price, source = ce.capacity_price_per_month(drivers, "F8", region="mars")
    assert source == "sku_table_us" and price == 1051.20
    with pytest.raises(KeyError):
        ce.capacity_price_per_month(drivers, "F8", region="mars", currency="EUR")


def test_overage_takes_the_regional_rate():
    drivers = load_cost_drivers()
    ov = compute_overage(drivers, "F8", threshold_cu_hours=20, payg_per_cu_hour=0.22)
    assert round(ov["max_usd_per_day"], 2) == round(20 * 3 * 0.22, 2)



def test_planning_share_takes_the_regional_rate():
    """Bis 02.10.2026 rechnete der Planning-Anteil auch in West Europe mit 0.18 USD."""
    we = compute("compact", {"planning_sessions": {"planner": 1}}, product_root=_product_root)
    assert we["planning"]["usd_equivalent_per_session_window"] == pytest.approx(847 * 0.22, abs=0.01)
    us = compute("compact", {"planning_sessions": {"planner": 1}}, product_root=_product_root,
                 region="East US")
    assert us["planning"]["usd_equivalent_per_session_window"] == pytest.approx(847 * 0.18, abs=0.01)


def test_compute_us_region_keeps_the_us_table_price():
    """East US is the region the SKU table was taken from: same numbers as before 01.10.2026."""
    result = compute("compact", product_root=_product_root, region="East US")
    assert result["capacity_month"] == pytest.approx(262.80 + 525.60 + 1051.20)
    assert {row["price_basis"] for row in result["capacity_breakdown"]} == {"region:eastus"}


def test_compute_unknown_region_falls_back_and_says_so():
    result = compute("compact", product_root=_product_root, region="Mars Central")
    assert result["capacity_month"] == pytest.approx(262.80 + 525.60 + 1051.20)
    assert {row["price_basis"] for row in result["capacity_breakdown"]} == {"sku_table_us"}


# --- EUR offers (02.10.2026): Microsoft's EUR list, never a converted USD price -----------------

def test_eur_prices_capacity_licences_and_storage_from_the_eur_lists():
    eur = compute("compact", {"pro_users": 5}, product_root=_product_root, currency="EUR", storage_gb=100)
    assert eur["currency"] == "EUR"
    assert eur["capacity_month"] == pytest.approx(round(2 * 0.1889 * 730, 2) + round(4 * 0.1889 * 730, 2)
                                                  + round(8 * 0.1889 * 730, 2))
    assert eur["license_month"] == pytest.approx(5 * 12.10)
    assert eur["storage_breakdown"]["per_month"] == eur["storage_month"]
    assert all("usd_per_month" not in row for row in eur["capacity_breakdown"] + eur["license_breakdown"])
    assert all("usd_per_month" not in b and "per_month" in b for b in eur["building_blocks"])
    assert eur["price_basis"].endswith("(EUR)")


def test_usd_result_keeps_the_historic_keys():
    usd = compute("compact", product_root=_product_root)
    assert usd["currency"] == "USD"
    row = usd["capacity_breakdown"][0]
    assert row["usd_per_month"] == row["per_month"]
    assert usd["building_blocks"][0]["usd_per_year"] == usd["building_blocks"][0]["per_year"]
    assert usd["overage"]["max_usd_per_day"] == usd["overage"]["max_per_day"]


def test_eur_overage_and_planning_carry_their_currency():
    eur = compute("compact", {"planning_sessions": {"planner": 1}}, product_root=_product_root, currency="EUR")
    assert eur["overage"]["currency"] == "EUR" and "max_usd_per_day" not in eur["overage"]
    assert eur["planning"]["equivalent_per_session_window"] == pytest.approx(847 * 0.1889, abs=0.01)
    assert "usd_equivalent_per_session_window" not in eur["planning"]


def test_eur_without_regional_rate_raises_instead_of_converting():
    with pytest.raises(ValueError, match="EUR rates"):
        compute("compact", product_root=_product_root, currency="EUR", region="Mars Central")


def test_eur_service_prices_are_never_converted_from_usd():
    with pytest.raises(ValueError, match="implementation_eur_per_fte_month"):
        compute("compact", product_root=_product_root, currency="EUR",
                implementation_fte=1, implementation_months=1)
    packages = load_product_packages(_product_root)
    fixed = next(pid for pid, p in packages.items() if p.get("implementation_fixed_usd") is not None)
    with pytest.raises(ValueError, match="implementation_fixed_eur"):
        compute("compact", product_root=_product_root, currency="EUR", package_id=fixed)


def test_unsupported_currency_is_rejected():
    with pytest.raises(ValueError, match="USD or EUR"):
        compute("compact", product_root=_product_root, currency="CHF")


def test_eur_template_shows_eur_and_no_usd():
    eur = compute("compact", {"pro_users": 5}, product_root=_product_root, currency="EUR")
    text = fill_template(eur, (_product_root / "templates" / "proposal_snippet.md").read_text(encoding="utf-8"))
    assert "EUR/month" in text and "USD" not in text and "{{" not in text
