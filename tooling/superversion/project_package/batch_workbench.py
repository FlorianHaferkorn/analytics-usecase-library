"""Version-pinned batch authoring and local tests; never platform execution."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .compiler_input import build_compiler_input
from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository, StaleProjectPackageDraftError

TARGET = "batch_ingestion_bundle"


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _current(repository, project_ref, revision):
    if not isinstance(project_ref, str) or not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{64}", revision):
        raise ValueError("Explicit project and revision are required")
    record = repository.get(revision)
    if record.project_ref != project_ref:
        raise ValueError("Package belongs to a different project")
    head = repository.head()
    if not head or head.revision_hash != revision:
        raise StaleProjectPackageDraftError("Package HEAD changed; refresh and review the current revision")
    return record


def inspect_batch(repository, project_ref, revision):
    from .batch_ingestion import describe_contract
    record = _current(repository, project_ref, revision)
    contract = build_compiler_input(record.package_root, repository.schema_root)["modules"].get("batch_ingestion")
    return {"project_ref": project_ref, "revision_hash": revision, "contract": contract,
            "view": describe_contract(contract) if contract else None, "is_current_revision": True,
            "tenant_actions_performed": False}


def _changes(before, after, path="contract"):
    if isinstance(before, dict) and isinstance(after, dict):
        return [change for key in sorted(before.keys() | after.keys())
                for change in _changes(before.get(key), after.get(key), path + "." + key)]
    return [] if before == after else [{"path": path, "before": before, "after": after}]


def preview_batch(repository, project_ref, revision, contract):
    from .batch_ingestion import describe_contract
    prior = inspect_batch(repository, project_ref, revision)
    view = describe_contract(contract)
    blockers = list(view.get("blockers", []))
    changes = _changes(prior["contract"], contract)
    value = {"project_ref": project_ref, "revision_hash": revision, "contract": copy.deepcopy(contract),
             "before": prior["contract"], "view": view, "changes": changes, "blockers": blockers,
             "can_save": bool(changes) and not blockers, "state_after_save": "working",
             "release_required": True, "tenant_actions_performed": False}
    return {**value, "preview_hash": canonical_sha256(value)}


def save_batch(repository, payload):
    if set(payload) != {"project_ref", "revision_hash", "contract", "preview_hash", "actor", "rationale", "confirmed"} or payload["confirmed"] is not True:
        raise ValueError("Exact reviewed save confirmation is required")
    if not isinstance(payload["actor"], str) or not 1 <= len(payload["actor"].strip()) <= 320:
        raise ValueError("Authenticated actor is required")
    if not isinstance(payload["rationale"], str) or not 20 <= len(payload["rationale"].strip()) <= 4000:
        raise ValueError("Review rationale requires 20 to 4000 characters")
    preview = preview_batch(repository, payload["project_ref"], payload["revision_hash"], payload["contract"])
    if payload["preview_hash"] != preview["preview_hash"]:
        raise ValueError("Preview changed; review the current before and after values")
    if not preview["can_save"]:
        raise ValueError("No valid changed contract is ready to save")
    with tempfile.TemporaryDirectory(prefix="batch-workbench-") as temporary:
        root = repository.checkout(Path(temporary) / "package", payload["revision_hash"])
        manifest_path = root / "package.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        module = next((row for row in manifest["modules"] if row["module_type"] == "batch_ingestion"), None)
        if module is None:
            module = {"module_type": "batch_ingestion", "path": "capabilities/batch_ingestion.json",
                      "schema_id": json.loads((repository.schema_root / "project_batch_ingestion.schema.json").read_text(encoding="utf-8"))["$id"]}
            if (root / module["path"]).exists():
                raise ValueError("Reserved batch contract path is already occupied")
            manifest["modules"].append(module)
        path = root / module["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        content = _json(payload["contract"]) if path.suffix.lower() == ".json" else yaml.safe_dump(payload["contract"], sort_keys=False, allow_unicode=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        module["sha256"] = canonical_sha256(payload["contract"])
        audit_ref = f"capabilities/batch-reviews/{preview['preview_hash']}.json"
        audit_path = root / audit_ref
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit = {**preview, "record_type": "reviewed_batch_contract", "reviewed_by": payload["actor"].strip(),
                 "reviewed_at": datetime.now(timezone.utc).isoformat(), "rationale": payload["rationale"].strip(),
                 "authority": "Draft authoring only. Not input approval, release, customer acceptance or tenant authorization."}
        with audit_path.open("x", encoding="utf-8") as handle:
            handle.write(_json(audit))
        manifest["state"] = "working"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
        saved = repository.commit_draft(root, expected_head_hash=payload["revision_hash"])
    return {"project_ref": saved.project_ref, "revision_hash": saved.revision_hash,
            "parent_revision_hash": saved.parent_revision_hash, "audit_ref": audit_ref,
            "state": "working", "release_required": True, "tenant_actions_performed": False}


def test_batch(repository, project_ref, revision, batches):
    from .batch_ingestion import run_batch
    saved = inspect_batch(repository, project_ref, revision)
    if not saved["contract"]:
        raise ValueError("Save a supported contract before running local tests")
    if not isinstance(batches, list) or not 1 <= len(batches) <= 3:
        raise ValueError("Provide one to three local batches")
    state, results = None, []
    for batch in batches:
        if not isinstance(batch, dict) or set(batch) != {"batch_id", "rows"} or not isinstance(batch["rows"], list) or len(batch["rows"]) > 1000:
            raise ValueError("Each batch requires batch_id and at most 1000 rows")
        try:
            result = run_batch(saved["contract"], batch["rows"], state, batch_id=batch["batch_id"])
        except (ValueError, TypeError, KeyError):
            raise ValueError("Local batch validation failed; check schema, keys, watermark and batch identity") from None
        state = result["state"]
        results.append(result)
    return {"project_ref": project_ref, "revision_hash": revision,
            "contract_hash": canonical_sha256(saved["contract"]), "evidence_kind": "local_check",
            "tenant_actions_performed": False, "batches": results,
            "limitations": ["In-memory test input only; no source, SQL, Spark or Fabric engine was contacted.",
                            "Rows and state are not persisted. This result is not tenant verification or release approval."]}


def batch_target(compiler):
    from .batch_ingestion import describe_contract
    contract = compiler["modules"].get("batch_ingestion")
    blockers = describe_contract(contract).get("blockers", []) if contract else ["No batch_ingestion contract is saved"]
    return {"id": TARGET, "label": "Local batch ingestion implementation and contract",
            "status": "blocked" if blockers else "ready",
            "reason": "; ".join(blockers) or "Self-contained local Python implementation; not a Fabric pipeline or tenant deployment."}


def build_batch_output(repository, project_ref, revision):
    from .batch_ingestion import describe_contract, export_bundle
    from .release import release_input
    released = release_input(repository, project_ref, revision)
    compiler = released["compiler_input"]
    target = batch_target(compiler)
    if target["status"] != "ready":
        raise ValueError("Target blocked: " + target["reason"])
    contract = compiler["modules"]["batch_ingestion"]
    provenance = {"project_ref": project_ref, "revision_hash": revision,
                  "contract_hash": canonical_sha256(contract), "compiler_input_sha256": canonical_sha256(compiler),
                  "release_record_sha256": released["release"]["record_sha256"]}
    files = export_bundle(contract, provenance)
    if isinstance(files, list):
        files = {row["path"]: row["content"] for row in files}
    files["delivery-work-plan.json"] = _json({**provenance, "authority": "Derived implementation checklist, not an approved commercial estimate or replacement for the Project Plan module",
        "work_packages": [
            {"id": "validate_local_batches", "title": "Validate representative batch inputs and recovery cases",
             "scope": f"{contract['load']['mode']} loading into {contract['target']['schema']}.{contract['target']['table']}",
             "acceptance": "Schema errors, repeats and updates produce the expected result without advancing rejected state.", "effort": None, "status": "requires_evidence"},
            {"id": "prove_source_extraction", "title": "Implement and prove the actual source extraction contract",
             "scope": contract["source"]["landing_path"], "acceptance": "A reviewed extractor supplies complete snapshots or supported integer-version batches; connection identity and source permissions are proven.", "effort": None, "status": "not_implemented"},
            {"id": "bind_and_verify_environments", "title": "Bind and verify each approved target environment",
             "scope": contract["environments"], "acceptance": "Real target IDs, identities, least-privilege access and runtime state persistence are validated under a separate scoped tenant authorization.", "effort": None, "status": "tenant_not_verified"},
            {"id": "prove_platform_runtime", "title": "Implement the platform writer, orchestration and recovery boundary",
             "scope": "No Fabric writer, Delta/CDF handling or transaction guarantee is supplied by this local bundle.",
             "acceptance": "Platform implementation passes crash, replay, schema and data reconciliation tests before customer acceptance.", "effort": None, "status": "not_implemented"}]})
    manifest = {"schema_version": "1.0.0", **provenance, "target": TARGET, "apply_ready": False,
                "tenant_actions_performed": False,
                "files": [{"path": path, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()} for path, content in sorted(files.items())]}
    files["output-manifest.json"] = _json(manifest)
    _current(repository, project_ref, revision)
    return {"output_type": TARGET, "manifest": manifest,
            "files": [{"path": path, "content": content} for path, content in sorted(files.items())],
            "limitations": describe_contract(contract).get("limitations", [])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--mode", choices=["inspect", "preview", "save", "test", "export"], required=True)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(1_000_001)
        if len(raw.encode("utf-8")) > 1_000_000:
            raise ValueError("Request is too large")
        payload = json.loads(raw)
        base = {"project_ref", "revision_hash"}
        extra = {"inspect": set(), "preview": {"contract"}, "save": {"contract", "preview_hash", "actor", "rationale", "confirmed"}, "test": {"batches"}, "export": set()}[args.mode]
        if not isinstance(payload, dict) or set(payload) != base | extra:
            raise ValueError("Invalid request fields")
        repo = ProjectPackageRevisionRepository(args.repository, args.schemas)
        project, revision = payload["project_ref"], payload["revision_hash"]
        if args.mode == "inspect": value = inspect_batch(repo, project, revision)
        elif args.mode == "preview": value = preview_batch(repo, project, revision, payload["contract"])
        elif args.mode == "save": value = save_batch(repo, payload)
        elif args.mode == "test": value = test_batch(repo, project, revision, payload["batches"])
        else: value = build_batch_output(repo, project, revision)
        print(_json({"ok": True, "value": value}))
        return 0
    except StaleProjectPackageDraftError:
        print(_json({"ok": False, "error": "Package HEAD changed; refresh and review the current revision", "status": 409}))
    except (ValueError, OSError, KeyError, TypeError):
        print(_json({"ok": False, "error": "Batch request failed validation or a required approval/release gate. Refresh the contract and review its blockers.", "status": 422}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
