"""Private Studio subprocess adapter, not a standalone authentication service.

Only the authenticated server may supply actor/project arguments. Filesystem
administrators are trusted. Host policy and credential references never come
from package, browser JSON, flags or dynamic imports.
"""
from __future__ import annotations

import argparse
import base64
import copy
import importlib.metadata
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

from . import deployment_plan as dp
from .protected_runner import AllowedScope, ProtectedWorkspaceRunner, RunnerPolicy, ID, PROJECT
from .repository import ProjectPackageRevisionRepository

FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
ENV_REF = re.compile(r"^STUDIO_RUNNER_[A-Z0-9_]{1,100}$")
ACTOR = re.compile(r"^github:[0-9]{1,30}$")
CONFIG_KEYS = {"schema_version", "enabled", "state_dir", "signing_key_env", "approvers", "executors", "scopes"}


def _fields(value: dict, fields: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Runner input or configuration has missing or unsupported fields")


def _path(value: str) -> Path:
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise ValueError("Runner host paths must be explicit absolute paths")
    path = Path(os.path.abspath(value))
    if any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()) for part in (path, *path.parents)):
        raise ValueError("Runner host paths must not use symlinks or junctions")
    return path


def _reference(value: str) -> str:
    if not isinstance(value, str) or not ENV_REF.fullmatch(value):
        raise ValueError("Runner credential references require a STUDIO_RUNNER_ environment name")
    return value


def _sdk_available() -> bool:
    # Distribution metadata only: do not construct a credential or inspect tokens.
    try:
        version = importlib.metadata.version("azure-identity")
        return isinstance(version, str) and bool(re.fullmatch(r"[0-9][0-9A-Za-z.!+_-]{0,99}", version))
    except (importlib.metadata.PackageNotFoundError, OSError, ValueError, TypeError, KeyError):
        return False


def _fab_available() -> bool:
    # Discoverability only: never execute the CLI, login or query a tenant here.
    try:
        return shutil.which("fab") is not None
    except (OSError, ValueError):
        return False


@dataclass(frozen=True)
class HostConfiguration:
    policy: RunnerPolicy
    state_dir: Path | None = None
    signing_key_env: str | None = None
    identities: tuple[dict, ...] = ()


def load_configuration(repository: ProjectPackageRevisionRepository, environment: Mapping[str, str]) -> HostConfiguration:
    filename = environment.get("STUDIO_RUNNER_CONFIG")
    if not filename:
        return HostConfiguration(RunnerPolicy())
    path = _path(filename)
    try:
        if path.stat().st_size > 1_000_000:
            raise ValueError("Runner host configuration exceeds the size limit")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Runner host configuration is unavailable or invalid") from error
    if value == {"schema_version": "1.0.0", "enabled": False}:
        return HostConfiguration(RunnerPolicy())
    _fields(value, CONFIG_KEYS)
    if value["schema_version"] != "1.0.0" or type(value["enabled"]) is not bool:
        raise ValueError("Unsupported runner configuration version or enable flag")
    state = _path(value["state_dir"])
    root = repository.root.absolute()
    if state == Path(state.anchor) or state.is_relative_to(root) or root.is_relative_to(state):
        raise ValueError("Runner state must be private and separate from the package repository")
    scopes, identities = [], []
    if not isinstance(value["scopes"], list) or len(value["scopes"]) > 100:
        raise ValueError("Runner scopes must be an explicit bounded list")
    for row in value["scopes"]:
        _fields(row, {"project_ref", "tenant_id", "principal_id", "environment", "identity", "permissions"})
        scope = AllowedScope(**{key: row[key] for key in ("project_ref", "tenant_id", "principal_id", "environment")})
        identity = row["identity"]
        if not isinstance(identity, dict):
            raise ValueError("Explicit runner identity configuration required")
        if identity.get("kind") == "client_secret":
            _fields(identity, {"kind", "client_id", "client_secret_env"})
            _reference(identity["client_secret_env"])
            if identity["client_secret_env"] == value["signing_key_env"]:
                raise ValueError("Signing and identity secrets require separate references")
        elif identity.get("kind") == "managed_identity":
            # Require a user-assigned identity; no ambient system-assigned fallback.
            _fields(identity, {"kind", "client_id"})
        else:
            raise ValueError("Only explicit client_secret or managed_identity credentials are supported")
        if dp._uuid(identity["client_id"]) != identity["client_id"]:
            raise ValueError("Runner client ID requires a canonical UUID")
        permissions = row["permissions"]
        dp._keys(permissions, {"create_workspaces", "capacity_assign_ids", "domain_assign_ids", "evidence_ref"})
        if type(permissions["create_workspaces"]) is not bool or not isinstance(permissions["evidence_ref"], str) or not permissions["evidence_ref"].strip():
            raise ValueError("Explicit trusted permission evidence required")
        for key in ("capacity_assign_ids", "domain_assign_ids"):
            if not isinstance(permissions[key], list) or any(dp._uuid(v) != v for v in permissions[key]):
                raise ValueError("Runner permission IDs require canonical UUID lists")
        scopes.append(scope)
        identities.append({"scope": scope, "identity": copy.deepcopy(identity), "permissions": copy.deepcopy(permissions)})
    for key in ("approvers", "executors"):
        if not isinstance(value[key], list) or any(not isinstance(actor, str) or not ACTOR.fullmatch(actor) for actor in value[key]):
            raise ValueError("Runner actors must use stable github:<provider-account-id> identities")
        if len(set(value[key])) != len(value[key]):
            raise ValueError("Duplicate runner actor")
    policy = RunnerPolicy(value["enabled"], tuple(scopes), frozenset(value["approvers"]), frozenset(value["executors"]))
    return HostConfiguration(policy, state, _reference(value["signing_key_env"]), tuple(identities))


def _credential(identity: dict, scope: AllowedScope, environment: Mapping[str, str]):
    """Closed SDK choice, called only after the signed attempt is consumed."""
    try:
        from azure.identity import ClientSecretCredential, ManagedIdentityCredential
    except ImportError as error:
        raise ValueError("The host runtime requires the optional azure-identity package") from error
    if identity["kind"] == "managed_identity":
        return ManagedIdentityCredential(client_id=identity["client_id"], connection_timeout=10, read_timeout=30, retry_total=0)
    secret = environment.get(identity["client_secret_env"])
    if not secret:
        raise ValueError("Configured runner identity secret is unavailable")
    return ClientSecretCredential(tenant_id=scope.tenant_id, client_id=identity["client_id"], client_secret=secret,
        authority="https://login.microsoftonline.com", connection_timeout=10, read_timeout=30, retry_total=0)


def client_factory(configuration: HostConfiguration, environment: Mapping[str, str], *, credential_factory: Callable = _credential):
    def create(scope: AllowedScope):
        entry = next((row for row in configuration.identities if row["scope"] == scope), None)
        if entry is None:
            raise ValueError("No identity broker for the exact allowed scope")
        credential = credential_factory(entry["identity"], scope, environment)
        def token() -> str:
            # Never return credential errors: they can include tenant diagnostics.
            try:
                return credential.get_token(FABRIC_SCOPE).token
            except Exception as error:
                raise ValueError("Configured Fabric identity could not acquire a token") from error
        return dp.FabWorkspaceClient(scope.tenant_id, scope.principal_id, token, entry["permissions"])
    return create


def status(configuration: HostConfiguration, project_ref: str, actor: str, environment: Mapping[str, str]) -> dict:
    policy = configuration.policy
    entries = [row for row in configuration.identities if row["scope"].project_ref == project_ref]
    enabled = policy.enabled and bool(entries)
    key_present = configuration.signing_key_env is not None and configuration.signing_key_env in environment
    identity_present = bool(entries) and all(row["identity"]["kind"] == "managed_identity"
        or row["identity"]["client_secret_env"] in environment for row in entries)
    sdk_available, fab_available = _sdk_available(), _fab_available()
    key_configured = enabled and key_present
    broker_configured = enabled and sdk_available and identity_present
    state_configured = configuration.state_dir is not None
    # Metadata only. No mkdir, write probe, permission escalation or ACL inference.
    try:
        state_exists = state_configured and configuration.state_dir.is_dir()
        state_path_usable = state_configured and (state_exists or not configuration.state_dir.exists())
    except OSError:
        state_exists = False
        state_path_usable = False
    checks = []
    def check(id: str, title: str, configured: bool | None, detail: str, action: str):
        checks.append({"id": id, "title": title,
            "state": "not_verified" if configured is None else "configured" if configured else "missing",
            "detail": detail, "action": action})
    check("host_policy", "Host execution policy", policy.enabled,
        "Execution is enabled by host policy." if policy.enabled else "Execution is disabled; read-only diagnostics do not enable it.",
        "A host administrator must explicitly configure and enable the runner before any approved test.")
    check("project_scope", "Exact project scope", bool(entries),
        "Explicit tenant, principal and environment scopes exist for this project." if entries else "No exact allowed scope exists for this project.",
        "Configure only the agreed nonproduction tenant, principal, project and environment; do not use wildcard scopes.")
    check("approver", "Approval operator", actor in policy.approvers,
        "The authenticated actor is on the approval allowlist." if actor in policy.approvers else "The authenticated actor is not on the approval allowlist.",
        "Have the host administrator review the stable OAuth actor and explicitly assign approval authority if appropriate.")
    check("executor", "Execution operator", actor in policy.executors,
        "The authenticated actor is on the execution allowlist." if actor in policy.executors else "The authenticated actor is not on the execution allowlist.",
        "Have the host administrator separately review and assign execution authority if appropriate.")
    check("signing_reference", "Approval signing reference", key_present,
        "The signing environment reference is present; its value and validity were not read." if key_present else "The configured signing reference is absent.",
        "Provision a dedicated random signing key through the host secret mechanism; never paste it into the project or Studio.")
    check("identity_reference", "Explicit identity reference", identity_present,
        "Each allowed project scope has an explicit identity and any required secret reference is present; values were not read." if identity_present else "An explicit project identity or its required environment reference is missing.",
        "Configure a dedicated client identity or explicit user-assigned managed identity for each allowed scope.")
    check("identity_sdk", "Identity SDK metadata", sdk_available,
        "azure-identity distribution metadata is discoverable; imports and token acquisition were not tested." if sdk_available else "azure-identity distribution metadata is missing or unreadable in the selected Python runtime.",
        "Have the host administrator install and pin the approved azure-identity dependency in the runner Python runtime.")
    check("fabric_cli", "Fabric CLI executable", fab_available,
        "A fab executable is discoverable on the host PATH; its version, operation and authenticity were not tested." if fab_available else "No fab executable is discoverable on the host PATH.",
        "Have the host administrator provision an approved Fabric CLI on the runner PATH and verify its version separately.")
    check("state_storage", "Private evidence storage path", state_path_usable,
        ("A separate configured state directory exists; ACLs and writability were not tested." if state_exists else
         "A separate state path is configured but no directory was observed; diagnostics did not create it.") if state_path_usable else
        "No usable private state path is configured, or its metadata is unavailable or identifies a non-directory.",
        "Provision persistent private storage with restricted host ACLs; independently test writability, backup and restore before live acceptance.")
    check("identity_permissions", "Live identity and permissions", None,
        "The configured principal, token claims and actual tenant permissions have not been verified by these diagnostics.",
        "Use the separately authorized nonproduction acceptance procedure to establish the actual principal and effective scope.")
    check("host_recovery", "Host protection and recovery", None,
        "Private ACLs, secret strength, durable evidence retention and recovery are not proven by configuration presence.",
        "Record host protection and recovery evidence, including read-only result retrieval after interruption and emergency disable.")
    check("tenant_acceptance", "Tenant acceptance", None,
        "No tenant API was called and no workspace, data, security or whole-project delivery has been verified.",
        "Approve a bounded nonproduction workspace test, verify readback and replanning, and retain expected and actual results.")
    return {"schema_version": "1.0.0", "project_ref": project_ref, "enabled": enabled,
            "scope": "fabric_workspaces_create_only", "environments": sorted({row["scope"].environment for row in entries}),
            "approval_storage_ready": bool(key_configured), "client_factory_configured": bool(broker_configured),
            "identity_broker_available": bool(broker_configured), "execute_endpoint_available": True,
            "can_approve": bool(key_configured and broker_configured and state_path_usable and fab_available and actor in policy.approvers),
            "can_execute": bool(key_configured and broker_configured and state_path_usable and fab_available and actor in policy.executors),
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "readiness_scope": "configuration_only", "tenant_actions_performed": False, "checks": checks,
            "configuration_checked_only": True, "identity_verified": False, "whole_project_apply_ready": False,
            "limitations": ["Status checks references only, not secret validity, host ACLs, credentials or tenant access.",
                "Only exact workspace creation and readback are supported; items, security, data and CI/CD remain separate gates.",
                "An interrupted or uncertain attempt is consumed. Inspect its evidence; never automatically retry."]}


def dispatch(repository: ProjectPackageRevisionRepository, mode: str, payload: dict, *,
             environment: Mapping[str, str] | None = None, factory_builder: Callable = client_factory,
             clock: Callable = dp._now) -> dict:
    environment = os.environ if environment is None else environment
    extra = {"status": set(), "approve": {"plan", "rationale", "confirm"},
             "execute": {"approval_id", "confirm"}, "outcome": {"approval_id"}}
    if mode not in extra:
        raise ValueError("Unsupported protected runner operation")
    _fields(payload, {"project_ref", "revision_hash", "actor"} | extra[mode])
    if (not isinstance(payload["project_ref"], str) or not PROJECT.fullmatch(payload["project_ref"])
            or not isinstance(payload["revision_hash"], str) or not ID.fullmatch(payload["revision_hash"])
            or not isinstance(payload["actor"], str) or not ACTOR.fullmatch(payload["actor"])):
        raise ValueError("Explicit project, pinned revision and authenticated stable operator required")
    config = load_configuration(repository, environment)
    if mode == "status":
        return status(config, payload["project_ref"], payload["actor"], environment)
    if not config.policy.enabled and mode != "outcome":
        raise ValueError("Protected runner is disabled")
    if mode == "outcome" and (config.state_dir is None or config.signing_key_env is None):
        raise ValueError("Read-only runner evidence requires explicit host storage, key and scope policy")
    # Refuse foreign scopes and actors before reading host secrets.
    if payload["project_ref"] not in {scope.project_ref for scope in config.policy.scopes}:
        raise ValueError("Project is outside the exact runner scope allowlist")
    actors = config.policy.approvers if mode == "approve" else config.policy.executors
    if mode == "outcome":
        actors = config.policy.approvers | config.policy.executors
    if payload["actor"] not in actors:
        raise ValueError("Authenticated operator is not allowed for this runner action")
    if mode == "approve" and not status(config, payload["project_ref"], payload["actor"], environment)["can_approve"]:
        raise ValueError("Runner approval requires configured signing and identity broker references")
    try:
        key = base64.b64decode(environment.get(config.signing_key_env, ""), validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("Configured runner signing key must be base64 with at least 32 bytes") from error
    if len(key) < 32:
        raise ValueError("Configured runner signing key must be base64 with at least 32 bytes")
    host = ProtectedWorkspaceRunner(repository, policy=config.policy, state_dir=config.state_dir,
        signing_key=key, client_factory=factory_builder(config, environment) if mode == "execute" else None, clock=clock)
    if mode == "approve":
        plan = payload["plan"]
        if not isinstance(plan, dict) or plan.get("project_ref") != payload["project_ref"] or plan.get("revision_hash") != payload["revision_hash"]:
            raise ValueError("Approval request does not match the pinned project revision")
        return host.approve(plan, actor=payload["actor"], rationale=payload["rationale"], confirm=payload["confirm"])
    args = {key: payload[key] for key in ("actor", "project_ref", "revision_hash")}
    if mode == "outcome":
        return host.read_outcome(payload["approval_id"], **args)
    return host.execute(payload["approval_id"], **args, confirm=payload["confirm"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Private authenticated Studio host adapter; not standalone caller authentication")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--mode", choices=("status", "approve", "execute", "outcome"), required=True)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Runner request exceeds the size limit")
        value = dispatch(ProjectPackageRevisionRepository(args.repository, args.schemas), args.mode, json.loads(raw))
        print(json.dumps({"ok": True, "value": value}))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        # Configuration and parser errors can contain filesystem paths or submitted
        # strings. Keep raw exception details in neither stdout nor stderr.
        print(json.dumps({"ok": False, "error": "Protected runner request refused. Check host configuration, exact scope and signed approval evidence.", "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
