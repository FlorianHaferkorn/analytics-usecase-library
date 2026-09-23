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
    ("COM-001", "sales.net_sales.plan.amount", "Plan Sales Amount"),
    ("COM-001", "sales.net_sales.ly.amount", "Last Year Net Sales Amount"),
    # Katalogname existiert, aber nur in einem FREMDEN Modell -> Variante des eigenen
    ("FIN-001", "supply.otif.pct", "OTIF % (FIN)"),
    ("XD-003", "margin.gm.pct", "Gross Margin % (XD)"),
    # Dictionary kennt die Variante nicht, das Modell fuehrt genau eine
    ("XD-004", "enterprise.avg_time_to_outcome.days", "Avg Time-to-Outcome Days (XD)"),
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
    assert loader._table_column("sales.net_sales.amount", b) is None      # KPI-Kennung
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
