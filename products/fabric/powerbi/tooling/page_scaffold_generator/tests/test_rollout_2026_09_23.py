"""Regressionen aus dem Ausrollen des Generators auf alle Reports (23.09.2026, R5.1).

Jede Klasse hier wurde beim ersten Lauf gemessen, nicht vermutet, und keine davon haette
ein vorhandenes Tor gemeldet: das ausgelieferte dist/ war an diesen Stellen von Hand
nachgezogen, der Generator nicht.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_PKG = Path(__file__).resolve().parents[1]
if str(_PKG.parent) not in sys.path:
    sys.path.insert(0, str(_PKG.parent))

from page_scaffold_generator.config_loader import ConfigLoader  # noqa: E402
from page_scaffold_generator.grid_calculator import (  # noqa: E402
    SLICER_DROPDOWN_FLOOR,
    ZONE0_HEADER_HEIGHT,
    enforce_slicer_floor,
    zone0_offset,
)


@pytest.fixture(scope="module")
def loader():
    return ConfigLoader(REPO)


@pytest.mark.parametrize("uc, kpi, erwartet", [
    # Katalogname existiert in keinem Modell -> Name aus dem Measure-Dictionary
    ("COM-001", "KPI-COM-006", "Plan Sales Amount"),
    ("COM-001", "KPI-COM-007", "Last Year Net Sales Amount"),
    # Katalogname existiert, aber nur in einem FREMDEN Modell -> Variante des eigenen
    ("FIN-001", "KPI-SCM-007", "OTIF % (FIN)"),
    ("XD-003", "KPI-COM-013", "Gross Margin % (XD)"),
    # Dictionary kennt die Variante nicht, das Modell fuehrt genau eine
    ("XD-004", "KPI-GOV-006", "Avg Time-to-Outcome Days (XD)"),
])
def test_measure_names_resolve_against_the_bound_model(loader, uc, kpi, erwartet):
    assert loader.measure_map_for(loader.load_use_case_bracket(uc))[kpi] == erwartet


def test_the_target_model_comes_from_the_report_not_from_the_domain_field(loader):
    """XD-003 fuehrt `domain: Executive`; ein Modell dieses Namens gibt es nicht."""
    assert loader._target_model_dir(loader.load_use_case_bracket("XD-003")).name == "Experience.SemanticModel"


def test_customer_token_follows_the_model(loader):
    eintrag = (("dim_customer", "CustomerName"), ("dim_org", "Customer"))
    assert loader._pick_column("customer", eintrag, loader.load_use_case_bracket("SCM-002")) == ("dim_org", "Customer")
    assert loader._pick_column("customer", eintrag, loader.load_use_case_bracket("COM-003")) == ("dim_customer", "CustomerName")


def test_an_explicit_table_column_is_a_column_not_a_measure(loader):
    b = loader.load_use_case_bracket("COM-001")
    assert loader._table_column("dim_org.Region", b) == ("dim_org", "Region")
    assert loader._table_column("KPI-COM-005", b) is None      # KPI-Kennung
    with pytest.raises(ValueError, match="Spalte"):
        loader._table_column("dim_org.Regoin", b)                       # Tippfehler


def test_domain_suffix_falls_back_to_the_models_single_narrative(loader):
    """XD-004 hat keinen zugeordneten Data Contract; das Experience-Modell fuehrt genau XD."""
    assert loader._domain_measure_suffix(loader.load_use_case_bracket("XD-004")) == "XD"


def test_zone0_reserves_the_header_strip():
    assert zone0_offset(True, 16) == ZONE0_HEADER_HEIGHT + 16
    assert zone0_offset(False, 16) == 0


def _slicer(y, h):
    return {"name": "Slicer_Date", "position": {"x": 0, "y": y, "width": 300, "height": h},
            "visual": {"visualType": "slicer",
                       "objects": {"data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}]}}}


def test_slicer_floor_lifts_the_row_and_pushes_content_down():
    s = _slicer(200, 64)
    main = {"name": "Main_1", "position": {"x": 0, "y": 280, "width": 300, "height": 768},
            "visual": {"visualType": "lineChart"}}
    kpi = {"name": "KPI_Cards", "position": {"x": 0, "y": 32, "width": 300, "height": 150},
           "visual": {"visualType": "cardVisual"}}
    assert enforce_slicer_floor([kpi, s, main], page_bottom=1048)
    assert s["position"]["height"] == SLICER_DROPDOWN_FLOOR
    assert main["position"]["y"] == 280 + (SLICER_DROPDOWN_FLOOR - 64)
    assert main["position"]["y"] + main["position"]["height"] <= 1048
    assert kpi["position"] == {"x": 0, "y": 32, "width": 300, "height": 150}   # darueber: unberuehrt


def test_a_tall_enough_slicer_is_left_alone():
    s = _slicer(200, 80)
    assert not enforce_slicer_floor([s], page_bottom=1048)
    assert s["position"]["height"] == 80


# --- Visualtypen ueber die governte Rollentabelle (Q-2, 23.09.2026) -------------------

from page_scaffold_generator.layout_calculator import Position  # noqa: E402
from page_scaffold_generator.visual_builder import VisualBuilder  # noqa: E402

_VB_PATH = REPO / "products" / "fabric" / "powerbi" / "tooling"
if str(_VB_PATH) not in sys.path:
    sys.path.insert(0, str(_VB_PATH))
import validate_bindings  # noqa: E402


def _pos():
    return Position(x=0, y=0, width=400, height=300)


@pytest.mark.parametrize("ux, erwartet", [
    ("variance_bar", "clusteredBarChart"),     # vorher still: lineChart
    ("exception_table", "tableEx"),            # vorher still: lineChart
    ("bar_chart_vertical", "clusteredColumnChart"),   # vorher: lineChart
    ("scatter_plot", "scatterChart"),
])
def test_declared_types_render_as_declared(ux, erwartet):
    v = VisualBuilder().build_by_ux_visual_type(ux, _pos(), name="Main_2", measures=["A", "B"],
                                                category_entity="dim_org", category_property="OrgName")
    assert v["visual"]["visualType"] == erwartet


def test_exception_table_is_sorted_worst_first():
    v = VisualBuilder().build_by_ux_visual_type("exception_table", _pos(), name="Main_3", measures=["Downtime %"])
    assert v["visual"]["query"]["sortDefinition"]["isDefaultSort"] is True


def test_an_unknown_type_is_an_error_not_a_line():
    with pytest.raises(ValueError, match="kein Visual ist besser als ein falsches"):
        VisualBuilder().build_by_ux_visual_type("gauge_of_doom", _pos(), name="Main_1", measures=["A"])


def test_bindings_allow_a_table_only_where_the_bracket_declares_one():
    assert validate_bindings._registry_table_allowed("OPS-001_Operations_Performance", "Main_3")
    assert not validate_bindings._registry_table_allowed("OPS-001_Operations_Performance", "Main_1")
    assert not validate_bindings._registry_table_allowed("COM-003_Customer_Value", "Main_2")


# --- Rangfolge nach governter Richtung (R6.3, 23.09.2026) ------------------------------

from page_scaffold_generator.page_builder import _sort_rangfolge  # noqa: E402


def _vis(vt, category=True):
    qs = {"Y": {"projections": []}}
    if category:
        qs["Category"] = {"projections": [{"field": {"Column": {"Property": "OrgName"}}}]}
    return {"visual": {"visualType": vt, "query": {"queryState": qs}}}


@pytest.mark.parametrize("good_is, erwartet", [
    ("higher", "Ascending"),      # schlechtester (niedrigster) zuerst
    ("lower", "Descending"),      # schlechtester (hoechster) zuerst
    (None, "Descending"),         # ohne Richtung: groesster zuerst
])
def test_ranking_sorts_worst_first_by_the_governed_direction(good_is, erwartet):
    richtung = {"k": good_is} if good_is else {}
    sd = _sort_rangfolge(_vis("clusteredBarChart"), ["Availability %"], ["k"], richtung)
    assert sd["sort"][0]["direction"] == erwartet


def test_a_time_axis_is_never_sorted_by_value():
    """SCM-001 Main_3 (Forecast Accuracy ueber Monate) wurde bis 23.09.2026 nach Wert sortiert."""
    assert _sort_rangfolge(_vis("lineChart"), ["Forecast Accuracy %"], ["k"], {"k": "higher"},
                           ranking_slot=True) is None


def test_an_evidence_table_sorts_by_its_first_measure():
    sd = _sort_rangfolge(_vis("tableEx", category=False), ["In-Full %", "Stockout Impact %"],
                         ["KPI-SCM-018", "KPI-SCM-009"], {"KPI-SCM-018": "higher"})
    assert sd["sort"][0]["field"]["Measure"]["Property"] == "In-Full %"
    assert sd["sort"][0]["direction"] == "Ascending"


# --- Kopfzeile und Charttitel ohne ungepruefte Behauptung (R6.2, 23.09.2026) ------------

import copy  # noqa: E402

from page_scaffold_generator.title_policy import EXPECTED_PREFIX  # noqa: E402


def test_an_unverified_header_leads_with_the_question_and_keeps_the_big_idea(loader):
    b = loader.load_use_case_bracket("COM-003")
    p1 = b["ux_layout_rules"]["page_1_summary"]
    kopf = loader.get_page_config("COM-003", "overview")["big_idea_text"]
    assert kopf.startswith(p1["decision_question"])
    assert kopf.endswith(EXPECTED_PREFIX + p1["big_idea"])      # woertlich enthalten


def test_statement_titles_are_opt_in_not_default(loader):
    """Bis 23.09.2026 galt `title_statements_verified` als wahr, wenn es fehlte."""
    b = loader.load_use_case_bracket("COM-003")
    assert "title_statements_verified" not in b["ux_layout_rules"]
    assert loader.get_page_config("COM-003", "overview")["assert_statement_titles"] is False
