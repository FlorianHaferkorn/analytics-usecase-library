"""Cross-ontology regression suite for value certification (task I-4.3).

I-4.1/4.2 stood up the concept + gate on ONE ontology (Commercial). I-4.3
guards against "only one demo tenant" by running the SAME checks across **every**
reference ontology (≥2): Commercial invoice lines + Supply-Chain deliveries.

Each ontology must: load with a grain, be self-consistent (checked-in expected
values equal their formula over the dataset), pass the Value-Gate on the
reference-computed values, and go red when a value is perturbed.
"""
from __future__ import annotations

import pytest

from tooling.superversion import eval as ev
from tooling.superversion.eval import refcalc, value_gate

# Every UC with checked-in expectations is exercised — discovered, not hardcoded,
# so adding a third ontology automatically extends the regression suite.
USE_CASES = ev.available_use_cases()


def test_at_least_two_reference_ontologies():
    """The whole point of I-4.3: the eval is not anchored to a single tenant."""
    assert len(USE_CASES) >= 2, f"expected ≥2 reference ontologies, got {USE_CASES}"
    assert len(ev.available_datasets()) >= 2


@pytest.mark.parametrize("uc", USE_CASES)
def test_ontology_dataset_loads(uc):
    exp = ev.load_expectations(uc)
    ds = ev.load_dataset(exp.dataset)          # raises if the ontology is incomplete
    assert ds.grain and ds.rows
    assert exp.kpis, f"{uc} has no expected KPIs"


@pytest.mark.parametrize("uc", USE_CASES)
def test_ontology_is_self_consistent(uc):
    exp = ev.load_expectations(uc)
    ds = ev.load_dataset(exp.dataset)
    for k in exp.kpis:
        recomputed = refcalc.recompute(k.formula, ds.rows)
        assert abs(recomputed - k.value) <= k.tolerance, (
            f"{uc}/{k.measure_name}: {k.value} drifts from {k.formula}={recomputed}"
        )


@pytest.mark.parametrize("uc", USE_CASES)
def test_value_gate_green_on_reference_values(uc):
    exp = ev.load_expectations(uc)
    ds = ev.load_dataset(exp.dataset)
    computed = {k.measure_name: refcalc.recompute(k.formula, ds.rows) for k in exp.kpis}
    outcomes = value_gate.assert_values(uc, computed)   # must not raise
    assert outcomes and all(o.within for o in outcomes)


@pytest.mark.parametrize("uc", USE_CASES)
def test_value_gate_red_on_perturbation(uc):
    exp = ev.load_expectations(uc)
    ds = ev.load_dataset(exp.dataset)
    computed = {k.measure_name: refcalc.recompute(k.formula, ds.rows) for k in exp.kpis}
    # Perturb the first KPI well beyond its tolerance.
    first = exp.kpis[0]
    computed[first.measure_name] += max(first.tolerance * 100, 1.0)
    with pytest.raises(value_gate.ValueGateError):
        value_gate.assert_values(uc, computed)
