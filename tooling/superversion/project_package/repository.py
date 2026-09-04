"""Immutable, content-addressed history for Project Package 2.0 directories.

The repository stores exact package-directory snapshots. It deliberately does not
interpret or merge decisions: ``validate_project_package`` remains the package
authority, while this module only adds persistence, history and transport
integrity.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import time
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

import yaml

from .hashes import canonical_sha256
from .validator import validate_project_package


_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DEFAULT_MAX_ZIP_MEMBERS = 10_000
DEFAULT_MAX_ZIP_MEMBER_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_ZIP_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_MAX_ZIP_COMPRESSION_RATIO = 200.0
_LOCK_TIMEOUT_SECONDS = 10.0
_METADATA_KEYS = {
    "format_version",
    "package_id",
    "parent_revision_hash",
    "project_ref",
    "revision",
    "revision_hash",
    "tree",
}


class ProjectPackageRepositoryError(ValueError):
    """Raised when a package revision cannot be stored or proven safely."""


class StaleProjectPackageDraftError(ProjectPackageRepositoryError):
    """Raised when optimistic concurrency detects a stale draft HEAD."""


class ProjectPackageRepositoryBusyError(ProjectPackageRepositoryError):
    """Raised when another process holds the repository lock too long."""


@contextmanager
def _repository_lock(repository_root: Path) -> Iterator[None]:
    """Hold a cross-process exclusive lock for one repository root."""
    lock_path = repository_root.parent / f".{repository_root.name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.is_symlink():
        raise ProjectPackageRepositoryError(f"repository lock path is a symbolic link: {lock_path}")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    handle = os.fdopen(descriptor, "r+b", buffering=0)
    acquired = False
    try:
        if lock_path.stat().st_size == 0:
            handle.write(b"\0")
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        while not acquired:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise ProjectPackageRepositoryBusyError(
                        f"repository lock timeout: {repository_root}"
                    ) from exc
                time.sleep(0.05)
        yield
    finally:
        if acquired:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


@dataclass(frozen=True)
class RevisionRecord:
    """Verified identity and location of one immutable package snapshot."""

    revision_hash: str
    package_id: str
    project_ref: str
    revision: int
    parent_revision_hash: str | None
    package_root: Path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(root: Path) -> list[dict[str, Any]]:
    """Return a deterministic raw-file inventory and reject link/special-file input."""
    resolved_root = root.resolve()
    if not root.is_dir() or root.is_symlink():
        raise ProjectPackageRepositoryError(f"package root must be a real directory: {root}")

    entries: list[dict[str, Any]] = []
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directory_names:
            candidate = current_path / name
            if candidate.is_symlink():
                raise ProjectPackageRepositoryError(
                    f"package directory contains a symbolic link: {candidate.relative_to(root).as_posix()}"
                )
        for name in file_names:
            candidate = current_path / name
            if candidate.is_symlink() or not candidate.is_file():
                raise ProjectPackageRepositoryError(
                    f"package directory contains a non-regular file: {candidate.relative_to(root).as_posix()}"
                )
            resolved = candidate.resolve()
            try:
                relative = resolved.relative_to(resolved_root).as_posix()
            except ValueError as exc:
                raise ProjectPackageRepositoryError(
                    f"package file escapes package root: {candidate}"
                ) from exc
            entries.append(
                {
                    "path": relative,
                    "sha256": _file_sha256(candidate),
                    "size": candidate.stat().st_size,
                }
            )
    return sorted(entries, key=lambda item: item["path"])


def _tree_hash(tree: list[dict[str, Any]]) -> str:
    return canonical_sha256({"tree": tree})


def _load_manifest(package_root: Path) -> dict[str, Any]:
    manifest_path = package_root / "package.yaml"
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ProjectPackageRepositoryError(f"cannot read package manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ProjectPackageRepositoryError("package manifest must be an object")
    return manifest


def _write_manifest(package_root: Path, manifest: dict[str, Any]) -> None:
    (package_root / "package.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )


def _load_module_document(package_root: Path, relative_value: Any) -> Any:
    if not isinstance(relative_value, str) or not relative_value:
        raise ProjectPackageRepositoryError("package module path must be a non-empty string")
    relative = Path(relative_value)
    if relative.is_absolute():
        raise ProjectPackageRepositoryError(f"package module path must be relative: {relative_value!r}")
    module_path = (package_root / relative).resolve()
    try:
        module_path.relative_to(package_root.resolve())
    except ValueError as exc:
        raise ProjectPackageRepositoryError(
            f"package module path escapes package root: {relative_value!r}"
        ) from exc
    if not module_path.is_file() or module_path.is_symlink():
        raise ProjectPackageRepositoryError(f"package module is not a regular file: {relative_value!r}")
    try:
        text = module_path.read_text(encoding="utf-8")
        return json.loads(text) if module_path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ProjectPackageRepositoryError(
            f"cannot parse package module {relative_value!r}: {exc}"
        ) from exc


def _validate_package(package_root: Path, schema_root: Path) -> dict[str, Any]:
    try:
        errors = validate_project_package(package_root, schema_root)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        yaml.YAMLError,
        TypeError,
        AttributeError,
        KeyError,
    ) as exc:
        raise ProjectPackageRepositoryError(f"package validation could not complete: {exc}") from exc
    if errors:
        raise ProjectPackageRepositoryError(
            "package validation failed: " + "; ".join(errors)
        )
    return _load_manifest(package_root)


def _copy_inventory(source_root: Path, target_root: Path, tree: list[dict[str, Any]]) -> None:
    for entry in tree:
        source = source_root / Path(entry["path"])
        target = target_root / Path(entry["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if _inventory(target_root) != tree:
        raise ProjectPackageRepositoryError("package changed while its revision was being stored")


def _replace_directory(source: Path, target: Path) -> None:
    """Atomically move a directory, tolerating short-lived Windows file locks."""
    for attempt in range(5):
        try:
            source.replace(target)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.02 * (attempt + 1))


def _reject_overlapping_roots(package_root: Path, repository_root: Path) -> None:
    package_resolved = package_root.resolve()
    repository_resolved = repository_root.resolve()
    if (
        repository_resolved == package_resolved
        or repository_resolved in package_resolved.parents
        or package_resolved in repository_resolved.parents
    ):
        raise ProjectPackageRepositoryError("package root and repository must not overlap")


def _json_pointer_segment(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _structural_changes(before: Any, after: Any, pointer: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"op": "replace", "path": pointer or "/", "before": before, "after": after}]
    if isinstance(before, dict):
        changes: list[dict[str, Any]] = []
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(before_keys - after_keys, key=str):
            path = f"{pointer}/{_json_pointer_segment(key)}"
            changes.append({"op": "remove", "path": path, "before": before[key]})
        for key in sorted(after_keys - before_keys, key=str):
            path = f"{pointer}/{_json_pointer_segment(key)}"
            changes.append({"op": "add", "path": path, "after": after[key]})
        for key in sorted(before_keys & after_keys, key=str):
            path = f"{pointer}/{_json_pointer_segment(key)}"
            changes.extend(_structural_changes(before[key], after[key], path))
        return changes
    if isinstance(before, list):
        changes = []
        common_length = min(len(before), len(after))
        for index in range(common_length):
            changes.extend(_structural_changes(before[index], after[index], f"{pointer}/{index}"))
        for index in range(len(before) - 1, common_length - 1, -1):
            changes.append({"op": "remove", "path": f"{pointer}/{index}", "before": before[index]})
        for index in range(common_length, len(after)):
            changes.append({"op": "add", "path": f"{pointer}/{index}", "after": after[index]})
        return changes
    if before != after:
        return [{"op": "replace", "path": pointer or "/", "before": before, "after": after}]
    return []


def _structured_document(path: Path) -> Any | None:
    try:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError):
        return None
    return None


class ProjectPackageRevisionRepository:
    """A linear, immutable repository of complete Project Package snapshots."""

    def __init__(self, root: Path, schema_root: Path) -> None:
        self.root = Path(root)
        self.schema_root = Path(schema_root)

    @property
    def revisions_root(self) -> Path:
        return self.root / "revisions"

    @property
    def head_path(self) -> Path:
        return self.root / "HEAD"

    def _read_head_file(self) -> str | None:
        if not self.head_path.exists():
            return None
        if not self.head_path.is_file() or self.head_path.is_symlink():
            raise ProjectPackageRepositoryError("repository HEAD is not a regular file")
        value = self.head_path.read_text(encoding="ascii").strip()
        if not _HASH_PATTERN.fullmatch(value):
            raise ProjectPackageRepositoryError("repository HEAD is not a revision hash")
        return value

    def _head_hash(self) -> str | None:
        value = self._read_head_file()
        if value is None and self.revisions_root.exists() and any(self.revisions_root.iterdir()):
            raise ProjectPackageRepositoryError("repository has revisions but no HEAD")
        return value

    def _read_record(self, revision_hash: str) -> RevisionRecord:
        if not _HASH_PATTERN.fullmatch(revision_hash):
            raise ProjectPackageRepositoryError(f"invalid revision hash: {revision_hash!r}")
        revision_root = self.revisions_root / revision_hash
        metadata_path = revision_root / "metadata.json"
        package_root = revision_root / "package"
        if revision_root.is_symlink() or metadata_path.is_symlink() or package_root.is_symlink():
            raise ProjectPackageRepositoryError(f"revision {revision_hash} contains a symbolic link")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ProjectPackageRepositoryError(
                f"cannot read metadata for revision {revision_hash}: {exc}"
            ) from exc
        if not isinstance(metadata, dict) or set(metadata) != _METADATA_KEYS:
            raise ProjectPackageRepositoryError(f"invalid metadata contract for revision {revision_hash}")

        manifest = _validate_package(package_root, self.schema_root)
        tree = _inventory(package_root)
        actual_hash = _tree_hash(tree)
        expected = {
            "format_version": "1.0.0",
            "package_id": manifest["package_id"],
            "parent_revision_hash": manifest["parent_revision_hash"],
            "project_ref": manifest["project_ref"],
            "revision": manifest["revision"],
            "revision_hash": actual_hash,
            "tree": tree,
        }
        if revision_hash != actual_hash:
            raise ProjectPackageRepositoryError(
                f"revision directory hash mismatch: expected {revision_hash}, actual {actual_hash}"
            )
        if metadata != expected:
            raise ProjectPackageRepositoryError(f"metadata drift for revision {revision_hash}")
        return RevisionRecord(
            revision_hash=revision_hash,
            package_id=manifest["package_id"],
            project_ref=manifest["project_ref"],
            revision=manifest["revision"],
            parent_revision_hash=manifest["parent_revision_hash"],
            package_root=package_root,
        )

    def _verify_unlocked(self) -> None:
        """Verify every stored byte, package contract and HEAD-reachable parent link."""
        if not self.root.is_dir() or self.root.is_symlink():
            raise ProjectPackageRepositoryError(f"repository does not exist: {self.root}")
        head_hash = self._head_hash()
        if head_hash is None:
            raise ProjectPackageRepositoryError("repository has no revisions")
        if not self.revisions_root.is_dir() or self.revisions_root.is_symlink():
            raise ProjectPackageRepositoryError("repository revisions path is not a real directory")

        unexpected = sorted(path.name for path in self.root.iterdir() if path.name not in {"HEAD", "revisions"})
        if unexpected:
            raise ProjectPackageRepositoryError(
                "repository contains unexpected top-level entries: " + ", ".join(unexpected)
            )

        revision_hashes: list[str] = []
        for path in self.revisions_root.iterdir():
            if not path.is_dir() or path.is_symlink() or not _HASH_PATTERN.fullmatch(path.name):
                raise ProjectPackageRepositoryError(f"invalid revision entry: {path.name}")
            child_names = {child.name for child in path.iterdir()}
            if child_names != {"metadata.json", "package"}:
                raise ProjectPackageRepositoryError(f"unexpected content in revision {path.name}")
            revision_hashes.append(path.name)

        records = {revision_hash: self._read_record(revision_hash) for revision_hash in sorted(revision_hashes)}
        if head_hash not in records:
            raise ProjectPackageRepositoryError(f"HEAD references missing revision {head_hash}")

        seen: set[str] = set()
        current = records[head_hash]
        package_id = current.package_id
        project_ref = current.project_ref
        while True:
            if current.revision_hash in seen:
                raise ProjectPackageRepositoryError("revision parent chain contains a cycle")
            seen.add(current.revision_hash)
            if current.package_id != package_id or current.project_ref != project_ref:
                raise ProjectPackageRepositoryError("revision chain changes package or project identity")
            if current.revision == 1:
                if current.parent_revision_hash is not None:
                    raise ProjectPackageRepositoryError("revision 1 must terminate the parent chain")
                break
            parent_hash = current.parent_revision_hash
            if parent_hash not in records:
                raise ProjectPackageRepositoryError(
                    f"revision {current.revision_hash} references missing parent {parent_hash}"
                )
            parent = records[parent_hash]
            if parent.revision != current.revision - 1:
                raise ProjectPackageRepositoryError("revision numbers are not contiguous along the parent chain")
            current = parent
        if seen != set(records):
            raise ProjectPackageRepositoryError("repository contains revisions not reachable from HEAD")

    def verify(self) -> None:
        """Verify the complete repository under a cross-process lock."""
        with _repository_lock(self.root):
            self._verify_unlocked()

    def _head_unlocked(self) -> RevisionRecord | None:
        head_hash = self._head_hash()
        if head_hash is None:
            return None
        self._verify_unlocked()
        return self._read_record(head_hash)

    def head(self) -> RevisionRecord | None:
        """Return the verified HEAD revision, or ``None`` for an uninitialised repository."""
        with _repository_lock(self.root):
            return self._head_unlocked()

    def _get_unlocked(self, revision_hash: str | None = None) -> RevisionRecord:
        self._verify_unlocked()
        selected = revision_hash or self._head_hash()
        assert selected is not None
        return self._read_record(selected)

    def get(self, revision_hash: str | None = None) -> RevisionRecord:
        """Return a verified revision, defaulting to HEAD."""
        with _repository_lock(self.root):
            return self._get_unlocked(revision_hash)

    def _commit_unlocked(self, package_root: Path) -> RevisionRecord:
        package_root = Path(package_root)
        manifest = _validate_package(package_root, self.schema_root)
        tree = _inventory(package_root)
        revision_hash = _tree_hash(tree)

        current_head = self._head_unlocked()
        if current_head is None:
            if manifest["revision"] != 1 or manifest["parent_revision_hash"] is not None:
                raise ProjectPackageRepositoryError("first stored package must be revision 1 without a parent")
        else:
            if revision_hash == current_head.revision_hash:
                return current_head
            if manifest["package_id"] != current_head.package_id or manifest["project_ref"] != current_head.project_ref:
                raise ProjectPackageRepositoryError("new revision changes package or project identity")
            if manifest["revision"] != current_head.revision + 1:
                raise ProjectPackageRepositoryError("new revision number must advance HEAD by exactly one")
            if manifest["parent_revision_hash"] != current_head.revision_hash:
                raise ProjectPackageRepositoryError("new revision parent_revision_hash must reference HEAD")

        _reject_overlapping_roots(package_root, self.root)

        self.revisions_root.mkdir(parents=True, exist_ok=True)
        destination = self.revisions_root / revision_hash
        if destination.exists():
            raise ProjectPackageRepositoryError(f"revision already exists outside HEAD: {revision_hash}")
        staging = Path(tempfile.mkdtemp(prefix=".revision-", dir=self.revisions_root))
        try:
            staged_package = staging / "package"
            staged_package.mkdir()
            _copy_inventory(package_root, staged_package, tree)
            metadata = {
                "format_version": "1.0.0",
                "package_id": manifest["package_id"],
                "parent_revision_hash": manifest["parent_revision_hash"],
                "project_ref": manifest["project_ref"],
                "revision": manifest["revision"],
                "revision_hash": revision_hash,
                "tree": tree,
            }
            (staging / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            if self._read_head_file() != (current_head.revision_hash if current_head else None):
                raise ProjectPackageRepositoryError("repository HEAD changed during commit")
            _replace_directory(staging, destination)
            descriptor, temporary_name = tempfile.mkstemp(prefix=".HEAD-", dir=self.root)
            os.close(descriptor)
            temporary_head = Path(temporary_name)
            temporary_head.write_text(revision_hash + "\n", encoding="ascii", newline="\n")
            temporary_head.replace(self.head_path)
        finally:
            if staging.exists():
                shutil.rmtree(staging)

        self._verify_unlocked()
        return self._read_record(revision_hash)

    def commit(self, package_root: Path) -> RevisionRecord:
        """Append an exact valid package snapshot without altering package content."""
        with _repository_lock(self.root):
            return self._commit_unlocked(package_root)

    def _commit_draft_unlocked(
        self,
        package_root: Path,
        expected_head_hash: str | None,
    ) -> RevisionRecord:
        """Commit a draft after deriving only its technical revision metadata.

        The caller-owned directory is copied first. Only ``revision``,
        ``parent_revision_hash`` and the hashes of already declared modules are
        updated in that temporary copy. The normal package validator and immutable
        commit path then remain the sole acceptance gates.
        """
        package_root = Path(package_root)
        _reject_overlapping_roots(package_root, self.root)
        source_tree = _inventory(package_root)
        current_head = self._head_unlocked()
        if expected_head_hash is not None and not _HASH_PATTERN.fullmatch(expected_head_hash):
            raise ProjectPackageRepositoryError(
                f"expected_head_hash is not a revision hash: {expected_head_hash!r}"
            )
        actual_head_hash = current_head.revision_hash if current_head else None
        if expected_head_hash != actual_head_hash:
            raise StaleProjectPackageDraftError(
                "stale draft: expected repository HEAD "
                f"{expected_head_hash!r}, actual HEAD is {actual_head_hash!r}"
            )

        with tempfile.TemporaryDirectory(prefix="project-package-draft-") as temporary:
            staged_package = Path(temporary) / "package"
            staged_package.mkdir()
            _copy_inventory(package_root, staged_package, source_tree)

            manifest = _load_manifest(staged_package)
            modules = manifest.get("modules")
            if not isinstance(modules, list):
                raise ProjectPackageRepositoryError("package manifest modules must be an array")
            manifest["revision"] = current_head.revision + 1 if current_head else 1
            manifest["parent_revision_hash"] = (
                current_head.revision_hash if current_head else None
            )
            for module in modules:
                if not isinstance(module, dict):
                    raise ProjectPackageRepositoryError("package manifest module must be an object")
                document = _load_module_document(staged_package, module.get("path"))
                module["sha256"] = canonical_sha256(document)
            _write_manifest(staged_package, manifest)

            # Validate the fully derived snapshot before the immutable commit. The
            # commit repeats validation and proves that HEAD has not changed.
            _validate_package(staged_package, self.schema_root)
            return self._commit_unlocked(staged_package)

    def commit_draft(
        self,
        package_root: Path,
        *,
        expected_head_hash: str | None,
    ) -> RevisionRecord:
        """Derive technical metadata and commit when the caller's HEAD is current."""
        with _repository_lock(self.root):
            return self._commit_draft_unlocked(package_root, expected_head_hash)

    def _checkout_unlocked(self, target_root: Path, revision_hash: str | None = None) -> Path:
        target_root = Path(target_root)
        if target_root.exists():
            raise ProjectPackageRepositoryError(f"checkout target already exists: {target_root}")
        record = self._get_unlocked(revision_hash)
        target_root.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target_root.name}-", dir=target_root.parent))
        try:
            tree = _inventory(record.package_root)
            _copy_inventory(record.package_root, staging, tree)
            _validate_package(staging, self.schema_root)
            _replace_directory(staging, target_root)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return target_root

    def checkout(self, target_root: Path, revision_hash: str | None = None) -> Path:
        """Restore one complete revision into a new directory."""
        with _repository_lock(self.root):
            return self._checkout_unlocked(target_root, revision_hash)

    def _diff_unlocked(self, before_hash: str, after_hash: str) -> dict[str, Any]:
        before = self._get_unlocked(before_hash)
        after = self._get_unlocked(after_hash)
        before_tree = {item["path"]: item for item in _inventory(before.package_root)}
        after_tree = {item["path"]: item for item in _inventory(after.package_root)}
        before_paths = set(before_tree)
        after_paths = set(after_tree)
        changed_files: list[dict[str, Any]] = []
        for relative in sorted(before_paths & after_paths):
            if before_tree[relative]["sha256"] == after_tree[relative]["sha256"]:
                continue
            before_path = before.package_root / Path(relative)
            after_path = after.package_root / Path(relative)
            before_document = _structured_document(before_path)
            after_document = _structured_document(after_path)
            if before_document is not None and after_document is not None:
                changed_files.append(
                    {
                        "path": relative,
                        "kind": "structured",
                        "changes": _structural_changes(before_document, after_document),
                    }
                )
            else:
                changed_files.append(
                    {
                        "path": relative,
                        "kind": "opaque",
                        "before_sha256": before_tree[relative]["sha256"],
                        "after_sha256": after_tree[relative]["sha256"],
                    }
                )
        return {
            "from_revision_hash": before_hash,
            "to_revision_hash": after_hash,
            "added_files": sorted(after_paths - before_paths),
            "removed_files": sorted(before_paths - after_paths),
            "changed_files": changed_files,
        }

    def diff(self, before_hash: str, after_hash: str) -> dict[str, Any]:
        """Return a deterministic file and JSON/YAML structural diff."""
        with _repository_lock(self.root):
            return self._diff_unlocked(before_hash, after_hash)

    def _export_zip_unlocked(self, target_zip: Path) -> Path:
        self._verify_unlocked()
        target_zip = Path(target_zip)
        if target_zip.exists():
            raise ProjectPackageRepositoryError(f"ZIP target already exists: {target_zip}")
        target_resolved = target_zip.resolve()
        repository_resolved = self.root.resolve()
        if target_resolved == repository_resolved or repository_resolved in target_resolved.parents:
            raise ProjectPackageRepositoryError("ZIP target must be outside the repository")
        target_zip.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target_zip.name}-",
            suffix=".tmp",
            dir=target_zip.parent,
        )
        os.close(descriptor)
        temporary_zip = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(
                    (candidate for candidate in self.root.rglob("*") if candidate.is_file()),
                    key=lambda candidate: candidate.relative_to(self.root).as_posix(),
                ):
                    if path.is_symlink():
                        raise ProjectPackageRepositoryError("repository contains a symbolic link")
                    relative = path.relative_to(self.root).as_posix()
                    info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, path.read_bytes())
            temporary_zip.replace(target_zip)
        finally:
            if temporary_zip.exists():
                temporary_zip.unlink()
        return target_zip

    def export_zip(self, target_zip: Path) -> Path:
        """Export the complete verified repository as a deterministic ZIP archive."""
        with _repository_lock(self.root):
            return self._export_zip_unlocked(target_zip)

    @classmethod
    def _import_zip_unlocked(
        cls,
        source_zip: Path,
        target_root: Path,
        schema_root: Path,
        *,
        max_members: int,
        max_member_bytes: int,
        max_total_bytes: int,
        max_compression_ratio: float,
    ) -> ProjectPackageRevisionRepository:
        source_zip = Path(source_zip)
        target_root = Path(target_root)
        if target_root.exists():
            raise ProjectPackageRepositoryError(f"import target already exists: {target_root}")
        target_root.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target_root.name}-", dir=target_root.parent))
        try:
            try:
                archive = zipfile.ZipFile(source_zip, "r")
            except (OSError, zipfile.BadZipFile) as exc:
                raise ProjectPackageRepositoryError(f"cannot open repository ZIP: {exc}") from exc
            with archive:
                members = archive.infolist()
                if len(members) > max_members:
                    raise ProjectPackageRepositoryError(
                        f"repository ZIP exceeds member limit: {len(members)} > {max_members}"
                    )
                total_bytes = sum(member.file_size for member in members)
                if total_bytes > max_total_bytes:
                    raise ProjectPackageRepositoryError(
                        "repository ZIP exceeds total uncompressed size limit: "
                        f"{total_bytes} > {max_total_bytes}"
                    )
                seen: dict[str, str] = {}
                for member in members:
                    if member.file_size > max_member_bytes:
                        raise ProjectPackageRepositoryError(
                            "repository ZIP member exceeds uncompressed size limit: "
                            f"{member.filename!r} has {member.file_size} bytes, limit is {max_member_bytes}"
                        )
                    if member.flag_bits & 0x1:
                        raise ProjectPackageRepositoryError(
                            f"encrypted ZIP member is not supported: {member.filename!r}"
                        )
                    compression_ratio = (
                        member.file_size / member.compress_size
                        if member.compress_size
                        else (0.0 if member.file_size == 0 else float("inf"))
                    )
                    if compression_ratio > max_compression_ratio:
                        raise ProjectPackageRepositoryError(
                            "repository ZIP member exceeds compression ratio limit: "
                            f"{member.filename!r} has {compression_ratio:.2f}, "
                            f"limit is {max_compression_ratio:.2f}"
                        )
                    normalized = member.filename.replace("\\", "/")
                    relative = PurePosixPath(normalized)
                    mode = (member.external_attr >> 16) & 0o170000
                    if (
                        not normalized
                        or relative.is_absolute()
                        or ".." in relative.parts
                        or any(":" in part or "\x00" in part for part in relative.parts)
                        or mode == stat.S_IFLNK
                    ):
                        raise ProjectPackageRepositoryError(
                            f"unsafe ZIP member path or type: {member.filename!r}"
                        )
                    key = relative.as_posix()
                    collision_key = key.casefold()
                    if collision_key in seen:
                        raise ProjectPackageRepositoryError(
                            f"duplicate or case-colliding ZIP member: {seen[collision_key]!r} and {key!r}"
                        )
                    seen[collision_key] = key
                    destination = staging.joinpath(*relative.parts)
                    try:
                        destination.resolve().relative_to(staging.resolve())
                    except ValueError as exc:
                        raise ProjectPackageRepositoryError(
                            f"ZIP member escapes import root: {member.filename!r}"
                        ) from exc
                    if member.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member, "r") as source, destination.open("xb") as target:
                        shutil.copyfileobj(source, target)

            imported = cls(staging, schema_root)
            imported._verify_unlocked()
            _replace_directory(staging, target_root)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        result = cls(target_root, schema_root)
        result._verify_unlocked()
        return result

    @classmethod
    def import_zip(
        cls,
        source_zip: Path,
        target_root: Path,
        schema_root: Path,
        *,
        max_members: int = DEFAULT_MAX_ZIP_MEMBERS,
        max_member_bytes: int = DEFAULT_MAX_ZIP_MEMBER_BYTES,
        max_total_bytes: int = DEFAULT_MAX_ZIP_TOTAL_BYTES,
        max_compression_ratio: float = DEFAULT_MAX_ZIP_COMPRESSION_RATIO,
    ) -> ProjectPackageRevisionRepository:
        """Safely import and fully verify an exported repository archive."""
        limits = {
            "max_members": max_members,
            "max_member_bytes": max_member_bytes,
            "max_total_bytes": max_total_bytes,
        }
        invalid = [name for name, value in limits.items() if not isinstance(value, int) or value < 1]
        if invalid:
            raise ProjectPackageRepositoryError(
                "repository ZIP limits must be positive integers: " + ", ".join(invalid)
            )
        if not isinstance(max_compression_ratio, (int, float)) or max_compression_ratio <= 0:
            raise ProjectPackageRepositoryError(
                "repository ZIP max_compression_ratio must be a positive number"
            )
        target_root = Path(target_root)
        with _repository_lock(target_root):
            return cls._import_zip_unlocked(
                source_zip,
                target_root,
                schema_root,
                max_members=max_members,
                max_member_bytes=max_member_bytes,
                max_total_bytes=max_total_bytes,
                max_compression_ratio=float(max_compression_ratio),
            )
