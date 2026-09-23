from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion.project_package.use_case_delivery import (
    render_delivery_document,
    validate_delivery_document,
)
from tooling.superversion.project_package.validator import SCHEMA_BY_MODULE


REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "tooling" / "generator" / "schemas" / "project_use_case_delivery.schema.json"
FIXTURE_PATH = REPO / "core" / "fixtures" / "neutral" / "use-case-delivery-spec" / "use_case_delivery.yaml"
OBSERVED_SCHEMA_PATH = REPO / "tooling" / "generator" / "schemas" / "project_observed_state.schema.json"
OBSERVED_FIXTURE_PATH = (
    REPO / "core" / "fixtures" / "neutral" / "use-case-delivery-spec" / "observed_state.dev.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_delivery_schema_and_neutral_fixture_are_valid() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert validate_delivery_document(_fixture(), schema) == []
    assert SCHEMA_BY_MODULE["use_case_delivery"] == "project_use_case_delivery.schema.json"
    observed_schema = json.loads(OBSERVED_SCHEMA_PATH.read_text(encoding="utf-8"))
    observed = json.loads(OBSERVED_FIXTURE_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(observed_schema)
    Draft202012Validator(observed_schema, format_checker=FormatChecker()).validate(observed)


def test_platform_contract_fields_are_backward_compatible_when_absent() -> None:
    document = deepcopy(_fixture())
    document.pop("platform_dependencies")
    for use_case in document["use_cases"]:
        use_case.pop("platform_dependency_refs")
        for boundary in use_case["source_contract"].values():
            for source in boundary:
                source.pop("connection_ref", None)
        for product in use_case["data_products"]:
            product.pop("target_ref", None)
    assert validate_delivery_document(document, _schema()) == []


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
        "## 8. Delivery assurance",
        "## 9. Security, quality, release and operational controls",
        "## 10. Acceptance and regression",
        "## 11. Open gates",
    ):
        assert heading in document
    assert "customer decisions" in document
    assert "Extract fallback does not close this gate" in document
    assert "gateway_enterprise_dev" in document
    assert "connection_enterprise_erp" in document
    assert "signal_quality_failure" in document
    assert "readback_before_retry" in document


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


def test_duplicate_platform_logical_ref_is_rejected_as_ambiguous() -> None:
    document = deepcopy(_fixture())
    document["platform_dependencies"]["connections"][0]["id"] = "gateway_enterprise_dev"
    errors = validate_delivery_document(document, _schema())
    assert any("ambiguous or duplicate logical ref 'gateway_enterprise_dev'" in error for error in errors)


def test_platform_source_and_data_product_refs_must_be_wired() -> None:
    document = deepcopy(_fixture())
    source = document["use_cases"][0]["source_contract"]["canonical"][0]
    source["connection_ref"] = "connection_missing"
    document["use_cases"][0]["data_products"][0].pop("target_ref")
    errors = validate_delivery_document(document, _schema())
    assert any("unresolved connection_ref 'connection_missing'" in error for error in errors)
    assert any("data product 'bronze_sales_month' requires target_ref" in error for error in errors)


def test_design_ready_requires_delivery_assurance() -> None:
    document = deepcopy(_fixture())
    use_case = document["use_cases"][0]
    use_case["delivery_state"] = "design_ready"
    use_case.pop("delivery_assurance")
    errors = validate_delivery_document(document, _schema())
    assert any("delivery_assurance is required" in error for error in errors)


def test_incremental_mode_requires_cursor_and_reconciliation() -> None:
    document = deepcopy(_fixture())
    source = document["use_cases"][0]["delivery_assurance"]["source_behavior"]
    source["incremental_mode"] = "delta_cdf"
    source["cursor_field"] = None
    source["reconciliation_cadence"] = None
    errors = validate_delivery_document(document, _schema())
    assert any("requires cursor_field" in error for error in errors)
    assert any("requires reconciliation_cadence" in error for error in errors)


def test_build_ready_rejects_false_green_assurance() -> None:
    document = deepcopy(_fixture())
    use_case = document["use_cases"][0]
    use_case["delivery_state"] = "build_ready"
    assurance = use_case["delivery_assurance"]
    assurance["source_behavior"]["incremental_mode"] = "open"
    assurance["data_quality"]["rules"][0]["severity"] = "warn"
    assurance["data_quality"]["rules"][1]["severity"] = "observe"
    assurance["observability"]["signals"] = assurance["observability"]["signals"][:1]
    assurance["reliability"]["retry_policy"] = assurance["reliability"]["retry_policy"][:1]
    errors = validate_delivery_document(document, _schema())
    assert any("requires selected incremental" in error for error in errors)
    assert any("requires at least one blocking" in error for error in errors)
    assert any("misses monitoring signal types" in error for error in errors)
    assert any("misses failure classes" in error for error in errors)


def test_non_retryable_failure_classes_and_uncertain_outcomes_fail_closed() -> None:
    document = deepcopy(_fixture())
    use_case = document["use_cases"][0]
    use_case["delivery_state"] = "build_ready"
    rules = use_case["delivery_assurance"]["reliability"]["retry_policy"]
    next(rule for rule in rules if rule["failure_class"] == "schema")["action"] = "retry"
    next(rule for rule in rules if rule["failure_class"] == "schema")["max_attempts"] = 2
    next(rule for rule in rules if rule["failure_class"] == "unknown")["action"] = "stop"
    errors = validate_delivery_document(document, _schema())
    assert any("non-retryable failure class 'schema' must stop" in error for error in errors)
    assert any("unknown mutation outcomes must reconcile" in error for error in errors)
