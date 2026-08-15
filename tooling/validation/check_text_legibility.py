#!/usr/bin/env python3
"""
check_text_legibility.py — Boutique rubric BC-TYPE-04 structural validator

BC-TYPE-04: "No ALL-CAPS for running text; every reader-facing size ≥ minimum."

Zwei Haelften, zwei governte Quellen — keine erfundene Zahl
------------------------------------------------------------
1. **Mindestgroesse**: `tokens/typography.yaml` fuehrt je Rolle ein `size_min_pt`. Die
   kleinste dieser Groessen ist der Boden, den das Haus sich selbst gesetzt hat; die
   `textClasses` des aktiven Themes duerfen ihn nicht unterschreiten. Kein Schwellwert
   im Code — der Boden wird gelesen.
2. **Versalien**: Fliesstext in Grossbuchstaben ist schwerer zu lesen, weil die
   Wortsilhouette verschwindet. Kurze Marker (`YTD`, `OK`, `EBIT`) sind KEIN Fliesstext,
   deshalb greift die Regel erst ab einer Laenge, ab der ein Text kein Etikett mehr
   sein kann.

Gemessen am 03.08.2026: 79 lesbare Texte im Bestand, **0** davon durchgaengig gross;
Theme-`textClasses` bei 40/16/14/12 pt gegen einen governten Boden von 10 pt.

Usage:
    python tooling/validation/check_text_legibility.py            # Bericht, exit 0
    python tooling/validation/check_text_legibility.py --strict   # Verstoss = exit 1

Exit codes:
    0 — kein Versalien-Fliesstext, keine Groesse unter dem governten Boden
    1 — mindestens ein Verstoss (mit --strict), oder nichts zu pruefen gefunden
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_TYPO = REPO / "core/templates/page_templates/tokens/typography.yaml"

#: Ab dieser Zeichenzahl ist ein Text kein Etikett mehr, sondern Fliesstext. Bewusst
#: grosszuegig: `QUARTAL 1` (9), `EBIT MARGE` (10) und `YTD VS PLAN` (11) sollen NICHT
#: anschlagen — die Regel zielt auf Saetze, nicht auf Marker.
FLIESSTEXT_AB = 25

#: Wo im PBIR lesbarer Text steht. Titel/Untertitel/Textbox sind die Stellen, die ein
#: Leser als Sprache wahrnimmt; Feldnamen und IDs sind keine Prosa.
_TEXT_MUSTER = re.compile(r'"Value":\s*"\'([^\']{3,300})\'"')


def governter_boden() -> float:
    """Kleinste `size_min_pt` aus `typography.yaml`. Wirft, wenn die Datei nichts hergibt."""
    doc = yaml.safe_load(_TYPO.read_text(encoding="utf-8")) or {}
    groessen = [float(v["size_min_pt"]) for v in (doc.get("scale") or {}).values()
                if isinstance(v, dict) and v.get("size_min_pt") is not None]
    if not groessen:
        raise ValueError(f"{_TYPO} fuehrt keine `size_min_pt` — ohne governten Boden "
                         f"waere jede Groesse gross genug.")
    return min(groessen)


def ist_versalien_fliesstext(text: str) -> bool:
    """Durchgehend gross UND lang genug, um kein Etikett mehr zu sein. Rein.

    `text.isupper()` allein genuegt nicht: es ist auch fuer `"2026-Q1"` False und fuer
    `"OK"` True. Die Laengengrenze traegt die Unterscheidung.
    """
    buchstaben = [c for c in text if c.isalpha()]
    if len(buchstaben) < FLIESSTEXT_AB:
        return False
    return all(c.isupper() for c in buchstaben)


def pruefe_groessen(theme: dict, boden: float) -> list[str]:
    """Theme-`textClasses` unter dem governten Boden. Rein."""
    zu_klein = []
    for rolle, spec in (theme.get("textClasses") or {}).items():
        groesse = (spec or {}).get("fontSize")
        if groesse is not None and float(groesse) < boden:
            zu_klein.append(f"textClass '{rolle}' {groesse} pt < governter Boden {boden:g} pt")
    return zu_klein


def pruefe_dist(dist: Optional[Path] = None) -> tuple[list[tuple[str, str]], int]:
    """→ ([(fundort, grund)], geprueft)."""
    from check_palette_monochrome import aktives_theme   # eine Quelle fuer „welches Theme"

    wurzel = dist or _DIST
    boden = governter_boden()
    treffer: list[tuple[str, str]] = []
    geprueft = 0

    for report in sorted(wurzel.glob("*.Report")):
        if (tj := aktives_theme(report)) is not None:
            theme = json.loads(tj.read_text(encoding="utf-8"))
            geprueft += 1
            for grund in pruefe_groessen(theme, boden):
                treffer.append((f"{report.name}/{tj.name}", grund))

    for vj in sorted(wurzel.glob("*.Report/definition/pages/*/visuals/*/visual.json")):
        roh = vj.read_text(encoding="utf-8")
        for text in _TEXT_MUSTER.findall(roh):
            geprueft += 1
            if ist_versalien_fliesstext(text):
                treffer.append((f"{vj.parents[2].name}/{vj.parent.name}",
                                f"Fliesstext durchgaengig gross: {text[:60]!r}"))
    return treffer, geprueft


def main() -> int:
    parser = argparse.ArgumentParser(description="BC-TYPE-04 Lesbarkeits-Validator")
    parser.add_argument("--strict", action="store_true", help="Verstoss = exit 1")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    treffer, geprueft = pruefe_dist()
    if not geprueft:
        print("ERROR: weder Theme noch Text gefunden — nichts geprueft.", file=sys.stderr)
        return 1
    for ort, grund in treffer:
        print(f"    ⚠ {ort}: {grund} — BC-TYPE-04")
    print(f"\nBC-TYPE-04: {len(treffer)} Verstoss/Verstoesse in {geprueft} geprueften "
          f"Texten und Theme-Klassen.")
    if args.strict and treffer:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
