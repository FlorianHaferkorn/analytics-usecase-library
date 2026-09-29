"""Gold-Quelle als Parameter (AP-3, 24.09.2026): lokal unveraendert, OneLake als Weiche.

`tooling/codegen/gold_source.py` schreibt die Weiche in `fn_DeltaCurrentFiles` aller fuenf
Modelle. Diese Tests halten die ausgelieferten Modelle daran fest und pruefen, dass die
Sandbox-Scheibe jede Tabelle abdeckt, die ein Modell liest.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tooling.codegen import gold_source as gs  # noqa: E402

# Meridian D-578 (29.09.2026): die Showdaten liegen nicht mehr in Git. Tests, die sie lesen,
# stehen ohne sie mit "nicht gelaufen: ... holen mit ..." im Skip-Grund, nicht gruen.
from showcases.aurora_group.data import showdaten  # noqa: E402

braucht_showdaten = showdaten.pytest_markierung()


MODELLE = sorted(gs.DIST.glob("*.SemanticModel"))


def test_shipped_models_carry_exactly_the_generated_source_switch():
    assert len(MODELLE) == 5
    assert gs.pruefe() == [], "python -m tooling.codegen.gold_source --write"


def test_generation_is_idempotent():
    for m in MODELLE:
        text = (m / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
        assert gs.soll(m.name, text) == text


def test_local_default_keeps_folder_files():
    """Mit der Vorgabe `folder` liest das Modell genau wie vorher ueber `Folder.Files`."""
    for m in MODELLE:
        text = (m / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
        assert 'expression GoldSourceKind = "folder"' in text
        assert "\t\t\t\tFolder.Files(TableFolderPath),\n" in text
        assert gs.ALT not in text


def test_onelake_lists_the_container_and_filters_to_the_table():
    """Microsoft Learn nennt Unterordner-URLs fuer den ADLS-Konnektor in Desktop und Power
    Query Online als nicht unterstuetzt -- also Container auflisten und filtern."""
    assert "AzureStorage.DataLake(GoldContainerUrl)" in gs.NEU
    assert "Text.StartsWith(Text.Replace([Folder Path]" in gs.NEU
    assert "AzureStorage.DataLake(TableFolderPath)" not in gs.NEU


def test_parameters_have_stable_lineage_tags():
    tags = set()
    for m in MODELLE:
        text = (m / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
        for name in ("GoldSourceKind", "GoldContainerUrl"):
            block = text.split(f"expression {name} =", 1)[1]
            tags.add(re.search(r"lineageTag: ([0-9a-f-]{36})", block).group(1))
    assert len(tags) == 10                                     # je Modell und Parameter eigener Tag


def test_an_unknown_function_shape_is_refused_not_guessed():
    with pytest.raises(ValueError, match="unbekannte Form"):
        gs.soll("X", "expression fn_DeltaCurrentFiles =\n\t\tAllFiles = Sonstwas(),\n")


@braucht_showdaten
def test_every_table_a_model_reads_exists_in_gold():
    """Die Scheibe schneidet alle Gold-Tabellen; fehlt eine im Gold, fehlt sie im Sandbox."""
    gold = REPO / "showcases" / "aurora_group" / "data" / "gold"
    gelesen = set()
    for m in MODELLE:
        for f in (m / "definition" / "tables").glob("*.tmdl"):
            gelesen |= set(re.findall(r'GoldDataPath & "/((?:dimensions|facts)/\w+)"',
                                      f.read_text(encoding="utf-8")))
    assert len(gelesen) >= 40
    assert sorted(t for t in gelesen if not (gold / t).is_dir()) == []


# --- Jede Quellspalte existiert in den Gold-Dateien (24.09.2026) ------------------------
#
# Gefunden von der DAX-Gegenprobe (AP-4): `fact_sales[Sales Units]` im SupplyChain-Modell liest
# eine Spalte, die in keiner der 60 aktiven Parquet-Dateien steht (dort heisst sie `Quantity`).
# Keine Partition benennt um oder ergaenzt; die Spalten fehlen also wirklich. Dass ein Refresh
# daran scheitert, ist **ANNAHME, ungeprueft** bis zum ersten Lauf im Tenant.
#
# E8 (24.09.2026): 10 der 20 behoben durch `tooling/codegen/model_alignment.py` (Umbenennen auf die
# Gold-Spalte, Modell folgt der Gold-Koernung). Die uebrigen 10 ergaenzt der Gold-Generator (Gruppen 3, 4).
#
# Die Liste ist eine Sperrklinke: sie darf nur schrumpfen. Eine neue Luecke macht den Test rot,
# ebenso eine behobene, die noch hier steht. Die Zuordnung ist Flos Entscheidung (Umbenennung im
# Vertrag oder Spalte im Gold-Generator ergaenzen), nicht geraten.
BEKANNTE_LUECKEN = {
    ("Experience", "fact_action_log", "Action Code"),
    ("Experience", "fact_action_log", "Responsible Role"),
    ("Finance", "dim_customer", "Region"),
    ("Finance", "fact_cost", "Material Cost Amount"),
    ("Finance", "fact_cost", "Overhead Amount"),
    ("Finance", "fact_inventory", "COGS Amount"),
    ("Operations", "fact_inventory_snapshot", "Reorder Flag"),
    ("SupplyChain", "dim_product", "ABC_Class"),
    ("SupplyChain", "dim_product", "XYZ_Class"),
    ("SupplyChain", "fact_procurement", "Contract Unit Price"),
}


def _quellspalten_ohne_gold() -> set[tuple[str, str, str]]:
    import importlib.util

    import pyarrow.parquet as pq

    spec = importlib.util.spec_from_file_location(
        "slice_gold", REPO / "showcases" / "aurora_group" / "data" / "scripts" / "slice_gold.py")
    sg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sg)
    gold = REPO / "showcases" / "aurora_group" / "data" / "gold"
    fehlt = set()
    for m in MODELLE:
        for f in sorted((m / "definition" / "tables").glob("*.tmdl")):
            text = f.read_text(encoding="utf-8")
            o = re.search(r'GoldDataPath & "/((?:dimensions|facts)/\w+)"', text)
            if not o:
                continue
            namen = set()
            for p in sg.aktive_dateien(gold / o.group(1)):
                if p.is_file():
                    namen |= set(pq.read_schema(str(p)).names)
            for q in re.findall(r"^\t\tsourceColumn: (.*)$", text, re.M):
                if q.strip() not in namen:
                    fehlt.add((m.name.split(".")[0], f.stem, q.strip()))
    return fehlt


@braucht_showdaten
def test_every_source_column_exists_in_gold_or_is_a_known_gap():
    fehlt = _quellspalten_ohne_gold()
    assert sorted(fehlt - BEKANNTE_LUECKEN) == [], "neue Luecke zwischen Modell und Gold"
    assert sorted(BEKANNTE_LUECKEN - fehlt) == [], "behoben -- aus BEKANNTE_LUECKEN streichen"
