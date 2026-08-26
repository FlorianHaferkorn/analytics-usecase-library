"""provision_dq — ingress DQ gates from the introspected source schema.

``provision_transforms.emit_dq_gates`` is already the one DQ surface in this repo (dbt
``schema.yml`` tests per gold product) and takes a ``column_tests`` supplier. So far it had
exactly one supplier: the SAP standard pack, which knows real keys and FKs. Every other
customer got the honest ``TODO(contract:…)`` placeholder, because the plain IR does not know
business columns.

The source-schema reader changed that — it now returns real columns, real nullability and
key/watermark candidates. This module is **supplier number two**, not a second DQ engine.

**Why ingress and not gold.** What introspection describes is the *source* (`dbo.Orders`),
not the gold product (`fact_orders`). Nothing in the IR records which source table becomes
which gold product, and mapping `Orders → fact_orders` by name similarity is the same guess
this Baukasten refuses elsewhere. Source knowledge therefore lands where it is actually
about: the **ingress** — does what arrived still match what the source declared? That is a
different and equally missing gate: today a source can silently drop a column or start
sending NULLs in a mandatory field, and nothing notices until a report looks wrong.

**What is factual vs proposed.** Nullability comes from the source catalogue and is a fact,
so ``not_null`` tests are emitted. Keys are *candidates* — `INFORMATION_SCHEMA.COLUMNS`
carries no key information — so a ``unique`` test is emitted only for a **confirmed** key.
An unconfirmed candidate becomes ``TODO(confirm:…)``: a uniqueness test on a guessed key
either passes meaninglessly or blocks a pipeline on a guess, and neither is worth having.

Finally this consumes ``medallion.silver.quality_threshold`` — a field the IR has always
declared and no emitter has ever read.
"""
from __future__ import annotations

from typing import Any

import yaml

from core.dataarch_engine.blueprint.source_schema import key_candidates, watermark_candidates

# Share of rows that must pass for silver to accept a load, when the IR says nothing.
_DEFAULT_THRESHOLD = 1.0


def quality_threshold(bp: dict[str, Any]) -> float:
    """The silver acceptance threshold from the IR, defaulting to "everything must pass".

    Defaulting to 1.0 rather than a lenient value is deliberate: a threshold nobody set
    should not silently permit bad rows.
    """
    raw = bp.get("medallion", {}).get("silver", {}).get("quality_threshold")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return _DEFAULT_THRESHOLD
    return value if 0.0 <= value <= 1.0 else _DEFAULT_THRESHOLD


def ingress_tests(schema_objects: list[dict[str, Any]],
                  confirmed_keys: dict[str, list[str]] | None = None) -> dict[str, list[dict]]:
    """``{table → [dbt column-test dicts]}`` from an introspected source schema.

    Factual tests only. ``confirmed_keys`` maps a table to the key columns someone actually
    confirmed; only those get ``unique``.
    """
    confirmed_keys = confirmed_keys or {}
    out: dict[str, list[dict]] = {}

    for obj in schema_objects:
        table = str(obj.get("name") or "")
        if not table:
            continue
        confirmed = list(confirmed_keys.get(table) or [])
        columns: list[dict[str, Any]] = []

        for prop in obj.get("properties") or []:
            name = str(prop.get("name") or "")
            if not name:
                continue
            tests: list[Any] = []
            # NOT NULL in the source catalogue is a fact, not an inference.
            if prop.get("required") is True:
                tests.append("not_null")
            if name in confirmed:
                # Only a single-column confirmed key can carry `unique` without dbt_utils;
                # a composite key needs unique_combination_of_columns, kept out to stay
                # tool-free (same boundary emit_dq_gates already documents).
                if len(confirmed) == 1:
                    tests.append("unique")
            if tests:
                columns.append({"name": name, "data_tests": tests})

        proposals = [k for k in key_candidates(obj) if k not in confirmed]
        if proposals:
            columns.append({
                "name": f"TODO(confirm:key)",
                "description": "Key candidates from column naming, unconfirmed: "
                               + ", ".join(proposals)
                               + ". A uniqueness test on a guessed key either passes "
                                 "meaninglessly or blocks the pipeline on a guess — confirm "
                                 "the key, then re-emit.",
            })

        if columns:
            out[table] = columns
    return out


def freshness_proposals(schema_objects: list[dict[str, Any]]) -> dict[str, list[str]]:
    """``{table → watermark candidates}`` — the basis for a freshness gate, unconfirmed.

    dbt's ``source freshness`` needs a ``loaded_at_field``; no catalogue says which timestamp
    that is, so this stays a proposal rather than an emitted check.
    """
    out = {}
    for obj in schema_objects:
        table = str(obj.get("name") or "")
        candidates = watermark_candidates(obj)
        if table and candidates:
            out[table] = candidates
    return out


def _readme(source: str, tests: dict[str, list[dict]],
            freshness: dict[str, list[str]], threshold: float) -> str:
    factual = sum(
        1 for cols in tests.values() for c in cols
        if not str(c["name"]).startswith("TODO(")
    )
    open_keys = sum(
        1 for cols in tests.values() for c in cols
        if str(c["name"]).startswith("TODO(")
    )

    lines = [
        f"# Ingress DQ gates — `{source}`",
        "",
        "Does what arrived still match what the source declared? Today a source can silently",
        "drop a column or start sending NULLs in a mandatory field, and nothing notices until",
        "a report looks wrong.",
        "",
        "These tests are generated from the source's own catalogue (`INFORMATION_SCHEMA` /",
        "OpenAPI) — so they assert what the source *promised*, not what we assumed.",
        "",
        "## What is emitted, and what is not",
        "",
        f"- **{factual} factual test(s)** — `not_null` where the source declares NOT NULL, and",
        "  `unique` only where a key was **confirmed**.",
        f"- **{open_keys} table(s) with unconfirmed key candidates** — emitted as",
        "  `TODO(confirm:key)`. `INFORMATION_SCHEMA.COLUMNS` carries no key information, and a",
        "  uniqueness test on a guessed key either passes meaninglessly or blocks a pipeline on",
        "  a guess.",
        "",
        "## Silver acceptance threshold",
        "",
        f"`medallion.silver.quality_threshold` = **{threshold:.2%}** of rows must pass.",
    ]
    if threshold == _DEFAULT_THRESHOLD:
        lines.append("")
        lines.append("This is the default — the IR did not set one. Defaulting to *everything must")
        lines.append("pass* is deliberate: a threshold nobody chose should not silently admit bad rows.")

    if freshness:
        lines += [
            "",
            "## Freshness (proposed, not emitted)",
            "",
            "dbt's `source freshness` needs a `loaded_at_field`. No catalogue says which timestamp",
            "that is, so these stay proposals:",
            "",
        ]
        lines += [f"- `{t}`: {', '.join(f'`{c}`' for c in cols)}" for t, cols in sorted(freshness.items())]

    lines += [
        "",
        "## Relationship to the gold gates",
        "",
        "This is the **ingress** half. Per-gold-product tests live in `dq/` "
        "(`provision_transforms.emit_dq_gates`) — one DQ surface, two suppliers: the SAP standard",
        "pack and this one. Source knowledge deliberately does not become gold tests: nothing in",
        "the IR records which source table becomes which gold product, and mapping them by name",
        "similarity would be a guess.",
    ]
    return "\n".join(lines) + "\n"


def emit_ingress_dq(bp: dict[str, Any],
                    schemas_by_source: dict[str, list[dict[str, Any]]],
                    confirmed_keys: dict[str, dict[str, list[str]]] | None = None
                    ) -> dict[str, str]:
    """Return the ingress-DQ artifact set (path → content).

    ``schemas_by_source`` maps a source name to its introspected schema objects (what
    ``source_schema.from_information_schema`` / ``from_openapi`` return). Sources that were
    never introspected are simply absent — they get no invented tests.
    """
    if not schemas_by_source:
        return {}

    confirmed_keys = confirmed_keys or {}
    threshold = quality_threshold(bp)
    out: dict[str, str] = {}
    covered: list[str] = []

    for source in sorted(schemas_by_source):
        objects = schemas_by_source[source] or []
        tests = ingress_tests(objects, confirmed_keys.get(source))
        if not tests:
            continue
        models = [{"name": table, "columns": cols} for table, cols in sorted(tests.items())]
        out[f"dq_ingress/{source}/schema.yml"] = yaml.safe_dump(
            {"version": 2, "models": models}, sort_keys=False, allow_unicode=True
        )
        out[f"dq_ingress/{source}/_INGRESS_DQ.md"] = _readme(
            source, tests, freshness_proposals(objects), threshold
        )
        covered.append(source)

    if not covered:
        return {}

    declared = sorted(str(e.get("source")) for e in bp.get("ingestion", []) or [] if e.get("source"))
    missing = [s for s in declared if s not in covered]
    index = [
        "# Ingress DQ gates",
        "",
        f"{len(covered)} of {len(declared)} declared source(s) have ingress tests.",
        "",
    ]
    index += [f"- `{s}` → `dq_ingress/{s}/schema.yml`" for s in covered]
    if missing:
        index += [
            "",
            "## Without ingress tests",
            "",
            "These sources were never introspected, so there is nothing factual to assert about",
            "them. No tests are invented for them:",
            "",
        ]
        index += [f"- `{s}`" for s in missing]
        index += ["", "Run their introspection query (`source_schema/queries/`) and re-emit."]
    out["dq_ingress/_INDEX.md"] = "\n".join(index) + "\n"
    return out
