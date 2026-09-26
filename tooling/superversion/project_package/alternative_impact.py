"""Read-only impact comparison of a draft decision alternative against a released baseline.

The comparison evaluates the authored decision rules as if the alternative option were
selected. It never records a decision, commits a revision, writes a release record or
contacts a tenant. It reports what would change and which obligations remain before the
alternative could itself be released.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .decision_derivation import _target, compile_derivation
from .hashes import canonical_sha256
from .migrations import migrate_project_package
from .release import release_input
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
FIXTURE = Path(__file__).resolve().parents[3] / "core/fixtures/neutral/alternative-impact-reference"
REFERENCE_PROJECT = "alternative_impact_reference"
REFERENCE_ACTOR = "synthetic_fixture_not_a_customer"
REFERENCE_DECISION = "decision_environment_model"
DOMAINS = {"domain_sales": ("sales", "11111111-1111-4111-8111-000000000001"),
           "domain_finance": ("finance", "11111111-1111-4111-8111-000000000002")}
CAPACITY = "22222222-2222-4222-8222-222222222222"
OPTIONS = {"dev_test_prod": ["dev", "test", "prod"], "dev_prod": ["dev", "prod"]}
PLAN_VALUES = {
    "dev_test_prod": {"role_refs": ["fabric_engineer", "test_lead"], "effort": 6,
                      "definition_of_done": ["DEV, TEST and PROD lanes validated for sales and finance"]},
    "dev_prod": {"role_refs": ["fabric_engineer"], "effort": 4,
                 "definition_of_done": ["DEV and PROD lanes validated for sales and finance"]},
}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _fingerprint(repository: ProjectPackageRevisionRepository) -> str:
    """Repository history, HEAD and release records; any write changes this value."""
    head = repository.head()
    revisions = sorted(path.name for path in repository.revisions_root.iterdir()) if repository.revisions_root.exists() else []
    release_root = repository.root.parent / "release-attestations" / repository.root.name
    releases = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(release_root.glob("*.json"))} if release_root.exists() else {}
    return canonical_sha256({"head": head.revision_hash if head else None, "revisions": revisions, "releases": releases})


def _view(modules: dict, decisions: dict, decision_ref: str, intended: list[str] | None = None) -> dict:
    """Project the comparable facts of one package state. Pure.

    ``intended`` names the stages an authored rule targets when that rule is blocked, so
    topology gaps stay visible although no change could be projected.
    """
    architecture = modules["architecture_input"]
    plan = modules.get("plan") or {"work_packages": [], "tasks": []}
    selected = list(architecture["environments"]["recommended"])
    wanted = list(intended or selected)
    instance = next(item for item in decisions["instances"] if item["id"] == decision_ref)
    option = instance["selection"]["option_ref"]
    packages = {row["id"]: {"role_refs": row["role_refs"], "effort": row["effort"]}
                for row in plan.get("work_packages", []) if decision_ref in row["decision_refs"]}
    tasks = {row["id"]: row["definition_of_done"] for row in plan.get("tasks", []) if decision_ref in row["decision_refs"]}
    effort: dict[str, float] = {}
    for row in packages.values():
        if row["effort"].get("value") is not None:
            effort[row["effort"]["unit"]] = effort.get(row["effort"]["unit"], 0) + row["effort"]["value"]
    workspaces = architecture.get("physical_workspaces", [])
    items = architecture.get("physical_items", [])
    authored = wanted + sorted({row["environment"] for row in workspaces} - set(wanted))
    topology = []
    for domain in architecture["domains"]:
        if domain["delivery_scope"] != "detailed":
            continue
        for stage in authored:
            present = [row["id"] for row in workspaces if row["domain_ref"] == domain["id"] and row["environment"] == stage]
            state = ("selected_and_authored" if present else "selected_but_missing") if stage in wanted else (
                "authored_but_unselected" if present else "absent")
            if state != "absent":
                topology.append({"domain_ref": domain["id"], "environment": stage, "state": state, "workspace_refs": present})
    manifests = {}
    for row in workspaces:
        if row["environment"] in selected:
            body = {"displayName": row["name"], "capacityId": row["capacity_id"], "domainId": row["domain_id"]}
            if "description" in row:
                body["description"] = row["description"]
            manifests[f"fabric/workspaces/{row['id']}.request.json"] = hashlib.sha256(_json(body).encode()).hexdigest()
    for row in items:
        if row["environment"] in selected:
            manifests[f"fabric/items/{row['id']}.definition.json"] = canonical_sha256(row)
    checks = []
    for rule in architecture.get("decision_rules", []):
        if rule["decision_ref"] == decision_ref and rule["option_ref"] == option and rule.get("plan_effects"):
            checks.append({"rule_id": rule["id"], "checks": sorted(
                f"{effect['target']['collection']}/{effect['target']['entity_id']}/{effect['target']['field']}="
                + canonical_sha256(effect["value"]) for effect in rule["plan_effects"])})
    execution = sorted([f"workspace_readback:{row['id']}" for row in workspaces if row["environment"] in selected]
                       + [f"binding:{row['id']}{binding['json_pointer']}={binding['expected_value']}"
                          for row in items if row["environment"] in selected for binding in row["environment_bindings"]])
    return {"option_ref": option, "environments": selected, "work_packages": packages, "tasks": tasks,
            "role_demand": sorted({role for row in packages.values() for role in row["role_refs"]}),
            "effort_totals": dict(sorted(effort.items())), "topology": topology, "manifests": dict(sorted(manifests.items())),
            "tests": {"decision_impact_checks": sorted(checks, key=lambda row: row["rule_id"]),
                      "lane_acceptance": dict(sorted(tasks.items())), "execution_obligations": execution}}


def _set_delta(before: list, after: list) -> dict:
    return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "unchanged": sorted(set(before) & set(after))}


def _map_delta(before: dict, after: dict) -> dict:
    return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "changed": sorted(key for key in set(before) & set(after) if before[key] != after[key])}


def compare_alternative(repository: ProjectPackageRevisionRepository, project_ref: str, baseline_revision: str,
                        decision_ref: str, option_ref: str) -> dict:
    """Compare a released baseline with one declared alternative option. Read-only."""
    before_fingerprint = _fingerprint(repository)
    released = release_input(repository, project_ref, baseline_revision)  # verification only; actor absent
    compiler = copy.deepcopy(released["compiler_input"])
    decisions = compiler["modules"]["decision_set"]
    instances = [item for item in decisions["instances"] if item["id"] == decision_ref]
    if len(instances) != 1:
        raise ValueError("Decision identity must match exactly one instance")
    instance = instances[0]
    definition = next(item for item in decisions["definitions"] if item["id"] == instance["definition_ref"])
    if option_ref not in {option["id"] for option in definition["options"]}:
        raise ValueError("Alternative option is not declared for this decision")
    if instance["approval"]["state"] != "approved" or instance["selection"]["state"] != "confirmed":
        raise ValueError("Baseline decision is not accepted; compare only against an approved, confirmed selection")
    if instance["selection"]["custom_value"] is not None:
        raise ValueError("Custom baseline values are outside the bounded comparison contract")
    if instance["selection"]["option_ref"] == option_ref:
        raise ValueError("Alternative equals the accepted baseline option")
    if not compiler["modules"].get("architecture_input"):
        raise ValueError("Architecture input is missing")

    hypothetical = copy.deepcopy(compiler)
    target = next(item for item in hypothetical["modules"]["decision_set"]["instances"] if item["id"] == decision_ref)
    target["selection"]["option_ref"] = option_ref
    derivation = compile_derivation(hypothetical, baseline_revision, repository.schema_root)
    blockers = list(derivation["blockers"])
    mapped = [rule for rule in derivation["rules"] if rule["decision_ref"] == decision_ref and rule["option_ref"] == option_ref]
    if not mapped:
        blockers.append("No authored decision rule maps the alternative option; its impacts cannot be derived")
    projected = {"architecture_input": copy.deepcopy(hypothetical["modules"]["architecture_input"]),
                 "plan": copy.deepcopy(hypothetical["modules"].get("plan"))}
    for change in derivation["changes"]:
        _target(projected, change["target"])[change["target"]["field"]] = copy.deepcopy(change["after"])

    base = _view(compiler["modules"], decisions, decision_ref)
    intended = next((rule["value"] for rule in projected["architecture_input"].get("decision_rules", [])
                     if rule["decision_ref"] == decision_ref and rule["option_ref"] == option_ref
                     and rule["target"] == {"collection": "environments", "entity_id": None, "field": "recommended"}), None)
    alt = _view(projected, hypothetical["modules"]["decision_set"], decision_ref, intended if blockers else None)
    obligations = [
        {"id": "record_decision_revision", "detail": "Record a new decision revision selecting the alternative and obtain approval through the decision process; review every rule pinned to the current revision against it."},
        {"id": "apply_reviewed_derivation", "detail": "Preview and apply the derivation on the package HEAD; this report is not that review."},
        {"id": "release_new_input", "detail": "Release the resulting approved revision; the baseline release does not cover it."},
    ]
    for row in alt["topology"]:
        if row["state"] == "authored_but_unselected":
            obligations.append({"id": f"retire_topology:{row['domain_ref']}/{row['environment']}",
                                "detail": "Authored workspaces for an unselected stage block workspace outputs; remove or rescope them in a reviewed topology change: "
                                + ", ".join(row["workspace_refs"])})
        elif row["state"] == "selected_but_missing":
            obligations.append({"id": f"author_topology:{row['domain_ref']}/{row['environment']}",
                                "detail": "Author workspace and item definitions for this stage; stages are never inferred from a label."})
    for task_id in _map_delta(base["tasks"], alt["tasks"])["changed"]:
        obligations.append({"id": f"reconfirm_acceptance:{task_id}", "detail": "Lane acceptance criterion changes; earlier evidence does not carry over."})
    impacts = {
        "architecture": {"environments": _set_delta(base["environments"], alt["environments"])},
        "plan": {"work_packages": {key: {"before": base["work_packages"].get(key), "after": alt["work_packages"].get(key)}
                                   for key in _map_delta(base["work_packages"], alt["work_packages"])["changed"]},
                 "tasks": {key: {"before": base["tasks"].get(key), "after": alt["tasks"].get(key)}
                           for key in _map_delta(base["tasks"], alt["tasks"])["changed"]}},
        "staffing": {"role_demand": _set_delta(base["role_demand"], alt["role_demand"]),
                     "effort_totals": {"before": base["effort_totals"], "after": alt["effort_totals"]},
                     "named_staffing_or_cost_evaluated": False},
        "topology": {"baseline": base["topology"], "alternative": alt["topology"]},
        "manifests": _map_delta(base["manifests"], alt["manifests"]),
        "tests": {"decision_impact_checks": {"before": base["tests"]["decision_impact_checks"], "after": alt["tests"]["decision_impact_checks"]},
                  "lane_acceptance": {"before": base["tests"]["lane_acceptance"], "after": alt["tests"]["lane_acceptance"]},
                  "execution_obligations": _set_delta(base["tests"]["execution_obligations"], alt["tests"]["execution_obligations"])},
    }
    if before_fingerprint != _fingerprint(repository):
        raise RuntimeError("Baseline repository changed during a read-only comparison")
    result = {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
              "baseline_release_record_sha256": released["release"]["record_sha256"], "decision_ref": decision_ref,
              "baseline_option_ref": base["option_ref"], "alternative_option_ref": option_ref,
              "status": "blocked" if blockers else "impact_ready", "blockers": sorted(set(blockers)),
              "derivation_rules": derivation["rules"], "impacts": impacts, "obligations": obligations,
              "baseline_unchanged": True, "hypothetical": True, "approval_granted": False, "release_granted": False,
              "tenant_actions_performed": False,
              "limitations": ["Hypothetical evaluation of authored rules; not a decision, derivation review or release.",
                              "Manifests are projected hashes of declared targets, not generated deployment artifacts.",
                              "Role demand and effort are package assumptions; named staffing, rates and duration are not evaluated.",
                              "Execution obligations list what must be tested; nothing is executed against a tenant."]}
    return {**result, "impact_sha256": canonical_sha256(result)}


def _part(path: str, value: Any) -> dict:
    content = value if isinstance(value, str) else _json(value)
    return {"path": path, "payload": base64.b64encode(content.encode()).decode(), "payloadType": "InlineBase64"}


def _reference_architecture(baseline: str, stages: list[str], with_alternative_rule: bool) -> dict:
    workspaces, items = [], []
    for domain_ref, (key, domain_id) in DOMAINS.items():
        for stage in stages:
            workspace = f"ws_{key}_{stage}"
            workspaces.append({"id": workspace, "name": f"synthetic_mfg_{key}_{stage}", "domain_ref": domain_ref, "environment": stage,
                               "capacity_id": CAPACITY, "domain_id": domain_id, "decision_refs": [REFERENCE_DECISION]})
            common = {"workspace_ref": workspace, "environment": stage, "decision_refs": [REFERENCE_DECISION]}
            items.append({**common, "id": f"nb_{key}_{stage}", "name": f"nb_{key}_load_{stage}", "type": "Notebook", "depends_on": [],
                          "environment_bindings": [], "definition": {"format": "FabricGitSource", "parts": [
                              _part("notebook-content.py", "# SYNTHETIC_ONLY: transport example, not a runnable data platform\n")]}})
            pipeline = {"properties": {"activities": [], "parameters": {"environment": {"type": "String", "defaultValue": stage}}}}
            items.append({**common, "id": f"pl_{key}_{stage}", "name": f"pl_{key}_{stage}", "type": "DataPipeline", "depends_on": [f"nb_{key}_{stage}"],
                          "environment_bindings": [{"part_path": "pipeline-content.json", "json_pointer": "/properties/parameters/environment/defaultValue",
                                                    "expected_value": stage, "authority_ref": "synthetic://environment"}],
                          "definition": {"parts": [_part("pipeline-content.json", pipeline)]}})
    rules = []
    for option, other in (("dev_test_prod", "dev_prod"), ("dev_prod", "dev_test_prod")):
        if option != baseline and not with_alternative_rule:
            continue
        new, old = PLAN_VALUES[option], PLAN_VALUES[other]
        rules.append({"id": f"environment_lanes_{option}", "decision_ref": REFERENCE_DECISION, "decision_revision": 1, "option_ref": option,
                      "target": {"collection": "environments", "entity_id": None, "field": "recommended"},
                      "expected_value": OPTIONS[other], "value": OPTIONS[option],
                      "rationale": "Map the explicit environment option to lanes, role demand, effort assumption and lane acceptance.",
                      "plan_effects": [
                          {"target": {"collection": "plan_work_packages", "entity_id": "wp_environment_lanes", "field": "role_refs"},
                           "expected_value": old["role_refs"], "value": new["role_refs"]},
                          {"target": {"collection": "plan_work_packages", "entity_id": "wp_environment_lanes", "field": "effort"},
                           "expected_value": {"value": old["effort"], "unit": "person_days", "provenance": "assumption"},
                           "value": {"value": new["effort"], "unit": "person_days", "provenance": "assumption"}},
                          {"target": {"collection": "plan_tasks", "entity_id": "task_lane_acceptance", "field": "definition_of_done"},
                           "expected_value": old["definition_of_done"], "value": new["definition_of_done"]}]})
    return {"schema_version": "2.0.0", "stack": "fabric", "reference_date": "2026-09-26", "tenant": "Synthetic tenant (not connected)",
            "region": "West Europe", "ledger_ref": "synthetic://alternative_impact_reference/decision_set.json",
            "model_ref": "synthetic://alternative_impact_reference/architecture", "blueprint_ref": "synthetic://alternative_impact_reference/outputs",
            "mapping_ref": "synthetic://alternative_impact_reference/bindings",
            "domains": [{"id": ref, "key": key, "capacity": "fbsynthetic01", "delivery_scope": "detailed",
                         "use_case_refs": ["uc_order_to_cash" if key == "sales" else "uc_general_ledger"]} for ref, (key, _) in DOMAINS.items()],
            "use_cases": [{"id": "uc_order_to_cash", "name": "Order to cash (synthetic SAP SD)", "domain_ref": "domain_sales", "architecture_detail": "full"},
                          {"id": "uc_general_ledger", "name": "General ledger (synthetic SAP FI)", "domain_ref": "domain_finance", "architecture_detail": "full"}],
            "environments": {"recommended": OPTIONS[baseline], "accepted": True, "decision_ref": REFERENCE_DECISION}, "contracts": [],
            "compiler_policy": {"version": "1", "generated_ref": "synthetic_outputs", "fail_closed_for_apply": True, "allow_review_with_blockers": True},
            "physical_workspaces": workspaces, "physical_items": items, "decision_rules": rules}


def _reference_plan(baseline: str, task_done: bool) -> dict:
    values = PLAN_VALUES[baseline]
    return {"schema_version": "2.0.0", "dependencies": [],
            "work_packages": [
                {"id": "wp_environment_lanes", "title": "Environment lanes for sales and finance", "status": "planned",
                 "decision_refs": [REFERENCE_DECISION], "role_refs": values["role_refs"],
                 "effort": {"value": values["effort"], "unit": "person_days", "provenance": "assumption"}},
                {"id": "wp_source_contracts", "title": "Synthetic SAP source contracts", "status": "planned",
                 "decision_refs": [], "role_refs": ["data_engineer"], "effort": {"value": 5, "unit": "person_days", "provenance": "assumption"}}],
            "tasks": [{"id": "task_lane_acceptance", "title": "Validate the selected environment lanes", "work_package_ref": "wp_environment_lanes",
                       "status": "done" if task_done else "todo", "priority": "high", "owner_ref": "fabric_engineer", "target_gate": "before_build",
                       "decision_refs": [REFERENCE_DECISION], "definition_of_done": values["definition_of_done"],
                       "evidence_refs": ["synthetic://alternative_impact_reference/lane_evidence"] if task_done else []}]}


def build_reference_baseline(root: Path, schemas: Path, *, baseline: str = "dev_test_prod", stages: list[str] | None = None,
                             with_alternative_rule: bool = True, task_done: bool = False) -> tuple[ProjectPackageRevisionRepository, str]:
    """Build and release the synthetic baseline in an empty trusted directory. Test and reference use only."""
    root, schemas = Path(root), Path(schemas)
    if baseline not in OPTIONS:
        raise ValueError("Unknown baseline option")
    source = root / "source"
    source.mkdir(parents=True)
    source.joinpath("package.yaml").write_text((FIXTURE / "package.json").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    package = migrate_project_package(source, root / "package", schemas)
    manifest = yaml.safe_load((package / "package.yaml").read_text(encoding="utf-8"))
    decision = json.loads((FIXTURE / "decision_set.json").read_text(encoding="utf-8"))
    decision["definitions"][0]["source"]["source_hash"] = hashlib.sha256((FIXTURE / "brief.md").read_bytes()).hexdigest()
    decision["instances"][0]["selection"]["option_ref"] = baseline
    modules = (("decision_set", decision), ("plan", _reference_plan(baseline, task_done)),
               ("architecture_input", _reference_architecture(baseline, stages or OPTIONS[baseline], with_alternative_rule)),
               ("use_case_delivery", json.loads((FIXTURE / "use_case_delivery.json").read_text(encoding="utf-8"))))
    for kind, document in modules:
        row = next((row for row in manifest["modules"] if row["module_type"] == kind), None)
        if row is None:
            row = {"module_type": kind, "path": f"{kind}.yaml"}
            manifest["modules"].append(row)
        (package / row["path"]).write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8", newline="\n")
        row["sha256"] = canonical_sha256(document)
        row["schema_id"] = json.loads((schemas / f"project_{kind}.schema.json").read_text(encoding="utf-8"))["$id"]
    (package / "SYNTHETIC_ONLY.json").write_text(_json({"source_kind": "synthetic", "project_ref": REFERENCE_PROJECT,
                                                       "tenant_actions_performed": False, "live_apply_allowed": False}), encoding="utf-8", newline="\n")
    (package / "brief.md").write_bytes((FIXTURE / "brief.md").read_bytes())
    (package / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
    repository = ProjectPackageRevisionRepository(root / "repositories" / REFERENCE_PROJECT, schemas)
    first = repository.commit(package)
    draft = repository.checkout(root / "approval", first.revision_hash)
    manifest = yaml.safe_load((draft / "package.yaml").read_text(encoding="utf-8"))
    manifest["state"] = "approved"
    (draft / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
    final = repository.commit_draft(draft, expected_head_hash=first.revision_hash)
    release_input(repository, REFERENCE_PROJECT, final.revision_hash, actor=REFERENCE_ACTOR,
                  rationale="Synthetic accepted baseline for the alternative-impact reference; never customer or tenant approval.")
    return repository, final.revision_hash


def run_reference(schemas: Path, option_ref: str = "dev_prod") -> dict:
    """Build the synthetic baseline in a fresh temporary directory and compare one alternative."""
    with tempfile.TemporaryDirectory(prefix="alternative-impact-") as temporary:
        baseline = "dev_test_prod" if option_ref == "dev_prod" else "dev_prod"
        repository, revision = build_reference_baseline(Path(temporary), Path(schemas), baseline=baseline)
        return compare_alternative(repository, REFERENCE_PROJECT, revision, REFERENCE_DECISION, option_ref)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas", required=True, type=Path)
    parser.add_argument("--repository", type=Path, help="Trusted repository path; omit to run the synthetic reference")
    parser.add_argument("--option", default="dev_prod")
    args = parser.parse_args()
    try:
        if args.repository is None:
            value = run_reference(args.schemas, args.option)
        else:
            payload = json.loads(sys.stdin.read(100_001))
            if not isinstance(payload, dict) or set(payload) != {"project_ref", "revision_hash", "decision_ref", "option_ref"}:
                raise ValueError("Invalid comparison request")
            if not re.fullmatch(r"[a-f0-9]{64}", str(payload["revision_hash"])):
                raise ValueError("Invalid request revision")
            value = compare_alternative(ProjectPackageRevisionRepository(args.repository, args.schemas), payload["project_ref"],
                                        payload["revision_hash"], payload["decision_ref"], payload["option_ref"])
        print(json.dumps({"ok": True, "value": value}, ensure_ascii=True))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
