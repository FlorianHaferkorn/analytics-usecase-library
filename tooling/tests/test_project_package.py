from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion._dataarch_vendor import load_emitters
from tooling.superversion.project_package.adapters.decision_proposals import (
    FIELD_MAPPING,
    SOURCE_FIELDS,
    adapt_decision_proposals,
)
from tooling.superversion.project_package.artifact_lifecycle import (
    ArtifactLifecycleError,
    build_publication_manifest,
    render_artifact_index,
)
from tooling.superversion.project_package.compiler_input import build_compiler_input
from tooling.superversion.project_package.cli import main as project_package_cli
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import (
    ProjectPackageMigrationError,
    migrate_project_package,
)
from tooling.superversion.project_package.use_case_delivery import validate_delivery_document, render_use_case
from tooling.superversion.project_package.validator import validate_project_package


REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "tooling" / "generator" / "schemas"
PROJECT_SCHEMAS = sorted(SCHEMAS.glob("project_*.schema.json"))
LEGACY_FIXTURE = REPO / "tooling" / "tests" / "fixtures" / "project_package" / "v1"
ARTIFACT_FIXTURE = REPO / "core" / "fixtures" / "neutral" / "project-package-artifact-lifecycle"
USE_CASE_DELIVERY_FIXTURE = REPO / "core" / "fixtures" / "neutral" / "use-case-delivery-spec" / "use_case_delivery.yaml"
OBSERVED_RUNTIME_FIXTURE = (
    REPO / "core" / "fixtures" / "neutral" / "use-case-delivery-spec" / "observed_state.dev.json"
)


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _proposal(**overrides: object) -> dict:
    base = {
        "id": "SEC-RLS",
        "topic": "Row-level security",
        "gap": "Which scope controls row access?",
        "proposal": "Use the approved organisation scope.",
        "derived_from": "governed organisation columns",
        "confidence": "hoch",
        "status": "vorbelegt",
        "alternatives": ["Use a project scope"],
        "optionen": [],
        "decider": "Data Owner",
        "if_undecided": "Build remains blocked.",
        "ermittlung": {"wo": "Policy", "wen": "Data Owner", "wenn_unklar": "Escalate"},
        "kunde": {"frage": "Who may see what?", "folge": "Controls access.", "warum": "Required."},
        "faelligkeit": "vor Produktivsetzung",
        "markers": ["SECURITY_SCOPE"],
    }
    base.update(overrides)
    return base


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _minimal_modules(root: Path) -> list[dict]:
    zero_hash = "0" * 64
    documents = {
        "opportunity/opportunity.yaml": (
            "opportunity",
            {
                "schema_version": "2.0.0",
                "opportunity_id": "opp_demo",
                "customer_ref": "customer_demo",
                "objectives": ["Prove the governed delivery path"],
                "scope_status": "qualified",
            },
            None,
        ),
        "commercial/commercial.yaml": (
            "commercial",
            {
                "schema_version": "2.0.0",
                "status": "assumption",
                "authority_ref": "env:PREIS_KANON_MANDANTEN_DIR/preis_kanon.yaml",
                "currency": "EUR",
                "estimate": {"value": None, "basis_refs": []},
                "price_values_embedded": False,
            },
            None,
        ),
        "plan/plan.yaml": (
            "plan",
            {"schema_version": "2.0.0", "work_packages": [], "dependencies": []},
            None,
        ),
        "observed/dev.json": (
            "observed_state",
            {
                "schema_version": "2.0.0",
                "environment": "dev",
                "collection_state": "collected",
                "captured_at": "2026-09-04T09:00:00Z",
                "collector": "fixture",
                "resources": [
                    {
                        "logical_id": "workspace_dev",
                        "resource_type": "workspace",
                        "physical_id": "fixture-workspace",
                        "state_hash": zero_hash,
                    }
                ],
            },
            "dev",
        ),
        "discovery/decision_set.yaml": (
            "decision_set",
            adapt_decision_proposals([_proposal()]),
            None,
        ),
    }
    modules = []
    for relative, (module_type, document, environment) in documents.items():
        path = root / relative
        if path.suffix == ".json":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        else:
            _write_yaml(path, document)
        schema_id = _load_schema(f"project_{module_type}.schema.json")["$id"]
        module = {
            "module_type": module_type,
            "path": relative,
            "schema_id": schema_id,
            "sha256": canonical_sha256(document),
        }
        if environment is not None:
            module["environment"] = environment
        modules.append(module)
    return modules


def _artifact_registry() -> dict:
    return yaml.safe_load(
        (ARTIFACT_FIXTURE / "artifacts" / "index.yaml").read_text(encoding="utf-8")
    )


def _add_artifact_registry(root: Path, modules: list[dict], registry: dict) -> None:
    relative = "artifacts/index.yaml"
    _write_yaml(root / relative, registry)
    modules.append(
        {
            "module_type": "artifact_registry",
            "path": relative,
            "schema_id": _load_schema("project_artifact_registry.schema.json")["$id"],
            "sha256": canonical_sha256(registry),
        }
    )


def _add_use_case_delivery(root: Path, modules: list[dict]) -> dict:
    document = yaml.safe_load(USE_CASE_DELIVERY_FIXTURE.read_text(encoding="utf-8"))
    relative = "delivery/use_case_delivery.yaml"
    _write_yaml(root / relative, document)
    modules.append(
        {
            "module_type": "use_case_delivery",
            "path": relative,
            "schema_id": _load_schema("project_use_case_delivery.schema.json")["$id"],
            "sha256": canonical_sha256(document),
        }
    )
    return document


def _ai_policy_document(decision_ref: str) -> dict:
    return {
        "schema_version": "1.0.0",
        "contract_version": "ai-data-handling-policy/1.0.0",
        "project_ref": "project_demo",
        "routes": [{
            "id": "discovery_public",
            "task_role": "source-discovery",
            "decision_ref": decision_ref,
            "profile": {"provider": "anthropic", "data_handling": {
                "processing_boundary": "external_cloud",
                "allowed_classifications": ["public"],
                "allowed_data_forms": ["metadata"],
                "allowed_purposes": ["studio_authoring"],
                "provider_training_allowed": False,
                "prompt_retention_days": 0,
                "require_redaction_for_egress": True,
            }},
            "allowed_inputs": [{"classification": "public", "data_form": "metadata",
                                "purpose": "studio_authoring", "source_refs": ["fixture://public-source"]}],
            "provider_region": "eu-west",
            "provider_geography": "eu",
            "credential_ref": "secret://studio/anthropic",
            "provider_terms_evidence_refs": ["fixture://provider-terms"],
            "expires_at": "2030-01-01T00:00:00Z",
        }],
    }


def _add_ai_policy(root: Path, modules: list[dict], document: dict) -> None:
    relative = "governance/ai_data_handling.yaml"
    _write_yaml(root / relative, document)
    modules.append({
        "module_type": "ai_data_handling",
        "path": relative,
        "schema_id": _load_schema("project_ai_data_handling.schema.json")["$id"],
        "sha256": canonical_sha256(document),
    })


def _scope_ai_decision(root: Path, modules: list[dict]) -> dict:
    path = root / "discovery/decision_set.yaml"
    decisions = yaml.safe_load(path.read_text(encoding="utf-8"))
    definition = decisions["definitions"][0]
    definition["title"] = "AI data handling for Discovery"
    definition["source"] = {"adapter": "project_ai_policy", "raw_id": "ai_policy",
                            "source_ref": "fixture://ai-policy", "source_hash": "a" * 64}
    definition["adr"] = {"record_id": "ADR-9001", "context": "Discovery AI data boundary",
                         "decision_drivers": ["Customer content protection"],
                         "affected_artifact_refs": ["discovery_public"]}
    decisions["instances"][0]["scope_refs"] = ["discovery_public"]
    _write_yaml(path, decisions)
    next(item for item in modules if item["module_type"] == "decision_set")["sha256"] = canonical_sha256(decisions)
    return decisions


def _replace_observed_state(root: Path, modules: list[dict], document: dict) -> None:
    module = next(item for item in modules if item["module_type"] == "observed_state")
    path = root / module["path"]
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    module["sha256"] = canonical_sha256(document)


def _write_delivery(root: Path, modules: list[dict], document: dict) -> None:
    module = next(item for item in modules if item["module_type"] == "use_case_delivery")
    _write_yaml(root / module["path"], document)
    module["sha256"] = canonical_sha256(document)


def _manifest(modules: list[dict]) -> dict:
    return {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {
            "id": "aluca_nagarro_consulting",
            "version": "1.0.0",
            "sha256": "1" * 64,
        },
        "capability_locks": [],
        "modules": modules,
    }


def _accept_runtime(delivery: dict, proof_ref: str = "runtime_revenue_dev") -> None:
    use_case = delivery["use_cases"][0]
    use_case["delivery_state"] = "verified"
    use_case["open_gates"] = []
    assurance = use_case["delivery_assurance"]
    measured_status = {
        "state": "measured",
        "evidence_refs": ["evidence/runtime-acceptance"],
        "note": "Neutral runtime acceptance fixture.",
    }
    assurance["source_behavior"]["status"] = dict(measured_status)
    for rule in assurance["data_quality"]["rules"]:
        rule["status"] = dict(measured_status)
        if rule.get("threshold"):
            rule["threshold"]["provenance"] = "accepted"
    assurance["data_quality"]["status"] = dict(measured_status)
    for signal in assurance["observability"]["signals"]:
        signal["status"] = dict(measured_status)
        if signal.get("threshold"):
            signal["threshold"]["provenance"] = "accepted"
    assurance["observability"]["status"] = dict(measured_status)
    assurance["reliability"]["status"] = dict(measured_status)
    assurance["status"] = dict(measured_status)
    use_case["acceptance"]["runtime_proof_refs"] = [
        {"environment": "dev", "proof_ref": proof_ref}
    ]
    use_case["acceptance"]["status"] = {
        "state": "measured",
        "evidence_refs": ["evidence/runtime-acceptance"],
        "note": "Neutral fixture acceptance only.",
    }


def test_all_project_package_schemas_are_closed_draft_2020_12() -> None:
    assert len(PROJECT_SCHEMAS) == 17
    for path in PROJECT_SCHEMAS:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_plan_schema_supports_milestones_staffing_tasks_and_readable_references() -> None:
    plan = {
        "schema_version": "2.0.0",
        "work_packages": [],
        "dependencies": [],
        "reference_labels": {"O-1": "Resolve the customer choice"},
        "milestones": [{
            "id": "milestone_acceptance", "title": "Acceptance complete", "status": "active",
            "target_gate": "Release gate", "owner_ref": "role_owner", "work_package_refs": [],
            "definition_of_done": ["Acceptance evidence is retained."],
        }],
        "staffing": {
            "delivery_model": "Named accountability with explicit availability",
            "assignments": [{
                "id": "assignment_owner", "role_ref": "role_owner", "person_ref": "person_owner",
                "responsibility": "Accept the outcome.", "allocation_percent": None,
                "state": "required", "basis_ref": "decision_owner",
            }],
        },
        "tasks": [{
            "id": "task_acceptance", "title": "Collect acceptance evidence",
            "work_package_ref": "wp_acceptance", "status": "doing", "priority": "high",
            "owner_ref": "role_owner", "target_gate": "Release gate", "decision_refs": ["O-1"],
            "definition_of_done": ["Positive and negative tests pass."], "evidence_refs": [],
        }],
    }
    schema = _load_schema("project_plan.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(plan)


def test_adapter_declares_every_source_field_exactly_once() -> None:
    assert frozenset(FIELD_MAPPING) == SOURCE_FIELDS
    assert all(paths for paths in FIELD_MAPPING.values())


def test_adapter_rejects_source_contract_drift() -> None:
    changed = _proposal(new_field="silent drift")
    with pytest.raises(ValueError, match="contract drift"):
        adapt_decision_proposals([changed])


def test_preselection_is_never_approval_or_buildable() -> None:
    result = adapt_decision_proposals([_proposal()])
    instance = result["instances"][0]
    assert instance["selection"] == {
        "state": "preselected",
        "option_ref": "proposal",
        "custom_value": None,
    }
    assert instance["approval"]["state"] == "proposed"
    assert instance["approval"]["decided_by"] is None
    assert instance["delivery"]["state"] == "not_compiled"


def test_open_without_proposal_stays_draft() -> None:
    result = adapt_decision_proposals(
        [_proposal(proposal=None, status="offen", alternatives=["Customer input"])]
    )
    instance = result["instances"][0]
    assert instance["selection"]["state"] == "unselected"
    assert instance["approval"]["state"] == "draft"


def test_domain_fanout_requires_explicit_scope_mapping() -> None:
    proposal = _proposal(id="SEC-RLS·retail")
    with pytest.raises(ValueError, match="unresolved domain scope"):
        adapt_decision_proposals([proposal])
    mapped = adapt_decision_proposals([proposal], {"retail": "domain_retail"})
    assert mapped["instances"][0]["scope_refs"] == ["domain_retail"]


def test_all_current_meridian_proposals_map_and_validate() -> None:
    proposals = load_emitters()["propose_all"]({})
    # 20 seit Meridian D-533 (DATA-SILVER-LOAD, das Schreibmuster von Silber).
    # 25 seit Meridian D-615 (30.09.2026): SEC-MIRROR, OPS-MONITORING, PLAT-OVERAGE,
    # OUT-REPORT, AI-DE-COPILOT - die Plattformfragen aus der FabCon Europe 2026.
    # 26 seit Meridian D-620 (01.10.2026): GOV-CATALOG, Purview als Andockmodul.
    assert len(proposals) == 26
    result = adapt_decision_proposals(proposals)
    schema = _load_schema("project_decision_set.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)
    assert len(result["definitions"]) == len(proposals)
    assert len(result["instances"]) == len(proposals)


def test_project_package_validates_hashes_references_and_revision(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {"id": "aluca_nagarro_consulting", "version": "1.0.0", "sha256": "1" * 64},
        "capability_locks": [{"id": "fabric_platform_foundation", "version": "1.0.0", "sha256": "2" * 64}],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)
    assert validate_project_package(tmp_path, SCHEMAS) == []

    manifest["revision"] = 2
    modules[0]["sha256"] = "f" * 64
    _write_yaml(tmp_path / "package.yaml", manifest)
    errors = validate_project_package(tmp_path, SCHEMAS)
    assert "package.yaml: revision > 1 requires parent_revision_hash" in errors
    assert any("hash drift" in error for error in errors)


def test_ai_policy_module_is_project_bound_and_compiles_without_authorizing_egress(tmp_path: Path) -> None:
    neutral = _load_schema("ai_data_handling_policy.schema.json")
    project_schema = _load_schema("project_ai_data_handling.schema.json")
    assert project_schema["$defs"]["policy"] == neutral["definitions"]["policy"]
    project_profile = json.loads(json.dumps(project_schema["$defs"]["profile"]))
    project_profile["properties"]["data_handling"]["$ref"] = "#/definitions/policy"
    assert project_profile == neutral["definitions"]["profile"]

    modules = _minimal_modules(tmp_path)
    decisions = _scope_ai_decision(tmp_path, modules)
    policy = _ai_policy_document(decisions["instances"][0]["id"])
    _add_ai_policy(tmp_path, modules, policy)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))

    assert validate_project_package(tmp_path, SCHEMAS) == []
    compiler = build_compiler_input(tmp_path, SCHEMAS)
    assert compiler["modules"]["ai_data_handling"] == policy
    assert compiler["readiness"]["build_ready"] is False

    policy["project_ref"] = "another_project"
    _add_ai_policy_update(tmp_path, modules, policy)
    assert any("project_ref does not match" in error for error in validate_project_package(tmp_path, SCHEMAS))
    policy["project_ref"] = "project_demo"
    policy["routes"][0]["decision_ref"] = "unknown_decision"
    _add_ai_policy_update(tmp_path, modules, policy)
    assert any("unresolved decision_ref" in error for error in validate_project_package(tmp_path, SCHEMAS))
    policy["routes"][0]["decision_ref"] = decisions["instances"][0]["id"]
    policy["routes"][0]["profile"]["data_handling"]["processing_boundary"] = "local"
    _add_ai_policy_update(tmp_path, modules, policy)
    assert any("external provider as local" in error for error in validate_project_package(tmp_path, SCHEMAS))
    policy["routes"][0]["profile"]["provider"] = "local"
    policy["routes"][0]["profile"]["base_url"] = "https://localhost@public.example/v1"
    _add_ai_policy_update(tmp_path, modules, policy)
    assert any("not a local endpoint candidate" in error for error in validate_project_package(tmp_path, SCHEMAS))
    policy["routes"][0]["profile"].pop("base_url")
    policy["routes"][0]["profile"]["provider"] = "anthropic"
    policy["routes"][0]["profile"]["data_handling"]["processing_boundary"] = "external_cloud"
    policy["routes"][0]["profile"]["data_handling"]["allowed_classifications"] = ["public", "customer_confidential"]
    _add_ai_policy_update(tmp_path, modules, policy)
    assert any("customer-confidential data in external cloud" in error for error in validate_project_package(tmp_path, SCHEMAS))


def _add_ai_policy_update(root: Path, modules: list[dict], document: dict) -> None:
    module = next(item for item in modules if item["module_type"] == "ai_data_handling")
    _write_yaml(root / module["path"], document)
    module["sha256"] = canonical_sha256(document)
    _write_yaml(root / "package.yaml", _manifest(modules))


def test_approved_ai_decision_must_bind_exact_policy_and_evidence(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    decision_path = tmp_path / "discovery/decision_set.yaml"
    decisions = _scope_ai_decision(tmp_path, modules)
    decision = decisions["instances"][0]
    policy = _ai_policy_document(decision["id"])
    route = policy["routes"][0]
    policy_hash = canonical_sha256({key: value for key, value in route.items() if key != "decision_ref"})
    decision["selection"] = {"state": "confirmed", "option_ref": decisions["definitions"][0]["options"][0]["id"],
                             "custom_value": f"sha256:{policy_hash}"}
    decision["approval"] = {"state": "approved", "proposed_by": "consultant", "decided_by": "customer_owner",
                            "rationale": "Public metadata only", "decided_at": "2026-09-25T10:00:00Z",
                            "evidence_refs": ["fixture://customer-decision"]}
    _write_yaml(decision_path, decisions)
    next(item for item in modules if item["module_type"] == "decision_set")["sha256"] = canonical_sha256(decisions)
    _add_ai_policy(tmp_path, modules, policy)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))
    assert validate_project_package(tmp_path, SCHEMAS) == []

    def validate_current() -> list[str]:
        decision["selection"]["custom_value"] = "sha256:" + canonical_sha256(
            {key: value for key, value in route.items() if key != "decision_ref"}
        )
        _write_yaml(decision_path, decisions)
        next(item for item in modules if item["module_type"] == "decision_set")["sha256"] = canonical_sha256(decisions)
        _add_ai_policy_update(tmp_path, modules, policy)
        return validate_project_package(tmp_path, SCHEMAS)

    route["provider_region"] = "us-east"
    _add_ai_policy_update(tmp_path, modules, policy)
    assert any("exact policy hash" in error for error in validate_project_package(tmp_path, SCHEMAS))
    route["provider_terms_evidence_refs"] = []
    assert any("provider terms evidence" in error for error in validate_current())
    route["provider_terms_evidence_refs"] = ["fixture://provider-terms"]
    route["profile"]["data_handling"]["allowed_classifications"] = ["public", "internal_generic"]
    route["profile"]["data_handling"]["require_redaction_for_egress"] = False
    assert any("waive redaction" in error for error in validate_current())
    route["profile"]["data_handling"]["allowed_classifications"] = ["public"]
    route["profile"]["data_handling"]["require_redaction_for_egress"] = True
    route["profile"]["data_residency"] = "eu-only"
    route["provider_geography"] = "us"
    assert any("contradicts declared residency" in error for error in validate_current())
    route["provider_geography"] = "eu"
    route["expires_at"] = "2025-01-01T00:00:00Z"
    assert any("expiry must be after" in error for error in validate_current())
    route["expires_at"] = "2030-01-01T00:00:00Z"
    route["profile"]["data_residency"] = "local"
    route["profile"]["provider"] = "local"
    route["profile"]["data_handling"]["processing_boundary"] = "local"
    route["provider_region"] = "local"
    route["provider_geography"] = "local"
    assert any("requires endpoint and boundary evidence" in error for error in validate_current())
    route["profile"]["base_url"] = "http://llm.internal:11434"
    route["profile"]["data_handling"]["boundary_evidence_ref"] = "fixture://internal-endpoint"
    assert validate_current() == []
    decision["scope_refs"] = []
    assert any("decision scope and ADR" in error for error in validate_current())
    decision.pop("approval")
    _write_yaml(decision_path, decisions)
    next(item for item in modules if item["module_type"] == "decision_set")["sha256"] = canonical_sha256(decisions)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))
    assert any("approval" in error for error in validate_project_package(tmp_path, SCHEMAS))


def test_project_package_rejects_unresolved_decision_references(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    decision_path = tmp_path / "discovery" / "decision_set.yaml"
    decisions = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
    decisions["instances"][0]["definition_ref"] = "d_missing"
    _write_yaml(decision_path, decisions)
    for module in modules:
        if module["module_type"] == "decision_set":
            module["sha256"] = canonical_sha256(decisions)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {"id": "aluca_nagarro_consulting", "version": "1.0.0", "sha256": "1" * 64},
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)
    assert any("unresolved definition_ref" in error for error in validate_project_package(tmp_path, SCHEMAS))


def test_artifact_registry_validates_and_compiles_as_optional_module(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    registry = _artifact_registry()
    _add_artifact_registry(tmp_path, modules, registry)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {
            "id": "aluca_nagarro_consulting",
            "version": "1.0.0",
            "sha256": "1" * 64,
        },
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)

    assert validate_project_package(tmp_path, SCHEMAS) == []
    assert build_compiler_input(tmp_path, SCHEMAS)["modules"]["artifact_registry"] == registry


def test_use_case_delivery_validates_and_compiles_as_optional_module(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    delivery = _add_use_case_delivery(tmp_path, modules)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {
            "id": "aluca_nagarro_consulting",
            "version": "1.0.0",
            "sha256": "1" * 64,
        },
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)

    assert validate_project_package(tmp_path, SCHEMAS) == []
    assert build_compiler_input(tmp_path, SCHEMAS)["modules"]["use_case_delivery"] == delivery


def test_pending_monitoring_contract_can_be_honest_but_cannot_be_build_ready() -> None:
    delivery = yaml.safe_load(USE_CASE_DELIVERY_FIXTURE.read_text(encoding="utf-8"))
    use_case = delivery["use_cases"][0]
    observability = use_case["delivery_assurance"]["observability"]
    observability["stale_after_minutes"] = None
    signal = observability["signals"][0]
    for field in ("recipient_ref", "channel", "response_slo", "runbook_ref", "retention_days", "test_method"):
        signal[field] = None
    schema = _load_schema("project_use_case_delivery.schema.json")

    assert validate_delivery_document(delivery, schema) == []
    rendered = render_use_case(use_case, delivery["project_ref"])
    assert "**Stale after:** open minutes" in rendered
    assert "| open | open | open | open | open | open |" in rendered

    use_case["delivery_state"] = "build_ready"
    errors = validate_delivery_document(delivery, schema)
    assert any("requires a measured or approved stale-after threshold" in error for error in errors)
    assert any("has unresolved operating fields" in error for error in errors)


def test_platform_runtime_evidence_is_resolved_across_project_modules(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    observed = json.loads(OBSERVED_RUNTIME_FIXTURE.read_text(encoding="utf-8"))
    _replace_observed_state(tmp_path, modules, observed)
    delivery = _add_use_case_delivery(tmp_path, modules)
    _accept_runtime(delivery)
    _write_delivery(tmp_path, modules, delivery)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))

    assert validate_project_package(tmp_path, SCHEMAS) == []
    compiler = build_compiler_input(tmp_path, SCHEMAS)
    assert compiler["modules"]["observed_states"]["dev"]["operational_evidence"] == observed["operational_evidence"]


def test_accepted_delivery_rejects_missing_runtime_proof(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    _replace_observed_state(
        tmp_path,
        modules,
        json.loads(OBSERVED_RUNTIME_FIXTURE.read_text(encoding="utf-8")),
    )
    delivery = _add_use_case_delivery(tmp_path, modules)
    _accept_runtime(delivery)
    delivery["use_cases"][0]["acceptance"]["runtime_proof_refs"] = []
    _write_delivery(tmp_path, modules, delivery)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))

    errors = validate_project_package(tmp_path, SCHEMAS)
    assert any("accepted acceptance status requires runtime_proof_refs" in error for error in errors)


def test_proposed_runtime_evidence_does_not_satisfy_acceptance(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    observed = json.loads(OBSERVED_RUNTIME_FIXTURE.read_text(encoding="utf-8"))
    runtime = observed["operational_evidence"]["runtime_tests"][0]
    runtime["outcome"] = "not_run"
    runtime["tested_at"] = None
    runtime["status"] = {
        "state": "proposed",
        "evidence_refs": [],
        "note": "Planned runtime test only.",
    }
    _replace_observed_state(tmp_path, modules, observed)
    delivery = _add_use_case_delivery(tmp_path, modules)
    _accept_runtime(delivery)
    _write_delivery(tmp_path, modules, delivery)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))

    errors = validate_project_package(tmp_path, SCHEMAS)
    assert any("'proposed' evidence and outcome 'not_run'; it does not satisfy acceptance" in error for error in errors)


def test_observed_operational_refs_must_resolve_to_declared_platform_dependencies(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    observed = json.loads(OBSERVED_RUNTIME_FIXTURE.read_text(encoding="utf-8"))
    observed["operational_evidence"]["runtime_tests"][0]["connection_refs"] = ["connection_missing"]
    _replace_observed_state(tmp_path, modules, observed)
    delivery = _add_use_case_delivery(tmp_path, modules)
    _accept_runtime(delivery)
    _write_delivery(tmp_path, modules, delivery)
    _write_yaml(tmp_path / "package.yaml", _manifest(modules))

    errors = validate_project_package(tmp_path, SCHEMAS)
    assert any(
        "runtime proof 'runtime_revenue_dev' has unresolved connection_ref 'connection_missing'" in error
        for error in errors
    )


def test_artifact_lifecycle_rejects_unsupported_status_claims(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    registry = _artifact_registry()
    artifact = registry["artifacts"][0]
    artifact["share_approval"] = {
        "state": "pending",
        "decided_by_ref": None,
        "evidence_refs": [],
    }
    artifact["customer_decision"] = {
        "state": "accepted",
        "decided_by_ref": None,
        "evidence_refs": [],
    }
    registry["publication_events"][0]["file_sha256"] = "9" * 64
    artifact["decision_refs"] = ["missing_decision"]
    _add_artifact_registry(tmp_path, modules, registry)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {
            "id": "aluca_nagarro_consulting",
            "version": "1.0.0",
            "sha256": "1" * 64,
        },
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)

    errors = validate_project_package(tmp_path, SCHEMAS)
    assert any("file and hash do not match" in error for error in errors)
    assert any("lacks approved share gate" in error for error in errors)
    assert any("customer decision lacks decider or evidence" in error for error in errors)
    assert any("unresolved decision_ref 'missing_decision'" in error for error in errors)


def test_artifact_projections_are_deterministic_and_frozen() -> None:
    registry = _artifact_registry()
    first_index = render_artifact_index(registry)
    assert first_index == render_artifact_index(registry)
    assert first_index.index("Architecture decision record") < first_index.index("Internal delivery notes")

    manifest = build_publication_manifest(registry, "send_architecture_decision_record_r2")
    Draft202012Validator(
        _load_schema("project_publication_manifest.schema.json"),
        format_checker=FormatChecker(),
    ).validate(manifest)
    assert manifest["event"]["file_sha256"] == "4" * 64
    assert manifest["artifact"]["customer_decision_state"] == "pending"

    with pytest.raises(ArtifactLifecycleError, match="does not describe the current"):
        registry["publication_events"][0]["artifact_revision"] = 1
        build_publication_manifest(registry, "send_architecture_decision_record_r2")


def test_neutral_artifact_fixture_is_schema_valid_and_uses_demo_identity() -> None:
    fixture = yaml.safe_load(
        (ARTIFACT_FIXTURE / "artifacts" / "index.yaml").read_text(encoding="utf-8")
    )
    Draft202012Validator(
        _load_schema("project_artifact_registry.schema.json"),
        format_checker=FormatChecker(),
    ).validate(fixture)
    assert {artifact["id"] for artifact in fixture["artifacts"]} == {
        "architecture_decision_record",
        "internal_delivery_notes",
    }


def test_legacy_shared_observation_does_not_invent_a_frozen_send() -> None:
    registry = _artifact_registry()
    artifact = registry["artifacts"][0]
    artifact["publication_state"] = "shared_unverified"
    artifact["share_approval"] = {
        "state": "pending",
        "decided_by_ref": None,
        "evidence_refs": ["evidence://historical-share-observation"],
    }
    artifact["customer_decision"] = {
        "state": "accepted",
        "decided_by_ref": "role:customer_decider",
        "evidence_refs": ["evidence://meeting/acceptance"],
    }
    registry["publication_events"] = []
    schema = _load_schema("project_artifact_registry.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(registry)
    with pytest.raises(ArtifactLifecycleError, match="exactly one publication event"):
        build_publication_manifest(registry, "missing_frozen_event")


def test_artifact_cli_renders_index_and_publication_manifest(tmp_path: Path) -> None:
    package_root = tmp_path / "package"
    package_root.mkdir()
    modules = _minimal_modules(package_root)
    registry = _artifact_registry()
    local_files = {
        "deliverables/architecture-decision-record.md": b"# Architecture decision\n",
        "generated/architecture-decision-record.docx": b"synthetic-docx-fixture",
        "internal/delivery-notes.md": b"# Internal notes\n",
    }
    for relative, content in local_files.items():
        path = package_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    artifact_by_id = {item["id"]: item for item in registry["artifacts"]}
    architecture = artifact_by_id["architecture_decision_record"]
    architecture["source_sha256"] = hashlib.sha256(
        local_files["deliverables/architecture-decision-record.md"]
    ).hexdigest()
    architecture["generated_outputs"][0]["sha256"] = hashlib.sha256(
        local_files["generated/architecture-decision-record.docx"]
    ).hexdigest()
    artifact_by_id["internal_delivery_notes"]["source_sha256"] = hashlib.sha256(
        local_files["internal/delivery-notes.md"]
    ).hexdigest()
    registry["publication_events"][0]["file_sha256"] = architecture["generated_outputs"][0]["sha256"]
    _add_artifact_registry(package_root, modules, registry)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {
            "id": "aluca_nagarro_consulting",
            "version": "1.0.0",
            "sha256": "1" * 64,
        },
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(package_root / "package.yaml", manifest)
    index_path = tmp_path / "generated" / "ARTIFACT_INDEX.md"
    release_path = tmp_path / "releases" / "send.json"

    common = ["--package", str(package_root), "--schemas", str(SCHEMAS)]
    assert project_package_cli([*common, "validate"]) == 0
    assert project_package_cli([*common, "reconcile-files"]) == 0
    assert project_package_cli([*common, "render-index", "--output", str(index_path)]) == 0
    assert project_package_cli(
        [
            *common,
            "publication-manifest",
            "--event-id",
            "send_architecture_decision_record_r2",
            "--output",
            str(release_path),
        ]
    ) == 0
    assert index_path.read_text(encoding="utf-8") == render_artifact_index(registry)
    assert json.loads(release_path.read_text(encoding="utf-8")) == build_publication_manifest(
        registry,
        "send_architecture_decision_record_r2",
    )

    (package_root / "generated" / "architecture-decision-record.docx").write_bytes(b"drift")
    with pytest.raises(ValueError, match="file hash drift"):
        project_package_cli([*common, "reconcile-files"])


def test_artifact_cli_validate_accepts_package_without_optional_registry(tmp_path: Path) -> None:
    package_root = migrate_project_package(LEGACY_FIXTURE, tmp_path / "migrated", SCHEMAS)
    common = ["--package", str(package_root), "--schemas", str(SCHEMAS)]

    assert validate_project_package(package_root, SCHEMAS) == []
    assert project_package_cli([*common, "validate"]) == 0
    with pytest.raises(ValueError, match="exactly one artifact_registry module"):
        project_package_cli([*common, "render-index", "--output", str(tmp_path / "index.md")])


def test_canonical_hash_ignores_mapping_order() -> None:
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_v1_migration_is_deterministic_and_retains_external_refs(tmp_path: Path) -> None:
    source_before = _tree_bytes(LEGACY_FIXTURE)
    first = migrate_project_package(LEGACY_FIXTURE, tmp_path / "first", SCHEMAS)
    second = migrate_project_package(LEGACY_FIXTURE, tmp_path / "second", SCHEMAS)

    assert _tree_bytes(first) == _tree_bytes(second)
    assert _tree_bytes(LEGACY_FIXTURE) == source_before
    assert validate_project_package(first, SCHEMAS) == []

    opportunity = yaml.safe_load((first / "opportunity" / "opportunity.yaml").read_text(encoding="utf-8"))
    assert opportunity["source_refs"] == [
        "brief://opportunity/demo",
        "ledger://decision/E-1",
        "contract://data-product/gold",
    ]
    manifest = yaml.safe_load((first / "package.yaml").read_text(encoding="utf-8"))
    legacy = yaml.safe_load((LEGACY_FIXTURE / "package.yaml").read_text(encoding="utf-8"))
    assert manifest["migration"] == {
        "adapter": "project_package_1_0_0",
        "source_version": "1.0.0",
        "source_revision": 1,
        "source_ref": "fixture://project-package/v1/package.yaml",
        "source_hash": canonical_sha256(legacy),
    }


def test_migration_rejects_unknown_version_and_nonempty_target(tmp_path: Path) -> None:
    unsupported = tmp_path / "unsupported"
    shutil.copytree(LEGACY_FIXTURE, unsupported)
    source = yaml.safe_load((unsupported / "package.yaml").read_text(encoding="utf-8"))
    source["schema_version"] = "0.9.0"
    _write_yaml(unsupported / "package.yaml", source)
    with pytest.raises(ProjectPackageMigrationError, match="unsupported migration path"):
        migrate_project_package(unsupported, tmp_path / "unknown-target", SCHEMAS)

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(ProjectPackageMigrationError, match="must be empty"):
        migrate_project_package(LEGACY_FIXTURE, occupied, SCHEMAS)
    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_compiler_input_is_deterministic_and_fail_closed(tmp_path: Path) -> None:
    migrated = migrate_project_package(LEGACY_FIXTURE, tmp_path / "migrated", SCHEMAS)
    first = build_compiler_input(migrated, SCHEMAS)
    second = build_compiler_input(migrated, SCHEMAS)
    Draft202012Validator(
        _load_schema("project_compiler_input.schema.json"),
        format_checker=FormatChecker(),
    ).validate(first)
    assert first == second
    assert first["readiness"] == {
        "decision_ready": True,
        "build_ready": False,
        "unapproved_decision_refs": [],
        "blockers": ["package_not_approved"],
    }
    assert first["provenance"]["migration"]["source_ref"] == (
        "fixture://project-package/v1/package.yaml"
    )


def test_superseded_decision_does_not_block_compiler_readiness(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    decision_path = tmp_path / "discovery" / "decision_set.yaml"
    decisions = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
    instance = decisions["instances"][0]
    instance["selection"] = {"state": "unselected", "option_ref": None, "custom_value": None}
    instance["approval"] = {
        "state": "superseded",
        "proposed_by": None,
        "decided_by": None,
        "rationale": None,
    }
    _write_yaml(decision_path, decisions)
    for module in modules:
        if module["module_type"] == "decision_set":
            module["sha256"] = canonical_sha256(decisions)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "approved",
        "parent_revision_hash": None,
        "operating_profile_lock": {
            "id": "aluca_nagarro_consulting",
            "version": "1.0.0",
            "sha256": "1" * 64,
        },
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)
    compiler_input = build_compiler_input(tmp_path, SCHEMAS)
    assert compiler_input["readiness"]["decision_ready"] is True
    assert compiler_input["readiness"]["build_ready"] is True
