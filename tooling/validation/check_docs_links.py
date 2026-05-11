"""
check_docs_links.py — Docs drift and broken-link validator.

Scans Markdown files in key onboarding/entry docs to detect:
  - References to known-deprecated or deleted paths.
  - Local [text](path) links that point to non-existent files/folders.

Scope: root *.md, docs/, core/usecases/ (factsheets only), products/fabric/powerbi/*.md
Excluded: internal/, dist/, tooling/ontology/out/, studio/playwright-report/, node_modules/

Exit 0 = clean; exit 1 = errors found.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Known-deprecated or deleted path fragments. Any Markdown file referencing
# these triggers an error so docs never silently rot after a refactor.
# ---------------------------------------------------------------------------
DEPRECATED_PATTERNS: list[tuple[str, str]] = [
    (
        r"tooling[/\\]generation[/\\]",
        "tooling/generation/ was renamed; use tooling/generator/ (or current script path)",
    ),
    (
        r"products/fabric/powerbi/guide/",
        "products/fabric/powerbi/guide/ does not exist; check docs/architecture/ instead",
    ),
    (
        r"tools/run_fabric_checks",
        "tools/run_fabric_checks is not the correct path; use products/fabric/powerbi/tooling/run_fabric_checks.ps1",
    ),
    (
        r"-UseAuroraShowcase",
        "-UseAuroraShowcase is deprecated (no-op); remove the flag from documentation",
    ),
    (
        r"Aurora showcase mirror",
        "Aurora showcase mirror was removed; update docs to reference dist/ directly",
    ),
    (
        r"pbip_templates/",
        "pbip_templates/ folder does not exist; use products/fabric/powerbi/templates/",
    ),
]

# Directories to scan (relative to repo root)
SCAN_ROOTS: list[str] = [
    ".",          # root *.md only (not recursive)
    "docs",
    "core/usecases",
    "products/fabric/powerbi",
]

# Root-level files to exclude from deprecated-path checks (historical records are OK)
DEPRECATED_CHECK_EXCLUSIONS: set[str] = {
    "CHANGELOG.md",
}

# Directories to exclude from recursive scan
EXCLUDE_DIRS: set[str] = {
    "internal",
    "dist",
    ".git",
    "node_modules",
    "studio/playwright-report",
    "studio/.next",
    "tooling/ontology/out",
    "tooling/.venv",
    ".cursor",
}


def _is_excluded(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return any(rel.startswith(ex) for ex in EXCLUDE_DIRS)


def collect_markdown_files(repo_root: Path) -> list[Path]:
    results: list[Path] = []

    # Root-level .md files only (non-recursive)
    for p in repo_root.glob("*.md"):
        if p.is_file():
            results.append(p)

    # Recursive scan in specific dirs
    recursive_roots = SCAN_ROOTS[1:]
    for rel in recursive_roots:
        base = repo_root / rel
        if not base.exists():
            continue
        for p in base.rglob("*.md"):
            if p.is_file() and not _is_excluded(p, repo_root):
                results.append(p)

    return sorted(set(results))


def check_deprecated(content: str, filepath: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    rel = filepath.relative_to(repo_root).as_posix()
    if filepath.name in DEPRECATED_CHECK_EXCLUSIONS:
        return errors
    for pattern, message in DEPRECATED_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append(f"{rel}: deprecated reference — {message}")
    return errors


_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')

# Template placeholder patterns to skip (e.g. Jinja/Handlebars {{VAR}})
_TEMPLATE_RE = re.compile(r'^\{\{.*\}\}$')

# Directories where relative links follow repo-root convention rather than
# file-relative convention (agent rule/skill docs use this pattern).
REPO_ROOT_LINK_DIRS: set[str] = {
    "docs/agent/rules",
    "docs/agent/skills",
    ".cursor/rules",
    ".cursor/skills",
}


def _is_repo_root_link_dir(filepath: Path, repo_root: Path) -> bool:
    try:
        rel = filepath.parent.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return any(rel == d or rel.startswith(d + "/") for d in REPO_ROOT_LINK_DIRS)


def check_local_links(content: str, filepath: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    rel_file = filepath.relative_to(repo_root).as_posix()
    is_agent_doc = _is_repo_root_link_dir(filepath, repo_root)

    for match in _LINK_RE.finditer(content):
        raw_target = match.group(2).strip()

        # Skip external links, anchors-only, mailto, and template placeholders
        if raw_target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if _TEMPLATE_RE.match(raw_target):
            continue
        # Skip generated .mdc config links
        if raw_target.endswith(".mdc"):
            continue

        # Strip anchor fragment
        target = raw_target.split("#")[0].strip()
        if not target:
            continue

        resolved_candidates: list[Path] = []

        if target.startswith("/"):
            # Absolute from repo root
            resolved_candidates.append((repo_root / target.lstrip("/")).resolve())
        else:
            # File-relative resolution (standard)
            resolved_candidates.append((filepath.parent / target).resolve())
            # Repo-root resolution as fallback (for agent rule docs and explicit convention)
            if is_agent_doc or not resolved_candidates[0].exists():
                resolved_candidates.append((repo_root / target).resolve())

        found = False
        for resolved in resolved_candidates:
            try:
                resolved.relative_to(repo_root.resolve())
            except ValueError:
                continue
            if resolved.exists():
                found = True
                break

        if not found:
            # Report using the primary resolution for the error message
            primary = resolved_candidates[0]
            try:
                display = primary.relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                display = str(primary)
            errors.append(
                f"{rel_file}: broken link -> {raw_target}  (resolved: {display})"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check docs for deprecated paths and broken links")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--no-link-check", action="store_true", help="Skip local link resolution check")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    files = collect_markdown_files(repo_root)
    all_errors: list[str] = []
    deprecation_errors: list[str] = []
    link_errors: list[str] = []

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        dep_errs = check_deprecated(content, filepath, repo_root)
        deprecation_errors.extend(dep_errs)

        if not args.no_link_check:
            lnk_errs = check_local_links(content, filepath, repo_root)
            link_errors.extend(lnk_errs)

    all_errors = deprecation_errors + link_errors

    if all_errors:
        print(f"Scanned {len(files)} Markdown files")
        print(f"FAIL: {len(deprecation_errors)} deprecated-path reference(s), {len(link_errors)} broken link(s)")
        for e in all_errors:
            print(f"  ERROR  {e}")
        print("")
        print("Fix guidance:")
        print("  - Deprecated paths: update the text to the current path shown in the message.")
        print("  - Broken links: verify the target file/folder exists or update the link.")
        print("  - See KNOWN_ERRORS_AND_FIXES.md for recurring patterns.")
        return 1

    print(f"Scanned {len(files)} Markdown files")
    print(f"OK: no deprecated-path references or broken links found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
