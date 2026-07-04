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

Honesty (Ehrlichkeit v3): OSI 0.2's Dialect enum has no DAX entry, so a Metric's
DAX-derived expression is emitted under the nearest available dialect, ``MDX``
(same SSAS expression family), labelled as such — not silently mislabelled as SQL.

Multi-dialect metrics (I-10.0 follow-up): a Metric backed by a resolvable governed
`technical.calculation` (`expressions['dsl']`) gets its expression synthesized
independently per dialect — ``MDX`` via `targets/dax_synth.py` (same as
`targets/tmdl.py`; covers all 16 ops) and, when the op has a flat-SQL shape (11 of
16 — see `targets/sql_synth.py`), an additional ``DATABRICKS`` dialect entry
(OSI 0.2's enum has a dedicated `DATABRICKS` value, distinct from generic
`ANSI_SQL` — `MEASURE(...)`/`TRY_DIVIDE(...)` are Databricks-specific builtins,
not portable ANSI SQL, so labelling them `DATABRICKS` is the honest choice).
Genuinely unresolvable measures (no `technical.calculation`, `op: hitl`, or a
malformed DSL payload) fall back to the metric's own name as a placeholder
expression, with the HITL reason surfaced in the Metric's `description` — the
required-`expression` field means there's no BLANK()-style placeholder value in
OSI's schema, so the reason has to travel via `description` instead (never
silently identical to a real formula).
"""
from __future__ import annotations

import json

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets import dax_synth, sql_synth
from tooling.superversion.targets.base import TargetAdapter, register

OSI_VERSION = "0.2.0.dev0"
_MEASURE_DIALECT = "MDX"  # nearest OSI dialect to Power BI DAX (no DAX in OSI 0.2 enum)
_GENERIC_HITL_REASON = "define dialect expression (ALUCA carries meaning, not DAX/SQL)"


def _expression(expr: str, dialect: str) -> dict:
    return {"dialects": [{"dialect": dialect, "expression": expr}]}


def _dialects_for(measure, available_measure_names: set[str]) -> tuple[list[dict], bool]:
    """([{"dialect":..., "expression":...}, ...], is_placeholder). Real dialect
    overrides win first; else synthesizes MDX (DAX, always — dax_synth covers
    all 16 ops, and DAX bracket references are model-global/order-free, no
    constraint to check) and, when possible, an additional DATABRICKS (SQL)
    entry from the same governed DSL; else a single placeholder dialect entry.

    The DATABRICKS entry is only added once every sibling-measure reference it
    touches is confirmed to already be in `available_measure_names` (metrics
    emitted earlier in this document) — `MEASURE(...)` is a Databricks Metric
    View construct with the same same-view/earlier-defined constraint
    `targets/databricks.py` enforces; a forward/dangling reference is dropped
    to MDX-only rather than emitted as an unusable DATABRICKS expression."""
    exprs = getattr(measure, "expressions", None) or {}
    dax_override = exprs.get("dax", "")
    if dax_override or measure.expression:
        return [{"dialect": _MEASURE_DIALECT, "expression": (dax_override or measure.expression).strip()}], False

    dsl = exprs.get("dsl", "")
    if dsl:
        try:
            resolved = json.loads(dsl)
            dialects = [{"dialect": _MEASURE_DIALECT, "expression": dax_synth.synthesize_dax(resolved)}]
        except (ValueError, dax_synth.SynthesisError):
            pass
        else:
            try:
                if not sql_synth.referenced_measure_names(resolved) <= available_measure_names:
                    raise sql_synth.SynthesisError("sibling measure reference not yet emitted earlier in this document")
                dialects.append({"dialect": "DATABRICKS", "expression": sql_synth.synthesize_sql(resolved)})
            except sql_synth.SynthesisError:
                pass  # no flat-SQL shape, or a forward/dangling reference — MDX-only is still honest
            return dialects, False

    return [{"dialect": _MEASURE_DIALECT, "expression": measure.name}], True


def _hitl_reason(measure) -> str:
    return (getattr(measure, "expressions", None) or {}).get("hitl_reason") or _GENERIC_HITL_REASON


def _same_view_refs(measure, view_measure_names: set[str]) -> set[str]:
    """This measure's sibling-measure references, restricted to names present
    in its OWN view (same table, mirroring `targets/databricks.py`'s identical
    helper — DATABRICKS-dialect availability is scoped per-table, the same
    physical shape `targets/databricks.py` actually emits, since a bare
    `MEASURE(...)` cannot cross Metric Views)."""
    exprs = getattr(measure, "expressions", None) or {}
    dsl = exprs.get("dsl", "")
    if not dsl:
        return set()
    try:
        resolved = json.loads(dsl)
    except ValueError:
        return set()
    return sql_synth.referenced_measure_names(resolved) & view_measure_names - {measure.name}


def _iter_measures_with_available_names(canonical: CanonicalModel):
    """Yields (table, measure, available_measure_names) in per-table
    topologically-sorted order (same-view forward-reference recovery, see
    `sql_synth.order_measure_names` — kept consistent with
    `targets/databricks.py::_metric_view`'s identical reordering, since the
    DATABRICKS dialect represents that same one-view-per-table shape).
    `available_measure_names` resets per table (a bare `MEASURE(...)` cannot
    cross Metric Views) and is every same-view measure name already emitted
    earlier in this table's topological order."""
    for table in canonical.semantic.tables:
        view_measure_names = {m.name for m in table.measures}
        name_refs = [(m.name, _same_view_refs(m, view_measure_names)) for m in table.measures]
        measures_by_name = {m.name: m for m in table.measures}
        ordered = [measures_by_name[n] for n in sql_synth.order_measure_names(name_refs)]
        available: set[str] = set()
        for m in ordered:
            yield table, m, set(available)
            available.add(m.name)


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
    sm = canonical.semantic
    datasets = [_dataset(t) for t in sm.tables]
    if not datasets:
        # OSI requires >=1 dataset; surface a minimal placeholder rather than emit invalid.
        datasets = [{"name": sm.name or "model", "source": sm.name or "model"}]

    metrics = []
    for _table, m, available in _iter_measures_with_available_names(canonical):
        dialects, is_placeholder = _dialects_for(m, available)
        metric: dict = {"name": m.name, "expression": {"dialects": dialects}}
        if is_placeholder:
            metric["description"] = f"HITL: {_hitl_reason(m)}"
        elif m.description:
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


def hitl_gaps(canonical: CanonicalModel) -> list[str]:
    """Human-in-the-loop gaps in the emitted OSI metrics (no derivable dialect
    expression at all — mirrors `targets/tmdl.py::hitl_gaps`). Note this is
    narrower than `targets/databricks.py::hitl_gaps`: OSI always has an MDX
    (DAX) expression whenever `dax_synth` can resolve the op (all 16), even if
    the DATABRICKS dialect entry is absent for the 4 SQL-shapeless ops — a gap
    here means NEITHER dialect resolved."""
    gaps: list[str] = []
    for table, measure, available in _iter_measures_with_available_names(canonical):
        _, is_placeholder = _dialects_for(measure, available)
        if is_placeholder:
            gaps.append(f"{table.name}.{measure.name}: {_hitl_reason(measure)}")
    return gaps


register(TargetAdapter(
    id="osi",
    label="Open Semantic Interchange (OSI Core 0.2)",
    fmt="json",
    emit=emit,
    data_platform="beliebig",
    visualization="",
    status="live",  # validated against the official upstream OSI schema (I-7.1)
))
