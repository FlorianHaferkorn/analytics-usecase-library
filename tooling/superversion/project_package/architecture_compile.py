"""Revision-bound architecture projection and bounded, non-executing target outputs.

This deliberately does not call derive_blueprint: its library heuristics invent
names, ingestion choices and serving defaults absent from project contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .compiler_input import build_compiler_input
from .hashes import canonical_sha256
from .release import release_input
from .repository import ProjectPackageRevisionRepository
from .use_case_delivery import render_delivery_document

SOURCE = "https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace"
VERSION = "1.0.0"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def compile_architecture(compiler_input: dict[str, Any], revision_hash: str) -> dict[str, Any]:
    """Project only declared relationships; reference reports are not target reports."""
    modules = compiler_input["modules"]
    architecture = modules.get("architecture_input")
    delivery = modules.get("use_case_delivery")
    project = compiler_input["package"]["project_ref"]
    if delivery and delivery["project_ref"] != project:
        raise ValueError("Use-case delivery belongs to a different project")
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    blockers = list(compiler_input["readiness"]["blockers"])
    if not architecture:
        blockers.append("architecture_input_missing")
    if not delivery or not delivery["use_cases"]:
        blockers.append("use_case_delivery_missing")
    for use_case in (delivery or {}).get("use_cases", []):
        prefix = use_case["id"] + ":"
        common = {"domain_ref": use_case["domain_ref"], "use_case_ref": use_case["id"]}
        for boundary in ("canonical", "fallback", "excluded"):
            for source in use_case["source_contract"][boundary]:
                nodes.append({"id": prefix + source["id"], "label": source["source_system"] + "." + source["source_object"],
                              "kind": "source", "layer": "source", **common,
                              "details": {**source, "boundary": boundary}})
        for product in use_case["data_products"]:
            nodes.append({"id": prefix + product["id"], "label": product["name"], "kind": "data_product",
                          "layer": product["layer"], **common, "details": product})
            for ref in product["source_refs"]:
                edges.append({"id": prefix + ref + ":lineage:" + product["id"], "source": prefix + ref,
                              "target": prefix + product["id"], "kind": "declared_lineage", "label": "Declared source"})
        for transform in use_case["transformations"]:
            nodes.append({"id": prefix + transform["id"], "label": transform["id"], "kind": "transformation",
                          "layer": transform["to_layer"], **common, "details": transform})
            for ref in transform["input_refs"]:
                edges.append({"id": prefix + ref + ":input:" + transform["id"], "source": prefix + ref,
                              "target": prefix + transform["id"], "kind": "transformation", "label": "Input"})
            for ref in transform["output_refs"]:
                edges.append({"id": prefix + transform["id"] + ":output:" + ref, "source": prefix + transform["id"],
                              "target": prefix + ref, "kind": "transformation", "label": "Output"})
        for report in use_case["reference_reports"]:
            nodes.append({"id": prefix + report["id"], "label": report["name"], "kind": "reference_report",
                          "layer": "reference", **common, "details": report})
        blockers.extend(f"{use_case['id']}:{gate['id']}" for gate in use_case["open_gates"]
                        if gate["status"]["state"] in {"open", "proposed", "derived"})
    ids = [node["id"] for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Architecture has duplicate object identifiers")
    if any(edge["source"] not in ids or edge["target"] not in ids for edge in edges):
        raise ValueError("Architecture contains unresolved object references")
    workspace_blockers = _workspace_blockers(architecture, modules["decision_set"])
    workspaces = (architecture or {}).get("physical_workspaces", [])
    shown_workspaces = set()
    for workspace in workspaces:
        if workspace["id"] in shown_workspaces:
            continue  # Keep review available while the workspace target reports duplicate contracts.
        shown_workspaces.add(workspace["id"])
        nodes.append({"id": "workspace:" + workspace["id"], "label": workspace["name"], "kind": "workspace",
                      "domain_ref": workspace["domain_ref"], "layer": workspace["environment"], "details": workspace})
    workspace_by_id = {workspace["id"]: workspace for workspace in workspaces}
    for item in (architecture or {}).get("physical_items", []):
        workspace = workspace_by_id.get(item["workspace_ref"])
        if not workspace or item["environment"] != workspace["environment"]:
            raise ValueError("Physical item workspace or environment reference mismatch")
        # Definition payloads belong to generated files, not graph tooltips.
        details = {key: value for key, value in item.items() if key != "definition"}
        details["definition_parts"] = [part["path"] for part in item["definition"]["parts"]]
        nodes.append({"id": "item:" + item["id"], "label": item["name"], "kind": "native_item",
                      "domain_ref": workspace["domain_ref"], "layer": item["environment"], "details": details})
        edges.append({"id": "ownership:" + item["id"], "source": "workspace:" + item["workspace_ref"],
                      "target": "item:" + item["id"], "kind": "ownership", "label": "Contains"})
        for dependency in item["depends_on"]:
            edges.append({"id": "dependency:" + dependency + ":" + item["id"], "source": "item:" + dependency,
                          "target": "item:" + item["id"], "kind": "dependency", "label": "Required before"})
    batch = modules.get("batch_ingestion")
    if batch:
        from .batch_ingestion import describe_contract
        batch_view = describe_contract(batch)
        blockers.extend("batch_ingestion:" + reason for reason in batch_view["blockers"])
        prefix = "batch:" + batch["id"] + ":"
        for node in batch_view["graph"]["nodes"]:
            nodes.append({**node, "id": prefix + node["id"], "domain_ref": batch["domain"],
                          "use_case_ref": "batch:" + batch["id"],
                          "details": {"contract_ref": batch["id"], "scope": "local_batch_contract_not_deployed_fabric_item",
                                      "description": node["details"]}})
        for edge in batch_view["graph"]["edges"]:
            edges.append({**edge, "id": prefix + edge["id"], "source": prefix + edge["source"], "target": prefix + edge["target"]})
    all_ids = [node["id"] for node in nodes]
    if len(all_ids) != len(set(all_ids)) or any(edge["source"] not in all_ids or edge["target"] not in all_ids for edge in edges):
        raise ValueError("Architecture has duplicate identifiers or unresolved physical references")
    return {
        "schema_version": VERSION, "project_ref": project, "revision_hash": revision_hash,
        "compiler_input_sha256": canonical_sha256(compiler_input),
        "architecture": architecture, "use_cases": (delivery or {}).get("use_cases", []),
        "graph": {"nodes": sorted(nodes, key=lambda n: n["id"]), "edges": sorted(edges, key=lambda e: e["id"])},
        "readiness": {"review_ready": bool(nodes or architecture), "release_ready": False,
                      "apply_ready": False, "blockers": sorted(set(blockers + ["tenant_apply_and_verification_not_implemented"]))},
        "outputs": [
            {"id": "architecture_bundle", "label": "Architecture and delivery specification", "status": "ready" if nodes or architecture else "blocked",
             "reason": "Revision-bound JSON graph, existing use-case architecture documents and readiness manifest; not deployment code."},
            {"id": "fabric_workspace_requests", "label": "Fabric workspace creation request bodies",
             "status": "blocked" if workspace_blockers else "ready",
             "reason": "; ".join(workspace_blockers) or "Explicitly declared workspaces only. No items, security roles, data or CI/CD are created."},
        ],
        "provenance": {"compiler": "project_package.architecture_compile/" + VERSION,
                       "module_locks": compiler_input["provenance"]["module_locks"], "workspace_api_reference": SOURCE},
    }


def _workspace_blockers(architecture: dict | None, decisions: dict) -> list[str]:
    if not architecture or not architecture.get("physical_workspaces"):
        return ["No explicit physical_workspaces contract"]
    errors = []
    if architecture["stack"] not in {"fabric", "microsoft_fabric"}:
        errors.append("Target stack is not fabric")
    if not architecture["environments"]["accepted"]:
        errors.append("Environment decision is not accepted")
    domains = {domain["id"] for domain in architecture["domains"] if domain["delivery_scope"] != "out_of_scope"}
    accepted = {item["id"] for item in decisions["instances"] if item["approval"]["state"] == "approved"}
    if architecture["environments"]["decision_ref"] not in accepted:
        errors.append("Environment decision reference is not approved")
    identities, names = set(), set()
    for workspace in architecture["physical_workspaces"]:
        if workspace["id"] in identities or workspace["name"].casefold() in names:
            errors.append("Duplicate workspace identifier or name")
        identities.add(workspace["id"])
        names.add(workspace["name"].casefold())
        if workspace["domain_ref"] not in domains:
            errors.append(f"{workspace['id']}: unresolved or excluded domain")
        if workspace["environment"] not in architecture["environments"]["recommended"]:
            errors.append(f"{workspace['id']}: environment is outside accepted scope")
        if set(workspace["decision_refs"]) - accepted:
            errors.append(f"{workspace['id']}: decision references are not approved")
        if workspace["name"].strip() != workspace["name"] or workspace["name"].casefold() == "admin monitoring":
            errors.append(f"{workspace['id']}: invalid or reserved workspace name")
    return sorted(set(errors))


def read_architecture(repository: ProjectPackageRevisionRepository, project_ref: str, revision: str | None) -> dict:
    record = repository.get(revision)
    if record.project_ref != project_ref:
        raise ValueError("Package project_ref does not match selected project")
    view = compile_architecture(build_compiler_input(record.package_root, repository.schema_root), record.revision_hash)
    try:
        release_input(repository, project_ref, record.revision_hash)
        view["readiness"]["release_ready"] = True
    except ValueError as error:
        view["readiness"]["blockers"].append(str(error))
    return view


def build_architecture_output(repository: ProjectPackageRevisionRepository, project_ref: str, revision: str, target: str) -> dict:
    """An existing release attestation is mandatory; never grants approval or applies."""
    if target not in {"architecture_bundle", "fabric_workspace_requests"}:
        raise ValueError("Unsupported project architecture target")
    released = release_input(repository, project_ref, revision)
    compiler = released["compiler_input"]
    from .decision_derivation import compile_derivation

    review = compile_derivation(compiler, revision, repository.schema_root)
    decision_impacts = []
    for evaluated in review["rules"]:
        if evaluated["status"] != "unchanged":
            continue  # A selected, unresolved rule cannot cross the release gate.
        authored = next(rule for rule in compiler["modules"]["architecture_input"]["decision_rules"] if rule["id"] == evaluated["id"])
        if not authored.get("plan_effects"):
            continue
        decision_impacts.append({
            "decision_ref": authored["decision_ref"], "decision_revision": authored["decision_revision"],
            "rule_id": authored["id"], "review_state": "reflected_in_released_input",
            "architecture_target": authored["target"],
            "plan_contract_checks": [{"target": effect["target"], "expected_value_sha256": canonical_sha256(effect["value"]),
                                      "result": "passed_in_released_input"} for effect in authored["plan_effects"]],
            "derivation_approves_named_staffing_or_cost": False,
            "test_scope": "static_package_contract_only_not_tenant_or_customer_acceptance",
        })
    view = compile_architecture(compiler, revision)
    view["readiness"]["release_ready"] = True
    selected = next(item for item in view["outputs"] if item["id"] == target)
    if selected["status"] != "ready":
        raise ValueError("Target blocked: " + selected["reason"])
    files = {"architecture.json": _json(view)}
    if decision_impacts:
        files["delivery/decision-impact-checks.json"] = _json({
            "schema_version": VERSION, "project_ref": project_ref, "revision_hash": revision,
            "compiler_input_sha256": view["compiler_input_sha256"],
            "checks": sorted(decision_impacts, key=lambda item: item["rule_id"]),
        })
    if target == "architecture_bundle":
        delivery = compiler["modules"].get("use_case_delivery")
        if delivery:
            files.update({"specifications/" + path: content for path, content in render_delivery_document(delivery).items()})
    else:
        for workspace in view["architecture"]["physical_workspaces"]:
            body = {"displayName": workspace["name"], "capacityId": workspace["capacity_id"], "domainId": workspace["domain_id"]}
            if "description" in workspace:
                body["description"] = workspace["description"]
            files[f"fabric/workspaces/{workspace['id']}.request.json"] = _json(body)
        files["fabric/request-plan.json"] = _json({"operation": "create_workspace", "method": "POST", "path": "/v1/workspaces",
            "request_files": sorted(path for path in files if path.endswith(".request.json")),
            "api_reference": SOURCE, "scope": "Only the explicitly declared workspace list; not whole-project provisioning",
            "preflight": ["Authenticate to the intended tenant; validate capacity and domain IDs and permissions",
                          "List existing workspaces including all pages; do not recreate or overwrite existing names",
                          "Obtain separate tenant apply approval; record response IDs and verify capacity/domain assignments"],
            "unimplemented": ["No executor, retry/LRO handler or idempotent reconciliation is included", "No item definitions, data, security, identity, CI/CD or acceptance tests"]})
    manifest = {"schema_version": VERSION, "project_ref": project_ref, "revision_hash": revision, "target": target,
                "release_record_sha256": released["release"]["record_sha256"], "compiler_input_sha256": view["compiler_input_sha256"],
                "decision_impact_rule_ids": sorted(item["rule_id"] for item in decision_impacts),
                "apply_ready": False, "files": [{"path": path, "sha256": hashlib.sha256(content.encode()).hexdigest()}
                                               for path, content in sorted(files.items())]}
    files["output-manifest.json"] = _json(manifest)
    return {"output_type": target, "manifest": manifest, "files": [{"path": path, "content": content} for path, content in sorted(files.items())],
            "limitations": ["Generated from released inputs; not tenant deployment authorization", "No live tenant action or runtime verification performed"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--project-ref", required=True)
    parser.add_argument("--revision")
    parser.add_argument("--target", choices=["architecture_bundle", "fabric_workspace_requests"])
    args = parser.parse_args()
    try:
        repository = ProjectPackageRevisionRepository(args.repository, args.schemas)
        if args.target and not args.revision:
            raise ValueError("Target generation requires an explicit pinned revision")
        result = build_architecture_output(repository, args.project_ref, args.revision, args.target) if args.target else read_architecture(repository, args.project_ref, args.revision)
        print(_json({"ok": True, "value": result}))
        return 0
    except (ValueError, OSError, AssertionError) as error:
        print(_json({"ok": False, "error": str(error) or "No stored project package revision is available", "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
