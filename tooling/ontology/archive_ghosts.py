#!/usr/bin/env python3
"""
Core-Wide Allowlist Ghost Archiver
===================================

Scans everything under core/ and archives files/directories that are:
1. NOT on the allowlist (always kept)
2. NOT reachable from the active set (brackets, referenced KPIs, referenced action codes)

Allowlist (always kept):
- core/strategy_operating_model/**
- core/templates/**
- core/semantic_models/**
- core/implementation_guides/**
- core/kpi_catalog/**
- core/data_contracts/**
- core/usecases/templates/**
- core/organization/**
- core/README.md
- core/agents/**

Active set (kept if referenced):
- core/usecases/core/<UC-DIR>/ — kept if bracket exists in registry active set
- core/action_codes/<DOMAIN>/<AC-FILE> — kept if action code ID in registry active set

Everything else under core/ is eligible for archiving.

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
from typing import Any, Dict, List, Set


ALLOWLIST_PREFIXES = [
    "core/strategy_operating_model/",
    "core/templates/",
    "core/semantic_models/",
    "core/implementation_guides/",
    "core/kpi_catalog/",
    "core/data_contracts/",
    "core/usecases/templates/",
    "core/organization/",
    "core/agents/",
]

ALLOWLIST_FILES = [
    "core/README.md",
    "core/usecases/README.md",
    "core/usecases/usecase_DoD_Core.md",
    "core/usecases/UseCase_Inventory.md",
    "core/usecases/core/README.md",
    "core/action_codes/README.md",
]


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
        json.dump(data, f, indent=2, ensure_ascii=False)


def _normalize(p: str) -> str:
    return p.replace("\\", "/").strip()


def _is_allowlisted(rel_path: str) -> bool:
    """Check if a path is on the static allowlist."""
    norm = _normalize(rel_path)
    if norm in ALLOWLIST_FILES:
        return True
    for prefix in ALLOWLIST_PREFIXES:
        if norm.startswith(prefix):
            return True
    return False


def load_active_set(orphans_path: Path) -> tuple[Set[str], Set[str]]:
    """
    Load active use case IDs and action code IDs from orphans_report.json.
    Active = total set minus orphans.
    We derive active IDs from the report's meta.active_use_cases.
    """
    active_uc_ids: Set[str] = set()
    orphan_action_ids: Set[str] = set()
    orphan_uc_ids: Set[str] = set()

    if not orphans_path.exists():
        return active_uc_ids, orphan_action_ids

    data = _read_json(orphans_path)
    meta = data.get("meta", {})
    active_uc_ids = set(meta.get("active_use_cases", []))

    for o in data.get("orphans", []):
        ot = o.get("type")
        oid = o.get("id", "")
        if ot == "action_code":
            orphan_action_ids.add(oid)
        elif ot == "use_case":
            orphan_uc_ids.add(oid)

    return active_uc_ids, orphan_action_ids


def scan_core_for_ghosts(
    repo_root: Path,
    active_uc_ids: Set[str],
    orphan_action_ids: Set[str],
) -> List[Dict[str, Any]]:
    """Scan core/ and identify files/directories to archive."""
    core_root = repo_root / "core"
    if not core_root.exists():
        return []

    to_archive: List[Dict[str, Any]] = []
    processed_dirs: Set[str] = set()

    # 1. Check use case directories
    uc_core = core_root / "usecases" / "core"
    if uc_core.exists():
        for uc_dir in sorted(uc_core.iterdir()):
            if not uc_dir.is_dir():
                continue
            rel = _normalize(str(uc_dir.relative_to(repo_root)))
            if _is_allowlisted(rel):
                continue
            # Extract UC ID from folder name (e.g. COM-001_Sales_Performance -> COM-001)
            dir_name = uc_dir.name
            uc_id = dir_name.split("_")[0] if "_" in dir_name else dir_name
            if uc_id not in active_uc_ids:
                to_archive.append({
                    "type": "use_case_dir",
                    "id": uc_id,
                    "source": rel,
                    "source_path": uc_dir,
                })
                processed_dirs.add(str(uc_dir))

    # 2. Check action code files
    ac_root = core_root / "action_codes"
    if ac_root.exists():
        for ac_file in sorted(ac_root.rglob("*.yaml")):
            if "decision_spines" in ac_file.parts:
                continue
            rel = _normalize(str(ac_file.relative_to(repo_root)))
            if _is_allowlisted(rel):
                continue
            # Extract action code ID from file
            ac_id = ac_file.stem
            if ac_id in orphan_action_ids:
                to_archive.append({
                    "type": "action_code",
                    "id": ac_id,
                    "source": rel,
                    "source_path": ac_file,
                })

    # 3. Check remaining files under core/ that aren't allowlisted or in known structures
    for item in sorted(core_root.rglob("*")):
        if not item.is_file():
            continue
        rel = _normalize(str(item.relative_to(repo_root)))
        if _is_allowlisted(rel):
            continue
        # Skip if already covered by use case dir or action code
        if any(str(item).startswith(d) for d in processed_dirs):
            continue
        # Skip if in usecases/core/ (handled above as directories)
        if rel.startswith("core/usecases/core/"):
            continue
        # Skip action codes (handled above)
        if rel.startswith("core/action_codes/") and rel.endswith(".yaml"):
            continue
        # Skip decision spines
        if "decision_spines" in rel:
            continue
        # This is a loose file under core/ — check if allowlisted
        # If we get here, it's not allowlisted and not in a known structure
        # Only archive known dead files, not unknown ones (conservative)

    return to_archive


def run(
    repo_root: Path,
    orphans_path: Path,
    archive_root: Path,
    log_path: Path,
    apply: bool,
) -> int:
    active_uc_ids, orphan_action_ids = load_active_set(orphans_path)

    if not active_uc_ids and not orphan_action_ids:
        if not orphans_path.exists():
            print(f"ERROR: Orphans report not found: {orphans_path}")
            print("Run registry_builder.py first to generate orphans_report.json")
            return 1
        print("No active set or orphan info found. Nothing to archive.")
        return 0

    to_archive = scan_core_for_ghosts(repo_root, active_uc_ids, orphan_action_ids)

    if not to_archive:
        print("No ghosts found. Everything under core/ is either allowlisted or active.")
        return 0

    moves_log: List[Dict[str, Any]] = []
    for m in to_archive:
        dest_rel = f"internal/archive/tooling/ghosts/{m['source']}"
        moves_log.append({
            "type": m["type"],
            "id": m["id"],
            "source": m["source"],
            "dest": dest_rel,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        })

    if apply:
        for m in to_archive:
            src = m["source_path"]
            dest = archive_root / m["source"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                if dest.exists():
                    shutil.rmtree(str(dest))
                shutil.move(str(src), str(dest))
            elif src.is_file():
                shutil.move(str(src), str(dest))
        _write_json(log_path, {"moves": moves_log, "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "active_use_cases": sorted(active_uc_ids),
            "orphan_action_codes": sorted(orphan_action_ids),
        }})
        print(f"Archived {len(to_archive)} ghost(s) to internal/archive/tooling/ghosts/")
        print(f"Log written to {log_path.relative_to(repo_root)}")
    else:
        print("DRY-RUN: Would archive the following to internal/archive/tooling/ghosts/:")
        for m in moves_log:
            print(f"  [{m['type']}] {m['id']}: {m['source']} -> {m['dest']}")
        print(f"\nTotal: {len(to_archive)} item(s)")
        print("Run with --apply to perform the moves.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Core-wide allowlist ghost archiver")
    parser.add_argument("--apply", action="store_true", help="Perform moves; default is dry-run")
    parser.add_argument("--out-dir", default="tooling/ontology/out",
                        help="Directory containing orphans_report.json and for log output")
    parser.add_argument("--repo-root", default=None, help="Repository root (default: auto-detect)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else _find_repo_root(Path.cwd())
    orphans_path = repo_root / args.out_dir / "orphans_report.json"
    archive_root = repo_root / "internal" / "archive" / "tooling" / "ghosts"
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
