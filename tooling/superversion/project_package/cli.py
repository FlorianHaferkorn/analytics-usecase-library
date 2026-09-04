"""CLI for validating and projecting a Project Package lifecycle registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .artifact_lifecycle import (
    build_publication_manifest,
    reconcile_artifact_files,
    render_artifact_index,
)
from .validator import validate_project_package


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _artifact_registry(package_root: Path) -> dict[str, Any]:
    manifest = _load(package_root / "package.yaml")
    matches = [
        module
        for module in manifest.get("modules", [])
        if module.get("module_type") == "artifact_registry"
    ]
    if len(matches) != 1:
        raise ValueError("package must contain exactly one artifact_registry module")
    registry = _load(package_root / matches[0]["path"])
    if not isinstance(registry, dict):
        raise ValueError("artifact_registry module must be an object")
    return registry


def _validated_registry(package_root: Path, schema_root: Path) -> dict[str, Any]:
    errors = validate_project_package(package_root, schema_root)
    if errors:
        raise ValueError("invalid project package: " + "; ".join(errors))
    return _artifact_registry(package_root)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True, help="Project Package root")
    parser.add_argument("--schemas", type=Path, required=True, help="Schema directory")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate", help="Validate the complete package and lifecycle invariants")
    commands.add_parser("reconcile-files", help="Verify package-local artifact files and hashes")
    render = commands.add_parser("render-index", help="Render the human-readable artifact inventory")
    render.add_argument("--output", type=Path, required=True)

    publication = commands.add_parser(
        "publication-manifest",
        help="Freeze one recorded publication event as a machine-readable manifest",
    )
    publication.add_argument("--event-id", required=True)
    publication.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        errors = validate_project_package(args.package, args.schemas)
        if errors:
            raise ValueError("invalid project package: " + "; ".join(errors))
        return 0
    registry = _validated_registry(args.package, args.schemas)
    if args.command == "reconcile-files":
        errors = reconcile_artifact_files(args.package, registry)
        if errors:
            raise ValueError("artifact file reconciliation failed: " + "; ".join(errors))
        return 0
    if args.command == "render-index":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_artifact_index(registry), encoding="utf-8", newline="\n")
        return 0
    if args.command == "publication-manifest":
        errors = reconcile_artifact_files(args.package, registry)
        if errors:
            raise ValueError("artifact file reconciliation failed: " + "; ".join(errors))
        manifest = build_publication_manifest(registry, args.event_id)
        schema = _load(args.schemas / "project_publication_manifest.schema.json")
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return 0
    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
