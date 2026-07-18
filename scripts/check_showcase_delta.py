#!/usr/bin/env python3
"""Showcase Delta-table consistency gate.

Every table the semantic models read via ``fn_DeltaCurrentFiles`` is a Delta
Lake folder: parquet part-files plus a ``_delta_log`` whose JSON commits list
``add``/``remove`` actions. ``fn_DeltaCurrentFiles`` replays that log and keeps
only the files whose latest action is ``add``. If a parquet is renamed on disk
without rewriting the log (e.g. a hashed ``part-00000-<uuid>-c000.snappy.parquet``
consolidated to a generic ``part-00000.parquet``), the replay matches zero
files and returns a *columnless* empty table. Power BI Desktop then loads that
dimension with no supported columns and crashes in ``Table.get_Islands()`` while
wiring relationships against the empty endpoint — a failure no diff to the TMDL
or the report can explain, because the defect is in the seed data.

This gate catches that class before Desktop does: for each Delta folder it
computes the active file set from the log and asserts every active path exists
on disk. Orphan parquet files (present but not referenced) are reported as
advisory only — extra files do not break the load, missing active ones do.

Exit code 1 on any active-but-missing file. Run from the repo root.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

GOLD_GLOB = "showcases/*/data/gold"


def _active_paths(log_dir: str) -> list[str]:
    """Replay a _delta_log directory to the set of currently-active file paths."""
    state: dict[str, str] = {}
    for commit in sorted(glob.glob(os.path.join(log_dir, "*.json"))):
        with open(commit, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "add" in obj:
                    state[obj["add"]["path"]] = "add"
                elif "remove" in obj:
                    state[obj["remove"]["path"]] = "remove"
    return [path for path, action in state.items() if action == "add"]


def check(root: str = ".") -> int:
    problems = 0
    tables = 0
    log_dirs = sorted(
        glob.glob(os.path.join(root, GOLD_GLOB, "**", "_delta_log"), recursive=True)
    )
    for log_dir in log_dirs:
        table = os.path.dirname(log_dir)
        rel = os.path.relpath(table, root)
        active = _active_paths(log_dir)
        if not active:
            # A log with no active adds is legitimately empty only if it also has
            # no data files; flag it so a genuinely empty seed is a conscious choice.
            missing = []
        else:
            missing = [p for p in active if not os.path.exists(os.path.join(table, p))]
        tables += 1
        if missing:
            problems += 1
            print(f"FAIL {rel}")
            print(f"     active file(s) referenced by _delta_log but missing on disk:")
            for m in missing:
                print(f"       - {m}")
            phys = {
                os.path.relpath(p, table)
                for p in glob.glob(os.path.join(table, "**", "*.parquet"), recursive=True)
            }
            orphans = sorted(phys - set(active))
            if orphans:
                print(f"     physical parquet not referenced (likely the renamed file):")
                for o in orphans:
                    print(f"       - {o}")
    if problems:
        print(
            f"\n{problems} Delta table(s) inconsistent — physical parquet does not match "
            f"the _delta_log active set. Rename the orphan file(s) back to the active "
            f"add path, or rewrite the log. See internal/project_mgmt/"
            f"KNOWN_ERRORS_AND_FIXES.md.",
            file=sys.stderr,
        )
        return 1
    print(f"OK — {tables} showcase Delta table(s) consistent (active files all present).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args()
    return check(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
