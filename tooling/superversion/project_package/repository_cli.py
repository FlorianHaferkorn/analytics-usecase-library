"""JSON CLI for the Project Package revision repository.

This is the narrow subprocess boundary used by Studio.  The Python repository
remains the only persistence authority; callers receive machine-readable
results and never implement package validation or history rules themselves.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .repository import (
    DEFAULT_MAX_ZIP_COMPRESSION_RATIO,
    DEFAULT_MAX_ZIP_MEMBER_BYTES,
    DEFAULT_MAX_ZIP_MEMBERS,
    DEFAULT_MAX_ZIP_TOTAL_BYTES,
    ProjectPackageRevisionRepository,
    RevisionRecord,
    StaleProjectPackageDraftError,
)


def _record(value: RevisionRecord | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "revision_hash": value.revision_hash,
        "package_id": value.package_id,
        "project_ref": value.project_ref,
        "revision": value.revision,
        "parent_revision_hash": value.parent_revision_hash,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)

    commit = commands.add_parser("commit", help="Append one validated package revision")
    commit.add_argument("--package", type=Path, required=True)

    commit_draft = commands.add_parser(
        "commit-draft",
        help="Derive technical manifest metadata and append a validated draft",
    )
    commit_draft.add_argument("--package", type=Path, required=True)
    commit_draft.add_argument(
        "--expected-head",
        required=True,
        help="Expected HEAD hash, or the explicit token 'none' for the first revision",
    )

    commands.add_parser("head", help="Read and verify the current revision")

    transfer = commands.add_parser("transfer-discovery", help="Append reviewed, source-backed discovery proposals")
    transfer.add_argument("--input", type=Path, required=True)

    checkout = commands.add_parser("checkout", help="Restore one complete package revision")
    checkout.add_argument("--output", type=Path, required=True)
    checkout.add_argument("--revision")

    release = commands.add_parser("release-input", help="Export or explicitly attest approved pinned compiler inputs")
    release.add_argument("--revision", required=True)
    release.add_argument("--project-ref", required=True)
    release.add_argument("--actor")
    release.add_argument("--rationale")
    release.add_argument("--output", type=Path)

    difference = commands.add_parser("diff", help="Compare two complete revisions")
    difference.add_argument("--from-revision", required=True)
    difference.add_argument("--to-revision", required=True)

    export = commands.add_parser("export", help="Export the complete repository history")
    export.add_argument("--output", type=Path, required=True)

    import_command = commands.add_parser("import", help="Import and verify complete history")
    import_command.add_argument("--input", type=Path, required=True)
    import_command.add_argument("--max-members", type=int, default=DEFAULT_MAX_ZIP_MEMBERS)
    import_command.add_argument("--max-member-bytes", type=int, default=DEFAULT_MAX_ZIP_MEMBER_BYTES)
    import_command.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_ZIP_TOTAL_BYTES)
    import_command.add_argument(
        "--max-compression-ratio",
        type=float,
        default=DEFAULT_MAX_ZIP_COMPRESSION_RATIO,
    )
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "import":
        repository = ProjectPackageRevisionRepository.import_zip(
            args.input,
            args.repository,
            args.schemas,
            max_members=args.max_members,
            max_member_bytes=args.max_member_bytes,
            max_total_bytes=args.max_total_bytes,
            max_compression_ratio=args.max_compression_ratio,
        )
        return {"ok": True, "head": _record(repository.head())}

    repository = ProjectPackageRevisionRepository(args.repository, args.schemas)
    if args.command == "transfer-discovery":
        from .discovery_transfer import transfer_discovery
        return {"ok": True, "revision": _record(transfer_discovery(repository, json.loads(args.input.read_text(encoding="utf-8"))))}
    if args.command == "release-input":
        from .release import release_input
        bundle = release_input(
            repository, args.project_ref, args.revision,
            actor=args.actor, rationale=args.rationale,
        )
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(bundle, handle, ensure_ascii=False, sort_keys=True)
            return {"ok": True, "output": str(args.output)}
        return {"ok": True, "release_bundle": bundle}
    if args.command == "commit":
        return {"ok": True, "revision": _record(repository.commit(args.package))}
    if args.command == "commit-draft":
        expected_head = None if args.expected_head.lower() == "none" else args.expected_head
        return {
            "ok": True,
            "revision": _record(
                repository.commit_draft(
                    args.package,
                    expected_head_hash=expected_head,
                )
            ),
        }
    if args.command == "head":
        return {"ok": True, "head": _record(repository.head())}
    if args.command == "checkout":
        output = repository.checkout(args.output, args.revision)
        return {"ok": True, "output": str(output), "revision": _record(repository.get(args.revision))}
    if args.command == "diff":
        return {
            "ok": True,
            "diff": repository.diff(args.from_revision, args.to_revision),
        }
    if args.command == "export":
        output = repository.export_zip(args.output)
        return {"ok": True, "output": str(output), "head": _record(repository.head())}
    raise AssertionError(f"unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = run(args)
    except StaleProjectPackageDraftError as exc:
        print(
            json.dumps(
                {"ok": False, "status": 409, "code": "stale_head", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
