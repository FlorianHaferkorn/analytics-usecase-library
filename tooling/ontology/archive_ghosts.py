#!/usr/bin/env python3
"""
Move orphan action codes and use cases into _legacy_archive.

Reads tooling/ontology/out/orphans_report.json. For orphans of type action_code or use_case:
- Moves the file (action code) or directory (use case) to _legacy_archive/<rel_path>
- Preserves relative paths under _legacy_archive/
- Writes tooling/ontology/out/ghosts_move_log.json

Usage:
  py -3 tooling/ontology/archive_ghosts.py [--apply]
  Default: --dry-run (log what would be moved, no filesystem changes)
  --apply: perform the moves
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


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


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _normalize_path(p: str) -> str:
    return p.replace("\\", "/").strip()


def run(
    repo_root: Path,
    orphans_path: Path,
    archive_root: Path,
    log_path: Path,
    apply: bool,
) -> int:
    if not orphans_path.exists():
        print(f"ERROR: Orphans report not found: {orphans_path}")
        print("Run registry_builder.py first to generate orphans_report.json")
        return 1

    data = _read_json(orphans_path)
    orphans = data.get("orphans", [])

    # Skip KPI orphans (handled by extract_kpi_orphans.py)
    to_move: List[Dict[str, Any]] = []
    for o in orphans:
        ot = o.get("type")
        src = o.get("source")
        if not src or (isinstance(src, str) and not src.strip()):
            continue
        src_norm = _normalize_path(src)

        if ot == "action_code":
            # Source is a single file path
            src_path = repo_root / src_norm
            if src_path.is_file():
                to_move.append({
                    "type": "action_code",
                    "id": o.get("id", ""),
                    "source": src_norm,
                    "source_path": src_path,
                    "dest_relative": src_norm,
                })
            else:
                print(f"WARN: Orphan action code file not found: {src_path}")

        elif ot == "use_case":
            # Source is Business_Factsheet or Technical_Factsheet path; move the parent directory
            src_path = repo_root / src_norm
            if src_path.is_file():
                uc_dir = src_path.parent
                rel_dir = uc_dir.relative_to(repo_root)
                dest_rel = str(rel_dir).replace("\\", "/")
                to_move.append({
                    "type": "use_case",
                    "id": o.get("id", ""),
                    "source": dest_rel,
                    "source_path": uc_dir,
                    "dest_relative": dest_rel,
                })
            else:
                print(f"WARN: Orphan use case path not found: {src_path}")

    # Deduplicate use_case moves (same directory may appear via business and technical)
    seen: set = set()
    deduped: List[Dict[str, Any]] = []
    for m in to_move:
        key = (m["type"], m["dest_relative"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)

    if not deduped:
        print("No orphan action codes or use cases to archive.")
        return 0

    moves_log: List[Dict[str, Any]] = []
    for m in deduped:
        moves_log.append({
            "type": m["type"],
            "id": m["id"],
            "source": m["source"],
            "dest": f"_legacy_archive/{m['dest_relative']}",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        })

    if apply:
        for m in deduped:
            src = m["source_path"]
            dest = archive_root / m["dest_relative"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.move(str(src), str(dest))
            else:
                shutil.move(str(src), str(dest))
        _write_json(log_path, {"moves": moves_log})
        print(f"Moved {len(deduped)} ghost(s) to _legacy_archive/")
        print(f"Log written to {log_path.relative_to(repo_root)}")
    else:
        print("DRY-RUN: Would move the following to _legacy_archive/:")
        for m in moves_log:
            print(f"  [{m['type']}] {m['id']}: {m['source']} -> {m['dest']}")
        print("Run with --apply to perform the moves.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive orphan action codes and use cases")
    parser.add_argument("--apply", action="store_true", help="Perform moves; default is dry-run")
    parser.add_argument("--out-dir", default="tooling/ontology/out", help="Directory containing orphans_report.json and for log output")
    parser.add_argument("--repo-root", default=None, help="Repository root (default: auto-detect)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else _find_repo_root(Path.cwd())
    orphans_path = repo_root / args.out_dir / "orphans_report.json"
    archive_root = repo_root / "_legacy_archive"
    log_path = repo_root / args.out_dir / "ghosts_move_log.json"

    return run(
        repo_root=repo_root,
        orphans_path=orphans_path,
        archive_root=archive_root,
        log_path=log_path,
        apply=args.apply,
    )


if __name__ == "__main__":
    sys.exit(main())
