from __future__ import annotations

import json
import multiprocessing
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
    StaleProjectPackageDraftError,
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


def _commit_draft_worker(
    repository_root: str,
    schema_root: str,
    package_root: str,
    expected_head_hash: str,
    start_event,
    result_queue,
) -> None:
    start_event.wait()
    repository = ProjectPackageRevisionRepository(Path(repository_root), Path(schema_root))
    try:
        revision = repository.commit_draft(
            Path(package_root),
            expected_head_hash=expected_head_hash,
        )
        result_queue.put(("committed", revision.revision_hash))
    except StaleProjectPackageDraftError as exc:
        result_queue.put(("stale", str(exc)))


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


def test_commit_draft_derives_v1_v2_metadata_without_mutating_input(tmp_path: Path) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    draft_v1 = _make_package(tmp_path / "draft-v1")
    opportunity_path = draft_v1 / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"].append("Save without manual module hash maintenance")
    _write_yaml(opportunity_path, opportunity)
    input_v1 = _file_bytes(draft_v1)

    first = repository.commit_draft(draft_v1, expected_head_hash=None)

    assert _file_bytes(draft_v1) == input_v1
    stored_v1_manifest = yaml.safe_load(
        (first.package_root / "package.yaml").read_text(encoding="utf-8")
    )
    assert stored_v1_manifest["revision"] == 1
    assert stored_v1_manifest["parent_revision_hash"] is None
    stored_v1_opportunity = yaml.safe_load(
        (first.package_root / "opportunity" / "opportunity.yaml").read_text(encoding="utf-8")
    )
    opportunity_module = next(
        module
        for module in stored_v1_manifest["modules"]
        if module["module_type"] == "opportunity"
    )
    assert opportunity_module["sha256"] == canonical_sha256(stored_v1_opportunity)

    draft_v2 = tmp_path / "draft-v2"
    shutil.copytree(draft_v1, draft_v2)
    opportunity_path = draft_v2 / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"].append("Append a second immutable revision")
    _write_yaml(opportunity_path, opportunity)
    input_v2 = _file_bytes(draft_v2)

    second = repository.commit_draft(draft_v2, expected_head_hash=first.revision_hash)

    assert _file_bytes(draft_v2) == input_v2
    assert second.revision == 2
    assert second.parent_revision_hash == first.revision_hash
    assert repository.head() == second


def test_commit_draft_remains_fail_closed_for_schema_and_reference_errors(
    tmp_path: Path,
) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    invalid_schema = _make_package(tmp_path / "invalid-schema")
    opportunity_path = invalid_schema / "opportunity" / "opportunity.yaml"
    opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
    opportunity["objectives"] = []
    _write_yaml(opportunity_path, opportunity)
    schema_input = _file_bytes(invalid_schema)

    with pytest.raises(ProjectPackageRepositoryError, match="opportunity.yaml"):
        repository.commit_draft(invalid_schema, expected_head_hash=None)
    assert _file_bytes(invalid_schema) == schema_input
    assert repository.head() is None

    invalid_reference = _make_package(tmp_path / "invalid-reference")
    registry = yaml.safe_load(
        (ARTIFACT_FIXTURE / "artifacts" / "index.yaml").read_text(encoding="utf-8")
    )
    _write_yaml(invalid_reference / "artifacts" / "index.yaml", registry)
    manifest_path = invalid_reference / "package.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    registry_schema = json.loads(
        (SCHEMAS / "project_artifact_registry.schema.json").read_text(encoding="utf-8")
    )
    manifest["modules"].append(
        {
            "module_type": "artifact_registry",
            "path": "artifacts/index.yaml",
            "schema_id": registry_schema["$id"],
            "sha256": "0" * 64,
        }
    )
    _write_yaml(manifest_path, manifest)
    reference_input = _file_bytes(invalid_reference)

    with pytest.raises(ProjectPackageRepositoryError, match="unresolved decision_ref"):
        repository.commit_draft(invalid_reference, expected_head_hash=None)
    assert _file_bytes(invalid_reference) == reference_input
    assert repository.head() is None


def test_commit_draft_rejects_stale_expected_head_without_orphan_revision(
    tmp_path: Path,
) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    first = repository.commit_draft(
        _make_package(tmp_path / "draft-v1"),
        expected_head_hash=None,
    )
    draft_v2 = repository.checkout(tmp_path / "draft-v2", first.revision_hash)

    with pytest.raises(StaleProjectPackageDraftError, match="stale draft"):
        repository.commit_draft(draft_v2, expected_head_hash=None)

    assert repository.head() == first
    assert [path.name for path in repository.revisions_root.iterdir()] == [
        first.revision_hash
    ]


def test_cross_process_writers_produce_one_revision_and_one_stale_result(
    tmp_path: Path,
) -> None:
    repository = ProjectPackageRevisionRepository(tmp_path / "repository", SCHEMAS)
    first = repository.commit_draft(
        _make_package(tmp_path / "draft-v1"),
        expected_head_hash=None,
    )
    drafts = []
    for index in (1, 2):
        draft = repository.checkout(tmp_path / f"draft-v2-{index}", first.revision_hash)
        opportunity_path = draft / "opportunity" / "opportunity.yaml"
        opportunity = yaml.safe_load(opportunity_path.read_text(encoding="utf-8"))
        opportunity["objectives"].append(f"Concurrent candidate {index}")
        _write_yaml(opportunity_path, opportunity)
        drafts.append(draft)

    context = multiprocessing.get_context("spawn")
    start_event = context.Event()
    result_queue = context.Queue()
    processes = [
        context.Process(
            target=_commit_draft_worker,
            args=(
                str(repository.root),
                str(SCHEMAS),
                str(draft),
                first.revision_hash,
                start_event,
                result_queue,
            ),
        )
        for draft in drafts
    ]
    for process in processes:
        process.start()
    start_event.set()
    results = [result_queue.get(timeout=60) for _ in processes]
    for process in processes:
        process.join(timeout=60)
        assert process.exitcode == 0

    assert sorted(result[0] for result in results) == ["committed", "stale"]
    repository.verify()
    assert repository.head().revision == 2
    assert len(list(repository.revisions_root.iterdir())) == 2
    assert not list(repository.revisions_root.glob(".revision-*"))


def test_zip_import_enforces_pre_extraction_limits(tmp_path: Path) -> None:
    member_limited = tmp_path / "member-limited.zip"
    with zipfile.ZipFile(member_limited, "w") as archive:
        archive.writestr("one", "1")
        archive.writestr("two", "2")
    with pytest.raises(ProjectPackageRepositoryError, match="member limit"):
        ProjectPackageRevisionRepository.import_zip(
            member_limited,
            tmp_path / "member-target",
            SCHEMAS,
            max_members=1,
        )

    file_limited = tmp_path / "file-limited.zip"
    with zipfile.ZipFile(file_limited, "w") as archive:
        archive.writestr("large", "12345")
    with pytest.raises(ProjectPackageRepositoryError, match="uncompressed size limit"):
        ProjectPackageRevisionRepository.import_zip(
            file_limited,
            tmp_path / "file-target",
            SCHEMAS,
            max_member_bytes=4,
        )

    total_limited = tmp_path / "total-limited.zip"
    with zipfile.ZipFile(total_limited, "w") as archive:
        archive.writestr("one", "123")
        archive.writestr("two", "456")
    with pytest.raises(ProjectPackageRepositoryError, match="total uncompressed"):
        ProjectPackageRevisionRepository.import_zip(
            total_limited,
            tmp_path / "total-target",
            SCHEMAS,
            max_total_bytes=5,
        )

    assert not (tmp_path / "member-target").exists()
    assert not (tmp_path / "file-target").exists()
    assert not (tmp_path / "total-target").exists()


def test_zip_import_rejects_case_collisions_and_excessive_compression_ratio(
    tmp_path: Path,
) -> None:
    colliding = tmp_path / "case-collision.zip"
    with zipfile.ZipFile(colliding, "w") as archive:
        archive.writestr("HEAD", "one")
        archive.writestr("head", "two")
    with pytest.raises(ProjectPackageRepositoryError, match="case-colliding"):
        ProjectPackageRevisionRepository.import_zip(
            colliding,
            tmp_path / "collision-target",
            SCHEMAS,
        )

    compressed = tmp_path / "compression-ratio.zip"
    with zipfile.ZipFile(compressed, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("repetitive", "0" * 10_000)
    with pytest.raises(ProjectPackageRepositoryError, match="compression ratio"):
        ProjectPackageRevisionRepository.import_zip(
            compressed,
            tmp_path / "compression-target",
            SCHEMAS,
            max_compression_ratio=2,
        )

    assert not (tmp_path / "collision-target").exists()
    assert not (tmp_path / "compression-target").exists()
