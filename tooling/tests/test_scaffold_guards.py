"""Slicer- und Kartenwahl des Report-Generators gegen das Zielmodell (24.10.2026).

`ConfigLoader._slicer_columns` laesst nur Spalten zu, die eine KPI-Measure des Brackets
ueber ihre Faktentabelle erreicht; `_card_kpi_ids` gibt einem beeinflussenden KPI keine
Karte, dessen Measure im Modell der `VAR _pending`-Platzhalter ist. Gemessen wird an den
committeten Brackets und an `dist/` -- die Faelle sind die, an denen die Guards entstanden.
"""
from __future__ import annotations

import pytest

from tooling.codegen.comparison_measures import _loader


@pytest.fixture(scope="module")
def loader():
    return _loader()


def _slicer(loader, uc: str) -> set:
    return loader._slicer_columns(loader.load_use_case_bracket(uc))


def test_com005_slicers_reach_the_pipeline_facts_only(loader):
    spalten = _slicer(loader, "COM-005")
    tabellen = {s.split(".", 1)[0] for s in spalten}
    assert {"fact_pipeline", "fact_sales_target", "dim_salesrep", "dim_sales_stage", "dim_date",
            "dim_org"} <= tabellen
    # dim_product haengt an fact_sales, nicht an den Pipeline-Fakten: ein Slicer ins Leere
    assert "dim_product" not in tabellen


def test_ops002_product_slicer_is_gone(loader):
    tabellen = {s.split(".", 1)[0] for s in _slicer(loader, "OPS-002")}
    assert "dim_product" not in tabellen and "dim_date" in tabellen


def test_cards_skip_placeholder_measures_but_keep_real_ones(loader):
    com = loader._card_kpi_ids(loader.load_use_case_bracket("COM-005"))
    assert com[0] == "KPI-COM-026"
    assert "KPI-COM-028" not in com
    # KPI-COM-030 ist seit 24.10.2026 eine DAX-Komposition aus dem Katalog: die Karte kommt zurueck
    assert "KPI-COM-030" in com
    # Katalog-hitl, aber im Modell eine echte Measure: die Karte bleibt
    assert "KPI-SCM-012" in loader._card_kpi_ids(loader.load_use_case_bracket("SCM-003"))
