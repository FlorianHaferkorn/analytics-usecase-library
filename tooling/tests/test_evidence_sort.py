"""Tests for the BC-CHART-10 evidence-sort validator (knock-out structural rule).

Covers the pure classifier and a coverage regression guard (governed worst-first
evidence ordering may only increase, never regress) — mirrors test_kpi_context.py.
"""
from __future__ import annotations

from pathlib import Path

import datetime as dt

from tooling.validation.check_evidence_sort import (
    ausnahme_veraltet,
    check_bracket,
    classify_evidence,
)

REPO = Path(__file__).resolve().parents[2]

# Baseline coverage: evidence tables that declare a valid worst-first sort + Top-N.
# Full rollout 2026-07-11 — all 17 evidence tables governed (COM-002 pilot + 16
# backlog). This guard only ratchets up — coverage must never drop below the baseline.
_BASELINE_COVERED = 17


def test_valid_ordering():
    # R2.1 canonical fields: sort_by {measure, direction} + top_n (ascending/descending).
    ok, _ = classify_evidence({
        "evidence_columns": ["sku", "KPI-FIN-017"],
        "sort_by": {"measure": "KPI-FIN-017", "direction": "ascending"},
        "top_n": 20,
    })
    assert ok is True


def test_missing_sort_is_invalid():
    ok, reason = classify_evidence({"evidence_columns": ["sku"]})
    assert ok is False and "sort_by" in reason


def test_missing_measure_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "KPI-COM-013"],
        "sort_by": {"direction": "ascending"},
        "top_n": 20,
    })
    assert ok is False and "measure" in reason


def test_bad_direction_is_invalid():
    ok, reason = classify_evidence({
        "evidence_columns": ["sku", "KPI-COM-013"],
        "sort_by": {"measure": "KPI-COM-013", "direction": "sideways"},
        "top_n": 20,
    })
    assert ok is False and "direction" in reason


def test_missing_or_bad_top_n_is_invalid():
    base = {
        "evidence_columns": ["sku", "KPI-COM-013"],
        "sort_by": {"measure": "KPI-COM-013", "direction": "descending"},
    }
    assert classify_evidence(base)[0] is False                      # missing
    assert classify_evidence({**base, "top_n": 0})[0] is False   # < 1
    assert classify_evidence({**base, "top_n": True})[0] is False  # bool, not int


_SORT = {"measure": "KPI-SVC-009", "direction": "descending"}


def _ausnahme(klasse: str = "kleine_koernung", zeilen: int = 32) -> dict:
    return {"klasse": klasse, "gemessene_zeilen": zeilen, "gemessen_am": "2026-10-24",
            "quelle": "fact_workforce_management (Gold, pandas)", "fakt": "fact_workforce_management"}


def test_ausnahme_kleine_koernung_is_valid():
    # ADR-0027: a measured small grain replaces top_n.
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": _ausnahme()})[0] is True


def test_ausnahme_kleine_koernung_over_limit_is_invalid():
    ok, reason = classify_evidence({"sort_by": _SORT, "top_n_ausnahme": _ausnahme(zeilen=51)})
    assert ok is False and "50" in reason


def test_ausnahme_matrix_only_for_matrix():
    c300 = {"sort_by": _SORT, "top_n_ausnahme": _ausnahme("matrix_zwischensummen", 40)}
    assert classify_evidence(c300)[0] is False                               # default table
    assert classify_evidence({**c300, "visual_type": "matrix"})[0] is True


def test_ausnahme_and_top_n_together_is_invalid():
    ok, reason = classify_evidence({"sort_by": _SORT, "top_n": 20, "top_n_ausnahme": _ausnahme()})
    assert ok is False and "both" in reason


def test_ausnahme_incomplete_or_unknown_class_is_invalid():
    unvollstaendig = {k: v for k, v in _ausnahme().items() if k != "quelle"}
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": unvollstaendig})[0] is False
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": _ausnahme("gross")})[0] is False
    falsches_datum = {**_ausnahme(), "gemessen_am": "24.10.2026"}
    assert classify_evidence({"sort_by": _SORT, "top_n_ausnahme": falsches_datum})[0] is False


def test_ausnahme_still_needs_sort():
    assert classify_evidence({"top_n_ausnahme": _ausnahme()})[0] is False


def test_ausnahme_veraltet_warns_after_180_days():
    c300 = {"sort_by": _SORT, "top_n_ausnahme": _ausnahme()}
    assert ausnahme_veraltet(c300, heute=dt.date(2027, 4, 22)) is None      # 180 Tage
    assert "181" in (ausnahme_veraltet(c300, heute=dt.date(2027, 4, 23)) or "")
    assert ausnahme_veraltet({"sort_by": _SORT, "top_n": 20}) is None


def test_no_evidence_table_is_not_applicable():
    assert classify_evidence(None) == (None, "")
    assert classify_evidence({}) == (None, "")


def test_coverage_does_not_regress():
    covered = sum(
        1 for b in REPO.glob("core/usecases/**/UseCase_Bracket.yaml")
        if check_bracket(b)[0] is True
    )
    assert covered >= _BASELINE_COVERED, (
        f"BC-CHART-10 evidence-sort coverage dropped below baseline "
        f"({covered} < {_BASELINE_COVERED})"
    )


# --- ADR-0027 §6: gemessene_zeilen gegen Gold (check_evidence_sort --gold) ------------------

import pytest  # noqa: E402

from tooling.validation.check_evidence_sort import GOLD, pruefe_gold, zaehle_zeilen  # noqa: E402

_VERTRAG = """\
domain: probe
dimension:
  - name: dim_org
    columns: [{name: OrgKey, role: key}, {name: Region}]
fact:
  - name: fact_probe
    grain: org x tag
    columns: [{name: OrgKey, ref: dim_org}, {name: Kanal}, {name: Menge}]
"""


def _probe_gold(tmp_path: Path) -> tuple[Path, Path]:
    import pandas as pd

    gold, vertraege = tmp_path / "gold", tmp_path / "contracts"
    (gold / "facts" / "fact_probe").mkdir(parents=True)
    (gold / "dimensions" / "dim_org").mkdir(parents=True)
    vertraege.mkdir()
    (vertraege / "probe.yaml").write_text(_VERTRAG, encoding="utf-8")
    pd.DataFrame({"OrgKey": [1, 2, 3], "Region": ["Nord", "Nord", "Sued"]}).to_parquet(
        gold / "dimensions" / "dim_org" / "teil.parquet")
    # Org 3 hat keine Faktzeile; Kanal B kommt nur im Norden vor.
    pd.DataFrame({"OrgKey": [1, 1, 2, 2], "Kanal": ["A", "B", "A", "A"], "Menge": [1, 2, 3, 4]}).to_parquet(
        gold / "facts" / "fact_probe" / "teil.parquet")
    return gold, vertraege


def test_zaehle_zeilen_counts_combinations_present_in_fact(tmp_path):
    gold, vertraege = _probe_gold(tmp_path)
    # Nord x {A, B} = 2; Sued hat keine Faktzeile und erscheint nicht.
    assert zaehle_zeilen("fact_probe", [("dim_org", "Region"), ("fact_probe", "Kanal")], gold, vertraege) == (2, "")
    assert zaehle_zeilen("fact_probe", [("dim_org", "Region")], gold, vertraege) == (1, "")


def test_zaehle_zeilen_says_not_checked_instead_of_zero(tmp_path):
    gold, vertraege = _probe_gold(tmp_path)
    zahl, grund = zaehle_zeilen("fact_fehlt", [("dim_org", "Region")], gold, vertraege)
    assert zahl is None and "Vertraege" in grund
    zahl, grund = zaehle_zeilen("fact_probe", [("dim_lane", "Mode")], gold, vertraege)
    assert zahl is None and "dim_lane" in grund
    zahl, grund = zaehle_zeilen("fact_probe", [("dim_org", "Region")], tmp_path / "leer", vertraege)
    assert zahl is None and "Gold fehlt" in grund


@pytest.mark.skipif(not (GOLD / "facts").is_dir(),
                    reason=f"nicht geprüft: Aurora-Gold fehlt unter {GOLD}")
def test_every_top_n_ausnahme_matches_gold():
    """Jede Ausnahme wird gezaehlt und stimmt; die Zahl der gepruften gehoert in den Assert."""
    ergebnisse = {}
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        res = pruefe_gold(b)
        if res is not None:
            ergebnisse[b.parent.name.split("_")[0]] = res
    assert len(ergebnisse) >= 6, f"nur {len(ergebnisse)} Ausnahmen gefunden: {sorted(ergebnisse)}"
    falsch = {uc: r for uc, r in ergebnisse.items() if r[0] != "gleich"}
    assert not falsch, falsch
