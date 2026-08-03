#!/usr/bin/env python3
"""
check_palette_monochrome.py — Boutique rubric BC-COLOR-02 structural validator

BC-COLOR-02 (knock-out): "Colour is only semantic (a judgment) or brand reference —
never decorative or to distinguish equal-rank categories."

Der `machine_hint` der Regel benennt den pruefbaren Kern genau: *categorical series
coloured by N distinct hues without semantic role*. Genau das laesst sich am
mitgelieferten Theme entscheiden — `dataColors` ist die Palette, mit der Power BI
gleichrangige Kategorien einfaerbt. Traegt sie mehrere Farbtoene, unterscheidet die
Farbe Kategorien statt zu urteilen.

Die Schwelle ist ABGELEITET, nicht erfunden
-------------------------------------------
Eine Gradzahl aus der Luft waere hier das uebliche Problem: sie entscheidet die Regel
im Code. Stattdessen liefert das Theme seinen eigenen Massstab. Es fuehrt semantische
Tokens (`good`, `bad`, `neutral`) — und deren kleinster Farbtonabstand ist der kleinste
Unterschied, den dieses Theme selbst als *bedeutungstragend* behandelt. Erreicht die
kategoriale Palette diesen Abstand, unterscheidet sie nach dem eigenen Massstab des
Themes durch Farbton.

Gemessen am 03.08.2026 (Aurora Monochromatic Light):
  * dataColors: Farbtoene 187.9°–189.3° → Spanne **1.4°**
  * semantisch: bad 13.5° · neutral 38.5° · good 147.9° → kleinster Abstand **25.0°**
Der Abstand zwischen Ist und Schwelle ist damit knapp achtzehnfach — die Regel ist
erfuellt, und eine Regenbogenpalette (Spanne >100°) fiele sofort auf.

Usage:
    python tooling/validation/check_palette_monochrome.py            # Bericht, exit 0
    python tooling/validation/check_palette_monochrome.py --strict   # Verstoss = exit 1

Exit codes:
    0 — jede Palette bleibt unter ihrem abgeleiteten Schwellwert (oder ohne --strict)
    1 — mindestens eine Palette unterscheidet nach Farbton, oder kein Theme gefunden
"""
from __future__ import annotations

import argparse
import colorsys
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"

#: Tokens, deren Farbe ein URTEIL traegt. Sie duerfen und sollen sich im Farbton
#: unterscheiden — sie sind der Massstab, nicht der Prueffall.
_SEMANTISCH = ("good", "bad", "neutral")


def farbton(hexwert: str) -> Optional[float]:
    """Hex → Farbton in Grad, oder None bei Grau/Unlesbarem.

    Grau hat keinen Farbton (Saettigung 0) — ein neutraler Ton in der Palette ist kein
    Kategorienunterschied und darf die Spanne nicht aufblaehen. Das ist keine Ausnahme,
    sondern die Definition: was nicht bunt ist, unterscheidet nicht durch Buntheit.
    """
    h = (hexwert or "").lstrip("#")
    if len(h) != 6:
        return None
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None
    ton, _, saettigung = colorsys.rgb_to_hls(r, g, b)
    return None if saettigung < 0.10 else ton * 360


def _abstand(a: float, b: float) -> float:
    """Farbtonabstand auf dem Kreis — 350° und 10° sind 20° auseinander, nicht 340°."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def spanne(hexwerte: list[str]) -> float:
    """Groesster Farbtonabstand innerhalb einer Palette. Rein."""
    toene = [t for t in (farbton(c) for c in hexwerte) if t is not None]
    if len(toene) < 2:
        return 0.0
    return max(_abstand(a, b) for i, a in enumerate(toene) for b in toene[i + 1:])


def schwelle(theme: dict) -> Optional[float]:
    """Kleinster Farbtonabstand der SEMANTISCHEN Tokens — der Massstab des Themes.

    None, wenn das Theme keine zwei bunten semantischen Tokens fuehrt: dann hat es
    keinen eigenen Massstab, und einen zu erfinden waere genau das, was dieser Aufbau
    vermeiden soll.
    """
    toene = [t for t in (farbton(theme.get(k, "")) for k in _SEMANTISCH) if t is not None]
    if len(toene) < 2:
        return None
    return min(_abstand(a, b) for i, a in enumerate(toene) for b in toene[i + 1:])


def pruefe(theme: dict) -> Optional[str]:
    """Grund des Verstosses, oder None. Rein — der Kern, den die Tests fahren."""
    grenze = schwelle(theme)
    if grenze is None:
        return ("Theme fuehrt keine zwei bunten semantischen Tokens "
                f"({', '.join(_SEMANTISCH)}) — ohne eigenen Massstab ist die Regel "
                f"nicht entscheidbar.")
    ist = spanne(list(theme.get("dataColors") or []))
    if ist >= grenze:
        return (f"kategoriale Palette spannt {ist:.1f}° Farbton, das Theme behandelt "
                f"schon {grenze:.1f}° als bedeutungstragend — Farbe unterscheidet "
                f"Kategorien statt zu urteilen")
    return None


def aktives_theme(report: Path) -> Optional[Path]:
    """Die Themedatei, die `report.json` als `customTheme` benennt — sonst None.

    Warum nicht einfach jede registrierte Ressource pruefen: der erste Entwurf tat das
    und meldete 16 Verstoesse. Alle betrafen `Brand_Rose__Monochromatic__…json`, eine
    Datei, die in jedem Report liegt, **nicht aktiv** ist und ueber 300 Farben ueber den
    ganzen Farbkreis fuehrt. Ein Gate, das eine nicht angewandte Datei rot macht,
    meldet etwas, das im Report nicht zu sehen ist.

    (Dass diese Datei existiert, ihren eigenen Namen widerlegt und ungenutzt
    mitgeliefert wird, ist ein eigener Befund — er steht in §19, nicht in diesem Gate.)
    """
    rj = report / "definition" / "report.json"
    if not rj.is_file():
        return None
    name = (((json.loads(rj.read_text(encoding="utf-8")) or {}).get("themeCollection")
             or {}).get("customTheme") or {}).get("name")
    if not name:
        return None
    kandidat = report / "StaticResources" / "RegisteredResources" / name
    return kandidat if kandidat.is_file() else None


def pruefe_dist(dist: Optional[Path] = None) -> tuple[list[tuple[str, str]], int]:
    """→ ([(themedatei, grund)], geprueft). Nur AKTIVE Themes."""
    wurzel = dist or _DIST
    treffer: list[tuple[str, str]] = []
    geprueft = 0
    for report in sorted(wurzel.glob("*.Report")):
        tj = aktives_theme(report)
        if tj is None:
            # Ein Report ohne aufloesbares Custom-Theme ist ein Befund, kein Ueberspringen:
            # BC-BRAND-01 verlangt ausdruecklich ein komponiertes Theme.
            treffer.append((report.name, "kein aufloesbares customTheme in report.json"))
            continue
        try:
            theme = json.loads(tj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            treffer.append((f"{report.name}/{tj.name}", "Theme ist kein gueltiges JSON"))
            continue
        if "dataColors" not in theme:
            continue                      # keine Palette → kein Prueffall
        geprueft += 1
        if grund := pruefe(theme):
            treffer.append((f"{report.name}/{tj.name}", grund))
    return treffer, geprueft


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-COLOR-02 Paletten-Validator")
    parser.add_argument("--strict", action="store_true", help="Verstoss = exit 1")
    args = parser.parse_args()

    treffer, geprueft = pruefe_dist()
    if not geprueft:
        # Null geprueft als „sauber" zu melden ist die Luege, gegen die dieser
        # Regelsatz gebaut ist.
        print("ERROR: kein Theme mit `dataColors` gefunden — nichts geprueft.",
              file=sys.stderr)
        return 1
    for datei, grund in treffer:
        print(f"    ⚠ {datei}: {grund} — BC-COLOR-02")
    print(f"\nBC-COLOR-02: {len(treffer)} von {geprueft} Palette(n) unterscheiden nach "
          f"Farbton (Schwelle je Theme aus seinen eigenen semantischen Tokens).")
    if args.strict and treffer:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
