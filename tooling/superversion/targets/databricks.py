"""targets.databricks — Databricks Metric View target adapter (task I-7.2).

Second semantic-layer stack for the Tool-Agnostik-Beweis (I-7): the SAME governed core
that emits Power BI (I-3) and OSI (I-7.1) also emits **Databricks Metric Views** (YAML),
on the ADR-0006 contract (`emit(canonical) -> {relative_path: content}`).

Emits one metric view per table that carries measures (the fact tables): `source` = the
table, `dimensions` = its columns, `measures` = its measures. Faithful to the official
YAML reference (version 1.1).

Honesty (Ehrlichkeit v3) — validation gate, like the PBIR official-CLI precedent (I-3.3):
the **authoritative** validator is a Databricks workspace, which cannot run offline →
that gate is *geplant*. The local gate validates the emitted YAML against an ALUCA-authored
JSON Schema **derived from the official YAML reference** (`schemas/databricks_metricview.schema.json`),
labelled docs-derived — not claimed as the vendor's own validator. Status is therefore
``beta`` until the workspace validator is wired.

Dialect note: Databricks measure expressions are SQL; Power-BI DAX measure expressions are
carried verbatim as the `expr` text (clearly a porting placeholder, not transpiled DAX→SQL).
"""
from __future__ import annotations

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets.base import TargetAdapter, register

MV_VERSION = "1.1"


def _metric_view(table) -> dict:
    mv: dict = {"version": MV_VERSION, "source": table.name}
    if table.description:
        mv["comment"] = table.description
    dims = [
        {"name": col.name, "expr": col.name}  # identity expr over the source column
        for col in table.columns
    ]
    if dims:
        mv["dimensions"] = dims
    measures = [
        {"name": m.name, "expr": m.expression or m.name}
        for m in table.measures
    ]
    if measures:
        mv["measures"] = measures
    return mv


def emit(canonical: CanonicalModel) -> dict[str, str]:
    import yaml

    sm = canonical.semantic
    # One metric view per table with measures; fall back to all tables if none has measures.
    fact_tables = [t for t in sm.tables if t.measures] or list(sm.tables)
    out: dict[str, str] = {}
    for table in fact_tables:
        doc = _metric_view(table)
        yaml_text = yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, allow_unicode=True)
        out[f"{table.name}.metricview.yaml"] = yaml_text
    return out


register(TargetAdapter(
    id="databricks",
    label="Databricks Metric View (YAML)",
    fmt="yaml",
    emit=emit,
    data_platform="databricks",
    visualization="",
    # docs-derived local gate; vendor (workspace) validator is geplant → beta, not live.
    status="beta",
))
