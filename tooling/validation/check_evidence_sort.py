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
    fehlend = [k for k in ("klasse", "gemessene_zeilen", "gemessen_am", "quelle", "fakt") if ausnahme.get(k) in (None, "")]
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


# --- ADR-0027 §6: gemessene_zeilen gegen Gold nachzaehlen (--gold) -------------------------
# Drei Ausgaenge je Ausnahme, nie zwei: "gleich", "abweichung" oder "nicht_geprueft" mit Grund.
# Wiederverwendet statt nachgebaut: die Spaltenaufloesung des Generators (ConfigLoader, also
# genau die Spalten der erzeugten Detail_Matrix), die Fakt->Dimension-Schluessel aus den
# Data Contracts und die laut _delta_log aktiven Dateien (beides check_data_model).
GOLD = REPO / "showcases" / "aurora_group" / "data" / "gold"


def _pfade() -> None:
    for pfad in (str(REPO), str(REPO / "products" / "fabric" / "powerbi" / "tooling")):
        if pfad not in sys.path:
            sys.path.insert(0, pfad)


def _evidence_columns(use_case_id: str) -> list[tuple[str, str]]:
    _pfade()
    from page_scaffold_generator.config_loader import ConfigLoader
    return list(ConfigLoader(REPO).get_page_config(use_case_id, "detail")["detail_matrix_columns"])


def zaehle_zeilen(fakt: str, spalten: list[tuple[str, str]], gold: Path = GOLD,
                  contracts: Path | None = None) -> tuple[Optional[int], str]:
    """Verschiedene Kombinationen der Evidenzspalten ueber den Zeilen von ``fakt``.

    Das ist die Zeilenzahl der Detail_Matrix ohne Filter (leere Kombinationen zeigt Power BI
    nicht, also zaehlt nur, was im Fakt vorkommt). Rueckgabe (zahl, "") oder (None, grund).
    """
    import pandas as pd

    _pfade()
    from tooling.validation import check_data_model as dm

    modell = dm.parse_model(contracts or dm.CONTRACTS)
    fakten = [f for f in modell["facts"] if f["name"] == fakt]
    if len(fakten) != 1:
        return None, f"{fakt}: {len(fakten)} Vertraege statt einem"
    schluessel = {d["name"]: d["key"] for d in modell["dims"]}
    fakt_pfad = gold / "facts" / fakt
    if not fakt_pfad.is_dir() or not dm._files(fakt_pfad):
        return None, f"Gold fehlt: {fakt_pfad.relative_to(gold.parent) if gold in fakt_pfad.parents else fakt_pfad}"
    fk_je_dim: dict[str, str] = {}
    for tabelle in dict.fromkeys(t for t, _ in spalten):
        if tabelle == fakt:
            continue
        fks = [c for c, ref in fakten[0]["refs"] if ref == tabelle]
        if len(fks) != 1 or tabelle not in schluessel:
            return None, f"{fakt} -> {tabelle}: {len(fks)} Fremdschluessel im Vertrag"
        fk_je_dim[tabelle] = fks[0]
    eigene = [c for t, c in spalten if t == fakt]
    rahmen = dm._read_small(fakt_pfad, sorted(set(fk_je_dim.values()) | set(eigene)))
    if rahmen is None:
        return None, f"{fakt}: Spalten {sorted(fk_je_dim.values())} fehlen im Gold"
    namen: list[str] = [c for c in eigene]
    for tabelle, fk in fk_je_dim.items():
        dim_pfad = gold / "dimensions" / tabelle
        cols = [c for t, c in spalten if t == tabelle]
        dim = dm._read_small(dim_pfad, [schluessel[tabelle], *cols]) if dim_pfad.is_dir() and dm._files(dim_pfad) else None
        if dim is None:
            return None, f"{tabelle}: Gold fehlt oder Spalten {cols} fehlen"
        dim = dim.drop_duplicates(subset=[schluessel[tabelle]])
        umbenannt = {c: f"{tabelle}.{c}" for c in cols}
        rahmen = rahmen.merge(dim.rename(columns={schluessel[tabelle]: fk, **umbenannt}), on=fk, how="inner")
        namen += umbenannt.values()
    return int(pd.DataFrame(rahmen[namen]).drop_duplicates().shape[0]), ""


def pruefe_gold(bracket_pfad: Path, gold: Path = GOLD) -> Optional[tuple[str, str]]:
    """None ohne Ausnahme; sonst (gleich|abweichung|nicht_geprueft, Text)."""
    data = yaml.safe_load(bracket_pfad.read_text(encoding="utf-8")) or {}
    ausnahme = (_c300(data) or {}).get("top_n_ausnahme")
    if not isinstance(ausnahme, dict):
        return None
    if not ausnahme.get("fakt"):
        return "nicht_geprueft", "top_n_ausnahme.fakt fehlt"
    uc = data.get("use_case_id") or bracket_pfad.parent.name.split("_")[0]
    try:
        spalten = _evidence_columns(uc)
    except Exception as exc:  # noqa: BLE001 -- jeder Aufloesungsfehler ist "nicht geprueft"
        return "nicht_geprueft", f"Evidenzspalten nicht aufloesbar: {exc}"
    zahl, grund = zaehle_zeilen(ausnahme["fakt"], spalten, gold)
    if zahl is None:
        return "nicht_geprueft", grund
    erklaert = ausnahme["gemessene_zeilen"]
    text = f"{zahl} Zeilen in Gold ({' x '.join(f'{t}.{c}' for t, c in spalten)}), erklaert {erklaert}"
    return ("gleich" if zahl == erklaert else "abweichung"), text


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
    parser.add_argument("--gold", action="store_true",
                        help="ADR-0027 §6: gemessene_zeilen gegen Aurora-Gold nachzaehlen "
                             "(Exit 0 alle gleich, 1 Abweichung, 2 nicht geprueft)")
    args = parser.parse_args()

    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    if args.use_case_id:
        brackets = [b for b in brackets if args.use_case_id.lower() in str(b).lower()]
        if not brackets:
            print(f"No UseCase_Bracket.yaml found matching '{args.use_case_id}'", file=sys.stderr)
            return 1

    if args.gold:
        return _main_gold(brackets)

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


def _main_gold(brackets: list[Path]) -> int:
    zaehler = {"gleich": 0, "abweichung": 0, "nicht_geprueft": 0}
    for b in brackets:
        res = pruefe_gold(b)
        if res is None:
            continue
        status, text = res
        zaehler[status] += 1
        print(f"    {status:<14} {b.parent.name.split('_')[0]}: {text}")
    geprueft = zaehler["gleich"] + zaehler["abweichung"]
    print(f"\nADR-0027 Gold: {zaehler['gleich']}/{geprueft} gleich, {zaehler['abweichung']} Abweichung, "
          f"{zaehler['nicht_geprueft']} nicht geprueft.")
    if zaehler["abweichung"]:
        return 1
    if zaehler["nicht_geprueft"] or not geprueft:
        return 2
    return 0


def _main_gold(brackets: list[Path]) -> int:
    zaehler = {"gleich": 0, "abweichung": 0, "nicht_geprueft": 0}
    for b in brackets:
        res = pruefe_gold(b)
        if res is None:
            continue
        status, text = res
        zaehler[status] += 1
        print(f"    {status:<14} {b.parent.name.split('_')[0]}: {text}")
    geprueft = zaehler["gleich"] + zaehler["abweichung"]
    print(f"\nADR-0027 Gold: {zaehler['gleich']}/{geprueft} gleich, {zaehler['abweichung']} Abweichung, "
          f"{zaehler['nicht_geprueft']} nicht geprueft.")
    if zaehler["abweichung"]:
        return 1
    if zaehler["nicht_geprueft"] or not geprueft:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
