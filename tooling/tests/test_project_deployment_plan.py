import base64
import copy
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from pathlib import Path

import pytest
import yaml

from tooling.superversion.project_package import deployment_plan as dp
from tooling.tests.test_project_architecture_compile import compiler

NOW = datetime(2026, 9, 7, 12, tzinfo=timezone.utc)
TENANT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
PRINCIPAL = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
WORKSPACE = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def observed(rows=None):
    return {"tenant_id": TENANT, "principal_id": PRINCIPAL, "observed_at": NOW.isoformat(), "complete": True,
            "workspaces": rows or [], "permissions": {"create_workspaces": True,
            "capacity_assign_ids": ["11111111-1111-4111-8111-111111111111"],
            "domain_assign_ids": ["22222222-2222-4222-8222-222222222222"], "evidence_ref": "access-test-001"}}


def existing(**overrides):
    value = {"id": WORKSPACE, "displayName": "acme_commercial_gold_dev", "capacityId": "11111111-1111-4111-8111-111111111111",
             "domainId": "22222222-2222-4222-8222-222222222222", "capacityAssignmentProgress": "Completed", "type": "Workspace"}
    value.update(overrides)
    return value


@pytest.fixture
def released(monkeypatch):
    value = {"compiler_input": compiler(), "release": {"record_sha256": "b" * 64}}
    monkeypatch.setattr(dp, "release_input", lambda *args: copy.deepcopy(value))
    return value


def plan(state=None):
    return dp.build_deployment_plan(None, "project_demo", "a" * 64, TENANT, "dev", state or observed(), now=NOW)


class FakeClient:
    def __init__(self, state=None):
        self.state, self.creates, self.observations = copy.deepcopy(state or observed()), [], 0
        self.race_at = None
        self.wrong_readback = False

    def observe(self):
        self.observations += 1
        if self.race_at == self.observations:
            self.state["workspaces"].append(existing())
        return copy.deepcopy(self.state)

    def create_workspace(self, body):
        self.creates.append(body)
        self.state["workspaces"].append(existing(**body))
        return {"id": WORKSPACE}

    def get_workspace(self, identity):
        result = copy.deepcopy(next(row for row in self.state["workspaces"] if row["id"] == identity))
        if self.wrong_readback:
            result["domainId"] = TENANT
        return result


def approve(value):
    return dp.approve_deployment(value, actor="operator@example.test", rationale="Reviewed exact create-only tenant scope.", now=NOW)


def test_plan_is_deterministic_and_does_not_mutate(released):
    value = observed()
    assert plan(value) == plan(value)
    assert value == observed()
    assert plan()["operations"][0]["action"] == "create"
    assert plan()["workspace_apply_ready"] is True
    assert plan()["whole_project_apply_ready"] is False
    assert {c["family"] for c in plan()["capabilities"] if c["status"] == "blocked"} == {"items", "security", "cicd", "data"}


def test_noop_exact_identity_and_description(released):
    assert plan(observed([existing()]))["operations"][0]["action"] == "noop"
    released["compiler_input"]["modules"]["architecture_input"]["physical_workspaces"][0]["description"] = "Required"
    assert plan(observed([existing()]))["operations"][0]["action"] == "conflict"


@pytest.mark.parametrize("field,value", [("capacityId", TENANT), ("domainId", TENANT), ("capacityAssignmentProgress", "InProgress"),
                                           ("type", "Personal"), ("displayName", "ACME_COMMERCIAL_GOLD_DEV")])
def test_wrong_assignment_or_case_is_conflict(released, field, value):
    assert plan(observed([existing(**{field: value})]))["operations"][0]["action"] == "conflict"


def test_ambiguous_names_never_adopt(released):
    value = plan(observed([existing(), existing(id=TENANT)]))
    assert not value["workspace_apply_ready"]
    with pytest.raises(ValueError):
        approve(value)


@pytest.mark.parametrize("mutation", ["tenant", "principal", "complete", "old", "future", "duplicate", "unknown", "permissions"])
def test_bad_evidence_fails_closed(released, mutation):
    value = observed()
    if mutation == "tenant": value["tenant_id"] = PRINCIPAL
    if mutation == "principal": value["principal_id"] = "unknown"
    if mutation == "complete": value["complete"] = False
    if mutation == "old": value["observed_at"] = (NOW - timedelta(hours=1)).isoformat()
    if mutation == "future": value["observed_at"] = (NOW + timedelta(hours=1)).isoformat()
    if mutation == "duplicate": value["workspaces"] = [existing(), existing()]
    if mutation == "unknown": value["command"] = "rm"
    if mutation == "permissions": value["permissions"]["evidence_ref"] = ""
    with pytest.raises(ValueError): plan(value)


@pytest.mark.parametrize("field", ["create_workspaces", "capacity_assign_ids", "domain_assign_ids"])
def test_missing_permission_blocks_create(released, field):
    value = observed()
    value["permissions"][field] = False if field == "create_workspaces" else []
    assert plan(value)["operations"][0]["action"] == "blocked"


def test_release_and_environment_still_required(released, monkeypatch):
    with pytest.raises(ValueError, match="Environment"):
        dp.build_deployment_plan(None, "project_demo", "a" * 64, TENANT, "sandbox", observed(), now=NOW)
    monkeypatch.setattr(dp, "release_input", lambda *args: (_ for _ in ()).throw(ValueError("No release")))
    with pytest.raises(ValueError, match="No release"): plan()


def test_execute_create_readback_then_idempotent_noop(released, tmp_path):
    value, client = plan(), FakeClient()
    result = dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW)
    assert result["status"] == "workspace_verified"
    assert result["results"][0]["state"] == "created_verified"
    assert len(client.creates) == 1
    second = plan(client.observe())
    result = dp.execute_workspace_plan(None, second, approve(second), client, tmp_path, now=NOW)
    assert result["results"][0]["state"] == "noop_verified"
    assert len(client.creates) == 1
    with pytest.raises(ValueError, match="already consumed"):
        dp.execute_workspace_plan(None, second, approve(second), client, tmp_path, now=NOW)


def test_scope_bound_approval_cannot_be_reused(released, tmp_path):
    value, client = plan(), FakeClient()
    approval = approve(value)
    approval["environment"] = "prod"
    with pytest.raises(ValueError, match="scope"):
        dp.execute_workspace_plan(None, value, approval, client, tmp_path, now=NOW)
    assert not client.creates


def test_expired_approval_fails_before_call(released, tmp_path):
    value, client = plan(), FakeClient()
    with pytest.raises(ValueError, match="expiry"):
        dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW + timedelta(minutes=16))
    assert client.observations == 0


def test_plan_tampering_and_changed_inventory_stop(released, tmp_path):
    value = plan()
    approval = approve(value)
    value["operations"][0]["desired"]["name"] = "other"
    with pytest.raises(ValueError, match="integrity"):
        dp.execute_workspace_plan(None, value, approval, FakeClient(), tmp_path, now=NOW)
    value = plan()
    client = FakeClient(observed([existing()]))
    with pytest.raises(ValueError, match="changed"):
        dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW)
    assert not client.creates


def test_between_preflight_and_write_race_never_overwrites(released, tmp_path):
    value, client = plan(), FakeClient()
    client.race_at = 2
    result = dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW)
    assert result["status"] == "stopped_requires_reconciliation"
    assert not client.creates
    assert list(tmp_path.glob("*/outcome.json"))


def test_wrong_readback_retains_resource_for_reconciliation(released, tmp_path):
    value, client = plan(), FakeClient()
    client.wrong_readback = True
    result = dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW)
    assert result["status"] == "stopped_requires_reconciliation"
    assert len(client.state["workspaces"]) == 1
    assert result["results"][0]["state"] == "created_unverified"
    assert list(tmp_path.glob("*/*.created.json"))


def test_uncertain_post_is_not_retried(released, tmp_path):
    value, client = plan(), FakeClient()
    def timeout(body):
        client.creates.append(body)
        raise subprocess.TimeoutExpired("fab", 120)
    client.create_workspace = timeout
    result = dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW)
    assert len(client.creates) == 1
    assert result["status"] == "stopped_requires_reconciliation"


def test_reconcile_detects_replaced_id(released):
    value = plan(observed([existing()]))
    result = dp.reconcile_deployment(value, observed([existing(id=TENANT)]), now=NOW)
    assert not result["workspace_match"]
    assert result["results"][0]["state"] == "drift"


def test_rehashed_forged_plan_cannot_bypass_released_authority(released):
    value = plan()
    value["operations"][0]["desired"]["name"] = "unapproved_workspace"
    value["plan_sha256"] = dp.canonical_sha256({k: v for k, v in value.items() if k != "plan_sha256"})
    with pytest.raises(ValueError, match="authoritative"):
        dp.validate_repository_plan(None, value)


def test_expiry_during_observation_prevents_write(released, tmp_path):
    value, client = plan(), FakeClient()
    times = iter([NOW, NOW, NOW + timedelta(minutes=16)])
    result = dp.execute_workspace_plan(None, value, approve(value), client, tmp_path, now=NOW, clock=lambda: next(times))
    assert result["status"] == "stopped_requires_reconciliation"
    assert not client.creates


def jwt(**overrides):
    claims = {"tid": TENANT, "oid": PRINCIPAL, "aud": "https://api.fabric.microsoft.com", "exp": datetime.now(timezone.utc).timestamp() + 300}
    claims.update(overrides)
    return "header." + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=") + ".signature"


def test_fab_closed_commands_and_token_isolation(monkeypatch):
    calls = []
    monkeypatch.setenv("FAB_SPN_CLIENT_SECRET", "ambient-secret")
    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout=json.dumps({"status_code": 201, "text": {"id": WORKSPACE}}))
    client = dp.FabWorkspaceClient(TENANT, PRINCIPAL, jwt, observed()["permissions"], runner=runner)
    name = 'workspace " & calc.exe'
    assert client.create_workspace({"displayName": name, "capacityId": TENANT, "domainId": PRINCIPAL})["id"] == WORKSPACE
    args, kwargs = calls[0]
    assert args[:6] == ["fab", "api", "workspaces", "-A", "fabric", "-X"]
    assert "-c" not in args and kwargs["shell"] is False
    assert json.loads(args[-1])["displayName"] == name
    assert "FAB_SPN_CLIENT_SECRET" not in kwargs["env"]
    assert kwargs["env"]["FAB_TENANT_ID"] == TENANT
    assert "x-ms-fabric-skill=deployment-pipelines-authoring-cli" in args


@pytest.mark.parametrize("claim", [{"tid": PRINCIPAL}, {"oid": TENANT}, {"aud": "https://management.azure.com"}, {"exp": 0}])
def test_fab_refuses_wrong_identity_token_before_request(claim):
    def never(*args, **kwargs): raise AssertionError("must not invoke CLI")
    client = dp.FabWorkspaceClient(TENANT, PRINCIPAL, lambda: jwt(**claim), observed()["permissions"], runner=never)
    with pytest.raises(ValueError, match="token"):
        client.get_workspace(WORKSPACE)


@pytest.mark.parametrize("claims", [{}, {"azp": TENANT}, {"appid": TENANT},
    {"azp": WORKSPACE, "appid": TENANT}])
def test_fab_refuses_missing_or_conflicting_application_identity_before_request(claims):
    def never(*args, **kwargs): raise AssertionError("must not invoke CLI")
    client = dp.FabWorkspaceClient(TENANT, PRINCIPAL, lambda: jwt(**claims), observed()["permissions"],
        runner=never, client_id=WORKSPACE)
    with pytest.raises(ValueError, match="application"):
        client.get_workspace(WORKSPACE)


@pytest.mark.parametrize("claim_name", ["azp", "appid"])
def test_fab_accepts_explicit_matching_application_identity(claim_name):
    client = dp.FabWorkspaceClient(TENANT, PRINCIPAL, lambda: jwt(**{claim_name: WORKSPACE}),
        observed()["permissions"], client_id=WORKSPACE,
        runner=lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(existing())))
    assert client.get_workspace(WORKSPACE)["id"] == WORKSPACE


def test_fab_pagination_and_get_readback(monkeypatch):
    calls = []
    monkeypatch.setattr(dp, "_now", lambda value=None: value or NOW)
    def runner(args, **kwargs):
        calls.append(args[2])
        result = ({"value": [{"id": WORKSPACE}], "continuationToken": "opaque +/"} if args[2] == "workspaces" else
                  {"value": []} if "continuationToken=" in args[2] else existing())
        return SimpleNamespace(stdout=json.dumps(result))
    client = dp.FabWorkspaceClient(TENANT, PRINCIPAL, lambda: jwt(exp=NOW.timestamp()+300), observed()["permissions"], runner=runner)
    state = client.observe()
    assert len(state["workspaces"]) == 1
    assert calls == ["workspaces", "workspaces?continuationToken=opaque+%2B%2F", "workspaces/" + WORKSPACE]


def test_fab_does_not_treat_error_or_lro_as_success():
    for status in [202, 400, 403, 429, 500]:
        client = dp.FabWorkspaceClient(TENANT, PRINCIPAL, jwt, observed()["permissions"],
            runner=lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps({"status_code": status, "text": {"id": WORKSPACE}})))
        with pytest.raises(ValueError, match="status"):
            client.create_workspace({"displayName": "safe", "capacityId": TENANT, "domainId": PRINCIPAL})


def test_real_released_repository_plan_cli_and_executor(tmp_path):
    from tooling.superversion.project_package.migrations import migrate_project_package
    from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository
    root = Path(__file__).resolve().parents[2]
    schemas = root / "tooling/generator/schemas"
    package = migrate_project_package(root / "tooling/tests/fixtures/project_package/v1", tmp_path / "package", schemas)
    manifest = yaml.safe_load((package / "package.yaml").read_text(encoding="utf-8"))
    definition = {"id": "definition_environment", "source": {"adapter": "engagement_ledger_package_1_0", "raw_id": "E-1", "source_ref": "fixture://decision", "source_hash": "c"*64},
        "title": "Environment", "question": {"technical_text": "Which environments?"},
        "recommendation": {"text": "Dev/test/prod", "basis": "Fixture", "confidence_raw": "high", "confidence": "high"},
        "options": [{"id": "three", "label": "Dev/test/prod", "kind": "proposal"}], "option_details": [],
        "decider": {"text": "Fixture owner", "role_ref": None}, "consequence_if_unresolved": "No deployment",
        "resolution_method": {"where_to_look": "Fixture", "who_knows": "Owner", "if_unclear": "Block"},
        "customer_copy": {"question": "Which environments?", "consequence": "Isolation", "why": "Testing"},
        "due": {"raw": "Before build", "gate": "before_build"}, "placeholder_refs": []}
    decision = {"schema_version": "2.0.0", "definitions": [definition], "instances": [{"id": "decision_environment_model",
        "definition_ref": "definition_environment", "scope_refs": [], "revision": 1, "initialization": "imported",
        "selection": {"state": "confirmed", "option_ref": "three", "custom_value": None},
        "approval": {"state": "approved", "proposed_by": "Fixture", "decided_by": "Owner", "rationale": "Approved fixture environment isolation"},
        "readiness": {"state": "ready_for_decision"}, "delivery": {"state": "not_compiled"}}]}
    (package / "discovery/decision_set.yaml").write_text(yaml.safe_dump(decision), encoding="utf8")
    next(row for row in manifest["modules"] if row["module_type"] == "decision_set")["sha256"] = dp.canonical_sha256(decision)
    architecture = compiler()["modules"]["architecture_input"]
    (package / "architecture.yaml").write_text(yaml.safe_dump(architecture), encoding="utf8")
    manifest["modules"].append({"module_type": "architecture_input", "path": "architecture.yaml",
        "schema_id": json.loads((schemas / "project_architecture_input.schema.json").read_text(encoding="utf-8"))["$id"], "sha256": dp.canonical_sha256(architecture)})
    manifest["state"] = "approved"
    (package / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf8")
    repository = ProjectPackageRevisionRepository(tmp_path / "repositories/project_demo", schemas)
    revision = repository.commit(package).revision_hash
    with pytest.raises(ValueError, match="attestation"):
        dp.build_deployment_plan(repository, "project_demo", revision, TENANT, "dev", observed(), now=NOW)
    dp.release_input(repository, "project_demo", revision, actor="fixture_owner", rationale="Reviewed all fixture inputs for bounded deployment.")
    value = dp.build_deployment_plan(repository, "project_demo", revision, TENANT, "dev", observed(), now=NOW)
    dp.validate_repository_plan(repository, value)
    result = dp.execute_workspace_plan(repository, value, approve(value), FakeClient(), tmp_path / "runs", now=NOW)
    assert result["status"] == "workspace_verified"
    wrong = copy.deepcopy(value)
    wrong["operations"][0]["desired"]["capacity_id"] = TENANT
    wrong["plan_sha256"] = dp.canonical_sha256({k: v for k, v in wrong.items() if k != "plan_sha256"})
    with pytest.raises(ValueError, match="authoritative"):
        dp.reconcile_deployment(wrong, observed(), now=NOW, repository=repository)
    fresh = observed()
    fresh["observed_at"] = datetime.now(timezone.utc).isoformat()
    args = [sys.executable, "-m", "tooling.superversion.project_package.deployment_plan", "--repository", str(repository.root), "--schemas", str(schemas)]
    planned = subprocess.run([*args, "--mode", "plan"], input=json.dumps({"project_ref": "project_demo", "revision_hash": revision,
        "tenant_id": TENANT, "environment": "dev", "observed_state": fresh}), text=True, capture_output=True, cwd=root, check=True, encoding="utf-8", errors="replace")
    assert json.loads(planned.stdout)["value"]["plan_sha256"] == value["plan_sha256"]
    rejected = subprocess.run([*args, "--mode", "reconcile"], input=json.dumps({"plan": wrong, "observed_state": fresh}), text=True, capture_output=True, cwd=root, encoding="utf-8", errors="replace")
    assert rejected.returncode == 1
    assert "authoritative" in json.loads(rejected.stdout)["error"]
