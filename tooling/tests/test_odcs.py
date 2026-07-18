"""
test_odcs.py — bidirectional IR ↔ Open Data Contract Standard mapping (ADR-0051 / I-20.3).
Cross-repo mirror of Meridian's test_odcs.

The gold layer round-trips through ODCS byte-stably; a CREATE TABLE imports to an ODCS schema object;
malformed contracts are reported (not silently accepted). Deterministic.
"""
from __future__ import annotations

import pytest
import yaml

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.odcs import (
    ODCS_API_VERSION,
    emit_odcs,
    from_odcs,
    import_sql_table,
    to_odcs,
    validate_odcs,
)

_INPUTS = {
    "stack": "fabric", "silver_contract_ref": "domains/commercial.yaml",
    "domains": [
        {"name": "Commercial",
         "gold_products": [{"name": "dim_customer", "kind": "dimension"},
                           {"name": "fact_sales", "kind": "fact", "grain": "order line"}],
         "sources": [{"source": "crm", "source_system": "Dynamics 365 db"}],
         "endorsement": "certified", "intended_audience": "partner"},
        {"name": "Finance",
         "gold_products": [{"name": "fact_ledger", "kind": "fact", "grain": "journal line"}],
         "sources": [{"source": "erp", "source_system": "SAP"}]},
    ],
}


def _bp():
    return derive_blueprint(_INPUTS)["blueprint"]


def test_to_odcs_one_contract_per_domain_deterministic():
    contracts = to_odcs(_bp())
    assert [c["domain"] for c in contracts] == ["Commercial", "Finance"]
    c0 = contracts[0]
    assert c0["apiVersion"] == ODCS_API_VERSION and c0["kind"] == "DataContract"
    assert c0["id"] == "fabric-commercial"
    assert [s["name"] for s in c0["schema"]] == ["dim_customer", "fact_sales"]
    fact = next(s for s in c0["schema"] if s["name"] == "fact_sales")
    props = {cp["property"]: cp["value"] for cp in fact["customProperties"]}
    assert props["kind"] == "fact" and props["grain"] == "order line"
    assert to_odcs(_bp()) == to_odcs(_bp())


def test_gold_layer_round_trips_through_odcs():
    bp = _bp()
    bp2 = derive_blueprint(from_odcs(to_odcs(bp)))["blueprint"]
    assert bp2["medallion"]["gold"] == bp["medallion"]["gold"]
    assert bp2["medallion"]["silver"] == bp["medallion"]["silver"]
    assert [d["data_products"] for d in bp2["mesh"]["domains"]] == \
        [d["data_products"] for d in bp["mesh"]["domains"]]
    assert bp2["mesh"]["domains"][0]["publishing"] == bp["mesh"]["domains"][0]["publishing"]
    assert bp2["ingestion"] == []          # honest scope: ingestion not in the gold contract


def test_emit_odcs_yaml_is_valid_and_parses():
    files = emit_odcs(_bp())
    assert "contracts/odcs/commercial.odcs.yaml" in files
    assert "contracts/odcs/_CONTRACTS.md" in files
    parsed = yaml.safe_load(files["contracts/odcs/commercial.odcs.yaml"])
    assert parsed["dataProduct"] == "Commercial"
    assert validate_odcs(parsed) == []
    assert emit_odcs(_bp()) == emit_odcs(_bp())


def test_validate_flags_schema_violations():
    assert "missing required field 'id'" in validate_odcs({"apiVersion": "v3.0.0", "kind": "DataContract"})
    bad_kind = {"apiVersion": "v3.0.0", "kind": "Nope", "id": "x", "name": "x",
                "version": "1.0.0", "status": "active", "schema": [{}]}
    problems = validate_odcs(bad_kind)
    assert any("kind must be" in p for p in problems)
    assert any("schema[0] missing 'name'" in p for p in problems)


def test_import_sql_table_maps_types_and_keys():
    ddl = """
    CREATE TABLE sales.fact_orders (
        order_id      BIGINT       NOT NULL PRIMARY KEY,
        customer_id   INT          NOT NULL,
        amount        DECIMAL(9,2),
        ordered_at    TIMESTAMP,
        is_paid       BOOLEAN,
        note          VARCHAR(200)
    );
    """
    obj = import_sql_table(ddl)
    assert obj["name"] == "fact_orders"
    assert obj["logicalType"] == "object"
    by_name = {p["name"]: p for p in obj["properties"]}
    assert by_name["order_id"]["logicalType"] == "integer"
    assert by_name["order_id"]["primaryKey"] is True and by_name["order_id"]["required"] is True
    assert by_name["amount"]["logicalType"] == "number"
    assert by_name["ordered_at"]["logicalType"] == "date"
    assert by_name["is_paid"]["logicalType"] == "boolean"
    assert by_name["note"]["logicalType"] == "string"
    assert by_name["customer_id"]["required"] is True


def test_import_sql_without_create_table_raises():
    with pytest.raises(ValueError, match="no CREATE TABLE"):
        import_sql_table("SELECT 1")
