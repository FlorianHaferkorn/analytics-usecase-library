"""
test_architecture_blueprint_derive.py — ADR-0015 / T3.

Guards the deterministic derivation of an ArchitectureBlueprint:
  - a fixture derives to a schema-valid blueprint;
  - derivation is deterministic (same input → identical output);
  - underspecified inputs surface as explicit HITL gaps (never guessed);
  - the grounding surface is gold/silver only (never bronze);
  - the shortcut-vs-mirror access heuristic is deterministic.
"""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tooling.superversion.architecture_blueprint import (
    derive_blueprint,
    validate_blueprint,
    _access_mode,
)
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA = json.loads(
    (_REPO_ROOT / "tooling" / "generator" / "schemas" / "architecture_blueprint.schema.json").read_text(encoding="utf-8")
)

_FIXTURE = {
    "stack": "fabric",
    "silver_contract_ref": "core/data_contracts/domains/commercial.yaml",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [
                {"name": "dim_customer", "kind": "dimension", "grain": "one per customer"},
                {"name": "fact_sales", "kind": "fact", "grain": "one per order line"},
            ],
            "sources": [
                {"source": "crm_orders", "source_system": "Dynamics 365", "sensitivity": "internal"},
                {"source": "web_events", "source_system": "ADLS Gen2"},
            ],
            "endorsement": "certified",
        }
    ],
}


def test_fixture_derives_to_valid_blueprint():
    result = derive_blueprint(_FIXTURE)
    Draft202012Validator(_SCHEMA).validate(result["blueprint"])  # raises on failure
    validate_blueprint(result["blueprint"])  # module helper agrees


def test_derivation_is_deterministic():
    a = derive_blueprint(_FIXTURE)
    b = derive_blueprint(_FIXTURE)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_gold_products_retain_their_declared_domain_owner():
    result = derive_blueprint({
        "stack": "fabric",
        "silver_contract_ref": "domains/all.yaml",
        "domains": [
            {"name": "Platform", "gold_products": [
                {"name": "dim_organisation", "kind": "dimension"}]},
            {"name": "Infrastructure", "gold_products": [
                {"name": "fact_projektmonat", "kind": "fact"}]},
        ],
    })
    products = result["blueprint"]["medallion"]["gold"]["data_products"]
    assert {p["name"]: p["domain"] for p in products} == {
        "dim_organisation": "Platform",
        "fact_projektmonat": "Infrastructure",
    }
    Draft202012Validator(_SCHEMA).validate(result["blueprint"])


def test_missing_gold_products_becomes_hitl():
    inputs = {
        "stack": "fabric",
        "silver_contract_ref": "x.yaml",
        "domains": [{"name": "Finance"}],  # no gold_products
    }
    result = derive_blueprint(inputs)
    assert any("gold.data_products" in g and "Finance" in g for g in result["hitl"])
    # still schema-valid (empty gold list is allowed; the gap is flagged, not guessed)
    Draft202012Validator(_SCHEMA).validate(result["blueprint"])


def test_missing_silver_ref_becomes_hitl():
    result = derive_blueprint({"stack": "fabric", "domains": [{"name": "Ops", "gold_products": [
        {"name": "fact_x", "kind": "fact"}]}]})
    assert any("silver.data_contract_ref" in g for g in result["hitl"])


def test_grounding_surface_is_gold_silver_only():
    bp = derive_blueprint(_FIXTURE)["blueprint"]
    assert bp["ai_grounding"]["grounding_surface"] == ["gold", "silver"]
    assert "bronze" not in bp["ai_grounding"]["grounding_surface"]


def test_access_mode_heuristic():
    assert _access_mode("Dynamics 365 SQL database") == "mirror"
    assert _access_mode("ADLS Gen2") == "shortcut"
    assert _access_mode(None) == "shortcut"  # safe default: virtualize


def test_access_mode_explicit_override_wins():
    inputs = {
        "stack": "fabric",
        "silver_contract_ref": "x.yaml",
        "domains": [{"name": "D", "gold_products": [{"name": "fact_y", "kind": "fact"}],
                     "sources": [{"source": "s", "source_system": "some DB", "access_mode": "copy",
                                  "rationale": "compliance requires a physical copy"}]}],
    }
    bp = derive_blueprint(inputs)["blueprint"]
    assert bp["ingestion"][0]["access_mode"] == "copy"
