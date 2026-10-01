#!/usr/bin/env python3
"""Secret scan over the release automation, as a build gate (I-21 W5.4).

The release pipelines publish ``products/fabric/powerbi/deployment`` as the ``automation``
artifact and run it with the service-principal secret in the environment. This gate fails the
build when a credential-like string is committed in the code and configuration of that
artifact. Tool: ``detect-secrets`` (PyPI, pinned in the pipeline), the same scanner the
Meridian secret-scan emitter uses.

Scope on purpose: the whole repository measured 630 detect-secrets findings in 50 files
(01.10.2026, ``detect-secrets scan`` over the git-tracked files, no baseline) — a repo-wide
gate would be red until someone reviews a baseline. The two directories below measured 0
findings with the ``tests/`` exclusion. Tests carry fake secrets on purpose
(``test_secret_not_in_argv.py``) and are excluded.

First choice on Azure Repos remains GitHub Advanced Security secret scanning with push
protection (repository setting, Learn ``azure/devops/repos/security/
github-advanced-security-secret-scanning``); this job covers repositories without it.

Exit codes: 0 scanned, no findings · 1 findings · 2 not scanned (tool missing, tool error,
or nothing to scan) — "nothing found" and "did not run" stay distinguishable.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SCAN_PATHS = (
    "products/fabric/powerbi/deployment/scripts",
    "products/fabric/powerbi/deployment/resources",
)
EXCLUDE_FILES = r"(^|/)tests/"


def files_in_scope(repo_root: Path, paths=SCAN_PATHS, exclude: str = EXCLUDE_FILES) -> list:
    """Files the scan covers (relative POSIX paths), so an empty scope is not read as clean."""
    pattern = re.compile(exclude)
    found = []
    for rel in paths:
        base = repo_root / rel
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            rel_path = path.relative_to(repo_root).as_posix()
            if not pattern.search(rel_path):
                found.append(rel_path)
    return found


def findings(report: dict) -> dict:
    """``{file: [finding types]}`` from a ``detect-secrets scan`` JSON report."""
    results = report.get("results")
    if not isinstance(results, dict):
        raise ValueError("detect-secrets report has no 'results' object")
    return {name: sorted({hit.get("type", "?") for hit in hits})
            for name, hits in results.items() if hits}


def main(repo_root: Path = Path(".")) -> int:
    scope = files_in_scope(repo_root)
    if not scope:
        print("secret scan NOT RUN: no files in scope " + ", ".join(SCAN_PATHS))
        return 2
    cmd = [sys.executable, "-m", "detect_secrets", "scan", "--all-files",
           *SCAN_PATHS, "--exclude-files", EXCLUDE_FILES]
    try:
        proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False)
    except OSError as exc:
        print(f"secret scan NOT RUN: {exc.__class__.__name__}")
        return 2
    if proc.returncode != 0:
        print(f"secret scan NOT RUN: detect-secrets exit {proc.returncode}: {proc.stderr.strip()}")
        return 2
    try:
        hits = findings(json.loads(proc.stdout))
    except ValueError as exc:
        print(f"secret scan NOT RUN: unreadable report ({exc})")
        return 2
    if hits:
        for name, types in sorted(hits.items()):
            print(f"FINDING {name}: {', '.join(types)}")
        print(f"secret scan: {len(hits)} file(s) with findings in {len(scope)} scanned")
        return 1
    print(f"secret scan: 0 findings in {len(scope)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
