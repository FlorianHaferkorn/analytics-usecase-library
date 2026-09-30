#!/usr/bin/env python3
"""Fabric Notebook Toolkit boundary (Meridian D-603, mirrored 30.09.2026).

The Fabric Notebook Toolkit (CLI ``fntk``, PyPI package in the pattern below) ships under a
proprietary pre-release licence: no redistribution (clause 2e), no reverse engineering (2b),
telemetry on by default. Decision Florian 30.09.2026: internal developer tool only, run
against dev workspaces of our own loop. It must never reach a customer deliverable, a
generator (whose source carries the generated scripts), CI or a dependency list.

Blocked (tracked files, ``git ls-files``):
  * ``products/**`` (including ``dist``), ``core/**``, ``tooling/**``, ``.github/**``
  * every ``requirements*.txt``
Allowed: documentation and plans outside those trees (``docs/``, ``internal/``), plus the
explicit exemptions in ``EXEMPT`` (each with its reason).

Token boundary as in Meridian ``scripts/check_repo_hygiene.py`` rule 5: ``+``, ``/`` and
``=`` count as word characters, because Base64 blocks (vendored JS assets, embedded PNGs)
contain the four letters by chance.

Exit codes: 0 no finding, 1 finding(s), 2 not checked (``git ls-files`` failed) -- a gate
must tell "nothing found" from "did not run".

Usage::

    python tooling/validation/check_fntk_boundary.py [--repo-root PATH]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

FNTK_RE = re.compile(
    r"(?<![A-Za-z0-9+/_-])fntk(?![A-Za-z0-9+/=_])|fabric[-_]notebook[-_]toolkit", re.IGNORECASE
)

BLOCKED_PREFIXES: tuple[str, ...] = ("products/", "core/", "tooling/", ".github/")
REQUIREMENTS_RE = re.compile(r"(^|/)requirements[^/]*\.txt$")
TEXT_SUFFIXES: tuple[str, ...] = (
    ".py", ".ps1", ".psm1", ".sh", ".txt", ".toml", ".cfg", ".yml", ".yaml", ".json",
    ".ipynb", ".md", ".tmdl", ".pbir", ".sql", ".js", ".ts", ".tsx", ".platform", ".ini",
    ".j2", ".html",
)

# Path -> reason. Exact paths only; a new exemption is a reviewed edit here.
EXEMPT: dict[str, str] = {
    "tooling/validation/check_fntk_boundary.py": "the guard itself names what it blocks",
    "tooling/quality/check_upstream_sources.py": (
        "pin registry: carries the PyPI pin 0.0.1a10 so the sensor reports new releases "
        "(the pin is metadata, never an install)"),
}


def in_blocked_area(path: str) -> bool:
    if path in EXEMPT:
        return False
    return bool(REQUIREMENTS_RE.search(path)) or path.startswith(BLOCKED_PREFIXES)


def find_offenders(files: Iterable[str],
                   read: Callable[[str], str | None]) -> list[tuple[str, int, str]]:
    """(path, line, match) for the first mention per blocked file. ``read`` is injected
    so the core stays testable without a repository."""
    offenders: list[tuple[str, int, str]] = []
    for f in files:
        if not in_blocked_area(f) or not f.endswith(TEXT_SUFFIXES):
            continue
        text = read(f)
        if not text:
            continue
        for nr, line in enumerate(text.splitlines(), 1):
            m = FNTK_RE.search(line)
            if m:
                offenders.append((f, nr, m.group(0)))
                break
    return offenders


def _tracked_files(root: Path) -> list[str] | None:
    try:
        proc = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                              capture_output=True, check=False)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    files = _tracked_files(root)
    if files is None:
        print("[fntk-boundary] NOT CHECKED: git ls-files failed", file=sys.stderr)
        return 2

    def _read(rel: str) -> str | None:
        try:
            return (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    offenders = find_offenders(files, _read)
    scanned = sum(1 for f in files if in_blocked_area(f) and f.endswith(TEXT_SUFFIXES))
    if offenders:
        print(f"[fntk-boundary] FAIL: {len(offenders)} file(s) name the Notebook Toolkit "
              "(internal dev tool only, Meridian D-603):")
        for path, nr, hit in offenders:
            print(f"  - {path}:{nr}: `{hit}`")
        return 1
    print(f"[fntk-boundary] OK: {scanned} tracked text file(s) in blocked areas, no mention.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
