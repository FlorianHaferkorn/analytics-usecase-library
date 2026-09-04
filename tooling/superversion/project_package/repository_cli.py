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

from .repository import ProjectPackageRevisionRepository, RevisionRecord


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

    commands.add_parser("head", help="Read and verify the current revision")

    checkout = commands.add_parser("checkout", help="Restore one complete package revision")
    checkout.add_argument("--output", type=Path, required=True)
    checkout.add_argument("--revision")

    difference = commands.add_parser("diff", help="Compare two complete revisions")
    difference.add_argument("--from-revision", required=True)
    difference.add_argument("--to-revision", required=True)

    export = commands.add_parser("export", help="Export the complete repository history")
    export.add_argument("--output", type=Path, required=True)

    import_command = commands.add_parser("import", help="Import and verify complete history")
    import_command.add_argument("--input", type=Path, required=True)
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "import":
        repository = ProjectPackageRevisionRepository.import_zip(
            args.input,
            args.repository,
            args.schemas,
        )
        return {"ok": True, "head": _record(repository.head())}

    repository = ProjectPackageRevisionRepository(args.repository, args.schemas)
    if args.command == "commit":
        return {"ok": True, "revision": _record(repository.commit(args.package))}
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
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
