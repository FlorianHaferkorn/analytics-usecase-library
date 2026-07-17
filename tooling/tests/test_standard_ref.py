"""Tests for check_standard_ref — KPI↔standard alignment integrity + duplicate sensor.

Guards: (1) the whole catalog is structurally clean (every standard_ref well-formed,
standard in the controlled vocabulary); (2) coverage does not regress; (3) every
identical-calc duplicate set is either resolved by a canonical_kpi_id pointer or is a
known count-shape collision — no NEW unresolved duplicate may appear.
"""
from __future__ import annotations

from pathlib import Path

from tooling.validation.check_standard_ref import (
    check_entry,
    divergence_flags,
    duplicate_sets,
    load_kpis,
)

REPO = Path(__file__).resolve().parents[2]

# Full-catalog coverage baseline: every real KPI carries standard_ref (100%).
# Decremented as the KPI de-duplication physically removes twin KPIs (each twin
# carried a standard_ref): 127 → 126 (svc.nps.index) → 125 (ops.inventory.value.amount)
# → 124 (ops.otif.pct) → 122 (scm.service_level.pct + ops.service_level.pct)
# → 121 (ops.production.volume) → 120 (ops.yield.pct)
# → 119 (deprecated plan.replan.count removed; survivor plans.count).
_BASELINE_COVERED = 119

# Duplicate sets whose members share a count/distinctcount shape but are semantically
# distinct metrics — surfaced by the sensor for human review, intentionally NOT merged.
_KNOWN_COUNT_COLLISIONS = {
    frozenset({"order.lines", "shipments.count"}),
}


def test_pure_entry_checks():
    assert check_entry({"standard": "SCOR-DS", "alignment": "exact",
                        "id": "RL.1.1", "note": "matches the standard definition."}) == []
    # unknown standard (typo) is caught
    assert any("controlled vocabulary" in p for p in
               check_entry({"standard": "SCOR", "alignment": "none", "note": "x" * 20}))
    # exact/partial without a pointer is caught
    assert any("concrete" in p for p in
               check_entry({"standard": "IFRS", "alignment": "exact", "note": "y" * 20}))
    # missing note is caught
    assert any("note" in p for p in
               check_entry({"standard": "IFRS 15", "alignment": "none"}))
    # bad alignment is caught
    assert any("alignment" in p for p in
               check_entry({"standard": "ITIL 4", "alignment": "loose", "note": "z" * 20}))


def test_divergence_sensor():
    assert divergence_flags({"alignment": "none", "note": "Matches ours exactly."})
    assert divergence_flags({"alignment": "exact", "note": "Matches ours."}) is None


def test_catalog_is_structurally_clean():
    kpis = load_kpis()
    violations = []
    for kid, d in kpis.items():
        for i, ref in enumerate(d.get("standard_ref", []) or []):
            violations += [f"{kid}[{i}]: {p}" for p in check_entry(ref)]
    assert not violations, "standard_ref structural violations:\n" + "\n".join(violations)


def test_canonical_pointers_resolve():
    kpis = load_kpis()
    for kid, d in kpis.items():
        canon = d.get("canonical_kpi_id")
        if canon:
            assert canon in kpis, f"{kid}: canonical_kpi_id '{canon}' missing"
            assert not kpis[canon].get("canonical_kpi_id"), \
                f"{kid}: canonical '{canon}' is itself a twin (chain)"


def test_no_new_unresolved_duplicate_sets():
    kpis = load_kpis()
    unresolved = []
    for ids in duplicate_sets(kpis):
        canon = next((k for k in ids if not kpis[k].get("canonical_kpi_id")), None)
        resolved = canon is not None and all(
            kpis[k].get("canonical_kpi_id") == canon for k in ids if k != canon
        )
        if resolved or frozenset(ids) in _KNOWN_COUNT_COLLISIONS:
            continue
        unresolved.append(ids)
    assert not unresolved, (
        "new unresolved duplicate KPI set(s) — declare a canonical_kpi_id or add to "
        f"_KNOWN_COUNT_COLLISIONS after confirming distinct: {unresolved}"
    )


def test_coverage_does_not_regress():
    kpis = load_kpis()
    covered = sum(1 for d in kpis.values() if d.get("standard_ref"))
    assert covered >= _BASELINE_COVERED, (
        f"standard_ref coverage dropped below baseline ({covered} < {_BASELINE_COVERED})"
    )
