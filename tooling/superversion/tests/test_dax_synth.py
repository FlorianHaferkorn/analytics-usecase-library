"""Unit tests for the DSL→DAX synthesis (task I-10.0 / Cut S-1).

Pure-function tests for `targets/dax_synth.py` — the deterministic materializer
that turns a resolved, stack-neutral formula (produced by `from_aluca`'s
`_resolve_calculation`) into real DAX text. See `test_calculation_coverage.py`
for the end-to-end (catalog → canonical model → TMDL) coverage assertions and
`test_dax_parity_legacy.py` for the parity check against the legacy generator.
"""
from __future__ import annotations

import pytest

from tooling.superversion.targets import dax_synth as d


def _col(table, column):
    return {"kind": "column", "table": table, "column": column}


def _measure(name):
    return {"kind": "measure", "name": name}


def test_sum_column():
    resolved = {"op": "sum", "ref": _col("fact_sales", "Net Sales Amount")}
    assert d.synthesize_dax(resolved) == "SUM ( fact_sales[Net Sales Amount] )"


def test_ratio_measure_over_measure():
    resolved = {"op": "ratio", "numerator": _measure("Gross Margin Amount"), "denominator": _measure("Net Sales Amount")}
    assert d.synthesize_dax(resolved) == "DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )"


def test_ratio_column_over_column():
    resolved = {"op": "ratio", "numerator": _col("fact_cost", "COGS Amount"), "denominator": _col("fact_output", "Output Units")}
    assert d.synthesize_dax(resolved) == "DIVIDE ( SUM ( fact_cost[COGS Amount] ), SUM ( fact_output[Output Units] ) )"


def test_ratio_with_scale():
    resolved = {
        "op": "ratio",
        "numerator": _col("fact_quality", "Defect Count"),
        "denominator": _col("fact_quality", "Total Units"),
        "scale": 1000,
    }
    assert d.synthesize_dax(resolved) == (
        "DIVIDE ( SUM ( fact_quality[Defect Count] ), SUM ( fact_quality[Total Units] ) ) * 1000"
    )


def test_ratio_scale_of_one_is_a_noop():
    resolved = {"op": "ratio", "numerator": _col("t", "a"), "denominator": _col("t", "b"), "scale": 1}
    assert d.synthesize_dax(resolved) == "DIVIDE ( SUM ( t[a] ), SUM ( t[b] ) )"


def test_mixed_ratio_measure_over_column():
    """cost.cogs_per_unit.amount: DIVIDE([Cost of Goods Sold Amount], SUM(fact_sales[Quantity]))."""
    resolved = {"op": "ratio", "numerator": _measure("Cost of Goods Sold Amount"), "denominator": _col("fact_sales", "Quantity")}
    assert d.synthesize_dax(resolved) == "DIVIDE ( [Cost of Goods Sold Amount], SUM ( fact_sales[Quantity] ) )"


def test_delta_of_measures():
    resolved = {"op": "delta", "minuend": _measure("Net Sales Amount"), "subtrahend": _measure("Cost of Goods Sold Amount")}
    assert d.synthesize_dax(resolved) == "[Net Sales Amount] - [Cost of Goods Sold Amount]"


def test_delta_pct_measure_minus_column():
    resolved = {"op": "delta_pct", "minuend": _measure("Net Sales Amount"), "subtrahend": _col("fact_sales", "Plan Sales Amount")}
    assert d.synthesize_dax(resolved) == (
        "DIVIDE ( [Net Sales Amount] - SUM ( fact_sales[Plan Sales Amount] ), "
        "ABS ( SUM ( fact_sales[Plan Sales Amount] ) ) )"
    )


def test_rate_flag_share():
    resolved = {"op": "rate", "table": "fact_fulfillment", "column": "OTIF Flag"}
    assert d.synthesize_dax(resolved) == (
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_fulfillment ), fact_fulfillment[OTIF Flag] = TRUE () ), "
        "COUNTROWS ( fact_fulfillment ) )"
    )


def test_count_table():
    resolved = {"op": "count", "table": "fact_fulfillment"}
    assert d.synthesize_dax(resolved) == "COUNTROWS ( fact_fulfillment )"


@pytest.mark.parametrize(
    "resolved",
    [
        {"op": "unknown_op"},
        {"op": "sum", "ref": {"kind": "bogus"}},
        {"op": "sum", "ref": {"kind": "column", "table": "t"}},  # missing column
        {"op": "ratio", "numerator": _col("t", "a")},  # missing denominator
        {"op": "rate", "table": "t"},  # missing column
        {"op": "count"},  # missing table
        "not-a-dict",
        {"op": "sum", "ref": None},
    ],
)
def test_malformed_or_unknown_raises_synthesis_error(resolved):
    with pytest.raises(d.SynthesisError):
        d.synthesize_dax(resolved)


def test_never_emits_colon_equals():
    """TMDL hard-rule (AGENTS.md): DAX assignment is '=', never ':=' — the
    synthesizer only returns the RHS expression, so this should be structurally
    impossible, but assert it explicitly across every op shape."""
    cases = [
        {"op": "sum", "ref": _col("t", "a")},
        {"op": "ratio", "numerator": _measure("A"), "denominator": _measure("B")},
        {"op": "delta", "minuend": _measure("A"), "subtrahend": _measure("B")},
        {"op": "delta_pct", "minuend": _measure("A"), "subtrahend": _col("t", "b")},
        {"op": "rate", "table": "t", "column": "Flag"},
        {"op": "count", "table": "t"},
    ]
    for resolved in cases:
        assert ":=" not in d.synthesize_dax(resolved)
