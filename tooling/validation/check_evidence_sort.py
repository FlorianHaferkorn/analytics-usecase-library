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
import datetime as dt
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

_VALID_DIRECTIONS = {"ascending", "descending"}

# ADR-0027 (Accepted 24.10.2026): eine begruendete Ausnahme statt eines wirkungslosen Top-N.
# Obergrenze kleine Koernung = untere Kante der Detail-Matrix-Empfehlung (Design_Spec_3_30_300, 50-100).
_MAX_ZEILEN_KLEINE_KOERNUNG = 50
_AUSNAHME_MAX_ALTER_TAGE = 180


def _pruefe_ausnahme(ausnahme: Any, visual_type: str) -> tuple[bool, str]:
    """``top_n_ausnahme`` gegen ihre Klasse pruefen (ADR-0027 §3, Regeln 1-2)."""
    if not isinstance(ausnahme, dict):
        return False, "top_n_ausnahme is not a mapping"
    fehlend = [k for k in ("klasse", "gemessene_zeilen", "gemessen_am", "quelle") if ausnahme.get(k) in (None, "")]
    if fehlend:
        return False, f"top_n_ausnahme missing {fehlend}"
    zeilen = ausnahme["gemessene_zeilen"]
    if not isinstance(zeilen, int) or isinstance(zeilen, bool) or zeilen < 0:
        return False, "top_n_ausnahme.gemessene_zeilen not a non-negative integer"
    try:
        dt.date.fromisoformat(str(ausnahme["gemessen_am"]))
    except ValueError:
        return False, f"top_n_ausnahme.gemessen_am '{ausnahme['gemessen_am']}' not an ISO date"
    klasse = ausnahme["klasse"]
    if klasse == "kleine_koernung":
        if zeilen > _MAX_ZEILEN_KLEINE_KOERNUNG:
            return False, (f"kleine_koernung needs <= {_MAX_ZEILEN_KLEINE_KOERNUNG} rows, "
                           f"measured {zeilen} — use top_n")
        return True, ""
    if klasse == "matrix_zwischensummen":
        if visual_type != "matrix":
            return False, f"matrix_zwischensummen needs visual_type matrix, got '{visual_type}'"
        return True, ""
    return False, f"top_n_ausnahme.klasse '{klasse}' unknown"


def ausnahme_veraltet(c300: Optional[dict[str, Any]], heute: dt.date | None = None) -> Optional[str]:
    """Warnung (nicht rot), wenn die Messung einer Ausnahme aelter als 180 Tage ist (Regel 3)."""
    ausnahme = (c300 or {}).get("top_n_ausnahme")
    if not isinstance(ausnahme, dict):
        return None
    try:
        gemessen = dt.date.fromisoformat(str(ausnahme.get("gemessen_am")))
    except ValueError:
        return None
    alter = ((heute or dt.date.today()) - gemessen).days
    return f"top_n_ausnahme measured {alter} days ago — re-measure" if alter > _AUSNAHME_MAX_ALTER_TAGE else None


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

    # R2.1 canonical fields (loving-einstein merge 2026-07-16): the governed
    # worst-first ordering is `sort_by {measure, direction}` + `top_n`. (Superseded
    # my earlier `evidence_sort {column, direction}` + `evidence_top_n`.)
    srt = c300.get("sort_by")
    top_n = c300.get("top_n")

    if not isinstance(srt, dict):
        return False, "no sort_by declared (worst-first ordering ungoverned)"
    measure = srt.get("measure")
    direction = srt.get("direction")
    if not measure:
        return False, "sort_by.measure missing"
    if direction not in _VALID_DIRECTIONS:
        return False, f"sort_by.direction '{direction}' not in {sorted(_VALID_DIRECTIONS)}"
    ausnahme = c300.get("top_n_ausnahme")
    if ausnahme is not None:
        if top_n is not None:
            return False, "top_n and top_n_ausnahme both set"
        return _pruefe_ausnahme(ausnahme, c300.get("visual_type", "table"))
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        return False, "top_n missing or not a positive integer (or a top_n_ausnahme, ADR-0027)"
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
            warnung = ausnahme_veraltet(_c300(yaml.safe_load(b.read_text(encoding="utf-8")) or {}))
            if warnung:
                print(f"    ⚠ {b.parent.name.split('_')[0]}: {warnung} — BC-CHART-10 (warning)")
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
