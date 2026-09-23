"""layer_tools.design_tokens — DTCG-Emitter für die governten Design-Tokens (L5).

Ein Layer-Tool (Invariante I4: laeuft standalone gegen die blanken YAMLs UND
integriert) neben `visual_library.py`. Es uebersetzt die vorhandenen Token-Dateien
unter `core/templates/page_templates/tokens/` in das **Design Tokens Format** der
W3C Design Tokens Community Group (erste stabile Fassung `v2025.10`).

Warum ueberhaupt ein Interchange-Format
---------------------------------------
Das Zielbild verlangt, denselben Use Case in mehreren Ziel-Werkzeugen darzustellen.
Farbe, Typografie und Raster muessen dafuer in jedem Ziel ankommen — Power BI
(theme.json), HTML/CSS (Custom Properties), Vega-Lite (config). Das Problem ist
ausserhalb BI geloest: DTCG ist genau dieser Austausch-Standard, JSON-basiert, mit
First-Class-Support in Style Dictionary 4. Official-First (D-156): kein Eigenbau,
wo ein Standard existiert.

Warum ERZEUGT und nicht ERSETZT
-------------------------------
Die YAMLs bleiben die Autorenquelle. Das ist keine Bequemlichkeit, sondern eine
Messung: **acht** Konsumenten lesen sie heute, darunter die lebenden Validatoren
`check_font_family`, `check_type_scale`, `check_tabular_numerals` und
`tooling/reporting/format_policy.py`. Sie auf DTCG umzustellen waere ein Umbau mit
acht Bruchstellen fuer einen Gewinn, den auch ein erzeugtes Artefakt liefert.

Damit die beiden Darstellungen nicht auseinanderlaufen, ist die Emission
deterministisch und wird per Drift-Test gegen die eingecheckte Fassung geprueft —
dieselbe Mechanik wie bei den uebrigen generierten Artefakten des Repos.

Was NICHT uebersetzt wird
-------------------------
Nur Farbe, Typografie und Raster. Die semantische Begruendung (ISO 3864-1, IEC 60073,
WCAG-Kontrastnachweise) bleibt in den YAMLs und der Prosa-Governance: DTCG kann sie
nicht tragen, und ein Token ohne seine Begruendung ist im Zweifel schlimmer als
keines — es sieht benutzbar aus, ohne zu sagen, wofuer.

Reines Lesen + Schreiben, keine Engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TOKENS = _REPO_ROOT / "core" / "templates" / "page_templates" / "tokens"
_OUT = _TOKENS / "dtcg" / "aluca.tokens.json"

# DTCG-Typbezeichner (Format Module 2025.10). Nur die drei, die wir wirklich
# emittieren — ein `$type`, den wir nicht belegen koennen, waere geraten.
_COLOR, _DIMENSION, _FONT = "color", "dimension", "fontFamily"


class TokenError(ValueError):
    """Die Token-Quellen sind nicht lesbar oder unvollstaendig."""


def _load(name: str) -> dict[str, Any]:
    path = _TOKENS / name
    if not path.exists():
        raise TokenError(f"Token-Datei fehlt: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _color_group(werte: dict[str, Any], beschreibung: str) -> dict[str, Any]:
    """Ein DTCG-Gruppenobjekt aus einer flachen Farb-Map."""
    gruppe: dict[str, Any] = {"$type": _COLOR, "$description": beschreibung}
    for schluessel, hexwert in sorted(werte.items()):
        if isinstance(hexwert, str) and hexwert.startswith("#"):
            gruppe[schluessel] = {"$value": hexwert}
    return gruppe


def build() -> dict[str, Any]:
    """Baue das DTCG-Dokument aus den governten YAMLs. Deterministisch."""
    farben = _load("color_semantics.yaml")
    typo = _load("typography.yaml")
    raster = _load("layout_grid.yaml")

    doc: dict[str, Any] = {
        "$description": (
            "ALUCA Design-Tokens im DTCG-Format (W3C Design Tokens Community Group, "
            "Format Module 2025.10). ERZEUGT aus core/templates/page_templates/tokens/*.yaml "
            "— nicht von Hand bearbeiten. Die semantische Begruendung (ISO 3864-1, "
            "IEC 60073, WCAG-Nachweise) steht in den YAML-Quellen und der Prosa-Governance."
        ),
    }

    if semantik := farben.get("semantic"):
        doc["semantic"] = _color_group(
            semantik,
            "Statusfarben nach ISO 3864-1 / IEC 60073 — nie fuer Aesthetik invertieren.")
    if tints := farben.get("severity_tints"):
        doc["severity"] = _color_group(tints, "Zeilen-/Hintergrund-Tints fuer Ausnahmelisten.")
    for key in ("surface", "text", "border", "brand"):
        if isinstance(werte := farben.get(key), dict):
            doc[key] = _color_group(werte, f"Farbgruppe '{key}' aus color_semantics.yaml.")

    familien = typo.get("font_family") or {}
    schrift: dict[str, Any] = {
        "$type": _FONT,
        "$description": "Zwei-Schnitt-System: primaer fuer Text, display fuer Highlight-Werte.",
    }
    for rolle in ("preferred", "display"):
        if wert := familien.get(rolle):
            schrift[rolle] = {"$value": wert}
    if len(schrift) > 2:
        doc["fontFamily"] = schrift

    # `scale` gibt Spannen (size_min_pt/size_max_pt), keine Einzelwerte. DTCG kennt
    # keine Spanne — emittiert wird deshalb die UNTERGRENZE als Token, weil sie die
    # Zusicherung ist (kleiner darf es nie werden); die Obergrenze bleibt in der YAML.
    if isinstance(skala := typo.get("scale"), dict):
        gruppe: dict[str, Any] = {
            "$type": _DIMENSION,
            "$description": ("Schriftgrade in pt auf der 1280x720-Basisleinwand. Wert = "
                             "size_min_pt (garantierte Untergrenze); size_max_pt und "
                             "weight/color_token stehen in typography.yaml."),
        }
        for rolle, spez in sorted(skala.items()):
            if isinstance(spez, dict) and isinstance(spez.get("size_min_pt"), (int, float)):
                gruppe[rolle] = {"$value": {"value": float(spez["size_min_pt"]), "unit": "pt"}}
        if len(gruppe) > 2:
            doc["fontSize"] = gruppe

    gitter: dict[str, Any] = {
        "$type": _DIMENSION,
        "$description": "Raster und Abstaende der Basisleinwand (px).",
    }
    for feld, wert in sorted((raster.get("spacing") or {}).items()):
        if isinstance(wert, (int, float)):
            gitter[feld] = {"$value": {"value": float(wert), "unit": "px"}}
    for feld, wert in (("canvas_width", (raster.get("canvas") or {}).get("design_base", {}).get("width")),
                       ("canvas_height", (raster.get("canvas") or {}).get("design_base", {}).get("height"))):
        if isinstance(wert, (int, float)):
            gitter[feld] = {"$value": {"value": float(wert), "unit": "px"}}
    if len(gitter) > 2:
        doc["grid"] = gitter

    # IBCS-Szenario-Notation (AC/PL/FC/PY) ist KEINE Farbe, sondern Fuellart + Deckkraft.
    # DTCG hat dafuer keinen Typ; sie wandert deshalb als typloser Block mit, damit ein
    # Konnektor sie lesen kann, ohne dass wir einen `$type` erfinden.
    if isinstance(szenario := farben.get("ibcs_scenario"), dict):
        doc["ibcsScenario"] = {
            "$description": ("IBCS-Szenario-Notation (Fuellart/Deckkraft je AC/PL/FC/PY). "
                             "Bewusst OHNE $type — DTCG kennt keinen Typ fuer Fuellmuster; "
                             "einen zu erfinden waere geraten."),
            **{k: dict(v) for k, v in sorted(szenario.items()) if isinstance(v, dict)},
        }

    _pruefe_abdeckung(doc, farben, typo, raster)
    return doc


# Jede Quellgruppe, die im Ergebnis vertreten sein MUSS. Ohne diese Pruefung meldet
# der Emitter „OK", waehrend er still ein Drittel der Tokens verliert — genau das ist
# beim ersten Lauf passiert (`type_scale` statt `scale`, verschachteltes `spacing`).
# Ein Emitter, der nichts findet, darf nicht wie einer aussehen, der nichts zu tun hat.
_PFLICHTGRUPPEN = {
    "semantic": "color_semantics.yaml:semantic",
    "severity": "color_semantics.yaml:severity_tints",
    "surface": "color_semantics.yaml:surface",
    "text": "color_semantics.yaml:text",
    "fontFamily": "typography.yaml:font_family",
    "fontSize": "typography.yaml:scale",
    "grid": "layout_grid.yaml:spacing+canvas",
    "ibcsScenario": "color_semantics.yaml:ibcs_scenario",
}


def _pruefe_abdeckung(doc: dict[str, Any], *_quellen: dict[str, Any]) -> None:
    fehlend = [f"{g} (aus {q})" for g, q in _PFLICHTGRUPPEN.items()
               if g not in doc or len([k for k in doc[g] if not k.startswith("$")]) == 0]
    if fehlend:
        raise TokenError(
            "DTCG-Emission unvollstaendig — folgende Gruppen sind leer geblieben: "
            + "; ".join(fehlend)
            + ". Vermutlich hat sich eine YAML-Struktur geaendert.")


def render() -> str:
    """Das DTCG-Dokument als stabil sortierter JSON-Text."""
    return json.dumps(build(), indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python tooling/superversion/layer_tools/design_tokens.py",
        description="DTCG-Emitter fuer die governten Design-Tokens (L5).")
    parser.add_argument("--write", action="store_true",
                        help="die erzeugte Fassung schreiben (sonst nur pruefen)")
    args = parser.parse_args(argv)

    try:
        neu = render()
    except TokenError as exc:
        print(f"[design-tokens] FAIL — {exc}")
        return 1

    if args.write:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        _OUT.write_text(neu, encoding="utf-8", newline="\n")
        print(f"[design-tokens] geschrieben: {_OUT.relative_to(_REPO_ROOT)}")
        return 0

    if not _OUT.exists():
        print(f"[design-tokens] FAIL — {_OUT.relative_to(_REPO_ROOT)} fehlt. "
              f"Erzeugen mit --write.")
        return 1
    if _OUT.read_text(encoding="utf-8") != neu:
        print(f"[design-tokens] FAIL — {_OUT.relative_to(_REPO_ROOT)} ist veraltet "
              f"(YAML-Quellen haben sich geaendert). Neu erzeugen mit --write.")
        return 1
    print(f"[design-tokens] OK — DTCG-Fassung deckungsgleich mit den YAML-Quellen.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
