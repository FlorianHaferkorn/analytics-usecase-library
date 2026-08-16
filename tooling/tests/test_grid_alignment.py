"""Tests fuer BC-LAYOUT-01 (check_grid_alignment.py).

Die Regel stand bis zum 03.08.2026 auf `check: structural` ohne Pruefer. Pruefbar wurde
sie durch L13 — seit die Geometrie in Logical Units liegt, gibt es eine Sollposition.

Die Tests fahren die reine Funktion, nicht die CLI: die Rasterparameter werden
uebergeben, damit kein Test von der gerade geltenden Leinwand abhaengt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tooling" / "validation"))
sys.path.insert(0, str(REPO))

import check_grid_alignment as cga  # noqa: E402

# 12 Spalten auf 1920 px, Gutter 16, Aussenrand 32 → lu_w = 140, Schritt = 156
def _params():
    from tooling.superversion.layer_tools.layout_grid import GridParams
    return GridParams(cols=12, rows=12, gutter=16.0, outer=32.0, width=1920, height=1080)


def _pos(x, width):
    return {"x": x, "y": 0, "width": width, "height": 100}


@pytest.mark.parametrize("col,span", [(0, 4), (4, 4), (8, 4), (2, 8), (10, 2), (0, 12)])
def test_governed_positions_are_clean(col, span):
    """Was `to_pixels` erzeugt, muss der Pruefer akzeptieren — sonst prueft er sich selbst."""
    from tooling.superversion.layer_tools.layout_grid import to_pixels

    p = _params()
    px = to_pixels(col, 0, span, 1, p)
    pos = {"x": round(px["x"]), "y": 0, "width": round(px["width"]), "height": 100}
    assert cga.abweichung(pos, p) is None


def test_pre_l13_geometry_is_caught():
    """Die real gefundenen Werte: Spanne 3.929 statt 4.00.

    Kein erfundenes Beispiel — das ist die Geometrie, die
    COM-001_Sales_Performance_vs_Plan_LY vor der Korrektur trug, und exakt die Zahl,
    die L13 als Defekt benannt hat.
    """
    grund = cga.abweichung(_pos(1291, 597), _params())
    assert grund and "x=1291" in grund and "Spalte 8 Spanne 4" in grund, grund


def test_rounding_noise_is_not_a_violation():
    """Der Emitter rundet auf ganze Pixel — das darf die Regel nicht ausloesen.

    Ohne diese Grenze waere der Pruefer ein Rauschmelder: bei Schritt 156 sind
    +/-1 px rund 0.006 Schritte, die gemessene echte Abweichung lag bei 0.032.
    """
    assert cga.abweichung(_pos(33, 607), _params()) is None
    assert cga.abweichung(_pos(31, 609), _params()) is None


def test_row_axis_is_deliberately_free():
    """y/height duerfen beliebig sein — L13 hat die Zeilenachse fraktional gelassen.

    Ein 12-Zeilen-Zwang liesse zwei Slots kollidieren und braeche die 76-px-
    Mindesthoehe des Slicers. Wer hier spaeter mitprueft, hebt eine Entscheidung auf.
    """
    assert cga.abweichung({"x": 32, "y": 289, "width": 608, "height": 750},
                          _params()) is None


def test_dist_corpus_is_on_the_grid():
    """Der lebende Bestand — und er ist es erst seit dem 03.08.2026."""
    treffer, geprueft = cga.pruefe_dist()
    assert geprueft > 100, f"nur {geprueft} Visuals geprueft — Korpus verloren?"
    assert not treffer, f"{len(treffer)} Visual(s) neben dem Raster: {treffer[:3]}"
