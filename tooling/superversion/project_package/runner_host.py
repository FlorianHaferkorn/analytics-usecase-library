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
from urllib.parse import urlencode, urlparse

from . import deployment_plan as dp
from .protected_runner import AllowedScope, ProtectedWorkspaceRunner, RunnerPolicy, ID, PROJECT
from .repository import ProjectPackageRevisionRepository

FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
ENV_REF = re.compile(r"^STUDIO_RUNNER_[A-Z0-9_]{1,100}$")
ACTOR = re.compile(r"^github:[0-9]{1,30}$")
SETTING_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,199}$")
ASSERTION = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
MAX_TENANT_SETTING_PAGES = 25
CONFIG_KEYS = {"schema_version", "enabled", "state_dir", "signing_key_env", "approvers", "executors", "scopes"}
CONFIG_KEYS_TEAM = CONFIG_KEYS | {"independent_execution_environments"}
SCOPE_KEYS = {"project_ref", "tenant_id", "principal_id", "environment", "identity", "permissions"}
CONFIG_VERSIONS = {"1.0.0", "1.1.0", "1.2.0"}


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


def _bounded_claim(value: object, label: str, *, uri: bool = False) -> str:
    if (not isinstance(value, str) or not value or value != value.strip() or len(value) > 500
            or any(ord(character) < 32 for character in value)):
        raise ValueError(f"Workload identity {label} must be an explicit bounded value")
    if uri:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc or parsed.fragment:
            raise ValueError(f"Workload identity {label} must be an explicit HTTPS URI")
    return value


def _decode_jwt_part(value: str) -> dict:
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        document = json.loads(decoded)
    except (ValueError, UnicodeError, json.JSONDecodeError, TypeError) as error:
        raise ValueError("Configured workload identity assertion is unavailable or invalid") from error
    if not isinstance(document, dict):
        raise ValueError("Configured workload identity assertion is unavailable or invalid")
    return document


def _validate_assertion(value: str, identity: dict, *, now: datetime | None = None) -> str:
    if not ASSERTION.fullmatch(value):
        raise ValueError("Configured workload identity assertion is unavailable or invalid")
    header, claims, _ = value.split(".")
    header_value, claim_value = _decode_jwt_part(header), _decode_jwt_part(claims)
    current = (now or datetime.now(timezone.utc)).timestamp()
    algorithm = header_value.get("alg")
    expires, not_before = claim_value.get("exp"), claim_value.get("nbf", current)
    if (not isinstance(algorithm, str) or not algorithm or algorithm.casefold() == "none"
            or claim_value.get("iss") != identity["issuer"] or claim_value.get("sub") != identity["subject"]
            or claim_value.get("aud") != identity["audience"]
            or not isinstance(expires, (int, float)) or isinstance(expires, bool)
            or not isinstance(not_before, (int, float)) or isinstance(not_before, bool)
            or expires <= current + 60 or not_before > current + 30 or expires <= not_before):
        # This local claim check is only a fail-closed scope guard. Entra remains
        # authoritative for signature, issuer federation and token acceptance.
        raise ValueError("Configured workload identity assertion has invalid scope or lifetime")
    return value


def _tenant_settings_configuration(value: object) -> dict | None:
    if value is None:
        return None
    _fields(value, {"permission_evidence_ref", "desired"})
    evidence = value["permission_evidence_ref"]
    desired = value["desired"]
    if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 500:
        raise ValueError("Tenant-setting permission evidence requires a bounded reference")
    if not isinstance(desired, list) or not desired or len(desired) > 100:
        raise ValueError("Tenant-setting expectations require a non-empty bounded list")
    rows, titles, names = [], set(), set()
    for row in desired:
        _fields(row, {"title", "setting_name", "enabled", "enabled_security_group_ids", "excluded_security_group_ids"})
        title, name = row["title"], row["setting_name"]
        if (not isinstance(title, str) or not title.strip() or title != title.strip() or len(title) > 300
                or not isinstance(name, str) or not SETTING_NAME.fullmatch(name)
                or type(row["enabled"]) is not bool):
            raise ValueError("Tenant-setting expectations require exact title, setting name and enabled state")
        groups = {}
        for key in ("enabled_security_group_ids", "excluded_security_group_ids"):
            values = row[key]
            if not isinstance(values, list) or len(values) > 1000:
                raise ValueError("Tenant-setting group expectations require bounded UUID lists")
            normalized = [dp._uuid(item) for item in values]
            if len(set(normalized)) != len(normalized):
                raise ValueError("Tenant-setting group expectations must not contain duplicates")
            groups[key] = sorted(normalized)
        if set(groups["enabled_security_group_ids"]) & set(groups["excluded_security_group_ids"]):
            raise ValueError("A tenant-setting group cannot be both enabled and excluded")
        if title in titles or name in names:
            raise ValueError("Tenant-setting expectations require unique titles and setting names")
        titles.add(title)
        names.add(name)
        rows.append({"title": title, "setting_name": name, "enabled": row["enabled"], **groups})
    return {"permission_evidence_ref": evidence.strip(), "desired": tuple(rows)}


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
    if value in ({"schema_version": version, "enabled": False} for version in CONFIG_VERSIONS):
        return HostConfiguration(RunnerPolicy())
    if not isinstance(value, dict):
        raise ValueError("Runner input or configuration has missing or unsupported fields")
    _fields(value, CONFIG_KEYS_TEAM if value.get("schema_version") == "1.2.0" else CONFIG_KEYS)
    if value["schema_version"] not in CONFIG_VERSIONS or type(value["enabled"]) is not bool:
        raise ValueError("Unsupported runner configuration version or enable flag")
    independent = value.get("independent_execution_environments", [])
    if (not isinstance(independent, list) or len(independent) > 3
            or any(not isinstance(environment, str) or environment not in {"dev", "test", "prod"}
                   for environment in independent)):
        raise ValueError("Independent execution environments must be an explicit bounded list")
    if len(set(independent)) != len(independent):
        raise ValueError("Independent execution environments contain duplicate values")
    state = _path(value["state_dir"])
    root = repository.root.absolute()
    if state == Path(state.anchor) or state.is_relative_to(root) or root.is_relative_to(state):
        raise ValueError("Runner state must be private and separate from the package repository")
    scopes, identities = [], []
    if not isinstance(value["scopes"], list) or len(value["scopes"]) > 100:
        raise ValueError("Runner scopes must be an explicit bounded list")
    for row in value["scopes"]:
        if not isinstance(row, dict) or set(row) not in (SCOPE_KEYS, SCOPE_KEYS | {"tenant_settings"}):
            raise ValueError("Runner input or configuration has missing or unsupported fields")
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
        elif identity.get("kind") == "workload_identity_federation":
            if value["schema_version"] not in {"1.1.0", "1.2.0"}:
                raise ValueError("Workload federation requires runner configuration schema 1.1.0 or later")
            _fields(identity, {"kind", "client_id", "assertion_file_env", "issuer", "subject", "audience"})
            _reference(identity["assertion_file_env"])
            if identity["assertion_file_env"] == value["signing_key_env"]:
                raise ValueError("Signing and workload assertion references must be separate")
            _bounded_claim(identity["issuer"], "issuer", uri=True)
            _bounded_claim(identity["subject"], "subject")
            _bounded_claim(identity["audience"], "audience")
        else:
            raise ValueError("Only explicit client_secret, managed_identity or workload_identity_federation credentials are supported")
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
        if "tenant_settings" in row and value["schema_version"] not in {"1.1.0", "1.2.0"}:
            raise ValueError("Tenant-setting contracts require runner configuration schema 1.1.0 or later")
        identities.append({"scope": scope, "identity": copy.deepcopy(identity), "permissions": copy.deepcopy(permissions),
            "tenant_settings": _tenant_settings_configuration(row.get("tenant_settings"))})
    for key in ("approvers", "executors"):
        if not isinstance(value[key], list) or any(not isinstance(actor, str) or not ACTOR.fullmatch(actor) for actor in value[key]):
            raise ValueError("Runner actors must use stable github:<provider-account-id> identities")
        if len(set(value[key])) != len(value[key]):
            raise ValueError("Duplicate runner actor")
    policy = RunnerPolicy(value["enabled"], tuple(scopes), frozenset(value["approvers"]),
        frozenset(value["executors"]), frozenset(independent))
    return HostConfiguration(policy, state, _reference(value["signing_key_env"]), tuple(identities))


def _credential(identity: dict, scope: AllowedScope, environment: Mapping[str, str]):
    """Closed SDK choice, called only after the signed attempt is consumed."""
    if identity["kind"] == "workload_identity_federation":
        filename = environment.get(identity["assertion_file_env"])
        if not filename:
            raise ValueError("Configured workload identity assertion path is unavailable")
        path = _path(filename)

    try:
        from azure.identity import ClientAssertionCredential, ClientSecretCredential, ManagedIdentityCredential
    except ImportError as error:
        raise ValueError("The host runtime requires the optional azure-identity package") from error
    if identity["kind"] == "managed_identity":
        return ManagedIdentityCredential(client_id=identity["client_id"], connection_timeout=10, read_timeout=30, retry_total=0)
    if identity["kind"] == "workload_identity_federation":

        def assertion() -> str:
            # The federated assertion is short-lived secret material. Read it only
            # when Azure Identity requests a new assertion, never during status.
            try:
                if not path.is_file() or not 0 < path.stat().st_size <= 64_000:
                    raise ValueError("invalid assertion file")
                with path.open("r", encoding="utf-8") as stream:
                    value = stream.read(64_001)
                if len(value) > 64_000:
                    raise ValueError("invalid assertion file")
                value = value.strip()
                return _validate_assertion(value, identity)
            except (OSError, UnicodeError, ValueError) as error:
                raise ValueError("Configured workload identity assertion is unavailable or invalid") from error

        return ClientAssertionCredential(scope.tenant_id, identity["client_id"], assertion,
            authority="https://login.microsoftonline.com", connection_timeout=10, read_timeout=30, retry_total=0)
    secret = environment.get(identity["client_secret_env"])
    if not secret:
        raise ValueError("Configured runner identity secret is unavailable")
    return ClientSecretCredential(tenant_id=scope.tenant_id, client_id=identity["client_id"], client_secret=secret,
        authority="https://login.microsoftonline.com", connection_timeout=10, read_timeout=30, retry_total=0)


def _entry(configuration: HostConfiguration, scope: AllowedScope) -> dict:
    entry = next((row for row in configuration.identities if row["scope"] == scope), None)
    if entry is None:
        raise ValueError("No identity broker for the exact allowed scope")
    return entry


def _identity_reference_present(identity: dict, environment: Mapping[str, str]) -> bool:
    return identity["kind"] == "managed_identity" or \
        identity.get("client_secret_env", identity.get("assertion_file_env")) in environment


def _token_provider(entry: dict, scope: AllowedScope, environment: Mapping[str, str], credential_factory: Callable) -> Callable[[], str]:
    credential = credential_factory(entry["identity"], scope, environment)

    def token() -> str:
        # Never return credential errors: they can include tenant diagnostics.
        try:
            return credential.get_token(FABRIC_SCOPE).token
        except Exception as error:
            raise ValueError("Configured Fabric identity could not acquire a token") from error
    return token


def client_factory(configuration: HostConfiguration, environment: Mapping[str, str], *, credential_factory: Callable = _credential):
    def create(scope: AllowedScope):
        entry = _entry(configuration, scope)
        return dp.FabWorkspaceClient(scope.tenant_id, scope.principal_id,
            _token_provider(entry, scope, environment, credential_factory), entry["permissions"],
            client_id=entry["identity"]["client_id"])
    return create


class FabTenantSettingsClient(dp.FabWorkspaceClient):
    """Closed, read-only Fabric Admin tenant-settings transport."""

    def list_tenant_settings(self) -> list[dict]:
        items, tokens, token, pages = [], set(), None, 0
        while True:
            if pages >= MAX_TENANT_SETTING_PAGES:
                raise ValueError("Tenant-setting pagination exceeds the per-run request limit")
            suffix = "?" + urlencode({"continuationToken": token}) if token else ""
            page = self._request("admin/tenantsettings" + suffix)
            pages += 1
            if not isinstance(page.get("value"), list):
                raise ValueError("Tenant-setting page is incomplete")
            items.extend(page["value"])
            if len(items) > 10_000:
                raise ValueError("Tenant-setting inventory exceeds the size limit")
            token = page.get("continuationToken")
            if not token:
                if page.get("continuationUri"):
                    raise ValueError("Continuation URI without token is unsupported")
                return items
            if not isinstance(token, str) or not token or token in tokens:
                raise ValueError("Repeated or excessive tenant-setting pagination")
            tokens.add(token)


def tenant_settings_client_factory(configuration: HostConfiguration, environment: Mapping[str, str], *,
                                   credential_factory: Callable = _credential):
    def create(scope: AllowedScope):
        entry = _entry(configuration, scope)
        return FabTenantSettingsClient(scope.tenant_id, scope.principal_id,
            _token_provider(entry, scope, environment, credential_factory), entry["permissions"],
            client_id=entry["identity"]["client_id"])
    return create


def _observed_groups(setting: dict, key: str) -> list[str]:
    values = setting.get(key, [])
    if not isinstance(values, list) or len(values) > 1000:
        raise ValueError("Tenant-setting group response is invalid")
    groups = []
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("Tenant-setting group response is invalid")
        groups.append(dp._uuid(value.get("graphId")))
    if len(set(groups)) != len(groups):
        raise ValueError("Tenant-setting group response contains duplicates")
    return sorted(groups)


def evaluate_tenant_settings(desired: tuple[dict, ...], observed: object) -> dict:
    """Compare selected settings without returning unrelated tenant configuration."""
    if not isinstance(observed, list) or len(observed) > 10_000:
        raise ValueError("Tenant-setting response requires a bounded list")
    rows = []
    for expectation in desired:
        exact = [row for row in observed if isinstance(row, dict) and row.get("title") == expectation["title"]]
        if len(exact) > 1:
            rows.append({"title": expectation["title"], "setting_name": expectation["setting_name"],
                "state": "AMBIGUOUS", "selection": "exact_title", "mismatches": []})
            continue
        if exact:
            selected, selection = exact[0], "exact_title"
        else:
            candidates = [row for row in observed
                if isinstance(row, dict) and row.get("settingName") == expectation["setting_name"]]
            if len(candidates) > 1:
                rows.append({"title": expectation["title"], "setting_name": expectation["setting_name"],
                    "state": "AMBIGUOUS", "selection": "setting_name_fallback", "mismatches": []})
                continue
            if not candidates:
                rows.append({"title": expectation["title"], "setting_name": expectation["setting_name"],
                    "state": "MISSING", "selection": "none", "mismatches": []})
                continue
            selected, selection = candidates[0], "setting_name_fallback"
        if (not isinstance(selected.get("settingName"), str) or not isinstance(selected.get("title"), str)
                or type(selected.get("enabled")) is not bool
                or type(selected.get("canSpecifySecurityGroups")) is not bool):
            raise ValueError("Tenant-setting response is incomplete")
        enabled_groups = _observed_groups(selected, "enabledSecurityGroups")
        excluded_groups = _observed_groups(selected, "excludedSecurityGroups")
        mismatches = []
        if selected["settingName"] != expectation["setting_name"]:
            mismatches.append("setting_name")
        if selected["enabled"] != expectation["enabled"]:
            mismatches.append("enabled")
        if enabled_groups != expectation["enabled_security_group_ids"]:
            mismatches.append("enabled_security_group_ids")
        if excluded_groups != expectation["excluded_security_group_ids"]:
            mismatches.append("excluded_security_group_ids")
        if (expectation["enabled_security_group_ids"] or expectation["excluded_security_group_ids"]) \
                and not selected["canSpecifySecurityGroups"]:
            mismatches.append("group_scope_support")
        rows.append({"title": expectation["title"], "setting_name": expectation["setting_name"],
            "state": "CONFORMANT" if not mismatches else "DRIFT", "selection": selection,
            "mismatches": mismatches, "observed": {"setting_name": selected["settingName"],
                "title": selected["title"], "enabled": selected["enabled"],
                "can_specify_security_groups": selected["canSpecifySecurityGroups"],
                "enabled_security_group_ids": enabled_groups, "excluded_security_group_ids": excluded_groups}})
    states = {row["state"] for row in rows}
    overall = next((state for state in ("AMBIGUOUS", "MISSING", "DRIFT") if state in states), "CONFORMANT")
    return {"state": overall, "settings": rows}


def probe_tenant_settings(configuration: HostConfiguration, scope: AllowedScope, client: object, *,
                          project_ref: str, revision_hash: str) -> dict:
    entry = _entry(configuration, scope)
    contract = entry["tenant_settings"]
    if contract is None:
        raise ValueError("No tenant-setting contract for the exact allowed scope")
    try:
        observed = client.list_tenant_settings()
        comparison = evaluate_tenant_settings(contract["desired"], observed)
    except Exception as error:
        raise ValueError("Tenant-setting conformance probe failed") from error
    return {"schema_version": "1.0.0", "project_ref": project_ref, "revision_hash": revision_hash,
        "tenant_id": scope.tenant_id, "client_id": entry["identity"]["client_id"],
        "principal_id": scope.principal_id, "environment": scope.environment,
        "configuration_readiness": "configured", "permission_proof": {
            "state": "effective_read_observed", "assignment_evidence": "referenced_not_verified"},
        "tenant_conformance": comparison, "tenant_acceptance": "not_recorded",
        "read_only": True, "tenant_actions_performed": True, "whole_project_apply_ready": False,
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "limitations": ["A successful read proves effective access for this observation, not the configured role assignment.",
            "Conformance with host-owned desired settings does not record customer acceptance or authorize a change."]}


def status(configuration: HostConfiguration, project_ref: str, actor: str, environment: Mapping[str, str]) -> dict:
    policy = configuration.policy
    entries = [row for row in configuration.identities if row["scope"].project_ref == project_ref]
    enabled = policy.enabled and bool(entries)
    key_present = configuration.signing_key_env is not None and configuration.signing_key_env in environment
    identity_present = bool(entries) and all(_identity_reference_present(row["identity"], environment) for row in entries)
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
        "Each allowed project scope has an explicit identity and any required credential reference is present; values were not read." if identity_present else "An explicit project identity or its required environment reference is missing.",
        "Configure a dedicated client identity, workload-federation assertion reference or explicit user-assigned managed identity for each allowed scope.")
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
            "actor": actor,
            "independent_execution_environments": sorted(policy.independent_execution_environments),
            "approval_storage_ready": bool(key_configured), "client_factory_configured": bool(broker_configured),
            "identity_broker_available": bool(broker_configured), "execute_endpoint_available": True,
            "tenant_settings_probe_configured": bool(entries) and all(row["tenant_settings"] is not None for row in entries),
            "can_probe_tenant_settings": bool(enabled and broker_configured and fab_available and actor in policy.executors
                and entries and all(row["tenant_settings"] is not None for row in entries)),
            "can_approve": bool(key_configured and broker_configured and state_path_usable and fab_available and actor in policy.approvers),
            "can_execute": bool(key_configured and broker_configured and state_path_usable and fab_available and actor in policy.executors),
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "readiness_scope": "configuration_only", "tenant_actions_performed": False, "checks": checks,
            "configuration_checked_only": True, "identity_verified": False, "whole_project_apply_ready": False,
            "limitations": ["Status checks references only, not credential validity, host ACLs, identity claims or tenant access.",
                "Only exact workspace creation and readback are supported; items, security, data and CI/CD remain separate gates.",
                "An interrupted or uncertain attempt is consumed. Inspect its evidence; never automatically retry."]}


def dispatch(repository: ProjectPackageRevisionRepository, mode: str, payload: dict, *,
             environment: Mapping[str, str] | None = None, factory_builder: Callable = client_factory,
             tenant_factory_builder: Callable = tenant_settings_client_factory,
             clock: Callable = dp._now) -> dict:
    environment = os.environ if environment is None else environment
    extra = {"status": set(), "approve": {"plan", "rationale", "confirm"},
             "execute": {"approval_id", "confirm"}, "outcome": {"approval_id"},
             "tenant_settings": {"tenant_id", "principal_id", "environment"}}
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
    if mode == "tenant_settings":
        try:
            scope = AllowedScope(payload["project_ref"], payload["tenant_id"], payload["principal_id"], payload["environment"])
            if scope not in config.policy.scopes:
                raise ValueError("Tenant-setting request is outside the exact runner scope allowlist")
            entry = _entry(config, scope)
            if entry["tenant_settings"] is None:
                raise ValueError("No tenant-setting contract for the exact allowed scope")
            if not _identity_reference_present(entry["identity"], environment) or not _sdk_available() or not _fab_available():
                raise ValueError("Tenant-setting probe host dependencies are unavailable")
            dp.release_input(repository, payload["project_ref"], payload["revision_hash"])
            client = tenant_factory_builder(config, environment)(scope)
            return probe_tenant_settings(config, scope, client, project_ref=payload["project_ref"],
                revision_hash=payload["revision_hash"])
        except Exception as error:
            raise ValueError("Tenant-setting conformance probe failed") from error
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
    parser.add_argument("--mode", choices=("status", "approve", "execute", "outcome", "tenant_settings"), required=True)
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
