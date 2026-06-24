"""Tests for the KPI value-certification gate (task I-4.2).

DoD: a deliberately wrong computed value turns the gate red; correct values pass;
the advisory rollback downgrades; no values (no engine) is advisory, not a failure.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.superversion import eval as ev
from tooling.superversion.eval import refcalc, value_gate

UC = "COM-001"
DATASET = "commercial_invoice_lines"


def _reference_computed() -> dict[str, float]:
    """Correct computed values = the reference oracle over the same dataset."""
    ds = ev.load_dataset(DATASET)
    exp = ev.load_expectations(UC)
    return {k.measure_name: refcalc.recompute(k.formula, ds.rows) for k in exp.kpis}


def test_correct_values_pass():
    computed = _reference_computed()
    outcomes = value_gate.assert_values(UC, computed)  # must not raise
    assert all(o.within for o in outcomes)
    assert all(o.computed for o in outcomes)


def test_wrong_value_is_caught():
    computed = _reference_computed()
    computed["Net Sales Amount"] += 5000.0  # well beyond tolerance 0.01
    with pytest.raises(value_gate.ValueGateError):
        value_gate.assert_values(UC, computed)
    outcomes = value_gate.check_values(UC, computed)
    bad = next(o for o in outcomes if o.measure_name == "Net Sales Amount")
    assert not bad.within and bad.deviation == pytest.approx(5000.0)


def test_advisory_downgrades_violation():
    computed = _reference_computed()
    computed["Net Sales Amount"] += 5000.0
    # advisory rollback: returns outcomes, does not raise
    outcomes = value_gate.assert_values(UC, computed, advisory=True)
    assert any(o.computed and not o.within for o in outcomes)


def test_uncomputed_is_not_a_violation():
    # No values at all (no engine) → every KPI uncomputed, nothing blocks.
    outcomes = value_gate.assert_values(UC, {})
    assert outcomes and all(not o.computed for o in outcomes)
    assert all(o.within for o in outcomes)  # uncomputed counts as within (advisory)


def test_tolerance_boundary():
    computed = _reference_computed()
    exp = {k.measure_name: k for k in ev.load_expectations(UC).kpis}
    tol = exp["Gross Margin %"].tolerance
    computed["Gross Margin %"] += tol            # exactly at tolerance → within
    assert value_gate.check_values(UC, computed)
    value_gate.assert_values(UC, computed)               # no raise
    computed["Gross Margin %"] += tol            # now beyond → violation
    with pytest.raises(value_gate.ValueGateError):
        value_gate.assert_values(UC, computed)


def test_cli_main_red_on_wrong_value(tmp_path: Path, capsys):
    import yaml
    computed = _reference_computed()
    computed["Net Sales Amount"] += 9999.0
    vfile = tmp_path / "computed.yaml"
    vfile.write_text(yaml.safe_dump(computed), encoding="utf-8")
    assert value_gate.main([UC, "--values", str(vfile)]) == 1
    assert "FAIL" in capsys.readouterr().out
    # rollback flag makes it exit 0
    assert value_gate.main([UC, "--values", str(vfile), "--advisory"]) == 0


def test_cli_main_advisory_without_values(capsys):
    assert value_gate.main([UC]) == 0
    assert "ADVISORY" in capsys.readouterr().out


def test_cli_main_green_on_correct_values(tmp_path: Path):
    import yaml
    vfile = tmp_path / "computed.yaml"
    vfile.write_text(yaml.safe_dump(_reference_computed()), encoding="utf-8")
    assert value_gate.main([UC, "--values", str(vfile)]) == 0
