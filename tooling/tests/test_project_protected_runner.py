"""Protected host boundaries exercised without a tenant or identity broker."""
import copy
import json
from dataclasses import replace
from datetime import timedelta
from threading import Event
from concurrent.futures import ThreadPoolExecutor

import pytest

from tooling.superversion.project_package import deployment_plan as dp
from tooling.superversion.project_package.protected_runner import AllowedScope, RunnerPolicy, ProtectedWorkspaceRunner
from tooling.tests.test_project_deployment_plan import NOW, TENANT, PRINCIPAL, FakeClient, plan, observed
from tooling.tests.test_project_architecture_compile import compiler

ACTOR = "operator@example.test"
KEY = b"neutral-test-key-not-a-production-secret-000"
SCOPE = AllowedScope("project_demo", TENANT, PRINCIPAL, "dev")
POLICY = RunnerPolicy(True, (SCOPE,), frozenset({ACTOR}), frozenset({ACTOR}))


@pytest.mark.parametrize("project_ref", ["local_reference", "local_reference_example", "LOCAL_REFERENCE", "Local_Reference_example", None, 123])
def test_local_reference_namespace_cannot_receive_live_authority(project_ref):
    with pytest.raises(ValueError):
        AllowedScope(project_ref, TENANT, PRINCIPAL, "dev")


@pytest.fixture
def released(monkeypatch):
    value = {"compiler_input": compiler(), "release": {"record_sha256": "b" * 64}}
    monkeypatch.setattr(dp, "release_input", lambda *args: copy.deepcopy(value))
    return value


def runner(tmp_path, client=None, **options):
    return ProtectedWorkspaceRunner(None, state_dir=tmp_path / "private-runner", policy=POLICY, signing_key=KEY,
        client_factory=(lambda scope: client) if client else None, clock=lambda: NOW, **options)


def approve(host, value=None):
    return host.approve(value or plan(), actor=ACTOR, rationale="Reviewed the exact released workspace creation plan.", confirm=True)


def execute(host, receipt, **overrides):
    args = {"actor": ACTOR, "project_ref": "project_demo", "revision_hash": "a" * 64, "confirm": True}
    args.update(overrides)
    return host.execute(receipt["approval_id"], **args)


def test_default_disabled_has_no_side_effects(tmp_path, released):
    host = ProtectedWorkspaceRunner(None, state_dir=tmp_path / "private-runner")
    status = host.status("project_demo")
    assert not status["enabled"] and not status["approval_storage_ready"]
    assert not status["execute_endpoint_available"] and not status["whole_project_apply_ready"]
    with pytest.raises(ValueError, match="disabled"):
        approve(host)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("kwargs", [{"enabled": "true"}, {"enabled": True}, {"approvers": {ACTOR}}, {"scopes": [SCOPE]}])
def test_policy_requires_explicit_immutable_authority(kwargs):
    with pytest.raises(ValueError):
        RunnerPolicy(**kwargs)


def test_no_key_no_short_key(tmp_path):
    with pytest.raises(ValueError, match="signing key"):
        ProtectedWorkspaceRunner(None, state_dir=tmp_path, policy=POLICY)
    with pytest.raises(ValueError, match="32 bytes"):
        ProtectedWorkspaceRunner(None, state_dir=tmp_path, policy=POLICY, signing_key=b"short")


@pytest.mark.parametrize("field,value", [("project_ref", "other_project"), ("tenant_id", PRINCIPAL),
    ("principal_id", TENANT), ("environment", "prod")])
def test_exact_scope_blocked_before_approval_storage(tmp_path, released, field, value):
    host, document = runner(tmp_path), plan()
    document[field] = value
    with pytest.raises(ValueError, match="allowlist"):
        approve(host, document)
    assert not list(tmp_path.iterdir())


def test_named_authenticated_actor_and_confirmation_required(tmp_path, released):
    host = runner(tmp_path)
    for actor, confirm in [("forged@example.test", True), (ACTOR, False), (ACTOR, "true")]:
        with pytest.raises(ValueError):
            host.approve(plan(), actor=actor, rationale="Reviewed exact neutral test scope", confirm=confirm)
    assert not list(tmp_path.iterdir())


def test_authoritative_plan_required_even_when_attacker_rehashes(tmp_path, released):
    value = plan()
    value["operations"][0]["desired"]["name"] = "unexpected_workspace"
    value["plan_sha256"] = dp.canonical_sha256({key: v for key, v in value.items() if key != "plan_sha256"})
    with pytest.raises(ValueError, match="authoritative"):
        approve(runner(tmp_path), value)


def test_persistent_approval_reusable_across_host_restart_not_execution(tmp_path, released):
    client = FakeClient()
    host = runner(tmp_path, client)
    receipt = approve(host)
    assert receipt["status"] == "approved_not_executed"
    assert not receipt["tenant_actions_performed"] and not client.creates
    restarted = runner(tmp_path, client)
    result = execute(restarted, receipt)
    assert result["outcome"]["status"] == "workspace_verified"
    assert len(client.creates) == 1
    assert len(list((host.state_dir / "consumed").glob("*.json"))) == 1
    assert len(list((host.state_dir / "outcomes").glob("*.json"))) == 1
    with pytest.raises(ValueError, match="consumed"):
        execute(restarted, receipt)
    assert len(client.creates) == 1


@pytest.mark.parametrize("mutation", ["plan", "approval", "hash", "rename", "malformed"])
def test_tampered_record_or_rehashed_json_has_no_authority(tmp_path, released, mutation):
    client, host = FakeClient(), runner(tmp_path, FakeClient())
    host.client_factory = lambda scope: client
    receipt = approve(host)
    path = host.state_dir / "approvals" / (receipt["approval_id"] + ".json")
    value = json.loads(path.read_text())
    if mutation == "plan": value["payload"]["plan"]["environment"] = "prod"
    if mutation == "approval": value["payload"]["approval"]["actor"] = "attacker"
    if mutation == "hash": value["mac"] = dp.canonical_sha256(value["payload"])
    if mutation == "malformed": value = {"payload": {}}
    if mutation == "rename":
        receipt["approval_id"] = "f" * 64
        path = host.state_dir / "approvals" / (receipt["approval_id"] + ".json")
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="integrity|identity"):
        execute(host, receipt)
    assert client.observations == 0 and not client.creates


def test_foreign_revision_and_actor_and_expiry_before_client(tmp_path, released):
    client, host = FakeClient(), runner(tmp_path)
    host.client_factory = lambda scope: client
    receipt = approve(host)
    for args in [{"project_ref": "other"}, {"revision_hash": "f" * 64}, {"actor": "other"}, {"confirm": False}]:
        with pytest.raises(ValueError):
            execute(host, receipt, **args)
    host.clock = lambda: NOW + timedelta(minutes=15)
    with pytest.raises(ValueError, match="expired"):
        execute(host, receipt)
    assert client.observations == 0


def test_removed_release_fails_before_client(tmp_path, released, monkeypatch):
    client, host = FakeClient(), runner(tmp_path)
    host.client_factory = lambda scope: client
    receipt = approve(host)
    def stale(*args): raise ValueError("Stale released revision")
    monkeypatch.setattr(dp, "release_input", stale)
    with pytest.raises(ValueError, match="Stale"):
        execute(host, receipt)
    assert not client.observations


def test_policy_or_key_rotation_invalidates_previous_approval(tmp_path, released):
    receipt = approve(runner(tmp_path))
    host = runner(tmp_path, FakeClient())
    host.policy = replace(POLICY, executors=frozenset({ACTOR, "second@example.test"}))
    with pytest.raises(ValueError, match="policy changed"):
        execute(host, receipt)
    host.policy, host.key = POLICY, b"other-test-signing-key-000000000000000000"
    with pytest.raises(ValueError, match="integrity"):
        execute(host, receipt)


def test_missing_broker_never_consumes_or_calls_tenant(tmp_path, released):
    host = runner(tmp_path)
    receipt = approve(host)
    assert not host.status("project_demo")["client_factory_configured"]
    with pytest.raises(ValueError, match="broker is not configured"):
        execute(host, receipt)
    assert not (host.state_dir / "consumed").exists()


def test_changed_live_inventory_consumes_and_stops_without_writes(tmp_path, released):
    host, client = runner(tmp_path), FakeClient()
    receipt = approve(host)
    client.state["permissions"]["evidence_ref"] = "changed-permissions"
    host.client_factory = lambda scope: client
    result = execute(host, receipt)
    assert result["outcome"]["status"] == "stopped_requires_reconciliation"
    assert not client.creates
    with pytest.raises(ValueError, match="consumed"):
        execute(host, receipt)


def test_client_failure_is_sanitized_and_consumed(tmp_path, released):
    host = runner(tmp_path)
    def broken(scope): raise RuntimeError("TOP-SECRET-TOKEN")
    host.client_factory = broken
    receipt = approve(host)
    result = execute(host, receipt)
    assert "TOP-SECRET" not in json.dumps(result)
    assert result["outcome"]["status"] == "stopped_requires_reconciliation"
    with pytest.raises(ValueError, match="consumed"):
        execute(host, receipt)


def test_paths_rejected_before_io_and_symlink_storage_rejected(tmp_path, released):
    host = runner(tmp_path)
    for identity in ["../escape", "/absolute", "a" * 63, "A" * 64]:
        with pytest.raises(ValueError, match="approval ID"):
            execute(host, {"approval_id": identity})
    target = tmp_path / "outside"
    target.mkdir()
    try:
        host.state_dir.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not allow test symlinks")
    with pytest.raises(ValueError, match="symlinks"):
        approve(host)


def test_concurrent_approvals_serialize_tenant_before_any_second_client(tmp_path, released):
    host = runner(tmp_path)
    first, second = approve(host), approve(host)
    entered, finish = Event(), Event()
    client = FakeClient()
    def factory(scope):
        entered.set()
        assert finish.wait(timeout=10)
        return client
    host.client_factory = factory
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(execute, host, first)
        assert entered.wait(timeout=10)
        try:
            with pytest.raises(ValueError, match="Tenant runner is active"):
                execute(host, second)
        finally:
            finish.set()
        assert future.result()["outcome"]["status"] == "workspace_verified"
    assert len(client.creates) == 1


def test_interrupted_lock_is_not_automatically_removed(tmp_path, released):
    host, client = runner(tmp_path), FakeClient()
    host.client_factory = lambda scope: client
    receipt = approve(host)
    lock = host.state_dir / "tenant-locks" / TENANT
    lock.mkdir(parents=True)
    with pytest.raises(ValueError, match="interrupted-run reconciliation"):
        execute(host, receipt)
    assert lock.is_dir() and client.observations == 0


def test_real_repository_release_signed_approval_executor_and_stale_head(tmp_path):
    import yaml
    from tooling.tests.test_project_item_compile import full_repository
    repository, revision = full_repository(tmp_path)
    with pytest.raises(ValueError, match="attestation"):
        dp.build_deployment_plan(repository, "project_demo", revision.revision_hash, TENANT, "dev", observed(), now=NOW)
    dp.release_input(repository, "project_demo", revision.revision_hash, actor=ACTOR,
                     rationale="Release only neutral test fixture workspace contracts.")
    value = dp.build_deployment_plan(repository, "project_demo", revision.revision_hash, TENANT, "dev", observed(), now=NOW)
    client = FakeClient()
    host = ProtectedWorkspaceRunner(repository, policy=POLICY, state_dir=tmp_path / "trusted-runner", signing_key=KEY,
        client_factory=lambda scope: client, clock=lambda: NOW)
    receipt = approve(host, value)
    result = execute(host, receipt, revision_hash=revision.revision_hash)
    assert result["outcome"]["status"] == "workspace_verified"
    assert len(client.creates) == 1
    next_plan = dp.build_deployment_plan(repository, "project_demo", revision.revision_hash, TENANT, "dev", client.observe(), now=NOW)
    pending = approve(host, next_plan)
    draft = repository.checkout(tmp_path / "new-draft", revision.revision_hash)
    manifest = yaml.safe_load((draft / "package.yaml").read_text())
    manifest["state"] = "working"
    (draft / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    repository.commit_draft(draft, expected_head_hash=revision.revision_hash)
    before = client.observations
    with pytest.raises(ValueError, match="HEAD|head|revision|current"):
        execute(host, pending, revision_hash=revision.revision_hash)
    assert client.observations == before
    repository.verify()
