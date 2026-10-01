"""Alt-Text je Visual (PBIR `visual.visualContainerObjects.general[0].properties.altText`).

Ort laut Schema visualConfiguration 2.3.0 (VisualContainerFormattingObjects.general ->
VisualContainerGeneralFormattingObjects.altText), derselbe Pfad, den die Regel ENSURE_ALTTEXT in
tooling/linters/powerbi/bpa-rules-report.json und tooling/validation/validate_report.ps1 lesen.

Quelle der Regeln: Microsoft Learn, "Design Power BI reports for accessibility"
(learn.microsoft.com/power-bi/create-reports/desktop-accessibility-creating-reports), gelesen am
01.10.2026:

* "The **Alt Text** textbox has a limit of 250 characters."  -> ALT_TEXT_MAX_CHARS
* "Because a screen reader reads out the title and type of a visual, you only need to fill in a
  description. An example of alt text for the following visual could be: *Net user satisfaction by
  color of product sold, further broken down by product class.*"  -> der Alt-Text wiederholt weder
  Titel noch Visualtyp; er beschreibt, was gezeigt wird: Kennzahl(en), Achse, Vergleich.
* "Ensure **alt text** is added to all non-decorative visuals on the page."
* Textbox: "Make sure to put text contents in the **alt text** box so screen readers can read them."
* "Keep in mind that calling out an insight or specific data points might not be the best thing to
  put in static alt text because data in Power BI is dynamic."  -> kein Befund, keine Zahl im Text.

Inhalt nur aus dem, was das Visual selbst bindet: Anzeigenamen der Measures (aus dem KPI-Katalog
bzw. Bracket aufgeloest, so wie sie auf Achse und Legende stehen), Kategoriespalten, der als
Vergleichsreihe gezeichnete Measure (comparison im Bracket, R6.1) und bei Textboxen deren Text.
Nichts wird erfunden: ein Visual, das nichts davon traegt, bekommt keinen Alt-Text (und
ENSURE_ALTTEXT meldet es), statt eines Platzhalters.

Sprache: Englisch, wie die Titel, die der Generator aus den Brackets uebernimmt (es gibt keine
Locale-Einstellung im Generator).

Ausnahmen wie in der BPA-Regel: `shape` (dekorativ) bekommt keinen Alt-Text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

#: Learn (01.10.2026): "The Alt Text textbox has a limit of 250 characters."
ALT_TEXT_MAX_CHARS = 250

#: Visualtypen ohne Alt-Text: dieselbe Ausschlussliste wie ENSURE_ALTTEXT in
#: bpa-rules-report.json (Test: test_alt_text.py haelt beide gleich).
ALT_TEXT_EXEMPT_TYPES = frozenset({"shape"})

_ELLIPSIS = "…"


def _split_camel(name: str) -> str:
    """`CalendarYearMonth` -> `Calendar Year Month`; Akronyme (`SKU`) bleiben zusammen."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name).replace("_", " ").strip()


def _join(items: Sequence[str]) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _projection_label(proj: Dict[str, Any]) -> Optional[str]:
    if proj.get("displayName"):
        return str(proj["displayName"])
    field = proj.get("field") or {}
    for kind in ("Measure", "Column", "Aggregation"):
        if kind in field:
            if proj.get("nativeQueryRef"):
                name = str(proj["nativeQueryRef"])
            else:
                inner = field[kind]
                nested = ((inner.get("Expression") or {}).get("Column") or {}).get("Property")
                name = str(inner.get("Property") or nested or "")
            return name if kind != "Column" else _split_camel(name)
    return None


def _fields(visual_cfg: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """(Measures, Kategoriespalten) in Rollenreihenfolge, ohne Dubletten."""
    measures: List[str] = []
    columns: List[str] = []
    state = ((visual_cfg.get("query") or {}).get("queryState")) or {}
    for role in state.values():
        for proj in (role or {}).get("projections") or []:
            label = _projection_label(proj)
            if not label:
                continue
            target = columns if "Column" in (proj.get("field") or {}) else measures
            if label not in target:
                target.append(label)
    return measures, columns


def _literal_text(expr: Any) -> str:
    value = (((expr or {}).get("expr") or {}).get("Literal") or {}).get("Value")
    if not isinstance(value, str) or len(value) < 2 or not (value.startswith("'") and value.endswith("'")):
        return ""
    return value[1:-1].replace("''", "'")


def _textbox_text(visual_cfg: Dict[str, Any]) -> str:
    """Text einer Textbox: Literal unter objects.text (Generator) oder paragraphs/textRuns (Desktop)."""
    objects = visual_cfg.get("objects") or {}
    parts: List[str] = []
    for entry in objects.get("text") or []:
        parts.append(_literal_text((entry.get("properties") or {}).get("text")))
    for entry in objects.get("general") or []:
        for para in (entry.get("properties") or {}).get("paragraphs") or []:
            run_text = "".join(str(r.get("value") or "") for r in para.get("textRuns") or [])
            parts.append(run_text)
    parts = [" ".join(p.split()) for p in parts if p and p.strip()]
    # Absaetze als Saetze trennen, damit der Screenreader eine Pause macht.
    return " ".join(p if p[-1] in ".!?:…" or i == len(parts) - 1 else p + "."
                    for i, p in enumerate(parts))


def _shorten(text: str, limit: int = ALT_TEXT_MAX_CHARS) -> str:
    """Kuerzt an einer Wortgrenze auf hoechstens `limit` Zeichen (mit Auslassungszeichen)."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:·—-") + _ELLIPSIS


def _measures_phrase(primary: List[str], compared: List[str], tail: str) -> str:
    """`A and B compared with C by X`, mit gekuerzter Measure-Liste, falls die Grenze reisst."""
    for keep in range(len(primary), 0, -1):
        shown = list(primary[:keep])
        rest = len(primary) - keep
        if rest:
            shown.append(f"{rest} more measure{'s' if rest > 1 else ''}")
        text = _join(shown)
        if compared:
            text += " compared with " + _join(compared)
        text += tail
        if len(text) <= ALT_TEXT_MAX_CHARS:
            return text
    return _shorten(_join(primary) + tail)


def describe(visual: Dict[str, Any], comparison_measures: Iterable[str] = ()) -> Optional[str]:
    """Alt-Text fuer ein PBIR-Visual (visual.json als dict), oder None.

    None heisst: dekorativ (`ALT_TEXT_EXEMPT_TYPES`), Gruppe, oder nichts Beschreibbares gebunden.
    `comparison_measures`: Measures, die als Vergleichsreihe gezeichnet sind (R6.1).
    """
    visual_cfg = visual.get("visual")
    if not isinstance(visual_cfg, dict):
        return None  # visualGroup: kein eigenes Visual
    vtype = str(visual_cfg.get("visualType") or "")
    if not vtype or vtype in ALT_TEXT_EXEMPT_TYPES:
        return None
    if vtype == "textbox":
        text = _textbox_text(visual_cfg)
        return _shorten(text) if text else None
    measures, columns = _fields(visual_cfg)
    if vtype == "slicer":
        return _shorten("Filter by " + _join(columns)) if columns else None
    if not measures:
        return _shorten(_join(columns)) if columns else None
    refs = set(comparison_measures)
    compared = [m for m in measures if m in refs]
    primary = [m for m in measures if m not in refs]
    if not primary:  # nur Referenzreihen gebunden: dann ist nichts "verglichen"
        primary, compared = measures, []
    tail = (" by " + _join(columns)) if columns else ""
    return _measures_phrase(primary, compared, tail)


def has_alt_text(visual: Dict[str, Any]) -> bool:
    """Wie Test-HasAltText in validate_report.ps1: nicht-leeres Literal oder ein Ausdruck."""
    vco = (visual.get("visual") or {}).get("visualContainerObjects") or {}
    for entry in vco.get("general") or []:
        alt = ((entry or {}).get("properties") or {}).get("altText")
        expr = (alt or {}).get("expr")
        if not expr:
            continue
        literal = expr.get("Literal")
        if literal is None or (literal.get("Value") and literal.get("Value") != "''"):
            return True
    return False


def apply_alt_text(visual: Dict[str, Any], comparison_measures: Iterable[str] = ()) -> Dict[str, Any]:
    """Setzt den Alt-Text als Literal, wenn das Visual noch keinen traegt. Gibt das Visual zurueck."""
    if has_alt_text(visual):
        return visual
    text = describe(visual, comparison_measures)
    if not text:
        return visual
    literal = "'" + text.replace("'", "''") + "'"
    vco = visual["visual"].setdefault("visualContainerObjects", {})
    general = vco.setdefault("general", [{"properties": {}}])
    if not general:
        general.append({"properties": {}})
    general[0].setdefault("properties", {})["altText"] = {"expr": {"Literal": {"Value": literal}}}
    return visual


def _serialize_like(raw: str, original: Dict[str, Any], updated: Dict[str, Any]) -> str:
    """Schreibt `updated` so, dass sich gegenueber `raw` nur die Alt-Text-Zeilen aendern.

    Passt `raw` zu einer json.dumps-Form (indent 2/4, mit/ohne ensure_ascii), wird in derselben Form
    geschrieben. Sonst (von Hand kompakt formatierte Objekte) wird der neue
    `visualContainerObjects`-Block textuell vor dem Ende des `visual`-Objekts eingefuegt, wenn
    `visual` der letzte Schluessel ist und noch keinen solchen Block hat; sonst Neuformatierung.
    """
    nl = "\n" if raw.endswith("\n") else ""
    for indent in (2, 4):
        for ascii_only in (False, True):
            if json.dumps(original, indent=indent, ensure_ascii=ascii_only) + nl == raw:
                return json.dumps(updated, indent=indent, ensure_ascii=ascii_only) + nl
    tail = "\n  }\n}" + nl
    if (list(original)[-1:] == ["visual"] and "visualContainerObjects" not in original["visual"]
            and raw.endswith(tail)):
        block = json.dumps(updated["visual"]["visualContainerObjects"], indent=2, ensure_ascii=False)
        block = block.replace("\n", "\n    ")
        return raw[: -len(tail)] + ',\n    "visualContainerObjects": ' + block + tail
    return json.dumps(updated, indent=2, ensure_ascii=False) + nl


def apply_to_report(report_dir: Path) -> List[Path]:
    """Alt-Text in einen bestehenden PBIR-Report schreiben (fuer Reports ohne Generatorpfad).

    Ueberschreibt keinen vorhandenen Alt-Text. Gibt die geaenderten visual.json zurueck.
    """
    changed: List[Path] = []
    for path in sorted((report_dir / "definition" / "pages").glob("*/visuals/*/visual.json")):
        raw = path.read_text(encoding="utf-8")
        original = json.loads(raw)
        updated = apply_alt_text(json.loads(raw))
        if updated == original:
            continue
        text = _serialize_like(raw, original, updated)
        if json.loads(text) != updated:
            raise RuntimeError(f"Alt-Text-Einfuegung in {path} ergibt anderes JSON")
        path.write_text(text, encoding="utf-8", newline="\n")
        changed.append(path)
    return changed


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Alt-Text in bestehende PBIR-Reports schreiben (Reports ohne Generatorpfad, "
                    "z. B. FIN-001 und COM-001_Sales_Performance_vs_Plan_LY).")
    parser.add_argument("reports", nargs="+", type=Path, help="Pfad(e) zu <Name>.Report")
    args = parser.parse_args(argv)
    for report in args.reports:
        if not (report / "definition" / "pages").is_dir():
            print(f"ERROR: kein PBIR-Report: {report}", file=sys.stderr)
            return 1
        changed = apply_to_report(report)
        print(f"{report.name}: {len(changed)} visual.json mit Alt-Text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
