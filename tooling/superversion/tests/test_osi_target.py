"""I-7.1 — OSI target emits a valid OSI Core document from the canonical model.

DoD: OSI-jsonschema-validate grün. Validates the emitted document against the
official upstream OSI JSON Schema vendored at `targets/schemas/osi-schema.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import base
from tooling.superversion.targets import osi  # noqa: F401 — registers "osi"

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
SCHEMA = Path(__file__).resolve().parents[1] / "targets" / "schemas" / "osi-schema.json"


def _emit_doc():
    model = from_bracket_file(COM001, KPIS)
    emitted = base.get("osi").emit(model)
    assert len(emitted) == 1
    return json.loads(next(iter(emitted.values())))


def test_osi_registered():
    assert "osi" in base.available()
    assert base.get("osi").status == "live"


def test_osi_validates_against_official_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    doc = _emit_doc()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    assert not errors, "OSI doc failed schema validation:\n" + "\n".join(
        f"  {list(e.path)}: {e.message}" for e in errors
    )


def test_osi_structure():
    doc = _emit_doc()
    assert doc["version"] == "0.2.0.dev0"
    assert isinstance(doc["semantic_model"], list) and len(doc["semantic_model"]) == 1
    sm = doc["semantic_model"][0]
    assert sm["name"] and len(sm["datasets"]) >= 1
    # COM-001 has measures → at least one metric, each with a dialect expression.
    assert sm.get("metrics"), "expected metrics from the use case's measures"
    for m in sm["metrics"]:
        assert m["expression"]["dialects"][0]["dialect"] in {
            "ANSI_SQL", "SNOWFLAKE", "MDX", "TABLEAU", "DATABRICKS", "MAQL",
        }
    for ds in sm["datasets"]:
        assert ds["name"] and ds["source"]


def test_osi_deterministic():
    assert base.get("osi").emit(from_bracket_file(COM001, KPIS)) == \
        base.get("osi").emit(from_bracket_file(COM001, KPIS))
