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


def _entity_slicer(loader, uc: str):
    return loader.get_page_config(uc, "detail")["entity_slicer_field"]


def test_detail_entity_slicer_follows_declared_slicer_field(loader):
    # COM-001 (24.10.2026): Region > Country > Store stehen in den Matrixzeilen, die Kategorie
    # war nur noch als slicer_field deklariert und fehlte im Report
    assert _entity_slicer(loader, "COM-001") == "dim_product.Category"
    assert _entity_slicer(loader, "FIN-002") == "dim_org.Entity"
    # ohne Deklaration bleibt der OrgName-Slicer (Fallback im PageBuilder)
    assert _entity_slicer(loader, "SCM-003") is None


def test_detail_entity_slicer_never_repeats_a_matrix_row(loader):
    # XD-004: slicer_field domain ist die oberste Matrixzeile; ein Slicer darauf filtert nichts
    # Neues, der OrgName-Slicer bleibt
    bracket = loader.load_use_case_bracket("XD-004")
    c300 = bracket["ux_layout_rules"]["page_2_execution"]["component_300s"]
    assert c300["slicer_field"] in c300["row_fields"]
    assert _entity_slicer(loader, "XD-004") is None
