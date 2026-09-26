"""Content-addressed, evidence-only bridge for an external delivery handoff.

The bridge records what was inspected. It never imports source payloads, changes
decisions, or turns a static package check into runtime/acceptance evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from .repository import ProjectPackageRevisionRepository, RevisionRecord


SCHEMA_VERSION = "1.0.0"
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def _file(root: Path, ref: str) -> Path:
    path = _path(root, ref)
    if not path.is_file():
        raise ValueError(f"handoff path is not a file: {ref}")
    return path


def _path(root: Path, ref: str) -> Path:
    if not isinstance(ref, str) or not ref or "\\" in ref:
        raise ValueError(f"invalid handoff path: {ref!r}")
    relative = PurePosixPath(ref)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"handoff path escapes root: {ref!r}")
    path = root.joinpath(*relative.parts)
    if path.is_symlink() or not path.exists() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"missing or unsafe handoff file: {ref}")
    return path


def _json(root: Path, ref: str) -> dict[str, Any]:
    value = json.loads(_file(root, ref).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"handoff document must be an object: {ref}")
    return value


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_sha(root: Path, ref: str) -> str:
    """Use the source manifest's directory digest: sorted path plus file hash."""
    path = _path(root, ref)
    if path.is_file():
        return _sha(path)
    if not path.is_dir():
        raise ValueError(f"unsupported handoff source: {ref}")
    files = sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix())
    if any(item.is_symlink() or not item.resolve().is_relative_to(path.resolve()) for item in files):
        raise ValueError(f"unsafe handoff directory: {ref}")
    if any(not item.is_file() and not item.is_dir() for item in files):
        raise ValueError(f"special file in handoff directory: {ref}")
    digest = hashlib.sha256()
    for item in files:
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(_sha(item).encode("ascii"))
    return digest.hexdigest()


def build_snapshot(root: Path, descriptor_ref: str) -> dict[str, Any]:
    """Check current bytes against both handoff manifests and retain only metadata."""
    root = Path(root).resolve()
    config = _json(root, descriptor_ref)
    schema_path = Path(__file__).resolve().parents[2] / "generator/schemas/external_handoff_bridge.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: str(error.path))
    if errors:
        raise ValueError(f"invalid external handoff descriptor: {errors[0].message}")

    authority_path = _file(root, config["authority_ref"])
    ledger = authority_path.read_text(encoding="utf-8")
    decision_rows = set(re.findall(r"(?m)^\|\s*\*{0,2}((?:E|K|O)-\d+)\*{0,2}\s*\|", ledger))
    unresolved_decisions = sorted(set(config["decision_refs"] + config["open_gate_refs"]) - decision_rows)
    if unresolved_decisions:
        raise ValueError(f"decision references missing from authority: {unresolved_decisions}")
    if any(not ref.startswith("O-") for ref in config["open_gate_refs"]):
        raise ValueError("open_gate_refs must reference O-* rows")

    handoff = _json(root, config["handoff_manifest_ref"])
    handoff_schema = handoff.get("schema")
    if not isinstance(handoff_schema, str) or not re.fullmatch(r"[^/]+/[^/]*handoff-manifest/v1", handoff_schema):
        raise ValueError("unsupported external handoff manifest")
    sources = handoff.get("sources")
    if not isinstance(sources, list) or any(not isinstance(row, dict) for row in sources):
        raise ValueError("invalid handoff source inventory")
    source_by_key = {row.get("key"): row for row in sources}
    if len(source_by_key) != len(sources):
        raise ValueError("duplicate handoff source key")
    missing_keys = sorted(set(config["required_source_keys"]) - set(source_by_key))
    if missing_keys:
        raise ValueError(f"required handoff sources missing: {missing_keys}")

    drift: list[str] = []
    source_rows: list[dict[str, str]] = []
    for key in config["required_source_keys"]:
        row = source_by_key[key]
        ref = row.get("path")
        try:
            actual = _source_sha(root, ref)
        except (ValueError, TypeError):
            actual = "missing"
        expected = row.get("sha256")
        if not isinstance(expected, str) or not _HASH.fullmatch(expected) or actual != expected:
            drift.append(f"source:{key}")
        source_rows.append({"key": key, "ref": ref, "sha256": actual})
    # The complete original inventory is checked as well, so changed ledger,
    # index, or missing legacy directories cannot disappear from the report.
    for row in sources:
        if row["key"] in config["required_source_keys"]:
            continue
        try:
            actual = _source_sha(root, row["path"])
        except (ValueError, TypeError):
            actual = "missing"
        if actual != row.get("sha256"):
            drift.append(f"handoff_manifest:{row['key']}")

    package = _json(root, config["package_manifest_ref"])
    package_schema = package.get("schema")
    if not isinstance(package_schema, str) or not re.fullmatch(r"[^/]+/[^/]*executable-package-manifest/v1", package_schema):
        raise ValueError("unsupported executable package manifest")
    entries = package.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("empty executable package manifest")
    package_base = PurePosixPath(config["package_manifest_ref"]).parent
    package_refs: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("invalid executable package entry")
        ref = entry["path"]
        if ref in package_refs:
            raise ValueError(f"duplicate executable package entry: {ref}")
        package_refs.add(ref)
        try:
            path = _file(root, str(package_base / ref))
            actual = _sha(path)
            size = path.stat().st_size
        except ValueError:
            actual, size = "missing", -1
        if actual != entry.get("sha256") or size != entry.get("bytes"):
            drift.append(f"package:{ref}")
    missing_refs = sorted(set(config["required_package_refs"]) - package_refs)
    if missing_refs:
        raise ValueError(f"required executable package entries missing: {missing_refs}")

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_delivery_handoff_snapshot",
        "project_ref": config["project_ref"],
        "use_case_ref": config["use_case_ref"],
        "descriptor": {"ref": descriptor_ref, "sha256": _sha(_file(root, descriptor_ref))},
        "authority": {"ref": config["authority_ref"], "sha256": _sha(authority_path)},
        "handoff_manifest": {"ref": config["handoff_manifest_ref"], "sha256": _sha(_file(root, config["handoff_manifest_ref"]))},
        "package_manifest": {"ref": config["package_manifest_ref"], "sha256": _sha(_file(root, config["package_manifest_ref"]))},
        "required_sources": source_rows,
        "executable_package_file_count": len(entries),
        "decision_refs": config["decision_refs"],
        "open_gate_refs": config["open_gate_refs"],
        "integrity_state": "needs_attention" if drift else "hashes_match",
        "drift": sorted(set(drift)),
        "evidence_level": "static_handoff_inventory",
        "apply_ready": False,
        "runtime_proven": False,
        "customer_accepted": False,
        "authority_note": "The external ledger remains authoritative. This metadata snapshot is neither an approval nor tenant evidence; recheck current source hashes before use.",
    }


def attach_snapshot(repository: ProjectPackageRevisionRepository, snapshot: dict[str, Any]) -> RevisionRecord:
    """Append a reviewed metadata sidecar as a new, validated Project Package revision."""
    current = repository.head()
    if current is None or current.project_ref != snapshot["project_ref"]:
        raise ValueError("external handoff does not match a saved Project Package")
    use_case_ref = snapshot.get("use_case_ref")
    if not isinstance(use_case_ref, str) or not _ID.fullmatch(use_case_ref):
        raise ValueError("invalid handoff use-case identity")
    with tempfile.TemporaryDirectory(prefix="external-handoff-") as temporary:
        root = repository.checkout(Path(temporary) / "package", current.revision_hash)
        target = root / "handoff" / f"{use_case_ref}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
        # One early prototype used a shared name. Its content is recoverable
        # from the previous immutable revision; do not carry the duplicate on.
        legacy = root / "handoff" / "external_handoff.json"
        if legacy.is_file():
            legacy.unlink()
        if target.is_file() and target.read_text(encoding="utf-8") == content:
            return current
        target.write_text(content, encoding="utf-8", newline="\n")
        return repository.commit_draft(root, expected_head_hash=current.revision_hash)


def refresh_handoff_manifest(
    root: Path, descriptor_ref: str, *, expected_manifest_sha256: str, allowed_drift_keys: set[str]
) -> list[str]:
    """Rebaseline only explicitly reviewed inventory rows, never a changed core contract."""
    snapshot = build_snapshot(root, descriptor_ref)
    drift = snapshot["drift"]
    if any(not item.startswith("handoff_manifest:") for item in drift):
        raise ValueError("cannot refresh a changed required contract or executable package")
    actual_keys = {item.removeprefix("handoff_manifest:") for item in drift}
    if actual_keys != allowed_drift_keys:
        raise ValueError(f"drift review mismatch: found {sorted(actual_keys)}, allowed {sorted(allowed_drift_keys)}")
    if not _HASH.fullmatch(expected_manifest_sha256) or snapshot["handoff_manifest"]["sha256"] != expected_manifest_sha256:
        raise ValueError("handoff manifest changed since review")
    if not drift:
        return []

    root = Path(root).resolve()
    config = _json(root, descriptor_ref)
    ref = config["handoff_manifest_ref"]
    path = _file(root, ref)
    manifest = _json(root, ref)
    for row in manifest["sources"]:
        if row["key"] not in actual_keys:
            continue
        source_path = _path(root, row["path"])
        row["sha256"] = _source_sha(root, row["path"])
        files = [item for item in source_path.rglob("*") if item.is_file()] if source_path.is_dir() else [source_path]
        if not files:
            raise ValueError(f"empty handoff source directory: {row['path']}")
        row["readStatus"] = f"readable_directory_{len(files)}_files" if source_path.is_dir() else "readable"
        row["lastModifiedUtc"] = datetime.fromtimestamp(max(item.stat().st_mtime for item in files), timezone.utc).isoformat()
    for decision_ref in config["decision_refs"] + config["open_gate_refs"]:
        if decision_ref not in manifest.setdefault("decisionRefs", []):
            manifest["decisionRefs"].append(decision_ref)
    manifest["generatedAtUtc"] = datetime.now(timezone.utc).isoformat()
    content = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if _sha(path) != expected_manifest_sha256:
        raise ValueError("handoff manifest changed before save")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".handoff-manifest-", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return sorted(actual_keys)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--descriptor", required=True)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--schemas", type=Path)
    parser.add_argument("--refresh-manifest", action="store_true", help="Explicitly rebaseline reviewed inventory rows")
    parser.add_argument("--expected-manifest-sha256")
    parser.add_argument("--allow-drift-key", action="append", default=[])
    args = parser.parse_args(argv)
    if args.refresh_manifest:
        if not args.expected_manifest_sha256 or not args.allow_drift_key:
            parser.error("refresh requires --expected-manifest-sha256 and at least one --allow-drift-key")
        refresh_handoff_manifest(
            args.source_root, args.descriptor,
            expected_manifest_sha256=args.expected_manifest_sha256,
            allowed_drift_keys=set(args.allow_drift_key),
        )
    snapshot = build_snapshot(args.source_root, args.descriptor)
    if args.repository:
        if not args.schemas:
            parser.error("--schemas is required with --repository")
        revision = attach_snapshot(ProjectPackageRevisionRepository(args.repository, args.schemas), snapshot)
        snapshot["project_package_revision"] = revision.revision
        snapshot["project_package_revision_hash"] = revision.revision_hash
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0 if snapshot["integrity_state"] == "hashes_match" else 2


if __name__ == "__main__":
    raise SystemExit(main())
