from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest
import yaml

from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import (
    ProjectPackageRepositoryError,
    ProjectPackageRevisionRepository,
)


REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "tooling" / "generator" / "schemas"
LEGACY_FIXTURE = REPO / "tooling" / "tests" / "fixtures" / "project_package" / "v1"
ARTIFACT_FIXTURE = (
    REPO / "core" / "fixtures" / "neutral" / "project-package-artifact-lifecycle"
)


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )


def _make_package(root: Path) -> Path:
    migrate_project_package(LEGACY_FIXTURE, root, SCHEMAS)
    notes = root / "notes" / "workshop-context.txt"
    notes.parent.mkdir(parents=True)
    notes.write_text("complete draft context\n", encoding="utf-8", newline="\n")
    return root


def _advance_package(root: Path, parent_revision_hash: str) -> None:
    opportunity_path = root / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"].append("Preserve complete revision history")
    _write_yaml(opportunity_path, opportunity)

    manifest_path = root / "package.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["revision"] = 2
    manifest["parent_revision_hash"] = parent_revision_hash
    next(
        module for module in manifest["modules"] if module["module_type"] == "opportunity"
    )["sha256"] = canonical_sha256(opportunity)
    _write_yaml(manifest_path, manifest)

    decision_log = root / "notes" / "decision-log.yaml"
    _write_yaml(decision_log, {"entries": [{"id": "decision_demo", "state": "proposed"}]})


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_repository_stores_complete_immutable_revisions_and_head_chain(tmp_path: Path) -> None:
    package_v1 = _make_package(tmp_path / "package-v1")
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)

    first = repository.commit(package_v1)
    assert first.revision == 1
    assert first.parent_revision_hash is None
    assert repository.head() == first
    assert (first.package_root / "notes" / "workshop-context.txt").read_text(
        encoding="utf-8"
    ) == "complete draft context\n"

    # A source draft remains mutable; its already stored snapshot does not.
    (package_v1 / "notes" / "workshop-context.txt").write_text(
        "changed outside repository\n", encoding="utf-8"
    )
    repository.verify()
    assert (first.package_root / "notes" / "workshop-context.txt").read_text(
        encoding="utf-8"
    ) == "complete draft context\n"

    package_v2 = repository.checkout(tmp_path / "package-v2", first.revision_hash)
    _advance_package(package_v2, first.revision_hash)
    second = repository.commit(package_v2)

    assert second.revision == 2
    assert second.parent_revision_hash == first.revision_hash
    assert repository.head() == second
    assert repository.get(first.revision_hash) == first
    assert len(list(repository.revisions_root.iterdir())) == 2

    immutable_conflict = repository.checkout(tmp_path / "conflict", second.revision_hash)
    (immutable_conflict / "notes" / "workshop-context.txt").write_text(
        "different revision two bytes\n", encoding="utf-8"
    )
    with pytest.raises(ProjectPackageRepositoryError, match="advance HEAD"):
        repository.commit(immutable_conflict)


def test_repository_returns_structural_diff_for_complete_package_snapshots(
    tmp_path: Path,
) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    first = repository.commit(_make_package(tmp_path / "package-v1"))
    package_v2 = repository.checkout(tmp_path / "package-v2", first.revision_hash)
    _advance_package(package_v2, first.revision_hash)
    second = repository.commit(package_v2)

    difference = repository.diff(first.revision_hash, second.revision_hash)

    assert difference["added_files"] == ["notes/decision-log.yaml"]
    assert difference["removed_files"] == []
    changed = {item["path"]: item for item in difference["changed_files"]}
    assert set(changed) == {"opportunity/opportunity.yaml", "package.yaml"}
    assert changed["opportunity/opportunity.yaml"] == {
        "path": "opportunity/opportunity.yaml",
        "kind": "structured",
        "changes": [
            {
                "op": "add",
                "path": "/objectives/1",
                "after": "Preserve complete revision history",
            }
        ],
    }
    manifest_changes = changed["package.yaml"]["changes"]
    assert any(
        item["op"] == "replace" and item["path"] == "/revision" and item["after"] == 2
        for item in manifest_changes
    )
    assert any(
        item["op"] == "replace"
        and item["path"] == "/parent_revision_hash"
        and item["after"] == first.revision_hash
        for item in manifest_changes
    )


def test_zip_export_reimport_preserves_complete_draft_and_history(tmp_path: Path) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    first = repository.commit(_make_package(tmp_path / "package-v1"))
    package_v2 = repository.checkout(tmp_path / "package-v2", first.revision_hash)
    _advance_package(package_v2, first.revision_hash)
    second = repository.commit(package_v2)

    first_zip = repository.export_zip(tmp_path / "project-package-history.zip")
    second_zip = repository.export_zip(tmp_path / "project-package-history-copy.zip")
    assert first_zip.read_bytes() == second_zip.read_bytes()

    imported = ProjectPackageRevisionRepository.import_zip(
        first_zip,
        tmp_path / "imported-repository",
        SCHEMAS,
    )
    assert imported.head() is not None
    assert imported.head().revision_hash == second.revision_hash
    assert imported.get(first.revision_hash).parent_revision_hash is None
    assert len(list(imported.revisions_root.iterdir())) == 2

    original_checkout = repository.checkout(tmp_path / "original-head", second.revision_hash)
    imported_checkout = imported.checkout(tmp_path / "imported-head", second.revision_hash)
    assert _file_bytes(imported_checkout) == _file_bytes(original_checkout)


def test_zip_import_rejects_zip_slip_without_creating_target(tmp_path: Path) -> None:
    malicious_zip = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious_zip, "w") as archive:
        archive.writestr("../escaped.txt", "must not escape")

    target = tmp_path / "imported-repository"
    with pytest.raises(ProjectPackageRepositoryError, match="unsafe ZIP member"):
        ProjectPackageRevisionRepository.import_zip(malicious_zip, target, SCHEMAS)

    assert not target.exists()
    assert not (tmp_path / "escaped.txt").exists()


def test_repository_fails_closed_on_validator_hash_and_reference_errors(
    tmp_path: Path,
) -> None:
    hash_drift = _make_package(tmp_path / "hash-drift")
    opportunity_path = hash_drift / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"].append("Unrecorded material change")
    _write_yaml(opportunity_path, opportunity)
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    with pytest.raises(ProjectPackageRepositoryError, match="hash drift"):
        repository.commit(hash_drift)

    unresolved_reference = _make_package(tmp_path / "unresolved-reference")
    registry = yaml.safe_load(
        (ARTIFACT_FIXTURE / "artifacts" / "index.yaml").read_text(encoding="utf-8")
    )
    registry_path = unresolved_reference / "artifacts" / "index.yaml"
    _write_yaml(registry_path, registry)
    manifest_path = unresolved_reference / "package.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    registry_schema = json.loads(
        (SCHEMAS / "project_artifact_registry.schema.json").read_text(encoding="utf-8")
    )
    manifest["modules"].append(
        {
            "module_type": "artifact_registry",
            "path": "artifacts/index.yaml",
            "schema_id": registry_schema["$id"],
            "sha256": canonical_sha256(registry),
        }
    )
    _write_yaml(manifest_path, manifest)

    with pytest.raises(ProjectPackageRepositoryError, match="unresolved decision_ref"):
        repository.commit(unresolved_reference)


def test_repository_detects_tampering_before_reload_or_export(tmp_path: Path) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    revision = repository.commit(_make_package(tmp_path / "package-v1"))
    opportunity_path = revision.package_root / "opportunity" / "opportunity.yaml"
    opportunity_path.write_text(
        opportunity_path.read_text(encoding="utf-8") + "# tampered\n",
        encoding="utf-8",
    )

    with pytest.raises(ProjectPackageRepositoryError, match="hash"):
        repository.get()
    with pytest.raises(ProjectPackageRepositoryError, match="hash"):
        repository.export_zip(tmp_path / "must-not-export.zip")
    assert not (tmp_path / "must-not-export.zip").exists()
