from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tooling.superversion.project_package.external_handoff import attach_snapshot, build_snapshot, refresh_handoff_manifest
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "tooling/generator/schemas"


def _write(root: Path, ref: str, content: str) -> str:
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "source"
    ledger_hash = _write(root, "Deliverables/_LEDGER.md", "| E-1 | Approved |\n| **O-2** | Open |\n")
    source_hash = _write(root, "contracts/source.json", '{"sample": true}')
    executable_hash = _write(root, "handoff/deployment/preflight.py", "print('static only')")
    directory_file_hash = _write(root, "legacy/definition/report.json", '{"pages": 1}')
    directory_hash = hashlib.sha256(("report.json" + directory_file_hash).encode("utf-8")).hexdigest()
    package = {
        "schema": "sample/example-executable-package-manifest/v1",
        "files": [{"path": "preflight.py", "sha256": executable_hash, "bytes": 20}],
    }
    package_hash = _write(root, "handoff/deployment/package_manifest.json", json.dumps(package))
    handoff = {
        "schema": "sample/example-handoff-manifest/v1",
        "sources": [
            {"key": "source", "path": "contracts/source.json", "sha256": source_hash},
            {"key": "ledger", "path": "Deliverables/_LEDGER.md", "sha256": ledger_hash},
            {"key": "deployment_package", "path": "handoff/deployment/package_manifest.json", "sha256": package_hash},
            {"key": "pbir", "path": "legacy/definition", "sha256": directory_hash},
        ],
    }
    _write(root, "handoff/manifest.json", json.dumps(handoff))
    descriptor = {
        "schema_version": "1.0.0", "project_ref": "project_demo", "use_case_ref": "uc2_esg",
        "authority_ref": "Deliverables/_LEDGER.md", "handoff_manifest_ref": "handoff/manifest.json",
        "package_manifest_ref": "handoff/deployment/package_manifest.json",
        "required_source_keys": ["source"], "required_package_refs": ["preflight.py"],
        "decision_refs": ["E-1"], "open_gate_refs": ["O-2"],
    }
    _write(root, "handoff/studio_bridge.json", json.dumps(descriptor))
    return root, "handoff/studio_bridge.json"


def test_snapshot_is_metadata_only_and_never_approval(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    result = build_snapshot(root, descriptor)
    assert result["integrity_state"] == "hashes_match"
    assert result["executable_package_file_count"] == 1
    assert result["open_gate_refs"] == ["O-2"]
    assert result["apply_ready"] is result["runtime_proven"] is result["customer_accepted"] is False
    assert "sample" not in json.dumps(result)


def test_source_and_executable_drift_fail_closed(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    _write(root, "contracts/source.json", '{"sample": false}')
    _write(root, "handoff/deployment/preflight.py", "print('changed')")
    result = build_snapshot(root, descriptor)
    assert result["integrity_state"] == "needs_attention"
    assert result["drift"] == ["package:preflight.py", "source:source"]


def test_unknown_manifest_schema_is_rejected(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    manifest = root / "handoff/manifest.json"
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["schema"] = "sample/unrelated/v1"
    _write(root, "handoff/manifest.json", json.dumps(value))
    with pytest.raises(ValueError, match="unsupported external handoff manifest"):
        build_snapshot(root, descriptor)


def test_directory_inventory_detects_changed_pbir_file(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    _write(root, "legacy/definition/report.json", '{"pages": 2}')
    result = build_snapshot(root, descriptor)
    assert result["drift"] == ["handoff_manifest:pbir"]


def test_ledger_drift_is_reported_without_inventing_acceptance(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    _write(root, "Deliverables/_LEDGER.md", "| E-1 | Approved |\n| **O-2** | Open with details |\n")
    result = build_snapshot(root, descriptor)
    assert result["drift"] == ["handoff_manifest:ledger"]
    assert result["customer_accepted"] is False


def test_reviewed_manifest_refresh_is_explicit_and_inventory_only(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    manifest = root / "handoff/manifest.json"
    old_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    _write(root, "Deliverables/_LEDGER.md", "| E-1 | Approved |\n| **O-2** | Open with details |\n")
    with pytest.raises(ValueError, match="drift review mismatch"):
        refresh_handoff_manifest(root, descriptor, expected_manifest_sha256=old_hash, allowed_drift_keys={"index"})
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == old_hash
    assert refresh_handoff_manifest(root, descriptor, expected_manifest_sha256=old_hash, allowed_drift_keys={"ledger"}) == ["ledger"]
    result = build_snapshot(root, descriptor)
    assert result["integrity_state"] == "hashes_match"
    assert result["apply_ready"] is result["customer_accepted"] is False


def test_manifest_refresh_rejects_required_contract_drift(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    old_hash = hashlib.sha256((root / "handoff/manifest.json").read_bytes()).hexdigest()
    _write(root, "contracts/source.json", '{"sample": false}')
    with pytest.raises(ValueError, match="changed required contract"):
        refresh_handoff_manifest(root, descriptor, expected_manifest_sha256=old_hash, allowed_drift_keys={"source"})


def test_rejects_path_escape_and_missing_authority_ref(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    config = json.loads((root / descriptor).read_text(encoding="utf-8"))
    config["authority_ref"] = "../outside.md"
    _write(root, descriptor, json.dumps(config))
    with pytest.raises(ValueError, match="invalid external handoff descriptor"):
        build_snapshot(root, descriptor)
    config["authority_ref"] = "Deliverables/_LEDGER.md"
    config["decision_refs"] = ["E-999"]
    _write(root, descriptor, json.dumps(config))
    with pytest.raises(ValueError, match="missing from authority"):
        build_snapshot(root, descriptor)


def test_attach_is_an_immutable_idempotent_sidecar(tmp_path: Path) -> None:
    root, descriptor = _fixture(tmp_path)
    snapshot = build_snapshot(root, descriptor)
    package = migrate_project_package(ROOT / "tooling/tests/fixtures/project_package/v1", tmp_path / "package", SCHEMAS)
    repo = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    first = repo.commit(package)
    second = attach_snapshot(repo, snapshot)
    assert second.revision == first.revision + 1
    assert second.parent_revision_hash == first.revision_hash
    assert attach_snapshot(repo, snapshot).revision_hash == second.revision_hash
    saved = json.loads((second.package_root / "handoff/uc2_esg.json").read_text(encoding="utf-8"))
    assert saved == snapshot
