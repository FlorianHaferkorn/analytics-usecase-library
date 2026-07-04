"""dax_synth — deterministic DSL-formula → DAX synthesis (task I-10.0 / Cut S-1).

This is the missing half of Invariant I1's "neutral core, dialect-materialized-at-
the-stack-step" story (Review `SUPERVERSION_ZIELBILD_REVIEW.md` Befund A1): the
governed KPI catalog carries a stack-neutral `technical.calculation` formula
(schema: `tooling/generator/schemas/kpi_definition.schema.json#/$defs/calculation`),
`from_aluca.py` *resolves* it (KPI-id refs → sibling measure names, column refs →
this KPI's own `technical.lineage`) into a fully self-contained neutral structure
carried in `Measure.expressions['dsl']` (JSON) — and THIS module is the pure
function that materializes that neutral structure into real DAX. `from_aluca`
never imports this module (I1: the source adapter stays dialect-neutral); only
`targets/tmdl.py` (the stack step) does.

Grammar (deliberately narrow — matches the legacy `dist/**/_Measures.tmdl` DAX
patterns actually observed for the 5 MVP use cases; anything wider is `hitl`,
resolved upstream in `from_aluca`, never reaches this module):

    sum              -- SUM ( table[column] )
    ratio            -- DIVIDE ( num, den ) [* scale]
    delta            -- minuend - subtrahend
    delta_pct        -- DIVIDE ( minuend - subtrahend, ABS ( subtrahend ) )
    rate             -- DIVIDE ( CALCULATE ( COUNTROWS ( t ), t[flag] = TRUE () ), COUNTROWS ( t ) )
    count            -- COUNTROWS ( table )
    mul              -- term_1 * term_2 * ... (n-ary)
    delta_chain      -- minuend - sub_1 - sub_2 - ... (n-ary)
    distinctcount    -- DISTINCTCOUNT ( t[col] ), optionally CALCULATE-wrapped with 1+ flag filters
    count_threshold  -- CALCULATE ( COUNTROWS ( t ), t[col] <cmp> value )
    round            -- ROUND ( value, digits )
    sumx_over_key    -- SUMX ( VALUES ( t[key] ), CALCULATE ( value ) )
    avgx_over_key    -- AVERAGEX ( VALUES ( t[key] ), CALCULATE ( value ) )
    pvm_volume_effect -- SUMX ( t, ( t[qty] - t[plan_qty] ) * DIVIDE ( t[plan_sales], t[plan_qty] ) )
    pvm_price_effect  -- SUMX ( t, ( DIVIDE ( t[net_price], t[qty] ) - DIVIDE ( t[plan_sales], t[plan_qty] ) ) * t[qty] )
    avg               -- AVERAGE ( t[col] )
    sumx_product      -- SUMX ( t, t[a] * t[b] )
    count_filtered    -- CALCULATE ( COUNTROWS ( t ), t[col1] = v1, t[col2] = v2, ... ) (v: TRUE()/FALSE() or a quoted string)

A "ref" term is one of:
  {"kind": "column", "table": ..., "column": ...}  -- ``SUM ( table[column] )``
  {"kind": "measure", "name": ...}                 -- ``[Measure Name]`` (sibling measure reference)
  {"kind": "expr", "op": ..., ...}                 -- a nested resolved formula, rendered
                                                       recursively via `synthesize_dax` and
                                                       parenthesized (recursive `calc_ref`, e.g.
                                                       the VAR-chain shape of `margin.gm.vs_plan.pct`)
  {"kind": "literal", "value": ...}                -- a bare numeric constant (e.g. the legacy
                                                       `[Baseline Sales Amount] * 0.15` proxy factor)
"""
from __future__ import annotations


class SynthesisError(ValueError):
    """A resolved formula is malformed or uses an unknown op/ref kind."""


def _format_number(n) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


def _dax_literal(value) -> str:
    """A `count_filtered` filter's `equals` value → its DAX literal: `TRUE ()`/
    `FALSE ()` for a bool, a double-quoted string literal (DAX escapes `"` by
    doubling it) for a string."""
    if isinstance(value, bool):
        return "TRUE ()" if value else "FALSE ()"
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def _term(ref: dict) -> str:
    if not isinstance(ref, dict):
        raise SynthesisError(f"ref must be an object, got {ref!r}")
    kind = ref.get("kind")
    if kind == "column":
        table, column = ref.get("table"), ref.get("column")
        if not table or not column:
            raise SynthesisError(f"column ref missing table/column: {ref!r}")
        return f"SUM ( {table}[{column}] )"
    if kind == "measure":
        name = ref.get("name")
        if not name:
            raise SynthesisError(f"measure ref missing name: {ref!r}")
        return f"[{name}]"
    if kind == "expr":
        return f"( {synthesize_dax(ref)} )"
    if kind == "literal":
        value = ref.get("value")
        if value is None:
            raise SynthesisError(f"literal ref missing value: {ref!r}")
        return _format_number(value)
    raise SynthesisError(f"unknown ref kind: {kind!r}")


def synthesize_dax(resolved: dict) -> str:
    """Pure, deterministic: resolved neutral formula → DAX expression text.

    Never emits ``:=`` (TMDL hard-rule owned by the caller); this returns only
    the right-hand-side expression.
    """
    if not isinstance(resolved, dict):
        raise SynthesisError(f"resolved formula must be an object, got {resolved!r}")
    op = resolved.get("op")

    if op == "sum":
        return _term(resolved.get("ref"))

    if op == "ratio":
        base = f"DIVIDE ( {_term(resolved.get('numerator'))}, {_term(resolved.get('denominator'))} )"
        scale = resolved.get("scale")
        if scale and scale != 1:
            return f"{base} * {_format_number(scale)}"
        return base

    if op == "delta":
        return f"{_term(resolved.get('minuend'))} - {_term(resolved.get('subtrahend'))}"

    if op == "delta_pct":
        minuend, subtrahend = _term(resolved.get("minuend")), _term(resolved.get("subtrahend"))
        return f"DIVIDE ( {minuend} - {subtrahend}, ABS ( {subtrahend} ) )"

    if op == "rate":
        table, column = resolved.get("table"), resolved.get("column")
        if not table or not column:
            raise SynthesisError(f"rate missing table/column: {resolved!r}")
        return (
            f"DIVIDE ( CALCULATE ( COUNTROWS ( {table} ), {table}[{column}] = TRUE () ), "
            f"COUNTROWS ( {table} ) )"
        )

    if op == "count":
        table = resolved.get("table")
        if not table:
            raise SynthesisError(f"count missing table: {resolved!r}")
        return f"COUNTROWS ( {table} )"

    if op == "mul":
        terms = resolved.get("terms") or []
        if len(terms) < 2:
            raise SynthesisError(f"mul needs 2+ terms: {resolved!r}")
        return " * ".join(_term(t) for t in terms)

    if op == "delta_chain":
        subtrahends = resolved.get("subtrahends") or []
        if not subtrahends:
            raise SynthesisError(f"delta_chain needs 1+ subtrahends: {resolved!r}")
        parts = [_term(resolved.get("minuend"))] + [_term(s) for s in subtrahends]
        return " - ".join(parts)

    if op == "distinctcount":
        table, column = resolved.get("table"), resolved.get("column")
        if not table or not column:
            raise SynthesisError(f"distinctcount missing table/column: {resolved!r}")
        base = f"DISTINCTCOUNT ( {table}[{column}] )"
        filters = resolved.get("filters") or []
        if not filters:
            return base
        conditions = ", ".join(
            f"{f['table']}[{f['column']}] = {'TRUE' if f['equals'] else 'FALSE'} ()"
            for f in filters
        )
        return f"CALCULATE ( {base}, {conditions} )"

    if op == "count_threshold":
        table, column = resolved.get("table"), resolved.get("column")
        comparator, value = resolved.get("comparator"), resolved.get("value")
        if not table or not column or not comparator:
            raise SynthesisError(f"count_threshold missing table/column/comparator: {resolved!r}")
        return (
            f"CALCULATE ( COUNTROWS ( {table} ), {table}[{column}] {comparator} "
            f"{_format_number(value)} )"
        )

    if op == "round":
        value = resolved.get("value")
        digits = resolved.get("digits", 0)
        return f"ROUND ( {_term(value)}, {_format_number(digits)} )"

    if op == "sumx_over_key":
        table, key_column, value = resolved.get("table"), resolved.get("key_column"), resolved.get("value")
        if not table or not key_column:
            raise SynthesisError(f"sumx_over_key missing table/key_column: {resolved!r}")
        return f"SUMX ( VALUES ( {table}[{key_column}] ), CALCULATE ( {_term(value)} ) )"

    if op == "avgx_over_key":
        table, key_column, value = resolved.get("table"), resolved.get("key_column"), resolved.get("value")
        if not table or not key_column:
            raise SynthesisError(f"avgx_over_key missing table/key_column: {resolved!r}")
        return f"AVERAGEX ( VALUES ( {table}[{key_column}] ), CALCULATE ( {_term(value)} ) )"

    if op == "pvm_volume_effect":
        table = resolved.get("table")
        qty, plan_qty, plan_sales = (
            resolved.get("quantity_column"), resolved.get("plan_quantity_column"), resolved.get("plan_sales_column"),
        )
        if not table or not qty or not plan_qty or not plan_sales:
            raise SynthesisError(f"pvm_volume_effect missing fields: {resolved!r}")
        return (
            f"SUMX ( {table}, ( {table}[{qty}] - {table}[{plan_qty}] ) * "
            f"DIVIDE ( {table}[{plan_sales}], {table}[{plan_qty}] ) )"
        )

    if op == "pvm_price_effect":
        table = resolved.get("table")
        net_price, qty, plan_sales, plan_qty = (
            resolved.get("net_price_column"), resolved.get("quantity_column"),
            resolved.get("plan_sales_column"), resolved.get("plan_quantity_column"),
        )
        if not table or not net_price or not qty or not plan_sales or not plan_qty:
            raise SynthesisError(f"pvm_price_effect missing fields: {resolved!r}")
        return (
            f"SUMX ( {table}, ( DIVIDE ( {table}[{net_price}], {table}[{qty}] ) - "
            f"DIVIDE ( {table}[{plan_sales}], {table}[{plan_qty}] ) ) * {table}[{qty}] )"
        )

    if op == "avg":
        table, column = resolved.get("table"), resolved.get("column")
        if not table or not column:
            raise SynthesisError(f"avg missing table/column: {resolved!r}")
        return f"AVERAGE ( {table}[{column}] )"

    if op == "sumx_product":
        table = resolved.get("table")
        col_a, col_b = resolved.get("factor_a_column"), resolved.get("factor_b_column")
        if not table or not col_a or not col_b:
            raise SynthesisError(f"sumx_product missing fields: {resolved!r}")
        return f"SUMX ( {table}, {table}[{col_a}] * {table}[{col_b}] )"

    if op == "count_filtered":
        table = resolved.get("table")
        filters = resolved.get("filters") or []
        if not table or not filters:
            raise SynthesisError(f"count_filtered missing table/filters: {resolved!r}")
        conditions = ", ".join(f"{f['table']}[{f['column']}] = {_dax_literal(f['equals'])}" for f in filters)
        return f"CALCULATE ( COUNTROWS ( {table} ), {conditions} )"

    raise SynthesisError(f"unknown op: {op!r}")
