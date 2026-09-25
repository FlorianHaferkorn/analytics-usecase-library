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
    "plan_work_packages": {"role_refs", "effort"},
    "plan_tasks": {"definition_of_done"},
}

ENVIRONMENT_PLAN_FIELDS = {
    ("plan_work_packages", "role_refs"),
    ("plan_work_packages", "effort"),
    ("plan_tasks", "definition_of_done"),
}


def _missing_stage_workspaces(architecture: dict, stages: list[str]) -> list[str]:
    """Require authored topology, never infer Fabric workspaces from a stage label."""
    declared = {(row["domain_ref"], row["environment"]) for row in architecture.get("physical_workspaces", [])}
    return [f"{domain['id']}/{stage}" for domain in architecture.get("domains", [])
            if domain["delivery_scope"] == "detailed" for stage in stages
            if (domain["id"], stage) not in declared]


def _same(left: Any, right: Any) -> bool:
    return canonical_sha256(left) == canonical_sha256(right)


def _target(modules: dict, target: dict) -> dict:
    collection, identity, field = target["collection"], target["entity_id"], target["field"]
    if field not in FIELDS.get(collection, set()):
        raise ValueError("Target field is not supported by the bounded derivation contract")
    if collection.startswith("plan_") and not isinstance(modules.get("plan"), dict):
        raise ValueError("Delivery plan module is missing")
    owner = modules["plan"] if collection.startswith("plan_") else modules["architecture_input"]
    rows = collection.removeprefix("plan_") if collection.startswith("plan_") else collection
    if collection == "environments":
        if identity is not None:
            raise ValueError("Environment target requires entity_id null")
        entity = owner.get(rows)
    else:
        matches = [row for row in owner.get(rows, []) if row.get("id") == identity]
        if not identity or len(matches) != 1:
            raise ValueError("Target identity must match exactly one existing element")
        entity = matches[0]
    if not isinstance(entity, dict) or field not in entity:
        raise ValueError("Target field must already exist; adding or deleting elements is unsupported")
    return entity


def _schema_errors(document: dict, schema_root: Path, name: str) -> list[str]:
    schema = json.loads((schema_root / f"project_{name}.schema.json").read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)]


def compile_derivation(compiler: dict, revision_hash: str, schema_root: Path) -> dict:
    """Pure preview. Pending and other-option rules are visible but not applicable."""
    modules = compiler["modules"]
    architecture = modules.get("architecture_input")
    projected = {"architecture_input": copy.deepcopy(architecture)}
    if "plan" in modules:
        projected["plan"] = copy.deepcopy(modules["plan"])
    rules, changes, blockers = [], [], []
    decisions = compiler["modules"]["decision_set"]
    authored = architecture.get("decision_rules", []) if architecture else []
    if architecture:
        errors = _schema_errors(architecture, schema_root, "architecture_input")
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
                entity = _target(modules, rule["target"])
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
                effects = [{"target": target, "expected_value": rule["expected_value"], "value": rule["value"]}, *rule.get("plan_effects", [])]
                if target == {"collection": "environments", "entity_id": None, "field": "recommended"}:
                    covered = {(effect["target"]["collection"], effect["target"]["field"]) for effect in rule.get("plan_effects", [])}
                    missing = ENVIRONMENT_PLAN_FIELDS - covered
                    if missing:
                        raise ValueError("Environment stage change requires explicit plan role, effort and task acceptance effects: " + str(sorted(missing)))
                    absent = _missing_stage_workspaces(architecture, rule["value"])
                    if absent:
                        raise ValueError("Environment stage change requires explicitly authored workspace topology for: " + ", ".join(absent))
                    for effect in rule["plan_effects"]:
                        field = effect["target"]["field"]
                        if field == "role_refs" and (not isinstance(effect["value"], list) or not effect["value"]):
                            raise ValueError("Environment stage change requires nonempty role demand")
                        if field == "effort" and (not isinstance(effect["value"], dict) or effect["value"].get("value") is None
                                                  or effect["value"].get("provenance") == "unknown"):
                            raise ValueError("Environment stage change requires an explicit effort value and provenance")
                        if field == "definition_of_done" and (not isinstance(effect["value"], list) or not effect["value"]):
                            raise ValueError("Environment stage change requires a nonempty task acceptance criterion")
                plan_work_package_ids = set()
                plan_task_ids = set()
                changed = False
                for effect in effects:
                    effect_target = effect["target"]
                    effect_entity = _target(modules, effect_target)
                    if effect_target["collection"].startswith("plan_"):
                        if rule["decision_ref"] not in effect_entity["decision_refs"]:
                            raise ValueError("Plan element does not reference this approved decision")
                        if effect_target["collection"] == "plan_work_packages":
                            plan_work_package_ids.add(effect_target["entity_id"])
                        else:
                            plan_task_ids.add(effect_entity["work_package_ref"])
                    effect_before = copy.deepcopy(effect_entity[effect_target["field"]])
                    if (effect_target["collection"] == "plan_tasks" and effect_target["field"] == "definition_of_done"
                            and not _same(effect_before, effect["value"])
                            and (effect_entity["status"] == "done" or effect_entity["evidence_refs"])):
                        raise ValueError("Changed task acceptance criteria require a task without completion status or retained evidence; review and reopen the task separately")
                    key = (effect_target["collection"], effect_target["entity_id"], effect_target["field"])
                    if key in affected:
                        raise ValueError(f"Conflicting active rule also targets this field: {affected[key]}")
                    affected[key] = rule["id"]
                    if _same(effect_before, effect["value"]):
                        continue
                    if not _same(effect_before, effect["expected_value"]):
                        raise ValueError("Current value differs from the rule precondition; review required")
                    changed = True
                    _target(projected, effect_target)[effect_target["field"]] = copy.deepcopy(effect["value"])
                    changes.append({**row, "before": effect_before, "after": effect["value"], "target": effect_target,
                                    "rule_id": rule["id"], "decision_revision": decision["revision"],
                                    "decision_sha256": canonical_sha256(decision)})
                if plan_task_ids - plan_work_package_ids:
                    raise ValueError("Plan acceptance task must belong to a work package impacted by the same decision")
                row.update(status="ready" if changed else "unchanged",
                           reason="Explicit approved architecture and plan mapping; review before creating a working revision" if changed else "Architecture and plan already contain the approved values")
        except ValueError as error:
            row.update(status="blocked", reason=str(error))
            blockers.append(f"{rule['id']}: {error}")
        rules.append(row)
    if changes:
        for name in ("architecture_input", "plan"):
            if name not in projected:
                blockers.append(f"Derived {name} module is missing")
            else:
                blockers.extend(f"Derived {name} schema: " + error for error in _schema_errors(projected[name], schema_root, name))
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
        edited = {}
        for kind in ("architecture_input", "plan"):
            module = next(item for item in manifest["modules"] if item["module_type"] == kind)
            path = root / module["path"]
            edited[kind] = json.loads(path.read_text(encoding="utf-8")) if path.suffix.lower() == ".json" else yaml.safe_load(path.read_text(encoding="utf-8"))
        for change in preview["changes"]:
            target = change["target"]
            _target(edited, target)[target["field"]] = copy.deepcopy(change["after"])
        changed_kinds = {"plan" if change["target"]["collection"].startswith("plan_") else "architecture_input"
                         for change in preview["changes"]}
        for kind in changed_kinds:
            document = edited[kind]
            module = next(item for item in manifest["modules"] if item["module_type"] == kind)
            path = root / module["path"]
            path.write_text(json.dumps(document, ensure_ascii=False, indent=2) if path.suffix.lower() == ".json" else yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8", newline="\n")
        audit_ref = f"architecture/derivations/{preview['preview_sha256']}.json"
        audit_path = root / audit_ref
        if audit_path.exists():
            raise ValueError("This exact derivation review was already recorded")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit = {**preview, "record_type": "reviewed_architecture_and_plan_derivation", "reviewed_by": payload["actor"],
                 "reviewed_at": datetime.now(timezone.utc).isoformat(), "review_rationale": payload["rationale"].strip(),
                 "authority": "Applies explicit existing approved decisions to existing architecture and plan fields only. Not package approval, release or tenant authorization."}
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
