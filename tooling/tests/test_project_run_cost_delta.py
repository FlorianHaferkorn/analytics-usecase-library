"""Run-cost delta: an environment decision is priced on the capacities it actually uses."""
from pathlib import Path

import pytest

from tooling.superversion.project_package import alternative_impact as impact
from tooling.superversion.project_package import run_cost_delta as rc

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
PROJECT, DECISION = impact.REFERENCE_PROJECT, impact.REFERENCE_DECISION
#: Synthetic price list: SKU table only, so the reference region falls back to it (USD).
DRIVERS = {"valid_from": "2025-02-01", "power_bi_licenses": [{"id": "pro", "price_usd_per_month": 10}],
           "onelake_storage": {"usd_per_gb_month": 0.5},
           "fabric_capacity": [
               {"sku": "F8", "price_usd_per_month": 1000.0, "reservation_discount_pct": 40},
               {"sku": "F16", "price_usd_per_month": 2000.0, "reservation_discount_pct": 40},
               {"sku": "F64", "price_usd_per_month": 8000.0, "reservation_discount_pct": 40}]}
#: Same, plus a regional rate for the reference region (West Europe) in both currencies.
REGIONAL = {**DRIVERS, "fabric_regions": {"fetched": "2026-10-01", "regions": {"westeurope": {
    "payg_usd_per_cu_hour": 0.25, "payg_eur_per_cu_hour": 0.2,
    "onelake_hot_usd_per_gb_month": 0.03, "onelake_hot_eur_per_gb_month": 0.025}}}}


def _compare(tmp_path, layout, drivers=DRIVERS):
    repository, revision = impact.build_reference_baseline(tmp_path, SCHEMAS, capacity_layout=layout)
    return rc.compare_run_cost(repository, PROJECT, revision, DECISION, "dev_prod", drivers=drivers)


def test_per_stage_capacities_drop_the_test_capacity(tmp_path):
    report = _compare(tmp_path, "per_stage")
    assert report["status"] == "evaluated" and report["comparable"] and report["currency"] == "USD"
    # F64 reserved (8000 x 0.6) + F8 + F16 -> without test the F16 goes.
    assert report["baseline"]["capacity_per_month"] == 4800 + 1000 + 2000
    assert report["alternative"]["capacity_per_month"] == 4800 + 1000
    # F64 in production: 5 authors Pro, 200 viewers free -> 50 USD on both sides.
    assert report["baseline"]["licences"]["per_month"] == 50 and not report["baseline"]["licences"]["viewers_need_pro"]
    assert report["delta"]["per_month"] == -2000 and report["delta"]["per_year"] == -24000
    assert report["delta"]["licence_per_month"] == 0
    assert report["delta"]["capacities_removed"] == [impact.CAPACITY_BY_STAGE["test"]]
    assert report["price_basis"].endswith("US table (region not in cost_drivers.yaml)")


def test_prod_non_prod_split_saves_nothing_when_test_is_dropped(tmp_path):
    """D-596: dev and test share one capacity, so dropping test leaves the bill unchanged."""
    report = _compare(tmp_path, "prod_non_prod")
    assert report["delta"]["per_month"] == 0 and not report["delta"]["capacities_removed"]
    shared = next(r for r in report["alternative"]["capacities"] if r["sku"] == "F8")
    assert shared["environments"] == ["dev", "monitoring"]


def test_overage_ceiling_is_reported_but_never_summed(tmp_path):
    side = _compare(tmp_path, "per_stage")["baseline"]
    prod = next(r for r in side["capacities"] if r["sku"] == "F64")
    assert prod["overage"]["enabled"] and prod["overage"]["max_per_month"] > 0
    assert side["capacity_per_month"] == sum(r["per_month"] for r in side["capacities"])
    assert side["per_month"] == (side["capacity_per_month"] + side["licences"]["per_month"]
                                 + side["monitoring_storage"]["per_month"])
    assert side["overage_ceiling_per_month"] == prod["overage"]["max_per_month"]


def test_regional_rate_prices_the_reference_region(tmp_path):
    report = _compare(tmp_path, "per_stage", REGIONAL)
    f8 = next(r for r in report["baseline"]["capacities"] if r["sku"] == "F8")
    assert f8["per_month"] == round(8 * 0.25 * 730, 2) and f8["price_basis"] == "region:westeurope"
    assert report["baseline"]["monitoring_storage"] == {"retained_gb": 40, "per_gb_month": 0.03, "per_month": 1.2}
    assert report["price_basis"].startswith("Microsoft list price, regional rate")
    assert report["price_valid_from"] == "2026-10-01"


def _arch(prod_sku, **extra):
    return {"environments": {"recommended": ["prod"]}, "region": "West Europe",
            "capacities": [{"id": "p", "sku": prod_sku}],
            "physical_workspaces": [{"environment": "prod", "capacity_id": "p"}],
            "report_audience": {"authors": 3, "viewers": 40}, **extra}


def test_eur_uses_the_eur_rate_and_leaves_licences_unpriced():
    side = rc.run_cost_side(_arch("F16", cost_currency="EUR", monitoring={"retained_gb": 100}), REGIONAL)
    assert side["currency"] == "EUR" and side["capacity_per_month"] == round(16 * 0.2 * 730, 2)
    assert side["licences"]["per_month"] is None and side["licences"]["pro_users"] == 43
    assert side["monitoring_storage"]["per_month"] == 2.5
    assert side["per_month"] == round(16 * 0.2 * 730 + 2.5, 2)
    assert [row["item"] for row in side["unpriced"]] == ["power_bi_licences"]


def test_eur_without_a_regional_rate_is_unpriced_not_converted():
    side = rc.run_cost_side(_arch("F16", cost_currency="EUR"), DRIVERS)
    assert side["priced_capacities"] == 0 and {row["item"] for row in side["unpriced"]} == {"p", "power_bi_licences"}


def test_monitoring_capacity_is_priced_even_without_workspaces():
    arch = _arch("F64", capacities=[{"id": "p", "sku": "F64"}, {"id": "m", "sku": "F8"}],
                 monitoring={"capacity_id": "m"})
    side = rc.run_cost_side(arch, DRIVERS)
    assert {r["capacity_id"]: r["environments"] for r in side["capacities"]} == {"m": ["monitoring"], "p": ["prod"]}
    assert side["capacity_per_month"] == 8000 + 1000


def test_monitoring_capacity_comes_from_the_blueprint_purpose():
    arch = _arch("F64", capacities=[{"id": "p", "sku": "F64"}, {"id": "m", "sku": "F8", "purpose": "monitoring"}])
    side = rc.run_cost_side(arch, DRIVERS)
    assert side["monitoring_capacity"] == {"capacity_id": "m", "source": "capacities[].purpose"}
    assert {r["capacity_id"]: r["environments"] for r in side["capacities"]} == {"m": ["monitoring"], "p": ["prod"]}
    assert side["capacity_per_month"] == 8000 + 1000


def test_explicit_monitoring_id_wins_and_the_disagreement_is_reported():
    arch = _arch("F64", capacities=[{"id": "p", "sku": "F64"}, {"id": "m", "sku": "F8", "purpose": "monitoring"}],
                 monitoring={"capacity_id": "p"})
    host = rc.monitoring_capacity(arch)
    assert host["capacity_id"] == "p" and host["source"] == "monitoring.capacity_id"
    assert "'m'" in host["note"]
    side = rc.run_cost_side(arch, DRIVERS)
    assert [r["capacity_id"] for r in side["capacities"]] == ["p"]


def test_without_monitoring_nothing_hosts_it():
    assert rc.monitoring_capacity(_arch("F64")) is None
    assert rc.run_cost_side(_arch("F64"), DRIVERS)["monitoring_capacity"] is None


def test_without_declared_capacities_nothing_is_guessed(tmp_path):
    report = _compare(tmp_path, None)
    assert report["status"] == "not_evaluated" and "not guessed" in report["reason"]


def test_undeclared_capacity_and_unknown_sku_are_unpriced_not_zero():
    arch = {"environments": {"recommended": ["dev", "prod"]},
            "capacities": [{"id": "a", "sku": "F4096"}],
            "physical_workspaces": [{"environment": "prod", "capacity_id": "a"},
                                    {"environment": "dev", "capacity_id": "b"}]}
    side = rc.run_cost_side(arch, DRIVERS)
    assert side["priced_capacities"] == 0 and side["per_month"] == 0
    assert {row["item"] for row in side["unpriced"]} == {"a", "b"}


def test_the_comparison_leaves_the_baseline_untouched(tmp_path):
    repository, revision = impact.build_reference_baseline(tmp_path, SCHEMAS, capacity_layout="per_stage")
    head = repository.head().revision_hash
    rc.compare_run_cost(repository, PROJECT, revision, DECISION, "dev_prod", drivers=DRIVERS)
    assert repository.head().revision_hash == head == revision


def test_real_cost_drivers_price_the_reference_in_both_currencies():
    """The shipped price list carries every SKU of the reference, in West Europe in USD and EUR."""
    engine = rc._engine()
    drivers = engine.load_cost_drivers()
    for layout in impact.CAPACITY_LAYOUTS.values():
        for row in layout["capacities"]:
            for currency in ("USD", "EUR"):
                price, basis = engine.capacity_price_per_month(drivers, row["sku"], region="West Europe",
                                                               currency=currency)
                assert price > 0 and basis == "region:westeurope"


def test_real_cost_drivers_price_licences_in_eur_from_the_eur_list():
    """Microsoft's EUR list price (12.10 / 20.80, annual billing, excl. VAT), not a converted USD price."""
    engine = rc._engine()
    drivers = engine.load_cost_drivers()
    assert engine._license_prices(drivers, "EUR") == (12.10, 20.80)
    assert engine._license_prices(drivers, "CHF") == (None, None)
    side = rc.run_cost_side(_arch("F16", cost_currency="EUR"), drivers)
    assert side["licences"]["pro_per_user_month"] == 12.10
    assert side["licences"]["per_month"] == round(43 * 12.10, 2)
    assert all(row["item"] != "power_bi_licences" for row in side["unpriced"])


def test_below_f64_every_viewer_pays_pro():
    side = rc.run_cost_side(_arch("F16"), DRIVERS)
    assert side["licences"]["viewers_need_pro"] and side["licences"]["pro_users"] == 43
    assert side["licences"]["per_month"] == 430
    assert side["per_month"] == 2000 + 430


def test_from_f64_viewers_read_free():
    side = rc.run_cost_side(_arch("F64"), DRIVERS)
    assert not side["licences"]["viewers_need_pro"] and side["licences"]["per_month"] == 30


def test_without_audience_no_licence_is_evaluated():
    arch = _arch("F16")
    del arch["report_audience"]
    side = rc.run_cost_side(arch, DRIVERS)
    assert side["licences"] is None and side["per_month"] == side["capacity_per_month"]


def test_unknown_layout_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unknown capacity layout"):
        impact.build_reference_baseline(tmp_path, SCHEMAS, capacity_layout="je_domaene")
