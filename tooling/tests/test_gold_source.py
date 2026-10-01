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
# Die Sperrklinke BEKANNTE_LUECKEN, die hier stand, lebt seit 29.09.2026 (Ledger A-24) als Tor
# `tooling/validation/check_model_vs_gold.py` mit Allowlist `model_vs_gold_allowlist.yaml`:
# ohne pyarrow, in Stage 1 und CI, mit „nicht geprüft“ statt Grün, wenn Gold fehlt.
# Tests: `tooling/tests/test_model_vs_gold.py`.
