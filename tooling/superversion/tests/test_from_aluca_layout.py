"""Layout-Bindung im Quell-Adapter (Task L8).

Der Befund, der L8 ausgeloest hat
---------------------------------
`from_aluca` erzeugte Visuals **ohne Geometrie** — jedes `Visual` ging mit
x=y=width=height=0 heraus. Sichtbar war das in den eingecheckten Golden Snapshots
(`"width": 0`), aber es fiel nicht auf, weil kein Test danach fragte. Der Vertrag
(`canonical_contract.Visual`) fuehrt die vier Felder seit jeher.

Aufgefallen ist es erst bei L13: die Umstellung auf Logical Units bewegte KEINEN
Snapshot — und diese Stille war der Hinweis, nicht die Bestaetigung.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tooling.superversion.from_aluca import KpiCatalog, from_bracket_file

_ROOT = Path(__file__).resolve().parents[3]
_KPIS = _ROOT / "core/kpi_catalog/kpis"
_FIN002 = _ROOT / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml"
_GRID = _ROOT / "core/templates/page_templates/tokens/layout_grid.yaml"


@pytest.fixture(scope="module")
def modell():
    return from_bracket_file(_FIN002, _KPIS)


def _visuals(modell):
    return [v for p in modell.report.pages for v in p.visuals]


def test_visuals_carry_geometry_at_all(modell):
    """Die Grundzusicherung von L8 — und genau die fehlte vorher.

    Nicht „die Zahlen stimmen", sondern „es gibt ueberhaupt welche". Ein Report, dessen
    Visuals alle bei (0,0) mit Groesse 0 liegen, ist kein Layout, sondern ein Stapel.
    """
    mit_geo = [v for v in _visuals(modell) if v.width > 0 and v.height > 0]
    assert mit_geo, "kein einziges Visual traegt Geometrie"
    assert len(mit_geo) == len(_visuals(modell)), (
        "Visuals ohne Geometrie: "
        f"{[v.visual_id for v in _visuals(modell) if not v.width]}"
    )


def test_main_columns_do_not_overlap(modell):
    """Zwei Hauptspalten duerfen sich nicht ueberlappen.

    Das ist der billigste Beweis, dass die Slots wirklich aus dem Raster kommen und
    nicht aus einem Default: bei kopierten oder geratenen Werten faellt genau das um.
    """
    mains = sorted((v for v in _visuals(modell) if "_30s_" in v.visual_id),
                   key=lambda v: v.x)
    for links, rechts in zip(mains, mains[1:]):
        assert links.x + links.width <= rechts.x + 1e-6, (
            f"{links.visual_id} ragt in {rechts.visual_id}")


def test_geometry_stays_inside_the_canvas(modell):
    grid = yaml.safe_load(_GRID.read_text(encoding="utf-8")) or {}
    prod = (grid.get("canvas") or {}).get("production") or {}
    w, h = prod.get("width", 1920), prod.get("height", 1080)
    for v in _visuals(modell):
        assert v.x >= 0 and v.y >= 0, v.visual_id
        assert v.x + v.width <= w + 1e-6, f"{v.visual_id} ragt rechts hinaus"
        assert v.y + v.height <= h + 1e-6, f"{v.visual_id} ragt unten hinaus"


def test_grid_change_takes_effect_without_code_change(tmp_path, monkeypatch):
    """DoD: „Aenderung an `layout_grid.yaml` wirkt ohne Codeaenderung."

    Geprueft wird die Zusicherung selbst, nicht ihre Formulierung: der Aussenrand wird
    zur Laufzeit veraendert und muss sich in der Geometrie niederschlagen. Waere die
    Tabelle im Adapter kopiert (statt gelesen), passierte hier nichts — und der Test
    faende genau das.
    """
    from tooling.generator_core.ir import compiler

    original = yaml.safe_load(_GRID.read_text(encoding="utf-8"))
    vorher = from_bracket_file(_FIN002, _KPIS)
    x_vorher = min(v.x for v in _visuals(vorher))

    geaendert = dict(original)
    geaendert["spacing"] = {**original["spacing"], "outer_margin": 64}
    kopie = tmp_path / "layout_grid.yaml"
    kopie.write_text(yaml.safe_dump(geaendert), encoding="utf-8")
    monkeypatch.setattr(compiler, "_GRID_YAML", kopie)

    nachher = from_bracket_file(_FIN002, _KPIS)
    x_nachher = min(v.x for v in _visuals(nachher))

    assert x_vorher == pytest.approx(32.0), "Ausgangswert stimmt nicht mit outer_margin 32"
    assert x_nachher == pytest.approx(64.0), (
        "Der Adapter liest das Raster nicht — eine YAML-Aenderung blieb wirkungslos")


def test_surplus_components_get_no_invented_slot():
    """Mehr als drei 30s-Komponenten bekommen KEINE vierte Spalte.

    Das Raster hat drei Hauptspalten. Eine vierte zu erfinden, waere derselbe Fehler
    wie der frueher entfernte KPI-Fallback im Page-Scaffold-Generator: sichtbar leer
    ist besser als still danebengesetzt.
    """
    from tooling.superversion.from_aluca import _MAIN_SLOTS, _slot_geometrie

    assert len(_MAIN_SLOTS) == 3
    assert _slot_geometrie("") == {}
    assert _slot_geometrie("Main_4") == {}


def test_geometry_matches_the_governed_slot_exactly(modell):
    """Die Werte stammen aus dem Raster, nicht aus einer zweiten Rechnung im Adapter."""
    from tooling.generator_core.ir.compiler import (
        _OVERVIEW_LU,
        _grid_params,
        lu_to_pixels,
    )

    p = _grid_params()
    erwartet = lu_to_pixels(*_OVERVIEW_LU["Main_1"], canvas_w=p["width"],
                            canvas_h=p["height"], grid=p)
    main1 = next(v for v in _visuals(modell) if v.visual_id.endswith("_30s_2"))
    assert main1.x == pytest.approx(erwartet["x"])
    assert main1.width == pytest.approx(erwartet["width"])
