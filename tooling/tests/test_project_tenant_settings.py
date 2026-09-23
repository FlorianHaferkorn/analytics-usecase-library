"""Workload federation and tenant-setting conformance, entirely offline."""
import base64
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from tooling.superversion.project_package import runner_host as rh


TENANT = "11111111-1111-1111-1111-111111111111"
PRINCIPAL = "22222222-2222-2222-2222-222222222222"
GROUP = "33333333-3333-3333-3333-333333333333"
EXCLUDED = "44444444-4444-4444-4444-444444444444"
CLIENT = "55555555-5555-5555-5555-555555555555"
ACTOR = "github:123456"
ASSERTION_REF = "STUDIO_RUNNER_TEST_ASSERTION_FILE"
ISSUER = "https://token.actions.githubusercontent.com"
SUBJECT = "repo:neutral/example:environment:dev"
AUDIENCE = "api://AzureADTokenExchange"


def jwt(**changes):
    claims = {"iss": ISSUER, "sub": SUBJECT, "aud": AUDIENCE, "exp": int(time.time()) + 300,
        "nbf": int(time.time()) - 30}
    claims.update(changes)
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
    return f"{encode({'alg': 'RS256', 'typ': 'JWT'})}.{encode(claims)}.signature"


def tenant_contract():
    return {"permission_evidence_ref": "change-record/test-only",
        "desired": [{"title": "Service principals can call Fabric public APIs",
            "setting_name": "ServicePrincipalAccessPermissionAPIs", "enabled": True,
            "enabled_security_group_ids": [GROUP], "excluded_security_group_ids": []}]}


def config_document(tmp_path, *, identity=None, include_contract=True):
    row = {"project_ref": "project_demo", "tenant_id": TENANT, "principal_id": PRINCIPAL,
        "environment": "dev", "identity": identity or {"kind": "workload_identity_federation",
            "client_id": CLIENT, "assertion_file_env": ASSERTION_REF,
            "issuer": ISSUER, "subject": SUBJECT, "audience": AUDIENCE},
        "permissions": {"create_workspaces": False, "capacity_assign_ids": [],
            "domain_assign_ids": [], "evidence_ref": "workspace-permissions-not-proven"}}
    if include_contract:
        row["tenant_settings"] = tenant_contract()
    return {"schema_version": "1.1.0", "enabled": True,
        "state_dir": str(tmp_path / "private-runner"), "signing_key_env": "STUDIO_RUNNER_TEST_HMAC",
        "approvers": [ACTOR], "executors": [ACTOR], "scopes": [row]}


def load(tmp_path, monkeypatch, *, identity=None, include_contract=True):
    path = tmp_path / "host.json"
    path.write_text(json.dumps(config_document(tmp_path, identity=identity, include_contract=include_contract)), encoding="utf-8")
    assertion_path = tmp_path / "assertion.jwt"
    environment = {"STUDIO_RUNNER_CONFIG": str(path), ASSERTION_REF: str(assertion_path)}
    repository = SimpleNamespace(root=tmp_path / "packages")
    monkeypatch.setattr(rh, "_sdk_available", lambda: True)
    monkeypatch.setattr(rh, "_fab_available", lambda: True)
    return repository, environment, path, assertion_path


def desired():
    return rh._tenant_settings_configuration(tenant_contract())["desired"]


def observed(**changes):
    row = {"settingName": "ServicePrincipalAccessPermissionAPIs",
        "title": "Service principals can call Fabric public APIs", "enabled": True,
        "canSpecifySecurityGroups": True,
        "enabledSecurityGroups": [{"graphId": GROUP, "name": "neutral-group"}],
        "excludedSecurityGroups": []}
    row.update(changes)
    return row


def request(**changes):
    value = {"project_ref": "project_demo", "revision_hash": "a" * 64, "actor": ACTOR,
        "tenant_id": TENANT, "principal_id": PRINCIPAL, "environment": "dev"}
    value.update(changes)
    return value


def test_wif_status_checks_reference_only_and_never_reads_path_or_assertion(tmp_path, monkeypatch):
    repository, environment, _, assertion_path = load(tmp_path, monkeypatch)
    class MetadataOnly(dict):
        def get(self, key, default=None):
            assert key == "STUDIO_RUNNER_CONFIG", "Status read a referenced value"
            return super().get(key, default)
        def __getitem__(self, key):
            raise AssertionError("Status read a referenced value")
    result = rh.dispatch(repository, "status", {key: request()[key] for key in ("project_ref", "revision_hash", "actor")},
        environment=MetadataOnly(environment))
    assert result["identity_broker_available"] and result["tenant_settings_probe_configured"]
    assert result["can_probe_tenant_settings"]
    assert not assertion_path.exists()
    assert ASSERTION_REF not in json.dumps(result)


def test_wif_assertion_file_is_read_by_sdk_callback_only(tmp_path, monkeypatch):
    repository, environment, _, assertion_path = load(tmp_path, monkeypatch)
    configuration = rh.load_configuration(repository, environment)
    captured = {}
    class Credential:
        def __init__(self, tenant_id, client_id, func, **kwargs):
            captured.update({"tenant_id": tenant_id, "client_id": client_id, "func": func, **kwargs})
    monkeypatch.setitem(sys.modules, "azure", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "azure.identity", SimpleNamespace(ClientAssertionCredential=Credential,
        ClientSecretCredential=Credential, ManagedIdentityCredential=Credential))
    credential = rh._credential(configuration.identities[0]["identity"], configuration.policy.scopes[0], environment)
    assert isinstance(credential, Credential) and not assertion_path.exists()
    first = jwt()
    second = jwt(exp=int(time.time()) + 600)
    assertion_path.write_text(first, encoding="utf-8")
    assert captured["func"]() == first
    assertion_path.write_text(second, encoding="utf-8")
    assert captured["func"]() == second
    assert captured["tenant_id"] == TENANT and captured["client_id"] == CLIENT
    assert captured["authority"] == "https://login.microsoftonline.com"


def test_runner_client_binds_application_and_service_principal_ids_independently(tmp_path, monkeypatch):
    repository, environment, *_ = load(tmp_path, monkeypatch)
    configuration = rh.load_configuration(repository, environment)
    class Credential:
        def get_token(self, scope):
            raise AssertionError("Construction must not request a token")
    create = rh.tenant_settings_client_factory(configuration, environment,
        credential_factory=lambda identity, scope, env: Credential())
    client = create(configuration.policy.scopes[0])
    assert client.client_id == CLIENT
    assert client.principal_id == PRINCIPAL
    assert client.tenant_id == TENANT


@pytest.mark.parametrize("value", ["secret", "a.b", "a.b.c.d", "a b.c.d", ""])
def test_wif_callback_rejects_invalid_assertions_without_echo(tmp_path, monkeypatch, value):
    repository, environment, _, assertion_path = load(tmp_path, monkeypatch)
    assertion_path.write_text(value, encoding="utf-8")
    captured = {}
    class Credential:
        def __init__(self, tenant_id, client_id, func, **kwargs):
            captured["func"] = func
    monkeypatch.setitem(sys.modules, "azure", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "azure.identity", SimpleNamespace(ClientAssertionCredential=Credential,
        ClientSecretCredential=Credential, ManagedIdentityCredential=Credential))
    configuration = rh.load_configuration(repository, environment)
    rh._credential(configuration.identities[0]["identity"], configuration.policy.scopes[0], environment)
    with pytest.raises(ValueError, match="unavailable or invalid") as raised:
        captured["func"]()
    if value:
        assert value not in str(raised.value)


@pytest.mark.parametrize("change", [{"iss": "https://wrong.example"}, {"sub": "wrong"}, {"aud": "wrong"},
    {"exp": 1}, {"nbf": int(time.time()) + 3600}])
def test_wif_callback_rejects_wrong_scope_or_lifetime_without_echo(tmp_path, monkeypatch, change):
    repository, environment, _, assertion_path = load(tmp_path, monkeypatch)
    assertion_path.write_text(jwt(**change), encoding="utf-8")
    captured = {}
    class Credential:
        def __init__(self, tenant_id, client_id, func, **kwargs):
            captured["func"] = func
    monkeypatch.setitem(sys.modules, "azure", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "azure.identity", SimpleNamespace(ClientAssertionCredential=Credential,
        ClientSecretCredential=Credential, ManagedIdentityCredential=Credential))
    configuration = rh.load_configuration(repository, environment)
    rh._credential(configuration.identities[0]["identity"], configuration.policy.scopes[0], environment)
    with pytest.raises(ValueError, match="unavailable or invalid") as raised:
        captured["func"]()
    assert all(str(value) not in str(raised.value) for value in change.values())


@pytest.mark.parametrize("mutation", ["invalid_client", "raw_assertion", "relative_path", "shared_reference"])
def test_wif_contract_rejects_ambient_or_cross_scope_values(tmp_path, monkeypatch, mutation):
    repository, environment, path, _ = load(tmp_path, monkeypatch)
    document = json.loads(path.read_text(encoding="utf-8"))
    identity = document["scopes"][0]["identity"]
    if mutation == "invalid_client": identity["client_id"] = "ambient"
    if mutation == "raw_assertion": identity["assertion"] = "sensitive"
    if mutation == "shared_reference": identity["assertion_file_env"] = document["signing_key_env"]
    path.write_text(json.dumps(document), encoding="utf-8")
    if mutation == "relative_path":
        environment[ASSERTION_REF] = "assertion.jwt"
        configuration = rh.load_configuration(repository, environment)
        with pytest.raises(ValueError, match="absolute"):
            rh._credential(configuration.identities[0]["identity"], configuration.policy.scopes[0], environment)
    else:
        with pytest.raises(ValueError):
            rh.load_configuration(repository, environment)


@pytest.mark.parametrize("field,value", [("issuer", "http://issuer.example"), ("issuer", "https://issuer.example/#fragment"),
    ("subject", ""), ("audience", " audience")])
def test_wif_contract_requires_exact_bounded_claims(tmp_path, monkeypatch, field, value):
    repository, environment, path, _ = load(tmp_path, monkeypatch)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["scopes"][0]["identity"][field] = value
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        rh.load_configuration(repository, environment)


def test_wif_and_tenant_contract_require_version_1_1(tmp_path, monkeypatch):
    repository, environment, path, _ = load(tmp_path, monkeypatch)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["schema_version"] = "1.0.0"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="schema 1.1.0"):
        rh.load_configuration(repository, environment)


def test_exact_title_precedes_fallback_but_wrong_setting_name_drifts():
    exact = observed(settingName="RenamedInternalKey")
    duplicate_fallback = observed(title="A renamed title")
    result = rh.evaluate_tenant_settings(desired(), [duplicate_fallback, exact, duplicate_fallback])
    assert result["state"] == "DRIFT"
    assert result["settings"][0]["selection"] == "exact_title"
    assert result["settings"][0]["mismatches"] == ["setting_name"]


def test_unique_setting_name_fallback_is_explicit():
    result = rh.evaluate_tenant_settings(desired(), [observed(title="A renamed title")])
    assert result["state"] == "CONFORMANT"
    assert result["settings"][0]["selection"] == "setting_name_fallback"


@pytest.mark.parametrize("inventory,state,selection", [
    ([observed(), observed()], "AMBIGUOUS", "exact_title"),
    ([observed(title="first"), observed(title="second")], "AMBIGUOUS", "setting_name_fallback"),
    ([], "MISSING", "none"),
])
def test_ambiguous_and_missing_settings_never_pass(inventory, state, selection):
    result = rh.evaluate_tenant_settings(desired(), inventory)
    assert result["state"] == state
    assert result["settings"][0]["state"] == state and result["settings"][0]["selection"] == selection


def test_enabled_and_group_scope_drift_is_field_specific():
    result = rh.evaluate_tenant_settings(desired(), [observed(enabled=False,
        enabledSecurityGroups=[], excludedSecurityGroups=[{"graphId": EXCLUDED, "name": "excluded"}])])
    assert result["state"] == "DRIFT"
    assert result["settings"][0]["mismatches"] == [
        "enabled", "enabled_security_group_ids", "excluded_security_group_ids"]


def test_group_scope_requires_api_support():
    result = rh.evaluate_tenant_settings(desired(), [observed(canSpecifySecurityGroups=False)])
    assert result["state"] == "DRIFT" and "group_scope_support" in result["settings"][0]["mismatches"]


def test_tenant_settings_client_collects_every_page_by_token_only(monkeypatch):
    client = rh.FabTenantSettingsClient(TENANT, PRINCIPAL, lambda: "unused", {})
    calls = []
    pages = iter([{"value": [{"settingName": "First"}], "continuationToken": "next page"},
        {"value": [{"settingName": "Second"}]}])
    def request_page(path):
        calls.append(path)
        return next(pages)
    monkeypatch.setattr(client, "_request", request_page)
    assert [row["settingName"] for row in client.list_tenant_settings()] == ["First", "Second"]
    assert calls == ["admin/tenantsettings", "admin/tenantsettings?continuationToken=next+page"]


@pytest.mark.parametrize("pages", [
    [{"value": [], "continuationUri": "https://untrusted.example/next"}],
    [{"value": [], "continuationToken": "repeat"}, {"value": [], "continuationToken": "repeat"}],
    [{"items": []}],
])
def test_tenant_settings_client_fails_closed_on_unsupported_pagination(monkeypatch, pages):
    client = rh.FabTenantSettingsClient(TENANT, PRINCIPAL, lambda: "unused", {})
    iterator = iter(pages)
    monkeypatch.setattr(client, "_request", lambda path: next(iterator))
    with pytest.raises(ValueError):
        client.list_tenant_settings()


def test_tenant_settings_client_honors_documented_request_limit(monkeypatch):
    client = rh.FabTenantSettingsClient(TENANT, PRINCIPAL, lambda: "unused", {})
    calls = []
    def page(path):
        calls.append(path)
        return {"value": [], "continuationToken": f"page-{len(calls)}"}
    monkeypatch.setattr(client, "_request", page)
    with pytest.raises(ValueError, match="per-run request limit"):
        client.list_tenant_settings()
    assert len(calls) == rh.MAX_TENANT_SETTING_PAGES


def test_readonly_probe_is_exactly_scoped_and_keeps_evidence_states_separate(tmp_path, monkeypatch):
    repository, environment, *_ = load(tmp_path, monkeypatch)
    monkeypatch.setattr(rh.dp, "release_input", lambda *args: {"released": True})
    calls = []
    class Client:
        def list_tenant_settings(self):
            calls.append("GET /v1/admin/tenantsettings")
            return [observed()]
    result = rh.dispatch(repository, "tenant_settings", request(), environment=environment,
        tenant_factory_builder=lambda *args: lambda scope: Client())
    assert calls == ["GET /v1/admin/tenantsettings"]
    assert result["configuration_readiness"] == "configured"
    assert result["client_id"] == CLIENT and result["principal_id"] == PRINCIPAL
    assert result["permission_proof"] == {"state": "effective_read_observed", "assignment_evidence": "referenced_not_verified"}
    assert result["tenant_conformance"]["state"] == "CONFORMANT"
    assert result["tenant_acceptance"] == "not_recorded"
    assert result["read_only"] and result["tenant_actions_performed"] and not result["whole_project_apply_ready"]


@pytest.mark.parametrize("field,value", [("tenant_id", GROUP), ("principal_id", GROUP), ("environment", "test"),
    ("project_ref", "another_project")])
def test_probe_refuses_cross_scope_before_constructing_client(tmp_path, monkeypatch, field, value):
    repository, environment, *_ = load(tmp_path, monkeypatch)
    monkeypatch.setattr(rh.dp, "release_input", lambda *args: {"released": True})
    def forbidden(*args):
        raise AssertionError("Cross-scope request constructed a client")
    expected = "scope allowlist" if field == "project_ref" else "conformance probe failed"
    with pytest.raises(ValueError, match=expected):
        rh.dispatch(repository, "tenant_settings", request(**{field: value}), environment=environment,
            tenant_factory_builder=forbidden)


def test_probe_failure_is_sanitized_and_does_not_become_acceptance(tmp_path, monkeypatch):
    repository, environment, *_ = load(tmp_path, monkeypatch)
    monkeypatch.setattr(rh.dp, "release_input", lambda *args: {"released": True})
    class Client:
        def list_tenant_settings(self):
            raise RuntimeError("secret tenant diagnostic")
    with pytest.raises(ValueError) as raised:
        rh.dispatch(repository, "tenant_settings", request(), environment=environment,
            tenant_factory_builder=lambda *args: lambda scope: Client())
    assert str(raised.value) == "Tenant-setting conformance probe failed"
    assert "secret tenant diagnostic" not in str(raised.value)


def test_probe_requires_contract_identity_reference_and_released_revision(tmp_path, monkeypatch):
    repository, environment, path, _ = load(tmp_path, monkeypatch, include_contract=False)
    called = []
    monkeypatch.setattr(rh.dp, "release_input", lambda *args: called.append("release"))
    with pytest.raises(ValueError, match="conformance probe failed"):
        rh.dispatch(repository, "tenant_settings", request(), environment=environment)
    assert not called
    document = config_document(tmp_path)
    path.write_text(json.dumps(document), encoding="utf-8")
    environment.pop(ASSERTION_REF)
    with pytest.raises(ValueError, match="conformance probe failed"):
        rh.dispatch(repository, "tenant_settings", request(), environment=environment)
    assert not called
