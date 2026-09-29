"""Tor „Semantic Model gegen Gold-Daten“ (Ledger A-24, 29.09.2026).

`tooling/validation/check_model_vs_gold.py` prüft jede `sourceColumn` der ausgelieferten Modelle
gegen die Gold-Tabelle, die ihre Partition liest. Diese Tests halten fest:

* das ausgelieferte Modell ist gegen die Allowlist grün — und ohne Allowlist rot;
* eine erfundene `sourceColumn` in einer Kopie macht es rot (Mutationstest);
* die Sperrklinke greift in beide Richtungen (neu und verschwunden);
* fehlende Gold-Daten sind „nicht geprüft“ (Exit 2 strikt, pytest-skip mit Grund), nie grün;
* der pyarrow-freie Parquet-Leser liefert dieselben Spalten wie pyarrow (zweite Messung).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tooling" / "validation"))

import check_model_vs_gold as cmg  # noqa: E402

GOLD_DA = (cmg.GOLD / "dimensions").is_dir() and (cmg.GOLD / "facts").is_dir()
braucht_gold = pytest.mark.skipif(
    not GOLD_DA, reason=f"nicht geprüft: Aurora-Gold fehlt unter {cmg.GOLD} — holen mit: {cmg.HOLEN}")


def _leere_allowlist(tmp_path: Path) -> Path:
    p = tmp_path / "leer.yaml"
    p.write_text("eintraege: []\n", encoding="utf-8")
    return p


def _dist_kopie(tmp_path: Path) -> Path:
    """Nur die Tabellen-TMDL der Modelle — reicht dem Tor und bleibt klein."""
    ziel = tmp_path / "dist"
    for m in sorted(cmg.DIST.glob("*.SemanticModel")):
        shutil.copytree(m / "definition" / "tables", ziel / m.name / "definition" / "tables")
    return ziel


# --- ausgelieferter Stand ---------------------------------------------------------------

@braucht_gold
def test_shipped_models_match_gold_up_to_the_allowlist():
    e = cmg.pruefe()
    assert e.nicht_geprueft == [], e.nicht_geprueft
    assert e.neu == [], "neue Lücke zwischen Modell und Gold"
    assert e.verschwunden == [], "behoben — aus model_vs_gold_allowlist.yaml streichen"
    # Gegen ein leeres Tor: gemessen 29.09.2026 506 sourceColumn in 77 Modelltabellen.
    assert e.geprueft >= 480 and e.tabellen_geprueft >= 70
    assert cmg.bericht(e, strict=True) == cmg.EXIT_OK


@braucht_gold
def test_gold_covers_every_source_column_without_any_allowlist(tmp_path):
    """Seit dem Generator-Fix (A-24, 29.09.2026) ist die Allowlist leer: jede sourceColumn steht
    in ihrer Gold-Tabelle. Bis dahin standen hier zehn bekannte Lücken; dass ein Befund rot
    macht, belegt der Mutationstest unten."""
    assert not cmg.lies_allowlist(cmg.ALLOWLIST)
    e = cmg.pruefe(allowlist=_leere_allowlist(tmp_path))
    assert not e.neu and not e.befunde
    assert cmg.bericht(e, strict=True) == cmg.EXIT_OK


@braucht_gold
def test_tables_without_gold_partition_are_their_own_class_not_findings():
    e = cmg.pruefe()
    ohne = {t for _, t, _ in e.ohne_gold_quelle}
    assert {"_Measures", "Vergleich", "dim_supplier", "dim_pvm_driver"} <= ohne
    assert not any(t in ohne for _, t, _ in e.befunde)
    # security_user_org liest Gold (ohne dimensions/facts-Präfix) und wird geprüft
    assert "security_user_org" in e.herkunft
    assert ("Commercial", "dim_pvm_driver", True) in e.ohne_gold_quelle


# --- Mutationstest und Sperrklinke ----------------------------------------------------

@braucht_gold
def test_mutation_invented_source_column_turns_red(tmp_path):
    dist = _dist_kopie(tmp_path)
    f = dist / "Finance.SemanticModel" / "definition" / "tables" / "fact_cost.tmdl"
    text = f.read_text(encoding="utf-8")
    assert "\t\tsourceColumn: DateKey\n" in text
    f.write_text(text.replace("\t\tsourceColumn: DateKey\n",
                              "\t\tsourceColumn: Erfundene Spalte A24\n", 1), encoding="utf-8")
    e = cmg.pruefe(dist=dist)
    assert e.neu == [("Finance", "fact_cost", "Erfundene Spalte A24")]
    assert cmg.bericht(e, strict=False) == cmg.EXIT_BEFUND


@braucht_gold
def test_stale_allowlist_entry_turns_red(tmp_path):
    allow = tmp_path / "allow.yaml"
    allow.write_text(
        "eintraege:\n"
        "  - modell: Finance\n    tabelle: fact_cost\n    quellspalte: DateKey\n"
        "    grund: Test\n    ledger: A-24\n", encoding="utf-8")
    e = cmg.pruefe(allowlist=allow)
    assert e.verschwunden == [("Finance", "fact_cost", "DateKey")]
    assert cmg.bericht(e, strict=True) == cmg.EXIT_BEFUND


def test_allowlist_entry_needs_reason_and_ledger(tmp_path):
    p = tmp_path / "a.yaml"
    p.write_text("eintraege:\n  - {modell: F, tabelle: t, quellspalte: c, ledger: A-24}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="grund"):
        cmg.lies_allowlist(p)


def test_table_file_named_relationship_is_still_checked(tmp_path):
    """Der vendorte Meridian-Parser verliert Tabellen mit „relationship“ im Dateinamen (PR #511);
    dieses Tor liest jede Datei unter tables/."""
    tabellen = tmp_path / "dist" / "X.SemanticModel" / "definition" / "tables"
    tabellen.mkdir(parents=True)
    (tabellen / "fact_relationship_manager.tmdl").write_text(
        "table fact_relationship_manager\n\tlineageTag: x\n\n"
        "\tcolumn A\n\t\tdataType: int64\n\t\tsourceColumn: A\n\n"
        "\tcolumn 'B C'\n\t\tdataType: string\n\t\tsourceColumn: B C\n\n"
        "\tcolumn Calc = [A] * 2\n\t\tdataType: int64\n\n"
        "\tpartition fact_relationship_manager = m\n\t\tmode: import\n\t\tsource =\n"
        '\t\t\t\tlet\n\t\t\t\t\tActiveFiles = fn_DeltaCurrentFiles(GoldDataPath & "/facts/fact_rm")\n'
        "\t\t\t\tin\n\t\t\t\t\tActiveFiles\n", encoding="utf-8")
    t, = cmg.lies_modelle(tmp_path / "dist")
    assert (t.name, t.gold_ordner, t.quellen) == (
        "fact_relationship_manager", ["facts/fact_rm"], [("A", "A"), ("B C", "B C")])


def test_renaming_partition_is_not_checked(tmp_path):
    tabellen = tmp_path / "dist" / "X.SemanticModel" / "definition" / "tables"
    tabellen.mkdir(parents=True)
    (tabellen / "t.tmdl").write_text(
        "table t\n\n\tcolumn A\n\t\tsourceColumn: A\n\n\tpartition t = m\n\t\tsource =\n"
        '\t\t\t\tlet S = fn_DeltaCurrentFiles(GoldDataPath & "/facts/t"),\n'
        '\t\t\t\tR = Table.RenameColumns(S, {{"x", "A"}}) in R\n', encoding="utf-8")
    (tmp_path / "gold" / "facts" / "t").mkdir(parents=True)
    e = cmg.pruefe(dist=tmp_path / "dist", gold=tmp_path / "gold", allowlist=_leere_allowlist(tmp_path))
    assert e.nicht_geprueft == [("X.t", "Partition formt Spalten um")]
    assert e.geprueft == 0
    assert cmg.bericht(e, strict=True) == cmg.EXIT_NICHT_GEPRUEFT


# --- „nicht geprüft“ ist nicht grün ------------------------------------------------------

def test_missing_gold_is_not_checked_never_green(tmp_path, capsys):
    e = cmg.pruefe(gold=tmp_path / "gibt_es_nicht")
    assert e.geprueft == 0 and e.anzahl_nicht_geprueft > 0
    assert e.verschwunden == [], "ungeprüfte Tabellen gelten nicht als behoben"
    assert cmg.bericht(e, strict=True) == cmg.EXIT_NICHT_GEPRUEFT
    assert cmg.bericht(e, strict=False) == cmg.EXIT_OK
    out = capsys.readouterr().out
    assert "NICHT GEPRÜFT" in out and cmg.HOLEN in out and "OK —" not in out
    assert cmg.main(["--strict", "--gold", str(tmp_path / "gibt_es_nicht")]) == cmg.EXIT_NICHT_GEPRUEFT


# --- zweite Messung: Leser gegen pyarrow ---------------------------------------------------

@braucht_gold
def test_footer_reader_and_log_replay_match_pyarrow():
    pq = pytest.importorskip("pyarrow.parquet")
    verglichen = 0
    for tabelle in sorted(p for b in ("dimensions", "facts") for p in (cmg.GOLD / b).iterdir()
                          if p.is_dir()) + [cmg.GOLD / "security_user_org"]:
        gs = cmg.gold_schema(tabelle)
        assert gs.namen is not None, tabelle
        log = tabelle / "_delta_log"
        dateien = ([tabelle / p for p in cmg._delta._active_paths(str(log))] if log.is_dir()
                   else [p for p in tabelle.rglob("*.parquet") if "_delta_log" not in p.parts])
        erwartet = set()
        for p in dateien:
            assert cmg.parquet_spalten(p) == pq.read_schema(str(p)).names, p
            erwartet |= set(pq.read_schema(str(p)).names)
        assert gs.namen == erwartet, tabelle
        verglichen += 1
    assert verglichen >= 40
