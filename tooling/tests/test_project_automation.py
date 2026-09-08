"""Real immutable-repository integration tests; no Fabric or customer writes."""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

from tooling.superversion.project_package.automation import read_automation, read_automation_run, run_automation
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.release import release_input
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository
from tooling.tests.test_project_architecture_compile import compiler

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
ACTOR = "reviewer@example.test"


def make_repository(tmp_path, *, approved=True, architecture=True):
    package = migrate_project_package(ROOT / "tooling/tests/fixtures/project_package/v1", tmp_path / "input", SCHEMAS)
    manifest = yaml.safe_load((package / "package.yaml").read_text(encoding="utf-8"))
    if architecture:
        modules = compiler()["modules"]
        modules["architecture_input"].pop("physical_workspaces")
        for kind in ("architecture_input", "use_case_delivery"):
            document = modules[kind]
            relative = kind + ".yaml"
            (package / relative).write_text(yaml.safe_dump(document), encoding="utf-8")
            schema = json.loads((SCHEMAS / f"project_{kind}.schema.json").read_text(encoding="utf-8"))
            manifest["modules"].append({"module_type": kind, "path": relative, "schema_id": schema["$id"], "sha256": canonical_sha256(document)})
    manifest["state"] = "approved" if approved else "working"
    (package / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    repository = ProjectPackageRevisionRepository(tmp_path / "repositories" / "project_demo", SCHEMAS)
    record = repository.commit(package)
    return repository, record


def attest(repository, record):
    return release_input(repository, "project_demo", record.revision_hash, actor=ACTOR, rationale="Explicit approval of neutral fixture inputs only.")


def run(repository, record, **options):
    return run_automation(repository, "project_demo", record.revision_hash, actor=ACTOR, confirm_generation=True,
                          targets=["architecture_bundle"], **options)


def test_status_is_read_only_and_does_not_equate_presence_with_approval(tmp_path):
    repository, record = make_repository(tmp_path)
    before = set(tmp_path.rglob("*"))
    status = read_automation(repository, "project_demo", record.revision_hash)
    assert before == set(tmp_path.rglob("*"))
    stages = {item["id"]: item for item in status["stages"]}
    assert stages["discovery"]["status"] == "recorded"
    assert stages["commercial"]["status"] == stages["plan"]["status"] == "blocked"
    assert stages["verification"]["status"] == "unsupported"
    assert stages["decisions"]["status"] == "blocked"
    assert not status["generation_allowed"]
    assert not status["can_generate"]
    assert not status["delivery_complete"]
    assert status["latest_run"] is None
    assert repository.head().revision_hash == record.revision_hash


def test_approved_package_is_not_automatically_released(tmp_path):
    repository, record = make_repository(tmp_path)
    with pytest.raises(ValueError, match="no explicit release"):
        run(repository, record)
    assert not (repository.root.parent / "automation-runs").exists()


def test_saved_output_download_is_read_only_and_keeps_exact_artifacts(tmp_path):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    output = run(repository, record)
    before = set(tmp_path.rglob("*"))
    downloaded = read_automation_run(repository, "project_demo", record.revision_hash, output["report"]["run_id"])
    assert downloaded == output
    assert set(tmp_path.rglob("*")) == before
    with pytest.raises(ValueError):
        read_automation_run(repository, "different_project", record.revision_hash, output["report"]["run_id"])
    with pytest.raises(ValueError):
        read_automation_run(repository, "project_demo", record.revision_hash, "../../escape")


def test_unapproved_package_cannot_generate(tmp_path):
    repository, record = make_repository(tmp_path, approved=False)
    with pytest.raises(ValueError, match="package_not_approved"):
        run(repository, record)


@pytest.mark.parametrize("project,revision", [("other", None), ("project_demo", "../escape"), ("project_demo", "" )])
def test_identity_is_mandatory(tmp_path, project, revision):
    repository, record = make_repository(tmp_path)
    with pytest.raises(ValueError):
        read_automation(repository, project, record.revision_hash if revision is None else revision)


def test_blocked_target_blocks_whole_run_not_partial_success(tmp_path):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    with pytest.raises(ValueError, match="Target blocked"):
        run_automation(repository, "project_demo", record.revision_hash, actor=ACTOR, confirm_generation=True)
    assert not (repository.root.parent / "automation-runs").exists()


def test_selected_run_is_persistent_deterministic_and_does_not_edit_package(tmp_path):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    first = run(repository, record)
    second = run(repository, record)
    assert first == second
    assert first["report"]["targets"] == ["architecture_bundle"]
    assert first["report"]["status"] == "generated"
    assert not first["report"]["apply_ready"]
    assert not first["report"]["tenant_actions_performed"]
    assert not first["report"]["delivery_complete"]
    assert len(first["files"]) > 2
    assert all(file["path"].startswith("architecture_bundle/") for file in first["files"])
    assert read_automation(repository, "project_demo", record.revision_hash)["latest_run"] == first["report"]
    repository.verify()
    assert repository.head().revision_hash == record.revision_hash
    assert len(list((repository.root.parent / "automation-runs").rglob("*.json"))) == 1


def test_parallel_same_input_reuses_single_immutable_run(tmp_path):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(repository, record), range(2)))
    assert results[0] == results[1]
    assert len(list((repository.root.parent / "automation-runs").rglob("*.json"))) == 1


@pytest.mark.parametrize("field", ["artifact", "report"])
def test_corrupted_stored_output_is_not_reused(tmp_path, field):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    run(repository, record)
    path = next((repository.root.parent / "automation-runs").rglob("*.json"))
    value = json.loads(path.read_text(encoding="utf-8"))
    if field == "artifact":
        value["files"][0]["content"] += "tamper"
    else:
        value["report"]["actor"] = "someone-else"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        run(repository, record)
    with pytest.raises(ValueError, match="integrity"):
        read_automation(repository, "project_demo", record.revision_hash)


def test_stale_revision_retains_history_but_cannot_generate(tmp_path):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    run(repository, record)
    draft = repository.checkout(tmp_path / "draft", record.revision_hash)
    opportunity = draft / "opportunity/opportunity.yaml"
    document = yaml.safe_load(opportunity.read_text(encoding="utf-8"))
    document["objectives"].append("New scope requires fresh review")
    opportunity.write_text(yaml.safe_dump(document), encoding="utf-8")
    repository.commit_draft(draft, expected_head_hash=record.revision_hash)
    status = read_automation(repository, "project_demo", record.revision_hash)
    assert status["latest_run"] is not None
    assert not status["is_current_revision"]
    assert not status["generation_allowed"]
    with pytest.raises(ValueError, match="no longer HEAD"):
        run(repository, record)


@pytest.mark.parametrize("actor,confirm,targets", [("", True, ["architecture_bundle"]), (ACTOR, False, ["architecture_bundle"]), (ACTOR, True, []), (ACTOR, True, ["tenant_apply"]), (ACTOR, True, ["architecture_bundle", "architecture_bundle"])])
def test_explicit_authority_and_supported_target_required(tmp_path, actor, confirm, targets):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    with pytest.raises(ValueError):
        run_automation(repository, "project_demo", record.revision_hash, actor=actor, confirm_generation=confirm, targets=targets)


def test_cli_returns_structured_status(tmp_path):
    repository, record = make_repository(tmp_path)
    result = subprocess.run([sys.executable, "-m", "tooling.superversion.project_package.automation", "--repository", str(repository.root), "--schemas", str(SCHEMAS), "--project-ref", "project_demo", "--revision", record.revision_hash], cwd=ROOT, capture_output=True, text=True, check=True)
    response = json.loads(result.stdout)
    assert response["ok"] is True
    assert response["value"]["revision_hash"] == record.revision_hash


def test_storage_collision_is_rejected_without_overwriting(tmp_path):
    repository, record = make_repository(tmp_path)
    attest(repository, record)
    collision = repository.root.parent / "automation-runs"
    collision.write_text("Unrelated data", encoding="utf-8")
    with pytest.raises(ValueError, match="real directory"):
        run(repository, record)
    assert collision.read_text(encoding="utf-8") == "Unrelated data"


def test_head_change_during_generation_does_not_persist_stale_run(tmp_path, monkeypatch):
    from tooling.superversion.project_package import automation

    repository, record = make_repository(tmp_path)
    attest(repository, record)
    original = automation.build_architecture_output

    def generate_then_advance(*args):
        output = original(*args)
        draft = repository.checkout(tmp_path / "concurrent-draft", record.revision_hash)
        opportunity = draft / "opportunity/opportunity.yaml"
        document = yaml.safe_load(opportunity.read_text(encoding="utf-8"))
        document["objectives"].append("Concurrent edit")
        opportunity.write_text(yaml.safe_dump(document), encoding="utf-8")
        repository.commit_draft(draft, expected_head_hash=record.revision_hash)
        return output

    monkeypatch.setattr(automation, "build_architecture_output", generate_then_advance)
    with pytest.raises(ValueError, match="HEAD changed during generation"):
        run(repository, record)
    assert not (repository.root.parent / "automation-runs").exists()
