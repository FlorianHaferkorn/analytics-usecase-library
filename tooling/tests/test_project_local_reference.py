"""Real local repository integration. No tenant, token broker or subprocess allowed."""
import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from tooling.superversion.project_package import local_reference as local
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"


@pytest.fixture(scope="module", params=["dev_test_prod", "dev_prod"])
def completed(request, tmp_path_factory):
    root = tmp_path_factory.mktemp("local_reference")
    def forbidden(*args, **kwargs):
        raise AssertionError("Network/process access is forbidden in the local reference")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket, "socket", forbidden)
        patch.setattr(socket, "create_connection", forbidden)
        patch.setattr(subprocess, "Popen", forbidden)
        report = local.run_reference(root, SCHEMAS, request.param)
    return root, report


def test_reference_uses_real_immutable_revision_and_synthetic_namespace(completed):
    root, report = completed
    repo = ProjectPackageRevisionRepository(root / "repositories/local_reference", SCHEMAS)
    record = repo.get(report["revision_hash"])
    assert record.project_ref == "local_reference"
    assert report["source_kind"] == "synthetic"
    assert not report["live_apply_allowed"] and not report["tenant_actions_performed"]
    assert json.loads((record.package_root / "SYNTHETIC_ONLY.json").read_text(encoding="utf-8"))["source_kind"] == "synthetic"
    assert len(list((repo.root / "revisions").iterdir())) == 3
    assert len(report["run_id"]) == 64


def test_exact_file_hashes_and_revision_bound_compiler_manifests(completed):
    _, report = completed
    assert len(report["files"]) >= 20
    assert len({row["path"] for row in report["files"]}) == len(report["files"])
    manifests = []
    for row in report["files"]:
        assert row["sha256"] == hashlib.sha256(row["content"].encode()).hexdigest()
        assert ".." not in Path(row["path"]).parts
        if row["path"].endswith("manifest.json"):
            value = json.loads(row["content"])
            if "revision_hash" in value:
                manifests.append(value)
                assert value["revision_hash"] == report["revision_hash"]
    assert len(manifests) >= 3
    assert not any(row["path"].endswith("approval.json") for row in report["files"])
    assert not any("release-attestations" in row["path"] for row in report["files"])


def test_explicit_variant_derives_architecture_and_declared_targets(completed):
    _, report = completed
    decision = json.loads(next(row["content"] for row in report["files"] if row["path"] == "evidence/decision_derivation.json"))
    assert decision["before_revision_hash"] != decision["derived_revision_hash"] != decision["revision_hash"]
    assert decision["preview"]["changes"][0]["before"] == ["dev"]
    assert decision["preview"]["changes"][0]["after"] == local.VARIANTS[report["variant"]]
    assert {change["target"]["field"] for change in decision["preview"]["changes"][1:]} == {"effort", "definition_of_done"} | ({"role_refs"} if report["variant"] == "dev_test_prod" else set())
    impact = json.loads(next(row["content"] for row in report["files"] if row["path"].endswith("delivery/decision-impact-checks.json")))
    assert impact["revision_hash"] == report["revision_hash"]
    assert {check["target"]["field"] for check in impact["checks"][0]["plan_contract_checks"]} == {"role_refs", "effort", "definition_of_done"}
    workspace_nodes = [node for node in report["graph"]["nodes"] if node["kind"] == "workspace"]
    assert sorted(node["details"]["environment"] for node in workspace_nodes) == sorted(local.VARIANTS[report["variant"]])
    native_nodes = [node for node in report["graph"]["nodes"] if node["kind"] == "native_item"]
    assert len(native_nodes) == len(workspace_nodes) * 2
    assert any(node["layer"] == "semantic" for node in report["graph"]["nodes"])
    assert any(node["layer"] == "report" for node in report["graph"]["nodes"])


def test_runtime_claims_are_separate_and_local_totals_are_computed(completed):
    _, report = completed
    assert {row["evidence_kind"] for row in report["checks"]} == {"local_check", "simulation", "not_verified"}
    not_run = next(row for row in report["checks"] if row["id"] == "tenant_verification")
    assert not_run["status"] == "not_run"
    data = json.loads(next(row["content"] for row in report["files"] if row["path"] == "evidence/local_data_check.json"))
    assert data["category_totals"] == {"hardware": "30.00", "services": "7.50"}
    assert data["grand_total"] == "37.50" and data["row_count"] == 3
    assert "not Fabric" in data["runtime"]
    assert any("not an executable" in note for note in report["limitations"])


def test_create_replay_conflict_and_interruption_pass_in_memory(completed):
    _, report = completed
    for family in ("workspace", "item"):
        evidence = json.loads(next(row["content"] for row in report["files"] if row["path"] == f"evidence/{family}_simulation.json"))
        assert evidence["evidence_kind"] == "simulation"
        assert not evidence["tenant_actions_performed"] and not evidence["live_apply_allowed"]
        assert all(evidence["checks"].values())
        assert evidence["checks"]["interruption_no_retry"]
    item = json.loads(next(row["content"] for row in report["files"] if row["path"] == "evidence/item_simulation.json"))
    assert all(not row["attempted"] for row in item["retry"]["operations"])
    assert all(row["resolved_value"].startswith("sim_") for row in item["first"]["resolved_bindings"])


def test_inputs_preserved_and_repeated_artifact_generation_proven(completed):
    root, report = completed
    assert json.loads((root / "report.json").read_text(encoding="utf-8")) == report
    assert next(row for row in report["checks"] if row["id"] == "reproducible_outputs")["status"] == "passed"
    assert next(row["content"] for row in report["files"] if row["path"] == "input/brief.md") == (local.FIXTURE / "brief.md").read_text(encoding="utf-8")
    assert "tooling.tests" not in Path(local.__file__).read_text(encoding="utf-8")


def test_nonempty_root_is_never_overwritten(tmp_path):
    marker = tmp_path / "existing.txt"
    marker.write_text("preserve me", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        local.run_reference(tmp_path, SCHEMAS)
    assert marker.read_text(encoding="utf-8") == "preserve me"


@pytest.mark.parametrize("variant", ["sandbox", "../dev", "DEV", "", None])
def test_unknown_variant_never_creates_files(tmp_path, variant):
    with pytest.raises(ValueError, match="variant"):
        local.run_reference(tmp_path, SCHEMAS, variant)
    assert not list(tmp_path.iterdir())


def test_relative_output_rejected():
    with pytest.raises(ValueError, match="absolute"):
        local.run_reference(Path("relative"), SCHEMAS)


@pytest.mark.parametrize("source", ["sale_id,category,amount\n1,hardware,10\n1,hardware,20\n", "sale_id,category,amount\n1,hardware,-1\n", "sale_id,category,amount\n1,hardware,NaN\n", "sale_id,category,amount\n1,hardware,11\n"])
def test_invalid_source_fails_quality_or_regression_check(source):
    with pytest.raises(ValueError):
        local._data_check(source)


def test_cli_sanitizes_failures_and_does_not_overwrite(tmp_path):
    private = tmp_path / "private_name.txt"
    private.write_text("sensitive fixture must remain", encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "tooling.superversion.project_package.local_reference", "--root", str(tmp_path), "--schemas", str(SCHEMAS)], capture_output=True, text=True, cwd=ROOT, encoding="utf-8", errors="replace")
    assert result.returncode == 1
    value = json.loads(result.stdout)
    assert not value["ok"] and "No tenant actions" in value["error"]
    assert "private_name" not in result.stdout and str(tmp_path) not in result.stdout
    assert private.read_text(encoding="utf-8") == "sensitive fixture must remain"
