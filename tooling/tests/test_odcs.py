"""
test_odcs.py — bidirectional IR ↔ Open Data Contract Standard mapping (ADR-0051 / I-20.3).
Cross-repo mirror of Meridian's test_odcs.

The gold layer round-trips through ODCS byte-stably; a CREATE TABLE imports to an ODCS schema object;
malformed contracts are reported (not silently accepted). Deterministic.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tooling.generator.export_governed_catalog import SPEC_KEYS, build_governed_catalog

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.odcs import (
    ODCS_API_VERSION,
    emit_odcs,
    emit_odcs_ingestion,
    from_odcs,
    import_sql_table,
    odcs_to_catalog,
    to_odcs,
    to_odcs_ingestion,
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
    assert f"Standard {ODCS_API_VERSION}" in files["contracts/odcs/_CONTRACTS.md"]


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


def test_odcs_ingestion_handover_boundary_contract():
    # mirror of Meridian Stage 0b: one ODCS boundary contract per ingestion source, carrying connector/layer
    inp = {"stack": "fabric", "silver_contract_ref": "contracts/silver.odcs.yaml",
           "domains": [{"name": "Sales", "gold_products": [{"name": "fact_sales", "kind": "fact"}],
                        "sources": [{"source": "s4hana_sd", "source_system": "SAP S/4HANA SD",
                                     "access_mode": "mirror", "handover_layer": "conformed",
                                     "connector": "mirroring", "rationale": "CDC"}]}]}
    bp = derive_blueprint(inp)["blueprint"]
    contracts = to_odcs_ingestion(bp)
    assert len(contracts) == 1 and validate_odcs(contracts[0]) == []
    cps = {p["property"]: p["value"] for p in contracts[0]["customProperties"]}
    assert cps["connector"] == "mirroring" and cps["handover_layer"] == "conformed"
    assert "contracts/odcs/handover/s4hana-sd.handover.odcs.yaml" in emit_odcs_ingestion(bp)
    assert contracts[0]["apiVersion"] == ODCS_API_VERSION
    srv = contracts[0]["servers"][0]
    assert srv["type"] == "custom" and srv["host"] == "SAP S/4HANA SD"      # v3.1/v3.2: host only on custom
    assert srv["customProperties"] == [{"property": "serverTypeHint", "value": "sap"}]


def test_handover_server_is_always_custom_with_type_hint():
    """Meridian D-584: `sap`/`odbc` are not in the ODCS server-type enum (v3.1 nor v3.2), `api`/`azure`
    need fields the handover does not know — every connector yields `type: custom` + `serverTypeHint`.
    Meridian D-586 (v3.2.0): the `hana` connector's hint is the new standard value `hana`."""
    from tooling.superversion.odcs import _CONNECTOR_SERVER_TYPE
    for conn in sorted(_CONNECTOR_SERVER_TYPE) + ["nicht-gelistet", None]:
        bp = {"platform": {"stack": "fabric"},
              "ingestion": [{"source": f"src_{conn}", "connector": conn, "handover_layer": "raw",
                             "access_mode": "copy", "source_system": "SAP S/4HANA"}]}
        (c,) = to_odcs_ingestion(bp)
        srv = c["servers"][0]
        assert srv["type"] == "custom", conn
        assert c["apiVersion"] == ODCS_API_VERSION and validate_odcs(c) == [], conn
        hint = _CONNECTOR_SERVER_TYPE.get(conn, "custom")
        expected = [] if hint == "custom" else [{"property": "serverTypeHint", "value": hint}]
        assert srv.get("customProperties", []) == expected, conn
    assert _CONNECTOR_SERVER_TYPE["hana"] == "hana"
    index = emit_odcs_ingestion(bp)["contracts/odcs/handover/_HANDOVER_CONTRACTS.md"]
    assert f"Standard {ODCS_API_VERSION}" in index


def test_odcs_to_catalog_bridges_contract_to_catalog_shape():
    # mirror of Meridian: an ODCS schema object with properties → {tables:[{name,columns}]}, sorted
    ddl = "CREATE TABLE fact_sales (sales_id INT PRIMARY KEY, customer_sk INT NOT NULL, amount DECIMAL(9,2))"
    cat = odcs_to_catalog({"schema": [import_sql_table(ddl)]})
    assert [(t["name"], t["columns"]) for t in cat["tables"]] == [
        ("fact_sales", ["amount", "customer_sk", "sales_id"])]
    # A-20: `required` aus dem Vertrag reist als `column_specs.nullable` mit (NOT NULL ist ein Fakt)
    assert {s["name"]: s["nullable"] for s in cat["tables"][0]["column_specs"]} == {
        "sales_id": False, "customer_sk": False, "amount": True}
    # to_odcs objects have no properties (IR has no columns) → skipped, honest
    bp = derive_blueprint(_INPUTS)["blueprint"]
    assert odcs_to_catalog(to_odcs(bp)) == {"tables": []}



# --- column_specs ⇄ ODCS (A-20/A-23, Meridian D-581) ------------------------------------------
# Synthetic fixture = Meridian's `test_vertrags_dq.GC`/`BP`, so both repos pin the same semantics.
REPO = Path(__file__).resolve().parents[2]

GC = {
    "schema": "meridian/governed-catalog/v1",
    "tables": [
        {"name": "dim_date", "kind": "dimension", "columns": ["Date", "DateKey"],
         "column_specs": [{"name": "DateKey", "type": "int", "nullable": False}]},
        {"name": "fact_sales", "kind": "fact", "showcase": False,
         "columns": ["DateKey", "Discount %", "End Date", "Promo Type", "Qty", "Start Date"],
         "column_specs": [
             {"name": "DateKey", "type": "date_key", "ref": "dim_date", "unknown_member": -1},
             {"name": "Discount %", "type": "decimal", "nullable": True,
              "checks": [{"between": [0, 1], "when_present": True}]},
             {"name": "Qty", "type": "int", "checks": [{"gte": 0}]},
             {"name": "Promo Type", "type": "text",
              "checks": [{"in": ["Bundle", "None"], "when_present": True}]},
             {"name": "Start Date", "type": "date",
              "checks": [{"lte_column": "End Date", "when_present": True}]},
             {"name": "Margin", "type": "decimal", "target_state": True, "checks": [{"gt": 0}]},
             {"name": "Sales Units", "source_column": "Quantity", "type": "decimal",
              "nullable": False, "checks": [{"gte": 0}]},
         ]},
    ],
}

BP = {
    "platform": {"stack": "fabric"},
    "medallion": {"silver": {"data_contract_ref": "c.yaml"},
                  "gold": {"data_products": [{"name": "dim_date", "kind": "dimension"},
                                             {"name": "fact_sales", "kind": "fact"}]}},
    "mesh": {"domains": [{"name": "Sales", "data_products": ["dim_date", "fact_sales"]}]},
}


def test_column_specs_round_trip_is_lossless():
    contracts = to_odcs(BP, GC)
    assert contracts[0]["apiVersion"] == ODCS_API_VERSION == "v3.2.0"   # eine Version (D-584, v3.2 seit D-586)
    assert validate_odcs(contracts[0]) == []
    back = {t["name"]: t for t in odcs_to_catalog(contracts)["tables"]}
    for t in GC["tables"]:
        assert back[t["name"]]["column_specs"] == t["column_specs"]
        assert back[t["name"]]["columns"] == sorted(t["columns"])
        assert back[t["name"]].get("showcase") == t.get("showcase")


def test_column_specs_use_the_official_odcs_expressions():
    props = {p["name"]: p for p in to_odcs(BP, GC)[0]["schema"][1]["properties"]}
    assert props["DateKey"]["required"] is True
    assert props["DateKey"]["relationships"] == [{"type": "foreignKey", "to": "dim_date.DateKey"}]
    promo = props["Promo Type"]["quality"][0]
    assert (promo["metric"], promo["mustBe"]) == ("invalidValues", 0)
    qty = props["Qty"]["quality"][0]
    assert qty["type"] == "sql" and qty["mustBe"] == 0 and "{object}" in qty["query"]
    assert qty["query"] == "SELECT COUNT(*) FROM {object} WHERE NOT ({property} IS NOT NULL AND {property} >= 0)"
    assert props["Sales Units"]["physicalName"] == "Quantity"
    assert "quality" not in props["Margin"]                  # Zielbild: getragen, nicht ausfuehrbar


def test_without_catalog_needs_no_mirror_and_carries_the_one_version(monkeypatch):
    import tooling.superversion.odcs as odcs_mod

    def _boom():
        raise AssertionError("to_odcs without a catalog must not load the mirror")
    monkeypatch.setattr(odcs_mod, "_provision_dq", _boom)
    assert to_odcs(BP)[0]["apiVersion"] == ODCS_API_VERSION
    assert "properties" not in to_odcs(BP)[0]["schema"][0]


def _domain_catalogs() -> list[tuple[str, dict, dict]]:
    """One (domain, governed catalog, blueprint) per real contract file under
    core/data_contracts/domains — every table the domain owns is a gold product of its domain.

    Per owning domain, as ODCS carries one contract per owning domain; since 29.09.2026 the full
    catalog is unique by table name (``test_catalog_table_names_are_unique``), so a conformed
    table sits in the contract of its owner only.
    """
    full = build_governed_catalog(REPO)
    out = []
    for dom in sorted({t["domain"] for t in full["tables"]}):
        tables = [t for t in full["tables"] if t["domain"] == dom]
        gc = {**full, "tables": tables}
        bp = {
            "platform": {"stack": "fabric"},
            "medallion": {"silver": {"data_contract_ref": f"core/data_contracts/domains/{dom}.yaml"},
                          "gold": {"data_products": [{"name": t["name"], "kind": t["kind"]}
                                                     for t in tables]}},
            "mesh": {"domains": [{"name": dom, "data_products": sorted(t["name"] for t in tables)}]},
        }
        out.append((dom, gc, bp))
    return out


def _normalised(spec: dict) -> dict:
    """The one documented normalisation (Meridian `_property_to_spec`): `nullable: false` beside
    `unknown_member` is redundant — `unknown_member` already means "never NULL"."""
    out = dict(spec)
    if "unknown_member" in out and out.get("nullable") is False:
        out.pop("nullable")
    return out


def test_real_contracts_round_trip_through_odcs():
    """Every column spec of every real contract survives column_specs → ODCS → column_specs."""
    catalogs = _domain_catalogs()
    tables = [t for _, gc, _ in catalogs for t in gc["tables"]]
    specs_total = sum(len(t["column_specs"]) for t in tables)
    checks_total = sum(len(s.get("checks") or []) for t in tables for s in t["column_specs"])
    assert len(catalogs) == len(list((REPO / "core/data_contracts/domains").glob("*.yaml")))
    assert specs_total > 500 and checks_total > 50, (specs_total, checks_total)
    assert {k for t in tables for s in t["column_specs"] for k in s} <= set(SPEC_KEYS)

    compared = 0
    for dom, gc, bp in catalogs:
        contracts = to_odcs(bp, gc)
        assert len(contracts) == 1
        assert contracts[0]["apiVersion"] == ODCS_API_VERSION, dom
        assert validate_odcs(contracts[0]) == [], dom
        assert yaml.safe_load(yaml.safe_dump(contracts[0], sort_keys=False,
                                             allow_unicode=True)) == contracts[0]
        back = {t["name"]: t for t in odcs_to_catalog(contracts)["tables"]}
        assert set(back) == {t["name"] for t in gc["tables"] if t["column_specs"]}, dom
        for t in gc["tables"]:
            if not t["column_specs"]:
                continue
            got = back[t["name"]]
            assert got["columns"] == t["columns"], (dom, t["name"])
            assert got["showcase"] == t["showcase"], (dom, t["name"])
            want = [s for s in (_normalised(s) for s in t["column_specs"]) if len(s) > 1]
            assert got.get("column_specs", []) == want, (dom, t["name"])
            compared += len(t["column_specs"])
    assert compared == specs_total


def test_real_contract_checks_become_executable_quality_rules():
    """Each non-target-state check becomes exactly one ODCS quality rule (sql or invalidValues)."""
    expected = rules = 0
    for _, gc, bp in _domain_catalogs():
        expected += sum(len(s.get("checks") or []) for t in gc["tables"] for s in t["column_specs"]
                        if s.get("target_state") is not True)
        found = [r for c in to_odcs(bp, gc) for o in c["schema"] for p in o.get("properties") or []
                 for r in p.get("quality") or []]
        assert all(r["mustBe"] == 0 and r["type"] in {"sql", "library"} for r in found)
        rules += len(found)
    assert rules == expected > 0


def test_real_contracts_carry_semantic_type_and_synonyms():
    """ODCS v3.2 (Meridian D-590, 30.09.2026): semanticType is derived mechanically (agg → measure,
    ref or a column of a kind:dimension table → dimension, otherwise omitted), synonyms come from the
    contract's curated ``synonyms`` as ``{synonym: …}`` objects; ``context`` is not written.
    Exact ratchet, measured 30.09.2026 on the 109 real tables (750 properties); cross-check by grep
    over core/data_contracts/domains/*.yaml: 231 column lines with ``agg:``, 63 with ``synonyms:``;
    dimension = 199 columns of dimension tables + 207 ``ref`` columns of fact tables."""
    from collections import Counter
    types: Counter = Counter()
    with_syn = terms = 0
    for _, gc, bp in _domain_catalogs():
        for c in to_odcs(bp, gc):
            assert "context" not in yaml.safe_dump(c)
            kinds = {o["name"]: next(cp["value"] for cp in o["customProperties"]
                                     if cp["property"] == "kind") for o in c["schema"]}
            specs = {(t["name"], s["name"]): s for t in gc["tables"] for s in t["column_specs"]}
            for o in c["schema"]:
                for prop in o.get("properties") or []:
                    st = prop.get("semanticType")
                    types[st] += 1
                    spec = specs[(o["name"], prop["name"])]
                    if spec.get("agg"):
                        assert st == "measure", (o["name"], prop["name"])
                    elif spec.get("ref") or kinds[o["name"]] == "dimension":
                        assert st == "dimension", (o["name"], prop["name"])
                    else:
                        assert "semanticType" not in prop, (o["name"], prop["name"])
                    if prop.get("synonyms"):
                        with_syn += 1
                        terms += len(prop["synonyms"])
                        assert [s["synonym"] for s in prop["synonyms"]] == spec["synonyms"]
                    else:
                        assert not spec.get("synonyms")
    assert dict(types) == {"measure": 231, "dimension": 406, None: 113}, dict(types)
    assert (with_syn, terms) == (63, 216)


def test_catalog_table_names_are_unique():
    """Exact ratchet on a measured catalog property. Until 29.09.2026 the same table name lived in
    several domain contracts with DIFFERENT column_specs (139 entries under 108 names; dim_customer,
    dim_date, dim_org, dim_product, fact_inventory, fact_nps, fact_safety, fact_sales), and every
    name-keyed consumer — ``to_odcs`` here, Meridian's ``_katalog_tabelle`` for
    ``emit_dq_gates``/``emit_mlv`` — saw only the first entry. Bus-Matrix since then: one definition
    per table, the other domains refer (``conformed_from``); zero collisions, and the validator
    rejects a second definition. 109 since 29.09.2026: fact_safety_incidents (incident grain)
    split off the monthly fact_safety snapshot."""
    full = build_governed_catalog(REPO)
    by_name: dict[str, list[dict]] = {}
    for t in full["tables"]:
        by_name.setdefault(t["name"], []).append(t)
    colliding = sorted(n for n, ts in by_name.items() if len(ts) > 1)
    assert (len(full["tables"]), len(by_name)) == (109, 109)
    assert colliding == []


def _meridian_root() -> Path | None:
    env = os.environ.get("MERIDIAN_ROOT")
    cand = Path(env).expanduser() if env else REPO.parent / "Freelancing"
    return cand if (cand / "core/dataarch_engine/blueprint/odcs.py").is_file() else None


_MERIDIAN_TO_ODCS = """
import json, sys
from core.dataarch_engine.blueprint.odcs import to_odcs, odcs_to_catalog
bp, gc = json.load(sys.stdin)
c = to_odcs(bp, gc)
json.dump({"contracts": c, "catalog": odcs_to_catalog(c)}, sys.stdout, ensure_ascii=False)
"""


def test_same_output_as_meridian_on_real_contracts():
    """Parity with the home implementation (Meridian `odcs.py`), measured on the real contracts.
    Soft-skip without a Freelancing checkout ($MERIDIAN_ROOT or ../Freelancing)."""
    mer = _meridian_root()
    if mer is None:
        pytest.skip("no Meridian checkout — parity with Meridian's odcs.py not measured")
    full = build_governed_catalog(REPO)
    cases = [(d, gc, bp) for d, gc, bp in _domain_catalogs()]
    # plus the full catalog in one go (unique by name since 29.09.2026, conformed tables included)
    cases.append(("*", full, {
        "platform": {"stack": "fabric"},
        "medallion": {"gold": {"data_products": [{"name": t["name"], "kind": t["kind"]}
                                                 for t in full["tables"]]}},
        "mesh": {"domains": [{"name": "all", "data_products": sorted({t["name"]
                                                                      for t in full["tables"]})}]}}))
    for dom, gc, bp in cases:
        proc = subprocess.run([sys.executable, "-c", _MERIDIAN_TO_ODCS], cwd=str(mer),
                              input=json.dumps([bp, gc]), capture_output=True, text=True,
                              encoding="utf-8", env={**os.environ, "PYTHONPATH": str(mer)})
        if proc.returncode != 0:
            pytest.skip(f"Meridian odcs.py not runnable here: {proc.stderr.strip()[-300:]}")
        theirs = json.loads(proc.stdout)
        ours = to_odcs(copy.deepcopy(bp), copy.deepcopy(gc))
        assert json.loads(json.dumps(ours, ensure_ascii=False)) == theirs["contracts"], dom
        assert json.loads(json.dumps(odcs_to_catalog(ours))) == theirs["catalog"], dom
