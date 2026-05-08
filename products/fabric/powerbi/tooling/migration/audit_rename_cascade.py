#!/usr/bin/env python3
"""
audit_rename_cascade.py — Audit all references to a table, measure, or column
across TMDL, DAX, PBIR JSON, filters, bookmarks, and report extensions.

This is AUDIT ONLY (read-only). It locates every occurrence of the old name
so you can review the full blast radius before renaming anything.

Usage (from repository root):
    # Audit a measure rename
    py -3 products/fabric/powerbi/tooling/migration/audit_rename_cascade.py \\
        --type measure --old-name "Net Sales Amount"

    # Audit a table rename
    py -3 products/fabric/powerbi/tooling/migration/audit_rename_cascade.py \\
        --type table --old-name "fact_sales"

    # Audit a column rename
    py -3 products/fabric/powerbi/tooling/migration/audit_rename_cascade.py \\
        --type column --old-name "net_sales" --table "fact_sales"

    # Output as JSON (useful for agent pipelines)
    py -3 ... --json

    # Scan a specific directory instead of the whole repo
    py -3 ... --type measure --old-name "X" --scan-root products/fabric/powerbi/dist

Exit codes: 0 = no references found, 1 = references found (review required), 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

_REPO_ROOT = Path(__file__).resolve().parents[5]

# File extensions to scan
_TMDL_EXT = {".tmdl"}
_JSON_EXT  = {".json", ".pbir"}
_ALL_EXT   = _TMDL_EXT | _JSON_EXT

# JSON files that should never be in source control and are skipped
_SKIP_PATTERNS = {".pbi/localSettings.json", ".pbi/cache.abf"}


@dataclass
class ReferenceHit:
    file: Path
    line_number: int
    line_content: str
    match_context: str


@dataclass
class AuditResult:
    old_name: str
    ref_type: str
    table: str
    hits: list[ReferenceHit] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.hits)


def _should_skip(path: Path) -> bool:
    path_str = path.as_posix()
    return any(pat in path_str for pat in _SKIP_PATTERNS)


def _iter_files(root: Path, extensions: set[str]) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in extensions and not _should_skip(path):
            yield path


def _search_text(path: Path, pattern: re.Pattern, context: str) -> list[ReferenceHit]:
    hits: list[ReferenceHit] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return hits
    for i, line in enumerate(lines, 1):
        if pattern.search(line):
            hits.append(ReferenceHit(
                file=path,
                line_number=i,
                line_content=line.strip(),
                match_context=context,
            ))
    return hits


def _measure_patterns(name: str) -> list[tuple[re.Pattern, str]]:
    """All regex patterns that reference a measure by name."""
    escaped = re.escape(name)
    return [
        # TMDL: measure 'Name' = ...
        (re.compile(r"measure\s+['\"]?" + escaped + r"['\"]?\s*=", re.IGNORECASE), "tmdl_measure_definition"),
        # TMDL/DAX: [Name] reference inside a measure DAX expression
        (re.compile(r"\[" + escaped + r"\]"), "dax_bracket_reference"),
        # JSON: "Property": "Name" in visual queryState
        (re.compile(r'"Property"\s*:\s*"' + escaped + r'"'), "json_property_ref"),
        # JSON: "nativeQueryRef": "Name"
        (re.compile(r'"nativeQueryRef"\s*:\s*"' + escaped + r'"'), "json_nativeQueryRef"),
        # JSON: "queryRef": "_Measures.Name"
        (re.compile(r'"queryRef"\s*:\s*"[^"]*\.' + escaped + r'"'), "json_queryRef"),
    ]


def _table_patterns(name: str) -> list[tuple[re.Pattern, str]]:
    """All regex patterns that reference a table by name."""
    escaped = re.escape(name)
    return [
        # TMDL: table Name or ref 'Name'
        (re.compile(r"^table\s+" + escaped + r"\b", re.IGNORECASE | re.MULTILINE), "tmdl_table_definition"),
        # TMDL relationships: `table1` or column reference
        (re.compile(r"\b" + escaped + r"\[", re.IGNORECASE), "tmdl_column_reference"),
        # DAX: RELATED(Name[col]) or CALCULATETABLE(, Name)
        (re.compile(r"\b" + escaped + r"\b"), "dax_or_json_name"),
        # JSON: "Entity": "Name"
        (re.compile(r'"Entity"\s*:\s*"' + escaped + r'"'), "json_entity_ref"),
        # JSON: "Table": "Name"
        (re.compile(r'"Table"\s*:\s*"' + escaped + r'"'), "json_table_ref"),
    ]


def _column_patterns(name: str, table: str) -> list[tuple[re.Pattern, str]]:
    """All patterns that reference a column, optionally scoped to a table."""
    escaped_col = re.escape(name)
    escaped_tbl = re.escape(table) if table else None
    patterns = [
        (re.compile(r"column\s+['\"]?" + escaped_col + r"['\"]?\b", re.IGNORECASE), "tmdl_column_definition"),
        (re.compile(r'"Property"\s*:\s*"' + escaped_col + r'"'), "json_property_ref"),
        (re.compile(r'"nativeQueryRef"\s*:\s*"' + escaped_col + r'"'), "json_nativeQueryRef"),
    ]
    if escaped_tbl:
        patterns.append((
            re.compile(r"\b" + escaped_tbl + r"\[" + escaped_col + r"\]", re.IGNORECASE),
            "dax_qualified_column_ref",
        ))
    else:
        patterns.append((
            re.compile(r"\[" + escaped_col + r"\]"),
            "dax_column_bracket_ref",
        ))
    return patterns


def audit(
    old_name: str,
    ref_type: str,
    table: str,
    scan_root: Path,
) -> AuditResult:
    result = AuditResult(old_name=old_name, ref_type=ref_type, table=table)

    if ref_type == "measure":
        pattern_list = _measure_patterns(old_name)
    elif ref_type == "table":
        pattern_list = _table_patterns(old_name)
    else:
        pattern_list = _column_patterns(old_name, table)

    for file_path in _iter_files(scan_root, _ALL_EXT):
        for pattern, ctx in pattern_list:
            hits = _search_text(file_path, pattern, ctx)
            result.hits.extend(hits)

    # Deduplicate: same file + line can match multiple patterns
    seen: set[tuple[Path, int]] = set()
    deduped: list[ReferenceHit] = []
    for h in result.hits:
        key = (h.file, h.line_number)
        if key not in seen:
            seen.add(key)
            deduped.append(h)
    result.hits = sorted(deduped, key=lambda h: (h.file, h.line_number))
    return result


def _print_result(result: AuditResult, scan_root: Path) -> None:
    print(f"\n=== Rename Cascade Audit ===")
    print(f"Type:      {result.ref_type}")
    print(f"Old name:  {result.old_name}")
    if result.table:
        print(f"Table:     {result.table}")
    print(f"Scan root: {scan_root}")
    print(f"References found: {result.count}\n")

    if not result.hits:
        print("No references found — safe to rename (double-check with Power BI Desktop before committing).")
        return

    current_file: Path | None = None
    for hit in result.hits:
        if hit.file != current_file:
            try:
                rel = hit.file.relative_to(scan_root)
            except ValueError:
                rel = hit.file
            print(f"\n  {rel}")
            current_file = hit.file
        print(f"    line {hit.line_number:4d}  [{hit.match_context}]  {hit.line_content[:120]}")

    print(f"\n{result.count} reference(s) must be updated before renaming.")
    print(
        "\nNext steps (AUDIT ONLY — no changes made):\n"
        "  1. Review the list above.\n"
        "  2. Update each reference manually or with a targeted script.\n"
        "  3. Open reports in Power BI Desktop and verify no broken references.\n"
        "  4. Run .\\ products\\fabric\\powerbi\\tooling\\run_fabric_checks.ps1."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=["measure", "table", "column"], required=True)
    parser.add_argument("--old-name", required=True, help="Exact current name to search for.")
    parser.add_argument("--table", default="", help="Table name (required when --type column).")
    parser.add_argument(
        "--scan-root",
        default=".",
        help="Root directory to scan (default: repository root).",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    if args.type == "column" and not args.table:
        parser.error("--table is required when --type is column")

    scan_root = (
        Path(args.scan_root)
        if Path(args.scan_root).is_absolute()
        else _REPO_ROOT / args.scan_root
    )

    result = audit(
        old_name=args.old_name,
        ref_type=args.type,
        table=args.table,
        scan_root=scan_root,
    )

    if args.json_output:
        payload = {
            "old_name": result.old_name,
            "ref_type": result.ref_type,
            "table": result.table,
            "count": result.count,
            "hits": [
                {
                    "file": str(h.file),
                    "line": h.line_number,
                    "content": h.line_content,
                    "context": h.match_context,
                }
                for h in result.hits
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_result(result, scan_root)

    return 1 if result.count else 0


if __name__ == "__main__":
    sys.exit(main())
