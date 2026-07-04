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

Sibling-measure-reference constraint (QA review finding, fixed before merge):
Databricks Metric Views only allow a measure's `expr` to call `MEASURE(x)` for
a measure `x` defined EARLIER in the SAME view — unlike DAX bracket
references, which are model-global and order-free. Since this module emits
ONE view PER SOURCE TABLE, a KPI whose formula references a sibling KPI's
measure living in a DIFFERENT table (or appearing later in the same table's
measure list) cannot honestly emit a `MEASURE(...)` call — `_sql_for` checks
`sql_synth.referenced_measure_names(resolved)` against the set of same-view,
already-emitted measure names before attempting synthesis, and falls back to
the HITL placeholder (not a `MEASURE()` call the real workspace would reject)
when the check fails.
"""
from __future__ import annotations

import json

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.targets import sql_synth
from tooling.superversion.targets.base import TargetAdapter, register

MV_VERSION = "1.1"

_GENERIC_HITL_REASON = "define SQL dialect (ALUCA carries meaning, not SQL)"


_CROSS_VIEW_REASON = (
    "sibling-measure reference crosses metric views, or references a measure not yet "
    "defined earlier in this view — Databricks Metric Views require MEASURE(...) to "
    "target an earlier-defined measure in the SAME view"
)


def _sql_for(measure, available_measure_names: set[str]) -> tuple[str, bool]:
    """(sql_expression, is_placeholder). Uses a real dialect override when
    present, else synthesizes SQL from the governed DSL formula (I-10.0) —
    but only once every sibling-measure reference it touches is confirmed
    available in THIS view, already defined earlier (Databricks constraint,
    see module docstring) — else a deterministic `NULL` placeholder. Mirrors
    `targets/tmdl.py::_dax_for`."""
    exprs = getattr(measure, "expressions", None) or {}
    dialect = exprs.get("sql", "")
    if dialect:
        return dialect.strip(), False
    dsl = exprs.get("dsl", "")
    if dsl:
        try:
            resolved = json.loads(dsl)
            if not sql_synth.referenced_measure_names(resolved) <= available_measure_names:
                raise sql_synth.SynthesisError(_CROSS_VIEW_REASON)
            return sql_synth.synthesize_sql(resolved), False
        except (ValueError, sql_synth.SynthesisError):
            pass  # malformed/unsupported-shape/cross-view DSL payload — fall through
    return "NULL", True


def _hitl_reason(measure, available_measure_names: set[str]) -> str:
    exprs = getattr(measure, "expressions", None) or {}
    reason = exprs.get("hitl_reason")
    if reason:
        return reason
    dsl = exprs.get("dsl", "")
    if dsl:
        try:
            resolved = json.loads(dsl)
        except ValueError:
            pass
        else:
            if not sql_synth.referenced_measure_names(resolved) <= available_measure_names:
                return _CROSS_VIEW_REASON
    return _GENERIC_HITL_REASON


def _measure_entry(m, available_measure_names: set[str]) -> dict:
    entry: dict = {"name": m.name}
    sql, is_placeholder = _sql_for(m, available_measure_names)
    entry["expr"] = sql
    if is_placeholder:
        entry["comment"] = f"HITL: {_hitl_reason(m, available_measure_names)}"
    elif m.description:
        entry["comment"] = m.description
    return entry


def _same_view_refs(measure, view_measure_names: set[str]) -> set[str]:
    """This measure's sibling-measure references, restricted to names present
    in its OWN view (same table) — the only ones `order_measure_names` needs
    to know about; a genuinely cross-view reference is not this function's
    concern (the availability check in `_sql_for`/`_hitl_reason` still gaps it,
    regardless of ordering)."""
    exprs = getattr(measure, "expressions", None) or {}
    dsl = exprs.get("dsl", "")
    if not dsl:
        return set()
    try:
        resolved = json.loads(dsl)
    except ValueError:
        return set()
    return sql_synth.referenced_measure_names(resolved) & view_measure_names - {measure.name}


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

    # Recover same-view forward references (bracket/catalog declaration order
    # is not topologically sorted by dependency) so they synthesize real SQL
    # instead of an avoidable HITL gap — see sql_synth.order_measure_names.
    view_measure_names = {m.name for m in table.measures}
    name_refs = [(m.name, _same_view_refs(m, view_measure_names)) for m in table.measures]
    order = sql_synth.order_measure_names(name_refs)
    measures_by_name = {m.name: m for m in table.measures}
    ordered = [measures_by_name[n] for n in order]

    measures = [
        _measure_entry(m, {earlier.name for earlier in ordered[:i]})
        for i, m in enumerate(ordered)
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


def hitl_gaps(canonical: CanonicalModel) -> list[str]:
    """Human-in-the-loop gaps in the emitted Metric Views (measures with no
    derivable SQL — either no `technical.calculation` was authored, it is an
    explicit `op: hitl` marker, or the op has no flat-expression SQL shape,
    e.g. `sumx_over_key`) — mirrors `targets/tmdl.py::hitl_gaps`. Every entry
    here is an explicit, diagnosable gap, never a silent one."""
    gaps: list[str] = []
    for table in canonical.semantic.tables:
        view_measure_names = {m.name for m in table.measures}
        name_refs = [(m.name, _same_view_refs(m, view_measure_names)) for m in table.measures]
        measures_by_name = {m.name: m for m in table.measures}
        ordered = [measures_by_name[n] for n in sql_synth.order_measure_names(name_refs)]
        for i, measure in enumerate(ordered):
            available = {earlier.name for earlier in ordered[:i]}
            _, is_placeholder = _sql_for(measure, available)
            if is_placeholder:
                gaps.append(f"{table.name}.{measure.name}: {_hitl_reason(measure, available)}")
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
