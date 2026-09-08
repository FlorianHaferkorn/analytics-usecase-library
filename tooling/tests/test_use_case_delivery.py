from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from tooling.superversion.project_package.use_case_delivery import (
    render_delivery_document,
    validate_delivery_document,
)
from tooling.superversion.project_package.validator import SCHEMA_BY_MODULE


REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "tooling" / "generator" / "schemas" / "project_use_case_delivery.schema.json"
FIXTURE_PATH = REPO / "core" / "fixtures" / "neutral" / "use-case-delivery-spec" / "use_case_delivery.yaml"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_delivery_schema_and_neutral_fixture_are_valid() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert validate_delivery_document(_fixture(), schema) == []
    assert SCHEMA_BY_MODULE["use_case_delivery"] == "project_use_case_delivery.schema.json"


def test_renderer_emits_complete_standard_sections() -> None:
    outputs = render_delivery_document(_fixture())
    assert list(outputs) == ["uc_revenue_demo_Use_Case_and_Data_Architecture.md"]
    document = next(iter(outputs.values()))
    for heading in (
        "## 1. Purpose and evidence rules",
        "## 2. Decision and report scope",
        "## 3. Source boundary",
        "## 4. Target data products",
        "## 5. Analytical model design",
        "## 6. Transformation design",
        "## 7. Orchestration and operations",
        "## 8. Security, quality, release and operational controls",
        "## 9. Acceptance and regression",
        "## 10. Open gates",
    ):
        assert heading in document
    assert "customer decisions" in document
    assert "Extract fallback does not close this gate" in document


def test_measured_claim_requires_evidence() -> None:
    document = deepcopy(_fixture())
    document["use_cases"][0]["source_contract"]["fallback"][0]["status"]["evidence_refs"] = []
    errors = validate_delivery_document(document, _schema())
    assert any("evidence_refs" in error and "non-empty" in error for error in errors)


def test_unresolved_lineage_reference_is_rejected() -> None:
    document = deepcopy(_fixture())
    document["use_cases"][0]["transformations"][0]["output_refs"] = ["missing_product"]
    errors = validate_delivery_document(document, _schema())
    assert any("unresolved object ref 'missing_product'" in error for error in errors)


def test_delivery_state_cannot_overrun_an_open_gate() -> None:
    document = deepcopy(_fixture())
    document["use_cases"][0]["delivery_state"] = "verified"
    errors = validate_delivery_document(document, _schema())
    assert any("conflicts with open gate 'gate_live_source'" in error for error in errors)


def test_relationship_assessment_requires_resolvable_data_products() -> None:
    document = deepcopy(_fixture())
    document["use_cases"][0]["analytical_design"]["relationship_assessments"][0]["subject_refs"] = [
        "missing_product"
    ]
    errors = validate_delivery_document(document, _schema())
    assert any("unresolved data-product ref 'missing_product'" in error for error in errors)


def test_weighted_relationship_rejects_uncontrolled_bridge_navigation() -> None:
    document = deepcopy(_fixture())
    assessment = document["use_cases"][0]["analytical_design"]["relationship_assessments"][0]
    assessment["carries_weight"] = True
    assessment["bridge_decision"] = "required"
    assessment["fact_filter_strategy"] = "bridge_only_navigation"
    errors = validate_delivery_document(document, _schema())
    assert any("must use an allocation-fact, measure-logic or open strategy" in error for error in errors)
