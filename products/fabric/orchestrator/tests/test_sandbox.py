"""AP-2 sandbox lifecycle: up, deploy, down and every guardrail, against a fake Fabric.

No network and no ``msal``: the sandbox takes the orchestrator pieces injected. The fake keeps a
workspace table and records each call, so every test can assert that nothing was written after
a guardrail fired. ``test_the_orchestrator_still_offers_what_the_sandbox_calls`` reads
``orchestrator.py`` and ``fabric_release.py`` as source (AST), so the contract is checked in CI
too, where the orchestrator's own tests skip for lack of ``msal``.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("_aluca_sandbox", HERE / "sandbox.py")
sb = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = sb          # dataclasses resolve their module by name
_spec.loader.exec_module(sb)

WS = "11111111-2222-3333-4444-555555555555"


class NotFound(Exception):
    status_code = 404


class FakeApi:
    def __init__(self, store, calls):
        self.store, self.calls = store, calls

    def get(self, endpoint):
        self.calls.append(("GET", endpoint))
        wid = endpoint.rsplit("/", 1)[-1]
        if wid not in self.store:
            raise NotFound(endpoint)
        return self.store[wid]


class FakeWorkspaces:
    def __init__(self, store, calls, delete_leaves_readable=False):
        self.store, self.calls, self.sticky = store, calls, delete_leaves_readable

    def create_workspace(self, name, capacity_id, description=""):
        self.calls.append(("CREATE", name))
        self.store[WS] = {"id": WS, "displayName": name, "type": "Workspace"}
        return self.store[WS]

    def delete_workspace(self, workspace_id, workspace_name):
        self.calls.append(("DELETE", workspace_id))
        if not self.sticky:
            self.store.pop(workspace_id, None)
        return True


def fake_fabric(**kw):
    store, calls = {}, []
    f = sb.Fabric(api=FakeApi(store, calls), workspaces=FakeWorkspaces(store, calls, **kw),
                  not_found=lambda e: isinstance(e, NotFound))
    f.store, f.calls = store, calls
    return f


def writes(f):
    return [c for c in f.calls if c[0] in ("CREATE", "DELETE")]


@pytest.fixture()
def pbip(tmp_path):
    d = tmp_path / "pbip"
    (d / "Ops.SemanticModel" / "definition").mkdir(parents=True)
    (d / "Ops.SemanticModel" / "definition" / "model.tmdl").write_text("model Model\n", encoding="utf-8")
    (d / "Ops.Report").mkdir()
    (d / "Ops.Report" / "definition.pbir").write_text("{}", encoding="utf-8")
    return d


def _up(tmp_path, f):
    m = tmp_path / "run.json"
    sb.up("run-0001", m, capacity_id="cap-1", apply=True, fabric=f)
    return m


def test_full_cycle_up_deploy_down(tmp_path, pbip):
    f = fake_fabric()
    m = _up(tmp_path, f)
    deployed = []
    out = sb.deploy(m, pbip, apply=True, fabric=f,
                    deployer=lambda wid, name, d: deployed.append((wid, name)) or {"stub": "1"})
    assert deployed == [(WS, "zz-aluca-sandbox-run-0001")]
    assert out["items"] == ["Ops.Report", "Ops.SemanticModel"]
    assert sb.down(m, apply=True, fabric=f)["verified"] == "404" and f.store == {}
    man = json.loads(m.read_text(encoding="utf-8"))
    assert [s["step"] for s in man["steps"]] == ["up", "deploy", "down"]
    assert man["inputs"]["pbip"] == sb.tree_sha256(pbip) and man["tools"] == {"stub": "1"}


def test_dry_run_is_default_and_touches_nothing(tmp_path, pbip):
    m = tmp_path / "run.json"
    plan = sb.up("run-0001", m, capacity_id=None, apply=False)          # no Fabric object at all
    assert plan["displayName"] == "zz-aluca-sandbox-run-0001" and not m.exists()
    f = fake_fabric()
    m = _up(tmp_path, f)
    f.calls.clear()
    sb.deploy(m, pbip, apply=False, deployer=lambda *a: pytest.fail("deployed on dry run"))
    sb.down(m, apply=False)
    assert f.calls == [] and WS in f.store


def test_wrong_workspace_id_aborts_before_any_write(tmp_path, pbip):
    f = fake_fabric()
    fremd = "99999999-0000-0000-0000-000000000000"
    f.store[fremd] = {"id": fremd, "displayName": "Finance Prod"}
    m = _up(tmp_path, f)
    man = json.loads(m.read_text(encoding="utf-8"))
    man["workspace_id"] = fremd                                          # manifest edited by hand
    m.write_text(json.dumps(man), encoding="utf-8")
    f.calls.clear()
    with pytest.raises(sb.SandboxError, match="refusing to write"):
        sb.down(m, apply=True, fabric=f)
    with pytest.raises(sb.SandboxError, match="refusing to write"):
        sb.deploy(m, pbip, apply=True, fabric=f, deployer=lambda *a: pytest.fail("deployed"))
    assert writes(f) == [] and fremd in f.store


def test_manifest_without_prefix_is_refused_without_reading(tmp_path):
    f = fake_fabric()
    m = _up(tmp_path, f)
    man = json.loads(m.read_text(encoding="utf-8"))
    man["workspace_name"] = "Finance Prod"
    m.write_text(json.dumps(man), encoding="utf-8")
    f.calls.clear()
    with pytest.raises(sb.SandboxError, match="not a zz-aluca-sandbox"):
        sb.down(m, apply=True, fabric=f)
    assert f.calls == []


def test_down_fails_when_workspace_is_still_readable(tmp_path):
    f = fake_fabric(delete_leaves_readable=True)
    m = _up(tmp_path, f)
    with pytest.raises(sb.SandboxError, match="still readable"):
        sb.down(m, apply=True, fabric=f)
    assert json.loads(m.read_text(encoding="utf-8"))["deleted_at"] is None


def test_an_error_other_than_404_is_not_taken_for_gone(tmp_path):
    f = fake_fabric()
    m = _up(tmp_path, f)

    def boom(endpoint):
        raise RuntimeError("HTTP 500")
    f.api.get = boom
    with pytest.raises(RuntimeError, match="500"):
        sb.down(m, apply=True, fabric=f)
    assert writes(f) == [("CREATE", "zz-aluca-sandbox-run-0001")]


def test_one_workspace_per_run_and_run_id_is_checked(tmp_path):
    f = fake_fabric()
    m = _up(tmp_path, f)
    with pytest.raises(sb.SandboxError, match="one workspace per run"):
        sb.up("run-0002", m, capacity_id=None, apply=True, fabric=f)
    with pytest.raises(sb.SandboxError, match="must match"):
        sb.up("Kunde X", tmp_path / "b.json", capacity_id=None, apply=True, fabric=f)
    assert len(writes(f)) == 1


def test_deleted_run_cannot_be_reused(tmp_path, pbip):
    f = fake_fabric()
    m = _up(tmp_path, f)
    sb.down(m, apply=True, fabric=f)
    with pytest.raises(sb.SandboxError, match="already deleted"):
        sb.deploy(m, pbip, apply=True, fabric=f, deployer=lambda *a: {})


def test_budget_caps_calls(tmp_path):
    f = fake_fabric()
    m = _up(tmp_path, f)
    with pytest.raises(sb.SandboxError, match="budget"):
        sb.down(m, apply=True, fabric=f, budget=sb.Budget(max_calls=1))     # read + delete + read
    assert writes(f) == [("CREATE", "zz-aluca-sandbox-run-0001")]


def test_secret_never_reaches_the_manifest(tmp_path, pbip, monkeypatch):
    monkeypatch.setenv("FABRIC_CLIENT_SECRET", "s3cr3t-wert")
    f = fake_fabric()
    m = _up(tmp_path, f)
    sb.deploy(m, pbip, apply=True, fabric=f, deployer=lambda *a: {"stub": "1"})
    assert "s3cr3t-wert" not in m.read_text(encoding="utf-8")


def test_apply_without_credentials_stops_before_loading_the_orchestrator(tmp_path, monkeypatch, capsys):
    for n in ("FABRIC_TENANT_ID", "FABRIC_CLIENT_ID", "FABRIC_CLIENT_SECRET"):
        monkeypatch.delenv(n, raising=False)
    assert sb.main(["up", "--manifest", str(tmp_path / "r.json"), "--run-id", "run-0001", "--apply"]) == 1
    assert "missing env vars" in capsys.readouterr().err


def test_cli_dry_run_writes_nothing(tmp_path, capsys):
    m = tmp_path / "run.json"
    assert sb.main(["up", "--manifest", str(m), "--run-id", "run-0001"]) == 0
    assert not m.exists() and "Trockenlauf" in capsys.readouterr().err
    assert sb.main(["down", "--manifest", str(m)]) == 1                   # no manifest -> abort


def _methods(path: Path) -> dict[str, dict[str, list[str]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, list[str]]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out[node.name] = {f.name: [a.arg for a in f.args.args] for f in node.body
                              if isinstance(f, ast.FunctionDef)}
        elif isinstance(node, ast.FunctionDef):
            out.setdefault("", {})[node.name] = [a.arg for a in node.args.args]
    return out


def test_the_orchestrator_still_offers_what_the_sandbox_calls():
    orch = _methods(HERE / "orchestrator.py")
    assert orch["FabricApiClient"]["__init__"][:3] == ["self", "config", "auth"]
    assert "get" in orch["FabricApiClient"]
    assert orch["AuthProvider"]["__init__"] == ["self", "config"]
    assert orch["WorkspaceManager"]["__init__"] == ["self", "api", "config"]
    assert orch["WorkspaceManager"]["create_workspace"][:3] == ["self", "name", "capacity_id"]
    assert orch["WorkspaceManager"]["delete_workspace"] == ["self", "workspace_id", "workspace_name"]
    assert "status_code" in orch["FabricApiError"]["__init__"]
    rel = _methods(sb.RELEASE_SCRIPT)[""]["release_to_workspace"]
    assert rel[:6] == ["workspace_name", "workspace_id", "repository_directory", "item_types",
                       "environment", "token_credential"]


def test_input_hash_is_stable_and_content_sensitive(pbip):
    a = sb.tree_sha256(pbip)
    assert a == sb.tree_sha256(pbip)
    (pbip / "Ops.Report" / "definition.pbir").write_text("{ }", encoding="utf-8")
    assert sb.tree_sha256(pbip) != a


def test_real_orchestrator_wiring_with_http_replaced(tmp_path, monkeypatch):
    """The real FabricApiClient/WorkspaceManager path, only ``requests.request`` and the token
    replaced. Skips without the orchestrator deps (CI has no ``msal``), like test_governance."""
    pytest.importorskip("msal", reason="orchestrator deps")
    pytest.importorskip("typer", reason="orchestrator deps")
    pytest.importorskip("rich", reason="orchestrator deps")
    import requests

    for n, v in (("FABRIC_TENANT_ID", "t"), ("FABRIC_CLIENT_ID", "c"), ("FABRIC_CLIENT_SECRET", "s")):
        monkeypatch.setenv(n, v)
    store, seen = {}, []

    class Resp:
        def __init__(self, status, body=None):
            self.status_code, self._body, self.headers, self.reason = status, body, {}, "x"
            self.content = json.dumps(body).encode() if body is not None else b""
            self.text = self.content.decode()

        def json(self):
            return self._body

    def fake_request(method, url, headers=None, json=None, params=None, timeout=None):
        seen.append((method, url.split("/v1/", 1)[1]))
        assert headers["Authorization"] == "Bearer tok"
        wid = url.rsplit("/", 1)[-1]
        if method == "POST":
            store[WS] = {"id": WS, "displayName": json["displayName"]}
            return Resp(201, store[WS])
        if method == "GET":
            return Resp(200, store[wid]) if wid in store else Resp(404, {"errorCode": "WorkspaceNotFound"})
        if method == "DELETE":
            store.pop(wid, None)
            return Resp(200)
        raise AssertionError(method)

    monkeypatch.setattr(requests, "request", fake_request)
    monkeypatch.setattr(sb.time, "sleep", lambda s: None)
    f = sb.orchestrator_fabric()
    monkeypatch.setattr(f.api.auth, "get_token", lambda force_refresh=False, scopes=None: "tok")
    monkeypatch.setattr(sys.modules["_aluca_orchestrator"].time, "sleep", lambda s: None)
    m = tmp_path / "run.json"
    sb.up("run-0001", m, capacity_id="cap", apply=True, fabric=f)
    assert sb.down(m, apply=True, fabric=f)["verified"] == "404"
    assert seen == [("POST", "workspaces"), ("GET", f"workspaces/{WS}"),
                    ("DELETE", f"workspaces/{WS}"), ("GET", f"workspaces/{WS}")]
