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


def _expr(inner: dict):
    return {"kind": "expr", **inner}


# ---- I-10.0 grammar extension (13-KPI follow-up) -------------------------- #

def test_mul_two_terms():
    resolved = {"op": "mul", "terms": [_measure("Incremental Sales Amount"), _measure("Gross Margin %")]}
    assert d.synthesize_dax(resolved) == "[Incremental Sales Amount] * [Gross Margin %]"


def test_mul_needs_at_least_two_terms():
    with pytest.raises(d.SynthesisError):
        d.synthesize_dax({"op": "mul", "terms": [_measure("A")]})


def test_delta_chain_four_terms():
    resolved = {
        "op": "delta_chain",
        "minuend": _measure("Net Sales Amount"),
        "subtrahends": [_col("fact_sales", "Plan Sales Amount"), _measure("Price Effect Amount"), _measure("Volume Effect Amount")],
    }
    assert d.synthesize_dax(resolved) == (
        "[Net Sales Amount] - SUM ( fact_sales[Plan Sales Amount] ) - [Price Effect Amount] - [Volume Effect Amount]"
    )


def test_delta_chain_needs_at_least_one_subtrahend():
    with pytest.raises(d.SynthesisError):
        d.synthesize_dax({"op": "delta_chain", "minuend": _measure("A"), "subtrahends": []})


def test_distinctcount_no_filter():
    resolved = {"op": "distinctcount", "table": "fact_customer_events", "column": "CustomerKey"}
    assert d.synthesize_dax(resolved) == "DISTINCTCOUNT ( fact_customer_events[CustomerKey] )"


def test_distinctcount_one_filter():
    resolved = {
        "op": "distinctcount", "table": "fact_customer_events", "column": "CustomerKey",
        "filters": [{"table": "fact_customer_events", "column": "Churn Flag", "equals": True}],
    }
    assert d.synthesize_dax(resolved) == (
        "CALCULATE ( DISTINCTCOUNT ( fact_customer_events[CustomerKey] ), "
        "fact_customer_events[Churn Flag] = TRUE () )"
    )


def test_distinctcount_two_filters_one_negated():
    resolved = {
        "op": "distinctcount", "table": "fact_customer_events", "column": "CustomerKey",
        "filters": [
            {"table": "fact_customer_events", "column": "Activity Flag", "equals": True},
            {"table": "fact_customer_events", "column": "Churn Flag", "equals": False},
        ],
    }
    assert d.synthesize_dax(resolved) == (
        "CALCULATE ( DISTINCTCOUNT ( fact_customer_events[CustomerKey] ), "
        "fact_customer_events[Activity Flag] = TRUE (), fact_customer_events[Churn Flag] = FALSE () )"
    )


def test_count_threshold():
    resolved = {"op": "count_threshold", "table": "fact_nps", "column": "NPS Score", "comparator": ">=", "value": 9}
    assert d.synthesize_dax(resolved) == "CALCULATE ( COUNTROWS ( fact_nps ), fact_nps[NPS Score] >= 9 )"


def test_round_wraps_nested_expr():
    resolved = {"op": "round", "digits": 0, "value": _expr({"op": "ratio", "numerator": _measure("A"), "denominator": _measure("B"), "scale": 100})}
    assert d.synthesize_dax(resolved) == "ROUND ( ( DIVIDE ( [A], [B] ) * 100 ), 0 )"


def test_sumx_over_key():
    resolved = {"op": "sumx_over_key", "table": "fact_sales", "key_column": "CustomerKey", "value": _measure("Net Sales Amount")}
    assert d.synthesize_dax(resolved) == "SUMX ( VALUES ( fact_sales[CustomerKey] ), CALCULATE ( [Net Sales Amount] ) )"


def test_avgx_over_key():
    resolved = {"op": "avgx_over_key", "table": "fact_customer_value", "key_column": "CustomerKey", "value": _col("fact_customer_value", "CLV Amount")}
    assert d.synthesize_dax(resolved) == (
        "AVERAGEX ( VALUES ( fact_customer_value[CustomerKey] ), CALCULATE ( SUM ( fact_customer_value[CLV Amount] ) ) )"
    )


def test_pvm_volume_effect():
    resolved = {
        "op": "pvm_volume_effect", "table": "fact_sales",
        "quantity_column": "Quantity", "plan_quantity_column": "Plan Quantity", "plan_sales_column": "Plan Sales Amount",
    }
    assert d.synthesize_dax(resolved) == (
        "SUMX ( fact_sales, ( fact_sales[Quantity] - fact_sales[Plan Quantity] ) * "
        "DIVIDE ( fact_sales[Plan Sales Amount], fact_sales[Plan Quantity] ) )"
    )


def test_pvm_price_effect():
    resolved = {
        "op": "pvm_price_effect", "table": "fact_sales",
        "net_price_column": "Net Price Amount", "quantity_column": "Quantity",
        "plan_sales_column": "Plan Sales Amount", "plan_quantity_column": "Plan Quantity",
    }
    assert d.synthesize_dax(resolved) == (
        "SUMX ( fact_sales, ( DIVIDE ( fact_sales[Net Price Amount], fact_sales[Quantity] ) - "
        "DIVIDE ( fact_sales[Plan Sales Amount], fact_sales[Plan Quantity] ) ) * fact_sales[Quantity] )"
    )


def test_nested_expr_ref_recurses_and_parenthesizes():
    resolved = {"op": "delta", "minuend": _measure("A"), "subtrahend": _expr({"op": "sum", "ref": _col("t", "b")})}
    assert d.synthesize_dax(resolved) == "[A] - ( SUM ( t[b] ) )"


@pytest.mark.parametrize(
    "resolved",
    [
        {"op": "mul", "terms": [_measure("A")]},
        {"op": "delta_chain", "minuend": _measure("A"), "subtrahends": []},
        {"op": "distinctcount", "table": "t"},  # missing column
        {"op": "count_threshold", "table": "t", "column": "c"},  # missing comparator
        {"op": "sumx_over_key", "key_column": "k", "value": _measure("A")},  # missing table
        {"op": "avgx_over_key", "table": "t", "value": _measure("A")},  # missing key_column
        {"op": "pvm_volume_effect", "table": "t"},  # missing columns
        {"op": "pvm_price_effect", "table": "t"},  # missing columns
        {"kind": "expr", "op": "unknown_op"},  # nested expr with unknown op bubbles up
    ],
)
def test_new_ops_malformed_raises_synthesis_error(resolved):
    with pytest.raises(d.SynthesisError):
        if resolved.get("kind") == "expr":
            d._term(resolved)
        else:
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
