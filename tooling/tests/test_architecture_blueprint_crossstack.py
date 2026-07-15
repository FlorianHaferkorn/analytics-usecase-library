"""
test_architecture_blueprint_crossstack.py — ADR-0015 / T7.

The same IR renders to Fabric, Databricks and Snowflake. Guards that the pattern
generalizes: the gold data-product name-set is identical across all renderers and
equals the blueprint's (analogous to targets/test_cross_target_equivalence).
"""
from __future__ import annotations

import json

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion import arch_targets

_FIXTURE = {
    "stack": "fabric",
    "silver_contract_ref": "core/data_contracts/domains/commercial.yaml",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [
                {"name": "dim_customer", "kind": "dimension"},
                {"name": "fact_sales", "kind": "fact"},
                {"name": "agg_margin_by_region", "kind": "aggregate"},
            ],
            "sources": [
                {"source": "crm_orders", "source_system": "Dynamics 365"},
                {"source": "web_events", "source_system": "ADLS Gen2"},
            ],
            "endorsement": "certified",
        }
    ],
}

_STACKS = ("fabric", "databricks", "snowflake")


def _bp():
    return derive_blueprint(_FIXTURE)["blueprint"]


def _gold_names(stack: str, out: dict[str, str]) -> list[str]:
    if stack == "fabric":
        return sorted(p["name"] for p in json.loads(out["fabric/medallion.json"])["gold"]["data_products"])
    if stack == "databricks":
        return sorted(json.loads(out["databricks/unity_catalog.json"])["gold_tables"])
    return sorted(json.loads(out["snowflake/schemas.json"])["gold_tables"])


def test_all_three_registered():
    for s in _STACKS:
        assert s in arch_targets.available()


def test_gold_nameset_identical_across_stacks():
    bp = _bp()
    expected = sorted(p["name"] for p in bp["medallion"]["gold"]["data_products"])
    names = {s: _gold_names(s, arch_targets.render(s, bp)) for s in _STACKS}
    for s in _STACKS:
        assert names[s] == expected, f"{s} gold name-set drifted"
    assert names["fabric"] == names["databricks"] == names["snowflake"]


def test_each_stack_is_deterministic():
    bp = _bp()
    for s in _STACKS:
        assert arch_targets.render(s, bp) == arch_targets.render(s, bp)


def test_ingestion_access_modes_preserved_cross_stack():
    """Access-mode decisions (P1) survive into every renderer's ingestion plan."""
    bp = _bp()
    for s, path in [("fabric", "fabric/ingestion_plan.json"),
                    ("databricks", "databricks/ingestion_plan.json"),
                    ("snowflake", "snowflake/ingestion_plan.json")]:
        plan = {e["source"]: e["access_mode"] for e in json.loads(arch_targets.render(s, bp)[path])}
        assert plan == {"crm_orders": "mirror", "web_events": "shortcut"}


def test_blueprint_ref_passthrough_does_not_break_renderers():
    bp = _bp()
    bp["platform"]["blueprint_ref"] = 2  # Meridian blueprint selection
    for s in _STACKS:
        assert arch_targets.render(s, bp)  # renders without error
