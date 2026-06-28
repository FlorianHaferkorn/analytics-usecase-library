"""I-7.3 — Stack-Indifferenz-Test (Cross-Target-Equivalence).

The litmus for the Tool-Agnostik-Beweis (§7 Synergy): ONE governed core → N targets,
KPI meaning identical across them. Mechanically: the exact set of KPI/measure names the
canonical model carries must appear — no more, no less — in every measure-bearing target
(TMDL / OSI / Databricks). No target may invent, drop, or rename a KPI.

KPI *meaning* is anchored by the governed name (Golden Thread): same name ⇒ same KPI.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base
from tooling.superversion.targets import osi  # noqa: F401 — registers "osi"
from tooling.superversion.targets import databricks  # noqa: F401 — registers "databricks"
from tooling.superversion.targets import tmdl  # noqa: F401 — registers "tmdl"

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
BRACKETS = sorted((REPO / "core/usecases/core").glob("*/UseCase_Bracket.yaml"))

_TMDL_MEASURE = re.compile(r"measure '([^']+)' =")


def _canonical_measure_names(model) -> set[str]:
    return {m.name for t in model.semantic.tables for m in t.measures}


def _tmdl_measure_names(model) -> set[str]:
    names: set[str] = set()
    for text in base.get("tmdl").emit(model).values():
        names.update(_TMDL_MEASURE.findall(text))
    return names


def _osi_metric_names(model) -> set[str]:
    names: set[str] = set()
    for text in base.get("osi").emit(model).values():
        doc = json.loads(text)
        for sm in doc["semantic_model"]:
            names.update(m["name"] for m in sm.get("metrics", []))
    return names


def _databricks_measure_names(model) -> set[str]:
    names: set[str] = set()
    for text in base.get("databricks").emit(model).values():
        doc = yaml.safe_load(text)
        names.update(m["name"] for m in doc.get("measures", []))
    return names


@pytest.mark.parametrize("bracket", BRACKETS, ids=lambda p: p.parent.name)
def test_kpi_set_identical_across_targets(bracket):
    model = from_bracket_file(bracket, KPIS)
    canonical = _canonical_measure_names(model)
    if not canonical:
        pytest.skip("use case has no measures")

    tmdl_names = _tmdl_measure_names(model)
    osi_names = _osi_metric_names(model)
    dbx_names = _databricks_measure_names(model)

    # Every target carries exactly the canonical KPI set — no invent, drop, or rename.
    assert tmdl_names == canonical, f"TMDL diverges: {tmdl_names ^ canonical}"
    assert osi_names == canonical, f"OSI diverges: {osi_names ^ canonical}"
    assert dbx_names == canonical, f"Databricks diverges: {dbx_names ^ canonical}"
    # Transitively the three targets agree with each other.
    assert tmdl_names == osi_names == dbx_names


def test_at_least_one_use_case_covered():
    # Guard against the glob silently matching nothing (would make the suite vacuously green).
    assert BRACKETS, "no UseCase_Bracket.yaml found — cross-target test would be vacuous"
