"""source_schema — read the *actual* shape of a source instead of guessing it.

Everything downstream of ingestion (bronze table specs, silver contracts, incremental
watermarks, CLS candidates) has so far rested on declarations: the IR said a source
exists and how it is accessed, never *what is in it*. Only the SAP path had substance,
and only because its pack ships a known catalogue. For every other source the silver
contract had to be hand-authored, which is exactly where a Baukasten stops paying off.

**Why two phases instead of a database client.** Our pipeline can never reach a customer
source: CI has no network to it, no drivers, no credentials — and per the Official-First
scope rule deliverables stay tool-free files, so we must not require the customer to
install anything either. So this module never connects. It

  1. **emits the exact introspection statement** to run against the source, and
  2. **consumes the returned rows** into a normalised schema.

That keeps the honest-by-construction property: we never claim to know a source, we state
precisely what to ask it, and the answer — not an assumption — becomes the contract.
A source whose rows were never supplied stays visibly unknown rather than silently
defaulting to a plausible-looking shape.

`INFORMATION_SCHEMA` is ANSI SQL-92 and implemented by SQL Server, PostgreSQL, MySQL,
Snowflake, Databricks and the Fabric SQL endpoint, so one statement covers them all;
the per-dialect notes below only cover where they genuinely differ. REST sources are read
from their OpenAPI document (`components.schemas`), which is the equivalent public
contract.

Output is the same ODCS schema-object shape `odcs.import_sql_table` already produces, so
there stays exactly one ODCS writer in the repo.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any

# Dialects whose INFORMATION_SCHEMA is close enough to ANSI for one statement, with the
# note that matters when it is not.
SUPPORTED_DIALECTS: dict[str, str] = {
    "ansi": "ANSI SQL-92 INFORMATION_SCHEMA.",
    "sqlserver": "Also exposes sys.* catalogue views; INFORMATION_SCHEMA is sufficient here.",
    "postgres": "Excludes pg_catalog/information_schema below; PostgreSQL lists them otherwise.",
    "mysql": "TABLE_SCHEMA is the database name — pass it via `schemas`.",
    "snowflake": "INFORMATION_SCHEMA is per-database; run once per database.",
    "databricks": "Unity Catalog exposes system.information_schema; run per catalog.",
    "fabric-sql": "Fabric SQL analytics endpoint over a Lakehouse/Warehouse.",
    "oracle": "No INFORMATION_SCHEMA — uses ALL_TAB_COLUMNS (emitted accordingly).",
    "hana": "No INFORMATION_SCHEMA — uses SYS.TABLE_COLUMNS (emitted accordingly). "
            "Covers SAP HANA, S/4HANA and SAP Datasphere (HANA Cloud SQL surface).",
}

# System schemas that are never customer data. Filtered in the emitted statement so the
# result set the customer sends back is already the relevant one.
_SYSTEM_SCHEMAS = ("information_schema", "pg_catalog", "sys", "INFORMATION_SCHEMA")

# INFORMATION_SCHEMA.COLUMNS field names, upper-cased on read so dialect casing
# (PostgreSQL lower-cases, SQL Server upper-cases) stops mattering.
_TABLE_SCHEMA = "TABLE_SCHEMA"
_TABLE_NAME = "TABLE_NAME"
_COLUMN_NAME = "COLUMN_NAME"
_DATA_TYPE = "DATA_TYPE"
_IS_NULLABLE = "IS_NULLABLE"
_POSITION = "ORDINAL_POSITION"
_MAXLEN = "CHARACTER_MAXIMUM_LENGTH"
_PRECISION = "NUMERIC_PRECISION"
_SCALE = "NUMERIC_SCALE"


# HANA's string/binary type names, as the predicate that decides what its single LENGTH
# column means. Kept as one expression so the two CASEs below cannot drift apart.
_HANA_IS_TEXTUAL = ("DATA_TYPE_NAME LIKE '%CHAR%' OR DATA_TYPE_NAME LIKE '%TEXT%' "
                    "OR DATA_TYPE_NAME LIKE '%BINARY%' OR DATA_TYPE_NAME LIKE '%LOB%' "
                    "OR DATA_TYPE_NAME = 'ALPHANUM'")


def _quote_list(values: tuple[str, ...] | list[str]) -> str:
    return ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)


def introspection_sql(dialect: str = "ansi", schemas: list[str] | None = None,
                      tables: list[str] | None = None) -> str:
    """The statement to run against the source; its result set is what `from_information_schema` eats.

    Deliberately one plain SELECT with no temp tables or procedures — it has to be
    runnable by whoever has read access, pasted into whatever client they already use,
    and reviewable by their DBA before they run it. It only reads catalogue metadata,
    never customer data.
    """
    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(
            f"unknown dialect '{dialect}'; supported: {sorted(SUPPORTED_DIALECTS)}"
        )

    if dialect == "oracle":
        # Oracle has no INFORMATION_SCHEMA; ALL_TAB_COLUMNS is the equivalent catalogue.
        owner_filter = (f"\n  AND OWNER IN ({_quote_list(schemas)})" if schemas else "")
        table_filter = (f"\n  AND TABLE_NAME IN ({_quote_list(tables)})" if tables else "")
        return (
            "-- Source introspection (Oracle). Reads catalogue metadata only, no table data.\n"
            "SELECT OWNER            AS TABLE_SCHEMA,\n"
            "       TABLE_NAME       AS TABLE_NAME,\n"
            "       COLUMN_NAME      AS COLUMN_NAME,\n"
            "       DATA_TYPE        AS DATA_TYPE,\n"
            "       NULLABLE         AS IS_NULLABLE,\n"
            "       COLUMN_ID        AS ORDINAL_POSITION,\n"
            "       DATA_LENGTH      AS CHARACTER_MAXIMUM_LENGTH,\n"
            "       DATA_PRECISION   AS NUMERIC_PRECISION,\n"
            "       DATA_SCALE       AS NUMERIC_SCALE\n"
            "FROM ALL_TAB_COLUMNS\n"
            "WHERE OWNER NOT IN ('SYS', 'SYSTEM')"
            f"{owner_filter}{table_filter}\n"
            "ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;\n"
        )

    if dialect == "hana":
        # SAP HANA has no INFORMATION_SCHEMA; SYS.TABLE_COLUMNS is the documented catalogue.
        # Aliased to the ANSI names so `from_information_schema` stays one reader — and so a
        # customer who exports the result cannot tell that the question was dialect-specific.
        # SAP's system schemas are excluded: they are the database's own metadata, never
        # customer data, and they would swamp the result set.
        schema_filter = (f"\n  AND SCHEMA_NAME IN ({_quote_list(schemas)})" if schemas else "")
        table_filter = (f"\n  AND TABLE_NAME IN ({_quote_list(tables)})" if tables else "")
        return (
            "-- Source introspection (SAP HANA / S/4HANA / Datasphere).\n"
            "-- HANA has no INFORMATION_SCHEMA — SYS.TABLE_COLUMNS is the catalogue.\n"
            "-- Reads catalogue metadata only, no table data.\n"
            "SELECT SCHEMA_NAME     AS TABLE_SCHEMA,\n"
            "       TABLE_NAME      AS TABLE_NAME,\n"
            "       COLUMN_NAME     AS COLUMN_NAME,\n"
            "       DATA_TYPE_NAME  AS DATA_TYPE,\n"
            "       IS_NULLABLE     AS IS_NULLABLE,\n"
            "       POSITION        AS ORDINAL_POSITION,\n"
            # HANA keeps one LENGTH column for both meanings: character length for string
            # types, precision for numeric ones. Mapping it to both ANSI columns would lose
            # the scale — the reader prefers the character length, so DECIMAL(10,2) would
            # arrive as DECIMAL(10). Splitting it here keeps the declared type intact.
            f"       CASE WHEN {_HANA_IS_TEXTUAL} THEN LENGTH END\n"
            "                       AS CHARACTER_MAXIMUM_LENGTH,\n"
            f"       CASE WHEN {_HANA_IS_TEXTUAL} THEN NULL ELSE LENGTH END\n"
            "                       AS NUMERIC_PRECISION,\n"
            "       SCALE           AS NUMERIC_SCALE\n"
            "FROM SYS.TABLE_COLUMNS\n"
            "WHERE SCHEMA_NAME NOT LIKE '\\_SYS%' ESCAPE '\\'\n"
            "  AND SCHEMA_NAME NOT IN ('SYS', 'SYSTEM')"
            f"{schema_filter}{table_filter}\n"
            "ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;\n"
        )

    schema_filter = (f"\n  AND TABLE_SCHEMA IN ({_quote_list(schemas)})" if schemas else "")
    table_filter = (f"\n  AND TABLE_NAME IN ({_quote_list(tables)})" if tables else "")
    note = SUPPORTED_DIALECTS[dialect]
    return (
        f"-- Source introspection ({dialect}). {note}\n"
        "-- Reads catalogue metadata only, no table data.\n"
        "SELECT TABLE_SCHEMA,\n"
        "       TABLE_NAME,\n"
        "       COLUMN_NAME,\n"
        "       DATA_TYPE,\n"
        "       IS_NULLABLE,\n"
        "       ORDINAL_POSITION,\n"
        "       CHARACTER_MAXIMUM_LENGTH,\n"
        "       NUMERIC_PRECISION,\n"
        "       NUMERIC_SCALE\n"
        "FROM INFORMATION_SCHEMA.COLUMNS\n"
        f"WHERE TABLE_SCHEMA NOT IN ({_quote_list(_SYSTEM_SCHEMAS)})"
        f"{schema_filter}{table_filter}\n"
        "ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;\n"
    )


def _upper_keys(row: dict[str, Any]) -> dict[str, Any]:
    return {str(k).upper(): v for k, v in row.items()}


def _physical_type(row: dict[str, Any]) -> str:
    """Rebuild the declared type, so `varchar(50)` survives instead of flattening to `varchar`."""
    base = str(row.get(_DATA_TYPE) or "").strip()
    if not base:
        return ""
    maxlen, prec, scale = row.get(_MAXLEN), row.get(_PRECISION), row.get(_SCALE)
    if maxlen not in (None, "", "NULL"):
        try:
            n = int(maxlen)
            return f"{base}({'max' if n < 0 else n})"
        except (TypeError, ValueError):
            pass
    if prec not in (None, "", "NULL"):
        try:
            p = int(prec)
            s = int(scale) if scale not in (None, "", "NULL") else 0
            return f"{base}({p},{s})" if s else f"{base}({p})"
        except (TypeError, ValueError):
            pass
    return base


def _nullable(value: Any) -> bool:
    """`IS_NULLABLE` is 'YES'/'NO' in ANSI and 'Y'/'N' in Oracle."""
    return str(value).strip().upper() in ("YES", "Y", "TRUE", "1")


def parse_rows(payload: str | bytes) -> list[dict[str, Any]]:
    """Accept the result set as JSON array or CSV with a header — whatever the client exported.

    Forcing one export format would just add a manual conversion step for whoever runs
    the query; both are what SQL clients hand out by default.
    """
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    stripped = text.lstrip()
    if stripped.startswith("["):
        data = json.loads(stripped)
        if not isinstance(data, list):
            raise ValueError("JSON payload must be an array of row objects")
        return [r for r in data if isinstance(r, dict)]
    return list(csv.DictReader(io.StringIO(text)))


def from_information_schema(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Result rows → ODCS schema objects, one per table, columns in ordinal order.

    Same object shape as ``odcs.import_sql_table`` so both feed one ODCS writer.
    Primary keys are deliberately absent: ``INFORMATION_SCHEMA.COLUMNS`` does not carry
    them, and inventing a key from a name like ``id`` is exactly the kind of plausible
    guess this module exists to avoid — ``key_candidates`` below proposes them instead,
    marked as proposals.
    """
    from core.dataarch_engine.blueprint.odcs import _logical_type

    by_table: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for raw in rows:
        row = _upper_keys(raw)
        table = str(row.get(_TABLE_NAME) or "").strip()
        column = str(row.get(_COLUMN_NAME) or "").strip()
        if not table or not column:
            continue
        schema = str(row.get(_TABLE_SCHEMA) or "").strip()
        physical = _physical_type(row)
        try:
            position = int(row.get(_POSITION) or 0)
        except (TypeError, ValueError):
            position = 0
        by_table.setdefault((schema, table), []).append({
            "_position": position,
            "name": column,
            "logicalType": _logical_type(physical),
            "physicalType": physical,
            "required": not _nullable(row.get(_IS_NULLABLE)),
        })

    objects: list[dict[str, Any]] = []
    for (schema, table), cols in sorted(by_table.items()):
        cols.sort(key=lambda c: (c["_position"], c["name"]))
        properties = [{k: v for k, v in c.items() if k != "_position"} for c in cols]
        obj: dict[str, Any] = {
            "name": table,
            "physicalName": table,
            "logicalType": "object",
            "physicalType": "table",
            "properties": properties,
        }
        if schema:
            obj["customProperties"] = [{"property": "sourceSchema", "value": schema}]
        objects.append(obj)
    return objects


# --------------------------------------------------------------------------- OpenAPI
_OPENAPI_TO_LOGICAL = {
    "string": "string", "integer": "integer", "number": "number",
    "boolean": "boolean", "array": "array", "object": "object",
}


def from_openapi(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """OpenAPI ``components.schemas`` → the same ODCS schema objects.

    The REST equivalent of INFORMATION_SCHEMA: the published contract of the source.
    Only object schemas with properties become tables — a bare string alias is a type,
    not an entity. ``$ref`` targets are recorded as their referenced name rather than
    inlined, because flattening a reference graph here would invent a shape the API never
    promised.
    """
    schemas = ((spec.get("components") or {}).get("schemas") or {})
    objects: list[dict[str, Any]] = []

    for name, schema in sorted(schemas.items()):
        if not isinstance(schema, dict):
            continue
        props = schema.get("properties")
        if not isinstance(props, dict) or not props:
            continue
        required = set(schema.get("required") or [])
        properties = []
        for prop_name, prop in sorted(props.items()):
            prop = prop if isinstance(prop, dict) else {}
            ref = prop.get("$ref")
            if ref:
                physical, logical = str(ref).rsplit("/", 1)[-1], "object"
            else:
                physical = str(prop.get("format") or prop.get("type") or "string")
                logical = _OPENAPI_TO_LOGICAL.get(str(prop.get("type") or ""), "string")
            properties.append({
                "name": prop_name,
                "logicalType": logical,
                "physicalType": physical,
                "required": prop_name in required,
            })
        objects.append({
            "name": name,
            "physicalName": name,
            "logicalType": "object",
            "physicalType": "object",
            "properties": properties,
        })
    return objects


# --------------------------------------------------------------------------- proposals
def key_candidates(obj: dict[str, Any]) -> list[str]:
    """Columns that *look* like the table's key — a proposal, never applied silently.

    INFORMATION_SCHEMA.COLUMNS carries no key information, so this stays a suggestion the
    workshop confirms. Ordered by how strong the signal is: an exact ``<table>id`` match
    beats a bare ``id``, which beats a trailing ``_key``/``_id``.
    """
    table = str(obj.get("name") or "").lower().rstrip("s")
    names = [str(p.get("name") or "") for p in obj.get("properties") or []]
    exact, bare, suffixed = [], [], []
    for n in names:
        low = n.lower()
        if low in (f"{table}id", f"{table}_id", f"{table}key", f"{table}_key"):
            exact.append(n)
        elif low in ("id", "key"):
            bare.append(n)
        # Matched on the ORIGINAL casing, not lower-cased: `CustomerId` and `customer_id`
        # are both foreign keys, while `valid` and `monkey` merely end in those letters.
        elif n.endswith(("_id", "_key", "Id", "Key", "ID", "KEY")):
            suffixed.append(n)
    return exact + bare + suffixed


def watermark_candidates(obj: dict[str, Any]) -> list[str]:
    """Timestamp columns usable as an incremental watermark — likewise a proposal.

    Feeds the incremental-load decision, which today has to ask the workshop blind.
    """
    out = []
    for prop in obj.get("properties") or []:
        logical = str(prop.get("logicalType") or "")
        name = str(prop.get("name") or "")
        low = name.lower()
        if logical == "date" or "date" in low or "time" in low or low.endswith(("_ts", "_at")):
            out.append(name)
    return out
