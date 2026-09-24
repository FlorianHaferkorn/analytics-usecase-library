#!/usr/bin/env python3
"""Sandbox lifecycle for tenant runs: up → deploy → down (UMSETZUNGSPLAN_AGENTIC_LOOP AP-2).

Only the guardrails live here. Everything that talks to Fabric is reused, not rebuilt
(Tool-Reuse, decision E4 of 24.09.2026):

* token, REST calls, retry with ``Retry-After`` → ``orchestrator.AuthProvider`` and
  ``orchestrator.FabricApiClient``;
* create/delete workspace → ``orchestrator.WorkspaceManager``;
* deploy → ``release_to_workspace`` in ``products/fabric/powerbi/deployment/scripts/
  fabric_release.py`` (``fabric-cicd``, decision E3: MS Learn documents it for PBIP, while the
  raw Items API needs a ``byConnection`` report reference and our PBIPs carry ``byPath``).

Guardrails (plan §5): one workspace per run, name ``zz-aluca-sandbox-<run-id>``, recorded in a
run manifest. Every writing step reads the workspace back first and aborts unless ID *and*
prefixed name match the manifest, so a hand-edited or stale manifest never touches a foreign
workspace. Dry run is the default; writing needs ``--apply``. A call budget per command.
Credentials only from ``FABRIC_TENANT_ID`` / ``FABRIC_CLIENT_ID`` / ``FABRIC_CLIENT_SECRET``,
never in the manifest.

The orchestrator is loaded lazily and only for ``--apply``: its module imports ``msal`` and
``requests``, which the CI does not install, so the tests inject a fake with the same methods
(``tooling/tests/test_sandbox.py`` also checks those methods exist in ``orchestrator.py``).

**ANNAHME, ungeprueft** until the first tenant run: that reading a deleted workspace answers
404. A deleted collaborative workspace stays restorable by admins for the retention period
(MS Learn, default 7 days); ``down`` proves "gone from the API", not "purged".

    python products/fabric/orchestrator/sandbox.py up --manifest run.json --run-id run-0001 --capacity-id <id> [--apply]
    python products/fabric/orchestrator/sandbox.py deploy --manifest run.json --pbip-dir <dir> [--apply]
    python products/fabric/orchestrator/sandbox.py down --manifest run.json [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RELEASE_SCRIPT = REPO / "products" / "fabric" / "powerbi" / "deployment" / "scripts" / "fabric_release.py"

PREFIX = "zz-aluca-sandbox-"
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{3,39}$")
DEFAULT_MAX_CALLS = 20


class SandboxError(RuntimeError):
    """A guardrail stopped the run. Nothing after the failing check was sent."""


class Budget:
    def __init__(self, max_calls: int = DEFAULT_MAX_CALLS):
        self.max_calls, self.used = max_calls, 0

    def take(self) -> None:
        if self.used >= self.max_calls:
            raise SandboxError(f"budget exhausted: {self.max_calls} calls")
        self.used += 1


@dataclass
class Fabric:
    """The three orchestrator pieces the sandbox uses. Tests pass fakes with the same methods."""
    api: Any                      # FabricApiClient: get(endpoint) -> body, raises on >= 400
    workspaces: Any               # WorkspaceManager: create_workspace, delete_workspace
    not_found: Callable[[Exception], bool]


def _load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                # dataclasses resolve their module by name
    spec.loader.exec_module(mod)
    return mod


class _EnvConfig:
    """What FabricApiClient/AuthProvider read from ConfigLoader, without a config.yaml."""

    def __init__(self) -> None:
        self._data = {"fabric": {"tenant_id": os.environ.get("FABRIC_TENANT_ID")}}

    def get(self, key_path: str, default: Any = None) -> Any:
        cur: Any = self._data
        for part in key_path.split("."):
            if not isinstance(cur, dict) or cur.get(part) is None:
                return default
            cur = cur[part]
        return cur


def orchestrator_fabric() -> Fabric:
    missing = [n for n in ("FABRIC_TENANT_ID", "FABRIC_CLIENT_ID", "FABRIC_CLIENT_SECRET") if not os.environ.get(n)]
    if missing:
        raise SandboxError(f"missing env vars: {', '.join(missing)}")
    orch = _load_by_path("_aluca_orchestrator", HERE / "orchestrator.py")
    cfg = _EnvConfig()
    api = orch.FabricApiClient(cfg, orch.AuthProvider(cfg))
    return Fabric(api=api, workspaces=orch.WorkspaceManager(api, cfg),
                  not_found=lambda e: isinstance(e, orch.FabricApiError) and e.status_code == 404)


def release_deployer(workspace_id: str, workspace_name: str, pbip_dir: Path) -> dict[str, str]:
    """Deploy through the existing fabric-cicd release (E3); semantic model before report."""
    sys.path.insert(0, str(RELEASE_SCRIPT.parent))
    rel = _load_by_path("_aluca_fabric_release", RELEASE_SCRIPT)
    cred = rel.ClientSecretCredential(tenant_id=os.environ["FABRIC_TENANT_ID"],
                                      client_id=os.environ["FABRIC_CLIENT_ID"],
                                      client_secret=os.environ["FABRIC_CLIENT_SECRET"])
    ok = rel.release_to_workspace(workspace_name, workspace_id, str(pbip_dir), ["SemanticModel", "Report"],
                                  "sandbox", cred, unpublish_orphans=False)
    if not ok:
        raise SandboxError("fabric_release.release_to_workspace reported failure")
    import fabric_cicd
    return {"fabric-cicd": getattr(fabric_cicd, "__version__", "unknown")}


@dataclass
class Manifest:
    run_id: str
    workspace_name: str
    workspace_id: str
    capacity_id: str | None
    created_at: str
    inputs: dict[str, str] = field(default_factory=dict)
    tools: dict[str, str] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    deleted_at: str | None = None

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        if not path.is_file():
            raise SandboxError(f"no manifest at {path} (run 'up --apply' first)")
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def tree_sha256(root: Path) -> str:
    """Hash over relative paths and bytes, sorted: same PBIP → same hash on every machine."""
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
        h.update(p.read_bytes())
    return h.hexdigest()


def _read(fabric: Fabric, budget: Budget, workspace_id: str) -> dict | None:
    """The workspace as the API sees it, or None for 404. Any other error propagates."""
    budget.take()
    try:
        return fabric.api.get(f"workspaces/{workspace_id}")
    except Exception as e:  # noqa: BLE001 -- only a 404 is an answer, everything else is raised
        if fabric.not_found(e):
            return None
        raise


def _guard(m: Manifest, fabric: Fabric, budget: Budget) -> None:
    """Read the workspace back; abort unless it is exactly the one this manifest created."""
    if m.deleted_at:
        raise SandboxError(f"workspace {m.workspace_id} already deleted at {m.deleted_at}")
    if not m.workspace_name.startswith(PREFIX):
        raise SandboxError(f"manifest names '{m.workspace_name}', not a {PREFIX}* workspace")
    body = _read(fabric, budget, m.workspace_id)
    if not body:
        raise SandboxError(f"workspace {m.workspace_id} not readable")
    if body.get("id") != m.workspace_id or body.get("displayName") != m.workspace_name:
        raise SandboxError(f"workspace {m.workspace_id} is '{body.get('displayName')}', manifest expects "
                           f"'{m.workspace_name}' -- refusing to write")


def up(run_id: str, manifest_path: Path, *, capacity_id: str | None, apply: bool,
       fabric: Fabric | None = None, budget: Budget | None = None) -> dict[str, Any]:
    if not RUN_ID.match(run_id):
        raise SandboxError(f"run id '{run_id}' must match {RUN_ID.pattern}")
    if manifest_path.exists():
        raise SandboxError(f"manifest {manifest_path} exists -- one workspace per run")
    name = PREFIX + run_id
    plan = {"action": "create_workspace", "displayName": name, "capacityId": capacity_id, "applied": False}
    if not apply:
        return plan
    budget = budget or Budget()
    budget.take()
    body = fabric.workspaces.create_workspace(name, capacity_id, description="ALUCA sandbox run (AP-2)")
    if not body or body.get("displayName") != name or not body.get("id"):
        raise SandboxError(f"create workspace returned an unexpected body for '{name}'")
    m = Manifest(run_id=run_id, workspace_name=name, workspace_id=body["id"],
                 capacity_id=capacity_id, created_at=_now())
    m.steps.append({"step": "up", "at": m.created_at})
    m.save(manifest_path)
    return {**plan, "applied": True, "workspace_id": m.workspace_id}


def deploy(manifest_path: Path, pbip_dir: Path, *, apply: bool, fabric: Fabric | None = None,
           budget: Budget | None = None,
           deployer: Callable[[str, str, Path], dict[str, str]] = release_deployer) -> dict[str, Any]:
    m = Manifest.load(manifest_path)
    items = sorted(p.name for p in pbip_dir.iterdir() if p.suffix in (".SemanticModel", ".Report"))
    if not items:
        raise SandboxError(f"{pbip_dir}: no *.SemanticModel or *.Report folder")
    digest = tree_sha256(pbip_dir)
    plan = {"action": "deploy", "workspace_id": m.workspace_id, "items": items,
            "input_sha256": digest, "applied": False}
    if not apply:
        return plan
    _guard(m, fabric, budget or Budget())
    tools = deployer(m.workspace_id, m.workspace_name, pbip_dir)
    m.inputs[pbip_dir.name] = digest
    m.tools.update(tools)
    m.steps.append({"step": "deploy", "at": _now(), "items": items, "input_sha256": digest})
    m.save(manifest_path)
    return {**plan, "applied": True, "tools": tools}


def down(manifest_path: Path, *, apply: bool, fabric: Fabric | None = None,
         budget: Budget | None = None) -> dict[str, Any]:
    m = Manifest.load(manifest_path)
    plan = {"action": "delete_workspace", "workspace_id": m.workspace_id,
            "workspace_name": m.workspace_name, "applied": False}
    if not apply:
        return plan
    budget = budget or Budget()
    _guard(m, fabric, budget)
    budget.take()
    if not fabric.workspaces.delete_workspace(m.workspace_id, m.workspace_name):
        raise SandboxError("delete workspace was not acknowledged")
    if _read(fabric, budget, m.workspace_id) is not None:
        raise SandboxError(f"workspace {m.workspace_id} still readable after delete")
    m.deleted_at = _now()
    m.steps.append({"step": "down", "at": m.deleted_at, "verified": "404"})
    m.save(manifest_path)
    return {**plan, "applied": True, "verified": "404"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("up", "deploy", "down"):
        sp = sub.add_parser(name)
        sp.add_argument("--manifest", required=True)
        sp.add_argument("--apply", action="store_true", help="actually write; default is a dry run")
        sp.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS)
        if name == "up":
            sp.add_argument("--run-id", required=True)
            sp.add_argument("--capacity-id", default=None)
        if name == "deploy":
            sp.add_argument("--pbip-dir", required=True)
    a = ap.parse_args(argv)
    try:
        fabric = orchestrator_fabric() if a.apply else None
        budget = Budget(a.max_calls)
        if a.cmd == "up":
            out = up(a.run_id, Path(a.manifest), capacity_id=a.capacity_id, apply=a.apply, fabric=fabric, budget=budget)
        elif a.cmd == "deploy":
            out = deploy(Path(a.manifest), Path(a.pbip_dir), apply=a.apply, fabric=fabric, budget=budget)
        else:
            out = down(Path(a.manifest), apply=a.apply, fabric=fabric, budget=budget)
    except SandboxError as e:
        print(f"[sandbox] ABBRUCH: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, sort_keys=True))
    if not a.apply:
        print("[sandbox] Trockenlauf -- nichts geschrieben (--apply zum Ausfuehren)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
