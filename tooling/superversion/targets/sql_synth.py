"""sql_synth — deterministic DSL-formula → Databricks SQL synthesis (I-10.0
follow-up, "go for 2": the same governed `technical.calculation` grammar that
`dax_synth.py` materializes into DAX (`targets/tmdl.py`) also materializes into
SQL here — proving the DSL is genuinely stack-agnostic, not DAX-shaped by
accident. Used by `targets/databricks.py` (Metric View `measures[].expr`) and
`targets/osi.py` (an additional `DATABRICKS`-dialect `Expression`, alongside
the existing `MDX` one from `dax_synth`).

Like `dax_synth.py`, this is the ONLY place SQL syntax is constructed for the
calculation grammar; `from_aluca.py` never imports this module either (I1:
the source adapter stays dialect-neutral for every stack, not just Power BI).

Grammar coverage — 13 of the 18 ops translate to a flat SQL aggregate
expression (a Databricks Metric View measure `expr` is exactly that: one
SQL expression over the view's single `source` table, no subquery):

    sum              -- SUM ( column )
    ratio            -- TRY_DIVIDE ( num, den ) [* scale]   (try_divide: Databricks SQL builtin, null-safe — the SQL analogue of DAX's DIVIDE)
    delta            -- minuend - subtrahend
    delta_pct        -- TRY_DIVIDE ( minuend - subtrahend, ABS ( subtrahend ) )
    rate             -- TRY_DIVIDE ( SUM ( CASE WHEN flag = TRUE THEN 1 ELSE 0 END ), COUNT ( * ) )
    count            -- COUNT ( * )
    mul              -- term_1 * term_2 * ... (n-ary)
    add              -- term_1 + term_2 + ... (n-ary)
    delta_chain      -- minuend - sub_1 - sub_2 - ... (n-ary)
    distinctcount    -- COUNT ( DISTINCT [CASE WHEN <filters> THEN] col [END] )
    count_threshold  -- COUNT ( CASE WHEN col <cmp> value THEN 1 END )
    round            -- ROUND ( value, digits )
    abs              -- ABS ( value )
    avg              -- AVG ( column )
    count_filtered   -- COUNT ( CASE WHEN <filters> THEN 1 END )   (filters: bool or string equality)

Five ops are explicit `SynthesisError` (HITL) here, never guessed: DAX's
SUMX/AVERAGEX-over-VALUES(key) pattern (`sumx_over_key`, `avgx_over_key`), the
fixed-shape PVM row-context iterators (`pvm_volume_effect`, `pvm_price_effect`),
and the generic row-context product-then-sum iterator (`sumx_product`) all
require a per-key/per-row GROUP BY subquery (or a windowed aggregate whose
composition with a further reducer isn't a documented, vendor-confirmed
Metric View pattern) — genuinely beyond a single flat SQL expression, not a
missing line of code. Callers (`targets/databricks.py`, `targets/osi.py`)
catch `SynthesisError` and fall back to their own placeholder + HITL-reason
convention (mirrors `dax_synth`'s callers).

A "ref" term is one of:
  {"kind": "column", "table": ..., "column": ...}  -- ``SUM ( col )`` (table ignored: a
                                                        Metric View is single-source)
  {"kind": "measure", "name": ...}                 -- ``MEASURE ( name )`` (Databricks
                                                        Metric View's official sibling-measure
                                                        reference builtin)
  {"kind": "expr", "op": ..., ...}                 -- a nested resolved formula, rendered
                                                        recursively and parenthesized
  {"kind": "literal", "value": ...}                -- a bare numeric constant

`synthesize_sql` is purely a formula→text function — it has no notion of
"which view is this rendered into" or "measure definition order", so it
cannot by itself guarantee a `MEASURE(...)` call it emits is actually valid
Databricks Metric View SQL (the vendor only allows referencing an
earlier-defined measure in the SAME view). `referenced_measure_names(resolved)`
gives callers the structural information (every sibling-measure name touched,
at any nesting depth) to check that BEFORE calling `synthesize_sql` —
`targets/databricks.py` does exactly this, falling back to the HITL
placeholder for a measure whose formula would need a cross-view or
forward reference.
"""
from __future__ import annotations

import re

_SIMPLE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Ops dax_synth covers but sql_synth deliberately cannot (see module docstring).
_NO_FLAT_SQL_SHAPE = {"sumx_over_key", "avgx_over_key", "pvm_volume_effect", "pvm_price_effect", "sumx_product"}


class SynthesisError(ValueError):
    """A resolved formula is malformed, uses an unknown op/ref kind, or has no
    flat-SQL-expression shape (see `_NO_FLAT_SQL_SHAPE`)."""


def _format_number(n) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


def _ident(name: str) -> str:
    """Databricks/Spark SQL identifier — bare if simple, backtick-quoted otherwise
    (KPI column/measure names routinely contain spaces, e.g. "Net Sales Amount")."""
    if _SIMPLE_IDENT_RE.match(name or ""):
        return name
    return f"`{(name or '').replace('`', '``')}`"


def _sql_literal(value) -> str:
    """A `count_filtered` filter's `equals` value → its Databricks SQL literal:
    `TRUE`/`FALSE` for a bool, a single-quoted string literal (SQL escapes `'`
    by doubling it) for a string."""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return f"'{value.replace(chr(39), chr(39) * 2)}'"


def _term(ref: dict) -> str:
    if not isinstance(ref, dict):
        raise SynthesisError(f"ref must be an object, got {ref!r}")
    kind = ref.get("kind")
    if kind == "column":
        column = ref.get("column")
        if not ref.get("table") or not column:
            raise SynthesisError(f"column ref missing table/column: {ref!r}")
        return f"SUM ( {_ident(column)} )"
    if kind == "measure":
        name = ref.get("name")
        if not name:
            raise SynthesisError(f"measure ref missing name: {ref!r}")
        return f"MEASURE ( {_ident(name)} )"
    if kind == "expr":
        return f"( {synthesize_sql(ref)} )"
    if kind == "literal":
        value = ref.get("value")
        if value is None:
            raise SynthesisError(f"literal ref missing value: {ref!r}")
        return _format_number(value)
    raise SynthesisError(f"unknown ref kind: {kind!r}")


def referenced_measure_names(resolved) -> set[str]:
    """Every sibling-measure name referenced anywhere inside a resolved neutral
    formula (any `{"kind": "measure", "name": ...}` ref, at any nesting depth),
    collected structurally rather than by re-parsing synthesized SQL text.

    Databricks Metric Views only allow `MEASURE(...)` to reference an
    earlier-defined measure in the SAME view (docs.databricks.com/.../metric-
    views/data-modeling/composability) — unlike DAX, where a bracket reference
    is model-global and order-free. `synthesize_sql` itself has no view/ordering
    context (it is a pure formula→text function), so callers
    (`targets/databricks.py`) call this first to check every referenced name is
    available in the current view before emitting a `MEASURE(...)` call —
    never a dangling/forward/cross-view reference."""
    names: set[str] = set()

    def _walk(node) -> None:
        if isinstance(node, dict):
            if node.get("kind") == "measure" and node.get("name"):
                names.add(node["name"])
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(resolved)
    return names


def order_measure_names(name_refs: list[tuple[str, set[str]]]) -> list[str]:
    """Stable topological sort of same-view measure names by sibling-`MEASURE()`
    dependency: a measure referencing another measure in the SAME view must be
    emitted AFTER it (Databricks' earlier-defined-in-this-view constraint).

    `name_refs` is `[(name, refs), ...]` in the view's original declaration
    order, where `refs` is that measure's `referenced_measure_names(...)`
    ALREADY FILTERED to names present in this same view (a caller-side
    concern — this function is dialect/view-context-free, it only sorts).

    Recovers same-view forward references (declaration order in the KPI
    catalog/bracket is not topologically sorted by dependency) so they
    synthesize real SQL instead of an avoidable HITL gap — genuine cross-view
    references are unaffected (a name outside this view's own `refs` is not
    this function's concern; the caller's availability check still gaps it).

    Kahn's algorithm, always picking the lowest-original-index ready node at
    each step (deterministic, I2). A cycle (should not occur for a legitimate
    KPI reference graph) never hangs or raises — leftover names are appended
    in their original order, same as if this function were a no-op for them."""
    order_index = {name: i for i, (name, _refs) in enumerate(name_refs)}
    refs_by_name = {name: refs for name, refs in name_refs}
    remaining = set(order_index)
    placed: list[str] = []

    while remaining:
        ready = sorted(
            (n for n in remaining if not (refs_by_name[n] & remaining)),
            key=lambda n: order_index[n],
        )
        if not ready:
            # cycle (or a ref outside this view, already excluded by the caller) —
            # never hang; keep the rest in original order and stop.
            placed.extend(sorted(remaining, key=lambda n: order_index[n]))
            break
        for n in ready:
            placed.append(n)
            remaining.discard(n)

    return placed


def synthesize_sql(resolved: dict) -> str:
    """Pure, deterministic: resolved neutral formula → Databricks SQL expression
    text. Raises `SynthesisError` for ops with no flat-expression SQL shape
    (never emits a guessed/incorrect expression)."""
    if not isinstance(resolved, dict):
        raise SynthesisError(f"resolved formula must be an object, got {resolved!r}")
    op = resolved.get("op")

    if op in _NO_FLAT_SQL_SHAPE:
        raise SynthesisError(
            f"op {op!r} needs a per-key GROUP BY subquery — no flat Metric View "
            "expr shape (HITL for SQL targets, even though DAX covers it)"
        )

    if op == "sum":
        return _term(resolved.get("ref"))

    if op == "ratio":
        base = f"TRY_DIVIDE ( {_term(resolved.get('numerator'))}, {_term(resolved.get('denominator'))} )"
        scale = resolved.get("scale")
        if scale and scale != 1:
            return f"{base} * {_format_number(scale)}"
        return base

    if op == "delta":
        return f"{_term(resolved.get('minuend'))} - {_term(resolved.get('subtrahend'))}"

    if op == "delta_pct":
        minuend, subtrahend = _term(resolved.get("minuend")), _term(resolved.get("subtrahend"))
        return f"TRY_DIVIDE ( {minuend} - {subtrahend}, ABS ( {subtrahend} ) )"

    if op == "rate":
        column = resolved.get("column")
        if not resolved.get("table") or not column:
            raise SynthesisError(f"rate missing table/column: {resolved!r}")
        flag = _ident(column)
        return (
            f"TRY_DIVIDE ( SUM ( CASE WHEN {flag} = TRUE THEN 1 ELSE 0 END ), COUNT ( * ) )"
        )

    if op == "count":
        if not resolved.get("table"):
            raise SynthesisError(f"count missing table: {resolved!r}")
        return "COUNT ( * )"

    if op == "mul":
        terms = resolved.get("terms") or []
        if len(terms) < 2:
            raise SynthesisError(f"mul needs 2+ terms: {resolved!r}")
        return " * ".join(_term(t) for t in terms)

    if op == "add":
        terms = resolved.get("terms") or []
        if len(terms) < 2:
            raise SynthesisError(f"add needs 2+ terms: {resolved!r}")
        return " + ".join(_term(t) for t in terms)

    if op == "delta_chain":
        subtrahends = resolved.get("subtrahends") or []
        if not subtrahends:
            raise SynthesisError(f"delta_chain needs 1+ subtrahends: {resolved!r}")
        parts = [_term(resolved.get("minuend"))] + [_term(s) for s in subtrahends]
        return " - ".join(parts)

    if op == "distinctcount":
        column = resolved.get("column")
        if not resolved.get("table") or not column:
            raise SynthesisError(f"distinctcount missing table/column: {resolved!r}")
        col = _ident(column)
        filters = resolved.get("filters") or []
        if not filters:
            return f"COUNT ( DISTINCT {col} )"
        conditions = " AND ".join(
            f"{_ident(f['column'])} = {'TRUE' if f['equals'] else 'FALSE'}" for f in filters
        )
        return f"COUNT ( DISTINCT CASE WHEN {conditions} THEN {col} END )"

    if op == "count_threshold":
        column = resolved.get("column")
        comparator, value = resolved.get("comparator"), resolved.get("value")
        if not resolved.get("table") or not column or not comparator:
            raise SynthesisError(f"count_threshold missing table/column/comparator: {resolved!r}")
        return f"COUNT ( CASE WHEN {_ident(column)} {comparator} {_format_number(value)} THEN 1 END )"

    if op == "round":
        value = resolved.get("value")
        digits = resolved.get("digits", 0)
        return f"ROUND ( {_term(value)}, {_format_number(digits)} )"

    if op == "abs":
        value = resolved.get("value")
        if value is None:
            raise SynthesisError(f"abs missing value: {resolved!r}")
        return f"ABS ( {_term(value)} )"

    if op == "avg":
        column = resolved.get("column")
        if not resolved.get("table") or not column:
            raise SynthesisError(f"avg missing table/column: {resolved!r}")
        return f"AVG ( {_ident(column)} )"

    if op == "count_filtered":
        filters = resolved.get("filters") or []
        if not resolved.get("table") or not filters:
            raise SynthesisError(f"count_filtered missing table/filters: {resolved!r}")
        conditions = " AND ".join(f"{_ident(f['column'])} = {_sql_literal(f['equals'])}" for f in filters)
        return f"COUNT ( CASE WHEN {conditions} THEN 1 END )"

    raise SynthesisError(f"unknown op: {op!r}")
