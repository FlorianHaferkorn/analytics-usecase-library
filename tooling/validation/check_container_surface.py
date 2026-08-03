#!/usr/bin/env python3
"""
check_container_surface.py — Boutique rubric BC-LAYOUT-02 structural validator

BC-LAYOUT-02: "Grouping by whitespace (zone_gap > gutter > padding); no decorative
boxes/borders."

Warum diese Regel eine Entscheidung brauchte, bevor sie einen Pruefer bekam
--------------------------------------------------------------------------
Woertlich gelesen verbietet sie jedes Kartensystem — und genau darauf bauen zwei
andere Regeln auf (BC-LAYOUT-03 Hero-Karte, BC-BRAND-01 komponiertes Theme). Das
aktive Theme setzt fuer JEDES Visual Hintergrund, Rahmen und Schatten; kein einziges
der 188 Visuals ueberschreibt das. Ein Pruefer, der das per Schwellenwert entschieden
haette, haette die Doktrinfrage im Code beantwortet.

Entschieden am 03.08.2026 (Weg A): das Kartensystem ist legitim, die Regel meint
"keine Dekoration **ueber** das Kartensystem hinaus". Die sanktionierte Obergrenze
steht in `tokens/color_semantics.yaml` → `container_baseline` — dort, wo `surface.card`
ohnehin seit jeher steht. Dieser Pruefer misst gegen sie, nicht gegen "nichts".

Drei Haelften (die Regel nennt zwei, das Artefakt hat drei Ebenen)
------------------------------------------------------------------
1. **Weissraum-Ordnung** aus `tokens/layout_grid.yaml`: zone_gap > gutter > padding.
   Kippt die Ordnung, gruppiert nicht mehr der Weissraum, sondern der Zufall.
2. **Theme** — die Container-Objekte des aktiven Themes muessen in der Grundlinie
   bleiben. Das ist die Ebene, auf der heute alles gesetzt wird.
3. **Visual** — kein einzelnes Visual darf die Grundlinie ueberschreiten.

Usage:
    python tooling/validation/check_container_surface.py            # Bericht, exit 0
    python tooling/validation/check_container_surface.py --strict   # Verstoss = exit 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_TOKENS = REPO / "core/templates/page_templates/tokens"


def grundlinie() -> dict[str, Any]:
    """Die sanktionierte Obergrenze. Wirft, wenn sie fehlt — statt alles durchzulassen."""
    doc = yaml.safe_load((_TOKENS / "color_semantics.yaml").read_text(encoding="utf-8")) or {}
    basis = doc.get("container_baseline")
    if not basis:
        raise ValueError(
            "color_semantics.yaml fuehrt keine `container_baseline` — ohne sanktionierte "
            "Obergrenze waere jede Dekoration erlaubt, und der Pruefer bestuende leer.")
    return basis


def _erste(objekt: Any) -> dict:
    """PBIR-Objekte sind Listen von {properties: {...}}; hier interessiert die erste."""
    if isinstance(objekt, list) and objekt:
        return (objekt[0] or {}).get("properties", objekt[0]) or {}
    return objekt if isinstance(objekt, dict) else {}


def _zahl(wert: Any) -> Optional[float]:
    """Zahl aus einem PBIR-Wert oder einem blanken Literal. None, wenn keine da ist."""
    if isinstance(wert, (int, float)):
        return float(wert)
    if isinstance(wert, dict):
        lit = (((wert.get("expr") or {}).get("Literal") or {}).get("Value"))
        if isinstance(lit, str):
            try:
                return float(lit.rstrip("DLF"))
            except ValueError:
                return None
        return _zahl(lit) if lit is not None else None
    return None


def pruefe_weissraum(spacing: dict) -> list[str]:
    """zone_gap > gutter > padding. Rein."""
    zone = spacing.get("zone_gap")
    gutter = spacing.get("gutter")
    pad = spacing.get("internal_padding")
    if None in (zone, gutter, pad):
        return ["layout_grid.yaml fuehrt nicht alle drei Abstaende (zone_gap/gutter/"
                "internal_padding) — die Ordnung ist dann nicht pruefbar"]
    if not (zone > gutter > pad):
        return [f"Weissraum-Ordnung gekippt: zone_gap {zone} > gutter {gutter} > "
                f"padding {pad} gilt nicht — dann gruppiert nicht mehr der Abstand"]
    return []


def pruefe_container(objekte: dict, basis: dict, wo: str) -> list[str]:
    """Container-Objekte (Theme oder Visual) gegen die Grundlinie. Rein."""
    verstoesse: list[str] = []
    schluessel = {k.lower(): k for k in objekte}

    for verboten in basis.get("never") or []:
        if verboten.lower() in schluessel:
            verstoesse.append(f"{wo}: `{schluessel[verboten.lower()]}` ist ausdruecklich "
                              f"nie erlaubt (container_baseline.never)")

    if "border" in schluessel:
        b = _erste(objekte[schluessel["border"]])
        grenzen = basis.get("border") or {}
        for feld, schranke in (("width", "width_max_px"), ("radius", "radius_max_px")):
            wert = _zahl(b.get(feld))
            if wert is not None and schranke in grenzen and wert > grenzen[schranke]:
                verstoesse.append(f"{wo}: Rahmen-{feld} {wert:g} > Grundlinie "
                                  f"{grenzen[schranke]:g}")

    for name in ("dropshadow", "shadow"):
        if name in schluessel:
            s = _erste(objekte[schluessel[name]])
            g = basis.get("drop_shadow") or {}
            paare = (("transparency", "transparency_min_pct", "unter"),
                     ("shadowDistance", "distance_max_px", "ueber"),
                     ("shadowBlur", "blur_max_px", "ueber"),
                     ("shadowSpread", "spread_max", "ueber"))
            for feld, schranke, richtung in paare:
                wert = _zahl(s.get(feld))
                if wert is None or schranke not in g:
                    continue
                kaputt = wert < g[schranke] if richtung == "unter" else wert > g[schranke]
                if kaputt:
                    verstoesse.append(f"{wo}: Schatten-{feld} {wert:g} {richtung} "
                                      f"Grundlinie {g[schranke]:g} — kraeftiger als "
                                      f"das sanktionierte Kartensystem")

    if "padding" in schluessel:
        p = _erste(objekte[schluessel["padding"]])
        grenze = (basis.get("padding") or {}).get("max_px")
        for seite in ("left", "right", "top", "bottom"):
            wert = _zahl(p.get(seite))
            if wert is not None and grenze is not None and wert > grenze:
                verstoesse.append(f"{wo}: padding.{seite} {wert:g} > Grundlinie {grenze:g}")
    return verstoesse


def pruefe_dist(dist: Optional[Path] = None) -> tuple[list[str], int]:
    """→ ([grund], geprueft)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from check_palette_monochrome import aktives_theme

    basis = grundlinie()
    wurzel = dist or _DIST
    treffer: list[str] = []
    geprueft = 0

    spacing = (yaml.safe_load((_TOKENS / "layout_grid.yaml").read_text(encoding="utf-8"))
               or {}).get("spacing") or {}
    treffer += pruefe_weissraum(spacing)
    geprueft += 1

    for report in sorted(wurzel.glob("*.Report")):
        if (tj := aktives_theme(report)) is not None:
            theme = json.loads(tj.read_text(encoding="utf-8"))
            stern = ((theme.get("visualStyles") or {}).get("*") or {}).get("*") or {}
            geprueft += 1
            treffer += pruefe_container(stern, basis, f"{report.name} Theme '*'")

    for vj in sorted(wurzel.glob("*.Report/definition/pages/*/visuals/*/visual.json")):
        objekte = ((json.loads(vj.read_text(encoding="utf-8")) or {}).get("visual")
                   or {}).get("visualContainerObjects") or {}
        if not objekte:
            continue
        geprueft += 1
        treffer += pruefe_container(objekte, basis,
                                    f"{vj.parents[2].name}/{vj.parent.name}")
    return treffer, geprueft


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-LAYOUT-02 Container-Validator")
    parser.add_argument("--strict", action="store_true", help="Verstoss = exit 1")
    args = parser.parse_args()

    treffer, geprueft = pruefe_dist()
    if geprueft < 2:
        print("ERROR: weder Theme noch Weissraum-Tokens gefunden — nichts geprueft.",
              file=sys.stderr)
        return 1
    for grund in treffer:
        print(f"    ⚠ {grund} — BC-LAYOUT-02")
    print(f"\nBC-LAYOUT-02: {len(treffer)} Verstoss/Verstoesse in {geprueft} geprueften "
          f"Ebenen (Weissraum-Ordnung, Theme, Visual) gegen die sanktionierte "
          f"Kartensystem-Grundlinie.")
    if args.strict and treffer:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
