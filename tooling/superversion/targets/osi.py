"""targets.osi — OSI (Open Semantic Interchange) target adapter (task I-7.1).

Emits an OSI Core Metadata document from the canonical model on the ADR-0006 target
contract (`emit(canonical) -> {relative_path: content}`), proving the agnostic core:
the SAME governed core that emits Power BI (TMDL/PBIR, I-3) also emits OSI, each
validated by its own official validator.

Validation is against the **official, upstream** OSI JSON Schema, vendored verbatim at
`targets/schemas/osi-schema.json`:
  - Source: https://github.com/open-semantic-interchange/OSI (core-spec/osi-schema.json)
  - Spec version: 0.2.0.dev0 · License: Apache-2.0 · retrieved 2026-06-25
(Obtained from the official OSI project, not via Meridian — so it is independent of the
Meridian vendoring pin.)

Canonical → OSI mapping:
  semantic.name              → semantic_model[0].name
  each Table                 → a Dataset (fields = its Columns; identity expression)
  each Measure               → a Metric (expression carried as a DialectExpression)
  each Relationship          → an OSI Relationship (from=many side, to=one side)

Honesty (Ehrlichkeit v3): OSI 0.2's Dialect enum has no DAX entry, so Power-BI
measure expressions are emitted under the nearest available dialect, ``MDX`` (same
SSAS expression family), labelled as such — not silently mislabelled as SQL.
"""
from __future__ import annotations

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets.base import TargetAdapter, register

OSI_VERSION = "0.2.0.dev0"
_MEASURE_DIALECT = "MDX"  # nearest OSI dialect to Power BI DAX (no DAX in OSI 0.2 enum)


def _expression(expr: str, dialect: str) -> dict:
    return {"dialects": [{"dialect": dialect, "expression": expr}]}


def _dataset(table) -> dict:
    ds: dict = {
        "name": table.name,
        # `source` is required; the physical binding is target-side — use the table name.
        "source": table.name,
    }
    if table.description:
        ds["description"] = table.description
    fields = []
    for col in table.columns:
        field: dict = {
            "name": col.name,
            # Identity expression: the field maps to its own column (ANSI_SQL identifier).
            "expression": _expression(col.name, "ANSI_SQL"),
        }
        if col.description:
            field["description"] = col.description
        if table.is_date_table:
            field["dimension"] = {"is_time": True}
        fields.append(field)
    if fields:
        ds["fields"] = fields
    return ds


def emit(canonical: CanonicalModel) -> dict[str, str]:
    import json

    sm = canonical.semantic
    datasets = [_dataset(t) for t in sm.tables]
    if not datasets:
        # OSI requires >=1 dataset; surface a minimal placeholder rather than emit invalid.
        datasets = [{"name": sm.name or "model", "source": sm.name or "model"}]

    metrics = []
    for table in sm.tables:
        for m in table.measures:
            metric: dict = {
                "name": m.name,
                "expression": _expression(m.expression or m.name, _MEASURE_DIALECT),
            }
            if m.description:
                metric["description"] = m.description
            metrics.append(metric)

    relationships = []
    for i, rel in enumerate(sm.relationships):
        relationships.append({
            "name": f"{rel.from_table}__{rel.from_column}__{rel.to_table}__{rel.to_column}" or f"rel_{i}",
            "from": rel.from_table,
            "to": rel.to_table,
            "from_columns": [rel.from_column],
            "to_columns": [rel.to_column],
        })

    model: dict = {"name": sm.name or "model", "datasets": datasets}
    if metrics:
        model["metrics"] = metrics
    if relationships:
        model["relationships"] = relationships

    doc = {"version": OSI_VERSION, "semantic_model": [model]}
    name = sm.name or "model"
    return {f"{name}.osi.json": json.dumps(doc, indent=2, ensure_ascii=False) + "\n"}


register(TargetAdapter(
    id="osi",
    label="Open Semantic Interchange (OSI Core 0.2)",
    fmt="json",
    emit=emit,
    data_platform="beliebig",
    visualization="",
    status="live",  # validated against the official upstream OSI schema (I-7.1)
))
