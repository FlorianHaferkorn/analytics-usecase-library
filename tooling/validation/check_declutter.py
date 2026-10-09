#!/usr/bin/env python3
"""
check_declutter.py — Boutique rubric BC-CHART-04 structural validator

Enforces "decluttered charts — no background fill, drop shadow, gradient or 3D" (Boutique-
Craft-Rubric BC-CHART-04, Craft-Core §5.3). Chartjunk competes with the data; a boutique
chart sits on the page ground with no decorative fill or depth effect. Checkable from the
committed PBIR (no render): a chart visual must not declare a shown `background`, a
`dropShadow`/`shadow`, a `gradient` fill, or a `bevel`/3D object.

Scope note: this is the *unambiguous* chartjunk slice. Gridline heaviness (also named in
BC-CHART-04) needs a rendered judgement of opacity/weight and stays with the LLM judge —
here we verify the emitted objects carry no decorative chrome, and lock that in (a
regression guard, like BC-CHART-08/09). Tables (tableEx) are exempt: light row gridlines
are legitimate table formatting, not chart decoration.

Usage:
    python tooling/validation/check_declutter.py            # all dist reports
    python tooling/validation/check_declutter.py --strict   # any chartjunk = exit 1

Exit codes:
    0 — no chart carries decorative chrome (else 1 when --strict)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"

# Chart families where a background/shadow/gradient/3D is decoration, never information.
_CHART_TYPES = {
    "lineChart", "lineClusteredColumnComboChart", "barChart", "clusteredBarChart",
    "clusteredColumnChart", "stackedBarChart", "stackedColumnChart", "columnChart",
    "hundredPercentStackedBarChart", "hundredPercentStackedColumnChart",
    "waterfallChart", "scatterChart", "areaChart", "stackedAreaChart", "ribbonChart",
}
# Object keys / substrings that mark decorative chrome.
_JUNK_OBJECTS = ("dropshadow", "shadow", "gradient", "bevel", "glow")


def _shown(block_list) -> bool:
    """True if any object block sets show=true (else treats mere presence as inert)."""
    for block in block_list or []:
        props = (block or {}).get("properties") or {}
        show = props.get("show")
        if isinstance(show, dict):
            val = str(((show.get("expr") or {}).get("Literal") or {}).get("Value", "")).lower()
            if val == "true":
                return True
    return False


def chartjunk(visual: dict) -> list[str]:
    """Return the decorative-chrome object names a chart visual declares. Pure — tested."""
    v = visual.get("visual", visual) if isinstance(visual, dict) else {}
    if v.get("visualType") not in _CHART_TYPES:
        return []
    objects = v.get("objects") or {}
    found: list[str] = []
    # a shown background fill is chartjunk on a chart
    if _shown(objects.get("background")):
        found.append("background")
    if _shown(objects.get("plotArea")):
        found.append("plotArea")
    # any shadow/gradient/bevel/glow object present is decoration
    for key in objects:
        kl = key.lower()
        if any(j in kl for j in _JUNK_OBJECTS):
            found.append(key)
    return found


def theme_chartjunk(report_dir: Path) -> list[str]:
    """Chartjunk, das im THEME fuer Chart-Typen gesetzt ist. Der geschlossene blinde Fleck.

    Gemessen am 03.08.2026 war dieser Pruefer gruen und hat nichts geprueft: er las
    ausschliesslich `visual.json`, waehrend das aktive Theme in `visualStyles["*"]["*"]`
    fuer JEDES Visual Hintergrund, Rahmen und Schatten setzt — und **0 von 188** Visuals
    das ueberschreiben. Ein gruener Haken, der an der falschen Stelle sucht, behauptet
    Deckung; das ist schlimmer als ein fehlender.

    Was hier NICHT passiert: das Kartensystem verbieten. Entscheidung Flo vom 03.08.2026
    (Weg A), seit 08.10.2026 auf Meridian D-685 gehoben und am wirksamen Theme (Basistheme +
    eigenes Theme) gemessen — Hintergrund, Rahmen und die dokumentierte Erhebung sind sanktioniert und
    stehen als Obergrenze in `tokens/color_semantics.yaml` → `container_baseline`.
    Dieser Pruefer meldet nur, was DARUEBER hinausgeht, plus die Objekte, die in jeder
    Lesart Zierrat sind (Verlauf, Fase, Glow).
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    _root = str(Path(__file__).resolve().parents[2])
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from check_container_surface import grundlinie, pruefe_container   # eine Grundlinie
    from check_palette_monochrome import aktives_theme                 # eine Theme-Quelle
    from tooling.report_quality.base_theme import basistheme_des_berichts, wirksame_visual_styles

    tj = aktives_theme(report_dir)
    if tj is None:
        return ["kein aufloesbares customTheme — Chart-Chrome nicht pruefbar"]
    theme = json.loads(tj.read_text(encoding="utf-8"))
    # Seit D-685 setzt das Basistheme Rahmen und Schatten: gemessen wird das wirksame Theme.
    basis_theme = basistheme_des_berichts(report_dir)
    if basis_theme is None:
        return ["Basistheme nicht aufloesbar — wirksames Chart-Chrome nicht pruefbar"]
    styles = wirksame_visual_styles(theme, basis_theme)
    basis = grundlinie()
    befunde: list[str] = []
    # `*` gilt fuer alle Typen, danach die namentlich gefuehrten Chart-Familien.
    for typ in ("*", *sorted(set(styles) & _CHART_TYPES)):
        for stil, objekte in (styles.get(typ) or {}).items():
            befunde += pruefe_container(objekte, basis, f"Theme {typ}/{stil}")
    return befunde


def check_report(report_dir: Path) -> list[tuple[str, list[str]]]:
    """Return [(visual_rel_path, [junk objects]), ...] for one .Report directory."""
    out: list[tuple[str, list[str]]] = []
    if theme_befunde := theme_chartjunk(report_dir):
        out.append(("<active theme>", theme_befunde))
    for vj in sorted(report_dir.glob("definition/pages/*/visuals/*/visual.json")):
        try:
            data = json.loads(vj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        junk = chartjunk(data)
        if junk:
            out.append((f"{vj.parent.parent.parent.name}/{vj.parent.name}", junk))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-CHART-04 declutter validator")
    parser.add_argument("--strict", action="store_true", help="Any chartjunk = exit 1")
    args = parser.parse_args()

    reports = sorted(_DIST.glob("*.Report")) if _DIST.is_dir() else []
    violations = 0
    for r in reports:
        for vpath, junk in check_report(r):
            violations += 1
            print(f"    ⚠ {r.name}/{vpath}: decorative chrome {junk} — BC-CHART-04")

    print(f"\nBC-CHART-04: {len(reports)} reports scanned, {violations} chart(s) with chartjunk.")
    if args.strict and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
