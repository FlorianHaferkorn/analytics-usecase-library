"""Build the neutral, deterministic compiler input from Project Package 2.0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .hashes import canonical_sha256
from .validator import validate_project_package


COMPILER_INPUT_VERSION = "1.0.0"


class CompilerInputError(ValueError):
    """Raised when a package cannot become trusted compiler input."""


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def build_compiler_input(package_root: Path, schema_root: Path) -> dict[str, Any]:
    """Aggregate a validated package without adding customer or architecture meaning."""
    errors = validate_project_package(package_root, schema_root)
    if errors:
        raise CompilerInputError("invalid project package: " + "; ".join(errors))

    manifest = _load(package_root / "package.yaml")
    singleton_modules: dict[str, Any] = {}
    observed_states: dict[str, Any] = {}
    module_locks: list[dict[str, Any]] = []
    for module in manifest["modules"]:
        document = _load(package_root / module["path"])
        module_type = module["module_type"]
        if module_type == "observed_state":
            observed_states[module["environment"]] = document
        else:
            singleton_modules[module_type] = document
        module_locks.append(
            {
                "module_type": module_type,
                "environment": module.get("environment"),
                "path": module["path"],
                "sha256": module["sha256"],
            }
        )

    decision_set = singleton_modules["decision_set"]
    unresolved_states = {"draft", "proposed", "rejected", "deferred"}
    unresolved = sorted(
        instance["id"]
        for instance in decision_set["instances"]
        if instance["approval"]["state"] in unresolved_states
    )
    package_approved = manifest["state"] == "approved"
    decision_ready = not unresolved

    return {
        "schema_version": COMPILER_INPUT_VERSION,
        "package": {
            "schema_version": manifest["schema_version"],
            "package_id": manifest["package_id"],
            "project_ref": manifest["project_ref"],
            "revision": manifest["revision"],
            "state": manifest["state"],
            "operating_profile_lock": manifest["operating_profile_lock"],
            "capability_locks": manifest["capability_locks"],
            "manifest_sha256": canonical_sha256(manifest),
        },
        "modules": {
            "opportunity": singleton_modules["opportunity"],
            "commercial": singleton_modules["commercial"],
            "plan": singleton_modules["plan"],
            "decision_set": decision_set,
            "observed_states": {
                key: observed_states[key] for key in sorted(observed_states)
            },
            **(
                {"architecture_input": singleton_modules["architecture_input"]}
                if "architecture_input" in singleton_modules
                else {}
            ),
            **(
                {"artifact_registry": singleton_modules["artifact_registry"]}
                if "artifact_registry" in singleton_modules
                else {}
            ),
            **(
                {"use_case_delivery": singleton_modules["use_case_delivery"]}
                if "use_case_delivery" in singleton_modules
                else {}
            ),
            **(
                {"batch_ingestion": singleton_modules["batch_ingestion"]}
                if "batch_ingestion" in singleton_modules
                else {}
            ),
            **(
                {"capability_state": singleton_modules["capability_state"]}
                if "capability_state" in singleton_modules
                else {}
            ),
            **(
                {"identity_access": singleton_modules["identity_access"]}
                if "identity_access" in singleton_modules
                else {}
            ),
            **(
                {"architecture_maintenance": singleton_modules["architecture_maintenance"]}
                if "architecture_maintenance" in singleton_modules
                else {}
            ),
            **(
                {"ai_data_handling": singleton_modules["ai_data_handling"]}
                if "ai_data_handling" in singleton_modules
                else {}
            ),
        },
        "readiness": {
            "decision_ready": decision_ready,
            "build_ready": package_approved and decision_ready,
            "unapproved_decision_refs": unresolved,
            "blockers": [
                *([] if package_approved else ["package_not_approved"]),
                *(["decisions_not_approved"] if unresolved else []),
            ],
        },
        "provenance": {
            "module_locks": sorted(
                module_locks,
                key=lambda item: (item["module_type"], item["environment"] or ""),
            ),
            "migration": manifest.get("migration"),
        },
    }
