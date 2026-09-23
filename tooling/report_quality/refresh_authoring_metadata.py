#!/usr/bin/env python3
"""Refresh the vendored authoring-metadata snapshot from the official CLI.

Runs Microsoft's ``powerbi-report-author`` (a Tier 1 / opt-in external tool) once
-- in OUR pipeline -- and vendors the authoritative visual-type role metadata as
JSON. This is the "metadata snapshot pattern" from ADR 0001: the pure-Python
floor (and the report generator) can then read authoritative queryState roles
WITHOUT requiring the CLI at the customer site.

Usage::

    npm install -g @microsoft/powerbi-report-authoring-cli   # once, in CI
    python -m tooling.report_quality.refresh_authoring_metadata

The output path defaults to ``tooling/schemas/pbir/authoring_metadata_snapshot.json``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CLI = "powerbi-report-author"
DEFAULT_OUT = Path("tooling/schemas/pbir/authoring_metadata_snapshot.json")


def _run_json(cli: str, args: list[str]) -> dict:
    proc = subprocess.run([cli, *args], capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
    return json.loads(proc.stdout)["data"]


def build_snapshot(cli: str = DEFAULT_CLI) -> dict:
    """Query the CLI for every visual type's role metadata and assemble a snapshot."""
    version = subprocess.run([cli, "--version"], capture_output=True, text=True, check=True, encoding="utf-8", errors="replace").stdout.strip()
    catalog = _run_json(cli, ["catalog", "list"])
    type_ids = [t["visualType"] if isinstance(t, dict) else t for t in catalog.get("visualTypes", [])]

    visual_types: dict[str, dict] = {}
    for visual_type in sorted(type_ids):
        described = _run_json(cli, ["catalog", "describe", visual_type])
        roles = {name: meta.get("kind") for name, meta in (described.get("roles") or {}).items()}
        visual_types[visual_type] = {
            "requiredRoles": list(described.get("requiredRoles") or []),
            "roles": roles,
        }

    return {
        "_meta": {
            "cli": "@microsoft/powerbi-report-authoring-cli",
            "cliVersion": version,
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "visualTypeCount": len(visual_types),
            "note": (
                "Generated in CI from the official CLI; consumed offline by the "
                "pure-Python floor. Do not hand-edit -- regenerate with "
                "tooling/report_quality/refresh_authoring_metadata.py (ADR 0001)."
            ),
        },
        "visualTypes": visual_types,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cli", default=DEFAULT_CLI, help="Path/name of the powerbi-report-author CLI.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Where to write the snapshot JSON.")
    args = parser.parse_args(argv)

    try:
        snapshot = build_snapshot(args.cli)
    except FileNotFoundError:
        print(
            f"ERROR: '{args.cli}' not found on PATH. "
            "Install: npm install -g @microsoft/powerbi-report-authoring-cli",
            file=sys.stderr,
        )
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: {args.cli} failed: {exc.stderr or exc}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(
        f"Wrote {args.out} "
        f"({snapshot['_meta']['visualTypeCount']} visual types, CLI {snapshot['_meta']['cliVersion']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
