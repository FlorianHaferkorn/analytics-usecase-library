#!/usr/bin/env python3
"""
check_evidence_sort.py — Boutique rubric BC-CHART-10 structural validator (knock-out)

Enforces "evidence tables sorted by most-relevant / worst-first with an explicit
Top-N" (Boutique-Craft-Rubric BC-CHART-10, Craft-Core §5.4 / R1.3 curated evidence).
The 300-second evidence matrix (component_300s) must declare a governed worst-first
ordering so the reader scans the rows that matter first, not an arbitrary or
alphabetical order — and an explicit Top-N cap so the scan is bounded.

Governed as data (like BC-NARR-01's `message` and BC-NARR-04's `comparison`): the
sort key + direction + Top-N live in the bracket, not in prose comments or a
hard-coded generator default. A future generator-emit cut wires `evidence_sort`
into the Detail_Matrix `sortDefinition` and `evidence_top_n` into its Top-N filter
(needs PBIR/Windows validation — the K3 pattern).

BC-CHART-10 is a knock-out. Rollout is curated (the worst-first column + direction
is a per-domain call: asc when low is worse, desc when high is worse), so the gate
runs advisory by default with a coverage-regression guard
(tooling/tests/test_evidence_sort.py) and turns hard with --strict once the backlog
is cleared — the BC-NARR-01 → BC-CHART-01 ratchet.

Usage:
    python tooling/validation/check_evidence_sort.py            # all use cases
    python tooling/validation/check_evidence_sort.py COM-002     # single use case
    python tooling/validation/check_evidence_sort.py --strict    # missing/invalid = exit 1

Exit codes:
    0 — always (advisory), unless --strict and an evidence table lacks valid ordering
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

REPO = Path(__file__).resolve().parents[2]

_VALID_DIRECTIONS = {"asc", "desc"}


def classify_evidence(c300: Optional[dict[str, Any]]) -> tuple[Optional[bool], str]:
    """Classify a component_300s evidence table's worst-first ordering.

    Returns (True, "")            — valid: sort column ∈ evidence_columns, valid
                                     direction, explicit Top-N.
            (False, reason)       — declared but invalid, or missing entirely.
            (None, "")            — no evidence table on this page (not applicable).

    Pure function — unit-tested in tooling/tests/test_evidence_sort.py.
    """
    if not isinstance(c300, dict) or not c300:
        return None, ""

    columns = c300.get("evidence_columns")
    columns = columns if isinstance(columns, list) else []
    srt = c300.get("evidence_sort")
    top_n = c300.get("evidence_top_n")

    if not isinstance(srt, dict):
        return False, "no evidence_sort declared (worst-first ordering ungoverned)"
    column = srt.get("column")
    direction = srt.get("direction")
    if not column:
        return False, "evidence_sort.column missing"
    if column not in columns:
        return False, f"evidence_sort.column '{column}' is not one of evidence_columns"
    if direction not in _VALID_DIRECTIONS:
        return False, f"evidence_sort.direction '{direction}' not in {sorted(_VALID_DIRECTIONS)}"
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        return False, "evidence_top_n missing or not a positive integer"
    return True, ""


def _c300(bracket: dict[str, Any]) -> Optional[dict[str, Any]]:
    page = (bracket.get("ux_layout_rules", {}) or {}).get("page_2_execution", {}) or {}
    c = page.get("component_300s")
    return c if isinstance(c, dict) and c else None


def check_bracket(path: Path) -> tuple[Optional[bool], str]:
    """Return (True valid / False invalid / None no-evidence-table, reason)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return classify_evidence(_c300(data))


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-CHART-10 evidence-sort validator")
    parser.add_argument("use_case_id", nargs="?", help="Validate a single use case by ID substring")
    parser.add_argument("--strict", action="store_true", help="Missing/invalid ordering = exit 1")
    args = parser.parse_args()

    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    if args.use_case_id:
        brackets = [b for b in brackets if args.use_case_id.lower() in str(b).lower()]
        if not brackets:
            print(f"No UseCase_Bracket.yaml found matching '{args.use_case_id}'", file=sys.stderr)
            return 1

    valid = invalid = 0
    for b in brackets:
        res, reason = check_bracket(b)
        if res is None:
            continue
        if res:
            valid += 1
        else:
            invalid += 1
            print(f"    ⚠ {b.parent.name.split('_')[0]}: {reason} — BC-CHART-10")

    total = valid + invalid
    print(f"\nBC-CHART-10: {valid}/{total} evidence tables sorted worst-first with Top-N, "
          f"{invalid} advisory.")
    if args.strict and invalid:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
