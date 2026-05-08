#!/usr/bin/env python3
"""
check_schema_versions.py — Validate $schema URLs in generated PBIR files.

Scans all .Report folders under dist/ and verifies that every generated file
declares a $schema URL matching the pinned version in schema_registry.py.

Failures mean a generator, writer, or adapter is still using a hard-coded
schema URL instead of the registry — or the registry was updated without
regenerating reports.

Usage (from repository root):
    py -3 products/fabric/powerbi/tooling/validation/check_schema_versions.py
    py -3 products/fabric/powerbi/tooling/validation/check_schema_versions.py --dist-root path/to/dist
    py -3 products/fabric/powerbi/tooling/validation/check_schema_versions.py --explain-known-fix

Exit codes: 0 = pass, 1 = failures found, 2 = no reports found (warn only).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.schema_registry import (
    REPORT_SCHEMA,
    PAGE_SCHEMA,
    VISUAL_SCHEMA,
    PAGES_METADATA_SCHEMA,
    VERSION_METADATA_SCHEMA,
    DEFINITION_PBIR_SCHEMA,
)

# Map of relative-path patterns to expected $schema values.
# Keys are descriptive labels for error messages.
_EXPECTED: list[tuple[str, str]] = [
    ("definition/report.json",           REPORT_SCHEMA),
    ("definition/version.json",          VERSION_METADATA_SCHEMA),
    ("definition/pages/pages.json",      PAGES_METADATA_SCHEMA),
    ("definition.pbir",                  DEFINITION_PBIR_SCHEMA),
]


class SchemaIssue(NamedTuple):
    report_path: Path
    file_path: Path
    expected: str
    actual: str
    context: str


def _check_report(report_dir: Path, issues: list[SchemaIssue]) -> None:
    """Scan one .Report folder for schema URL mismatches."""
    definition = report_dir / "definition"

    for rel, expected_url in _EXPECTED:
        target = report_dir / rel
        if not target.exists():
            continue
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        actual = data.get("$schema", "")
        if actual and actual != expected_url:
            issues.append(SchemaIssue(
                report_path=report_dir,
                file_path=target,
                expected=expected_url,
                actual=actual,
                context=rel,
            ))

    if not definition.is_dir():
        return

    for page_dir in (definition / "pages").iterdir() if (definition / "pages").is_dir() else []:
        if not page_dir.is_dir():
            continue
        page_json = page_dir / "page.json"
        if page_json.exists():
            try:
                data = json.loads(page_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            actual = data.get("$schema", "")
            if actual and actual != PAGE_SCHEMA:
                issues.append(SchemaIssue(
                    report_path=report_dir,
                    file_path=page_json,
                    expected=PAGE_SCHEMA,
                    actual=actual,
                    context=f"pages/{page_dir.name}/page.json",
                ))

        visuals_dir = page_dir / "visuals"
        if not visuals_dir.is_dir():
            continue
        for visual_dir in visuals_dir.iterdir():
            if not visual_dir.is_dir():
                continue
            visual_json = visual_dir / "visual.json"
            if not visual_json.exists():
                continue
            try:
                data = json.loads(visual_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            actual = data.get("$schema", "")
            if actual and actual != VISUAL_SCHEMA:
                issues.append(SchemaIssue(
                    report_path=report_dir,
                    file_path=visual_json,
                    expected=VISUAL_SCHEMA,
                    actual=actual,
                    context=f"visuals/{visual_dir.name}/visual.json",
                ))


def _explain_fix(issue: SchemaIssue) -> str:
    return (
        f"  Fix: The file was generated with an outdated schema URL.\n"
        f"       1. Verify schema_registry.py has the correct pinned version.\n"
        f"       2. Regenerate the report: py -3 products/fabric/powerbi/tooling/"
        f"page_scaffold_generator/generate_full_report.py --use-case "
        f"{issue.report_path.stem.split('_')[0]} --force-full\n"
        f"       3. Re-run this check."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist-root",
        default="products/fabric/powerbi/dist",
        help="Directory containing .Report folders (default: products/fabric/powerbi/dist).",
    )
    parser.add_argument(
        "--explain-known-fix",
        action="store_true",
        help="Print remediation steps next to each failure.",
    )
    args = parser.parse_args()

    dist_root = (
        Path(args.dist_root)
        if Path(args.dist_root).is_absolute()
        else _REPO_ROOT / args.dist_root
    )

    report_dirs = [d for d in dist_root.glob("*.Report") if d.is_dir()] if dist_root.is_dir() else []
    if not report_dirs:
        print(f"WARN: No .Report folders found under {dist_root}. Skipping schema version check.")
        return 2

    issues: list[SchemaIssue] = []
    for report_dir in sorted(report_dirs):
        _check_report(report_dir, issues)

    if not issues:
        print(f"Schema version check passed ({len(report_dirs)} report(s) scanned).")
        return 0

    print(f"FAIL: {len(issues)} schema URL mismatch(es) found:\n", file=sys.stderr)
    for issue in issues:
        rel_report = issue.report_path.relative_to(dist_root)
        print(
            f"  {rel_report}/{issue.context}\n"
            f"    expected: {issue.expected}\n"
            f"    actual:   {issue.actual}",
            file=sys.stderr,
        )
        if args.explain_known_fix:
            print(_explain_fix(issue), file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
