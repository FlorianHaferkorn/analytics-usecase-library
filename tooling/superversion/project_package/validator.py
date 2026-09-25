"""Validation for a modular Project Package 2.0 directory."""

from __future__ import annotations

import json
import ipaddress
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .hashes import canonical_sha256
from .use_case_delivery import ACCEPTED_EVIDENCE_STATES, validate_delivery_document


SCHEMA_BY_MODULE = {
    "opportunity": "project_opportunity.schema.json",
    "commercial": "project_commercial.schema.json",
    "plan": "project_plan.schema.json",
    "observed_state": "project_observed_state.schema.json",
    "decision_set": "project_decision_set.schema.json",
    "architecture_input": "project_architecture_input.schema.json",
    "artifact_registry": "project_artifact_registry.schema.json",
    "use_case_delivery": "project_use_case_delivery.schema.json",
    "batch_ingestion": "project_batch_ingestion.schema.json",
    "capability_state": "project_capability_state.schema.json",
    "identity_access": "project_identity_access.schema.json",
    "architecture_maintenance": "project_architecture_maintenance.schema.json",
    "ai_data_handling": "project_ai_data_handling.schema.json",
}


def _load_document(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _validate(schema: dict[str, Any], value: Any, label: str) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{label}: {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    ]


def _validate_decision_references(document: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    definitions = document.get("definitions", [])
    instances = document.get("instances", [])
    definition_by_id = {item.get("id"): item for item in definitions}
    if len(definition_by_id) != len(definitions):
        errors.append(f"{label}: duplicate decision definition id")
    instance_ids = [item.get("id") for item in instances]
    if len(set(instance_ids)) != len(instance_ids):
        errors.append(f"{label}: duplicate decision instance id")
    for instance in instances:
        definition_ref = instance.get("definition_ref")
        definition = definition_by_id.get(definition_ref)
        if definition is None:
            errors.append(f"{label}: unresolved definition_ref {definition_ref!r}")
            continue
        option_ref = (instance.get("selection") or {}).get("option_ref")
        option_ids = {option.get("id") for option in definition.get("options", [])}
        if option_ref is not None and option_ref not in option_ids:
            errors.append(f"{label}: unresolved option_ref {option_ref!r} for {instance.get('id')!r}")
        approval = instance.get("approval") or {}
        if approval.get("state") == "approved":
            if (instance.get("selection") or {}).get("state") not in {"selected", "confirmed", "adjusted"}:
                errors.append(f"{label}: approved decision {instance.get('id')!r} has no explicit selection")
            if not approval.get("decided_by") or not approval.get("rationale"):
                errors.append(f"{label}: approved decision {instance.get('id')!r} lacks decider or rationale")
            if definition.get("adr") and (not approval.get("decided_at") or not approval.get("evidence_refs")):
                errors.append(
                    f"{label}: ADR-backed approved decision {instance.get('id')!r} lacks decision time or evidence"
                )
    return errors


def _validate_artifact_lifecycle(document: dict[str, Any], label: str) -> list[str]:
    """Validate lifecycle invariants that JSON Schema cannot express clearly."""
    errors: list[str] = []
    artifacts = document.get("artifacts", [])
    events = document.get("publication_events", [])
    artifact_by_id = {item.get("id"): item for item in artifacts}
    if len(artifact_by_id) != len(artifacts):
        errors.append(f"{label}: duplicate artifact id")

    event_ids = [item.get("id") for item in events]
    if len(set(event_ids)) != len(event_ids):
        errors.append(f"{label}: duplicate publication event id")

    output_ids: list[str] = []
    for artifact in artifacts:
        output_ids.extend(output.get("id") for output in artifact.get("generated_outputs", []))
    if len(set(output_ids)) != len(output_ids):
        errors.append(f"{label}: duplicate generated output id")

    events_by_artifact_revision: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for event in events:
        artifact_ref = event.get("artifact_ref")
        artifact = artifact_by_id.get(artifact_ref)
        if artifact is None:
            errors.append(f"{label}: unresolved artifact_ref {artifact_ref!r}")
            continue
        revision = event.get("artifact_revision")
        events_by_artifact_revision.setdefault((artifact_ref, revision), []).append(event)

        if isinstance(revision, int) and revision > artifact.get("revision", 0):
            errors.append(
                f"{label}: publication event {event.get('id')!r} references a future "
                f"revision of artifact {artifact_ref!r}"
            )
        if revision == artifact.get("revision"):
            expected_files = {artifact.get("source_ref"): artifact.get("source_sha256")}
            expected_files.update(
                {
                    output.get("output_ref"): output.get("sha256")
                    for output in artifact.get("generated_outputs", [])
                }
            )
            if expected_files.get(event.get("file_ref")) != event.get("file_sha256"):
                errors.append(
                    f"{label}: publication event {event.get('id')!r} file and hash do not match "
                    f"artifact {artifact_ref!r} revision {revision!r}"
                )

    for artifact in artifacts:
        artifact_id = artifact.get("id")
        revision = artifact.get("revision")
        current_events = events_by_artifact_revision.get((artifact_id, revision), [])
        event_types = {event.get("event_type") for event in current_events}

        if artifact.get("authority") == "generated_projection" and not artifact.get("generated_from_refs"):
            errors.append(f"{label}: generated projection {artifact_id!r} requires generated_from_refs")
        for source_ref in artifact.get("generated_from_refs", []):
            if source_ref not in artifact_by_id:
                errors.append(
                    f"{label}: artifact {artifact_id!r} has unresolved generated_from_ref {source_ref!r}"
                )

        superseded_by = artifact.get("superseded_by_ref")
        if artifact.get("content_state") == "superseded":
            if not superseded_by:
                errors.append(f"{label}: superseded artifact {artifact_id!r} requires superseded_by_ref")
            elif superseded_by not in artifact_by_id:
                errors.append(
                    f"{label}: artifact {artifact_id!r} has unresolved superseded_by_ref {superseded_by!r}"
                )
        elif superseded_by is not None:
            errors.append(f"{label}: active artifact {artifact_id!r} must not set superseded_by_ref")

        share_approval = artifact.get("share_approval") or {}
        if share_approval.get("state") in {"approved", "rejected"}:
            if not share_approval.get("decided_by_ref") or not share_approval.get("evidence_refs"):
                errors.append(
                    f"{label}: artifact {artifact_id!r} share approval lacks approver or evidence"
                )

        publication_state = artifact.get("publication_state")
        if artifact.get("audience") == "internal" and publication_state != "never_shared":
            errors.append(f"{label}: internal artifact {artifact_id!r} cannot be customer-published")
        if publication_state in {"shared_for_review", "sent_frozen"} and share_approval.get("state") != "approved":
            errors.append(f"{label}: published artifact {artifact_id!r} lacks approved share gate")
        if publication_state == "shared_for_review" and "shared_for_review" not in event_types:
            errors.append(f"{label}: artifact {artifact_id!r} lacks current review-share event")
        if publication_state == "sent_frozen" and "sent_frozen" not in event_types:
            errors.append(f"{label}: artifact {artifact_id!r} lacks current frozen-send event")
        if publication_state == "never_shared" and current_events:
            errors.append(f"{label}: never-shared artifact {artifact_id!r} has current publication events")
        if publication_state == "shared_unverified" and current_events:
            errors.append(
                f"{label}: unverified historical share {artifact_id!r} must not carry an exact publication event"
            )

        customer_decision = artifact.get("customer_decision") or {}
        if customer_decision.get("state") in {"accepted", "rejected"}:
            if not customer_decision.get("decided_by_ref") or not customer_decision.get("evidence_refs"):
                errors.append(
                    f"{label}: artifact {artifact_id!r} customer decision lacks decider or evidence"
                )
            if not current_events and publication_state != "shared_unverified":
                errors.append(
                    f"{label}: artifact {artifact_id!r} customer decision has no publication event"
                )
        if artifact.get("audience") == "internal" and customer_decision.get("state") != "not_requested":
            errors.append(f"{label}: internal artifact {artifact_id!r} cannot carry a customer decision")

    return errors


def _validate_observed_evidence(document: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    resource_ids = [item["logical_id"] for item in document["resources"]]
    if len(resource_ids) != len(set(resource_ids)):
        errors.append(f"{label}: duplicate observed resource logical_id")

    operational = document.get("operational_evidence")
    if operational is None:
        return errors
    proof_rows = [
        (kind, proof)
        for kind in ("connection_tests", "network_tests", "runtime_tests")
        for proof in operational[kind]
    ]
    proof_occurrences: dict[str, list[str]] = {}
    for kind, proof in proof_rows:
        proof_occurrences.setdefault(proof["id"], []).append(kind)
        completed = proof["outcome"] in {"passed", "failed"}
        accepted = proof["status"]["state"] in ACCEPTED_EVIDENCE_STATES
        if completed and (proof["tested_at"] is None or not accepted):
            errors.append(
                f"{label}: {kind} proof {proof['id']!r} with outcome {proof['outcome']!r} "
                "requires a timestamp and confirmed or measured evidence"
            )
        if completed and kind in {"connection_tests", "runtime_tests"} and proof["principal_ref"] is None:
            errors.append(f"{label}: {kind} proof {proof['id']!r} requires the tested principal_ref")
        if proof["outcome"] == "not_run" and (proof["tested_at"] is not None or accepted):
            errors.append(
                f"{label}: {kind} proof {proof['id']!r} marked not_run cannot carry "
                "a timestamp or accepted evidence"
            )
    for proof_id, kinds in sorted(proof_occurrences.items()):
        if len(kinds) > 1:
            errors.append(f"{label}: ambiguous or duplicate operational evidence ref {proof_id!r} in {kinds}")
    return errors


def _validate_capability_state(document: dict[str, Any], label: str) -> list[str]:
    """Keep measurements, decisions and proposals distinct in adaptive discovery."""
    errors: list[str] = []
    capability_ids = [item["id"] for item in document["capabilities"]]
    if len(capability_ids) != len(set(capability_ids)):
        errors.append(f"{label}: duplicate capability-state id")
    for capability in document["capabilities"]:
        fact_ids = [item["id"] for item in capability["facts"]]
        question_refs = [item["question_ref"] for item in capability["answers"]]
        if len(fact_ids) != len(set(fact_ids)):
            errors.append(f"{label}: capability {capability['id']!r} has duplicate fact id")
        if len(question_refs) != len(set(question_refs)):
            errors.append(f"{label}: capability {capability['id']!r} has duplicate question answer")
        rows = [
            (f"fact {item['id']!r}", item["evidence"])
            for item in capability["facts"]
        ] + [
            (f"answer {item['question_ref']!r}", item["evidence"])
            for item in capability["answers"]
        ]
        for row, evidence in rows:
            provenance = evidence["provenance"]
            if provenance == "measured" and (not evidence["evidence_refs"] or evidence["measured_at"] is None):
                errors.append(f"{label}: {row} marked measured requires evidence_refs and measured_at")
            if provenance == "customer_decision" and (not evidence["evidence_refs"] or not evidence["decision_ref"]):
                errors.append(f"{label}: {row} marked customer_decision requires evidence_refs and decision_ref")
            if provenance != "measured" and evidence["measured_at"] is not None:
                errors.append(f"{label}: {row} may set measured_at only for measured provenance")
            if provenance != "customer_decision" and evidence["decision_ref"] is not None:
                errors.append(f"{label}: {row} may set decision_ref only for customer_decision provenance")
        for answer in capability["answers"]:
            if answer["state"] == "answered" and answer["response"] is None:
                errors.append(f"{label}: answered question {answer['question_ref']!r} requires a response")
            if answer["state"] in {"open", "deferred"} and answer["owner_ref"] is None:
                errors.append(f"{label}: unresolved question {answer['question_ref']!r} requires owner_ref")
    return errors


def _validate_ai_data_handling(
    document: dict[str, Any], decision_instances: dict[str, dict[str, Any]],
    decision_definitions: dict[str, dict[str, Any]], label: str,
) -> list[str]:
    """Bind each AI policy to the existing decision set without granting egress."""
    errors: list[str] = []
    routes = document["routes"]
    route_ids = [route["id"] for route in routes]
    if len(set(route_ids)) != len(route_ids):
        errors.append(f"{label}: duplicate AI route id")
    for route in routes:
        route_label = f"{label}: AI route {route['id']!r}"
        decision = decision_instances.get(route["decision_ref"])
        definition = decision_definitions.get(decision["definition_ref"]) if decision else None
        if decision is None:
            errors.append(f"{route_label} has unresolved decision_ref {route['decision_ref']!r}")
        elif route["id"] not in decision["scope_refs"] or not definition or route["id"] not in (definition.get("adr") or {}).get("affected_artifact_refs", []):
            errors.append(f"{route_label} decision scope and ADR must name this AI route")
        policy = route["profile"]["data_handling"]
        boundary = policy["processing_boundary"]
        provider = route["profile"]["provider"].strip().lower()
        if not provider:
            errors.append(f"{route_label} requires a provider name")
        if boundary == "local" and provider not in {"local", "mock"}:
            errors.append(f"{route_label} cannot label an external provider as local")
        if boundary == "local" and provider == "local" and route["profile"].get("base_url") and not _plausible_local_ai_endpoint(route["profile"]["base_url"]):
            errors.append(f"{route_label} local base_url is not a local endpoint candidate")
        if boundary == "local" and provider == "mock" and route["profile"].get("base_url"):
            errors.append(f"{route_label} mock provider cannot carry a base_url")
        if boundary == "external_cloud" and "customer_confidential" in policy["allowed_classifications"]:
            errors.append(f"{route_label} cannot permit customer-confidential data in external cloud")
        if boundary == "external_cloud" and "internal_generic" in policy["allowed_classifications"] and policy["require_redaction_for_egress"] is not True:
            errors.append(f"{route_label} cannot waive redaction for non-public external-cloud input")
        for allowed in route["allowed_inputs"]:
            for field, policy_field in (
                ("classification", "allowed_classifications"),
                ("data_form", "allowed_data_forms"),
                ("purpose", "allowed_purposes"),
            ):
                if allowed[field] not in policy[policy_field]:
                    errors.append(f"{route_label} {field} {allowed[field]!r} is outside its profile")
        if decision is not None and decision["approval"]["state"] == "superseded":
            errors.append(f"{route_label} references a superseded decision")
        if decision is None or decision["approval"]["state"] != "approved":
            continue
        approval = decision["approval"]
        selection = decision["selection"]
        policy_hash = canonical_sha256({key: value for key, value in route.items() if key != "decision_ref"})
        if selection["state"] != "confirmed" or selection["custom_value"] != f"sha256:{policy_hash}":
            errors.append(f"{route_label} approved decision is not bound to this exact policy hash")
        if not approval.get("decided_at") or not approval.get("evidence_refs"):
            errors.append(f"{route_label} approved decision requires date and evidence")
        geography = route["provider_geography"]
        if not route["provider_region"] or not geography or not route["provider_terms_evidence_refs"] or not route["expires_at"]:
            errors.append(f"{route_label} approved policy requires region, geography, provider terms evidence and expiry")
        residency = route["profile"].get("data_residency")
        expected_geography = {"eu-only": "eu", "us-only": "us", "local": "local"}.get(residency)
        if expected_geography and geography != expected_geography:
            errors.append(f"{route_label} provider geography contradicts declared residency")
        if (boundary == "local" and geography != "local") or (boundary != "local" and geography == "local"):
            errors.append(f"{route_label} provider geography contradicts processing boundary")
        if boundary == "local" and provider == "local" and (not route["profile"].get("base_url") or not policy.get("boundary_evidence_ref")):
            errors.append(f"{route_label} approved local route requires endpoint and boundary evidence")
        if approval.get("decided_at") and route["expires_at"]:
            decided = datetime.fromisoformat(approval["decided_at"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(route["expires_at"].replace("Z", "+00:00"))
            if expires <= decided:
                errors.append(f"{route_label} expiry must be after its decision date")
        if any(not allowed["source_refs"] or any(not ref.strip() for ref in allowed["source_refs"]) for allowed in route["allowed_inputs"]):
            errors.append(f"{route_label} approved policy requires source refs for every allowed input")
    return errors


def _plausible_local_ai_endpoint(value: str) -> bool:
    """Reject obvious public URLs; DNS names still require separate runtime proof."""
    try:
        url = urlsplit(value)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
            return False
        host = url.hostname.rstrip(".").lower()
        if host == "localhost":
            return True
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return bool(host) and ("." not in host or host.endswith((".local", ".lan", ".internal", ".intranet", ".home.arpa", ".corp")))
        ranges = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("127.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("fc00::/7"),
            ipaddress.ip_network("::1/128"),
        )
        return any(address in network for network in ranges if address.version == network.version)
    except ValueError:
        return False


def _validate_identity_access(document: dict[str, Any], label: str) -> list[str]:
    """Validate identity references and prevent unproven or personal production access."""
    errors: list[str] = []
    accounts = document["accounts"]
    groups = document["groups"]
    assignments = document["role_assignments"]
    account_by_id = {item["id"]: item for item in accounts}
    group_by_id = {item["id"]: item for item in groups}
    identifiers = [*account_by_id, *group_by_id]
    if len(account_by_id) != len(accounts):
        errors.append(f"{label}: duplicate account id")
    if len(group_by_id) != len(groups):
        errors.append(f"{label}: duplicate group id")
    if len(identifiers) != len(set(identifiers)):
        errors.append(f"{label}: account and group identifiers must be globally unique")
    assignment_ids = [item["id"] for item in assignments]
    if len(assignment_ids) != len(set(assignment_ids)):
        errors.append(f"{label}: duplicate role assignment id")
    for account in accounts:
        credential = account["credential"]
        if credential["authentication"] in {"certificate", "secret"} and not credential["secret_store_ref"]:
            errors.append(f"{label}: account {account['id']!r} requires a secret_store_ref")
        if account["lifecycle_state"] == "verified" and not account["evidence_refs"]:
            errors.append(f"{label}: verified account {account['id']!r} requires evidence_refs")
    for group in groups:
        if group["lifecycle_state"] == "verified" and not group["evidence_refs"]:
            errors.append(f"{label}: verified group {group['id']!r} requires evidence_refs")
    for assignment in assignments:
        subjects = account_by_id if assignment["subject_kind"] == "account" else group_by_id
        subject = subjects.get(assignment["subject_ref"])
        if subject is None:
            errors.append(f"{label}: assignment {assignment['id']!r} has unresolved subject_ref {assignment['subject_ref']!r}")
            continue
        if assignment["subject_kind"] == "group" and assignment["assignment_mode"] != "group_based":
            errors.append(f"{label}: group assignment {assignment['id']!r} must use group_based mode")
        if assignment["subject_kind"] == "account":
            if subject["principal_type"] == "human" and assignment["assignment_mode"] != "direct_exception":
                errors.append(f"{label}: human account assignment {assignment['id']!r} must be a documented direct_exception")
            if assignment["assignment_mode"] == "direct_exception" and not assignment["decision_ref"]:
                errors.append(f"{label}: direct exception {assignment['id']!r} requires decision_ref")
        if assignment["state"] in {"approved", "applied", "verified"} and not assignment["approver_ref"]:
            errors.append(f"{label}: assignment {assignment['id']!r} in state {assignment['state']!r} requires approver_ref")
        if assignment["state"] in {"applied", "verified"} and not assignment["evidence_refs"]:
            errors.append(f"{label}: assignment {assignment['id']!r} in state {assignment['state']!r} requires evidence_refs")
    all_subjects = set(identifiers)
    for rule in document["separation_rules"]:
        for field in ("left_subject_ref", "right_subject_ref"):
            if rule[field] not in all_subjects:
                errors.append(f"{label}: separation rule {rule['id']!r} has unresolved {field} {rule[field]!r}")
        if rule["left_subject_ref"] == rule["right_subject_ref"]:
            errors.append(f"{label}: separation rule {rule['id']!r} must reference two subjects")
        if rule["state"] in {"enforced", "exception_approved"} and not rule["evidence_refs"]:
            errors.append(f"{label}: separation rule {rule['id']!r} in state {rule['state']!r} requires evidence_refs")
    return errors


def _validate_architecture_maintenance(document: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    reconciliation = document["reconciliation"]
    if reconciliation["observed_state_max_age_hours"] < reconciliation["cadence_hours"]:
        errors.append(f"{label}: observed-state maximum age must cover at least one reconciliation cadence")
    if reconciliation["last_result"] == "conformant" and reconciliation["drift_refs"]:
        errors.append(f"{label}: conformant reconciliation must not retain active drift_refs")
    if reconciliation["last_result"] in {"drift", "approved_exception"} and not reconciliation["drift_refs"]:
        errors.append(f"{label}: non-conformant reconciliation requires drift_refs")
    if reconciliation["last_result"] == "approved_exception" and not document["exception_decision_ref"]:
        errors.append(f"{label}: approved reconciliation exception requires a decision reference")
    for collection in ("technology_watch", "transitions"):
        identifiers = [item["id"] for item in document[collection]]
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"{label}: duplicate {collection} id")
    for transition in document["transitions"]:
        if transition["current_ref"] == transition["target_ref"]:
            errors.append(f"{label}: transition {transition['id']!r} must change the architecture reference")
        if transition["state"] in {"cutover_verified", "retired"} and not transition["evidence_refs"]:
            errors.append(
                f"{label}: transition {transition['id']!r} in state {transition['state']!r} requires evidence_refs"
            )
    if document["state"] == "exception" and not document["exception_decision_ref"]:
        errors.append(f"{label}: maintenance exception requires a decision reference")
    return errors


def _validate_delivery_observations(
    delivery: dict[str, Any], observed_states: dict[str, dict[str, Any]]
) -> list[str]:
    dependencies = delivery.get("platform_dependencies")
    if dependencies is None:
        return [
            f"observed[{environment}]: operational_evidence requires platform_dependencies"
            for environment, observed in sorted(observed_states.items())
            if any((observed.get("operational_evidence") or {}).values())
        ]
    errors: list[str] = []
    dependency_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection, kind in (
        ("gateways", "gateway"),
        ("connections", "connection"),
        ("workspaces", "workspace"),
        ("targets", "target"),
    ):
        for dependency in dependencies[collection]:
            dependency_by_id[dependency["id"]] = (kind, dependency)
    use_case_by_id = {use_case["id"]: use_case for use_case in delivery["use_cases"]}

    runtime_by_environment: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for environment, observed in sorted(observed_states.items()):
        operational = observed.get("operational_evidence") or {
            "connection_tests": [],
            "network_tests": [],
            "runtime_tests": [],
        }
        runtime_by_id: dict[str, list[dict[str, Any]]] = {}
        for proof in operational["runtime_tests"]:
            runtime_by_id.setdefault(proof["id"], []).append(proof)
            use_case = use_case_by_id.get(proof["use_case_ref"])
            if use_case is None:
                errors.append(
                    f"observed[{environment}]: runtime proof {proof['id']!r} has unresolved "
                    f"use_case_ref {proof['use_case_ref']!r}"
                )
            for connection_ref in proof["connection_refs"]:
                resolved = dependency_by_id.get(connection_ref)
                if resolved is None or resolved[0] != "connection":
                    errors.append(
                        f"observed[{environment}]: runtime proof {proof['id']!r} has unresolved "
                        f"connection_ref {connection_ref!r}"
                    )
                elif use_case is not None and connection_ref not in use_case.get("platform_dependency_refs", []):
                    errors.append(
                        f"observed[{environment}]: runtime proof {proof['id']!r} uses connection "
                        f"{connection_ref!r} outside use case {use_case['id']!r}"
                    )
            for target_ref in proof["target_refs"]:
                resolved = dependency_by_id.get(target_ref)
                if resolved is None or resolved[0] != "target":
                    errors.append(
                        f"observed[{environment}]: runtime proof {proof['id']!r} has unresolved "
                        f"target_ref {target_ref!r}"
                    )
                elif use_case is not None and target_ref not in use_case.get("platform_dependency_refs", []):
                    errors.append(
                        f"observed[{environment}]: runtime proof {proof['id']!r} uses target "
                        f"{target_ref!r} outside use case {use_case['id']!r}"
                    )
        runtime_by_environment[environment] = runtime_by_id

        for proof in operational["connection_tests"]:
            resolved = dependency_by_id.get(proof["connection_ref"])
            if resolved is None or resolved[0] != "connection":
                errors.append(
                    f"observed[{environment}]: connection proof {proof['id']!r} has unresolved "
                    f"connection_ref {proof['connection_ref']!r}"
                )
        for proof in operational["network_tests"]:
            resolved = dependency_by_id.get(proof["connection_ref"])
            if resolved is None or resolved[0] != "connection":
                errors.append(
                    f"observed[{environment}]: network proof {proof['id']!r} has unresolved "
                    f"connection_ref {proof['connection_ref']!r}"
                )
                continue
            expected_gateway = resolved[1]["gateway_ref"]
            if proof["gateway_ref"] != expected_gateway:
                errors.append(
                    f"observed[{environment}]: network proof {proof['id']!r} gateway_ref "
                    f"{proof['gateway_ref']!r} does not match connection {proof['connection_ref']!r}"
                )

    for use_case in delivery["use_cases"]:
        acceptance = use_case["acceptance"]
        acceptance_state = acceptance["status"]["state"]
        accepted_acceptance = acceptance_state in ACCEPTED_EVIDENCE_STATES
        references = acceptance.get("runtime_proof_refs", [])
        accepted_proofs: list[tuple[str, dict[str, Any]]] = []
        for reference in references:
            environment = reference["environment"]
            proof_ref = reference["proof_ref"]
            observed = observed_states.get(environment)
            candidates = runtime_by_environment.get(environment, {}).get(proof_ref, [])
            if observed is None or observed.get("collection_state") != "collected" or len(candidates) != 1:
                errors.append(
                    f"{use_case['id']}: unresolved runtime proof {proof_ref!r} in collected "
                    f"environment {environment!r}"
                )
                continue
            proof = candidates[0]
            if proof["use_case_ref"] != use_case["id"]:
                errors.append(
                    f"{use_case['id']}: runtime proof {proof_ref!r} belongs to "
                    f"{proof['use_case_ref']!r}"
                )
                continue
            proof_accepted = (
                proof["outcome"] == "passed"
                and proof["tested_at"] is not None
                and proof["status"]["state"] in ACCEPTED_EVIDENCE_STATES
                and bool(proof["status"]["evidence_refs"])
            )
            if accepted_acceptance and not proof_accepted:
                errors.append(
                    f"{use_case['id']}: runtime proof {proof_ref!r} has "
                    f"{proof['status']['state']!r} evidence and outcome {proof['outcome']!r}; "
                    "it does not satisfy acceptance"
                )
            if proof_accepted:
                accepted_proofs.append((environment, proof))

        if not accepted_acceptance:
            continue

        required_connection_refs = {
            source["connection_ref"]
            for boundary in ("canonical",)
            for source in use_case["source_contract"][boundary]
            if source.get("connection_ref") is not None
        }
        required_target_refs = {
            product["target_ref"]
            for product in use_case["data_products"]
            if product.get("target_ref") is not None
        }
        covered_connections = {
            reference for _, proof in accepted_proofs for reference in proof["connection_refs"]
        }
        covered_targets = {reference for _, proof in accepted_proofs for reference in proof["target_refs"]}
        missing_connections = sorted(required_connection_refs - covered_connections)
        missing_targets = sorted(required_target_refs - covered_targets)
        if missing_connections or missing_targets:
            errors.append(
                f"{use_case['id']}: accepted runtime proofs do not cover connections "
                f"{missing_connections} and targets {missing_targets}"
            )

        for environment, proof in accepted_proofs:
            operational = observed_states[environment]["operational_evidence"]
            observed_resource_refs = {
                item["logical_id"] for item in observed_states[environment]["resources"]
            }
            required_resource_refs = set(proof["connection_refs"]) | set(proof["target_refs"])
            for connection_ref in proof["connection_refs"]:
                resolved_connection = dependency_by_id.get(connection_ref)
                if resolved_connection and resolved_connection[0] == "connection":
                    gateway_ref = resolved_connection[1]["gateway_ref"]
                    if gateway_ref is not None:
                        required_resource_refs.add(gateway_ref)
            for target_ref in proof["target_refs"]:
                resolved_target = dependency_by_id.get(target_ref)
                if resolved_target and resolved_target[0] == "target":
                    required_resource_refs.add(resolved_target[1]["workspace_ref"])
            missing_resource_refs = sorted(required_resource_refs - observed_resource_refs)
            if missing_resource_refs:
                errors.append(
                    f"{use_case['id']}: runtime proof {proof['id']!r} lacks observed resources "
                    f"{missing_resource_refs} in {environment!r}"
                )
            for connection_ref in sorted(required_connection_refs.intersection(proof["connection_refs"])):
                connection_ok = any(
                    item["connection_ref"] == connection_ref
                    and item["outcome"] == "passed"
                    and item["status"]["state"] in ACCEPTED_EVIDENCE_STATES
                    for item in operational["connection_tests"]
                )
                if not connection_ok:
                    errors.append(
                        f"{use_case['id']}: runtime proof {proof['id']!r} lacks accepted connection "
                        f"evidence for {connection_ref!r} in {environment!r}"
                    )
                gateway_ref = dependency_by_id[connection_ref][1]["gateway_ref"]
                if gateway_ref is not None:
                    network_ok = any(
                        item["connection_ref"] == connection_ref
                        and item["gateway_ref"] == gateway_ref
                        and item["outcome"] == "passed"
                        and item["status"]["state"] in ACCEPTED_EVIDENCE_STATES
                        for item in operational["network_tests"]
                    )
                    if not network_ok:
                        errors.append(
                            f"{use_case['id']}: runtime proof {proof['id']!r} lacks accepted network "
                            f"evidence for {gateway_ref!r} -> {connection_ref!r} in {environment!r}"
                        )
    return errors


def validate_project_package(package_root: Path, schema_root: Path) -> list[str]:
    """Return deterministic validation errors; an empty list means valid."""
    manifest_path = package_root / "package.yaml"
    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]

    manifest = _load_document(manifest_path)
    manifest_schema = _load_document(schema_root / "project_package.schema.json")
    errors = _validate(manifest_schema, manifest, "package.yaml")

    revision = manifest.get("revision") if isinstance(manifest, dict) else None
    parent_hash = manifest.get("parent_revision_hash") if isinstance(manifest, dict) else None
    if revision == 1 and parent_hash is not None:
        errors.append("package.yaml: revision 1 must not have a parent_revision_hash")
    if isinstance(revision, int) and revision > 1 and parent_hash is None:
        errors.append("package.yaml: revision > 1 requires parent_revision_hash")

    seen: set[tuple[str, str | None]] = set()
    required = {"opportunity", "commercial", "plan", "decision_set"}
    present: set[str] = set()
    decision_ids: set[str] = set()
    decision_instances: dict[str, dict[str, Any]] = {}
    decision_definitions: dict[str, dict[str, Any]] = {}
    ai_data_handling: dict[str, Any] | None = None
    artifact_registry: dict[str, Any] | None = None
    delivery_document: dict[str, Any] | None = None
    observed_states: dict[str, dict[str, Any]] = {}
    for module in manifest.get("modules", []) if isinstance(manifest, dict) else []:
        module_type = module.get("module_type")
        environment = module.get("environment")
        if module_type in {"batch_ingestion", "capability_state", "identity_access", "architecture_maintenance", "ai_data_handling"} and environment is not None:
            errors.append(f"package.yaml: {module_type} is a singleton and cannot have an environment key")
        key = (module_type, environment)
        if key in seen:
            errors.append(f"package.yaml: duplicate module key {key}")
            continue
        seen.add(key)
        present.add(module_type)
        relative = Path(module.get("path", ""))
        module_path = (package_root / relative).resolve()
        try:
            module_path.relative_to(package_root.resolve())
        except ValueError:
            errors.append(f"package.yaml: module path escapes package root: {relative.as_posix()}")
            continue
        if not module_path.is_file():
            errors.append(f"package.yaml: missing module {relative.as_posix()}")
            continue
        document = _load_document(module_path)
        expected_hash = canonical_sha256(document)
        if module.get("sha256") != expected_hash:
            errors.append(f"package.yaml: hash drift for {relative.as_posix()}")
        schema_name = SCHEMA_BY_MODULE.get(module_type)
        if schema_name:
            schema = _load_document(schema_root / schema_name)
            module_schema_errors = _validate(schema, document, relative.as_posix())
            errors.extend(module_schema_errors)
            if module_type == "use_case_delivery" and isinstance(document, dict) and not module_schema_errors:
                delivery_errors = validate_delivery_document(document, schema)
                errors.extend(f"{relative.as_posix()}: {error}" for error in delivery_errors)
                if not delivery_errors:
                    delivery_document = document
        if module_type == "decision_set" and isinstance(document, dict) and not module_schema_errors:
            errors.extend(_validate_decision_references(document, relative.as_posix()))
            decision_ids = {item.get("id") for item in document.get("instances", [])}
            decision_instances = {item.get("id"): item for item in document.get("instances", [])}
            decision_definitions = {item.get("id"): item for item in document.get("definitions", [])}
        if module_type == "artifact_registry" and isinstance(document, dict):
            errors.extend(_validate_artifact_lifecycle(document, relative.as_posix()))
            artifact_registry = document
        if module_type == "observed_state" and isinstance(document, dict) and not module_schema_errors:
            if document.get("environment") != environment:
                errors.append(f"{relative.as_posix()}: environment does not match manifest")
            else:
                observed_errors = _validate_observed_evidence(document, relative.as_posix())
                errors.extend(observed_errors)
                if not observed_errors:
                    observed_states[environment] = document
        if module_type == "batch_ingestion" and isinstance(document, dict) and not module_schema_errors:
            from .batch_ingestion import validate_contract
            errors.extend(f"{relative.as_posix()}: {error}" for error in validate_contract(document))
        if module_type == "capability_state" and isinstance(document, dict) and not module_schema_errors:
            errors.extend(_validate_capability_state(document, relative.as_posix()))
        if module_type == "identity_access" and isinstance(document, dict) and not module_schema_errors:
            errors.extend(_validate_identity_access(document, relative.as_posix()))
        if module_type == "architecture_maintenance" and isinstance(document, dict) and not module_schema_errors:
            errors.extend(_validate_architecture_maintenance(document, relative.as_posix()))
            if document["project_ref"] != manifest.get("project_ref"):
                errors.append(f"{relative.as_posix()}: project_ref does not match package.yaml")
        if module_type == "ai_data_handling" and isinstance(document, dict) and not module_schema_errors:
            ai_data_handling = document
            if document["project_ref"] != manifest.get("project_ref"):
                errors.append(f"{relative.as_posix()}: project_ref does not match package.yaml")

    missing = sorted(required - present)
    if missing:
        errors.append(f"package.yaml: missing required module types: {', '.join(missing)}")
    if "observed_state" not in present:
        errors.append("package.yaml: at least one observed_state module is required")
    if artifact_registry is not None:
        for artifact in artifact_registry.get("artifacts", []):
            for decision_ref in artifact.get("decision_refs", []):
                if decision_ref not in decision_ids:
                    errors.append(
                        "artifacts/index.yaml: artifact "
                        f"{artifact.get('id')!r} has unresolved decision_ref {decision_ref!r}"
                    )
    if ai_data_handling is not None:
        errors.extend(_validate_ai_data_handling(ai_data_handling, decision_instances, decision_definitions, "ai_data_handling"))
    if delivery_document is not None:
        errors.extend(_validate_delivery_observations(delivery_document, observed_states))
    elif any(
        any((observed.get("operational_evidence") or {}).values())
        for observed in observed_states.values()
    ):
        errors.append("operational_evidence requires a valid use_case_delivery module")
    return errors
