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
    load_cost_drivers,
    load_proposal_defaults,
    load_projection,
    load_role_allocation,
    load_scenarios,
    format_breakdown_capacity,
    format_breakdown_license,
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
    result = compute("compact", product_root=_product_root)
    # F2 262.80 + F4 525.60 + F8 1051.20 = 1839.60; 3 Pro = 42
    expected_capacity = 262.80 + 525.60 + 1051.20
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
    # F2 + F4 + F64 = 262.80 + 525.60 + 8409.60 = 9198; 5 Pro = 70
    expected_cap = 262.80 + 525.60 + 8409.60
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
    # 500 * 0.023 = 11.50 USD/mo
    assert result["storage_month"] == pytest.approx(11.50)
    assert result["storage_breakdown"] is not None
    assert result["storage_breakdown"]["gb"] == 500
    assert result["total_month"] == pytest.approx(1839.60 + 42 + 11.50)
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
