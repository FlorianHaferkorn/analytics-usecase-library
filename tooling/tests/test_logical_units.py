"""Ein Koordinatensystem: Geometrie in Logical Units (Task L13).

Die Tests hier pruefen die beiden Befunde, die L13 ausgeloest haben — und zwar so,
dass ein Rueckfall auffaellt, nicht nur die Reparatur.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tooling.generator_core.ir.compiler import _DETAIL_LU, _OVERVIEW_LU
from tooling.superversion.layer_tools.layout_grid import GridParams, load, to_pixels


def _grid_params() -> dict:
    g = load("production")
    return {"cols": g.cols, "rows": g.rows, "gutter": g.gutter,
            "outer": g.outer, "width": g.width, "height": g.height}


def lu_to_pixels(col, row, cs, rs, canvas_w, canvas_h, grid):
    """Testhelfer: LU→px fuer eine ABWEICHENDE Leinwand (der Kern des Befunds)."""
    return to_pixels(col, row, cs, rs, GridParams(
        cols=grid["cols"], rows=grid["rows"], gutter=grid["gutter"],
        outer=grid["outer"], width=canvas_w, height=canvas_h))

_ROOT = Path(__file__).resolve().parents[2]
_GRID = _ROOT / "core/templates/page_templates/tokens/layout_grid.yaml"
_SLOT_POS_TS = _ROOT / "core/templates/page_templates/preview/src/grid/slot-pos.ts"
_COMPILER = _ROOT / "tooling/generator_core/ir/compiler.py"

_CANVASES = [(1280, 720), (1920, 1080)]


def _col_span(px: dict, canvas_w: int, p: dict) -> tuple[float, float]:
    lu_w = (canvas_w - 2 * p["outer"] - (p["cols"] - 1) * p["gutter"]) / p["cols"]
    schritt = lu_w + p["gutter"]
    return (px["x"] - p["outer"]) / schritt, (px["width"] + p["gutter"]) / schritt


@pytest.mark.parametrize("layout", [_OVERVIEW_LU, _DETAIL_LU], ids=["overview", "detail"])
def test_same_slot_yields_same_column_on_every_canvas(layout):
    """Befund 1: die Brueche waren gegen 1920 geschrieben, die LU gegen 1280.

    Auf der design_base lag der erste Slot bei Spalte -0.10 — ausserhalb des Rasters.
    Jetzt muss derselbe Slot auf JEDER Leinwand dieselbe Spalte und Spanne ergeben;
    genau das ist die Zusicherung, die „proportional skalierbar" ueberhaupt bedeutet.
    """
    p = _grid_params()
    for slot, lu in layout.items():
        werte = []
        for w, h in _CANVASES:
            px = lu_to_pixels(*lu, canvas_w=w, canvas_h=h, grid=p)
            werte.append(_col_span(px, w, p))
        (c1, s1), (c2, s2) = werte
        assert c1 == pytest.approx(c2, abs=1e-9), f"{slot}: Spalte driftet {c1} vs {c2}"
        assert s1 == pytest.approx(s2, abs=1e-9), f"{slot}: Spanne driftet {s1} vs {s2}"


def test_main_columns_are_whole_units():
    """Befund 2: `Main_1` ergab 3.93 statt 4 Spalten.

    Ursache war kein Rundungsfehler, sondern dass `gutter`/`outer_margin` absolut
    blieben, waehrend die Brueche mitskalierten. Diese Zahl ist der Beweis, dass die
    Aufloesung die Abstaende jetzt einschliesst.
    """
    p = _grid_params()
    for w, h in _CANVASES:
        for slot in ("Main_1", "Main_2", "Main_3"):
            px = lu_to_pixels(*_OVERVIEW_LU[slot], canvas_w=w, canvas_h=h, grid=p)
            _, spanne = _col_span(px, w, p)
            assert spanne == pytest.approx(4.00, abs=1e-9), f"{slot}@{w}: {spanne}"


def test_detail_columns_fill_the_grid_exactly():
    """Slicer (2) + Inhalt (8) + Aktionspanel (2) = 12 — ohne Rest und ohne Ueberlappung."""
    spannen = {s: lu[2] for s, lu in _DETAIL_LU.items()}
    assert spannen["Slicer_Pane"] + spannen["Smart_Narrative"] + spannen["ActionPanel"] == 12
    assert _DETAIL_LU["ActionPanel"][0] + _DETAIL_LU["ActionPanel"][2] == 12


def test_formula_mirrors_slot_pos_ts():
    """Die Python-Aufloesung spiegelt `slot-pos.ts` — belegt, nicht nachgelesen.

    Zwei Implementierungen derselben Formel sind erst dann keine Drift-Quelle, wenn
    eine Pruefung sie zusammenhaelt. Geprueft wird der Vertrag im TS-Quelltext, weil
    er dort als CSS-`calc()` steht und nicht ausgefuehrt werden kann.
    """
    ts = _SLOT_POS_TS.read_text(encoding="utf-8")
    for erwartet in (
        "var(--outer) + ${col} * (var(--lu-w) + var(--gutter))",
        "var(--outer) + ${row} * (var(--lu-h) + var(--gutter))",
        "${cs} * var(--lu-w) + ${cs - 1} * var(--gutter)",
        "${rs} * var(--lu-h) + ${rs - 1} * var(--gutter)",
    ):
        assert erwartet in ts, f"slot-pos.ts fuehrt die Formel nicht mehr so: {erwartet}"


def test_spacing_obeys_the_8px_doctrine():
    """INVARIANT A7 gilt fuer ABSTAENDE — dort ist sie erfuellbar und wird geprueft.

    Die abgeleitete Logical Unit ist davon ausdruecklich ausgenommen: sie ist ein
    Restwert (`lu_w` = 1040/12 = 86.67 auf der design_base) und darf krumm sein, weil
    sie niemand schreibt. Gemessen am 02.08.2026: auf keiner der beiden Leinwaende
    macht ein Aussenrand aus der 8er-Skala BEIDE Achsen 8er-rein, bei 1920x1080 ist
    die Vertikale mit 12 Zeilen gar nicht loesbar. Entscheidung Flo: Weg (a).
    """
    sp = (yaml.safe_load(_GRID.read_text(encoding="utf-8")) or {}).get("spacing") or {}
    assert sp, "layout_grid.yaml fuehrt keine Abstaende mehr"
    for name, wert in sp.items():
        assert wert % 8 == 0, f"{name}={wert} liegt nicht auf der 8er-Skala (INVARIANT A7)"


def test_no_canvas_fractions_return_to_the_authoring_source():
    """Rueckfall-Waechter: keine handgeschriebenen Leinwandbrueche im Compiler.

    Ohne diesen Test ist die Umstellung eine Momentaufnahme. Der naechste Slot, der
    „schnell mal" als 0.0167 dazukommt, bringt beide Befunde zurueck — und faellt
    nicht auf, weil er auf der Autorenleinwand richtig aussieht.
    """
    quelle = _COMPILER.read_text(encoding="utf-8")
    for verboten in ("_OVERVIEW_LAYOUT", "_DETAIL_LAYOUT"):
        assert verboten not in quelle, (
            f"{verboten} ist zurueck — Geometrie gehoert in Logical Units (_*_LU), "
            "die Aufloesung nach Pixel in lu_to_pixels()."
        )
    # Verdaechtige Bruchliterale (0.0167, 0.9666 …) — nur in CODE-Zeilen. Kommentare
    # duerfen die alten Werte nennen; die Erklaerung des Fehlers ist nicht der Fehler.
    # (Erster Lauf dieses Tests hat genau daran angeschlagen — an meinem eigenen
    # Kommentar, der die Ursache dokumentiert.)
    code = "\n".join(z for z in quelle.splitlines() if not z.lstrip().startswith("#"))
    verdaechtig = re.findall(r"0\.\d{4}", code)
    assert not verdaechtig, f"Leinwandbrueche im Compiler gefunden: {sorted(set(verdaechtig))}"


def test_slicer_keeps_its_documented_pixel_floor():
    """Der Datums-Slicer bleibt ueber 76 px — die Plattform-Zusicherung schlaegt das Raster.

    Ein Dropdown-Slicer braucht Header 28 + Selektor 32 + Padding; darunter meldet die
    offizielle CLI `PBIR_SLICER_HEIGHT_BELOW_FLOOR` und das Control schneidet im Service
    ab. Genau deshalb ist die Vertikale fraktional geblieben statt auf 12 Zeilen gezwungen
    zu werden — ein Raster, das eine dokumentierte Zusicherung bricht, gewinnt nicht.
    """
    p = _grid_params()
    px = lu_to_pixels(*_OVERVIEW_LU["Slicer_Date"], canvas_w=1920, canvas_h=1080, grid=p)
    assert px["height"] >= 76, f"Slicer-Hoehe {px['height']:.1f} px unter dem 76-px-Boden"
