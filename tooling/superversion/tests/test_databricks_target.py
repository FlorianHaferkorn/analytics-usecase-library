"""I-7.2 — Databricks Metric View target emits valid metric-view YAML.

Second semantic-layer stack (Tool-Agnostik-Beweis). Validates the emitted YAML
against the docs-derived JSON Schema (ALUCA-authored from the official Databricks
YAML reference). The vendor's own validator (a Databricks workspace) is the
production gate and is out of scope offline (Ehrlichkeit v3) — see databricks.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base
from tooling.superversion.targets import databricks  # noqa: F401 — registers "databricks"

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
SCHEMA = Path(__file__).resolve().parents[1] / "targets" / "schemas" / "databricks_metricview.schema.json"


def _emit():
    model = from_bracket_file(COM001, KPIS)
    return base.get("databricks").emit(model)


def test_databricks_registered_beta():
    assert "databricks" in base.available()
    # beta: local gate is docs-derived; the vendor workspace validator is geplant.
    assert base.get("databricks").status == "beta"


def test_metricview_validates_against_docs_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    emitted = _emit()
    assert emitted, "expected at least one metric view"
    for path, text in emitted.items():
        doc = yaml.safe_load(text)
        errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
        assert not errors, f"{path} failed schema validation:\n" + "\n".join(
            f"  {list(e.path)}: {e.message}" for e in errors
        )


def test_metricview_structure():
    emitted = _emit()
    # COM-001 has a fact table with measures → exactly one metric view, with measures.
    assert len(emitted) >= 1
    doc = yaml.safe_load(next(iter(emitted.values())))
    assert doc["version"] == "1.1"
    assert doc["source"]
    assert doc.get("measures"), "expected measures from the use case"
    for m in doc["measures"]:
        assert m["name"] and m["expr"]


def test_databricks_deterministic():
    assert _emit() == _emit()
