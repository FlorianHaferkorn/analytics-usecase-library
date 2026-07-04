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

    sum        -- SUM ( table[column] )
    ratio      -- DIVIDE ( num, den ) [* scale]
    delta      -- minuend - subtrahend
    delta_pct  -- DIVIDE ( minuend - subtrahend, ABS ( subtrahend ) )
    rate       -- DIVIDE ( CALCULATE ( COUNTROWS ( t ), t[flag] = TRUE () ), COUNTROWS ( t ) )
    count      -- COUNTROWS ( table )

A "ref" term is either {"kind": "column", "table": ..., "column": ...} (rendered
as ``SUM ( table[column] )``) or {"kind": "measure", "name": ...} (rendered as
``[Measure Name]``, a DAX measure reference to a sibling measure).
"""
from __future__ import annotations


class SynthesisError(ValueError):
    """A resolved formula is malformed or uses an unknown op/ref kind."""


def _format_number(n) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


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

    raise SynthesisError(f"unknown op: {op!r}")
