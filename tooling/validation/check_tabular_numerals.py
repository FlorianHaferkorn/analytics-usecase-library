#!/usr/bin/env python3
"""
check_tabular_numerals.py — Boutique rubric BC-TYPE-02 (STRUKTURELLES GATE seit 05.08.2026)

BC-TYPE-02: Tabellenziffern in jeder senkrecht verglichenen Zahlenspalte (Craft-Core §5.2)
— damit die Stellen untereinander stehen und das Auge eine Spalte hinunter vergleichen kann.

Bis 05.08.2026 war das ein ADVISORY-Reporter mit der Begruendung, Power BI biete keinen
Umschalter fuer Tabellenziffern. Das stimmt — und war trotzdem der falsche Schluss. Wenn
die Eigenschaft nicht existiert, ist die Schriftwahl der einzige Hebel, und DIE ist im
Theme nachlesbar. Pruefbar war die Regel also die ganze Zeit; es fehlte nur die Tatsache,
welche Schnitte Tabellenziffern haben.

Diese Tatsache steht jetzt gemessen in `tokens/typography.yaml` (`tabular_numeral_fonts` /
`proportional_numeral_fonts`, mit Methode und Quelle). Der Fund, der das lohnend macht:
**Segoe UI Light hat PROPORTIONALE Ziffern** (vier verschiedene Vorbreiten), Regular und
Bold nicht. Eine Zahlenflaeche in Light verletzt die Regel, und man sieht es der
Theme-Datei nicht an.

Geprueft werden die Flaechen, auf denen Zahlen SENKRECHT verglichen werden:
Tabellen-/Matrixwerte, die Werteachse und Datenbeschriftungen. Ueberschriften, Legenden
und Fliesstext sind ausgenommen — dort steht keine Zahlenspalte.

Usage:
    python tooling/validation/check_tabular_numerals.py            # Bericht, rc=0/1
    python tooling/validation/check_tabular_numerals.py --strict   # rc=1 bei Verstoss
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_TOKENS = REPO / "core/templates/page_templates/tokens/typography.yaml"

# Theme-Rollen, auf denen Zahlen senkrecht verglichen werden. `title`/`subTitle`/
# `legend`/`subheader` fehlen bewusst — dort steht Text, keine Spalte.
NUMERIC_SURFACES = {"values", "total", "columnHeaders", "rowHeaders",
                    "valueAxis", "labels", "dataLabels", "callout", "calloutValue"}


def _fonts() -> tuple[set[str], dict[str, str]]:
    """(Schnitte mit Tabellenziffern, {Schnitt: Beleg} fuer proportionale)."""
    t = yaml.safe_load(_TOKENS.read_text(encoding="utf-8")) or {}
    ok = {e["family"] for e in (t.get("tabular_numeral_fonts") or []) if e.get("family")}
    bad = {e["family"]: e.get("evidence", "") for e in (t.get("proportional_numeral_fonts") or [])
           if e.get("family")}
    return ok, bad


def _theme_numeric_fonts(theme: dict) -> list[tuple[str, str]]:
    """[(Pfad, fontFamily)] fuer jede Zahlenflaeche im Theme."""
    out: list[tuple[str, str]] = []

    def walk(o, path: str, surface: str | None):
        if isinstance(o, dict):
            for k, v in o.items():
                nxt = k if k in NUMERIC_SURFACES else surface
                if k == "fontFamily" and isinstance(v, str) and surface:
                    out.append((path, v))
                walk(v, f"{path}/{k}", nxt)
        elif isinstance(o, list):
            for x in o:
                walk(x, path, surface)

    walk(theme, "", None)
    return out


def violations() -> list[str]:
    """Zahlenflaechen, deren Schrift nachweislich proportionale Ziffern hat."""
    ok, bad = _fonts()
    found: list[str] = []
    for theme_path in sorted(_DIST.glob("*.Report/StaticResources/RegisteredResources/*.json")):
        try:
            theme = json.loads(theme_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        report = next((p for p in theme_path.parts if p.endswith(".Report")), "?")
        for path, fam in _theme_numeric_fonts(theme):
            if fam in bad:
                found.append(f"{report} · {theme_path.name} · {path} → {fam!r} "
                             f"(proportional: {bad[fam]})")
            elif fam not in ok:
                found.append(f"{report} · {theme_path.name} · {path} → {fam!r} "
                             f"(unbelegt — weder in tabular_numeral_fonts noch in "
                             f"proportional_numeral_fonts; Ziffernbreiten messen und eintragen)")
    return found


def main() -> int:
    v = violations()
    ok, bad = _fonts()
    print("BC-TYPE-02 (Tabellenziffern auf Zahlenflaechen):")
    print(f"    belegt tabular:      {sorted(ok)}")
    print(f"    belegt proportional: {sorted(bad)}")
    if not v:
        print("\nOK — keine Zahlenflaeche nutzt eine Schrift mit proportionalen Ziffern.")
        return 0
    print(f"\n{len(v)} Verstoss/Verstoesse:")
    for line in v:
        print(f"    {line}")
    print("\n  Zahlen, die nicht untereinander stehen, kann man eine Spalte hinunter nicht "
          "vergleichen — genau dafuer ist die Spalte da.")
    return 1 if "--strict" in sys.argv else 0


if __name__ == "__main__":
    raise SystemExit(main())
