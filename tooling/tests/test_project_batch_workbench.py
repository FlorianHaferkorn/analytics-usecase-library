"""Real immutable package integration; no credentials, tenant or customer data."""
import copy
import hashlib
import json
import subprocess
import sys

import pytest
import yaml

from tooling.superversion.project_package import batch_workbench as workbench
from tooling.superversion.project_package.architecture_compile import compile_architecture
from tooling.superversion.project_package.automation import run_automation
from tooling.superversion.project_package.compiler_input import build_compiler_input
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.release import release_input
from tooling.superversion.project_package.repository import StaleProjectPackageDraftError
from tooling.tests.test_project_automation import make_repository, ROOT, SCHEMAS


def contract():
    return {"schema_version": "1.0.0", "id": "sales_batch", "domain": "commercial",
            "source": {"kind": "csv_landing", "object_name": "sales", "landing_path": "Files/landing/sales.csv"},
            "target": {"schema": "erp", "table": "sales"}, "environments": ["dev", "test", "prod"],
            "columns": [{"name": "id", "type": "integer", "nullable": False},
                        {"name": "version", "type": "integer", "nullable": False},
                        {"name": "label", "type": "string", "nullable": True}], "keys": ["id"],
            "load": {"mode": "incremental", "watermark_column": "version", "delete_behavior": "retain", "schema_drift": "fail", "bad_rows": "fail_batch"},
            "naming": {"namespace": "acme"}}


def payload(repo, record, value=None):
    value = contract() if value is None else value
    preview = workbench.preview_batch(repo, "project_demo", record.revision_hash, value)
    return {"project_ref": "project_demo", "revision_hash": record.revision_hash, "contract": value,
            "preview_hash": preview["preview_hash"], "actor": "editor@example.test",
            "rationale": "Reviewed schema, source boundary and incremental semantics.", "confirmed": True}


def saved(tmp_path):
    repo, record = make_repository(tmp_path)
    result = workbench.save_batch(repo, payload(repo, record))
    return repo, repo.get(result["revision_hash"])


def approve(repo, record, tmp_path):
    root = repo.checkout(tmp_path / "approval", record.revision_hash)
    manifest = yaml.safe_load((root / "package.yaml").read_text())
    manifest["state"] = "approved"
    (root / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    new = repo.commit_draft(root, expected_head_hash=record.revision_hash)
    release_input(repo, "project_demo", new.revision_hash, actor="owner@example.test", rationale="Explicit fixture approval of the exact local implementation input.")
    return new


def test_inspect_and_preview_are_readonly_deterministic_and_old_packages_unchanged(tmp_path):
    repo, record = make_repository(tmp_path)
    before = {str(p): p.read_bytes() for p in repo.root.rglob("*") if p.is_file()}
    assert workbench.inspect_batch(repo, "project_demo", record.revision_hash)["contract"] is None
    first = workbench.preview_batch(repo, "project_demo", record.revision_hash, contract())
    assert first == workbench.preview_batch(repo, "project_demo", record.revision_hash, contract())
    assert first["can_save"] and len(first["preview_hash"]) == 64
    assert before == {str(p): p.read_bytes() for p in repo.root.rglob("*") if p.is_file()}
    assert "batch_ingestion" not in build_compiler_input(record.package_root, SCHEMAS)["modules"]


def test_save_keeps_other_modules_and_invalidates_release(tmp_path):
    repo, old = make_repository(tmp_path)
    old_modules = build_compiler_input(old.package_root, SCHEMAS)["modules"]
    result = workbench.save_batch(repo, payload(repo, old))
    new = repo.get(result["revision_hash"])
    compiled = build_compiler_input(new.package_root, SCHEMAS)
    assert result["state"] == "working" and result["parent_revision_hash"] == old.revision_hash
    assert result["release_required"] and not result["tenant_actions_performed"]
    assert compiled["modules"].pop("batch_ingestion") == contract()
    assert compiled["modules"] == old_modules
    assert (new.package_root / result["audit_ref"]).is_file()
    with pytest.raises(ValueError): workbench.build_batch_output(repo, "project_demo", new.revision_hash)
    assert not (repo.root.parent / "release-attestations").exists()


@pytest.mark.parametrize("mutation", ["hash", "confirmation", "actor", "rationale", "field", "contract"])
def test_save_rejects_unreviewed_or_injected_input(tmp_path, mutation):
    repo, record = make_repository(tmp_path)
    request = payload(repo, record)
    if mutation == "hash": request["preview_hash"] = "f" * 64
    elif mutation == "confirmation": request["confirmed"] = "true"
    elif mutation == "actor": request["actor"] = " "
    elif mutation == "rationale": request["rationale"] = "yes"
    elif mutation == "field": request["path"] = "other.json"
    else: request["contract"]["environments"] = ["dev", "prod"]
    with pytest.raises(ValueError): workbench.save_batch(repo, request)
    assert repo.head().revision_hash == record.revision_hash


def test_unknown_sql_and_invalid_keys_block_preview_and_save(tmp_path):
    repo, record = make_repository(tmp_path)
    for changes in [{"source": {**contract()["source"], "kind": "sql_server"}}, {"keys": ["missing"]}]:
        value = {**contract(), **changes}
        preview = workbench.preview_batch(repo, "project_demo", record.revision_hash, value)
        assert not preview["can_save"] and preview["blockers"]
        with pytest.raises(ValueError): workbench.save_batch(repo, payload(repo, record, value))


def test_stale_preview_wrong_project_and_noop_rejected(tmp_path):
    repo, old = make_repository(tmp_path)
    request = payload(repo, old)
    result = workbench.save_batch(repo, request)
    with pytest.raises(StaleProjectPackageDraftError): workbench.save_batch(repo, request)
    with pytest.raises(ValueError): workbench.inspect_batch(repo, "different", result["revision_hash"])
    assert not workbench.preview_batch(repo, "project_demo", result["revision_hash"], contract())["can_save"]


def test_real_batch_repeat_and_new_version_no_persistence(tmp_path):
    repo, record = saved(tmp_path)
    row = {"id": 1, "version": 1, "label": "Synthetic"}
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = workbench.test_batch(repo, "project_demo", record.revision_hash,
        [{"batch_id": "first", "rows": [row]}, {"batch_id": "first", "rows": [row]},
         {"batch_id": "second", "rows": [{**row, "version": 2, "label": "Changed"}]}])
    assert result["batches"][1]["replayed"]
    assert result["batches"][2]["state"]["rows"][0]["label"] == "Changed"
    assert result["evidence_kind"] == "local_check" and not result["tenant_actions_performed"]
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


@pytest.mark.parametrize("batches", [[], [{}], [{"batch_id": "a", "rows": [], "state": {}}], [{"batch_id": "a", "rows": [{}] * 1001}], [{"batch_id": "a", "rows": []}] * 4])
def test_bounded_test_payload(tmp_path, batches):
    repo, record = saved(tmp_path)
    with pytest.raises(ValueError): workbench.test_batch(repo, "project_demo", record.revision_hash, batches)


def test_test_error_does_not_echo_values(tmp_path):
    repo, record = saved(tmp_path)
    with pytest.raises(ValueError) as error:
        workbench.test_batch(repo, "project_demo", record.revision_hash, [{"batch_id": "a", "rows": [{"id": "PRIVATE", "version": 1, "label": None}]}])
    assert "PRIVATE" not in str(error.value)


def test_graph_append_is_scoped_and_preserves_existing(tmp_path):
    repo, record = saved(tmp_path)
    compiled = build_compiler_input(record.package_root, SCHEMAS)
    base = copy.deepcopy(compiled)
    base["modules"].pop("batch_ingestion")
    before = compile_architecture(base, record.revision_hash)
    after = compile_architecture(compiled, record.revision_hash)
    assert all(n in after["graph"]["nodes"] for n in before["graph"]["nodes"])
    added = [n for n in after["graph"]["nodes"] if n["id"].startswith("batch:")]
    assert len(added) == 9
    assert all(n["domain_ref"] == "commercial" and n["use_case_ref"] == "batch:sales_batch" for n in added)


def test_release_export_and_automation_same_revision_real_files(tmp_path):
    repo, record = saved(tmp_path)
    released = approve(repo, record, tmp_path)
    output = workbench.build_batch_output(repo, "project_demo", released.revision_hash)
    assert output["manifest"]["revision_hash"] == released.revision_hash
    files = {f["path"]: f["content"] for f in output["files"]}
    for row in output["manifest"]["files"]:
        assert hashlib.sha256(files[row["path"]].encode()).hexdigest() == row["sha256"]
    result = run_automation(repo, "project_demo", released.revision_hash, actor="editor@example.test", confirm_generation=True, targets=[workbench.TARGET])
    assert result["report"]["revision_hash"] == released.revision_hash
    assert all(f["path"].startswith(workbench.TARGET + "/") for f in result["files"])


def test_cli_rejects_injected_fields_without_path_disclosure(tmp_path):
    repo, record = make_repository(tmp_path)
    result = subprocess.run([sys.executable, "-m", "tooling.superversion.project_package.batch_workbench", "--repository", str(repo.root), "--schemas", str(SCHEMAS), "--mode", "inspect"], cwd=ROOT,
        input=json.dumps({"project_ref": "project_demo", "revision_hash": record.revision_hash, "path": "private"}), text=True, capture_output=True)
    value = json.loads(result.stdout)
    assert result.returncode == 1 and value["status"] == 422 and str(tmp_path) not in result.stdout
