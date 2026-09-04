"""Validation for a modular Project Package 2.0 directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .hashes import canonical_sha256


SCHEMA_BY_MODULE = {
    "opportunity": "project_opportunity.schema.json",
    "commercial": "project_commercial.schema.json",
    "plan": "project_plan.schema.json",
    "observed_state": "project_observed_state.schema.json",
    "decision_set": "project_decision_set.schema.json",
    "architecture_input": "project_architecture_input.schema.json",
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
            errors.extend(_validate(schema, document, relative.as_posix()))
        if module_type == "decision_set" and isinstance(document, dict):
            errors.extend(_validate_decision_references(document, relative.as_posix()))
        if module_type == "observed_state" and document.get("environment") != environment:
            errors.append(f"{relative.as_posix()}: environment does not match manifest")

    missing = sorted(required - present)
    if missing:
        errors.append(f"package.yaml: missing required module types: {', '.join(missing)}")
    if "observed_state" not in present:
        errors.append("package.yaml: at least one observed_state module is required")
    return errors
