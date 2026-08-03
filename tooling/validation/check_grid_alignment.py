#!/usr/bin/env python3
"""
check_grid_alignment.py — Boutique rubric BC-LAYOUT-01 structural validator

BC-LAYOUT-01: "Strict grid; all card edges and chart baselines aligned to the grid."
Bis zum 03.08.2026 war das eine Regel ohne Pruefer — sie stand auf `check: structural`
und niemand konnte sie entscheiden. Pruefbar ist sie erst, seit L13 die Geometrie in
Logical Units legt und `layout_grid.to_pixels()` die einzige Aufloesungsstelle ist:
damit gibt es eine Sollposition, gegen die sich eine Istposition rechnen laesst.

Waagerecht ganzzahlig, senkrecht frei — und das ist keine Nachlaessigkeit
-------------------------------------------------------------------------
L13 hat ausdruecklich entschieden: die Spaltenachse ist ganzzahlig, die Zeilenachse
fraktional. Ein 12-Zeilen-Zwang liesse zwei Slots kollidieren und braeche die
dokumentierte 76-px-Mindesthoehe des Slicers. Dieser Pruefer bildet genau das ab —
er prueft `x` und `width` gegen das Raster und laesst `y`/`height` in Ruhe. Wer hier
spaeter die Zeilenachse mitprueft, hebt eine Entscheidung auf, statt eine Luecke zu
schliessen.

Erster Lauf (03.08.2026): 183 von 188 Visuals sitzen exakt auf der Spalte. Die
Ausreisser liegen alle in EINEM Report und tragen `span = 3.929` — exakt die Zahl, die
L13 als Defekt gefunden und auf 4,00 korrigiert hat. Der Report wurde also vor L13
erzeugt und nie neu gebaut. Genau dafuer gibt es den Pruefer.

Usage:
    python tooling/validation/check_grid_alignment.py            # Bericht, exit 0
    python tooling/validation/check_grid_alignment.py --strict   # jede Abweichung = exit 1

Exit codes:
    0 — alle Visuals auf dem Raster (oder ohne --strict)
    1 — mindestens ein Visual daneben (BC-LAYOUT-01), oder kein Report gefunden
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"

#: Rundungsspielraum in PIXELN. Der Emitter rundet Sollpositionen auf ganze Pixel, also
#: sind +/-1 px kein Befund. Die real gefundenen Abweichungen lagen bei 5–24 px — die
#: Luecke dazwischen ist gross genug, dass die Schwelle keine Ermessensfrage ist.
TOLERANZ_PX = 1


def rasterlagen(params) -> dict[tuple[int, int], tuple[int, int]]:
    """Alle waagerechten Sollpositionen: (Spalte, Spanne) → (x, width) in Pixeln.

    **Erzeugt mit `layout_grid.to_pixels`, nicht mit einer Umkehrformel.** Der erste
    Entwurf rechnete `col = (x - outer) / (lu_w + gutter)` selbst — und der
    Konsolidierungs-Waechter aus §11 hat das zu Recht als zweiten LU→px-Resolver
    gemeldet. Der Einwand ist nicht formal: aendert sich `to_pixels`, driftet eine
    handgeschriebene Umkehrung still mit, und der Pruefer bestaetigt dann ein Raster,
    das es nicht mehr gibt. Statt der Umkehrung wird der Sollraum aufgezaehlt — 12×12
    Kandidaten, und die einzige Aufloesungsstelle bleibt die einzige.
    """
    from tooling.superversion.layer_tools.layout_grid import to_pixels

    out: dict[tuple[int, int], tuple[int, int]] = {}
    for col in range(params.cols + 1):
        for span in range(1, params.cols + 1 - col):
            px = to_pixels(col, 0, span, 1, params)
            out[(col, span)] = (round(px["x"]), round(px["width"]))
    return out


def abweichung(pos: dict, params) -> Optional[str]:
    """Grund der Rasterverletzung, oder None. Rein — der Kern, den die Tests fahren."""
    x, w = pos["x"], pos["width"]
    for (col, span), (sx, sw) in rasterlagen(params).items():
        if abs(x - sx) <= TOLERANZ_PX and abs(w - sw) <= TOLERANZ_PX:
            return None
    # Naechstliegende Sollposition nennen — eine blosse Ablehnung waere fuer den
    # Leser wertlos, er muesste das Raster im Kopf nachrechnen.
    (col, span), (sx, sw) = min(rasterlagen(params).items(),
                                key=lambda kv: abs(x - kv[1][0]) + abs(w - kv[1][1]))
    return (f"x={x} w={w} liegt auf keiner Rasterspalte; naechste waere "
            f"Spalte {col} Spanne {span} → x={sx} w={sw}")


def _report_name(visual_json: Path) -> str:
    for teil in visual_json.parents:
        if teil.name.endswith(".Report"):
            return teil.name[: -len(".Report")]
    return visual_json.parent.name


def pruefe_dist(dist: Optional[Path] = None) -> tuple[list[tuple[str, str, str, str]], int]:
    """→ ([(report, page, visual, grund)], geprueft). Leere Liste = alles auf dem Raster."""
    from tooling.superversion.layer_tools.layout_grid import load as grid_load

    p = grid_load()
    wurzel = dist or _DIST
    treffer: list[tuple[str, str, str, str]] = []
    geprueft = 0
    for vj in sorted(wurzel.glob("*.Report/definition/pages/*/visuals/*/visual.json")):
        pos = (json.loads(vj.read_text(encoding="utf-8")) or {}).get("position") or {}
        if not {"x", "width"} <= set(pos):
            continue
        geprueft += 1
        if grund := abweichung(pos, p):
            # parents: [0]=<Visual>, [1]=visuals, [2]=<Page> — [1] waere immer "visuals".
            treffer.append((_report_name(vj), vj.parents[2].name, vj.parent.name, grund))
    return treffer, geprueft


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-LAYOUT-01 Rasterbindungs-Validator")
    parser.add_argument("--strict", action="store_true",
                        help="jede Rasterabweichung = exit 1")
    args = parser.parse_args()

    if not _DIST.is_dir():
        print(f"ERROR: {_DIST} fehlt — ungeprueft ist nicht dasselbe wie sauber.",
              file=sys.stderr)
        return 1

    treffer, geprueft = pruefe_dist()
    if not geprueft:
        # Null geprueft und „keine Verletzung" zu melden waere die Luege, gegen die
        # dieser ganze Regelsatz gebaut ist.
        print("ERROR: kein einziges Visual mit Position gefunden — nichts geprueft.",
              file=sys.stderr)
        return 1

    for rep, page, vis, grund in treffer:
        print(f"    ⚠ {rep}/{page}/{vis}: {grund} — BC-LAYOUT-01")
    print(f"\nBC-LAYOUT-01: {len(treffer)} von {geprueft} Visual(s) nicht auf der "
          f"Rasterspalte (waagerecht ganzzahlig; die Zeilenachse ist laut L13 bewusst frei).")
    if args.strict and treffer:
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    raise SystemExit(main())
