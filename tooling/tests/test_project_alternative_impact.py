"""WB-008: a draft alternative is compared against a released baseline without changing it."""
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tooling.superversion.project_package import alternative_impact as impact
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"
PROJECT, DECISION = impact.REFERENCE_PROJECT, impact.REFERENCE_DECISION


@pytest.fixture()
def no_side_channels():
    def forbidden(*args, **kwargs):
        raise AssertionError("Network/process access is forbidden in the alternative comparison")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket, "socket", forbidden)
        patch.setattr(socket, "create_connection", forbidden)
        patch.setattr(subprocess, "Popen", forbidden)
        yield


def _tree(path: Path) -> dict:
    return {item.relative_to(path).as_posix(): item.read_bytes() for item in sorted(path.rglob("*")) if item.is_file()}


def _baseline(tmp_path, **options):
    return impact.build_reference_baseline(tmp_path, SCHEMAS, **options)


def test_alternative_updates_every_impact_class_without_touching_the_baseline(tmp_path, no_side_channels):
    repository, revision = _baseline(tmp_path)
    before = _tree(tmp_path / "repositories") | {"release/" + k: v for k, v in _tree(tmp_path / "release-attestations").items()}
    report = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_prod")
    after = _tree(tmp_path / "repositories") | {"release/" + k: v for k, v in _tree(tmp_path / "release-attestations").items()}
    assert before == after
    assert repository.head().revision_hash == revision
    assert report["status"] == "impact_ready" and not report["blockers"]
    assert report["baseline_option_ref"] == "dev_test_prod" and report["alternative_option_ref"] == "dev_prod"
    assert report["baseline_unchanged"] and report["hypothetical"]
    assert not report["approval_granted"] and not report["release_granted"] and not report["tenant_actions_performed"]
    impacts = report["impacts"]
    assert impacts["architecture"]["environments"]["removed"] == ["test"]
    assert impacts["plan"]["work_packages"]["wp_environment_lanes"]["after"]["effort"]["value"] == 4
    assert impacts["plan"]["tasks"]["task_lane_acceptance"]["after"] == ["DEV and PROD lanes validated for sales and finance"]
    assert "wp_source_contracts" not in impacts["plan"]["work_packages"]
    assert impacts["staffing"]["role_demand"]["removed"] == ["test_lead"]
    assert impacts["staffing"]["effort_totals"] == {"before": {"person_days": 6}, "after": {"person_days": 4}}
    assert not impacts["staffing"]["named_staffing_or_cost_evaluated"]
    assert impacts["manifests"]["removed"] == sorted([
        "fabric/items/nb_finance_test.definition.json", "fabric/items/nb_sales_test.definition.json",
        "fabric/items/pl_finance_test.definition.json", "fabric/items/pl_sales_test.definition.json",
        "fabric/workspaces/ws_finance_test.request.json", "fabric/workspaces/ws_sales_test.request.json"])
    assert not impacts["manifests"]["added"] and not impacts["manifests"]["changed"]
    tests = impacts["tests"]
    assert [row["rule_id"] for row in tests["decision_impact_checks"]["before"]] == ["environment_lanes_dev_test_prod"]
    assert [row["rule_id"] for row in tests["decision_impact_checks"]["after"]] == ["environment_lanes_dev_prod"]
    assert set(tests["execution_obligations"]["removed"]) == {
        "workspace_readback:ws_sales_test", "workspace_readback:ws_finance_test",
        "binding:pl_sales_test/properties/parameters/environment/defaultValue=test",
        "binding:pl_finance_test/properties/parameters/environment/defaultValue=test"}
    obligations = {row["id"] for row in report["obligations"]}
    assert {"record_decision_revision", "apply_reviewed_derivation", "release_new_input",
            "retire_topology:domain_sales/test", "retire_topology:domain_finance/test",
            "reconfirm_acceptance:task_lane_acceptance"} == obligations


def test_comparison_is_deterministic(tmp_path):
    repository, revision = _baseline(tmp_path)
    first = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_prod")
    second = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_prod")
    assert first["impact_sha256"] == second["impact_sha256"]
    assert first == second


def test_expansion_without_authored_topology_is_blocked_and_names_the_gap(tmp_path):
    repository, revision = _baseline(tmp_path, baseline="dev_prod")
    report = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_test_prod")
    assert report["status"] == "blocked"
    assert any("domain_sales/test" in blocker and "domain_finance/test" in blocker for blocker in report["blockers"])
    assert {"author_topology:domain_sales/test", "author_topology:domain_finance/test"} <= {row["id"] for row in report["obligations"]}
    assert report["impacts"]["manifests"] == {"added": [], "removed": [], "changed": []}
    assert repository.head().revision_hash == revision


def test_expansion_with_authored_topology_adds_manifests_roles_and_tests(tmp_path):
    repository, revision = _baseline(tmp_path, baseline="dev_prod", stages=["dev", "test", "prod"])
    report = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_test_prod")
    assert report["status"] == "impact_ready"
    assert report["impacts"]["architecture"]["environments"]["added"] == ["test"]
    assert report["impacts"]["staffing"]["role_demand"]["added"] == ["test_lead"]
    assert len(report["impacts"]["manifests"]["added"]) == 6
    assert "workspace_readback:ws_sales_test" in report["impacts"]["tests"]["execution_obligations"]["added"]
    assert not any(row["id"].startswith(("retire_topology", "author_topology")) for row in report["obligations"])


def test_missing_mapping_for_the_alternative_is_blocked(tmp_path):
    repository, revision = _baseline(tmp_path, with_alternative_rule=False)
    report = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_prod")
    assert report["status"] == "blocked"
    assert any("No authored decision rule" in blocker for blocker in report["blockers"])
    assert report["impacts"]["plan"] == {"work_packages": {}, "tasks": {}}


def test_completed_acceptance_task_with_evidence_blocks_the_alternative(tmp_path):
    repository, revision = _baseline(tmp_path, task_done=True)
    report = impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_prod")
    assert report["status"] == "blocked"
    assert any("reopen the task separately" in blocker for blocker in report["blockers"])


@pytest.mark.parametrize("option, message", [("dev_test_prod", "equals the accepted baseline"),
                                              ("dev_qa_prod", "not declared")])
def test_invalid_alternatives_are_rejected(tmp_path, option, message):
    repository, revision = _baseline(tmp_path)
    with pytest.raises(ValueError, match=message):
        impact.compare_alternative(repository, PROJECT, revision, DECISION, option)


def test_unreleased_head_is_not_a_baseline(tmp_path):
    repository, revision = _baseline(tmp_path)
    draft = repository.checkout(tmp_path / "edit", revision)
    manifest = yaml.safe_load((draft / "package.yaml").read_text(encoding="utf-8"))
    manifest["state"] = "working"
    (draft / "package.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n")
    working = repository.commit_draft(draft, expected_head_hash=revision)
    with pytest.raises(ValueError):
        impact.compare_alternative(repository, PROJECT, working.revision_hash, DECISION, "dev_prod")
    with pytest.raises(ValueError, match="no longer HEAD"):
        impact.compare_alternative(repository, PROJECT, revision, DECISION, "dev_prod")


def test_unknown_decision_and_foreign_project_are_rejected(tmp_path):
    repository, revision = _baseline(tmp_path)
    with pytest.raises(ValueError, match="exactly one instance"):
        impact.compare_alternative(repository, PROJECT, revision, "decision_unknown", "dev_prod")
    with pytest.raises(ValueError, match="project_ref"):
        impact.compare_alternative(repository, "other_project", revision, DECISION, "dev_prod")


def test_fixture_is_synthetic_and_names_no_real_organisation():
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(impact.FIXTURE.iterdir()) if path.is_file())
    assert "synthetic" in text.lower()
    assert "synthetic_fixture_not_a_customer" in text
    for forbidden in ("tenant.onmicrosoft", "@", "http://", "https://"):
        assert forbidden not in text


def test_cli_runs_the_synthetic_reference():
    completed = subprocess.run([sys.executable, "-m", "tooling.superversion.project_package.alternative_impact",
                                "--schemas", str(SCHEMAS)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=300, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    value = json.loads(completed.stdout)["value"]
    assert value["status"] == "impact_ready" and value["baseline_unchanged"]
