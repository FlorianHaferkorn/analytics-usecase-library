#!/usr/bin/env python3
"""GADW gate — run ALUCA's always-on Tier-0 gates in one command.

Bundles the Guided Agent Development Workflow's deterministic, offline gates
(see docs/agent/guided-agent-development-workflow.md):

  - Navigation         index drift-gate (scripts/check_index.py --strict)
  - Stage 0            use-case contract (aluca preflight)
  - Stage 4            report-quality Tier-0 floor (pbi-quality validate)

Each gate runs isolated; a per-stage PASS/FAIL summary is printed and the exit
code is non-zero if any gate fails. This is the fast dev-loop gate — the full
Stage-1 governance + Fabric quality gate (PowerShell) remains the heavier CI gate.

Usage:  python3 scripts/gadw_gate.py [--verbose]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# pbi-quality ships as a package under packages/; invoke its CLI without install.
_PBI_QUALITY = (
    "import sys; sys.path.insert(0, 'packages/pbi_quality_tools'); "
    "from pbi_quality_tools.cli import main; "
    "raise SystemExit(main(['validate', '--summary']))"
)


@dataclass(frozen=True)
class Gate:
    stage: str
    description: str
    argv: list[str]


GATES: list[Gate] = [
    Gate(
        "Navigation",
        "index drift-gate (_INDEX.md completeness)",
        [sys.executable, "scripts/check_index.py", "--strict"],
    ),
    Gate(
        "Stage 0 — Use Case",
        "aluca preflight (KPI catalog / Golden Thread)",
        [sys.executable, "-m", "aluca", "preflight"],
    ),
    Gate(
        "Stage 4 — Validate",
        "pbi-quality report-quality Tier-0 floor",
        [sys.executable, "-c", _PBI_QUALITY],
    ),
]


def run_gate(gate: Gate, *, verbose: bool) -> bool:
    """Run one gate from the repo root; return True on success (exit code 0)."""
    proc = subprocess.run(
        gate.argv,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8", errors="replace")
    ok = proc.returncode == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {gate.stage:<20} {gate.description}")
    if verbose or not ok:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-8:]
        for line in tail:
            print(f"        {line}")
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ALUCA's always-on GADW gates.")
    parser.add_argument("--verbose", action="store_true", help="show each gate's output")
    args = parser.parse_args(argv)

    print("GADW gate — always-on Tier-0 checks\n")
    results = [run_gate(g, verbose=args.verbose) for g in GATES]
    passed, total = sum(results), len(results)
    print(f"\n{passed}/{total} gates passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
