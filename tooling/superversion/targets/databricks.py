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

Dialect note (I-10.0 follow-up): a measure's governed `technical.calculation` DSL
(`expressions['dsl']`, resolved by `from_aluca.py`) is synthesized into real
Databricks SQL HERE via `targets/sql_synth.py` — the SQL-target counterpart to
`targets/dax_synth.py` (used by `targets/tmdl.py`), proving the DSL is genuinely
stack-agnostic rather than DAX-shaped by accident. A real `expressions['sql']`
override (if ever authored) wins first, same precedence as `dax_synth`'s callers.
4 of the 16 ops (`sumx_over_key`/`avgx_over_key`/`pvm_volume_effect`/
`pvm_price_effect`) have no flat Metric-View-`expr` SQL shape (they need a
per-key GROUP BY subquery) — `sql_synth.synthesize_sql` raises `SynthesisError`
for those, and this module falls back to an explicit `NULL` placeholder + an
adjacent `comment: "HITL: ..."` (the Metric View analogue of `dax_synth`'s
`BLANK()` + `/// HITL:` — never a silently wrong SQL expression).
"""
from __future__ import annotations

import json

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets import sql_synth
from tooling.superversion.targets.base import TargetAdapter, register

MV_VERSION = "1.1"

_GENERIC_HITL_REASON = "define SQL dialect (ALUCA carries meaning, not SQL)"


def _sql_for(measure) -> tuple[str, bool]:
    """(sql_expression, is_placeholder). Uses a real dialect override when
    present, else synthesizes SQL from the governed DSL formula (I-10.0), else
    a deterministic `NULL` placeholder — mirrors `targets/tmdl.py::_dax_for`."""
    exprs = getattr(measure, "expressions", None) or {}
    dialect = exprs.get("sql", "")
    if dialect:
        return dialect.strip(), False
    dsl = exprs.get("dsl", "")
    if dsl:
        try:
            resolved = json.loads(dsl)
            return sql_synth.synthesize_sql(resolved), False
        except (ValueError, sql_synth.SynthesisError):
            pass  # malformed/unsupported-shape DSL payload — fall through
    return "NULL", True


def _hitl_reason(measure) -> str:
    return (getattr(measure, "expressions", None) or {}).get("hitl_reason") or _GENERIC_HITL_REASON


def _measure_entry(m) -> dict:
    entry: dict = {"name": m.name}
    sql, is_placeholder = _sql_for(m)
    entry["expr"] = sql
    if is_placeholder:
        entry["comment"] = f"HITL: {_hitl_reason(m)}"
    elif m.description:
        entry["comment"] = m.description
    return entry


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
    measures = [_measure_entry(m) for m in table.measures]
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


def hitl_gaps(canonical: CanonicalModel) -> list[str]:
    """Human-in-the-loop gaps in the emitted Metric Views (measures with no
    derivable SQL — either no `technical.calculation` was authored, it is an
    explicit `op: hitl` marker, or the op has no flat-expression SQL shape,
    e.g. `sumx_over_key`) — mirrors `targets/tmdl.py::hitl_gaps`. Every entry
    here is an explicit, diagnosable gap, never a silent one."""
    gaps: list[str] = []
    for table in canonical.semantic.tables:
        for measure in table.measures:
            _, is_placeholder = _sql_for(measure)
            if is_placeholder:
                gaps.append(f"{table.name}.{measure.name}: {_hitl_reason(measure)}")
    return gaps


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
