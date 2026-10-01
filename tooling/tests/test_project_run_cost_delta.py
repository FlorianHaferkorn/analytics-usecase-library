"""Run-cost delta: an environment decision is priced on the capacities it actually uses."""
from pathlib import Path

import pytest

from tooling.superversion.project_package import alternative_impact as impact
from tooling.superversion.project_package import run_cost_delta as rc

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
PROJECT, DECISION = impact.REFERENCE_PROJECT, impact.REFERENCE_DECISION
DRIVERS = {"valid_from": "2025-02-01", "fabric_capacity": [
    {"sku": "F8", "price_usd_per_month": 1000.0, "reservation_discount_pct": 40},
    {"sku": "F16", "price_usd_per_month": 2000.0, "reservation_discount_pct": 40},
    {"sku": "F64", "price_usd_per_month": 8000.0, "reservation_discount_pct": 40}]}


def _compare(tmp_path, layout):
    repository, revision = impact.build_reference_baseline(tmp_path, SCHEMAS, capacity_layout=layout)
    return rc.compare_run_cost(repository, PROJECT, revision, DECISION, "dev_prod", drivers=DRIVERS)


def test_per_stage_capacities_drop_the_test_capacity(tmp_path):
    report = _compare(tmp_path, "per_stage")
    assert report["status"] == "evaluated" and report["comparable"]
    # F64 reserved (8000 x 0.6) + F8 + F16 -> without test the F16 goes.
    assert report["baseline"]["usd_per_month"] == 4800 + 1000 + 2000
    assert report["alternative"]["usd_per_month"] == 4800 + 1000
    assert report["delta"]["usd_per_month"] == -2000 and report["delta"]["usd_per_year"] == -24000
    assert report["delta"]["capacities_removed"] == [impact.CAPACITY_BY_STAGE["test"]]


def test_prod_non_prod_split_saves_nothing_when_test_is_dropped(tmp_path):
    """D-596: dev and test share one capacity, so dropping test leaves the bill unchanged."""
    report = _compare(tmp_path, "prod_non_prod")
    assert report["delta"]["usd_per_month"] == 0 and not report["delta"]["capacities_removed"]
    shared = next(r for r in report["alternative"]["capacities"] if r["sku"] == "F8")
    assert shared["environments"] == ["dev"]


def test_overage_ceiling_is_reported_but_never_summed(tmp_path):
    side = _compare(tmp_path, "per_stage")["baseline"]
    prod = next(r for r in side["capacities"] if r["sku"] == "F64")
    assert prod["overage"]["enabled"] and prod["overage"]["max_usd_per_month"] > 0
    assert side["usd_per_month"] == sum(r["usd_per_month"] for r in side["capacities"])
    assert side["overage_ceiling_usd_per_month"] == prod["overage"]["max_usd_per_month"]


def test_without_declared_capacities_nothing_is_guessed(tmp_path):
    report = _compare(tmp_path, None)
    assert report["status"] == "not_evaluated" and "not guessed" in report["reason"]


def test_undeclared_capacity_and_unknown_sku_are_unpriced_not_zero():
    arch = {"environments": {"recommended": ["dev", "prod"]},
            "capacities": [{"id": "a", "sku": "F4096"}],
            "physical_workspaces": [{"environment": "prod", "capacity_id": "a"},
                                    {"environment": "dev", "capacity_id": "b"}]}
    side = rc.run_cost_side(arch, DRIVERS)
    assert side["priced_capacities"] == 0 and side["usd_per_month"] == 0
    assert {row["capacity_id"] for row in side["unpriced"]} == {"a", "b"}


def test_the_comparison_leaves_the_baseline_untouched(tmp_path):
    repository, revision = impact.build_reference_baseline(tmp_path, SCHEMAS, capacity_layout="per_stage")
    head = repository.head().revision_hash
    rc.compare_run_cost(repository, PROJECT, revision, DECISION, "dev_prod", drivers=DRIVERS)
    assert repository.head().revision_hash == head == revision


def test_real_cost_drivers_price_the_reference():
    """The shipped list prices carry every SKU the reference uses."""
    drivers = rc._engine().load_cost_drivers()
    for layout in impact.CAPACITY_LAYOUTS.values():
        for row in layout["capacities"]:
            assert rc._engine()._price_by_sku(drivers, row["sku"]) > 0


def test_unknown_layout_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unknown capacity layout"):
        impact.build_reference_baseline(tmp_path, SCHEMAS, capacity_layout="je_domaene")
