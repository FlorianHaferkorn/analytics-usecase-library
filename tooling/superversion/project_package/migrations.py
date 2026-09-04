"""Explicit, deterministic migrations between Project Package versions."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .hashes import canonical_sha256
from .validator import validate_project_package


CURRENT_VERSION = "2.0.0"
_MODULE_PATHS = {
    "opportunity": "opportunity/opportunity.yaml",
    "commercial": "commercial/commercial.yaml",
    "plan": "plan/plan.yaml",
    "decision_set": "discovery/decision_set.yaml",
}
_SCHEMA_FILES = {
    "opportunity": "project_opportunity.schema.json",
    "commercial": "project_commercial.schema.json",
    "plan": "project_plan.schema.json",
    "observed_state": "project_observed_state.schema.json",
    "decision_set": "project_decision_set.schema.json",
}


class ProjectPackageMigrationError(ValueError):
    """Raised when an explicit package migration cannot be completed safely."""


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _schema(schema_root: Path, name: str) -> dict[str, Any]:
    return json.loads((schema_root / name).read_text(encoding="utf-8"))


def _validate_or_raise(schema: dict[str, Any], value: Any, label: str) -> None:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ProjectPackageMigrationError(f"{label} is invalid: {detail}")


def _write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )


def _assert_empty_target(target_root: Path) -> None:
    if target_root.exists() and (
        not target_root.is_dir() or any(target_root.iterdir())
    ):
        raise ProjectPackageMigrationError(
            f"target directory must be empty: {target_root}"
        )


def _upgrade_module(document: dict[str, Any]) -> dict[str, Any]:
    upgraded = deepcopy(document)
    upgraded["schema_version"] = CURRENT_VERSION
    return upgraded


def _migrate_1_0_0_to_2_0_0(
    source: dict[str, Any],
    target_root: Path,
    schema_root: Path,
) -> None:
    modules: list[dict[str, Any]] = []
    outputs: dict[str, tuple[str, dict[str, Any]]] = {}

    for module_type, relative_path in _MODULE_PATHS.items():
        document = _upgrade_module(source[module_type])
        if module_type == "opportunity":
            refs = list(document.get("source_refs", []))
            for ref in source.get("external_refs", []):
                if ref not in refs:
                    refs.append(ref)
            document["source_refs"] = refs
        _validate_or_raise(
            _schema(schema_root, _SCHEMA_FILES[module_type]),
            document,
            module_type,
        )
        outputs[relative_path] = ("yaml", document)
        modules.append(
            {
                "module_type": module_type,
                "path": relative_path,
                "schema_id": _schema(schema_root, _SCHEMA_FILES[module_type])["$id"],
                "sha256": canonical_sha256(document),
            }
        )

    observed_states = source["observed_states"]
    for observed in sorted(observed_states, key=lambda item: item["environment"]):
        document = _upgrade_module(observed)
        environment = document["environment"]
        _validate_or_raise(
            _schema(schema_root, _SCHEMA_FILES["observed_state"]),
            document,
            f"observed_state[{environment}]",
        )
        relative_path = f"observed/{environment}.json"
        outputs[relative_path] = ("json", document)
        modules.append(
            {
                "module_type": "observed_state",
                "environment": environment,
                "path": relative_path,
                "schema_id": _schema(schema_root, _SCHEMA_FILES["observed_state"])["$id"],
                "sha256": canonical_sha256(document),
            }
        )

    manifest = {
        "schema_version": CURRENT_VERSION,
        "package_id": source["package_id"],
        "project_ref": source["project_ref"],
        "revision": source["revision"],
        "state": source["state"],
        "parent_revision_hash": source["parent_revision_hash"],
        "operating_profile_lock": deepcopy(source["operating_profile_lock"]),
        "capability_locks": deepcopy(source["capability_locks"]),
        "modules": modules,
        "migration": {
            "adapter": "project_package_1_0_0",
            "source_version": "1.0.0",
            "source_revision": source["revision"],
            "source_ref": source["source_ref"],
            "source_hash": canonical_sha256(source),
        },
    }
    outputs["package.yaml"] = ("yaml", manifest)

    # Write only after every source module and the resulting manifest have validated.
    _validate_or_raise(
        _schema(schema_root, "project_package.schema.json"),
        manifest,
        "migrated manifest",
    )
    for relative_path, (file_type, document) in outputs.items():
        output_path = target_root / relative_path
        if file_type == "yaml":
            _write_yaml(output_path, document)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )


Migration = Callable[[dict[str, Any], Path, Path], None]
MIGRATIONS: dict[tuple[str, str], Migration] = {
    ("1.0.0", CURRENT_VERSION): _migrate_1_0_0_to_2_0_0,
}


def migrate_project_package(
    source_root: Path,
    target_root: Path,
    schema_root: Path,
    *,
    target_version: str = CURRENT_VERSION,
) -> Path:
    """Migrate a package through a registered path and return its target root."""
    source_path = source_root / "package.yaml"
    if not source_path.is_file():
        raise ProjectPackageMigrationError(f"missing source manifest: {source_path}")
    source = _load(source_path)
    if not isinstance(source, dict):
        raise ProjectPackageMigrationError("source manifest must be an object")

    source_version = source.get("schema_version")
    migration = MIGRATIONS.get((source_version, target_version))
    if migration is None:
        raise ProjectPackageMigrationError(
            f"unsupported migration path: {source_version!r} -> {target_version!r}"
        )
    _validate_or_raise(
        _schema(schema_root, "legacy_project_package_1_0.schema.json"),
        source,
        "source package",
    )
    _assert_empty_target(target_root)
    target_root.mkdir(parents=True, exist_ok=True)
    migration(source, target_root, schema_root)

    errors = validate_project_package(target_root, schema_root)
    if errors:
        raise ProjectPackageMigrationError(
            "migrated package failed validation: " + "; ".join(errors)
        )
    return target_root
