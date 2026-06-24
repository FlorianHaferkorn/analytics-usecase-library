"""eval — value-certification reference data + oracle (Initiative I-4).

I-4.1 ships the *concept + reference dataset*: a small synthetic fact, per-UC
expected KPI values, a transparent reference aggregation (`refcalc`), and loaders
(`refdata`). The Value-Gate that compares a generated model against these
(FAIL on drift > tolerance) is I-4.2.
"""
from tooling.superversion.eval.refcalc import FormulaError, recompute
from tooling.superversion.eval.refdata import (
    ExpectedKpi,
    Expectations,
    ReferenceDataset,
    available_datasets,
    available_use_cases,
    load_dataset,
    load_expectations,
)

# Note: the Value-Gate lives in `value_gate.py` and is used as a CLI stage gate
# (`python -m tooling.superversion.eval.value_gate`), like `golden_thread`; it is
# intentionally NOT re-exported here (re-exporting a `__main__`-run submodule
# triggers a runpy double-import warning). Import it directly:
#   from tooling.superversion.eval import value_gate

__all__ = [
    "FormulaError", "recompute",
    "ReferenceDataset", "ExpectedKpi", "Expectations",
    "available_datasets", "available_use_cases", "load_dataset", "load_expectations",
]
