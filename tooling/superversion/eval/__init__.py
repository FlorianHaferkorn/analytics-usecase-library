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

__all__ = [
    "FormulaError", "recompute",
    "ReferenceDataset", "ExpectedKpi", "Expectations",
    "available_datasets", "available_use_cases", "load_dataset", "load_expectations",
]
