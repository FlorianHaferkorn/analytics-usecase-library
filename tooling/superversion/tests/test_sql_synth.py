"""Unit tests for the DSL→SQL synthesis (I-10.0 follow-up, "go for 2").

Pure-function tests for `targets/sql_synth.py` — the Databricks-SQL counterpart
to `targets/dax_synth.py`. Same resolved-neutral-formula input shape (produced
by `from_aluca._resolve_calculation`); different, SQL-flavored output.
"""
from __future__ import annotations

import pytest

from tooling.superversion.targets import sql_synth as s


def _col(table, column):
    return {"kind": "column", "table": table, "column": column}


def _measure(name):
    return {"kind": "measure", "name": name}


def _expr(inner: dict):
    return {"kind": "expr", **inner}


def test_sum_column_simple_ident():
    resolved = {"op": "sum", "ref": _col("fact_sales", "quantity")}
    assert s.synthesize_sql(resolved) == "SUM ( quantity )"


def test_sum_column_needs_backtick_quoting():
    resolved = {"op": "sum", "ref": _col("fact_sales", "Net Sales Amount")}
    assert s.synthesize_sql(resolved) == "SUM ( `Net Sales Amount` )"


def test_measure_ref_uses_measure_builtin():
    resolved = {"op": "ratio", "numerator": _measure("Gross Margin Amount"), "denominator": _measure("Net Sales Amount")}
    assert s.synthesize_sql(resolved) == "TRY_DIVIDE ( MEASURE ( `Gross Margin Amount` ), MEASURE ( `Net Sales Amount` ) )"


def test_ratio_with_scale():
    resolved = {"op": "ratio", "numerator": _col("t", "a"), "denominator": _col("t", "b"), "scale": 1000}
    assert s.synthesize_sql(resolved) == "TRY_DIVIDE ( SUM ( a ), SUM ( b ) ) * 1000"


def test_ratio_scale_of_one_is_noop():
    resolved = {"op": "ratio", "numerator": _col("t", "a"), "denominator": _col("t", "b"), "scale": 1}
    assert s.synthesize_sql(resolved) == "TRY_DIVIDE ( SUM ( a ), SUM ( b ) )"


def test_delta():
    resolved = {"op": "delta", "minuend": _measure("A"), "subtrahend": _measure("B")}
    assert s.synthesize_sql(resolved) == "MEASURE ( A ) - MEASURE ( B )"


def test_delta_pct():
    resolved = {"op": "delta_pct", "minuend": _measure("Net Sales Amount"), "subtrahend": _col("fact_sales", "Plan Sales Amount")}
    assert s.synthesize_sql(resolved) == (
        "TRY_DIVIDE ( MEASURE ( `Net Sales Amount` ) - SUM ( `Plan Sales Amount` ), "
        "ABS ( SUM ( `Plan Sales Amount` ) ) )"
    )


def test_rate_flag_share():
    resolved = {"op": "rate", "table": "fact_fulfillment", "column": "OTIF Flag"}
    assert s.synthesize_sql(resolved) == (
        "TRY_DIVIDE ( SUM ( CASE WHEN `OTIF Flag` = TRUE THEN 1 ELSE 0 END ), COUNT ( * ) )"
    )


def test_count_bare_table():
    resolved = {"op": "count", "table": "fact_fulfillment"}
    assert s.synthesize_sql(resolved) == "COUNT ( * )"


def test_mul_two_terms():
    resolved = {"op": "mul", "terms": [_measure("Incremental Sales Amount"), _measure("Gross Margin %")]}
    assert s.synthesize_sql(resolved) == "MEASURE ( `Incremental Sales Amount` ) * MEASURE ( `Gross Margin %` )"


def test_delta_chain_four_terms():
    resolved = {
        "op": "delta_chain",
        "minuend": _measure("Net Sales Amount"),
        "subtrahends": [_col("fact_sales", "Plan Sales Amount"), _measure("Price Effect Amount"), _measure("Volume Effect Amount")],
    }
    assert s.synthesize_sql(resolved) == (
        "MEASURE ( `Net Sales Amount` ) - SUM ( `Plan Sales Amount` ) - "
        "MEASURE ( `Price Effect Amount` ) - MEASURE ( `Volume Effect Amount` )"
    )


def test_distinctcount_no_filter():
    resolved = {"op": "distinctcount", "table": "fact_customer_events", "column": "CustomerKey"}
    assert s.synthesize_sql(resolved) == "COUNT ( DISTINCT CustomerKey )"


def test_distinctcount_two_filters_one_negated():
    resolved = {
        "op": "distinctcount", "table": "fact_customer_events", "column": "CustomerKey",
        "filters": [
            {"table": "fact_customer_events", "column": "Activity Flag", "equals": True},
            {"table": "fact_customer_events", "column": "Churn Flag", "equals": False},
        ],
    }
    assert s.synthesize_sql(resolved) == (
        "COUNT ( DISTINCT CASE WHEN `Activity Flag` = TRUE AND `Churn Flag` = FALSE THEN CustomerKey END )"
    )


def test_count_threshold():
    resolved = {"op": "count_threshold", "table": "fact_nps", "column": "NPS Score", "comparator": ">=", "value": 9}
    assert s.synthesize_sql(resolved) == "COUNT ( CASE WHEN `NPS Score` >= 9 THEN 1 END )"


def test_round_wraps_nested_expr():
    resolved = {"op": "round", "digits": 0, "value": _expr({"op": "ratio", "numerator": _measure("A"), "denominator": _measure("B"), "scale": 100})}
    assert s.synthesize_sql(resolved) == "ROUND ( ( TRY_DIVIDE ( MEASURE ( A ), MEASURE ( B ) ) * 100 ), 0 )"


def test_nested_expr_ref_recurses_and_parenthesizes():
    resolved = {"op": "delta", "minuend": _measure("A"), "subtrahend": _expr({"op": "sum", "ref": _col("t", "b")})}
    assert s.synthesize_sql(resolved) == "MEASURE ( A ) - ( SUM ( b ) )"


@pytest.mark.parametrize("op", ["sumx_over_key", "avgx_over_key", "pvm_volume_effect", "pvm_price_effect"])
def test_no_flat_sql_shape_ops_raise_synthesis_error(op):
    """These 4 ops (of the 16 the DAX side covers) need a per-key GROUP BY
    subquery — genuinely beyond a single Metric View `expr` string. Must raise,
    never guess a wrong flat expression."""
    with pytest.raises(s.SynthesisError):
        s.synthesize_sql({"op": op, "table": "t", "key_column": "k", "value": _measure("A")})


@pytest.mark.parametrize(
    "resolved",
    [
        {"op": "unknown_op"},
        {"op": "sum", "ref": {"kind": "bogus"}},
        {"op": "sum", "ref": {"kind": "column", "table": "t"}},  # missing column
        {"op": "ratio", "numerator": _col("t", "a")},  # missing denominator
        {"op": "rate", "table": "t"},  # missing column
        {"op": "count"},  # missing table
        {"op": "mul", "terms": [_measure("A")]},  # needs 2+
        {"op": "delta_chain", "minuend": _measure("A"), "subtrahends": []},
        {"op": "distinctcount", "table": "t"},  # missing column
        {"op": "count_threshold", "table": "t", "column": "c"},  # missing comparator
        "not-a-dict",
        {"op": "sum", "ref": None},
    ],
)
def test_malformed_or_unknown_raises_synthesis_error(resolved):
    with pytest.raises(s.SynthesisError):
        s.synthesize_sql(resolved)


def test_identifier_quoting_is_idempotent_for_simple_names():
    assert s._ident("quantity") == "quantity"
    assert s._ident("Net Sales Amount") == "`Net Sales Amount`"
    assert s._ident("weird`name") == "`weird``name`"
