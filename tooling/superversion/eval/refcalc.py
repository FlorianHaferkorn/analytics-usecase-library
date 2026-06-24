"""refcalc — transparent reference aggregation for value certification (task I-4.1).

The KPI catalog deliberately carries *meaning + lineage*, not a formula (Golden
Thread: ALUCA defines what a KPI means, not its DAX). To certify *values* we
therefore need an independent, auditable reference computation over the synthetic
fact — that is this module.

It supports a tiny, deliberately-readable formula DSL so the expectation files
stay human-checkable:

    sum(<column>)                       → Σ column
    sum(<a>) / sum(<b>)                 → Σa / Σb   (ratio; b must be non-zero)

This is NOT a calc engine and is not on any generation path (Invariant I2): it is
the reference oracle the Value-Gate (I-4.2) compares the generated model against.
Anything outside the grammar raises `FormulaError` rather than guessing.
"""
from __future__ import annotations

import re

Rows = list[dict]


class FormulaError(ValueError):
    """A formula is outside the supported reference grammar (or references an
    unknown / non-numeric column)."""


_SUM = re.compile(r"^sum\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)$")


def _column_sum(rows: Rows, column: str) -> float:
    total = 0.0
    for i, row in enumerate(rows):
        if column not in row:
            raise FormulaError(f"row {i} has no column '{column}'")
        try:
            total += float(row[column])
        except (TypeError, ValueError) as exc:
            raise FormulaError(f"row {i} column '{column}' is not numeric: {row[column]!r}") from exc
    return total


def recompute(formula: str, rows: Rows) -> float:
    """Evaluate a reference `formula` over `rows`. Pure & deterministic."""
    expr = formula.strip()
    if "/" in expr:
        left, right = (part.strip() for part in expr.split("/", 1))
        num, den = _eval_sum(left, rows), _eval_sum(right, rows)
        if den == 0:
            raise FormulaError(f"division by zero in '{formula}' (denominator {right} is 0)")
        return num / den
    return _eval_sum(expr, rows)


def _eval_sum(term: str, rows: Rows) -> float:
    match = _SUM.match(term.strip())
    if not match:
        raise FormulaError(f"unsupported term '{term}' (expected 'sum(<column>)')")
    return _column_sum(rows, match.group(1))
