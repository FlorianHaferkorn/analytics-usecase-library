import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tooling.superversion.project_package.decision_derivation import apply_derivation, compile_derivation, preview_derivation
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository, StaleProjectPackageDraftError
from tooling.superversion.project_package.release import release_input
from tooling.tests.test_project_architecture_compile import compiler

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"


def data():
    value = compiler()
    value["modules"]["decision_set"] = {
        "schema_version": "2.0.0", "definitions": [{
            "id": "definition_environment", "source": {"adapter": "engagement_ledger_package_1_0", "raw_id": "E-1", "source_ref": "fixture://decision", "source_hash": "c" * 64},
            "title": "Environment", "question": {"technical_text": "Which environments?"},
            "recommendation": {"text": "Dev/test/prod", "basis": "Fixture", "confidence_raw": "high", "confidence": "high"},
            "options": [{"id": "three", "label": "Dev/test/prod", "kind": "proposal"}, {"id": "two", "label": "Dev/prod", "kind": "alternative"}], "option_details": [],
            "decider": {"text": "Fixture owner", "role_ref": None}, "consequence_if_unresolved": "No deployment",
            "resolution_method": {"where_to_look": "Fixture", "who_knows": "Owner", "if_unclear": "Block"},
            "customer_copy": {"question": "Which environments?", "consequence": "Isolation", "why": "Testing"},
            "due": {"raw": "Before build", "gate": "before_build"}, "placeholder_refs": []}],
        "instances": [{"id": "decision_environment_model", "definition_ref": "definition_environment", "scope_refs": [], "revision": 1, "initialization": "imported",
                       "selection": {"state": "confirmed", "option_ref": "three", "custom_value": None},
                       "approval": {"state": "approved", "proposed_by": "Fixture", "decided_by": "Owner", "rationale": "Approved environment isolation"},
                       "readiness": {"state": "ready_for_decision"}, "delivery": {"state": "not_compiled"}}]}
    architecture = value["modules"]["architecture_input"]
    architecture["environments"]["recommended"] = ["dev", "prod"]
    architecture["decision_rules"] = [{"id": "environment_lanes", "decision_ref": "decision_environment_model", "decision_revision": 1, "option_ref": "three",
        "target": {"collection": "environments", "entity_id": None, "field": "recommended"}, "expected_value": ["dev", "prod"], "value": ["dev", "test", "prod"],
        "rationale": "Show the three explicitly approved isolation stages in the architecture."}]
    return value


def preview(value):
    return compile_derivation(value, "a" * 64, SCHEMAS)


def setup(tmp_path):
    package = migrate_project_package(ROOT / "tooling/tests/fixtures/project_package/v1", tmp_path / "package", SCHEMAS)
    manifest = yaml.safe_load((package / "package.yaml").read_text(encoding="utf-8"))
    modules = data()["modules"]
    for kind in ["decision_set", "architecture_input"]:
        document = modules[kind]
        row = next((item for item in manifest["modules"] if item["module_type"] == kind), None)
        if row is None:
            row = {"module_type": kind, "path": "architecture.yaml", "schema_id": json.loads((SCHEMAS / f"project_{kind}.schema.json").read_text(encoding="utf-8"))["$id"]}
            manifest["modules"].append(row)
        (package / row["path"]).write_text(yaml.safe_dump(document), encoding="utf8")
        row["sha256"] = canonical_sha256(document)
    manifest["state"] = "approved"
    (package / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf8")
    repo = ProjectPackageRevisionRepository(tmp_path / "repositories/project_demo", SCHEMAS)
    return repo, repo.commit(package)


def request(repo, record):
    return {"project_ref": "project_demo", "revision_hash": record.revision_hash,
            "preview_sha256": preview_derivation(repo, "project_demo", record.revision_hash)["preview_sha256"],
            "actor": "reviewer@example.test", "rationale": "Reviewed the exact environment before and after values.", "confirm_apply": True}


def test_preview_is_deterministic_exact_and_readonly():
    value = data()
    before = copy.deepcopy(value)
    result = preview(value)
    assert result == preview(value)
    assert value == before
    assert result["can_apply"]
    assert result["changes"][0]["before"] == ["dev", "prod"]
    assert result["changes"][0]["after"] == ["dev", "test", "prod"]
    assert not result["tenant_actions_performed"]


@pytest.mark.parametrize("mutation", ["revision", "custom", "option", "decider", "rationale", "scope", "identity", "field", "precondition", "schema", "collision", "duplicate"])
def test_bad_mapping_fails_closed(mutation):
    value = data()
    rule = value["modules"]["architecture_input"]["decision_rules"][0]
    decision = value["modules"]["decision_set"]["instances"][0]
    if mutation == "revision": decision["revision"] = 2
    if mutation == "custom": decision["selection"]["custom_value"] = "manual override"
    if mutation == "option": rule["option_ref"] = "unknown"
    if mutation == "decider": decision["approval"]["decided_by"] = None
    if mutation == "rationale": decision["approval"]["rationale"] = None
    if mutation == "scope": decision["scope_refs"] = ["unrelated_workspace"]
    if mutation == "identity": rule["target"]["entity_id"] = "wrong"
    if mutation == "field": rule["target"]["field"] = "decision_ref"
    if mutation == "precondition": rule["expected_value"] = ["sandbox"]
    if mutation == "schema": rule["value"] = ["invalid stage"]
    if mutation in ["collision", "duplicate"]:
        other = copy.deepcopy(rule)
        if mutation == "collision": other["id"] = "second_mapping"
        value["modules"]["architecture_input"]["decision_rules"].append(other)
    result = preview(value)
    assert not result["can_apply"]
    assert result["blockers"]


@pytest.mark.parametrize("state", ["draft", "proposed", "deferred", "rejected", "superseded"])
def test_only_approved_confirmed_selection_can_change_architecture(state):
    value = data()
    value["modules"]["decision_set"]["instances"][0]["approval"]["state"] = state
    result = preview(value)
    assert result["rules"][0]["status"] == "pending"
    assert not result["can_apply"] and not result["changes"]


def test_preselection_and_other_option_do_not_approve_or_apply():
    value = data()
    decision = value["modules"]["decision_set"]["instances"][0]
    decision["selection"]["state"] = "preselected"
    assert preview(value)["rules"][0]["status"] == "pending"
    decision["selection"]["state"] = "confirmed"
    decision["selection"]["option_ref"] = "two"
    assert preview(value)["rules"][0]["status"] == "not_selected"
    assert not preview(value)["blockers"]


def test_no_rules_or_missing_architecture_does_not_invent_changes():
    value = data()
    value["modules"]["architecture_input"].pop("decision_rules")
    assert not preview(value)["can_apply"]
    value["modules"].pop("architecture_input")
    assert preview(value)["rules"] == []


def test_unselected_alternative_can_reference_an_absent_target_without_blocking():
    value = data()
    architecture = value["modules"]["architecture_input"]
    alternative = copy.deepcopy(architecture["decision_rules"][0])
    alternative.update(id="unused_alternative", option_ref="two", target={"collection": "physical_workspaces", "entity_id": "not_created", "field": "name"})
    architecture["decision_rules"].append(alternative)
    result = preview(value)
    assert result["can_apply"] and not result["blockers"]
    assert result["rules"][1]["status"] == "not_selected"


def test_unrelated_decision_cannot_accept_environment_or_rewrite_workspace():
    for collection in ["environments", "physical_workspaces"]:
        value = data()
        architecture = value["modules"]["architecture_input"]
        if collection == "environments":
            architecture["environments"]["decision_ref"] = "another_decision"
        else:
            rule = architecture["decision_rules"][0]
            rule.update(target={"collection": collection, "entity_id": "workspace_gold_dev", "field": "name"}, expected_value="acme_commercial_gold_dev", value="new_name")
            architecture[collection][0]["decision_refs"] = ["another_decision"]
        result = preview(value)
        assert result["blockers"] and not result["can_apply"]


def test_array_reordering_uses_identity_not_position():
    value = data()
    architecture = value["modules"]["architecture_input"]
    rule = architecture["decision_rules"][0]
    rule.update(target={"collection": "physical_workspaces", "entity_id": "workspace_gold_dev", "field": "name"},
                expected_value="acme_commercial_gold_dev", value="acme_sales_gold_dev")
    other = copy.deepcopy(architecture["physical_workspaces"][0])
    other.update(id="another", name="do_not_touch")
    architecture["physical_workspaces"].insert(0, other)
    assert preview(value)["changes"][0]["before"] == "acme_commercial_gold_dev"


def test_apply_real_package_preserves_decisions_history_and_requires_new_release(tmp_path):
    repo, first = setup(tmp_path)
    with pytest.raises(ValueError, match="decision effects"):
        release_input(repo, "project_demo", first.revision_hash, actor="owner", rationale="Cannot release unapplied decision effects.")
    payload = request(repo, first)
    result = apply_derivation(repo, payload)
    second = repo.head()
    assert second.parent_revision_hash == first.revision_hash
    assert result["state"] == "working" and result["release_required"]
    manifest = yaml.safe_load((second.package_root / "package.yaml").read_text(encoding="utf-8"))
    assert manifest["state"] == "working"
    for module in manifest["modules"]:
        if module["module_type"] != "architecture_input":
            assert (first.package_root / module["path"]).read_bytes() == (second.package_root / module["path"]).read_bytes()
    audit = json.loads((second.package_root / result["audit_ref"]).read_text(encoding="utf-8"))
    assert audit["reviewed_by"] == payload["actor"]
    assert audit["preview_sha256"] == payload["preview_sha256"]
    assert audit["changes"][0]["decision_sha256"] == canonical_sha256(data()["modules"]["decision_set"]["instances"][0])
    fresh = preview_derivation(repo, "project_demo", second.revision_hash)
    assert not fresh["can_apply"]
    assert fresh["rules"][0]["status"] == "unchanged"
    with pytest.raises(ValueError): release_input(repo, "project_demo", second.revision_hash)
    with pytest.raises(StaleProjectPackageDraftError): apply_derivation(repo, payload)


@pytest.mark.parametrize("status", ["ready", "blocked", "pending"])
def test_release_rejects_unapplied_conflicting_or_unconfirmed_rules_without_attestation(tmp_path, status):
    repo, first = setup(tmp_path)
    if status != "ready":
        draft = repo.checkout(tmp_path / "modified", first.revision_hash)
        if status == "blocked":
            path = draft / "architecture.yaml"
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document["decision_rules"][0]["expected_value"] = ["sandbox"]
        else:
            path = draft / "discovery/decision_set.yaml"
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document["instances"][0]["selection"]["state"] = "selected"
        path.write_text(yaml.safe_dump(document), encoding="utf8")
        first = repo.commit_draft(draft, expected_head_hash=first.revision_hash)
    with pytest.raises(ValueError, match="decision effects"):
        release_input(repo, "project_demo", first.revision_hash, actor="owner", rationale="Review explicit architecture decision effects before release.")
    release_root = repo.root.parent / "release-attestations" / repo.root.name
    assert not release_root.exists()


def test_derived_architecture_releases_only_after_explicit_package_approval(tmp_path):
    repo, first = setup(tmp_path)
    result = apply_derivation(repo, request(repo, first))
    with pytest.raises(ValueError, match="package_not_approved"):
        release_input(repo, "project_demo", result["revision_hash"], actor="owner", rationale="Working architecture is not approved for release.")
    draft = repo.checkout(tmp_path / "approval", result["revision_hash"])
    manifest = yaml.safe_load((draft / "package.yaml").read_text(encoding="utf-8"))
    manifest["state"] = "approved"
    (draft / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf8")
    approved = repo.commit_draft(draft, expected_head_hash=result["revision_hash"])
    released = release_input(repo, "project_demo", approved.revision_hash, actor="owner", rationale="Reviewed and approved the explicitly derived architecture.")
    assert released["release"]["revision_hash"] == approved.revision_hash
    assert released["compiler_input"]["modules"]["architecture_input"]["environments"]["recommended"] == ["dev", "test", "prod"]


def test_existing_legacy_attestation_cannot_bypass_decision_effect_gate(tmp_path):
    from tooling.superversion.project_package.compiler_input import build_compiler_input

    repo, first = setup(tmp_path)
    path = repo.root.parent / "release-attestations" / repo.root.name / f"{first.revision_hash}.json"
    approval = {"schema_version": "1.0.0", "scope": "approved_project_input_bundle", "project_ref": "project_demo",
                "revision_hash": first.revision_hash, "compiler_input_sha256": canonical_sha256(build_compiler_input(first.package_root, SCHEMAS)),
                "attested_by": "legacy_owner", "attested_at": "2026-09-07T12:00:00Z", "rationale": "Previously attested without a derivation gate."}
    approval["record_sha256"] = canonical_sha256(approval)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(approval), encoding="utf8")
    before = path.read_bytes()
    for actor in [None, "owner"]:
        with pytest.raises(ValueError, match="decision effects"):
            release_input(repo, "project_demo", first.revision_hash, actor=actor, rationale="Existing attestation must not bypass decision effects.")
    assert path.read_bytes() == before


@pytest.mark.parametrize("mutation", ["hash", "project", "confirmation", "actor", "rationale", "extra"])
def test_bad_apply_request_never_changes_head(tmp_path, mutation):
    repo, first = setup(tmp_path)
    payload = request(repo, first)
    if mutation == "hash": payload["preview_sha256"] = "b" * 64
    if mutation == "project": payload["project_ref"] = "other_project"
    if mutation == "confirmation": payload["confirm_apply"] = False
    if mutation == "actor": payload["actor"] = ""
    if mutation == "rationale": payload["rationale"] = "yes"
    if mutation == "extra": payload["command"] = "apply"
    with pytest.raises(ValueError): apply_derivation(repo, payload)
    assert repo.head().revision_hash == first.revision_hash


def test_cli_preview_and_apply_use_real_repository(tmp_path):
    repo, first = setup(tmp_path)
    command = [sys.executable, "-m", "tooling.superversion.project_package.decision_derivation", "--repository", str(repo.root), "--schemas", str(SCHEMAS)]
    result = subprocess.run([*command, "--mode", "preview"], input=json.dumps({"project_ref": "project_demo", "revision_hash": first.revision_hash}), capture_output=True, text=True, cwd=ROOT, check=True, encoding="utf-8", errors="replace")
    assert json.loads(result.stdout)["value"]["can_apply"]
    result = subprocess.run([*command, "--mode", "apply"], input=json.dumps(request(repo, first)), capture_output=True, text=True, cwd=ROOT, check=True, encoding="utf-8", errors="replace")
    assert json.loads(result.stdout)["value"]["state"] == "working"


def test_concurrent_head_change_is_rejected_at_commit(tmp_path, monkeypatch):
    repo, first = setup(tmp_path)
    payload = request(repo, first)
    original = repo.commit_draft

    def concurrent(root, *, expected_head_hash):
        competing = repo.checkout(tmp_path / "competing", first.revision_hash)
        (competing / "concurrent.txt").write_text("another editor", encoding="utf8")
        original(competing, expected_head_hash=first.revision_hash)
        return original(root, expected_head_hash=expected_head_hash)

    monkeypatch.setattr(repo, "commit_draft", concurrent)
    with pytest.raises(StaleProjectPackageDraftError): apply_derivation(repo, payload)
    assert not list((repo.head().package_root / "architecture/derivations").glob("*.json"))
