"""Tests for the value-certification reference data + oracle (task I-4.1).

DoD: reference data loads (testable), and the checked-in expected KPI values are
self-consistent with their formulas over the reference dataset (so they are
reproducible golden values, not hand-authored magic numbers).
"""
from __future__ import annotations

import pytest

from tooling.superversion import eval as ev
from tooling.superversion.eval import refcalc

GATED_UC = "COM-001"
DATASET = "commercial_invoice_lines"


def test_dataset_loads_with_grain_and_rows():
    ds = ev.load_dataset(DATASET)
    assert ds.grain == "invoice_line"
    assert ds.rows, "reference dataset must have rows"
    # Every declared column is present in every row.
    for row in ds.rows:
        assert set(ds.columns) <= set(row), f"row missing columns: {row}"


def test_available_lists():
    assert DATASET in ev.available_datasets()
    assert GATED_UC in ev.available_use_cases()


def test_expectations_load_and_reference_governed_kpis():
    exp = ev.load_expectations(GATED_UC)
    assert exp.dataset == DATASET
    names = {k.measure_name for k in exp.kpis}
    assert {"Net Sales Amount", "Gross Margin Amount", "Gross Margin %"} <= names
    # Governed KPIs carry a catalog kpi_id; comparison measures may not.
    governed = [k for k in exp.kpis if not k.comparison]
    assert governed and all(k.kpi_id for k in governed)


def test_expected_values_are_self_consistent():
    """Each checked-in `value` equals its `formula` recomputed over the dataset."""
    ds = ev.load_dataset(DATASET)
    exp = ev.load_expectations(GATED_UC)
    for k in exp.kpis:
        recomputed = refcalc.recompute(k.formula, ds.rows)
        assert abs(recomputed - k.value) <= k.tolerance, (
            f"{k.measure_name}: checked-in {k.value} drifts from "
            f"{k.formula}={recomputed}"
        )


def test_known_aggregates():
    ds = ev.load_dataset(DATASET)
    assert refcalc.recompute("sum(net_sales_amount)", ds.rows) == pytest.approx(10000.0)
    assert refcalc.recompute("sum(gross_margin_amount) / sum(net_sales_amount)", ds.rows) == pytest.approx(0.409)


def test_refcalc_rejects_unknown_grammar_and_columns():
    rows = [{"a": 1.0, "b": 2.0}]
    with pytest.raises(refcalc.FormulaError):
        refcalc.recompute("avg(a)", rows)          # unsupported function
    with pytest.raises(refcalc.FormulaError):
        refcalc.recompute("sum(missing)", rows)    # unknown column
    with pytest.raises(refcalc.FormulaError):
        refcalc.recompute("sum(a) / sum(zero)", [{"a": 1.0, "zero": 0.0}])  # missing col in denom


def test_refcalc_division_by_zero():
    with pytest.raises(refcalc.FormulaError):
        refcalc.recompute("sum(a) / sum(b)", [{"a": 5.0, "b": 0.0}])


def test_missing_dataset_and_uc_raise():
    with pytest.raises(FileNotFoundError):
        ev.load_dataset("does_not_exist")
    with pytest.raises(FileNotFoundError):
        ev.load_expectations("ZZZ-999")
