"""Validation for a modular Project Package 2.0 directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .hashes import canonical_sha256
from .use_case_delivery import validate_delivery_document


SCHEMA_BY_MODULE = {
    "opportunity": "project_opportunity.schema.json",
    "commercial": "project_commercial.schema.json",
    "plan": "project_plan.schema.json",
    "observed_state": "project_observed_state.schema.json",
    "decision_set": "project_decision_set.schema.json",
    "architecture_input": "project_architecture_input.schema.json",
    "artifact_registry": "project_artifact_registry.schema.json",
    "use_case_delivery": "project_use_case_delivery.schema.json",
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
    artifact_registry: dict[str, Any] | None = None
    for module in manifest.get("modules", []) if isinstance(manifest, dict) else []:
        module_type = module.get("module_type")
        environment = module.get("environment")
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
                errors.extend(
                    f"{relative.as_posix()}: {error}"
                    for error in validate_delivery_document(document, schema)
                )
        if module_type == "decision_set" and isinstance(document, dict):
            errors.extend(_validate_decision_references(document, relative.as_posix()))
            decision_ids = {item.get("id") for item in document.get("instances", [])}
        if module_type == "artifact_registry" and isinstance(document, dict):
            errors.extend(_validate_artifact_lifecycle(document, relative.as_posix()))
            artifact_registry = document
        if module_type == "observed_state" and document.get("environment") != environment:
            errors.append(f"{relative.as_posix()}: environment does not match manifest")

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
    return errors
