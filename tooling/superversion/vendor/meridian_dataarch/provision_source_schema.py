"""provision_source_schema — emit the introspection ask, and the contracts once it is answered.

Phase 1 (always): one runnable statement per source plus a README that says who runs it and
what comes back. Phase 2 (when result rows are supplied): the real source shape becomes
bronze table specs and a grounded silver contract instead of a hand-authored guess.

The split is not ceremony — it is the only honest shape available. Our pipeline cannot
reach a customer source, so a module that claimed to know the schema would be inventing it.
Emitting the exact question keeps the unknown visible until it is actually answered.
"""
from __future__ import annotations

import json
from typing import Any

from core.dataarch_engine.blueprint.source_schema import (
    SUPPORTED_DIALECTS,
    from_information_schema,
    from_openapi,
    introspection_sql,
    key_candidates,
    watermark_candidates,
)

# Which introspection a source needs, by what the IR already records about it. REST/file
# sources have no INFORMATION_SCHEMA; naming them explicitly keeps the fallback honest.
_REST_HINTS = ("rest", "api", "odata", "openapi", "graphql")
_FILE_HINTS = ("adls", "blob", "s3", "gcs", "file", "csv", "parquet", "lake")


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(text)).strip("_").lower()


def source_kind(entry: dict[str, Any]) -> str:
    """``sql`` · ``rest`` · ``file`` — decides which introspection applies.

    Read from ``source_system``/``connector``, never from the source *name*: a name
    convention that drifts would silently route a database to the REST branch.
    """
    haystack = " ".join([
        str(entry.get("source_system") or ""),
        str(entry.get("connector") or ""),
    ]).lower()
    if any(h in haystack for h in _REST_HINTS):
        return "rest"
    if any(h in haystack for h in _FILE_HINTS):
        return "file"
    return "sql"


def dialect_for(entry: dict[str, Any]) -> str:
    """Best-known dialect for a source; ``ansi`` when the system string says nothing."""
    system = str(entry.get("source_system") or "").lower()
    connector = str(entry.get("connector") or "").lower()

    # SAP first: `s/4hana` also contains no other vendor's marker, but "hana" must be seen
    # before the ANSI fallback. HANA has no INFORMATION_SCHEMA, so falling through to `ansi`
    # would hand the customer a statement that simply errors on their system — the one
    # outcome this module exists to avoid. Datasphere shares HANA Cloud's SQL surface.
    if ("hana" in system or "datasphere" in system
            or connector in ("hana", "datasphere") or "hana" in connector):
        return "hana"

    for name in ("sqlserver", "postgres", "mysql", "snowflake", "databricks", "oracle"):
        if name in system.replace(" ", ""):
            return name
    if "sql server" in system or "mssql" in system:
        return "sqlserver"
    if "fabric" in system:
        return "fabric-sql"
    return "ansi"


def _readme(bp: dict[str, Any], planned: list[dict[str, Any]], answered: list[str]) -> str:
    lines = [
        "# Source introspection — read the sources instead of assuming them",
        "",
        "Bronze table specs, silver contracts, incremental watermarks and CLS candidates all",
        "depend on what a source actually contains. Nothing in this Baukasten can reach your",
        "sources, so it does the next honest thing: it states exactly what to ask them.",
        "",
        "## How to run this",
        "",
        "1. Give `queries/<source>.sql` to whoever has **read access** to that source. Each file",
        "   is a single SELECT over catalogue metadata — it reads no table data, so it is safe to",
        "   review and run as-is.",
        "2. Export the result as **CSV (with header) or JSON array** — whatever your client",
        "   produces by default; both are accepted.",
        "3. Drop it next to the query as `results/<source>.csv` (or `.json`) and re-run the",
        "   emitter with `--source-schema results/`.",
        "",
        "Until step 3 happens for a source, that source stays **unknown** here — it will not be",
        "given a plausible-looking default shape.",
        "",
        "## Status per source",
        "",
        "| Source | System | Introspection | Schema known |",
        "|---|---|---|---|",
    ]
    for p in planned:
        known = "yes" if p["source"] in answered else "**no — not yet answered**"
        lines.append(f"| `{p['source']}` | {p['system'] or '—'} | {p['how']} | {known} |")

    unanswered = [p["source"] for p in planned if p["source"] not in answered]
    lines += ["", "## What is still open", ""]
    if unanswered:
        lines.append(f"{len(unanswered)} of {len(planned)} source(s) have not been introspected:")
        lines += [f"- `{s}`" for s in unanswered]
        lines += [
            "",
            "Their silver contracts cannot be grounded yet. Emitting a guessed shape would look",
            "like progress and cost a workshop round to unpick, so nothing is emitted for them.",
        ]
    else:
        lines.append("Every source has been introspected — the emitted contracts reflect real schemas.")

    lines += [
        "",
        "## What is proposed, not decided",
        "",
        "`INFORMATION_SCHEMA.COLUMNS` carries no primary keys, and no catalogue tells you which",
        "timestamp is the right incremental watermark. Both are therefore emitted as **candidates**",
        "in `proposals.json` for the workshop to confirm — never applied silently.",
        "",
        f"Supported dialects: {', '.join(sorted(SUPPORTED_DIALECTS))}.",
    ]
    return "\n".join(lines) + "\n"


def emit_source_schema(bp: dict[str, Any],
                       results: dict[str, str] | None = None) -> dict[str, str]:
    """Return the artifact set (path → content).

    ``results`` maps a source name to the raw result payload (CSV or JSON) returned by its
    introspection query, or an OpenAPI document for REST sources. Sources absent from it
    stay unknown by design.
    """
    results = results or {}
    ingestion = sorted(bp.get("ingestion", []), key=lambda e: str(e.get("source", "")))
    out: dict[str, str] = {}
    planned: list[dict[str, Any]] = []
    answered: list[str] = []
    proposals: dict[str, Any] = {}
    contracts: dict[str, list[dict[str, Any]]] = {}

    for entry in ingestion:
        source = str(entry.get("source") or "")
        if not source:
            continue
        slug = _slug(source)
        kind = source_kind(entry)
        system = str(entry.get("source_system") or "")

        if kind == "sql":
            dialect = dialect_for(entry)
            schemas = entry.get("schemas") if isinstance(entry.get("schemas"), list) else None
            tables = entry.get("tables") if isinstance(entry.get("tables"), list) else None
            out[f"source_schema/queries/{slug}.sql"] = introspection_sql(
                dialect, schemas=schemas, tables=tables)
            how = f"`queries/{slug}.sql` ({dialect})"
        elif kind == "rest":
            out[f"source_schema/queries/{slug}.md"] = (
                f"# {source} — OpenAPI document needed\n\n"
                f"This source is a REST/API source ({system or 'no system recorded'}), which has no\n"
                "`INFORMATION_SCHEMA`. Its published OpenAPI document is the equivalent contract.\n\n"
                "Fetch it (commonly `/openapi.json`, `/swagger/v1/swagger.json` or `/$metadata` for\n"
                f"OData) and drop it as `results/{slug}.json`.\n\n"
                "`components.schemas` is what gets read; object schemas with properties become tables.\n"
            )
            how = f"OpenAPI → `results/{slug}.json`"
        else:
            out[f"source_schema/queries/{slug}.md"] = (
                f"# {source} — file/lake source, no catalogue to query\n\n"
                f"This source is file/lake storage ({system or 'no system recorded'}). It has no\n"
                "catalogue to introspect; its schema comes from the files themselves.\n\n"
                "Two honest options:\n\n"
                "- If it is already a Delta table, read its schema from `_delta_log` — the shape is\n"
                "  authoritative there.\n"
                "- Otherwise export a `CREATE TABLE` DDL of the intended shape and import it with\n"
                "  `odcs.import_sql_table`.\n\n"
                "No shape is inferred from file names or a sampled row here: a sample is evidence\n"
                "about one file, not a contract about the source.\n"
            )
            how = "file/lake — see note"

        planned.append({"source": source, "system": system, "how": how, "kind": kind})

        payload = results.get(source) or results.get(slug)
        if not payload:
            continue

        try:
            if kind == "rest":
                objects = from_openapi(json.loads(payload))
            else:
                from core.dataarch_engine.blueprint.source_schema import parse_rows
                objects = from_information_schema(parse_rows(payload))
        except (ValueError, json.JSONDecodeError) as exc:
            out[f"source_schema/results/{slug}.ERROR.md"] = (
                f"# {source} — introspection result could not be read\n\n"
                f"`{exc}`\n\n"
                "Expected a CSV export with a header row, a JSON array of row objects, or (for REST)\n"
                "an OpenAPI document. The source stays unknown until a readable result is supplied —\n"
                "it is not filled in with a default.\n"
            )
            continue

        if not objects:
            out[f"source_schema/results/{slug}.ERROR.md"] = (
                f"# {source} — introspection returned no tables\n\n"
                "The result parsed cleanly but contained no table with columns. Check that the query\n"
                "ran against the right database/schema and that the account can see the catalogue.\n"
            )
            continue

        answered.append(source)
        contracts[source] = objects
        proposals[source] = {
            table["name"]: {
                "key_candidates": key_candidates(table),
                "watermark_candidates": watermark_candidates(table),
            }
            for table in objects
        }

    if not planned:
        return {}

    for source, objects in contracts.items():
        out[f"source_schema/schemas/{_slug(source)}.json"] = (
            json.dumps({"source": source, "schema": objects}, indent=2, ensure_ascii=False) + "\n"
        )

    if proposals:
        out["source_schema/proposals.json"] = (
            json.dumps({
                "_note": "Candidates for the workshop to confirm. INFORMATION_SCHEMA carries no "
                         "primary keys, and no catalogue says which timestamp is the right "
                         "incremental watermark — so neither is applied automatically.",
                "sources": proposals,
            }, indent=2, ensure_ascii=False) + "\n"
        )

    out["source_schema/_SOURCE_SCHEMA.md"] = _readme(bp, planned, answered)
    return out


def tables_by_source(bp: dict[str, Any],
                     results: dict[str, str] | None) -> dict[str, list[dict[str, Any]]]:
    """Introspektions-Rohpayloads -> ODCS-Tabellenobjekte je Quelle.

    Eine Stelle statt zwei: der Ingress-DQ-Emitter und der Copy-job-Emitter brauchen
    dieselbe Umwandlung, und zwei Kopien haetten frueher oder later verschieden entschieden,
    welche Quelle als REST gilt. Unlesbare Payloads werden uebersprungen — sie sind
    bereits von ``emit_source_schema`` als solche ausgewiesen.
    """
    import json as _json

    from core.dataarch_engine.blueprint.source_schema import (
        from_information_schema, from_openapi, parse_rows)

    out: dict[str, list[dict[str, Any]]] = {}
    for entry in bp.get("ingestion", []) or []:
        name = str(entry.get("source") or "")
        payload = (results or {}).get(name)
        if not payload:
            continue
        try:
            if source_kind(entry) == "rest":
                out[name] = from_openapi(_json.loads(payload))
            else:
                out[name] = from_information_schema(parse_rows(payload))
        except (ValueError, _json.JSONDecodeError):
            continue
    return out
