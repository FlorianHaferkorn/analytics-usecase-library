#!/usr/bin/env python3
"""
Extract KPI orphans from KPI_Catalog.md into internal/archive/tooling/kpi_orphans/kpi_catalog_orphans.yaml.

Reads tooling/ontology/out/orphans_report.json and processes each KPI orphan whose
source is core/kpi_catalog/KPI_Catalog.md. For each:
- Locates the full YAML list item chunk (- kpi_id: <id> until next - kpi_id: or fence)
- Appends to internal/archive/tooling/kpi_orphans/kpi_catalog_orphans.yaml
- Removes the chunk from KPI_Catalog.md

Writes internal/archive/tooling/kpi_orphans/kpi_catalog_orphans_move_log.json with kpi_id, source, line range, timestamp.

Usage:
  py -3 tooling/ontology/extract_kpi_orphans.py [--apply]
  Default: dry-run (log what would be done, no filesystem changes)
  --apply: perform the extract and purge
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / ".git").exists():
            return cur
        cur = cur.parent
    return start


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _locate_kpi_chunk(lines: List[str], kpi_id: str) -> Optional[Tuple[int, int]]:
    """
    Find the (start_0based, end_0based_inclusive) line range for the YAML list item
    with kpi_id. Returns None if not found or ambiguous.
    """
    pattern = re.compile(r"^-\s*kpi_id:\s*" + re.escape(kpi_id) + r"\s*$")
    matches: List[int] = []
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            matches.append(i)
    if len(matches) != 1:
        return None

    start = matches[0]
    end = start
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        stripped = ln.strip()
        if stripped.startswith("- kpi_id:"):
            end = i - 1
            break
        if stripped == "```":
            end = i - 1
            break
        end = i

    return (start, end)


def _extract_chunk(lines: List[str], start: int, end: int) -> str:
    return "".join(lines[start : end + 1])


def run(
    repo_root: Path,
    orphans_path: Path,
    catalog_path: Path,
    archive_path: Path,
    log_path: Path,
    apply: bool,
) -> int:
    if not orphans_path.exists():
        print(f"ERROR: Orphans report not found: {orphans_path}")
        print("Run registry_builder.py first to generate orphans_report.json")
        return 1

    data = _read_json(orphans_path)
    orphans = data.get("orphans", [])
    kpi_orphans = [
        o for o in orphans
        if o.get("type") == "kpi" and o.get("source", "").replace("\\", "/") == "core/kpi_catalog/KPI_Catalog.md"
    ]

    if not kpi_orphans:
        print("No KPI orphans from KPI_Catalog.md to extract.")
        return 0

    if not catalog_path.exists():
        print(f"ERROR: KPI catalog not found: {catalog_path}")
        return 1

    content = _read_text(catalog_path)
    lines = content.splitlines(keepends=True)
    # Ensure last line has newline for join
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    moves: List[Dict[str, Any]] = []
    chunks_to_remove: List[Tuple[str, int, int, str]] = []  # (kpi_id, start, end, yaml_text)

    for o in kpi_orphans:
        kpi_id = o.get("id")
        if not kpi_id:
            continue
        loc = _locate_kpi_chunk(lines, kpi_id)
        if loc is None:
            print(f"ERROR: Could not uniquely locate KPI chunk for {kpi_id} (ambiguous or not found)")
            return 1
        start, end = loc
        chunk = _extract_chunk(lines, start, end)
        # Include trailing blank line in removal if present
        removal_end = end
        if end + 1 < len(lines) and lines[end + 1].strip() == "":
            removal_end = end + 1
        chunks_to_remove.append((kpi_id, start, removal_end, chunk))
        moves.append({
            "kpi_id": kpi_id,
            "source": str(catalog_path.relative_to(repo_root)),
            "line_start": start + 1,
            "line_end": end + 1,
            "removal_end": removal_end + 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        })

    if apply:
        # Append to archive (create file with header if new); preserve exact YAML content
        archive_content: List[str] = []
        if archive_path.exists():
            archive_content.append(_read_text(archive_path))
            if not archive_content[0].endswith("\n\n"):
                archive_content.append("\n")
        else:
            archive_content.append("# KPI catalog orphans (extracted from KPI_Catalog.md)\n")
            archive_content.append("# These KPIs were not referenced by any active UseCase_Bracket or subscribed Action Code.\n\n")

        for _, _, _, chunk in chunks_to_remove:
            archive_content.append(chunk.rstrip())
            archive_content.append("\n\n")

        _write_text(archive_path, "".join(archive_content))

        # Remove chunks from catalog (process in reverse order to preserve indices)
        for kpi_id, start, removal_end, _ in sorted(chunks_to_remove, key=lambda x: -x[1]):
            del lines[start : removal_end + 1]

        _write_text(catalog_path, "".join(lines))

        _write_text(log_path, json.dumps({"moves": moves}, indent=2))

        print(f"Extracted {len(moves)} KPI orphan(s) to {archive_path.relative_to(repo_root)}")
        print(f"Log written to {log_path.relative_to(repo_root)}")
    else:
        print("DRY-RUN: Would extract the following KPI orphans:")
        for m in moves:
            print(f"  - {m['kpi_id']} (lines {m['line_start']}-{m['line_end']})")
        print("Run with --apply to perform the extraction.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract KPI orphans from KPI_Catalog.md into internal/archive/tooling/kpi_orphans")
    parser.add_argument("--apply", action="store_true", help="Perform extraction; default is dry-run")
    parser.add_argument("--out-dir", default="tooling/ontology/out", help="Directory containing orphans_report.json")
    parser.add_argument("--repo-root", default=None, help="Repository root (default: auto-detect)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else _find_repo_root(Path.cwd())
    orphans_path = repo_root / args.out_dir / "orphans_report.json"
    catalog_path = repo_root / "core" / "kpi_catalog" / "KPI_Catalog.md"
    archive_path = repo_root / "internal" / "archive" / "tooling" / "kpi_orphans" / "kpi_catalog_orphans.yaml"
    log_path = repo_root / "internal" / "archive" / "tooling" / "kpi_orphans" / "kpi_catalog_orphans_move_log.json"

    return run(
        repo_root=repo_root,
        orphans_path=orphans_path,
        catalog_path=catalog_path,
        archive_path=archive_path,
        log_path=log_path,
        apply=args.apply,
    )


if __name__ == "__main__":
    sys.exit(main())
