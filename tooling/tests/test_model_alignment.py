"""E8 Gruppen 1 und 2 (24.09.2026): Modell an Vertrag und Gold ausgerichtet, und das bleibt so.

Die Ausrichtung selbst schreibt ``tooling/codegen/model_alignment.py``. Diese Tests halten die
ausgelieferten Modelle daran fest und prüfen die Schutzregeln. Der letzte Test ist allgemeiner:
jede Beziehung aller fünf Modelle zeigt auf Spalten, die es gibt. An ``fact_nps.QueueKey`` und
``fact_procurement.ProductKey`` hingen Beziehungen auf Spalten ohne Gold-Quelle, und kein Gate
hatte das gesehen.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tooling.codegen import model_alignment as ma  # noqa: E402


def test_shipped_models_are_aligned():
    assert ma.pruefe() == [], "python -m tooling.codegen.model_alignment --write"


def test_alignment_is_idempotent():
    for p, inhalt in ma.soll().items():
        if inhalt is None:
            assert not p.exists(), p
        else:
            assert p.read_text(encoding="utf-8") == inhalt, p


def test_model_column_names_stay_so_dax_and_visuals_are_untouched():
    text = (ma._defn("SupplyChain") / "tables" / "fact_sales.tmdl").read_text(encoding="utf-8")
    assert "\tcolumn 'Sales Units'\n" in text and "\t\tsourceColumn: Quantity\n" in text


def test_procurement_follows_the_gold_grain():
    d = ma._defn("SupplyChain")
    text = (d / "tables" / "fact_procurement.tmdl").read_text(encoding="utf-8")
    assert ma._column_block(text, "ProductKey") is None
    assert ma._column_block(text, "CategoryKey") and ma._column_block(text, "VendorKey")
    assert not (d / "relationships" / "dim_product_fact_procurement.tmdl").exists()
    model = (d / "model.tmdl").read_text(encoding="utf-8")
    assert "ref table dim_category\n" in model and "ref table dim_vendor\n" in model


def test_a_used_column_is_never_dropped(monkeypatch):
    """Gegenprobe zur Schutzregel: `Sales Units` wird von vier Measures genutzt."""
    assert ma._nutzungen("SupplyChain", "fact_sales", "Sales Units")
    monkeypatch.setattr(ma, "DROPS", (("SupplyChain", "fact_sales", "Sales Units", "x"),))
    with pytest.raises(ValueError, match="noch genutzt"):
        ma.soll()


def test_rename_refuses_ambiguity_and_unknown_sources():
    zweimal = "\t\tsourceColumn: A\n\t\tsourceColumn: A\n"
    with pytest.raises(ValueError, match="nicht eindeutig"):
        ma.rename(zweimal, "A", "B", "t")
    with pytest.raises(ValueError, match="weder"):
        ma.rename("\t\tsourceColumn: C\n", "A", "B", "t")
    assert ma.rename("\t\tsourceColumn: B\n", "A", "B", "t") == "\t\tsourceColumn: B\n"


def _spalten(tabellen_dir: Path) -> set[tuple[str, str]]:
    out = set()
    for f in tabellen_dir.glob("*.tmdl"):
        text = f.read_text(encoding="utf-8")
        tab = re.search(r"^table (.+)$", text, re.M).group(1).strip().strip("'")
        for c in re.findall(r"^\tcolumn (.+?)(?: =.*)?$", text, re.M):
            out.add((tab, c.strip().strip("'")))
    return out


def test_every_relationship_points_at_existing_columns():
    kaputt = []
    for sm in sorted(ma.DIST.glob("*.SemanticModel")):
        spalten = _spalten(sm / "definition" / "tables")
        for r in sorted((sm / "definition" / "relationships").glob("*.tmdl")):
            for seite in re.findall(r"^\t(?:fromColumn|toColumn): (.+)$", r.read_text(encoding="utf-8"), re.M):
                tab, col = seite.strip().split(".", 1)
                if (tab.strip("'"), col.strip("'")) not in spalten:
                    kaputt.append(f"{sm.name}/{r.name}: {seite}")
    assert kaputt == []
