"""Tenant-free reference using the real revision, derivation and output compilers.

Fixture actors exercise local approval mechanics only. The reserved project ID,
ephemeral repository and SYNTHETIC_ONLY marker prevent confusion with customer
delivery. No SDK, token broker, shell command, supplied code or network is used.
"""
from __future__ import annotations

import argparse
import base64
import copy
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import yaml

from .architecture_compile import read_architecture
from .automation import run_automation
from .decision_derivation import apply_derivation, preview_derivation
from .deployment_plan import approve_deployment, build_deployment_plan, execute_workspace_plan
from .hashes import canonical_sha256
from .item_simulation import simulate_item_contract
from .migrations import migrate_project_package
from .release import release_input
from .repository import ProjectPackageRevisionRepository

FIXTURE = Path(__file__).resolve().parents[3] / "core/fixtures/neutral/local-delivery-reference"
PROJECT = "local_reference"
VARIANTS = {"dev_test_prod": ["dev", "test", "prod"], "dev_prod": ["dev", "prod"]}
ACTOR = "synthetic_fixture_not_a_customer"
NOW = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
TENANT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
PRINCIPAL = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CAPACITY = "11111111-1111-4111-8111-111111111111"
DOMAIN = "22222222-2222-4222-8222-222222222222"
MARKER = {"source_kind": "synthetic", "project_ref": PROJECT, "tenant_actions_performed": False, "live_apply_allowed": False,
          "notice": "Local reference only. Fixture approval is not customer authorization. Do not import into a live runner."}


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _part(path, value):
    content = value if isinstance(value, str) else _json(value)
    return {"path": path, "payload": base64.b64encode(content.encode()).decode(), "payloadType": "InlineBase64"}


def _targets(environments):
    workspaces, items = [], []
    for env in environments:
        workspace_id = f"workspace_local_{env}"
        workspaces.append({"id": workspace_id, "name": f"synthetic_local_sales_{env}", "domain_ref": "domain_local", "environment": env,
                           "capacity_id": CAPACITY, "domain_id": DOMAIN, "decision_refs": ["decision_environment_model"]})
        common = {"workspace_ref": workspace_id, "environment": env, "decision_refs": ["decision_environment_model"]}
        items.append({**common, "id": f"notebook_{env}", "name": f"nb_local_sales_{env}", "type": "Notebook", "depends_on": [], "environment_bindings": [],
                      "definition": {"format": "FabricGitSource", "parts": [_part("notebook-content.py", "# Fabric notebook source\n# SYNTHETIC_ONLY: transport example, not a runnable data platform\nprint('Local reference; tenant execution is disabled')\n")]}})
        pipeline = {"properties": {"activities": [], "parameters": {"environment": {"type": "String", "defaultValue": env},
                    "notebookId": {"type": "String", "defaultValue": "LOCAL_NOTEBOOK_BINDING"}}}}
        items.append({**common, "id": f"pipeline_{env}", "name": f"pl_local_sales_{env}", "type": "DataPipeline", "depends_on": [f"notebook_{env}"],
                      "environment_bindings": [{"part_path": "pipeline-content.json", "json_pointer": "/properties/parameters/environment/defaultValue", "expected_value": env, "authority_ref": "synthetic://environment"}],
                      "definition": {"parts": [_part("pipeline-content.json", pipeline)]}})
    return workspaces, items


def _architecture(variant):
    selected_workspaces, selected_items = _targets(VARIANTS[variant])
    value = {"schema_version": "2.0.0", "stack": "fabric", "reference_date": "2026-09-08", "tenant": "Synthetic tenant (not connected)", "region": "West Europe",
             "ledger_ref": "synthetic://local_reference/decision_set.json", "model_ref": "synthetic://local_reference/architecture", "blueprint_ref": "synthetic://local_reference/outputs", "mapping_ref": "synthetic://local_reference/bindings",
             "domains": [{"id": "domain_local", "key": "local", "capacity": "fbsynthetic01", "delivery_scope": "detailed", "use_case_refs": ["uc_local_sales"]}],
             "use_cases": [{"id": "uc_local_sales", "name": "Synthetic sales totals", "domain_ref": "domain_local", "architecture_detail": "full"}],
             "environments": {"recommended": ["dev"], "accepted": True, "decision_ref": "decision_environment_model"}, "contracts": [],
             "compiler_policy": {"version": "1", "generated_ref": "synthetic_outputs", "fail_closed_for_apply": True, "allow_review_with_blockers": True},
             "physical_workspaces": selected_workspaces, "physical_items": selected_items,
             "decision_rules": [{"id": "environment_lanes", "decision_ref": "decision_environment_model", "decision_revision": 1, "option_ref": variant,
                 "target": {"collection": "environments", "entity_id": None, "field": "recommended"}, "expected_value": ["dev"], "value": VARIANTS[variant],
                 "rationale": "Apply the explicit synthetic choice to the supported environment lanes; fixture targets are declared for that same choice."}]}
    return value


def _module(package, manifest, kind, document):
    row = next((row for row in manifest["modules"] if row["module_type"] == kind), None)
    if row is None:
        row = {"module_type": kind, "path": f"{kind}.yaml", "schema_id": f"https://aluca.local/schemas/project-package/{kind.replace('_', '-')}/2.0.0"}
        manifest["modules"].append(row)
    path = package / row["path"]
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    row["sha256"] = canonical_sha256(document)


def _build_repository(root, schemas, variant):
    source = root / "source"
    source.mkdir()
    source.joinpath("package.yaml").write_text((FIXTURE / "package.json").read_text(encoding="utf-8"), encoding="utf-8")
    package = migrate_project_package(source, root / "package", schemas)
    manifest = yaml.safe_load((package / "package.yaml").read_text(encoding="utf-8"))
    decision = json.loads((FIXTURE / "decision_set.json").read_text(encoding="utf-8"))
    decision["definitions"][0]["source"]["source_hash"] = hashlib.sha256((FIXTURE / "brief.md").read_bytes()).hexdigest()
    decision["instances"][0]["selection"]["option_ref"] = variant
    for kind, document in (("decision_set", decision), ("architecture_input", _architecture(variant)),
                           ("use_case_delivery", json.loads((FIXTURE / "use_case_delivery.json").read_text(encoding="utf-8")))):
        _module(package, manifest, kind, document)
        next(row for row in manifest["modules"] if row["module_type"] == kind)["schema_id"] = json.loads((schemas / f"project_{kind}.schema.json").read_text(encoding="utf-8"))["$id"]
    (package / "SYNTHETIC_ONLY.json").write_text(_json(MARKER), encoding="utf-8")
    for name in ("brief.md", "sales.csv"):
        (package / name).write_bytes((FIXTURE / name).read_bytes())
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    repo = ProjectPackageRevisionRepository(root / "repositories" / PROJECT, schemas)
    first = repo.commit(package)
    preview = preview_derivation(repo, PROJECT, first.revision_hash)
    if not preview["can_apply"]:
        raise ValueError("Synthetic fixture decision cannot be derived")
    derived = apply_derivation(repo, {"project_ref": PROJECT, "revision_hash": first.revision_hash, "preview_sha256": preview["preview_sha256"],
                                    "actor": ACTOR, "rationale": "Review the exact environment change for local fixture testing only.", "confirm_apply": True})
    draft = repo.checkout(root / "fixture_approval", derived["revision_hash"])
    manifest = yaml.safe_load((draft / "package.yaml").read_text(encoding="utf-8"))
    manifest["state"] = "approved"
    (draft / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    final = repo.commit_draft(draft, expected_head_hash=derived["revision_hash"])
    released = release_input(repo, PROJECT, final.revision_hash, actor=ACTOR, rationale="Synthetic local compiler release only; never customer or tenant approval.")
    return repo, final, released, {"before_revision_hash": first.revision_hash, "derived_revision_hash": derived["revision_hash"], "revision_hash": final.revision_hash, "preview": preview}


class _SyntheticWorkspaceClient:
    """In-memory implementation of WorkspaceClient; no external access exists."""
    def __init__(self, *, interrupted=False):
        self.state = {"tenant_id": TENANT, "principal_id": PRINCIPAL, "observed_at": NOW.isoformat(), "complete": True, "workspaces": [],
                      "permissions": {"create_workspaces": True, "capacity_assign_ids": [CAPACITY], "domain_assign_ids": [DOMAIN], "evidence_ref": "synthetic://permissions_not_live"}}
        self.creates = 0
        self.interrupted = interrupted

    def observe(self):
        return copy.deepcopy(self.state)

    def create_workspace(self, body):
        self.creates += 1
        identity = f"cccccccc-cccc-4ccc-8ccc-{self.creates:012d}"
        self.state["workspaces"].append({"id": identity, **body, "type": "Workspace", "capacityAssignmentProgress": "Completed"})
        if self.interrupted:
            raise TimeoutError("Synthetic interruption after in-memory creation")
        return {"id": identity}

    def get_workspace(self, identity):
        return copy.deepcopy(next(row for row in self.state["workspaces"] if row["id"] == identity))


def _workspace_checks(repo, revision, root):
    client = _SyntheticWorkspaceClient()
    plan = lambda state: build_deployment_plan(repo, PROJECT, revision, TENANT, "dev", state, now=NOW)
    approve = lambda value: approve_deployment(value, actor=ACTOR, rationale="Synthetic create-only contract exercise, no tenant action.", now=NOW)
    first = plan(client.observe())
    created = execute_workspace_plan(repo, first, approve(first), client, root / "simulated_claims", now=NOW)
    second = plan(client.observe())
    replay = execute_workspace_plan(repo, second, approve(second), client, root / "simulated_claims", now=NOW)
    conflict_state = client.observe()
    conflict_state["workspaces"][0]["capacityId"] = TENANT
    conflict = plan(conflict_state)
    interrupted_client = _SyntheticWorkspaceClient(interrupted=True)
    stopped = execute_workspace_plan(repo, first, approve(first), interrupted_client, root / "interrupted_claims", now=NOW)
    duplicate_blocked = False
    try:
        execute_workspace_plan(repo, first, approve(first), interrupted_client, root / "interrupted_claims", now=NOW)
    except ValueError:
        duplicate_blocked = True
    recovery = plan(interrupted_client.observe())
    results = {"create": created["status"] == "workspace_verified", "repeat_noop": replay["status"] == "workspace_verified" and client.creates == 1,
               "conflict_blocked": not conflict["workspace_apply_ready"] and conflict["operations"][0]["action"] == "conflict",
               "interruption_no_retry": stopped["status"] == "stopped_requires_reconciliation" and duplicate_blocked and interrupted_client.creates == 1,
               "recovery_readback": recovery["operations"][0]["action"] == "noop"}
    if not all(results.values()):
        raise ValueError("Synthetic workspace scenarios failed")
    return {**MARKER, "evidence_kind": "simulation", "revision_hash": revision, "checks": results,
            "note": "The existing create-only executor was called only with an in-memory client. Verified statuses refer to simulated readback, not Fabric."}


def _item_checks(compiler, variant, revision):
    workspace_map = [{"workspace_ref": f"workspace_local_{env}", "environment": env, "physical_id": f"sim_workspace_{env}"} for env in VARIANTS[variant]]
    bindings = [{"item_ref": f"pipeline_{env}", "part_path": "pipeline-content.json", "json_pointer": "/properties/parameters/notebookId/defaultValue", "expected_value": "LOCAL_NOTEBOOK_BINDING", "target_kind": "item", "target_ref": f"notebook_{env}"} for env in VARIANTS[variant]]
    first = simulate_item_contract(compiler, workspace_map, bindings)
    repeated = simulate_item_contract(compiler, workspace_map, bindings, state=first["state"])
    uncertain = simulate_item_contract(compiler, workspace_map, bindings, uncertain_item_id="notebook_dev")
    blocked_retry = simulate_item_contract(compiler, workspace_map, bindings, state=uncertain["state"])
    wrong = copy.deepcopy(bindings)
    wrong[0]["expected_value"] = "WRONG_PLACEHOLDER"
    rejected = simulate_item_contract(compiler, workspace_map, wrong)
    checks = {"create": first["status"] == "simulated", "repeat_noop": repeated["status"] == "simulated" and all(row["status"] == "noop" for row in repeated["operations"]),
              "binding_conflict_blocked": rejected["status"] == "blocked", "interruption_no_retry": uncertain["status"] == blocked_retry["status"] == "reconciliation_required"}
    if not all(checks.values()):
        raise ValueError("Synthetic item scenarios failed: " + _json(checks))
    return {**MARKER, "revision_hash": revision, "evidence_kind": "simulation", "checks": checks, "first": first, "repeated": repeated,
            "binding_conflict": rejected, "interrupted": uncertain, "retry": blocked_retry}


def _data_check(source):
    totals, seen = {}, set()
    for row in csv.DictReader(io.StringIO(source)):
        if row["sale_id"] in seen:
            raise ValueError("Duplicate synthetic sale ID")
        seen.add(row["sale_id"])
        amount = Decimal(row["amount"])
        if not amount.is_finite() or amount < 0:
            raise ValueError("Invalid synthetic amount")
        totals[row["category"]] = totals.get(row["category"], Decimal(0)) + amount
    if totals != {"hardware": Decimal("30.00"), "services": Decimal("7.50")}:
        raise ValueError("Synthetic arithmetic regression")
    return {"row_count": len(seen), "category_totals": {key: f"{value:.2f}" for key, value in sorted(totals.items())}, "grand_total": f"{sum(totals.values()):.2f}",
            "evidence_kind": "local_check", "runtime": "Python decimal arithmetic; not Fabric, Spark or semantic-model execution"}


def run_reference(root: Path, schemas: Path, variant: str = "dev_test_prod") -> dict:
    """Run one isolated local fixture. root is a trusted, empty host temp folder."""
    if variant not in VARIANTS:
        raise ValueError("Unknown local reference variant")
    root, schemas = Path(root), Path(schemas)
    if not root.is_absolute() or any(path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()) for path in (root, *root.parents)):
        raise ValueError("Local reference root must be an absolute, non-linked empty directory")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("Local reference root must be empty")
    root.mkdir(parents=True, exist_ok=True)
    repo, record, released, decision = _build_repository(root, schemas, variant)
    revision = record.revision_hash
    first = run_automation(repo, PROJECT, revision, actor=ACTOR, confirm_generation=True)
    repeated = run_automation(repo, PROJECT, revision, actor=ACTOR, confirm_generation=True)
    if first["files"] != repeated["files"]:
        raise ValueError("Repeated generation drifted")
    repo.verify()
    workspace = _workspace_checks(repo, revision, root)
    items = _item_checks(released["compiler_input"], variant, revision)
    arithmetic = _data_check((record.package_root / "sales.csv").read_text(encoding="utf-8"))
    graph = read_architecture(repo, PROJECT, revision)["graph"]
    extra = {"SYNTHETIC_ONLY.json": _json({**MARKER, "revision_hash": revision}), "input/brief.md": (record.package_root / "brief.md").read_text(encoding="utf-8"),
             "input/sales.csv": (record.package_root / "sales.csv").read_text(encoding="utf-8"), "evidence/decision_derivation.json": _json(decision),
             "evidence/workspace_simulation.json": _json(workspace), "evidence/item_simulation.json": _json(items), "evidence/local_data_check.json": _json({**arithmetic, "revision_hash": revision})}
    files = [{"path": f"synthetic_outputs/{row['path']}", "content": row["content"]} for row in first["files"]] + [{"path": path, "content": content} for path, content in extra.items()]
    for row in files:
        row["sha256"] = hashlib.sha256(row["content"].encode()).hexdigest()
    checks = [{"id": "immutable_revision", "title": "One final revision", "status": "passed", "evidence_kind": "local_check", "detail": "Real immutable repository verified; all generated target manifests pin the final approved fixture revision."},
              {"id": "reproducible_outputs", "title": "Repeat generation", "status": "passed", "evidence_kind": "local_check", "detail": f"{len(first['files'])} compiler files are byte-identical when generated twice from the same revision."},
              {"id": "local_totals", "title": "Synthetic data totals", "status": "passed", "evidence_kind": "local_check", "detail": "3 rows; hardware 30.00, services 7.50, total 37.50. Python arithmetic only."}]
    for prefix, result in (("workspace", workspace), ("item", items)):
        for id in result["checks"]:
            checks.append({"id": f"{prefix}_{id}", "title": f"{prefix.title()}: {id.replace('_', ' ')}", "status": "passed", "evidence_kind": "simulation", "detail": "Passed against in-memory state. No Fabric acceptance or tenant verification is claimed."})
    checks.append({"id": "tenant_verification", "title": "Tenant verification", "status": "not_run", "evidence_kind": "not_verified", "detail": "No tenant is configured or called. Platform behavior, security, data refresh and reports remain unverified."})
    stages = [{"id": id, "title": title, "status": "passed", "evidence_kind": kind, "summary": summary} for id, title, kind, summary in [
        ("input", "Synthetic brief", "local_check", "Versioned brief and invented sales rows; no customer content."),
        ("decision", "Decision and revision", "local_check", f"Explicit {variant.replace('_', ' / ').upper()} fixture choice applied through reviewed derivation."),
        ("architecture", "Architecture and blueprint", "local_check", "Existing project compilers generate diagram data, workspace and native item requests."),
        ("contracts", "Adapter scenarios", "simulation", "Create, repeated run, conflict and interruption exercised without a tenant."),
        ("documentation", "Evidence and documents", "local_check", "Generated documents, exact file hashes and simulation records are available together.")]]
    report = {"schema_version": "1.0.0", "reference_id": "synthetic_sales_delivery", "run_id": first["report"]["run_id"], "variant": variant, "project_ref": PROJECT,
              "revision_hash": revision, **MARKER, "evidence_kind": "local_check", "stages": stages, "checks": checks, "graph": graph, "files": files,
              "limitations": ["Local approval and release are fixture mechanics, not customer authorization. The live runner rejects the local_reference namespace.",
                  "Only Notebook and DataPipeline native definition transport and JSON bindings are simulated. These placeholder definitions are not an executable end-to-end Fabric data pipeline.",
                  "Lakehouse storage, semantic model and report are logical specifications only; no Spark, DAX, Direct Lake, report rendering or refresh has run.",
                  "The three-row arithmetic check does not prove incremental loading, data volumes, security, promotion, cost, staffing or customer acceptance.",
                  "Real Fabric compatibility and all tenant evidence remain not run until a separately authorized nonproduction tenant is available."]}
    (root / "report.json").write_text(_json(report), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Run synthetic local delivery reference; never a tenant deployment")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--variant", choices=tuple(VARIANTS), default="dev_test_prod")
    args = parser.parse_args()
    try:
        # ASCII transport also works on Windows hosts whose console encoding is
        # not UTF-8; JSON decoding restores the exact Unicode artifact content.
        print(json.dumps({"ok": True, "value": run_reference(args.root, args.schemas, args.variant)}, ensure_ascii=True))
        return 0
    except Exception:
        print(_json({"ok": False, "error": "Local reference failed. No tenant actions were performed."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
