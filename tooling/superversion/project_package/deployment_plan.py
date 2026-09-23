"""Released, revision-bound workspace planning and create-only execution.

The CLI is deliberately read-only. The Python executor is a seam for a trusted,
authenticated operator/runner, not a public arbitrary-command endpoint.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Protocol
from urllib.parse import urlencode
from uuid import UUID

from .architecture_compile import _workspace_blockers
from .hashes import canonical_sha256
from .release import release_input
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
MAX_AGE = timedelta(minutes=15)
CAPABILITIES = [
    {"family": "workspaces", "status": "create_only", "reason": "Exact names, capacity/domain IDs; no updates, deletion or automatic adoption."},
    *[{"family": family, "status": "blocked", "reason": reason} for family, reason in [
        ("items", "This executor has no item definition deployment or binding verification."),
        ("security", "Identity and OneLake/semantic security need separate approved contracts and tests."),
        ("cicd", "Git and stage promotion need supported-item checks, binding rules and release evidence."),
        ("data", "Ingestion, refresh, quality and business acceptance are not workspace creation."),
    ]],
]


def _now(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("A timezone-aware time is required")
    return value.astimezone(timezone.utc)


def _time(value: str) -> datetime:
    try:
        return _now(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("Invalid evidence timestamp") from error


def _uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError("Explicit UUID required") from error


def _keys(value: dict, allowed: set, required: set | None = None) -> None:
    if not isinstance(value, dict) or set(value) - allowed or (required or allowed) - set(value):
        raise ValueError("Invalid or incomplete deployment evidence fields")


def validate_observed_state(value: dict, tenant_id: str, *, now: datetime | None = None) -> dict:
    """Validate a complete principal-visible inventory, never imply tenant-wide access."""
    _keys(value, {"tenant_id", "principal_id", "observed_at", "complete", "workspaces", "permissions"})
    if _uuid(value["tenant_id"]) != _uuid(tenant_id) or value["complete"] is not True:
        raise ValueError("Tenant mismatch or incomplete observed workspace inventory")
    age = _now(now) - _time(value["observed_at"])
    if age < timedelta(seconds=-30) or age > MAX_AGE:
        raise ValueError("Observed state is stale or dated in the future")
    principal = _uuid(value["principal_id"])
    permissions = value["permissions"]
    _keys(permissions, {"create_workspaces", "capacity_assign_ids", "domain_assign_ids", "evidence_ref"})
    if type(permissions["create_workspaces"]) is not bool or not isinstance(permissions["evidence_ref"], str) or not permissions["evidence_ref"].strip():
        raise ValueError("Explicit permission evidence is required")
    for key in ("capacity_assign_ids", "domain_assign_ids"):
        if not isinstance(permissions[key], list):
            raise ValueError("Permission IDs must be lists")
    clean_permissions = {**permissions, **{key: sorted({_uuid(x) for x in permissions[key]}) for key in ("capacity_assign_ids", "domain_assign_ids")}}
    if not isinstance(value["workspaces"], list) or len(value["workspaces"]) > 100000:
        raise ValueError("Invalid workspace inventory")
    rows, ids = [], set()
    for row in value["workspaces"]:
        _keys(row, {"id", "displayName", "capacityId", "domainId", "capacityAssignmentProgress", "type", "description"},
              {"id", "displayName", "capacityId", "domainId", "capacityAssignmentProgress", "type"})
        identity = _uuid(row["id"])
        if identity in ids or not isinstance(row["displayName"], str) or not row["displayName"].strip():
            raise ValueError("Duplicate workspace ID or invalid display name")
        ids.add(identity)
        rows.append({**row, "id": identity, "capacityId": _uuid(row["capacityId"]) if row["capacityId"] else None,
                     "domainId": _uuid(row["domainId"]) if row["domainId"] else None})
    return {"tenant_id": _uuid(tenant_id), "principal_id": principal, "observed_at": value["observed_at"], "complete": True,
            "workspaces": sorted(rows, key=lambda row: row["id"]), "permissions": clean_permissions}


def _matches(desired: dict, observed: dict) -> bool:
    return (observed["displayName"] == desired["name"] and observed["type"] == "Workspace"
            and observed["capacityId"] == _uuid(desired["capacity_id"])
            and observed["domainId"] == _uuid(desired["domain_id"])
            and observed["capacityAssignmentProgress"] == "Completed"
            and ("description" not in desired or observed.get("description", "") == desired["description"]))


def _observation_hash(observed: dict) -> str:
    return canonical_sha256({key: value for key, value in observed.items() if key != "observed_at"})


def build_deployment_plan(repository: ProjectPackageRevisionRepository, project_ref: str,
                          revision_hash: str, tenant_id: str, environment: str,
                          observed_state: dict, *, now: datetime | None = None) -> dict:
    released = release_input(repository, project_ref, revision_hash)
    compiler = released["compiler_input"]
    architecture = compiler["modules"].get("architecture_input")
    blockers = _workspace_blockers(architecture, compiler["modules"]["decision_set"])
    if blockers:
        raise ValueError("Workspace plan blocked: " + "; ".join(blockers))
    if environment not in architecture["environments"]["recommended"]:
        raise ValueError("Environment is not part of the accepted contract")
    observed = validate_observed_state(observed_state, tenant_id, now=now)
    desired = sorted([row for row in architecture["physical_workspaces"] if row["environment"] == environment], key=lambda row: row["id"])
    if not desired:
        raise ValueError("No physical workspace contract for the selected environment")
    operations = []
    for workspace in desired:
        if not 1 <= len(workspace["name"]) <= 256 or len(workspace.get("description", "")) > 4000:
            raise ValueError("Workspace exceeds documented name/description limits")
        candidates = [row for row in observed["workspaces"] if row["displayName"].casefold() == workspace["name"].casefold()]
        action, reason, existing_id = "create", "Absent from the complete principal-visible inventory", None
        if candidates:
            if len(candidates) == 1 and _matches(workspace, candidates[0]):
                action, reason, existing_id = "noop", "Exact existing workspace matches; no write or ownership claim", candidates[0]["id"]
            else:
                action, reason = "conflict", "Name is ambiguous or existing workspace differs; no overwrite"
        else:
            permissions = observed["permissions"]
            if (not permissions["create_workspaces"] or _uuid(workspace["capacity_id"]) not in permissions["capacity_assign_ids"]
                    or _uuid(workspace["domain_id"]) not in permissions["domain_assign_ids"]):
                action, reason = "blocked", "Workspace creation, capacity assignment or domain assignment evidence missing"
        operations.append({"id": workspace["id"], "action": action, "reason": reason, "desired": workspace,
                           "existing_id": existing_id})
    result = {"schema_version": VERSION, "scope": "fabric_workspaces_create_only", "project_ref": project_ref,
              "revision_hash": revision_hash, "release_record_sha256": released["release"]["record_sha256"],
              "tenant_id": _uuid(tenant_id), "principal_id": observed["principal_id"], "environment": environment,
              "observed_sha256": _observation_hash(observed), "operations": operations,
              "workspace_apply_ready": all(row["action"] in {"create", "noop"} for row in operations),
              "whole_project_apply_ready": False, "capabilities": CAPABILITIES}
    result["plan_sha256"] = canonical_sha256(result)
    return result


def _validate_plan(plan: dict) -> None:
    if (plan.get("scope") != "fabric_workspaces_create_only" or plan.get("schema_version") != VERSION
            or plan.get("whole_project_apply_ready") is not False
            or canonical_sha256({key: value for key, value in plan.items() if key != "plan_sha256"}) != plan.get("plan_sha256")):
        raise ValueError("Deployment plan integrity or scope mismatch")


def validate_repository_plan(repository: ProjectPackageRevisionRepository, plan: dict) -> None:
    """A recomputed client hash is not authority: compare the released contract."""
    _validate_plan(plan)
    released = release_input(repository, plan["project_ref"], plan["revision_hash"])
    architecture = released["compiler_input"]["modules"].get("architecture_input")
    blockers = _workspace_blockers(architecture, released["compiler_input"]["modules"]["decision_set"])
    if blockers or plan["environment"] not in architecture["environments"]["recommended"]:
        raise ValueError("Plan environment or physical contract is no longer valid")
    expected = sorted([row for row in architecture["physical_workspaces"] if row["environment"] == plan["environment"]], key=lambda row: row["id"])
    operations = plan.get("operations", [])
    if (not expected or [row.get("desired") for row in operations] != expected
            or [row.get("id") for row in operations] != [row["id"] for row in expected]
            or any(row.get("action") not in {"create", "noop", "blocked", "conflict"} for row in operations)
            or plan.get("release_record_sha256") != released["release"]["record_sha256"]
            or plan.get("capabilities") != CAPABILITIES):
        raise ValueError("Plan does not match the authoritative released workspace contract")


def reconcile_deployment(plan: dict, observed_state: dict, *, now: datetime | None = None,
                         repository: ProjectPackageRevisionRepository | None = None) -> dict:
    _validate_plan(plan)
    if repository is not None:
        validate_repository_plan(repository, plan)
    observed = validate_observed_state(observed_state, plan["tenant_id"], now=now)
    if observed["principal_id"] != plan["principal_id"]:
        raise ValueError("Readback principal differs from planned principal")
    rows = []
    for operation in plan["operations"]:
        desired = operation["desired"]
        candidates = [row for row in observed["workspaces"] if row["displayName"].casefold() == desired["name"].casefold()]
        state = "missing" if not candidates else "matched" if len(candidates) == 1 and _matches(desired, candidates[0]) else "drift"
        if state == "matched" and operation["existing_id"] and candidates[0]["id"] != operation["existing_id"]:
            state = "drift"
        rows.append({"id": operation["id"], "state": state, "workspace_ids": [row["id"] for row in candidates]})
    return {"plan_sha256": plan["plan_sha256"], "project_ref": plan["project_ref"], "revision_hash": plan["revision_hash"],
            "tenant_id": plan["tenant_id"], "observed_at": observed["observed_at"], "results": rows,
            "workspace_match": all(row["state"] == "matched" for row in rows), "whole_project_verified": False}


def approve_deployment(plan: dict, *, actor: str, rationale: str, now: datetime | None = None) -> dict:
    """Called only by a trusted authenticated approver; hashes are not signatures."""
    _validate_plan(plan)
    if not plan["workspace_apply_ready"] or not actor.strip() or not 20 <= len(rationale.strip()) <= 2000:
        raise ValueError("Ready workspace plan, named approver and 20–2000 character rationale required")
    time = _now(now)
    approval = {key: plan[key] for key in ("project_ref", "revision_hash", "tenant_id", "principal_id", "environment", "plan_sha256", "scope")}
    approval.update({"actor": actor.strip(), "rationale": rationale.strip(), "approved_at": time.isoformat(),
                     "expires_at": (time + MAX_AGE).isoformat()})
    approval["approval_sha256"] = canonical_sha256(approval)
    return approval


class WorkspaceClient(Protocol):
    def observe(self) -> dict: ...
    def create_workspace(self, body: dict) -> dict: ...
    def get_workspace(self, workspace_id: str) -> dict: ...


def execute_workspace_plan(repository: ProjectPackageRevisionRepository, plan: dict, approval: dict,
                           client: WorkspaceClient, state_dir: Path, *, now: datetime | None = None,
                           clock: Callable[[], datetime] | None = None) -> dict:
    """Create-only, one-shot approval consumption. Failures require readback + new plan.

    state_dir must be a trusted runner-owned directory, not a client-supplied path.
    Approval storage/authentication and exclusive runner ownership are host duties.
    """
    validate_repository_plan(repository, plan)
    current_time = clock or (lambda: _now(now))
    time = current_time()
    expected = approve_deployment(plan, actor=approval.get("actor", ""), rationale=approval.get("rationale", ""), now=_time(approval.get("approved_at")))
    if approval != expected or not _time(approval["approved_at"]) <= time < _time(approval["expires_at"]):
        raise ValueError("Approval scope, integrity or expiry mismatch")
    observed = client.observe()
    refreshed = build_deployment_plan(repository, plan["project_ref"], plan["revision_hash"], plan["tenant_id"], plan["environment"], observed, now=time)
    if refreshed != plan:
        raise ValueError("Observed state or released revision changed; review and approve a new plan")
    state_dir = Path(state_dir)
    if any(path.is_symlink() for path in (state_dir, *state_dir.parents)):
        raise ValueError("Execution state cannot use symlinks")
    state_dir.mkdir(parents=True, exist_ok=True)
    claim = state_dir / approval["approval_sha256"]
    try:
        claim.mkdir()
    except FileExistsError as error:
        raise ValueError("Approval already consumed; inspect recorded outcome and re-plan") from error
    (claim / "approval.json").write_text(json.dumps(approval, sort_keys=True), encoding="utf-8", newline="\n")
    results, expected_inventory = [], validate_observed_state(observed, plan["tenant_id"], now=time)
    outcome = {"plan_sha256": plan["plan_sha256"], "approval_sha256": approval["approval_sha256"], "results": results,
               "status": "incomplete", "whole_project_verified": False}
    try:
        for operation in plan["operations"]:
            time = current_time()
            if not _time(approval["approved_at"]) <= time < _time(approval["expires_at"]):
                raise ValueError("Approval expired during apply")
            release_input(repository, plan["project_ref"], plan["revision_hash"])
            fresh = validate_observed_state(client.observe(), plan["tenant_id"], now=time)
            if _observation_hash(fresh) != _observation_hash(expected_inventory):
                raise ValueError("Inventory or principal changed during apply; stopped without further writes")
            desired = operation["desired"]
            if operation["action"] == "noop":
                identity = operation["existing_id"]
            elif operation["action"] == "create":
                if current_time() >= _time(approval["expires_at"]):
                    raise ValueError("Approval expired before workspace creation")
                # Inventory collection may take time; pin HEAD again at the write boundary.
                release_input(repository, plan["project_ref"], plan["revision_hash"])
                body = {"displayName": desired["name"], "capacityId": desired["capacity_id"], "domainId": desired["domain_id"]}
                if "description" in desired:
                    body["description"] = desired["description"]
                # Never retry POST after an uncertain result: it may already have committed.
                created = client.create_workspace(body)
                identity = _uuid(created.get("id"))
                results.append({"id": operation["id"], "workspace_id": identity, "state": "created_unverified"})
                (claim / (operation["id"] + ".created.json")).write_text(json.dumps(results[-1]), encoding="utf-8", newline="\n")
            else:
                raise ValueError("Blocked/conflicting operation cannot execute")
            readback = client.get_workspace(identity)
            if _uuid(readback.get("id")) != identity or not _matches(desired, readback):
                raise ValueError("Workspace readback differs from name, ID, capacity, domain or assignment contract")
            if operation["action"] == "create":
                results[-1]["state"] = "created_verified"
                expected_inventory["workspaces"].append(readback)
                expected_inventory = validate_observed_state(expected_inventory, plan["tenant_id"], now=time)
            else:
                results.append({"id": operation["id"], "workspace_id": identity, "state": "noop_verified"})
        outcome["readback"] = reconcile_deployment(plan, client.observe(), now=current_time(), repository=repository)
        expected_ids = {row["id"]: row["workspace_id"] for row in results}
        for row in outcome["readback"]["results"]:
            if row["workspace_ids"] != [expected_ids[row["id"]]]:
                row["state"] = "drift"
                outcome["readback"]["workspace_match"] = False
        outcome["status"] = "workspace_verified" if outcome["readback"]["workspace_match"] else "drift"
    except Exception as error:
        # Do not echo subprocess output: it may contain credentials or tenant payloads.
        outcome.update({"status": "stopped_requires_reconciliation", "error_type": type(error).__name__,
                        "recovery": "Read back the tenant, preserve created resources, and approve a new plan; no automatic rollback or retry."})
    (claim / "outcome.json").write_text(json.dumps(outcome, sort_keys=True), encoding="utf-8", newline="\n")
    return outcome


class FabWorkspaceClient:
    """Official fab transport with isolated token auth and a closed endpoint set.

    token_provider comes from the trusted runner's identity broker, never package
    JSON. Local claim checks bind the context; Fabric validates the JWT signature.
    Permission evidence is supplied by the runner; list access alone is not proof.
    """
    def __init__(self, tenant_id: str, principal_id: str, token_provider: Callable[[], str],
                 permission_evidence: dict, *, runner: Callable = subprocess.run, client_id: str | None = None):
        self.tenant_id, self.principal_id = _uuid(tenant_id), _uuid(principal_id)
        self.client_id = _uuid(client_id) if client_id is not None else None
        self.token_provider, self.permissions, self.runner = token_provider, permission_evidence, runner

    def _request(self, path: str, method: str = "get", body: dict | None = None) -> dict:
        token = self.token_provider()
        try:
            segment = token.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
            application_ids = [claims[key] for key in ("azp", "appid") if key in claims]
            if (_uuid(claims["tid"]) != self.tenant_id or _uuid(claims["oid"]) != self.principal_id
                    or claims["aud"] not in {"https://api.fabric.microsoft.com", "https://api.fabric.microsoft.com/"}
                    or claims["exp"] <= _now().timestamp() + 60
                    or (self.client_id is not None and (not application_ids
                        or any(_uuid(value) != self.client_id for value in application_ids)))):
                raise ValueError("Token scope mismatch")
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ValueError("Trusted Fabric token has wrong tenant, application, principal, audience or lifetime") from error
        env = {key: value for key, value in os.environ.items() if not key.upper().startswith("FAB_")}
        env.update({"FAB_TOKEN": token, "FAB_TENANT_ID": self.tenant_id})
        args = ["fab", "api", path, "-A", "fabric", "-X", method,
                "-H", "x-ms-fabric-skill=deployment-pipelines-authoring-cli"]
        if body is not None:
            args.extend(["-i", json.dumps(body, separators=(",", ":"))])
        result = self.runner(args, capture_output=True, text=True, encoding="utf-8", check=True, timeout=120, shell=False, env=env)
        try:
            response = json.loads(result.stdout)
        except (ValueError, TypeError) as error:
            raise ValueError("fab returned an unsupported response shape; no retry") from error
        if not isinstance(response, dict):
            raise ValueError("fab response must be an object")
        # fab wraps status/body. Preserve failure rather than interpreting it as data.
        if "status_code" in response:
            if response["status_code"] != (201 if method == "post" else 200):
                raise ValueError("Unexpected Fabric status; reconcile before retry")
            response = response.get("text") or response.get("body")
            if isinstance(response, str):
                response = json.loads(response)
        if not isinstance(response, dict) or "errorCode" in response:
            raise ValueError("Invalid Fabric response")
        return response

    def observe(self) -> dict:
        items, tokens, token = [], set(), None
        while True:
            suffix = "?" + urlencode({"continuationToken": token}) if token else ""
            page = self._request("workspaces" + suffix)
            if not isinstance(page.get("value"), list):
                raise ValueError("Workspace page is incomplete")
            items.extend(page["value"])
            token = page.get("continuationToken")
            if not token:
                if page.get("continuationUri"):
                    raise ValueError("Continuation URI without token is unsupported")
                break
            if not isinstance(token, str) or token in tokens or len(tokens) >= 1000:
                raise ValueError("Repeated or excessive pagination")
            tokens.add(token)
        rows = [self.get_workspace(_uuid(item.get("id"))) for item in items]
        return validate_observed_state({"tenant_id": self.tenant_id, "principal_id": self.principal_id,
            "observed_at": _now().isoformat(), "complete": True, "workspaces": rows, "permissions": self.permissions}, self.tenant_id)

    def get_workspace(self, workspace_id: str) -> dict:
        value = self._request("workspaces/" + _uuid(workspace_id))
        # Normalize the documented subset; omitted assignments remain unknown/null.
        return {key: value.get(key) for key in ("id", "displayName", "capacityId", "domainId", "capacityAssignmentProgress", "type", "description")}

    def create_workspace(self, body: dict) -> dict:
        _keys(body, {"displayName", "capacityId", "domainId", "description"}, {"displayName", "capacityId", "domainId"})
        return self._request("workspaces", "post", body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only workspace plan and reconciliation from JSON stdin")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--mode", choices=("plan", "reconcile"), required=True)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("Input exceeds deployment evidence limit")
        payload = json.loads(raw)
        if args.mode == "plan":
            _keys(payload, {"project_ref", "revision_hash", "tenant_id", "environment", "observed_state"})
            result = build_deployment_plan(ProjectPackageRevisionRepository(args.repository, args.schemas), **payload)
        else:
            _keys(payload, {"plan", "observed_state"})
            result = reconcile_deployment(**payload, repository=ProjectPackageRevisionRepository(args.repository, args.schemas))
        print(json.dumps({"ok": True, "value": result}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
