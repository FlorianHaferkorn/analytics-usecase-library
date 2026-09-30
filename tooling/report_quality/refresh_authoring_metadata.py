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

``--base-theme-only`` vendors the base theme instead (Meridian D-587): it runs
``scaffold --offline`` of the pinned CLI in a temp dir and copies the scaffolded
``BaseThemes/<name>.json`` byte-for-byte to ``tooling/schemas/pbir/base_themes/``.
Name and ``reportVersionAtImport`` are printed; they live as constants in
``tooling/report_quality/base_theme.py`` and the drift test compares all three.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
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


def cli_version(cli: str = DEFAULT_CLI) -> str:
    """``powerbi-report-author --version`` (stripped)."""
    return subprocess.run([cli, "--version"], capture_output=True, text=True, check=True,
                          encoding="utf-8", errors="replace").stdout.strip()


def scaffold_base_theme(cli: str = DEFAULT_CLI) -> dict:
    """Scaffold a report with the official CLI and return what it pins as base theme.

    Returns ``{"cliVersion", "name", "reportVersionAtImport", "content"}``; ``content``
    is the scaffolded ``BaseThemes/<name>.json`` as bytes. ``--offline`` keeps the
    $schema versions pinned in the CLI (no network), the theme is a bundled asset.
    """
    version = cli_version(cli)
    with tempfile.TemporaryDirectory(prefix="aluca_scaffold_") as tmp:
        subprocess.run([cli, "scaffold", "--offline", "--name", "Probe", tmp],
                       capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
        report = Path(tmp) / "Probe.Report"
        data = json.loads((report / "definition" / "report.json").read_text(encoding="utf-8"))
        base = data["themeCollection"]["baseTheme"]
        items = [it for pkg in data.get("resourcePackages", []) for it in pkg.get("items", [])
                 if it.get("type") == "BaseTheme"]
        if len(items) != 1 or items[0].get("name") != base["name"]:
            raise ValueError(f"scaffold: unexpected BaseTheme items {items} for {base['name']}")
        content = (report / "StaticResources" / "SharedResources" / items[0]["path"]).read_bytes()
    return {
        "cliVersion": version,
        "name": base["name"],
        "reportVersionAtImport": base["reportVersionAtImport"],
        "content": content,
    }


def refresh_base_theme(cli: str = DEFAULT_CLI, out_dir: Path | None = None) -> dict:
    """Vendor the scaffolded base theme to ``out_dir`` (default: base_theme.VENDORED_DIR)."""
    from tooling.report_quality import base_theme as bt

    got = scaffold_base_theme(cli)
    target = (out_dir or bt.VENDORED_DIR) / f"{got['name']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(got["content"])
    got["path"] = target
    return got


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cli", default=DEFAULT_CLI, help="Path/name of the powerbi-report-author CLI.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Where to write the snapshot JSON.")
    parser.add_argument("--base-theme-only", action="store_true",
                        help="Vendor the scaffolded base theme (D-587) instead of the role snapshot.")
    args = parser.parse_args(argv)

    if args.base_theme_only:
        try:
            got = refresh_base_theme(args.cli)
        except FileNotFoundError:
            print(f"ERROR: '{args.cli}' not found on PATH.", file=sys.stderr)
            return 2
        except (subprocess.CalledProcessError, ValueError, KeyError) as exc:
            print(f"ERROR: scaffold failed: {getattr(exc, 'stderr', None) or exc}", file=sys.stderr)
            return 1
        print(f"Wrote {got['path']} (CLI {got['cliVersion']}, baseTheme {got['name']}, "
              f"reportVersionAtImport {json.dumps(got['reportVersionAtImport'], sort_keys=True)})")
        return 0

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
