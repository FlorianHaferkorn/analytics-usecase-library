from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion.project_package.capability_state import evaluate_capability, render_questionnaire
from tooling.superversion.project_package.validator import SCHEMA_BY_MODULE, _validate_capability_state


REPO = Path(__file__).resolve().parents[2]
PACK_PATH = REPO / "core" / "capabilities" / "fabric-data-delivery-assurance" / "capability.yaml"
SCHEMA_PATH = REPO / "tooling" / "generator" / "schemas" / "project_capability_state.schema.json"


def _pack() -> dict:
    return yaml.safe_load(PACK_PATH.read_text(encoding="utf-8"))


def _evidence(provenance: str = "derived") -> dict:
    return {
        "provenance": provenance,
        "evidence_refs": ["evidence/neutral-fixture"],
        "measured_at": "2026-01-01T00:00:00Z" if provenance == "measured" else None,
        "decision_ref": "decision_neutral_fixture" if provenance == "customer_decision" else None,
        "note": "Synthetic neutral fixture only.",
    }


def _state() -> dict:
    pack = _pack()["capability"]
    facts = {
        "target_platform": "microsoft_fabric",
        "recurring_data_delivery": True,
        "operating_responsibility_required": True,
        "reliable_change_feed_available": False,
        "full_snapshot_within_window": False,
        "transformation_requires_procedural_state": False,
        "product_requires_trusted_publication": True,
    }
    return {
        "id": "assurance_operated_product",
        "capability_ref": pack["id"],
        "capability_version": pack["version"],
        "scope_level": "operate",
        "facts": [
            {"id": key, "value": value, "evidence": _evidence("measured")}
            for key, value in facts.items()
        ],
        "answers": [
            {
                "question_ref": question["id"],
                "state": "answered",
                "response": "Resolved by the governed project contract.",
                "owner_ref": "role_accountable_owner",
                "due_date": None,
                "evidence": _evidence(),
            }
            for question in pack["questions"]
        ],
    }


def test_capability_state_schema_and_mapping_are_valid() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    document = {"schema_version": "1.0.0", "project_ref": "project_demo", "capabilities": [_state()]}
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    assert _validate_capability_state(document, "capability_state.yaml") == []
    assert SCHEMA_BY_MODULE["capability_state"] == "project_capability_state.schema.json"


def test_engine_derives_adaptive_questions_and_recommendations_without_approving_them() -> None:
    result = evaluate_capability(_pack(), _state())
    assert result["questionnaire_complete"] is True
    assert result["build_input_ready"] is True
    options = {item["option_ref"] for item in result["recommendations"]}
    assert options == {
        "watermark_with_reconciliation",
        "declarative_sql",
        "fail_closed_with_quarantine",
        "composite_product_health",
    }
    assert all(item["status"] == "recommendation_not_approval" for item in result["recommendations"])
    rendered = render_questionnaire(result)
    assert "Which failure classes are retryable" in rendered
    assert "Questionnaire complete: `yes`" in rendered


def test_missing_applicability_fact_and_proposed_answer_block_operated_input() -> None:
    state = _state()
    state["facts"] = [item for item in state["facts"] if item["id"] != "recurring_data_delivery"]
    answer = next(item for item in state["answers"] if item["question_ref"] == "q_alert_routes")
    answer["evidence"] = _evidence("proposed")
    result = evaluate_capability(_pack(), state)
    assert result["questionnaire_complete"] is False
    assert result["build_input_ready"] is False
    assert "q_change_semantics:applicability_fact_missing" in result["blockers"]
    assert "q_alert_routes:proposed_answer_not_sufficient" in result["blockers"]


def test_provenance_contract_prevents_false_measurement_and_decision_claims() -> None:
    document = {"schema_version": "1.0.0", "project_ref": "project_demo", "capabilities": [_state()]}
    fact = document["capabilities"][0]["facts"][0]
    fact["evidence"]["evidence_refs"] = []
    fact["evidence"]["measured_at"] = None
    answer = document["capabilities"][0]["answers"][0]
    answer["evidence"] = _evidence("customer_decision")
    answer["evidence"]["decision_ref"] = None
    errors = _validate_capability_state(document, "capability_state.yaml")
    assert any("marked measured requires evidence_refs and measured_at" in error for error in errors)
    assert any("marked customer_decision requires evidence_refs and decision_ref" in error for error in errors)


def test_unknown_question_answer_is_rejected() -> None:
    state = deepcopy(_state())
    state["answers"][0]["question_ref"] = "q_unknown"
    try:
        evaluate_capability(_pack(), state)
    except ValueError as error:
        assert "unknown question refs" in str(error)
    else:
        raise AssertionError("unknown question answer was accepted")
