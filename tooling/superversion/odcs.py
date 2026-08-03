"""odcs — bidirectional mapping between the neutral IR and the Open Data Contract Standard (I-20.3).

Cross-repo mirror of Meridian's `core.dataarch_engine.blueprint.odcs` (contract surface). Official-First
(ADR-0051): the gold data contract is expressed in **ODCS** (Bitol Open Data Contract Standard v3.0.0),
not a home-grown format. This module bridges the two directions the Baukasten needs:

  * **export** ``to_odcs(blueprint)`` — one ODCS ``DataContract`` per mesh domain; each gold product
    becomes a schema object (``kind``/``grain`` preserved via ``customProperties`` so the round-trip is
    lossless for the gold/mesh layer). ``emit_odcs(blueprint)`` renders these as ``path → YAML`` files.
  * **import** ``from_odcs(contracts)`` — reconstructs the deriver ``inputs`` domains fragment, so an
    existing contract set re-derives an identical ``medallion``/``mesh`` IR (bottom-up seed).
  * **SQL import** ``import_sql_table(ddl)`` — a single ``CREATE TABLE`` → an ODCS schema object.
  * **catalog bridge** ``odcs_to_catalog(contracts)`` — an ODCS contract set → the ``governed_catalog``
    shape the emitters consume (the governed contract drives column projection; Meridian-side consumer).

Honest scope: ODCS carries the **gold contract** (data products + their schema), not the bronze
ingestion sources — so the round-trip is exact for ``medallion.gold`` + ``mesh.domains[].data_products``,
and ingestion is intentionally out of the contract. Deterministic: sorted, no timestamps, no randomness.
"""
from __future__ import annotations

import re
from typing import Any

import yaml

from tooling.superversion.architecture_blueprint import _slug

ODCS_API_VERSION = "v3.0.0"
ODCS_KIND = "DataContract"
_CONTRACT_STANDARD = "odcs"

# ODCS v3 logical types: string · integer · number · boolean · object · array · date.
_SQL_TYPE_TO_LOGICAL = [
    (re.compile(r"^(tinyint|smallint|int|integer|bigint)\b", re.I), "integer"),
    (re.compile(r"^(decimal|numeric|number|float|real|double|money|smallmoney)\b", re.I), "number"),
    (re.compile(r"^(bit|bool|boolean)\b", re.I), "boolean"),
    (re.compile(r"^(date|datetime2?|smalldatetime|timestamp|datetimeoffset|time)\b", re.I), "date"),
]


def _logical_type(sql_type: str) -> str:
    for rx, logical in _SQL_TYPE_TO_LOGICAL:
        if rx.match(sql_type.strip()):
            return logical
    return "string"  # varchar/char/nvarchar/text/uuid/… — safe default


# --------------------------------------------------------------------------- export (IR → ODCS)
def _schema_object(product: dict[str, Any]) -> dict[str, Any]:
    """One gold product → an ODCS schema object; kind/grain survive as customProperties."""
    custom = [{"property": "kind", "value": product["kind"]}]
    if product.get("grain"):
        custom.append({"property": "grain", "value": product["grain"]})
    return {
        "name": product["name"],
        "physicalName": product["name"],
        "logicalType": "object",
        "physicalType": "table",
        "customProperties": custom,
    }


def to_odcs(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Export the IR's gold/mesh layer as one ODCS ``DataContract`` per domain (sorted, deterministic)."""
    stack = blueprint.get("platform", {}).get("stack", "fabric")
    gold = blueprint.get("medallion", {}).get("gold", {}).get("data_products", [])
    gold_by_name = {p["name"]: p for p in gold}
    contract_ref = blueprint.get("medallion", {}).get("silver", {}).get("data_contract_ref")

    contracts: list[dict[str, Any]] = []
    for dom in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        name = dom["name"]
        pub = dom.get("publishing", {})
        schema = [
            _schema_object(gold_by_name[pn])
            for pn in sorted(dom.get("data_products", []))
            if pn in gold_by_name
        ]
        contract: dict[str, Any] = {
            "apiVersion": ODCS_API_VERSION,
            "kind": ODCS_KIND,
            "id": f"{_slug(stack)}-{_slug(name)}",
            "name": name,
            "version": "1.0.0",
            "status": "active",
            "domain": name,
            "dataProduct": name,
            "description": {
                "purpose": f"Gold data products owned by the {name} domain (single owning domain).",
            },
            "schema": schema,
            "customProperties": [
                {"property": "endorsement", "value": pub.get("endorsement", "promoted")},
                {"property": "intended_audience", "value": pub.get("intended_audience", "internal")},
            ],
        }
        if contract_ref:
            contract["customProperties"].append(
                {"property": "silver_contract_ref", "value": contract_ref})
        contracts.append(contract)
    return contracts


def _yaml(contract: dict[str, Any]) -> str:
    """Deterministic YAML (insertion order preserved, no aliases)."""
    return yaml.safe_dump(contract, sort_keys=False, allow_unicode=True, default_flow_style=False)


def emit_odcs(blueprint: dict[str, Any]) -> dict[str, str]:
    """Return the ODCS contract set as ``path → content`` (one file per domain + an index)."""
    contracts = to_odcs(blueprint)
    out: dict[str, str] = {}
    index = ["# ODCS data contracts (generated — ADR-0051 / Official-First)", "",
             "Open Data Contract Standard v3.0.0 · one contract per governance domain "
             "(data product = single owning domain).", "",
             "| Domain | Contract | Data products |", "|---|---|---|"]
    for c in contracts:
        rel = f"contracts/odcs/{_slug(c['domain'])}.odcs.yaml"
        out[rel] = _yaml(c)
        products = ", ".join(f"`{s['name']}`" for s in c["schema"]) or "—"
        index.append(f"| {c['domain']} | `{rel}` | {products} |")
    index.append("")
    out["contracts/odcs/_CONTRACTS.md"] = "\n".join(index) + "\n"
    return out


# --------------------------------------------------------------------------- handover boundary (ingestion/silver)
# Cross-repo mirror of Meridian's Stage-0b ODCS-beyond-gold: govern the inbound SAP→Fabric interface —
# one boundary contract per ingestion source, carrying handover_layer + connector + access_mode.
_CONNECTOR_SERVER_TYPE = {
    "odbc-live": "odbc", "odbc-copy": "odbc", "hana": "sap", "odata": "api",
    "premium-outbound-shortcut": "azure", "mirroring": "sap", "sap-cdc": "sap",
    "open-mirroring": "custom", "bdc-connect": "sap",
}


def _handover_schema_object(entry: dict[str, Any]) -> dict[str, Any]:
    custom = [{"property": "handover_layer", "value": entry.get("handover_layer") or "unspecified"},
              {"property": "access_mode", "value": entry.get("access_mode", "")}]
    if entry.get("connector"):
        custom.append({"property": "connector", "value": entry["connector"]})
    return {
        "name": _slug(entry["source"]).replace("-", "_"),
        "physicalName": entry["source"],
        "logicalType": "object",
        "physicalType": "table",
        "description": "Inbound dataset crossing the SAP→Fabric handover boundary; inbound columns are "
                       "governed by the silver data contract (referenced, not invented here).",
        "customProperties": custom,
    }


def to_odcs_ingestion(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Export the ingestion/handover boundary as ODCS ``DataContract``s — one per ingestion source
    (mirror of Meridian; governs the inbound SAP→Fabric interface beyond the gold ``to_odcs`` scope)."""
    stack = blueprint.get("platform", {}).get("stack", "fabric")
    contract_ref = blueprint.get("medallion", {}).get("silver", {}).get("data_contract_ref")
    contracts: list[dict[str, Any]] = []
    for e in sorted(blueprint.get("ingestion", []), key=lambda e: e.get("source", "")):
        connector = e.get("connector")
        server: dict[str, Any] = {
            "server": "sap-source",
            "type": _CONNECTOR_SERVER_TYPE.get(connector, "custom"),
            "description": f"handover via {connector or 'unspecified connector'} at the "
                           f"{e.get('handover_layer') or 'unspecified'} layer",
        }
        if e.get("source_system"):
            server["host"] = e["source_system"]
        custom = [{"property": "layer", "value": "ingestion/handover-boundary"},
                  {"property": "handover_layer", "value": e.get("handover_layer") or "unspecified"}]
        if connector:
            custom.append({"property": "connector", "value": connector})
        if contract_ref:
            custom.append({"property": "silver_contract_ref", "value": contract_ref})
        contracts.append({
            "apiVersion": ODCS_API_VERSION,
            "kind": ODCS_KIND,
            "id": f"{_slug(stack)}-handover-{_slug(e['source'])}",
            "name": e["source"],
            "version": "1.0.0",
            "status": "active",
            "dataProduct": e["source"],
            "description": {"purpose": f"SAP→Fabric handover boundary contract for source '{e['source']}'."},
            "servers": [server],
            "schema": [_handover_schema_object(e)],
            "customProperties": custom,
        })
    return contracts


def emit_odcs_ingestion(blueprint: dict[str, Any]) -> dict[str, str]:
    """Return the handover-boundary ODCS contracts as ``path → content`` (one file per source + index)."""
    contracts = to_odcs_ingestion(blueprint)
    out: dict[str, str] = {}
    index = ["# ODCS handover-boundary contracts (generated — Fahrplan Stage 0b)", "",
             "Open Data Contract Standard v3.0.0 · one contract per **ingestion source** — governs the "
             "inbound SAP→Fabric interface (raw/conformed/silver), beyond the gold `to_odcs` scope.", "",
             "| Source | Handover layer | Connector | Contract |", "|---|---|---|---|"]
    for c in contracts:
        rel = f"contracts/odcs/handover/{_slug(c['name'])}.handover.odcs.yaml"
        out[rel] = _yaml(c)
        layer = _custom(c, "handover_layer") or "—"
        connector = _custom(c, "connector") or "—"
        index.append(f"| `{c['name']}` | {layer} | {connector} | `{rel}` |")
    index.append("")
    out["contracts/odcs/handover/_HANDOVER_CONTRACTS.md"] = "\n".join(index) + "\n"
    return out


# --------------------------------------------------------------------------- import (ODCS → IR)
def _custom(contract_or_object: dict[str, Any], key: str) -> Any:
    for cp in contract_or_object.get("customProperties", []) or []:
        if cp.get("property") == key:
            return cp.get("value")
    return None


def from_odcs(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct the deriver ``inputs`` domains fragment from an ODCS contract set (bottom-up seed).

    Recovers domains + gold_products (name/kind/grain) + publishing hints + silver_contract_ref, so
    ``derive_blueprint(from_odcs(to_odcs(bp)))`` reproduces an identical ``medallion``/``mesh``. Ingestion
    is intentionally not in the gold contract (honest scope) → the imported inputs carry no ``sources``.
    """
    domains: list[dict[str, Any]] = []
    silver_ref: str | None = None
    for c in sorted(contracts, key=lambda c: c.get("domain") or c.get("name", "")):
        name = c.get("domain") or c.get("name")
        gold_products: list[dict[str, Any]] = []
        for obj in c.get("schema", []):
            gp: dict[str, Any] = {"name": obj["name"], "kind": _custom(obj, "kind") or "dimension"}
            grain = _custom(obj, "grain")
            if grain:
                gp["grain"] = grain
            gold_products.append(gp)
        gold_products.sort(key=lambda p: p["name"])
        dom: dict[str, Any] = {"name": name, "gold_products": gold_products}
        endorsement = _custom(c, "endorsement")
        audience = _custom(c, "intended_audience")
        if endorsement:
            dom["endorsement"] = endorsement
        if audience:
            dom["intended_audience"] = audience
        domains.append(dom)
        silver_ref = silver_ref or _custom(c, "silver_contract_ref")
    inputs: dict[str, Any] = {"domains": domains}
    if silver_ref:
        inputs["silver_contract_ref"] = silver_ref
    return inputs


def odcs_to_catalog(contracts: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    """Bridge an ODCS contract set → the ``governed_catalog`` shape the Meridian emitters consume.

    Cross-repo mirror of Meridian's ``odcs_to_catalog`` (contract surface). Returns
    ``{"tables": [{"name", "columns"}]}`` — one entry per schema object that declares ``properties``
    (columns); objects without columns are skipped (nothing to project, honest). Deterministic (sorted).
    """
    if isinstance(contracts, dict):
        contracts = [contracts]
    tables: list[dict[str, Any]] = []
    for c in contracts:
        for obj in c.get("schema", []) or []:
            cols = sorted({p["name"] for p in (obj.get("properties") or []) if p.get("name")})
            if not cols:
                continue
            tables.append({"name": obj.get("physicalName") or obj.get("name"), "columns": cols})
    tables.sort(key=lambda t: t.get("name") or "")
    return {"tables": tables}


def import_sql_table(ddl: str) -> dict[str, Any]:
    """Parse a single ``CREATE TABLE`` DDL into one ODCS schema object (datacontract-cli import pattern).

    Honest scope: one table, column ``name type`` pairs, ``PRIMARY KEY``/``NOT NULL`` flags. Table-level
    constraints and multi-statement scripts are out of scope (a real DB import would use the CLI).
    """
    m = re.search(r"create\s+table\s+(?:if\s+not\s+exists\s+)?([^\s(]+)\s*\((.*)\)",
                  ddl, re.I | re.S)
    if not m:
        raise ValueError("no CREATE TABLE statement found")
    raw_name = m.group(1).strip().strip('`"[]')
    table_name = raw_name.split(".")[-1].strip('`"[]')  # drop schema qualifier
    body = m.group(2)

    # split on top-level commas (ignore commas inside type parens like decimal(9,2))
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur))

    pk_cols: set[str] = set()
    properties: list[dict[str, Any]] = []
    for part in parts:
        line = part.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith(("primary key", "constraint", "foreign key", "unique", "key ", "index ")):
            for col in re.findall(r"[`\"\[]?([A-Za-z_][A-Za-z0-9_]*)[`\"\]]?", line[low.find("(") + 1:] if "(" in line else ""):
                pk_cols.add(col)
            continue
        cm = re.match(r"[`\"\[]?([A-Za-z_][A-Za-z0-9_]*)[`\"\]]?\s+([A-Za-z0-9_]+(?:\s*\([^)]*\))?)(.*)$",
                      line)
        if not cm:
            continue
        col_name, col_type, rest = cm.group(1), cm.group(2), cm.group(3).lower()
        prop: dict[str, Any] = {
            "name": col_name,
            "logicalType": _logical_type(col_type),
            "physicalType": col_type.strip(),
            "required": "not null" in rest or "primary key" in rest,
        }
        if "primary key" in rest:
            prop["primaryKey"] = True
            pk_cols.add(col_name)
        properties.append(prop)

    for prop in properties:
        if prop["name"] in pk_cols:
            prop["primaryKey"] = True
            prop["required"] = True

    return {
        "name": table_name,
        "physicalName": table_name,
        "logicalType": "object",
        "physicalType": "table",
        "properties": properties,
    }


# --------------------------------------------------------------------------- validation
_REQUIRED_TOP = ("apiVersion", "kind", "id", "name", "version", "status")


def validate_odcs(contract: dict[str, Any]) -> list[str]:
    """Return a list of ODCS conformance violations (empty = valid). Structural, deterministic."""
    problems: list[str] = []
    for field in _REQUIRED_TOP:
        if not contract.get(field):
            problems.append(f"missing required field '{field}'")
    if contract.get("kind") and contract["kind"] != ODCS_KIND:
        problems.append(f"kind must be '{ODCS_KIND}', got {contract['kind']!r}")
    schema = contract.get("schema")
    if schema is None:
        problems.append("missing 'schema' (a DataContract must declare at least one object)")
    else:
        for i, obj in enumerate(schema):
            if not obj.get("name"):
                problems.append(f"schema[{i}] missing 'name'")
    return problems
