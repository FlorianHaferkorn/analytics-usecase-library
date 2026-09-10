"""Authenticated server subprocess and credential selection, entirely offline."""
import base64
import copy
import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from tooling.superversion.project_package import runner_host as rh
from tooling.superversion.project_package import deployment_plan as dp
from tooling.superversion.project_package.protected_runner import ProtectedWorkspaceRunner
from tooling.tests.test_project_deployment_plan import NOW, TENANT, PRINCIPAL, FakeClient, plan, observed
from tooling.tests.test_project_architecture_compile import compiler

ACTOR = "github:123456"
KEY_REF = "STUDIO_RUNNER_TEST_HMAC"
SECRET_REF = "STUDIO_RUNNER_TEST_CLIENT_SECRET"
KEY = base64.b64encode(b"synthetic-unit-test-signing-key-00000000").decode()
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def deterministic_cli_discovery(monkeypatch):
    monkeypatch.setattr(rh.shutil, "which", lambda name: "C:/test-host/fab.exe" if name == "fab" else None)


def config_document(tmp_path):
    return {"schema_version": "1.0.0", "enabled": True, "state_dir": str(tmp_path / "private-runner"),
        "signing_key_env": KEY_REF, "approvers": [ACTOR], "executors": [ACTOR],
        "scopes": [{"project_ref": "project_demo", "tenant_id": TENANT, "principal_id": PRINCIPAL, "environment": "dev",
            "identity": {"kind": "client_secret", "client_id": PRINCIPAL, "client_secret_env": SECRET_REF},
            "permissions": observed()["permissions"]}]}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    path = tmp_path / "host.json"
    document = config_document(tmp_path)
    path.write_text(json.dumps(document), encoding="utf-8")
    environment = {"STUDIO_RUNNER_CONFIG": str(path), KEY_REF: KEY, SECRET_REF: "fake-not-a-credential"}
    repository = SimpleNamespace(root=tmp_path / "packages")
    monkeypatch.setattr(rh, "_sdk_available", lambda: True)
    monkeypatch.setattr(dp, "release_input", lambda *args: {"compiler_input": compiler(), "release": {"record_sha256": "b" * 64}})
    return repository, environment, document, path


def request(**values):
    return {"project_ref": "project_demo", "revision_hash": "a" * 64, "actor": ACTOR, **values}


def dispatch(setup, mode, value, client=None, clock=lambda: NOW):
    repository, environment, *_ = setup
    return rh.dispatch(repository, mode, value, environment=environment,
        factory_builder=lambda *args: (lambda scope: client or FakeClient()), clock=clock)


def approved(setup):
    return dispatch(setup, "approve", request(plan=plan(), rationale="Approved exact neutral test workspace scope.", confirm=True))


def test_absent_configuration_is_disabled_without_side_effects(tmp_path):
    result = rh.dispatch(SimpleNamespace(root=tmp_path / "packages"), "status", request(), environment={})
    assert not result["enabled"] and not result["can_approve"] and not result["can_execute"]
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match="disabled"):
        rh.dispatch(SimpleNamespace(root=tmp_path / "packages"), "execute", request(approval_id="b" * 64, confirm=True), environment={})


def test_status_reads_only_config_not_secrets_and_never_constructs_broker(setup):
    repository, environment, _, path = setup
    class MetadataOnly(dict):
        def get(self, key, default=None):
            assert key == "STUDIO_RUNNER_CONFIG", "Status read a secret value"
            return super().get(key, default)
        def __getitem__(self, key):
            raise AssertionError("Status read an environment value")
    def forbidden(*args):
        raise AssertionError("Status constructed a broker")
    result = rh.dispatch(repository, "status", request(), environment=MetadataOnly(environment), factory_builder=forbidden)
    assert result["enabled"] and result["can_approve"] and result["can_execute"]
    assert result["configuration_checked_only"] and not result["identity_verified"]
    assert not (path.parent / "private-runner").exists()
    assert KEY not in json.dumps(result) and SECRET_REF not in json.dumps(result)


@pytest.mark.parametrize("missing", [KEY_REF, SECRET_REF, "sdk", "cli"])
def test_missing_host_dependency_blocks_readiness_and_approval(setup, monkeypatch, missing):
    if missing == "sdk":
        monkeypatch.setattr(rh, "_sdk_available", lambda: False)
    elif missing == "cli":
        monkeypatch.setattr(rh.shutil, "which", lambda name: None)
    else:
        setup[1].pop(missing)
    status = dispatch(setup, "status", request())
    assert not status["can_approve"] and not status["can_execute"]
    with pytest.raises(ValueError, match="references"):
        approved(setup)


def test_readiness_check_contract_distinguishes_configuration_from_verification(setup):
    result = dispatch(setup, "status", request())
    checks = {row["id"]: row for row in result["checks"]}
    assert len(checks) == 12
    assert {row["state"] for row in result["checks"]} == {"configured", "not_verified"}
    assert all(set(row) == {"id", "title", "state", "detail", "action"} for row in result["checks"])
    assert all(row["title"] and row["detail"] and row["action"] for row in result["checks"])
    assert {key for key, row in checks.items() if row["state"] == "not_verified"} == {
        "identity_permissions", "host_recovery", "tenant_acceptance"}
    assert "no directory" in checks["state_storage"]["detail"]
    assert result["readiness_scope"] == "configuration_only" and not result["tenant_actions_performed"]
    assert not result["whole_project_apply_ready"] and result["checked_at"].endswith("Z")
    assert rh.datetime.fromisoformat(result["checked_at"]).utcoffset().total_seconds() == 0


def test_disabled_full_config_reports_references_without_authorizing_execution(setup):
    setup[2]["enabled"] = False
    setup[3].write_text(json.dumps(setup[2]), encoding="utf-8")
    result = dispatch(setup, "status", request())
    checks = {row["id"]: row for row in result["checks"]}
    assert checks["host_policy"]["state"] == "missing"
    assert checks["signing_reference"]["state"] == checks["identity_reference"]["state"] == "configured"
    assert not result["can_approve"] and not result["can_execute"]


def test_scope_and_actor_readiness_checks_are_independent(setup):
    result = dispatch(setup, "status", request(project_ref="unlisted", actor="github:999"))
    checks = {row["id"]: row for row in result["checks"]}
    assert checks["host_policy"]["state"] == "configured"
    assert all(checks[key]["state"] == "missing" for key in ("project_scope", "approver", "executor", "identity_reference"))
    assert not result["can_approve"] and not result["can_execute"]


def test_status_never_writes_calls_processes_or_reads_secret_values(setup, monkeypatch):
    class MetadataOnly(dict):
        def get(self, key, default=None):
            assert key == "STUDIO_RUNNER_CONFIG"
            return super().get(key, default)
        def __getitem__(self, key):
            raise AssertionError("Secret value read")
    def forbidden(*args, **kwargs):
        raise AssertionError("Readiness attempted a side effect")
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(rh, "_credential", forbidden)
    result = rh.dispatch(setup[0], "status", request(), environment=MetadataOnly(setup[1]), factory_builder=forbidden)
    assert result["can_approve"] and result["tenant_actions_performed"] is False
    assert not (setup[3].parent / "private-runner").exists()


@pytest.mark.parametrize("metadata", [None, "", "not a version", "1.0\n", 123, "1" * 101])
def test_sdk_metadata_missing_or_malformed_is_not_ready(monkeypatch, metadata):
    monkeypatch.setattr(rh.importlib.metadata, "version", lambda name: metadata)
    assert rh._sdk_available() is False


@pytest.mark.parametrize("error", [rh.importlib.metadata.PackageNotFoundError("azure-identity"), OSError("unreadable"), ValueError("malformed"), KeyError("Version")])
def test_sdk_metadata_failure_is_not_ready(monkeypatch, error):
    def broken(name):
        raise error
    monkeypatch.setattr(rh.importlib.metadata, "version", broken)
    assert rh._sdk_available() is False


def test_valid_sdk_metadata_is_not_a_token_or_import_test(monkeypatch):
    monkeypatch.setattr(rh.importlib.metadata, "version", lambda name: "1.24.0b1")
    assert rh._sdk_available() is True


def test_existing_state_path_is_not_claimed_writable_or_secure(setup):
    Path(setup[2]["state_dir"]).mkdir()
    check = next(row for row in dispatch(setup, "status", request())["checks"] if row["id"] == "state_storage")
    assert check["state"] == "configured" and "ACLs and writability were not tested" in check["detail"]


def test_existing_state_file_blocks_approval_without_overwriting(setup):
    path = Path(setup[2]["state_dir"])
    path.write_text("preserve existing file", encoding="utf-8")
    result = dispatch(setup, "status", request())
    check = next(row for row in result["checks"] if row["id"] == "state_storage")
    assert check["state"] == "missing" and not result["can_approve"] and not result["can_execute"]
    with pytest.raises(ValueError, match="references"):
        approved(setup)
    assert path.read_text(encoding="utf-8") == "preserve existing file"


@pytest.mark.parametrize("field,value", [("token", "untrusted"), ("command", "fab"), ("state_dir", "C:/public"), ("signing_key", "attacker")])
def test_browser_configuration_injection_rejected(setup, field, value):
    with pytest.raises(ValueError, match="fields"):
        dispatch(setup, "status", request(**{field: value}))


@pytest.mark.parametrize("actor", ["email@example.test", "github:123:admin", "github:other", "", " github:123456"])
def test_stable_provider_identity_required(setup, actor):
    with pytest.raises(ValueError, match="operator"):
        dispatch(setup, "status", request(actor=actor))


@pytest.mark.parametrize("mutation", ["wildcard", "ambient", "relative", "overlap", "unknown", "short-id", "secret-body", "same-secret", "string-enabled", "duplicate"])
def test_host_configuration_refuses_unsafe_or_ambiguous_values(setup, mutation):
    repository, environment, document, path = setup
    if mutation == "wildcard": document["approvers"] = ["*"]
    if mutation == "ambient": document["scopes"][0]["identity"] = {"kind": "default"}
    if mutation == "relative": document["state_dir"] = "private-runner"
    if mutation == "overlap": document["state_dir"] = str(repository.root / "state")
    if mutation == "unknown": document["command"] = "arbitrary"
    if mutation == "short-id": document["scopes"][0]["identity"]["client_id"] = "client"
    if mutation == "secret-body": document["scopes"][0]["identity"]["client_secret"] = "raw-secret"
    if mutation == "same-secret": document["scopes"][0]["identity"]["client_secret_env"] = KEY_REF
    if mutation == "string-enabled": document["enabled"] = "true"
    if mutation == "duplicate": document["scopes"].append(copy.deepcopy(document["scopes"][0]))
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        rh.load_configuration(repository, environment)


def test_minimal_disabled_config_never_reads_signing_key(setup):
    setup[3].write_text(json.dumps({"schema_version": "1.0.0", "enabled": False}), encoding="utf-8")
    assert not dispatch(setup, "status", request())["enabled"]


def test_approval_execute_retrieve_is_persistent_and_one_shot(setup):
    receipt, client = approved(setup), FakeClient()
    assert dispatch(setup, "outcome", request(approval_id=receipt["approval_id"]))["status"] == "approved_not_executed"
    result = dispatch(setup, "execute", request(approval_id=receipt["approval_id"], confirm=True), client)
    assert result["outcome"]["status"] == "workspace_verified"
    assert len(client.creates) == 1
    readback = dispatch(setup, "outcome", request(approval_id=receipt["approval_id"]))
    assert readback["status"] == "completed" and readback["result"] == result
    with pytest.raises(ValueError, match="consumed"):
        dispatch(setup, "execute", request(approval_id=receipt["approval_id"], confirm=True), client)


def test_outcome_survives_expiry_and_stale_head_without_renewing(setup, monkeypatch):
    receipt = approved(setup)
    later = lambda: NOW + timedelta(hours=2)
    def stale(*args):
        raise AssertionError("Historical evidence consulted HEAD")
    monkeypatch.setattr(dp, "release_input", stale)
    assert dispatch(setup, "outcome", request(approval_id=receipt["approval_id"]), clock=later)["status"] == "expired"
    with pytest.raises(ValueError, match="expired"):
        dispatch(setup, "execute", request(approval_id=receipt["approval_id"], confirm=True), clock=later)


def test_inflight_consumption_is_visible_and_not_reported_as_success(setup):
    receipt = approved(setup)
    config = rh.load_configuration(setup[0], setup[1])
    host = ProtectedWorkspaceRunner(setup[0], policy=config.policy, state_dir=config.state_dir,
        signing_key=base64.b64decode(KEY), clock=lambda: NOW)
    host._persist(config.state_dir / "consumed" / (receipt["approval_id"] + ".json"),
        {"approval_id": receipt["approval_id"], "project_ref": "project_demo", "revision_hash": "a" * 64, "plan_sha256": receipt["plan_sha256"]})
    result = dispatch(setup, "outcome", request(approval_id=receipt["approval_id"]))
    assert result["status"] == "consumed_requires_reconciliation" and not result["whole_project_verified"]


@pytest.mark.parametrize("field,value", [("project_ref", "foreign"), ("revision_hash", "b" * 64), ("actor", "github:99")])
def test_foreign_evidence_request_rejected(setup, field, value):
    receipt = approved(setup)
    with pytest.raises(ValueError):
        dispatch(setup, "outcome", request(approval_id=receipt["approval_id"], **{field: value}))


def test_tampered_evidence_is_not_displayed_as_trusted(setup):
    receipt = approved(setup)
    path = setup[3].parent / "private-runner" / "approvals" / (receipt["approval_id"] + ".json")
    record = json.loads(path.read_text(encoding="utf-8"))
    record["payload"]["plan"]["environment"] = "prod"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        dispatch(setup, "outcome", request(approval_id=receipt["approval_id"]))


def test_optional_sdk_broker_requests_only_fabric_scope_lazily(setup):
    config = rh.load_configuration(setup[0], setup[1])
    calls = []
    class Credential:
        def get_token(self, scope):
            calls.append(scope)
            return SimpleNamespace(token="synthetic-token")
    def credential(identity, scope, environment):
        assert identity["kind"] == "client_secret" and scope.tenant_id == TENANT
        calls.append("constructed")
        return Credential()
    create = rh.client_factory(config, setup[1], credential_factory=credential)
    assert not calls
    client = create(config.policy.scopes[0])
    assert calls == ["constructed"]
    assert client.token_provider() == "synthetic-token"
    assert calls == ["constructed", rh.FABRIC_SCOPE]


def test_sdk_selection_is_explicit_without_default_credential(setup, monkeypatch):
    calls = []
    class Credential:
        def __init__(self, **kwargs):
            calls.append(kwargs)
    monkeypatch.setitem(sys.modules, "azure", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "azure.identity", SimpleNamespace(ClientSecretCredential=Credential, ManagedIdentityCredential=Credential))
    config = rh.load_configuration(setup[0], setup[1])
    rh._credential(config.identities[0]["identity"], config.policy.scopes[0], setup[1])
    assert calls[0]["tenant_id"] == TENANT and calls[0]["client_id"] == PRINCIPAL
    assert calls[0]["authority"] == "https://login.microsoftonline.com"
    rh._credential({"kind": "managed_identity", "client_id": PRINCIPAL}, config.policy.scopes[0], {})
    assert calls[1]["client_id"] == PRINCIPAL and "client_secret" not in calls[1]


def test_broker_startup_failure_is_consumed_and_sanitized(setup):
    receipt = approved(setup)
    def builder(*args):
        def fail(scope):
            raise RuntimeError("secret-value-must-never-leak")
        return fail
    result = rh.dispatch(setup[0], "execute", request(approval_id=receipt["approval_id"], confirm=True),
        environment=setup[1], factory_builder=builder, clock=lambda: NOW)
    assert "secret-value" not in json.dumps(result)
    assert result["outcome"]["status"] == "stopped_requires_reconciliation"
    assert dispatch(setup, "outcome", request(approval_id=receipt["approval_id"]))["result"] == result


def test_real_subprocess_disabled_status_and_injected_fields(tmp_path):
    env = {key: value for key, value in os.environ.items() if not key.startswith("STUDIO_RUNNER_")}
    args = [sys.executable, "-m", "tooling.superversion.project_package.runner_host", "--repository", str(tmp_path / "packages"),
        "--schemas", str(ROOT / "tooling/generator/schemas"), "--mode", "status"]
    result = subprocess.run(args, input=json.dumps(request()), text=True, capture_output=True, cwd=ROOT, env=env, timeout=30, encoding="utf-8", errors="replace")
    assert result.returncode == 0 and not json.loads(result.stdout)["value"]["enabled"]
    result = subprocess.run(args, input=json.dumps(request(token="raw-secret-value")), text=True, capture_output=True, cwd=ROOT, env=env, timeout=30, encoding="utf-8", errors="replace")
    assert result.returncode == 1 and not json.loads(result.stdout)["ok"]
    assert "raw-secret-value" not in result.stdout + result.stderr


def test_real_released_repository_host_approval_execute_readback(tmp_path, monkeypatch):
    from tooling.tests.test_project_item_compile import full_repository
    repository, revision = full_repository(tmp_path)
    document = config_document(tmp_path)
    path = tmp_path / "trusted-host.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    environment = {"STUDIO_RUNNER_CONFIG": str(path), KEY_REF: KEY, SECRET_REF: "test-only"}
    monkeypatch.setattr(rh, "_sdk_available", lambda: True)
    dp.release_input(repository, "project_demo", revision.revision_hash, actor=ACTOR,
        rationale="Release the neutral integration-test workspace contract.")
    value = dp.build_deployment_plan(repository, "project_demo", revision.revision_hash, TENANT, "dev", observed(), now=NOW)
    base = request(revision_hash=revision.revision_hash)
    client = FakeClient()
    options = {"environment": environment, "factory_builder": lambda *args: lambda scope: client, "clock": lambda: NOW}
    receipt = rh.dispatch(repository, "approve", {**base, "plan": value, "confirm": True,
        "rationale": "Approve this exact integration-test plan with no live tenant."}, **options)
    result = rh.dispatch(repository, "execute", {**base, "approval_id": receipt["approval_id"], "confirm": True}, **options)
    assert result["outcome"]["status"] == "workspace_verified" and len(client.creates) == 1
    stored = rh.dispatch(repository, "outcome", {**base, "approval_id": receipt["approval_id"]}, **options)
    assert stored["result"] == result
    assert not stored["whole_project_verified"]
    repository.verify()


@pytest.mark.parametrize("mutation", ["outcome", "claim"])
def test_swapped_signed_record_from_another_attempt_refused(setup, mutation):
    first, second = approved(setup), approved(setup)
    dispatch(setup, "execute", request(approval_id=first["approval_id"], confirm=True))
    state = setup[3].parent / "private-runner"
    folder = "outcomes" if mutation == "outcome" else "consumed"
    original = state / folder / (first["approval_id"] + ".json")
    target = state / folder / (second["approval_id"] + ".json")
    target.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        dispatch(setup, "outcome", request(approval_id=second["approval_id"]))


def test_emergency_disable_preserves_readonly_signed_evidence_without_reenabling(setup, monkeypatch):
    receipt = approved(setup)
    result = dispatch(setup, "execute", request(approval_id=receipt["approval_id"], confirm=True))
    setup[2]["enabled"] = False
    setup[3].write_text(json.dumps(setup[2]), encoding="utf-8")
    status = dispatch(setup, "status", request())
    assert not status["enabled"] and not status["can_approve"] and not status["can_execute"]
    setup[1].pop(SECRET_REF)
    monkeypatch.setattr(rh, "_sdk_available", lambda: False)
    def forbidden(*args):
        raise AssertionError("Read-only recovery constructed a broker")
    readback = rh.dispatch(setup[0], "outcome", request(approval_id=receipt["approval_id"]),
        environment=setup[1], factory_builder=forbidden, clock=lambda: NOW)
    assert readback["result"] == result
    with pytest.raises(ValueError, match="disabled"):
        approved(setup)
    with pytest.raises(ValueError, match="disabled"):
        dispatch(setup, "execute", request(approval_id=receipt["approval_id"], confirm=True))


@pytest.mark.parametrize("mutation", ["minimal", "scope", "actor", "key", "foreign-revision"])
def test_disabled_recovery_still_requires_scope_actor_key_and_exact_revision(setup, mutation):
    receipt = approved(setup)
    setup[2]["enabled"] = False
    payload = request(approval_id=receipt["approval_id"])
    if mutation == "scope": setup[2]["scopes"][0]["project_ref"] = "other_project"
    if mutation == "actor": setup[2]["approvers"] = setup[2]["executors"] = ["github:99"]
    if mutation == "key": setup[1][KEY_REF] = base64.b64encode(b"different-synthetic-key-00000000000").decode()
    if mutation == "foreign-revision": payload["revision_hash"] = "f" * 64
    document = {"schema_version": "1.0.0", "enabled": False} if mutation == "minimal" else setup[2]
    setup[3].write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        dispatch(setup, "outcome", payload)
