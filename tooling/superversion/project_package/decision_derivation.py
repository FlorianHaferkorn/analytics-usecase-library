"""Reviewed, identity-addressed architecture changes; never decision approval or apply."""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .compiler_input import build_compiler_input
from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository, StaleProjectPackageDraftError


# Deliberately not a generic JSON Patch: identifiers, approval references, native
# executable definitions and fail-closed policy cannot be rewritten through rules.
FIELDS = {
    "domains": {"capacity", "delivery_scope"},
    "use_cases": {"name", "architecture_detail"},
    "physical_workspaces": {"name", "description", "capacity_id", "domain_id"},
    "physical_items": {"name", "description"},
    "environments": {"recommended", "accepted"},
}


def _same(left: Any, right: Any) -> bool:
    return canonical_sha256(left) == canonical_sha256(right)


def _target(architecture: dict, target: dict) -> dict:
    collection, identity, field = target["collection"], target["entity_id"], target["field"]
    if field not in FIELDS.get(collection, set()):
        raise ValueError("Target field is not supported by the bounded derivation contract")
    if collection == "environments":
        if identity is not None:
            raise ValueError("Environment target requires entity_id null")
        entity = architecture.get(collection)
    else:
        matches = [row for row in architecture.get(collection, []) if row.get("id") == identity]
        if not identity or len(matches) != 1:
            raise ValueError("Target identity must match exactly one existing architecture element")
        entity = matches[0]
    if not isinstance(entity, dict) or field not in entity:
        raise ValueError("Target field must already exist; adding or deleting elements is unsupported")
    return entity


def _schema_errors(architecture: dict, schema_root: Path) -> list[str]:
    schema = json.loads((schema_root / "project_architecture_input.schema.json").read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(architecture)]


def compile_derivation(compiler: dict, revision_hash: str, schema_root: Path) -> dict:
    """Pure preview. Pending and other-option rules are visible but not applicable."""
    architecture = compiler["modules"].get("architecture_input")
    projected = copy.deepcopy(architecture)
    rules, changes, blockers = [], [], []
    decisions = compiler["modules"]["decision_set"]
    authored = architecture.get("decision_rules", []) if architecture else []
    if architecture:
        errors = _schema_errors(architecture, schema_root)
        if errors:
            raise ValueError("Invalid architecture rule schema: " + "; ".join(errors))
    seen, affected = set(), {}
    for rule in authored:
        row = {"id": rule["id"], "decision_ref": rule["decision_ref"], "option_ref": rule["option_ref"],
               "target": rule["target"], "rationale": rule["rationale"]}
        if rule["id"] in seen:
            blockers.append(f"{rule['id']}: duplicate rule identity")
        seen.add(rule["id"])
        try:
            instances = [item for item in decisions["instances"] if item["id"] == rule["decision_ref"]]
            if len(instances) != 1:
                raise ValueError("Decision identity must match exactly one instance")
            decision = instances[0]
            definitions = [item for item in decisions["definitions"] if item["id"] == decision["definition_ref"]]
            if len(definitions) != 1 or len([option for option in definitions[0]["options"] if option["id"] == rule["option_ref"]]) != 1:
                raise ValueError("Rule option must belong to the referenced decision definition")
            approval, selection = decision["approval"], decision["selection"]
            if approval["state"] != "approved" or selection["state"] != "confirmed":
                row.update(status="pending", reason="Decision needs an approved, confirmed selection")
            elif selection["custom_value"] is not None:
                raise ValueError("Custom decision values require a separately authored mapping")
            elif selection["option_ref"] != rule["option_ref"]:
                row.update(status="not_selected", reason="A different option was approved")
            else:
                entity = _target(architecture, rule["target"])
                before = copy.deepcopy(entity[rule["target"]["field"]])
                row.update(before=before, after=rule["value"])
                if decision["revision"] != rule["decision_revision"]:
                    raise ValueError("Decision revision changed; review the rule against its current evidence")
                if not approval.get("decided_by") or not approval.get("rationale"):
                    raise ValueError("Approved decision requires a recorded decider and rationale")
                target = rule["target"]
                if target["collection"] == "environments" and entity["decision_ref"] != rule["decision_ref"]:
                    raise ValueError("Environment mapping must use its declared decision reference")
                if target["collection"] in {"physical_workspaces", "physical_items"} and rule["decision_ref"] not in entity["decision_refs"]:
                    raise ValueError("Physical element does not reference this approved decision")
                # Scoped decisions cannot silently affect another entity. Root-wide
                # environment rules require explicitly project-wide (empty) scope.
                scope = decision["scope_refs"]
                if scope and target["entity_id"] not in scope:
                    raise ValueError("Rule target is outside the approved decision scope")
                key = (target["collection"], target["entity_id"], target["field"])
                if key in affected:
                    raise ValueError(f"Conflicting active rule also targets this field: {affected[key]}")
                affected[key] = rule["id"]
                if _same(before, rule["value"]):
                    row.update(status="unchanged", reason="Architecture already contains the approved value")
                elif not _same(before, rule["expected_value"]):
                    raise ValueError("Current value differs from the rule precondition; review required")
                else:
                    row.update(status="ready", reason="Explicit approved mapping; review before creating a working revision")
                    _target(projected, target)[target["field"]] = copy.deepcopy(rule["value"])
                    changes.append({**row, "rule_id": rule["id"], "decision_revision": decision["revision"], "decision_sha256": canonical_sha256(decision)})
        except ValueError as error:
            row.update(status="blocked", reason=str(error))
            blockers.append(f"{rule['id']}: {error}")
        rules.append(row)
    if changes:
        blockers.extend("Derived architecture schema: " + error for error in _schema_errors(projected, schema_root))
    result = {"schema_version": "1.0.0", "project_ref": compiler["package"]["project_ref"],
              "revision_hash": revision_hash, "rules": rules, "changes": changes, "blockers": blockers,
              "can_apply": bool(changes) and not blockers, "state_after_apply": "working", "release_required": True,
              "tenant_actions_performed": False}
    return {**result, "preview_sha256": canonical_sha256(result)}


def preview_derivation(repository: ProjectPackageRevisionRepository, project_ref: str, revision_hash: str) -> dict:
    current = repository.head()
    if not current or current.revision_hash != revision_hash:
        raise StaleProjectPackageDraftError("Package HEAD changed; refresh before reviewing architecture derivations")
    if current.project_ref != project_ref:
        raise ValueError("Package belongs to a different project")
    return compile_derivation(build_compiler_input(current.package_root, repository.schema_root), revision_hash, repository.schema_root)


def apply_derivation(repository: ProjectPackageRevisionRepository, payload: dict) -> dict:
    required = {"project_ref", "revision_hash", "preview_sha256", "actor", "rationale", "confirm_apply"}
    if set(payload) != required or payload.get("confirm_apply") is not True:
        raise ValueError("Exact reviewed derivation confirmation required")
    if not isinstance(payload["actor"], str) or not payload["actor"].strip():
        raise ValueError("Authenticated actor required")
    if not isinstance(payload["rationale"], str) or not 20 <= len(payload["rationale"].strip()) <= 4000:
        raise ValueError("Review rationale requires 20 to 4000 characters")
    preview = preview_derivation(repository, payload["project_ref"], payload["revision_hash"])
    if preview["preview_sha256"] != payload["preview_sha256"]:
        raise ValueError("Preview changed; review the current before/after values")
    if not preview["can_apply"]:
        raise ValueError("No conflict-free approved changes are ready")
    with tempfile.TemporaryDirectory(prefix="decision-derivation-") as temporary:
        root = repository.checkout(Path(temporary) / "package", payload["revision_hash"])
        manifest_path = root / "package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        module = next(item for item in manifest["modules"] if item["module_type"] == "architecture_input")
        path = root / module["path"]
        architecture = yaml.safe_load(path.read_text(encoding="utf-8"))
        for change in preview["changes"]:
            target = change["target"]
            _target(architecture, target)[target["field"]] = copy.deepcopy(change["after"])
        path.write_text(json.dumps(architecture, ensure_ascii=False, indent=2) if path.suffix.lower() == ".json" else yaml.safe_dump(architecture, sort_keys=False, allow_unicode=True), encoding="utf-8", newline="\n")
        audit_ref = f"architecture/derivations/{preview['preview_sha256']}.json"
        audit_path = root / audit_ref
        if audit_path.exists():
            raise ValueError("This exact derivation review was already recorded")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit = {**preview, "record_type": "reviewed_architecture_derivation", "reviewed_by": payload["actor"],
                 "reviewed_at": datetime.now(timezone.utc).isoformat(), "review_rationale": payload["rationale"].strip(),
                 "authority": "Applies explicit existing approved decisions to draft architecture only. Not package approval, release or tenant authorization."}
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest["state"] = "working"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
        result = repository.commit_draft(root, expected_head_hash=payload["revision_hash"])
    return {"project_ref": result.project_ref, "revision_hash": result.revision_hash,
            "parent_revision_hash": result.parent_revision_hash, "audit_ref": audit_ref,
            "state": "working", "release_required": True, "tenant_actions_performed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--schemas", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=["preview", "apply"])
    args = parser.parse_args()
    try:
        text = sys.stdin.read(1_000_001)
        if len(text.encode("utf-8")) > 1_000_000:
            raise ValueError("Request is too large")
        payload = json.loads(text)
        if not isinstance(payload, dict) or not isinstance(payload.get("revision_hash"), str) or not re.fullmatch(r"[a-f0-9]{64}", payload["revision_hash"]):
            raise ValueError("Invalid request revision")
        repo = ProjectPackageRevisionRepository(args.repository, args.schemas)
        if args.mode == "preview":
            if set(payload) != {"project_ref", "revision_hash"}:
                raise ValueError("Invalid preview request")
            value = preview_derivation(repo, payload["project_ref"], payload["revision_hash"])
        else:
            value = apply_derivation(repo, payload)
        print(json.dumps({"ok": True, "value": value}, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
