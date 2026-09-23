"""Pure local item/binding contract rehearsal, never a Fabric executor.

Only native-definition transport and declared JSON-pointer replacements are
checked. Fake IDs are deliberately invalid Fabric IDs. No credentials, network,
subprocess, item execution, or persistence are used by this module.
"""
from __future__ import annotations

import base64
import copy
import json
import re

from .hashes import canonical_sha256
from .item_compile import _parts, compile_item_plan


LIMITATIONS = [
    "Simulation only: no Fabric endpoint accepted these definitions or bindings.",
    "Native envelope and required parts reuse the item compiler; full activity, TMDL, PBIR and notebook semantics are not validated.",
    "Only explicit JSON-pointer bindings within the same workspace and environment are supported; source-code and TMDL replacement are blocked.",
    "Synthetic sim_ IDs are not deployable IDs. Lakehouse, table, security, data loading, refresh and identity operations are not simulated here.",
    "State is an in-memory test fixture, not signed tenant evidence. Uncertain attempts require reconciliation and are never automatically retried.",
]


def _pointer_parent(document, pointer: str):
    if not isinstance(pointer, str) or not pointer.startswith("/") or re.search(r"~(?![01])", pointer):
        raise ValueError("An exact non-root JSON pointer is required")
    segments = [segment.replace("~1", "/").replace("~0", "~") for segment in pointer.split("/")[1:]]
    parent = document
    for segment in segments[:-1]:
        parent = parent[_pointer_key(parent, segment)]
    key = _pointer_key(parent, segments[-1])
    return parent, key


def _pointer_key(parent, segment):
    if isinstance(parent, list):
        if not re.fullmatch(r"0|[1-9][0-9]*", segment):
            raise ValueError("Invalid JSON array index")
        index = int(segment)
        if index >= len(parent):
            raise ValueError("Unresolved JSON array index")
        return index
    if not isinstance(parent, dict) or segment not in parent:
        raise ValueError("Unresolved JSON pointer")
    return segment


def simulate_item_contract(compiler_input: dict, workspace_map: list[dict], bindings: list[dict],
                           state: dict | None = None, *, uncertain_item_id: str | None = None) -> dict:
    """Rehearse create/noop/conflict/binding/uncertain behavior without side effects.

    workspace_map: {workspace_ref, environment, physical_id: 'sim_workspace_...'}.
    bindings: {item_ref, part_path, json_pointer, expected_value: string,
               target_kind: 'workspace'|'item', target_ref}.
    Pass the returned state back for a deterministic repeat. Invalid contracts
    return blocked without changing input state. Partial simulated attempts are
    explicit in operations and the returned state; no rollback is implied.
    """
    result = {"schema_version": "1.0.0", "evidence_kind": "simulation", "tenant_actions_performed": False,
              "live_apply_allowed": False, "accepted_by_fabric": False, "status": "blocked",
              "operations": [], "resolved_bindings": [], "state": copy.deepcopy(state),
              "limitations": list(LIMITATIONS)}
    try:
        _simulate(compiler_input, workspace_map, bindings, state, uncertain_item_id, result)
    except (ValueError, KeyError, TypeError, IndexError, UnicodeDecodeError) as error:
        # Deliberately do not echo native payloads, source strings or credentials.
        result["status"] = "blocked"
        result["reason"] = str(error) if isinstance(error, ValueError) else "Malformed item simulation contract"
    return result


def _simulate(compiler_input, workspace_map, bindings, state, uncertain_item_id, result):
    plan = compile_item_plan(compiler_input)
    project = plan["project_ref"]
    if not isinstance(project, str) or not project:
        raise ValueError("Project scope is required")
    if not isinstance(workspace_map, list) or not isinstance(bindings, list):
        raise ValueError("Workspace map and binding list are required")
    architecture = compiler_input["modules"]["architecture_input"]
    workspaces = {entry["id"]: entry for entry in architecture["physical_workspaces"]}
    items = {entry["id"]: entry for entry in architecture["physical_items"]}
    mapped, physical = {}, set()
    for entry in workspace_map:
        if not isinstance(entry, dict) or set(entry) != {"workspace_ref", "environment", "physical_id"}:
            raise ValueError("Unexpected workspace map fields")
        ref = entry["workspace_ref"]
        if ref not in workspaces or entry["environment"] != workspaces[ref]["environment"]:
            raise ValueError("Workspace map has an unresolved or wrong environment scope")
        if not isinstance(entry["physical_id"], str) or not re.fullmatch(r"sim_workspace_[a-zA-Z0-9_]{1,80}", entry["physical_id"]):
            raise ValueError("Only synthetic sim_workspace_ IDs are allowed")
        if ref in mapped or entry["physical_id"] in physical:
            raise ValueError("Duplicate workspace mapping")
        mapped[ref] = entry
        physical.add(entry["physical_id"])
    if set(entry["workspace_ref"] for entry in items.values()) - set(mapped):
        raise ValueError("An item workspace has no explicit simulated physical ID")
    if uncertain_item_id is not None and uncertain_item_id not in items:
        raise ValueError("Uncertain attempt references an unknown item")
    scope_hash = canonical_sha256({"project_ref": project, "workspace_map": sorted(workspace_map, key=lambda entry: entry["workspace_ref"])})
    next_state = {"project_ref": project, "scope_sha256": scope_hash, "records": {}} if state is None else copy.deepcopy(state)
    if not isinstance(next_state, dict) or set(next_state) != {"project_ref", "scope_sha256", "records"} or next_state["project_ref"] != project or next_state["scope_sha256"] != scope_hash or not isinstance(next_state["records"], dict):
        raise ValueError("Simulation state belongs to a different project or workspace scope")
    ids = {ref: "sim_item_" + canonical_sha256({"scope": scope_hash, "item_ref": ref})[:24] for ref in items}
    for ref, record in next_state["records"].items():
        if ref not in items or not isinstance(record, dict) or set(record) != {"physical_id", "fingerprint", "status"} or record["physical_id"] != ids[ref] or record["status"] not in {"created", "uncertain"} or not isinstance(record["fingerprint"], str) or not re.fullmatch(r"[0-9a-f]{64}", record["fingerprint"]):
            raise ValueError("Simulation state has unsupported or conflicting records")
    definitions = {ref: copy.deepcopy(item["definition"]) for ref, item in items.items()}
    seen = set()
    resolved = []
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"item_ref", "part_path", "json_pointer", "expected_value", "target_kind", "target_ref"}:
            raise ValueError("Unexpected item binding fields")
        ref = binding["item_ref"]
        if ref not in items:
            raise ValueError("Binding source item is unresolved")
        item = items[ref]
        target = binding["target_ref"]
        if binding["target_kind"] == "workspace":
            if target != item["workspace_ref"] or target not in mapped:
                raise ValueError("Workspace binding is unresolved or outside the item workspace")
            replacement = mapped[target]["physical_id"]
        elif binding["target_kind"] == "item":
            if target not in items or target not in item["depends_on"]:
                raise ValueError("Item binding must reference a declared dependency")
            if items[target]["workspace_ref"] != item["workspace_ref"] or items[target]["environment"] != item["environment"]:
                raise ValueError("Cross-workspace or cross-environment binding is not supported")
            replacement = ids[target]
        else:
            raise ValueError("Unsupported binding target family")
        path, pointer = binding["part_path"], binding["json_pointer"]
        if not isinstance(path, str) or not path.endswith((".json", ".pbir", ".pbism", ".bim", ".ipynb")):
            raise ValueError("Binding parser unavailable for source-code or TMDL parts")
        identity = (ref, path, pointer)
        if identity in seen:
            raise ValueError("Duplicate binding pointer")
        seen.add(identity)
        # Use the existing decoder/path validation before changing only this field.
        parts = _parts({**item, "definition": definitions[ref]})
        if path not in parts:
            raise ValueError("Binding part is unresolved")
        document = json.loads(parts[path])
        parent, key = _pointer_parent(document, pointer)
        expected = binding["expected_value"]
        if not isinstance(expected, str) or not expected or type(parent[key]) is not str or parent[key] != expected:
            raise ValueError("Exact JSON-pointer placeholder assertion failed")
        parent[key] = replacement
        encoded = base64.b64encode(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).decode()
        next(part for part in definitions[ref]["parts"] if part["path"] == path)["payload"] = encoded
        resolved.append({"item_ref": ref, "part_path": path, "json_pointer": pointer, "target_kind": binding["target_kind"], "target_ref": target, "resolved_value": replacement})
    # Conflicts anywhere in the batch block before any new simulated attempt.
    fingerprints = {ref: canonical_sha256({"item": {**item, "definition": definitions[ref]}, "workspace_id": mapped[item["workspace_ref"]]["physical_id"]}) for ref, item in items.items()}
    for ref, record in next_state["records"].items():
        if record["fingerprint"] != fingerprints[ref]:
            raise ValueError("Existing simulated item conflicts with the requested definition or binding")
    result["project_ref"] = project
    result["resolved_bindings"] = resolved
    result["state"] = next_state
    # Reconciliation blocks the whole batch, including unrelated new items.
    # Otherwise a repeat could keep making progress around an unknown outcome.
    uncertain_records = sorted(ref for ref, record in next_state["records"].items() if record["status"] == "uncertain")
    if uncertain_records:
        result["operations"] = [{"item_ref": ref, "workspace_id": mapped[items[ref]["workspace_ref"]]["physical_id"],
                                 "physical_id": ids[ref], "definition_sha256": fingerprints[ref],
                                 "status": "reconciliation_required", "attempted": False} for ref in uncertain_records]
        result["status"] = "reconciliation_required"
        return
    for item in plan["ordered_items"]:
        ref = item["id"]
        record = next_state["records"].get(ref)
        operation = {"item_ref": ref, "workspace_id": mapped[item["workspace_ref"]]["physical_id"], "physical_id": ids[ref], "definition_sha256": fingerprints[ref]}
        if record:
            result["operations"].append({**operation, "status": "noop", "attempted": False})
            continue
        uncertain = ref == uncertain_item_id
        next_state["records"][ref] = {"physical_id": ids[ref], "fingerprint": fingerprints[ref], "status": "uncertain" if uncertain else "created"}
        result["operations"].append({**operation, "status": "uncertain" if uncertain else "created", "attempted": True})
        if uncertain:
            result["status"] = "reconciliation_required"
            return
    result["status"] = "simulated"
