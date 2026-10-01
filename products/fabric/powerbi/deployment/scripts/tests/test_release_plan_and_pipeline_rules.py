"""Release side of I-21: deployment plan flag (W2.7), pipeline independence (W1.9), branch rule
and secret scan in the Azure release pipelines (W5.4). No tenant, no network.

`fabric_release.py` is read as text / via AST (it imports fabric_cicd and azure-identity, which
are deployment-only dependencies), like test_release_cli_contract.py.

Microsoft Learn sources (read 01.10.2026):
- fabric/cicd/deployment-plan/deployment-plan-automation: `options.deploymentPlan`, `?beta=true`,
  extra scope Item.Execute.All; Bulk Import takes `logicalId` + `ByLogicalId`;
  "The fabric-cicd library doesn't support deployment plans."
- fabric/cicd/cicd-security: deployment pipelines unsupported with inbound access protection.
- azure/devops/pipelines/tasks/reference/manual-validation-v0: agentless job only.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

_SCRIPTS = Path(__file__).resolve().parents[1]
_DEPLOYMENT = _SCRIPTS.parent
_RELEASE_PY = _SCRIPTS / "fabric_release.py"
_PIPELINES = _DEPLOYMENT / ".azure-pipelines"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import secret_scan_gate as gate  # noqa: E402

PLAN_ID = "11111111-2222-3333-4444-555555555555"
WS_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _release_source() -> str:
    return _RELEASE_PY.read_text(encoding="utf-8")


def _load_plan_function():
    """`deployment_plan_request` plus the constants it reads, without the heavy imports."""
    tree = ast.parse(_release_source())
    wanted = {"FABRIC_API", "DEPLOYMENT_PLAN_SCOPES", "_GUID", "deployment_plan_request"}
    body = [n for n in tree.body
            if (isinstance(n, ast.FunctionDef) and n.name in wanted)
            or (isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id in wanted for t in n.targets))]
    ns: dict = {"re": re}
    exec(compile(ast.Module(body=body, type_ignores=[]), "<plan>", "exec"), ns)
    return ns["deployment_plan_request"]


# -- W2.7 deployment plan ------------------------------------------------------------


def test_plan_request_matches_the_documented_bulk_import_shape():
    req = _load_plan_function()(WS_ID, PLAN_ID)
    assert req == {
        "method": "POST",
        "url": f"https://api.fabric.microsoft.com/v1/workspaces/{WS_ID}"
               "/items/bulkImportDefinitions?beta=true",
        "options": {"allowPairingByName": False,
                    "deploymentPlan": {"logicalId": PLAN_ID, "referenceType": "ByLogicalId"}},
        "scopes": ["Item.ReadWrite.All", "Item.Execute.All"],
    }


@pytest.mark.parametrize("bad", ["", "not-a-guid", PLAN_ID[:-1], None])
def test_plan_id_must_be_a_guid(bad):
    with pytest.raises(ValueError):
        _load_plan_function()(WS_ID, bad)


def test_plan_flag_is_off_by_default():
    src = _release_source()
    block = re.search(r'"--deployment_plan_logical_id",(.*?)\n    \)', src, re.S)
    assert block, "--deployment_plan_logical_id is not declared"
    assert "default=None" in block.group(1)


def test_live_release_with_plan_is_refused_not_silently_dropped():
    """fabric-cicd cannot carry a plan; a live run must stop before auth, not publish without it."""
    src = _release_source()
    guard = src[src.index("if args.deployment_plan_logical_id:"):
                src.index("if args.workspace_id and len(")]
    assert "if not args.dry_run:" in guard and "sys.exit(1)" in guard
    assert src.index("if args.deployment_plan_logical_id:") < src.index("login_service_principal(")


# -- W1.9 release path is not a deployment pipeline -------------------------------------


@pytest.mark.parametrize("path", [_RELEASE_PY, _SCRIPTS / "modules" / "fabric_cli_functions.py"])
def test_release_does_not_use_fabric_deployment_pipelines(path):
    """The inbound-protection restriction hits Fabric deployment pipelines; the release goes
    through fabric-cicd (Items APIs). Pin that no deployment-pipeline API is called."""
    code = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                     if not line.lstrip().startswith("#"))
    code = re.sub(r'""".*?"""', "", code, flags=re.S)
    assert "deploymentPipelines" not in code
    assert "/deploy?" not in code


def test_release_publishes_via_fabric_cicd():
    assert "from fabric_cicd import FabricWorkspace, publish_all_items" in _release_source()


# -- W5.4 branch rule ----------------------------------------------------------------------

RELEASE_PIPELINES = ("solution_release_multistages.yml", "solution_release_simple.yml")


def _yaml(name: str) -> dict:
    return yaml.safe_load((_PIPELINES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", RELEASE_PIPELINES)
def test_release_stages_run_only_from_release_branches(name):
    """The pipelines also trigger on PRs to main; without a condition a PR build deploys."""
    stages = {s["stage"]: s for s in _yaml(name)["stages"]}
    for stage in ("ReleaseTest", "ReleaseProd"):
        cond = stages[stage].get("condition", "")
        assert "startsWith(variables['Build.SourceBranch'], 'refs/heads/releases/')" in cond
        assert "ne(variables['Build.Reason'], 'PullRequest')" in cond
    assert "condition" not in stages["Build"] or "releases/" not in stages["Build"]["condition"]


@pytest.mark.parametrize("name", RELEASE_PIPELINES)
def test_trigger_branch_matches_the_stage_rule(name):
    include = _yaml(name)["trigger"]["branches"]["include"]
    assert include and all(b.startswith("releases/") for b in include)


def _steps(doc) -> list:
    found = []
    if isinstance(doc, dict):
        if "steps" in doc and isinstance(doc["steps"], list):
            found.extend(doc["steps"])
        for value in doc.values():
            found.extend(_steps(value))
    elif isinstance(doc, list):
        for value in doc:
            found.extend(_steps(value))
    return found


@pytest.mark.parametrize("name", ["_template_release_solution.yml", "_template_build_solution.yml"])
def test_script_steps_carry_no_pwsh_key(name):
    """`pwsh` is not a property of a `script` step (Azure Pipelines YAML schema); the backtick
    continuations of the release call need a real `pwsh` step."""
    for step in _steps(_yaml(name)):
        if "script" in step:
            assert "pwsh" not in step, step.get("displayName")


def test_release_step_runs_fabric_release_in_pwsh():
    steps = [s for s in _steps(_yaml("_template_release_solution.yml")) if "pwsh" in s]
    assert any("fabric_release.py" in s["pwsh"] for s in steps)


# -- ManualValidation@0 only in agentless jobs (Learn manual-validation-v0, 01.10.2026) ------


def _jobs(doc) -> list:
    found = []
    if isinstance(doc, dict):
        if isinstance(doc.get("jobs"), list):
            found.extend(j for j in doc["jobs"] if isinstance(j, dict))
        for value in doc.values():
            found.extend(_jobs(value))
    elif isinstance(doc, list):
        for value in doc:
            found.extend(_jobs(value))
    return found


def _is_manual_validation(step: dict) -> bool:
    return str(step.get("task", "")).startswith("ManualValidation@")


ALL_PIPELINE_FILES = sorted(p.name for p in _PIPELINES.glob("*.yml"))


@pytest.mark.parametrize("name", ALL_PIPELINE_FILES)
def test_manual_validation_runs_only_in_agentless_jobs(name):
    """"can only be used in an agentless job" — a steps template is expanded into agent jobs,
    so it must not carry the task at all."""
    doc = _yaml(name)
    if "jobs" not in doc and "stages" not in doc:      # a steps template
        assert not any(_is_manual_validation(s) for s in _steps(doc)), name
        return
    for job in _jobs(doc):
        tasks = [s for s in job.get("steps", []) if isinstance(s, dict) and _is_manual_validation(s)]
        if not tasks:
            continue
        assert job.get("pool") == "server", (name, job.get("job"))
        for task in tasks:
            assert "timeoutInMinutes" not in task.get("inputs", {}), "common property, not an input"
            assert task.get("timeoutInMinutes", 60) < job.get("timeoutInMinutes", 60), \
                "job timeout must exceed the task timeout"
            assert "notifyUsers" in task["inputs"]


def test_simple_pipeline_gates_each_release_job_on_its_approval_job():
    doc = _yaml("solution_release_simple.yml")
    checked = 0
    for stage in doc["stages"]:
        jobs = {j.get("job"): j for j in stage.get("jobs", [])}
        approvals = [n for n, j in jobs.items() if j.get("pool") == "server"]
        for name, job in jobs.items():
            if any("_template_release_solution.yml" in str(s.get("template", ""))
                   for s in job.get("steps", [])):
                assert job.get("dependsOn") in approvals, (stage["stage"], name)
                checked += 1
    assert checked == 2, "Gegenprobe: TEST und PRODUCTION"


def test_release_template_no_longer_takes_approval_parameters():
    names = {p["name"] for p in _yaml("_template_release_solution.yml")["parameters"]}
    assert names == {"environment"}
    for pipeline in RELEASE_PIPELINES:
        assert "requireManualApproval" not in (_PIPELINES / pipeline).read_text(encoding="utf-8")


# -- W5.4 secret scan ----------------------------------------------------------------------


def test_build_template_runs_the_pinned_secret_scan_before_artifacts():
    steps = _steps(_yaml("_template_build_solution.yml"))
    names = [s.get("displayName", "") for s in steps]
    install = next(s for s in steps if "detect-secrets==" in str(s.get("script", "")))
    assert re.search(r"detect-secrets==\d+\.\d+\.\d+", install["script"])
    scan = next(i for i, s in enumerate(steps) if "secret_scan_gate.py" in str(s.get("script", "")))
    assert scan < names.index("Upload solution artifacts")
    assert steps[scan].get("continueOnError", False) is False


def test_gate_scope_is_not_empty_in_this_repo():
    repo_root = _SCRIPTS.parents[4]
    scope = gate.files_in_scope(repo_root)
    assert scope and not any("/tests/" in f for f in scope)
    assert "products/fabric/powerbi/deployment/scripts/fabric_release.py" in scope


def test_gate_findings_are_extracted_per_file():
    report = {"results": {"a.py": [{"type": "Secret Keyword"}, {"type": "AWS Access Key"}],
                          "b.json": []}}
    assert gate.findings(report) == {"a.py": ["AWS Access Key", "Secret Keyword"]}


def test_gate_rejects_a_report_without_results():
    with pytest.raises(ValueError):
        gate.findings({})


def _fake_run(stdout: str, returncode: int = 0):
    class _Proc:
        def __init__(self):
            self.stdout, self.returncode, self.stderr = stdout, returncode, "boom"
    return lambda *a, **k: _Proc()


@pytest.mark.parametrize("stdout,rc,expected", [
    (json.dumps({"results": {}}), 0, 0),
    (json.dumps({"results": {"x.py": [{"type": "Secret Keyword"}]}}), 0, 1),
    ("", 1, 2),             # detect-secrets missing / failed: not run, not clean
    ("{not json", 0, 2),
])
def test_gate_exit_codes_separate_clean_from_not_run(monkeypatch, tmp_path, stdout, rc, expected):
    target = tmp_path / gate.SCAN_PATHS[0]
    target.mkdir(parents=True)
    (target / "x.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(gate.subprocess, "run", _fake_run(stdout, rc))
    assert gate.main(tmp_path) == expected


def test_gate_with_empty_scope_reports_not_run(tmp_path):
    assert gate.main(tmp_path) == 2


# -- --unpublish_items: "false" muss False ergeben (Befund 01.10.2026, type=bool) ------------

def _load_parse_bool():
    """`_parse_bool` per AST, wie oben: das Skript importiert fabric_cicd."""
    import argparse

    tree = ast.parse(_release_source())
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_parse_bool"]
    ns: dict = {"argparse": argparse}
    exec(compile(ast.Module(body=body, type_ignores=[]), "<bool>", "exec"), ns)
    return ns["_parse_bool"]


def test_unpublish_items_uses_the_bool_parser_not_type_bool():
    assert not re.search(r"^\s*type=bool,", _release_source(), re.M)


@pytest.mark.parametrize("raw, erwartet", [("true", True), ("false", False), ("False", False),
                                           ("0", False), ("1", True)])
def test_unpublish_items_parses_false_as_false(raw, erwartet):
    assert _load_parse_bool()(raw) is erwartet


def test_unpublish_items_rejects_garbage():
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        _load_parse_bool()("vielleicht")
