from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion.project_package.adr import main as render_adr_main, render_adr_register
from tooling.superversion.project_package.delivery_quality import assess_delivery_quality, render_assessment
from tooling.superversion.project_package.compiler_input import build_compiler_input
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.validator import _validate_identity_access, validate_project_package


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling" / "generator" / "schemas"
LEGACY = ROOT / "tooling" / "tests" / "fixtures" / "project_package" / "v1"
MODEL = ROOT / "core" / "reference_models" / "e2e_delivery_quality" / "model.yaml"
IDENTITY = ROOT / "core" / "fixtures" / "neutral" / "project-identity-access" / "identity_access.yaml"
MAINTENANCE = ROOT / "core" / "fixtures" / "neutral" / "project-architecture-maintenance" / "architecture_maintenance.yaml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else yaml.safe_load(path.read_text(encoding="utf-8"))


def test_reference_model_and_identity_contract_are_closed_and_valid() -> None:
    model_schema = _load(SCHEMAS / "delivery_quality_model.schema.json")
    identity_schema = _load(SCHEMAS / "project_identity_access.schema.json")
    Draft202012Validator.check_schema(model_schema)
    Draft202012Validator.check_schema(identity_schema)
    Draft202012Validator(model_schema, format_checker=FormatChecker()).validate(_load(MODEL))
    identity = _load(IDENTITY)
    Draft202012Validator(identity_schema, format_checker=FormatChecker()).validate(identity)
    assert _validate_identity_access(identity, "identity_access.yaml") == []


def test_architecture_maintenance_contract_is_closed_and_valid() -> None:
    schema = _load(SCHEMAS / "project_architecture_maintenance.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(_load(MAINTENANCE))


def test_verified_architecture_transition_requires_retained_evidence(tmp_path: Path) -> None:
    package = migrate_project_package(LEGACY, tmp_path / "package", SCHEMAS)
    manifest = _load(package / "package.yaml")
    maintenance = _load(MAINTENANCE)
    maintenance["transitions"][0]["state"] = "cutover_verified"
    path = package / "governance" / "architecture_maintenance.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(maintenance, sort_keys=False), encoding="utf-8")
    manifest["modules"].append({
        "module_type": "architecture_maintenance", "path": "governance/architecture_maintenance.yaml",
        "schema_id": _load(SCHEMAS / "project_architecture_maintenance.schema.json")["$id"],
        "sha256": canonical_sha256(maintenance),
    })
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    errors = validate_project_package(package, SCHEMAS)
    assert any("cutover_verified' requires evidence_refs" in error for error in errors)


def test_architecture_maintenance_rejects_ineffective_reconciliation_and_noop_transition(tmp_path: Path) -> None:
    package = migrate_project_package(LEGACY, tmp_path / "package", SCHEMAS)
    manifest = _load(package / "package.yaml")
    maintenance = _load(MAINTENANCE)
    maintenance["reconciliation"]["observed_state_max_age_hours"] = 24
    maintenance["transitions"][0]["target_ref"] = maintenance["transitions"][0]["current_ref"]
    path = package / "governance" / "architecture_maintenance.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(maintenance, sort_keys=False), encoding="utf-8")
    manifest["modules"].append({
        "module_type": "architecture_maintenance", "path": "governance/architecture_maintenance.yaml",
        "schema_id": _load(SCHEMAS / "project_architecture_maintenance.schema.json")["$id"],
        "sha256": canonical_sha256(maintenance),
    })
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    errors = validate_project_package(package, SCHEMAS)
    assert any("maximum age must cover at least one reconciliation cadence" in error for error in errors)
    assert any("must change the architecture reference" in error for error in errors)


def test_identity_contract_rejects_unapproved_personal_access_and_unproven_apply() -> None:
    identity = _load(IDENTITY)
    identity["accounts"].append({
        "id": "consultant", "display_name_pattern": "person@example.invalid", "principal_type": "human",
        "purpose": "Temporary support", "owner_ref": "role_platform_owner", "environments": ["prod"],
        "credential": {"authentication": "interactive_mfa", "secret_store_ref": None, "rotation_days": None},
        "lifecycle_state": "provisioned", "evidence_refs": [],
    })
    identity["role_assignments"].append({
        "id": "personal_prod_admin", "subject_ref": "consultant", "subject_kind": "account",
        "target_ref": "scope:prod", "role": "administrator", "environments": ["prod"],
        "assignment_mode": "group_based", "justification": "Temporary", "state": "applied",
        "approver_ref": "role_platform_owner", "decision_ref": None, "evidence_refs": [],
    })
    errors = _validate_identity_access(identity, "identity_access.yaml")
    assert any("documented direct_exception" in error for error in errors)
    assert any("requires evidence_refs" in error for error in errors)


def test_assessment_compares_strengths_but_uses_fail_closed_gates(tmp_path: Path) -> None:
    package = migrate_project_package(LEGACY, tmp_path / "package", SCHEMAS)
    manifest = _load(package / "package.yaml")
    identity = _load(IDENTITY)
    path = package / "governance" / "identity_access.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(identity, sort_keys=False), encoding="utf-8")
    manifest["state"] = "approved"
    manifest["modules"].append({
        "module_type": "identity_access", "path": "governance/identity_access.yaml",
        "schema_id": _load(SCHEMAS / "project_identity_access.schema.json")["$id"],
        "sha256": canonical_sha256(identity),
    })
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    assert validate_project_package(package, SCHEMAS) == []
    compiler = build_compiler_input(package, SCHEMAS)
    Draft202012Validator(
        _load(SCHEMAS / "project_compiler_input.schema.json"), format_checker=FormatChecker()
    ).validate(compiler)
    assert compiler["modules"]["identity_access"] == identity
    result = assess_delivery_quality(package, SCHEMAS, _load(MODEL))
    assert result["weighted_score"] > 0
    assert result["gates"]["build_ready"]["ready"] is False
    assert result["gates"]["apply_ready"]["ready"] is False
    identity_dimension = next(item for item in result["dimensions"] if item["id"] == "identity_access")
    assert identity_dimension["score"] == 100
    assert "evidenced_adr_flow" in result["gates"]["build_ready"]["blockers"]
    assert "Diagnostic comparison only" in render_assessment(result)


def test_architecture_lifecycle_requires_current_review_and_observed_state(tmp_path: Path) -> None:
    package = migrate_project_package(LEGACY, tmp_path / "package", SCHEMAS)
    manifest = _load(package / "package.yaml")
    maintenance = _load(MAINTENANCE)
    path = package / "governance" / "architecture_maintenance.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(maintenance, sort_keys=False), encoding="utf-8")
    manifest["modules"].append({
        "module_type": "architecture_maintenance", "path": "governance/architecture_maintenance.yaml",
        "schema_id": _load(SCHEMAS / "project_architecture_maintenance.schema.json")["$id"],
        "sha256": canonical_sha256(maintenance),
    })
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    now = datetime(2026, 9, 22, 12, tzinfo=timezone.utc)
    result = assess_delivery_quality(package, SCHEMAS, _load(MODEL), now=now)
    lifecycle = next(item for item in result["dimensions"] if item["id"] == "architecture_lifecycle")
    assert lifecycle["score"] == 100
    assert result["reference_review"]["current"] is True
    assert build_compiler_input(package, SCHEMAS)["modules"]["architecture_maintenance"] == maintenance

    maintenance["technology_watch"][0]["reviewed_at"] = "2025-01-01T00:00:00Z"
    path.write_text(yaml.safe_dump(maintenance, sort_keys=False), encoding="utf-8")
    manifest["modules"][-1]["sha256"] = canonical_sha256(maintenance)
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    stale = assess_delivery_quality(package, SCHEMAS, _load(MODEL), now=now)
    lifecycle = next(item for item in stale["dimensions"] if item["id"] == "architecture_lifecycle")
    assert lifecycle["score"] == 0
    assert "technology review microsoft_fabric is overdue" in lifecycle["controls"][0]["evidence"]

    maintenance = _load(MAINTENANCE)
    maintenance["reconciliation"]["last_result"] = "drift"
    maintenance["reconciliation"]["drift_refs"] = ["drift://workspace/unmanaged-item"]
    path.write_text(yaml.safe_dump(maintenance, sort_keys=False), encoding="utf-8")
    manifest["modules"][-1]["sha256"] = canonical_sha256(maintenance)
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    drift = assess_delivery_quality(package, SCHEMAS, _load(MODEL), now=now)
    lifecycle = next(item for item in drift["dimensions"] if item["id"] == "architecture_lifecycle")
    assert lifecycle["score"] == 0
    assert "unresolved architecture drift blocks release" in lifecycle["controls"][0]["evidence"]


def test_reference_source_freshness_is_reported_without_overriding_project_gates(tmp_path: Path) -> None:
    package = migrate_project_package(LEGACY, tmp_path / "package", SCHEMAS)
    model = _load(MODEL)
    model["dimensions"][0]["controls"][0]["source"]["reviewed_at"] = "2025-01-01T00:00:00Z"
    result = assess_delivery_quality(
        package, SCHEMAS, model, now=datetime(2026, 9, 22, 12, tzinfo=timezone.utc)
    )
    assert result["reference_review"]["current"] is False
    assert "governed_capability_intake" in result["reference_review"]["overdue_controls"]
    assert "Reference-source review: `overdue`" in render_assessment(result)


def test_adr_register_is_derived_from_decision_set_and_keeps_approval_evidence() -> None:
    decision_set = {
        "definitions": [{
            "id": "deployment_model", "title": "Deployment model", "question": {"technical_text": "How is delivery promoted?"},
            "recommendation": {"text": "Use controlled promotion."}, "decider": {"text": "Platform owner"},
            "consequence_if_unresolved": "Production release remains blocked.",
            "options": [{"id": "controlled", "label": "Controlled promotion", "kind": "proposal"}], "option_details": [],
            "adr": {"record_id": "ADR-0001", "context": "Three isolated environments are required.", "decision_drivers": ["separation"], "affected_artifact_refs": ["architecture"]},
        }],
        "instances": [{
            "id": "deployment_model_instance", "definition_ref": "deployment_model",
            "selection": {"state": "confirmed", "option_ref": "controlled", "custom_value": None},
            "approval": {"state": "approved", "decided_by": "role_platform_owner", "rationale": "Controlled release.", "decided_at": "2026-09-22T10:00:00Z", "evidence_refs": ["evidence://meeting/minutes"], "approval_flow_ref": "flow:architecture_decision"},
        }],
    }
    rendered = render_adr_register(deepcopy(decision_set))
    assert "ADR-0001 · Deployment model" in rendered
    assert "**Status:** Accepted" in rendered
    assert "evidence://meeting/minutes" in rendered


def test_adr_register_cli_writes_a_shareable_document(tmp_path: Path) -> None:
    source = tmp_path / "decisions.yaml"
    output = tmp_path / "architecture-decision-register.md"
    source.write_text(yaml.safe_dump({
        "definitions": [{
            "id": "environment_model", "title": "Environment model",
            "question": {"technical_text": "Which environments are required?"},
            "recommendation": {"text": "Use Dev, Test and Prod."},
            "decider": {"text": "Platform owner"},
            "consequence_if_unresolved": "Provisioning remains blocked.",
            "options": [{"id": "three_stage", "label": "Dev, Test and Prod", "kind": "proposal"}],
            "option_details": [],
            "adr": {"record_id": "ADR-0002", "context": "Controlled promotion is required.", "decision_drivers": ["risk"], "affected_artifact_refs": ["architecture"]},
        }],
        "instances": [{
            "id": "environment_model_instance", "definition_ref": "environment_model",
            "selection": {"state": "confirmed", "option_ref": "three_stage", "custom_value": None},
            "approval": {"state": "approved", "decided_by": "role_platform_owner", "rationale": "Release isolation.", "decided_at": "2026-09-22T10:00:00Z", "evidence_refs": ["evidence://meeting/minutes"], "approval_flow_ref": "flow:architecture_decision"},
        }],
    }, sort_keys=False), encoding="utf-8", newline="\n")
    assert render_adr_main(["--decision-set", str(source), "--output", str(output)]) == 0
    assert "ADR-0002 · Environment model" in output.read_text(encoding="utf-8")
