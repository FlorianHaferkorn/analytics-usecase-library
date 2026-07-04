"""Unit tests for `from_aluca._resolve_calculation`/`_resolve_calc_node` — the
resolution half of the DSL grammar extension (I-10.0 follow-up, "go for 1"):
recursive `calc_ref` (nested `{"calc": {...}}` terms) and the 9 new ops (mul,
delta_chain, distinctcount, count_threshold, round, sumx_over_key,
avgx_over_key, pvm_volume_effect, pvm_price_effect).

`test_dax_synth.py` covers synthesis from an already-resolved dict;
`test_dax_parity_legacy.py` covers the real catalog end-to-end against legacy
DAX. This file isolates the RESOLUTION step (calc_ref → neutral structure,
own-lineage column lookup, HITL fallback on unresolvable refs) using synthetic
in-memory KPI dicts, independent of the real catalog's authored content.
"""
from __future__ import annotations

from pathlib import Path

from tooling.superversion.from_aluca import KpiCatalog, _resolve_calc_node, _resolve_calculation
from tooling.superversion.targets import dax_synth

REPO = Path(__file__).resolve().parents[3]
CATALOG = KpiCatalog(REPO / "core/kpi_catalog/kpis")


def _kpi(calculation: dict, lineage: list[str]) -> dict:
    return {"kpi_id": "test.synthetic", "technical": {"lineage": lineage, "calculation": calculation}}


def test_mul_resolves_two_terms():
    kpi = _kpi(
        {"op": "mul", "terms": [{"kpi": "sales.net_sales.amount"}, {"column": "Discount Rate"}]},
        ["fact_sales.Discount Rate"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "mul",
        "terms": [{"kind": "measure", "name": "Net Sales Amount"}, {"kind": "column", "table": "fact_sales", "column": "Discount Rate"}],
    }


def test_mul_unresolvable_term_becomes_hitl():
    kpi = _kpi({"op": "mul", "terms": [{"kpi": "sales.net_sales.amount"}, {"kpi": "no.such.kpi"}]}, [])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert resolved is None
    assert "HITL:" in hitl and "terms" in hitl


def test_delta_chain_resolves_minuend_and_subtrahends():
    kpi = _kpi(
        {
            "op": "delta_chain",
            "minuend": {"kpi": "sales.net_sales.amount"},
            "subtrahends": [{"column": "Plan Sales Amount"}, {"kpi": "sales.pvm.price_effect.amount"}],
        },
        ["fact_sales.Plan Sales Amount"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved["op"] == "delta_chain"
    assert resolved["minuend"] == {"kind": "measure", "name": "Net Sales Amount"}
    assert len(resolved["subtrahends"]) == 2


def test_distinctcount_resolves_table_from_own_lineage():
    kpi = _kpi(
        {"op": "distinctcount", "column": "CustomerKey", "filters": [{"column": "Churn Flag", "equals": True}]},
        ["fact_customer_events.CustomerKey", "fact_customer_events.Churn Flag"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "distinctcount", "table": "fact_customer_events", "column": "CustomerKey",
        "filters": [{"table": "fact_customer_events", "column": "Churn Flag", "equals": True}],
    }


def test_distinctcount_unresolvable_filter_column_becomes_hitl():
    kpi = _kpi(
        {"op": "distinctcount", "column": "CustomerKey", "filters": [{"column": "Not In Lineage", "equals": True}]},
        ["fact_customer_events.CustomerKey"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert resolved is None
    assert "HITL:" in hitl


def test_count_threshold_resolves():
    kpi = _kpi({"op": "count_threshold", "column": "NPS Score", "comparator": ">=", "value": 9}, ["fact_nps.NPS Score"])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {"op": "count_threshold", "table": "fact_nps", "column": "NPS Score", "comparator": ">=", "value": 9}


def test_round_resolves_nested_calc_as_expr_kind():
    kpi = _kpi(
        {"op": "round", "digits": 0, "value": {"calc": {"op": "count", "column": "NPS Score"}}},
        ["fact_nps.NPS Score"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {"op": "round", "digits": 0, "value": {"kind": "expr", "op": "count", "table": "fact_nps"}}
    assert dax_synth.synthesize_dax(resolved) == "ROUND ( ( COUNTROWS ( fact_nps ) ), 0 )"


def test_sumx_over_key_resolves():
    kpi = _kpi({"op": "sumx_over_key", "key_column": "CustomerKey", "value": {"kpi": "sales.net_sales.amount"}}, ["fact_sales.CustomerKey"])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "sumx_over_key", "table": "fact_sales", "key_column": "CustomerKey",
        "value": {"kind": "measure", "name": "Net Sales Amount"},
    }


def test_avgx_over_key_missing_key_column_becomes_hitl():
    kpi = _kpi({"op": "avgx_over_key", "key_column": "Missing", "value": {"column": "CLV Amount"}}, ["fact_customer_value.CLV Amount"])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert resolved is None
    assert "HITL:" in hitl


def test_pvm_volume_effect_requires_all_columns_in_same_table():
    kpi = _kpi(
        {"op": "pvm_volume_effect", "quantity": "Quantity", "plan_quantity": "Plan Quantity", "plan_sales": "Plan Sales Amount"},
        ["fact_sales.Quantity", "fact_sales.Plan Quantity", "fact_sales.Plan Sales Amount"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved["table"] == "fact_sales"


def test_pvm_volume_effect_columns_in_different_tables_becomes_hitl():
    kpi = _kpi(
        {"op": "pvm_volume_effect", "quantity": "Quantity", "plan_quantity": "Plan Quantity", "plan_sales": "Plan Sales Amount"},
        ["fact_sales.Quantity", "fact_sales.Plan Quantity", "fact_other.Plan Sales Amount"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert resolved is None
    assert "HITL:" in hitl


def test_pvm_price_effect_resolves():
    kpi = _kpi(
        {
            "op": "pvm_price_effect", "net_price": "Net Price Amount", "quantity": "Quantity",
            "plan_sales": "Plan Sales Amount", "plan_quantity": "Plan Quantity",
        },
        ["fact_sales.Net Price Amount", "fact_sales.Quantity", "fact_sales.Plan Sales Amount", "fact_sales.Plan Quantity"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved["table"] == "fact_sales"
    assert resolved["net_price_column"] == "Net Price Amount"


def test_recursive_calc_ref_two_levels_deep():
    """`calc_ref` nesting isn't limited to one level — a `calc` term's own
    subterms can themselves nest `calc` again (verifies genuine recursion,
    not just one hardcoded level)."""
    kpi = _kpi(
        {
            "op": "delta",
            "minuend": {"kpi": "sales.net_sales.amount"},
            "subtrahend": {
                "calc": {
                    "op": "ratio",
                    "numerator": {"calc": {"op": "sum", "column": "A"}},
                    "denominator": {"calc": {"op": "sum", "column": "B"}},
                }
            },
        },
        ["fact_test.A", "fact_test.B"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    dax = dax_synth.synthesize_dax(resolved)
    assert dax == "[Net Sales Amount] - ( DIVIDE ( ( SUM ( fact_test[A] ) ), ( SUM ( fact_test[B] ) ) ) )"


def test_unknown_op_becomes_hitl_with_diagnosable_reason():
    kpi = _kpi({"op": "not_a_real_op"}, [])
    resolved, hitl = _resolve_calc_node({"op": "not_a_real_op"}, {}, [], CATALOG)
    assert resolved is None
    assert "unknown op" in hitl


def test_literal_calc_ref_resolves_to_bare_value():
    """`{"literal": n}` — a bare numeric constant term (e.g. the legacy
    `[Baseline Sales Amount] * 0.15` proxy factor for Cannibalized Sales
    Amount) — resolves without needing any lineage/catalog lookup."""
    kpi = _kpi({"op": "mul", "terms": [{"kpi": "sales.net_sales.amount"}, {"literal": 0.15}]}, [])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "mul",
        "terms": [{"kind": "measure", "name": "Net Sales Amount"}, {"kind": "literal", "value": 0.15}],
    }
    assert dax_synth.synthesize_dax(resolved) == "[Net Sales Amount] * 0.15"


def test_avg_resolves_column_to_table():
    kpi = _kpi({"op": "avg", "column": "Standard Rate Units Per Minute"}, ["fact_ops.Standard Rate Units Per Minute"])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {"op": "avg", "table": "fact_ops", "column": "Standard Rate Units Per Minute"}


def test_sumx_product_requires_same_table_for_both_factors():
    kpi = _kpi(
        {"op": "sumx_product", "factor_a": "Standard Rate Units Per Minute", "factor_b": "Planned Time Minutes"},
        ["fact_ops.Standard Rate Units Per Minute", "fact_ops.Planned Time Minutes"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "sumx_product", "table": "fact_ops",
        "factor_a_column": "Standard Rate Units Per Minute", "factor_b_column": "Planned Time Minutes",
    }


def test_sumx_product_different_tables_becomes_hitl():
    kpi = _kpi(
        {"op": "sumx_product", "factor_a": "A", "factor_b": "B"},
        ["fact_x.A", "fact_y.B"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert resolved is None
    assert "HITL:" in hitl


def test_count_filtered_resolves_string_and_bool_filters():
    kpi = _kpi(
        {
            "op": "count_filtered", "column": "Order Type",
            "filters": [{"column": "Order Type", "equals": "PM"}, {"column": "Order Status", "equals": "Completed"}],
        },
        ["fact_maintenance.Order Type", "fact_maintenance.Order Status"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "count_filtered", "table": "fact_maintenance",
        "filters": [
            {"table": "fact_maintenance", "column": "Order Type", "equals": "PM"},
            {"table": "fact_maintenance", "column": "Order Status", "equals": "Completed"},
        ],
    }


def test_count_filtered_unresolvable_filter_column_becomes_hitl():
    kpi = _kpi(
        {"op": "count_filtered", "column": "Order Type", "filters": [{"column": "Not In Lineage", "equals": "x"}]},
        ["fact_maintenance.Order Type"],
    )
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert resolved is None
    assert "HITL:" in hitl


def test_add_resolves_kpi_and_column_terms():
    kpi = _kpi({"op": "add", "terms": [{"kpi": "wc.dso.days"}, {"kpi": "wc.dio.days"}]}, [])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {
        "op": "add",
        "terms": [{"kind": "measure", "name": "DSO Days"}, {"kind": "measure", "name": "DIO Days"}],
    }
    assert dax_synth.synthesize_dax(resolved) == "[DSO Days] + [DIO Days]"


def test_abs_resolves_nested_calc():
    kpi = _kpi({"op": "abs", "value": {"calc": {"op": "sum", "column": "A"}}}, ["fact_test.A"])
    resolved, hitl = _resolve_calculation(kpi, CATALOG)
    assert hitl is None
    assert resolved == {"op": "abs", "value": {"kind": "expr", "op": "sum", "ref": {"kind": "column", "table": "fact_test", "column": "A"}}}
    assert dax_synth.synthesize_dax(resolved) == "ABS ( ( SUM ( fact_test[A] ) ) )"
