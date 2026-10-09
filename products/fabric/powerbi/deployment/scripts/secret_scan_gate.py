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

Second mode ``--baseline`` (07.10.2026): the repository-wide ``.secrets.baseline`` as a gate.
It runs ``detect-secrets-hook --baseline`` (``python -m detect_secrets.pre_commit_hook``, the
same entry point) over the git-tracked files (CI ``stage1.yml`` job ``python-checks``) or over
the staged files (``--staged``, versioned pre-commit hook ``.githooks/pre-commit``). Red is a
finding that is not in the baseline. The hook runs against a temporary copy, so the gate never
rewrites ``.secrets.baseline`` itself; a stale baseline (moved line numbers, removed findings)
is reported as a note, refreshed with ``detect-secrets scan --baseline .secrets.baseline``.
The installed detect-secrets must equal the baseline's ``version`` (pin, otherwise exit 2):
another version may bring other plugins and other findings.

Hash fields are filtered structurally, not reviewed one by one: ``HASH_LINE_PATTERNS`` are
stored in the baseline (``filters_used``, ``should_exclude_line``) and the hook applies them
from there. Each pattern matches a whole JSON line whose key names a hash and whose value has
the exact shape of that hash; any other string in the same files is still scanned.

Exit codes: 0 scanned, no findings · 1 findings · 2 not scanned (tool missing, tool error,
or nothing to scan) — "nothing found" and "did not run" stay distinguishable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from importlib import metadata
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


# -- repository-wide baseline gate (--baseline) --------------------------------------------

BASELINE = ".secrets.baseline"

# Lines that carry nothing but a hash, written by tools (hashlib hexdigest, git rev-parse).
# Each pattern pins key AND exact value shape, so a real secret under another key, or a value
# of another shape under these keys, is still reported. Measured 07.10.2026 over the 4298
# git-tracked files: every line with one of these keys and a literal value matched; the
# non-matching lines are code (``"sha256": _sha256(...)``). These patterns are what the
# baseline stores under ``filters_used`` (test: test_secret_baseline_gate.py).
HASH_LINE_PATTERNS = (
    # SHA-256 pins: PIN.json mirrors, showdaten.lock.json, MIRROR.json, dax_smoke quelle_sha256,
    # egress-case payload_sha256 (check_dataarch_mirror.py, check_superversion_pins.py, showdaten.py).
    r'^\s*"(?:sha256|[a-z0-9_]+_sha256)"\s*:\s*"[0-9a-f]{64}",?\s*$',
    # Git commit pins (40 hex): PIN.json source_commit, upstream-source commit pins.
    r'^\s*"(?:commit|source_commit)"\s*:\s*"[0-9a-f]{40}",?\s*$',
    # Visual-regression signatures (tooling/visual_library/visreg.py): 256-bit dHash = 64 hex,
    r'^\s*"dhash"\s*:\s*"[0-9a-f]{64}",?\s*$',
    # and the 8x8x3 colour grid of 5-bit values = 192 bytes, each byte 00..1f.
    r'^\s*"color"\s*:\s*"(?:[01][0-9a-f]){192}",?\s*$',
    # Rule-body fingerprint of scripts/plattform_baseline.json (check_plattform.regelstand, 12 hex).
    r'^\s*"_regelstand"\s*:\s*"[0-9a-f]{12}",?\s*$',
)

HOOK_FINDING_MARK = "Potential secrets about to be committed"
CHUNK = 150


def _git_files(repo_root: Path, staged: bool) -> list:
    """Git-tracked (or staged: added/copied/modified/renamed) files, without the baseline."""
    cmd = (["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"] if staged
           else ["git", "ls-files", "-z"])
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, check=False)
    if proc.returncode != 0:
        raise OSError(f"git exit {proc.returncode}")
    names = [n for n in proc.stdout.decode("utf-8", "replace").split("\0") if n]
    return [n for n in names if n != BASELINE and (repo_root / n).is_file()]


def _hook_command() -> list | None:
    """``python -m detect_secrets.pre_commit_hook`` if importable, else ``detect-secrets-hook``."""
    try:
        metadata.version("detect-secrets")
        return [sys.executable, "-m", "detect_secrets.pre_commit_hook"]
    except metadata.PackageNotFoundError:
        exe = shutil.which("detect-secrets-hook")
        return [exe] if exe else None


def _installed_version(hook: list) -> str:
    if hook[0] == sys.executable:
        return metadata.version("detect-secrets")
    cli = Path(hook[0]).with_name("detect-secrets")
    try:
        proc = subprocess.run([str(cli), "--version"], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False)
    except OSError:
        return ""
    return proc.stdout.strip()


def _run_chunk(hook: list, baseline_text: str, repo_root: Path, files: list) -> tuple:
    """One hook run over ``files`` against a fresh temporary copy of the baseline."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / BASELINE
        copy.write_text(baseline_text, encoding="utf-8", newline="\n")
        proc = subprocess.run([*hook, "--baseline", str(copy), *files], cwd=repo_root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", check=False)
    return proc.returncode, proc.stdout, proc.stderr


def baseline_main(repo_root: Path = Path("."), staged: bool = False) -> int:
    """Gate: no finding outside ``.secrets.baseline``. Exit 0 / 1 / 2 as in ``main``."""
    path = repo_root / BASELINE
    try:
        text = path.read_text(encoding="utf-8")
        pinned = json.loads(text)["version"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"secret baseline gate NOT RUN: {BASELINE} unreadable ({exc.__class__.__name__})")
        return 2
    hook = _hook_command()
    if hook is None:
        print(f"secret baseline gate NOT RUN: detect-secrets missing "
              f"(pip install detect-secrets=={pinned})")
        return 2
    installed = _installed_version(hook)
    if installed != pinned:
        print(f"secret baseline gate NOT RUN: detect-secrets {installed or '?'} installed, "
              f"baseline pins {pinned} (pip install detect-secrets=={pinned})")
        return 2
    try:
        files = _git_files(repo_root, staged)
    except OSError as exc:
        print(f"secret baseline gate NOT RUN: file list ({exc})")
        return 2
    if not files:
        if staged:
            print("secret baseline gate: no staged files to scan")
            return 0
        print("secret baseline gate NOT RUN: no git-tracked files")
        return 2
    chunks = [files[i:i + CHUNK] for i in range(0, len(files), CHUNK)]
    workers = max(1, min(len(chunks), os.cpu_count() or 1))
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda c: _run_chunk(hook, text, repo_root, c), chunks))
    except OSError as exc:
        print(f"secret baseline gate NOT RUN: {exc.__class__.__name__}")
        return 2
    found, stale = [], 0
    for rc, out, err in results:
        if rc == 1 and HOOK_FINDING_MARK in out:
            found.append(out)
        elif rc == 3:
            stale += 1
        elif rc != 0:
            print(f"secret baseline gate NOT RUN: hook exit {rc}: {(err or out).strip()[-400:]}")
            return 2
    if found:
        for out in found:
            for line in out.splitlines():
                if line.startswith(("Secret Type:", "Location:")):
                    print(line)
        print(f"secret baseline gate: findings not in {BASELINE} — remove the secret, or, for a "
              f"false positive, `# pragma: allowlist secret` or "
              f"`detect-secrets scan --baseline {BASELINE}` + `detect-secrets audit {BASELINE}`")
        return 1
    if stale:
        print(f"note: {BASELINE} lists line numbers or findings that moved or vanished; "
              f"refresh with `detect-secrets scan --baseline {BASELINE}`")
    print(f"secret baseline gate: 0 new findings in {len(files)} file(s) "
          f"(detect-secrets {installed})")
    return 0


def cli(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", action="store_true",
                        help="repository-wide gate against .secrets.baseline")
    parser.add_argument("--staged", action="store_true",
                        help="with --baseline: only staged files (pre-commit)")
    args = parser.parse_args(argv)
    if args.staged and not args.baseline:
        parser.error("--staged requires --baseline")
    if not args.baseline:
        return main()
    try:
        return baseline_main(staged=args.staged)
    except Exception as exc:  # noqa: BLE001 - a crash must read "not run", never "finding" (1)
        print(f"secret baseline gate NOT RUN: {exc.__class__.__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(cli())
