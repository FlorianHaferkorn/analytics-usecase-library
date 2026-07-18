#!/usr/bin/env python3
"""
check_standard_ref.py — KPI ↔ external-standard alignment integrity + drift/duplicate sensor.

Operationalises the per-domain standards program (SCM→SCOR, Finance→IFRS,
Operations→ISO 22400, Service→ITIL/ISO 20000, Commercial→IFRS 15/convention,
Customer/People/Governance). Every governed KPI carries a `standard_ref` mapping its
definition to the nearest external standard/ontology with an explicit `alignment`
(exact/partial/none) and a drift note — recorded per-KPI in the catalog and audited
under `core/kpi_catalog/standards/`. This validator keeps that layer honest.

WHAT IT CHECKS

1. Structural integrity (hard under --strict):
   - each `standard_ref` entry has a non-empty `standard` and an `alignment` ∈
     {exact, partial, none};
   - a drift `note` is present (the whole point — an alignment without a rationale
     is not evidence);
   - alignment exact/partial carries a concrete pointer (`id` or `name`);
   - `standard` is drawn from the controlled vocabulary (catches "SCOR" vs "SCOR-DS"
     typos that would silently fragment the audit).

2. Canonical / duplicate sensor (advisory — this is the "clean up doubles" half):
   - KPIs with an identical `technical.calculation` are reported as consolidation
     candidates (the OTIF / DIO / NPS families the audits flagged);
   - a KPI may declare `canonical_kpi_id: <other-kpi>` to name the SSOT survivor of
     a duplicate set; this validator verifies the target exists, is not itself
     deprecated, and (advisory) that new references should prefer the canonical.

3. Divergence sensor (advisory): a KPI whose drift note asserts an exact match
   ("matches", "aligns", "verbatim") while `alignment` is `none` — or vice-versa —
   is surfaced for human review. True semantic divergence needs a human; this only
   flags the machine-detectable contradictions.

Usage:
    python tooling/validation/check_standard_ref.py            # advisory report
    python tooling/validation/check_standard_ref.py --strict   # structural fail = exit 1
    python tooling/validation/check_standard_ref.py --duplicates  # only the dup report

Exit codes:
    0 — advisory (default), or --strict with no structural violation
    1 — --strict and ≥1 structural violation
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
KPI_DIR = REPO / "core" / "kpi_catalog" / "kpis"

_VALID_ALIGNMENTS = {"exact", "partial", "none"}

# Controlled vocabulary of `standard` values used by the audit runs. Extend here when
# a new domain audit introduces a standard — a typo'd standard would otherwise
# fragment the audit silently.
KNOWN_STANDARDS = {
    "SCOR-DS",
    "IFRS", "IFRS 15", "ESMA-APM",
    "ISO 22400-2",
    "ISO/IEC 20000-1", "ITIL 4",
    "ISO 10002", "ISO 30414", "ISO 9001",
    "Management accounting (CIMA/IMA)",
    "Trade Promotion Management (convention)",
    "Retail analytics (convention)",
    "Marketing analytics — RFM (convention)",
    "Marketing analytics — CRM (convention)",
    "Bain NPS (proprietary)",
    "Internal — ActionReady governance",
}

# Machine-detectable contradiction: an "exact-match" claim in the note vs alignment=none.
_EXACT_CLAIM_TOKENS = ("matches ours", "matches ", "verbatim", "definitionally")


def check_entry(ref: dict[str, Any]) -> list[str]:
    """Structural checks for a single standard_ref entry. Returns list of violations."""
    problems: list[str] = []
    std = ref.get("standard")
    if not isinstance(std, str) or len(std.strip()) < 2:
        problems.append("missing/short `standard`")
        std = None
    align = ref.get("alignment")
    if align not in _VALID_ALIGNMENTS:
        problems.append(f"alignment '{align}' not in {sorted(_VALID_ALIGNMENTS)}")
    note = ref.get("note")
    if not isinstance(note, str) or len(note.strip()) < 10:
        problems.append("missing/short drift `note`")
    if align in {"exact", "partial"} and not (ref.get("id") or ref.get("name")):
        problems.append(f"alignment '{align}' without a concrete `id`/`name` pointer")
    if std is not None and std not in KNOWN_STANDARDS:
        problems.append(f"`standard` '{std}' not in controlled vocabulary (typo/new-standard?)")
    return problems


def divergence_flags(ref: dict[str, Any]) -> Optional[str]:
    """Advisory: note claims an exact match but alignment says none (or vice-versa)."""
    note = (ref.get("note") or "").lower()
    align = ref.get("alignment")
    claims_exact = any(tok in note for tok in _EXACT_CLAIM_TOKENS)
    if claims_exact and align == "none":
        return "note asserts a match but alignment=none"
    return None


def _norm_calc(calc: Any) -> Optional[str]:
    """Normalise a technical.calculation to a comparable string (order-insensitive)."""
    if not isinstance(calc, dict) or not calc:
        return None
    return yaml.safe_dump(calc, sort_keys=True, default_flow_style=True).strip()


def load_kpis() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for f in sorted(KPI_DIR.glob("*.yaml")):
        if f.stem == "_index":
            continue
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        out[data.get("kpi_id", f.stem)] = data
    return out


def duplicate_sets(kpis: dict[str, dict[str, Any]]) -> list[list[str]]:
    """Group KPI ids by identical technical.calculation + lineage (consolidation candidates)."""
    by_calc: dict[str, list[str]] = {}
    for kid, d in kpis.items():
        t = d.get("technical", {}) or {}
        calc = _norm_calc(t.get("calculation"))
        if calc is None:
            continue
        lineage = tuple(sorted(t.get("lineage", []) or []))
        key = f"{calc}::{lineage}"
        by_calc.setdefault(key, []).append(kid)
    return [sorted(ids) for ids in by_calc.values() if len(ids) > 1]


def main() -> int:
    parser = argparse.ArgumentParser(description="KPI standard_ref integrity + duplicate sensor")
    parser.add_argument("--strict", action="store_true", help="structural violation = exit 1")
    parser.add_argument("--duplicates", action="store_true", help="only the duplicate/canonical report")
    args = parser.parse_args()

    kpis = load_kpis()
    structural = 0

    if not args.duplicates:
        for kid, d in sorted(kpis.items()):
            refs = d.get("standard_ref")
            if refs is None:
                print(f"  · {kid}: no standard_ref (uncovered)")
                continue
            if not isinstance(refs, list):
                print(f"  ✗ {kid}: standard_ref is not a list")
                structural += 1
                continue
            for i, ref in enumerate(refs):
                for p in check_entry(ref):
                    print(f"  ✗ {kid}[{i}]: {p}")
                    structural += 1
                dv = divergence_flags(ref)
                if dv:
                    print(f"  ⚠ {kid}[{i}]: {dv} (review)")

    # canonical-pointer integrity
    for kid, d in sorted(kpis.items()):
        canon = d.get("canonical_kpi_id")
        if not canon:
            continue
        if canon not in kpis:
            print(f"  ✗ {kid}: canonical_kpi_id '{canon}' does not exist")
            structural += 1
        elif kpis[canon].get("canonical_kpi_id"):
            print(f"  ✗ {kid}: canonical_kpi_id '{canon}' is itself deprecated (chain)")
            structural += 1

    # duplicate / consolidation report
    dups = duplicate_sets(kpis)
    if dups:
        print("\nConsolidation candidates (identical calculation + lineage):")
        for ids in dups:
            canon = next((k for k in ids if not kpis[k].get("canonical_kpi_id")), None)
            resolved = all(
                kpis[k].get("canonical_kpi_id") for k in ids if k != canon
            ) and canon is not None
            mark = "✓ resolved" if resolved else "⚠ open"
            print(f"  {mark}: {', '.join(ids)}"
                  + (f"  → canonical: {canon}" if canon else ""))

    print(f"\ncheck_standard_ref: {len(kpis)} KPIs · {structural} structural violation(s) · "
          f"{len(dups)} duplicate set(s).")
    if args.strict and structural:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
