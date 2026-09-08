"""Explicit native Fabric definition transport; no invented implementation logic.

Only supplied parts are emitted. A release is required for outputs; target item
semantic validation, runtime binding and tenant authorization remain separate.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from .architecture_compile import _workspace_blockers
from .hashes import canonical_sha256
from .release import release_input
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
TARGET = "fabric_item_requests"
REFERENCES = {
    "CreateItem": "https://learn.microsoft.com/en-us/rest/api/fabric/core/items/create-item",
    "Notebook": "https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition",
    "DataPipeline": "https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition",
    "SemanticModel": "https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition",
    "Report": "https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/report-definition",
}
LIMITATIONS = [
    "Supplied native definition parts are preserved; business logic, measures, visuals and source mappings are not inferred.",
    "Definition envelope and required parts are validated; this is not full TMDL, PBIR, notebook or activity semantic validation.",
    "A verified workspace-ID map, credentials, target binding validation and separate tenant authorization are required before apply.",
    "Dependency order does not resolve physical item IDs. Environment assertions check exact JSON pointers locally; no tenant binding is verified. TMDL and source-code binding parsers are not included.",
    "No security-role configuration, LRO execution, data loading, runtime test or customer acceptance is performed.",
]


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _parts(item: dict) -> dict[str, bytes]:
    result = {}
    for part in item["definition"]["parts"]:
        path = part["path"]
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts or "\\" in path or ":" in path or str(parsed) != path or path == "." or path.casefold() in {key.casefold() for key in result}:
            raise ValueError(f"{item['id']}: invalid or duplicate definition part path")
        if part["payloadType"] != "InlineBase64":
            raise ValueError(f"{item['id']}: unsupported payload type")
        try:
            decoded = base64.b64decode(part["payload"], validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError(f"{item['id']}: invalid Base64 definition part") from error
        if not decoded:
            raise ValueError(f"{item['id']}: empty definition part")
        if path.endswith((".json", ".pbir", ".pbism", ".bim", ".ipynb")) or path == ".platform":
            try:
                json.loads(decoded)
            except (ValueError, UnicodeDecodeError) as error:
                raise ValueError(f"{item['id']}: invalid JSON in {path}") from error
        result[path] = decoded
    if ".platform" in result:
        platform = json.loads(result[".platform"])
        metadata = platform.get("metadata", {}) if isinstance(platform, dict) else {}
        if metadata.get("displayName", item["name"]) != item["name"] or metadata.get("type", item["type"]) != item["type"]:
            raise ValueError(f"{item['id']}: platform metadata conflicts with declared item name or type")
    return result


def _validate_definition(item: dict) -> None:
    parts = _parts(item)
    paths = set(parts) - {".platform"}
    kind = item["type"]
    format = item["definition"].get("format")
    if kind == "Notebook":
        if format not in {None, "FabricGitSource", "ipynb"}:
            raise ValueError(f"{item['id']}: unsupported notebook format")
        allowed = {path for path in paths if path.endswith(".ipynb")} if format == "ipynb" else paths & {"notebook-content.py", "notebook-content.sql", "notebook-content.scala", "notebook-content.r"}
        if len(paths) != 1 or len(allowed) != 1:
            raise ValueError(f"{item['id']}: notebook requires exactly one content part matching its format")
    elif kind == "DataPipeline":
        if format is not None or paths != {"pipeline-content.json"}:
            raise ValueError(f"{item['id']}: pipeline requires pipeline-content.json and no unrecognized format")
        pipeline = json.loads(parts["pipeline-content.json"])
        if not isinstance(pipeline, dict) or not isinstance(pipeline.get("properties"), dict):
            raise ValueError(f"{item['id']}: pipeline properties object is required")
    elif kind == "SemanticModel":
        tmdl = any(path.startswith("definition/") and path.endswith(".tmdl") for path in paths)
        tmsl = "model.bim" in paths
        if format not in {None, "TMDL", "TMSL"} or "definition.pbism" not in paths or tmdl == tmsl or (format == "TMSL" and not tmsl) or (format in {None, "TMDL"} and not tmdl):
            raise ValueError(f"{item['id']}: semantic model requires definition.pbism and exactly the declared TMDL or TMSL format")
    elif kind == "Report":
        pbir = any(path.startswith("definition/") and path.endswith(".json") for path in paths)
        legacy = "report.json" in paths
        if format not in {None, "PBIR", "PBIR-Legacy"} or "definition.pbir" not in paths or pbir == legacy or (format == "PBIR-Legacy" and not legacy) or (format in {None, "PBIR"} and not pbir):
            raise ValueError(f"{item['id']}: report requires definition.pbir and exactly the declared PBIR or PBIR-Legacy format")
    else:
        raise ValueError(f"{item['id']}: unsupported native definition type")
    for binding in item["environment_bindings"]:
        decoded = parts.get(binding["part_path"])
        try:
            if not binding["part_path"].endswith((".json", ".pbir", ".pbism", ".bim", ".ipynb")) and binding["part_path"] != ".platform":
                raise ValueError("Binding parser unavailable for this part type")
            value = json.loads(decoded) if decoded is not None else None
            pointer = binding["json_pointer"]
            if (pointer and not pointer.startswith("/")) or re.search(r"~(?![01])", pointer):
                raise ValueError("Invalid JSON pointer")
            for segment in pointer.split("/")[1:] if pointer else []:
                segment = segment.replace("~1", "/").replace("~0", "~")
                if isinstance(value, list):
                    if not re.fullmatch(r"0|[1-9][0-9]*", segment):
                        raise ValueError("Invalid JSON array index")
                    value = value[int(segment)]
                else:
                    value = value[segment]
            if decoded is None or type(value) is not type(binding["expected_value"]) or value != binding["expected_value"]:
                raise ValueError("Binding value mismatch")
        except (ValueError, TypeError, KeyError, IndexError, UnicodeDecodeError) as error:
            raise ValueError(f"{item['id']}: exact JSON-pointer environment assertion failed; source-code/TMDL bindings require a supported parser") from error


def compile_item_plan(compiler_input: dict) -> dict:
    architecture = compiler_input["modules"].get("architecture_input")
    if not architecture or not architecture.get("physical_items"):
        raise ValueError("No explicit physical_items contract")
    errors = _workspace_blockers(architecture, compiler_input["modules"]["decision_set"])
    if errors:
        raise ValueError("Workspace scope blocked: " + "; ".join(errors))
    workspaces = {item["id"]: item for item in architecture["physical_workspaces"]}
    items = architecture["physical_items"]
    indexed = {item["id"]: item for item in items}
    if len(indexed) != len(items):
        raise ValueError("Duplicate physical item identifier")
    accepted = {item["id"] for item in compiler_input["modules"]["decision_set"]["instances"] if item["approval"]["state"] == "approved"}
    names = set()
    for item in items:
        workspace = workspaces.get(item["workspace_ref"])
        if not workspace or item["environment"] != workspace["environment"]:
            raise ValueError(f"{item['id']}: workspace or environment reference mismatch")
        if not item["decision_refs"] or set(item["decision_refs"]) - accepted:
            raise ValueError(f"{item['id']}: decision references are not approved")
        name = (item["workspace_ref"], item["name"].casefold())
        if name in names or item["name"].strip() != item["name"]:
            raise ValueError(f"{item['id']}: duplicate or invalid item name")
        names.add(name)
        if any(ref not in indexed or indexed[ref]["environment"] != item["environment"] for ref in item["depends_on"]):
            raise ValueError(f"{item['id']}: unresolved or cross-environment item dependency")
        _validate_definition(item)
    remaining = set(indexed)
    order = []
    while remaining:
        batch = sorted(id for id in remaining if set(indexed[id]["depends_on"]) <= set(order))
        if not batch:
            raise ValueError("Cyclic physical item dependencies")
        order.extend(batch)
        remaining.difference_update(batch)
    return {"schema_version": VERSION, "project_ref": compiler_input["package"]["project_ref"],
            "operation": "create_declared_items", "method": "POST", "path_template": "/v1/workspaces/{workspaceId}/items",
            "ordered_items": [{"id": id, "workspace_ref": indexed[id]["workspace_ref"], "environment": indexed[id]["environment"],
                               "depends_on": indexed[id]["depends_on"], "request_file": f"fabric/items/{id}.request.json",
                               "environment_bindings": indexed[id]["environment_bindings"], "tenant_bindings_verified": False} for id in order],
            "workspace_resolution": "Resolve each declared workspace_ref to its verified target workspace ID before execution. No IDs are guessed.",
            "apply_ready": False, "validation_scope": "native_definition_transport_and_declared_dependencies",
            "references": REFERENCES, "limitations": LIMITATIONS}


def item_target(compiler_input: dict) -> dict:
    try:
        plan = compile_item_plan(compiler_input)
        return {"id": TARGET, "label": "Native Fabric item definition requests", "status": "ready",
                "reason": f"{len(plan['ordered_items'])} explicitly defined items, ordered by dependencies. Transport validation only; no tenant apply."}
    except (ValueError, KeyError, TypeError) as error:
        return {"id": TARGET, "label": "Native Fabric item definition requests", "status": "blocked", "reason": str(error)}


def build_item_output(repository: ProjectPackageRevisionRepository, project_ref: str, revision: str) -> dict:
    released = release_input(repository, project_ref, revision)
    compiler = released["compiler_input"]
    plan = compile_item_plan(compiler)
    files = {"fabric/item-plan.json": _json(plan)}
    for item in compiler["modules"]["architecture_input"]["physical_items"]:
        body = {"displayName": item["name"], "type": item["type"], "definition": item["definition"]}
        if "description" in item:
            body["description"] = item["description"]
        files[f"fabric/items/{item['id']}.request.json"] = _json(body)
    manifest = {"schema_version": VERSION, "project_ref": project_ref, "revision_hash": revision, "target": TARGET,
                "compiler_input_sha256": canonical_sha256(compiler), "release_record_sha256": released["release"]["record_sha256"],
                "apply_ready": False, "files": [{"path": path, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()} for path, content in sorted(files.items())]}
    files["output-manifest.json"] = _json(manifest)
    return {"output_type": TARGET, "manifest": manifest, "files": [{"path": path, "content": content} for path, content in sorted(files.items())], "limitations": LIMITATIONS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--project-ref", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        result = build_item_output(ProjectPackageRevisionRepository(args.repository, args.schemas), args.project_ref, args.revision)
        print(_json({"ok": True, "value": result}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(_json({"ok": False, "error": str(error), "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
