"""Trusted-host workspace execution boundary; no public CLI or token discovery.

The host authenticates callers and owns policy, HMAC key, storage and client
factory. Browser/package data cannot configure them. This module deliberately
does not establish an HTTP authentication or Fabric identity broker itself.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import deployment_plan as dp
from .hashes import canonical_bytes, canonical_sha256
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
ID = re.compile(r"^[a-f0-9]{64}$")
PROJECT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}$")


@dataclass(frozen=True)
class AllowedScope:
    project_ref: str
    tenant_id: str
    principal_id: str
    environment: str

    def __post_init__(self):
        if not isinstance(self.project_ref, str):
            raise ValueError("Runner scope requires an explicit project")
        if self.project_ref.casefold() == 'local_reference' or self.project_ref.casefold().startswith('local_reference_'):
            raise ValueError('The synthetic local reference namespace cannot be authorized for live execution')
        if not PROJECT.fullmatch(self.project_ref) or self.environment not in {"dev", "test", "prod"}:
            raise ValueError("Runner scope requires an explicit project and environment")
        if dp._uuid(self.tenant_id) != self.tenant_id or dp._uuid(self.principal_id) != self.principal_id:
            raise ValueError("Runner scope UUIDs must use canonical form")


@dataclass(frozen=True)
class RunnerPolicy:
    enabled: bool = False
    scopes: tuple[AllowedScope, ...] = ()
    approvers: frozenset[str] = field(default_factory=frozenset)
    executors: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("Runner enabled flag must be boolean")
        if not isinstance(self.scopes, tuple) or any(not isinstance(scope, AllowedScope) for scope in self.scopes):
            raise ValueError("Runner scopes must be immutable explicit scopes")
        if len(set(self.scopes)) != len(self.scopes):
            raise ValueError("Duplicate runner scope")
        for actors in (self.approvers, self.executors):
            if not isinstance(actors, frozenset) or any(not isinstance(actor, str) or not actor.strip() or actor != actor.strip() for actor in actors):
                raise ValueError("Runner actors must be explicit immutable identities")
        if self.enabled and (not self.scopes or not self.approvers or not self.executors):
            raise ValueError("Enabling the runner requires scopes, approvers and executors")

    def document(self) -> dict:
        return {"enabled": self.enabled, "scopes": [scope.__dict__ for scope in self.scopes],
                "approvers": sorted(self.approvers), "executors": sorted(self.executors)}


class ProtectedWorkspaceRunner:
    """Create-only execution with signed, persisted, expiring, single-use intent.

    ``actor`` must come from the host's authenticated session after project/admin
    authorization, never a request body. The allowlist adds a second restriction;
    it is not a substitute for authenticating a supplied actor string.

    ``client_factory`` is code configured by the host. It receives an exact scope
    and may construct FabWorkspaceClient using a trusted token provider. No token,
    executable, credential path or dynamic import is accepted by this API.
    """

    def __init__(self, repository: ProjectPackageRevisionRepository, *, policy: RunnerPolicy | None = None,
                 state_dir: Path, signing_key: bytes | None = None,
                 client_factory: Callable[[AllowedScope], dp.WorkspaceClient] | None = None,
                 clock: Callable[[], datetime] = dp._now):
        self.repository = repository
        self.policy = policy or RunnerPolicy()
        self.state_dir = Path(state_dir).absolute()
        self.key = signing_key
        self.client_factory = client_factory
        self.clock = clock
        if signing_key is not None and (not isinstance(signing_key, bytes) or len(signing_key) < 32):
            raise ValueError("Runner signing key must contain at least 32 bytes")
        if self.policy.enabled and signing_key is None:
            raise ValueError("Enabled runner requires a host-owned signing key")
        if client_factory is not None and not callable(client_factory):
            raise ValueError("Runner client factory must be trusted host code")

    def status(self, project_ref: str) -> dict:
        """Read-only capabilities, not proof that authentication/tenant is ready."""
        scopes = [scope for scope in self.policy.scopes if scope.project_ref == project_ref]
        enabled = self.policy.enabled and bool(scopes)
        return {"schema_version": VERSION, "project_ref": project_ref, "enabled": enabled,
                "approval_storage_ready": enabled and self.key is not None,
                "client_factory_configured": self.client_factory is not None,
                "execute_endpoint_available": False, "whole_project_apply_ready": False,
                "scope": "fabric_workspaces_create_only",
                "environments": sorted({scope.environment for scope in scopes}),
                "limitations": ["The host must authenticate and authorize each operator.",
                    "No public execute endpoint or automatic token discovery is supplied.",
                    "Only workspace creation and readback are supported; no item, security, data or CI/CD apply.",
                    "Host ACLs must protect state and the signing key; a host administrator remains trusted."]}

    def _authorize(self, actor: str, action: str) -> None:
        if not self.policy.enabled:
            raise ValueError("Protected runner is disabled")
        permitted = self.policy.approvers if action == "approve" else self.policy.executors
        if not isinstance(actor, str) or actor not in permitted:
            raise ValueError("Authenticated operator is not allowed for this runner action")

    def _scope(self, plan: dict) -> AllowedScope:
        for scope in self.policy.scopes:
            if all(plan.get(key) == value for key, value in scope.__dict__.items()):
                return scope
        raise ValueError("Plan is outside the exact runner scope allowlist")

    def _safe(self, path: Path) -> Path:
        if any(parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()) for parent in (path, *path.parents)):
            raise ValueError("Runner state must not use symlinks or junctions")
        if not path.is_relative_to(self.state_dir):
            raise ValueError("Runner state path is outside host storage")
        return path

    def _signed(self, payload: dict) -> dict:
        if self.key is None:
            raise ValueError("Runner signing key unavailable")
        return {"payload": payload, "mac": hmac.new(self.key, canonical_bytes(payload), hashlib.sha256).hexdigest()}

    def _persist(self, path: Path, payload: dict) -> None:
        # Exclusive creation: partial writes fail closed and never overwrite evidence.
        self._safe(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            json.dump(self._signed(payload), stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            import os
            os.fsync(stream.fileno())

    def _read(self, path: Path) -> dict:
        self._safe(path)
        try:
            if path.stat().st_size > 5_000_000:
                raise ValueError("Oversized runner record")
            record = json.loads(path.read_text(encoding="utf-8"))
            if set(record) != {"payload", "mac"} or not isinstance(record["payload"], dict):
                raise ValueError("Malformed runner record")
            if not isinstance(record["mac"], str) or not hmac.compare_digest(record["mac"], self._signed(record["payload"])["mac"]):
                raise ValueError("Invalid runner signature")
            return record["payload"]
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise ValueError("Runner record missing or integrity verification failed") from error

    def approve(self, plan: dict, *, actor: str, rationale: str, confirm: bool = False) -> dict:
        self._authorize(actor, "approve")
        if confirm is not True:
            raise ValueError("Explicit plan approval confirmation is required")
        plan = copy.deepcopy(plan)
        self._scope(plan)
        dp.validate_repository_plan(self.repository, plan)
        approval = dp.approve_deployment(plan, actor=actor, rationale=rationale, now=self.clock())
        identity = secrets.token_hex(32)
        payload = {"schema_version": VERSION, "approval_id": identity, "plan": plan, "approval": approval,
                   "policy_sha256": canonical_sha256(self.policy.document())}
        self._persist(self.state_dir / "approvals" / (identity + ".json"), payload)
        return {"approval_id": identity, "project_ref": plan["project_ref"], "revision_hash": plan["revision_hash"],
                "plan_sha256": plan["plan_sha256"], "expires_at": approval["expires_at"],
                "status": "approved_not_executed", "tenant_actions_performed": False}

    def _approval(self, identity: str) -> dict:
        if not isinstance(identity, str) or not ID.fullmatch(identity):
            raise ValueError("Invalid protected approval ID")
        payload = self._read(self.state_dir / "approvals" / (identity + ".json"))
        if (payload.get("schema_version") != VERSION or payload.get("approval_id") != identity
                or payload.get("policy_sha256") != canonical_sha256(self.policy.document())):
            raise ValueError("Runner approval identity or host policy changed; approve a new plan")
        self._scope(payload["plan"])
        approval = payload["approval"]
        if not dp._time(approval["approved_at"]) <= dp._now(self.clock()) < dp._time(approval["expires_at"]):
            raise ValueError("Protected approval expired or is dated in the future")
        dp.validate_repository_plan(self.repository, payload["plan"])
        return payload

    def read_outcome(self, approval_id: str, *, actor: str, project_ref: str, revision_hash: str) -> dict:
        """Read signed historical evidence without renewing or executing approval.

        Current host scope/operator authorization still applies. Expiry and HEAD
        changes prevent execution, not investigation of an earlier attempt.
        """
        # Emergency disable stops writes, not investigation. Explicit current
        # operator/scope policy and the original signing key remain mandatory.
        if actor not in self.policy.approvers | self.policy.executors:
            raise ValueError("Authenticated operator is not allowed to read runner evidence")
        if not isinstance(approval_id, str) or not ID.fullmatch(approval_id):
            raise ValueError("Invalid protected approval ID")
        stored = self._read(self.state_dir / "approvals" / (approval_id + ".json"))
        if stored.get("schema_version") != VERSION or stored.get("approval_id") != approval_id:
            raise ValueError("Runner approval identity mismatch")
        plan = stored["plan"]
        self._scope(plan)
        if plan["project_ref"] != project_ref or plan["revision_hash"] != revision_hash:
            raise ValueError("Evidence request does not match the stored project revision")
        receipt = {"approval_id": approval_id, "project_ref": project_ref, "revision_hash": revision_hash,
                   "plan_sha256": plan["plan_sha256"], "expires_at": stored["approval"]["expires_at"],
                   "tenant_id": plan["tenant_id"], "principal_id": plan["principal_id"], "environment": plan["environment"]}
        expected = {key: receipt[key] for key in ("approval_id", "project_ref", "revision_hash", "plan_sha256")}
        outcome_path = self._safe(self.state_dir / "outcomes" / (approval_id + ".json"))
        claim_path = self._safe(self.state_dir / "consumed" / (approval_id + ".json"))
        if outcome_path.exists():
            result = self._read(outcome_path)
            if any(result.get(key) != value for key, value in expected.items()):
                raise ValueError("Runner outcome identity mismatch")
            claim = self._read(claim_path)
            if any(claim.get(key) != value for key, value in expected.items()):
                raise ValueError("Runner consumption identity mismatch")
            return {"status": "completed", "receipt": receipt, "result": result,
                    "whole_project_verified": False}
        if claim_path.exists():
            claim = self._read(claim_path)
            if any(claim.get(key) != value for key, value in expected.items()):
                raise ValueError("Runner consumption identity mismatch")
            return {"status": "consumed_requires_reconciliation", "receipt": receipt,
                    "whole_project_verified": False,
                    "message": "The attempt is running or was interrupted. Do not retry; inspect signed evidence and live inventory."}
        status = "expired" if dp._now(self.clock()) >= dp._time(receipt["expires_at"]) else "approved_not_executed"
        return {"status": status, "receipt": receipt, "whole_project_verified": False}

    def execute(self, approval_id: str, *, actor: str, project_ref: str, revision_hash: str,
                confirm: bool = False) -> dict:
        """Consumes stored intent, never accepts pasted plan/approval or host inputs."""
        self._authorize(actor, "execute")
        if confirm is not True:
            raise ValueError("Explicit execution confirmation is required")
        payload = self._approval(approval_id)
        plan = payload["plan"]
        if plan["project_ref"] != project_ref or plan["revision_hash"] != revision_hash:
            raise ValueError("Execution request does not match the stored project revision")
        if self.client_factory is None:
            raise ValueError("Trusted runner identity/client broker is not configured")
        scope = self._scope(plan)
        # Serialize all workspace writes to this tenant within this host. A crash
        # leaves a lock for operator reconciliation; automatic stale unlock is unsafe.
        lock = self._safe(self.state_dir / "tenant-locks" / scope.tenant_id)
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock.mkdir()
        except FileExistsError as error:
            raise ValueError("Tenant runner is active or requires interrupted-run reconciliation") from error
        try:
            claim = self.state_dir / "consumed" / (approval_id + ".json")
            try:
                self._persist(claim, {"approval_id": approval_id, "actor": actor, "started_at": self.clock().isoformat(),
                                      "project_ref": project_ref, "revision_hash": revision_hash, "plan_sha256": plan["plan_sha256"]})
            except FileExistsError as error:
                raise ValueError("Protected approval already consumed; reconcile and approve a new plan") from error
            try:
                # Consume before constructing any network-capable client, including
                # on startup failure. Never retry an uncertain attempt automatically.
                client = self.client_factory(scope)
                outcome = dp.execute_workspace_plan(self.repository, plan, payload["approval"], client,
                    self.state_dir / "executor-receipts", clock=self.clock)
            except Exception as error:
                outcome = {"status": "stopped_requires_reconciliation", "error_type": type(error).__name__,
                           "whole_project_verified": False,
                           "recovery": "Inspect runner receipts and tenant readback; approve a new plan before any retry."}
            result = {"schema_version": VERSION, "approval_id": approval_id, "actor": actor,
                      "project_ref": project_ref, "revision_hash": revision_hash, "plan_sha256": plan["plan_sha256"],
                      "finished_at": self.clock().isoformat(), "outcome": outcome}
            self._persist(self.state_dir / "outcomes" / (approval_id + ".json"), result)
            return result
        finally:
            # Empty lock only. If cleanup fails, leave it for host reconciliation.
            lock.rmdir()
