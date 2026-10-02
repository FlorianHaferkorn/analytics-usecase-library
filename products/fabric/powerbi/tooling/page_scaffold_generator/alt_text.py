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

Sprache (seit 01.10.2026): `ux_layout_rules.report_locale` im UseCase_Bracket (BCP 47, Default
`en-US`, Schema usecase_bracket.schema.json). Uebersetzt werden nur die Satzbausteine, die dieses Modul
selbst zusammensetzt (`PHRASES`: "and", "compared with", "by", "Filter by", "n more measures"). Namen
von Measures und Spalten bleiben, wie das Visual sie bindet: KPI-Katalog und Modell fuehren keine
lokalisierten Namen (kein `name_de`/`display_name`, Modell-`cultures/` nur en-US). Unbekannte Sprache:
Fallback `en` mit `UnknownLocaleWarning`. Das Modell-`culture` ist bewusst keine Quelle: es steht in
vier von fuenf Modellen auf de-DE, deren Reports aber englische Titel tragen (gemessen 01.10.2026).

Ausnahmen wie in der BPA-Regel: `shape` (dekorativ) bekommt keinen Alt-Text.

Kacheln (seit 02.10.2026, `CARD_TYPES`): Alt-Text nennt den Kennzahlnamen und dass die Kachel
dessen aktuellen Wert zeigt ("Net Sales: current value", de "Net Sales: aktueller Wert"), bei
einer Vergleichsreihe mit "compared with". Der Wert selbst steht nicht im Text: statischer Alt-Text
ist ein Literal und veraltet mit jedem Filter (Learn, s. o.). Learn kennt dynamischen Alt-Text
("You can use DAX measures and conditional formatting to create dynamic alt text", Abschnitt
"Conditional formatting for alt text", gelesen 02.10.2026); in PBIR ist das ein `altText.expr` mit
`Measure` statt `Literal`. Dafuer braucht das Modell je KPI ein Text-Measure (Name + FORMAT des
Werts), das der Modellgenerator nicht erzeugt -- offen, dieses Modul setzt nur Literale und laesst
einen vorhandenen Ausdruck stehen (`has_alt_text`).

Lokalisierte KPI-Namen: `kpi_namen` (Anzeigename -> {Sprache: Name}) ersetzt gebundene Namen in der
Sprache des Reports. Der KPI-Katalog fuehrt heute keine Namen je Sprache (gemessen 02.10.2026: kein
solches Feld in `core/kpi_catalog/kpis/*.yaml`, Schema `kpi_definition.schema.json`); ohne Eintrag
bleibt der gebundene Name. Kein Name wird uebersetzt oder erfunden.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

#: Learn (01.10.2026): "The Alt Text textbox has a limit of 250 characters."
ALT_TEXT_MAX_CHARS = 250

#: Kacheln: Alt-Text "<Kennzahl>: aktueller Wert" statt der blossen Measure-Liste.
CARD_TYPES = frozenset({"card", "cardVisual", "multiRowCard", "kpi"})

#: Rolle des Zielwerts im KPI-Visual: wird wie eine Vergleichsreihe genannt.
_COMPARISON_ROLES = frozenset({"Goal"})

#: Visualtypen ohne Alt-Text: dieselbe Ausschlussliste wie ENSURE_ALTTEXT in
#: bpa-rules-report.json (Test: test_alt_text.py haelt beide gleich).
ALT_TEXT_EXEMPT_TYPES = frozenset({"shape"})

_ELLIPSIS = "…"

#: Default, wenn das Bracket keine `ux_layout_rules.report_locale` deklariert (Stand vor 01.10.2026).
DEFAULT_LOCALE = "en-US"

#: Satzbausteine je Sprache (Sprachteil der Locale). Nur was dieses Modul selbst formuliert.
PHRASES: Dict[str, Dict[str, str]] = {
    "en": {"and": "and", "compared_with": "compared with", "by": "by", "filter_by": "Filter by",
           "more_one": "{n} more measure", "more_many": "{n} more measures",
           "card_one": "{name}: current value", "card_many": "Current values of {names}"},
    "de": {"and": "und", "compared_with": "im Vergleich zu", "by": "nach", "filter_by": "Filtern nach",
           "more_one": "{n} weitere Kennzahl", "more_many": "{n} weitere Kennzahlen",
           "card_one": "{name}: aktueller Wert", "card_many": "Aktuelle Werte von {names}"},
}

_FALLBACK_LANGUAGE = "en"


class UnknownLocaleWarning(UserWarning):
    """Locale ohne Satzbausteine in `PHRASES`: der Alt-Text faellt auf Englisch zurueck."""


def language(locale: Optional[str]) -> str:
    """`de-DE` -> `de`. Ohne Angabe `en`; unbekannte Sprache -> `en` mit `UnknownLocaleWarning`."""
    if not locale:
        return _FALLBACK_LANGUAGE
    lang = str(locale).replace("_", "-").split("-")[0].lower()
    if lang in PHRASES:
        return lang
    warnings.warn(f"Alt-Text: keine Satzbausteine fuer Locale {locale!r} (vorhanden: "
                  f"{', '.join(sorted(PHRASES))}); Fallback '{_FALLBACK_LANGUAGE}'.",
                  UnknownLocaleWarning, stacklevel=2)
    return _FALLBACK_LANGUAGE


def bracket_locale(bracket: Optional[Dict[str, Any]]) -> str:
    """`ux_layout_rules.report_locale` aus einem UseCase_Bracket, sonst `DEFAULT_LOCALE`."""
    ux = (bracket or {}).get("ux_layout_rules") or {}
    return str(ux.get("report_locale") or DEFAULT_LOCALE)


def _split_camel(name: str) -> str:
    """`CalendarYearMonth` -> `Calendar Year Month`; Akronyme (`SKU`) bleiben zusammen."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name).replace("_", " ").strip()


def _join(items: Sequence[str], lang: str = _FALLBACK_LANGUAGE) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {PHRASES[lang]['and']} " + items[-1]


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


KpiNamen = Mapping[str, Mapping[str, str]]


def localized_name(name: str, lang: str, kpi_namen: Optional[KpiNamen] = None) -> str:
    """Name in der Sprache `lang`, wenn `kpi_namen` ihn fuehrt; sonst der gebundene Name."""
    return ((kpi_namen or {}).get(name) or {}).get(lang) or name


def _fields(visual_cfg: Dict[str, Any], lang: str = _FALLBACK_LANGUAGE,
            kpi_namen: Optional[KpiNamen] = None) -> tuple[List[str], List[str], List[str]]:
    """(Measures, Kategoriespalten, Measures in Zielwert-Rollen) in Rollenreihenfolge, ohne Dubletten."""
    measures: List[str] = []
    columns: List[str] = []
    goals: List[str] = []
    state = ((visual_cfg.get("query") or {}).get("queryState")) or {}
    for role_name, role in state.items():
        for proj in (role or {}).get("projections") or []:
            label = _projection_label(proj)
            if not label:
                continue
            is_column = "Column" in (proj.get("field") or {})
            if not is_column:
                label = localized_name(label, lang, kpi_namen)
            target = columns if is_column else measures
            if label not in target:
                target.append(label)
            if not is_column and role_name in _COMPARISON_ROLES and label not in goals:
                goals.append(label)
    return measures, columns, goals


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


def _measures_phrase(primary: List[str], compared: List[str], tail: str,
                     lang: str = _FALLBACK_LANGUAGE, card: bool = False) -> str:
    """`A and B compared with C by X`, mit gekuerzter Measure-Liste, falls die Grenze reisst.

    `card`: Kachel -- `A: current value` bzw. `Current values of A and B` (`PHRASES` card_*).
    """
    ph = PHRASES[lang]
    for keep in range(len(primary), 0, -1):
        shown = list(primary[:keep])
        rest = len(primary) - keep
        if rest:
            shown.append(ph["more_many" if rest > 1 else "more_one"].format(n=rest))
        text = _join(shown, lang)
        if card:
            text = (ph["card_one"].format(name=text) if len(primary) == 1
                    else ph["card_many"].format(names=text))
        if compared:
            text += f" {ph['compared_with']} " + _join(compared, lang)
        text += tail
        if len(text) <= ALT_TEXT_MAX_CHARS:
            return text
    return _shorten(_join(primary, lang) + tail)


def describe(visual: Dict[str, Any], comparison_measures: Iterable[str] = (),
             locale: Optional[str] = None, kpi_namen: Optional[KpiNamen] = None) -> Optional[str]:
    """Alt-Text fuer ein PBIR-Visual (visual.json als dict), oder None.

    None heisst: dekorativ (`ALT_TEXT_EXEMPT_TYPES`), Gruppe, oder nichts Beschreibbares gebunden.
    `comparison_measures`: Measures, die als Vergleichsreihe gezeichnet sind (R6.1).
    `locale`: Sprache der Satzbausteine (`report_locale` des Brackets); None -> Englisch.
    `kpi_namen`: lokalisierte Kennzahlnamen (Anzeigename -> {Sprache: Name}); None -> wie gebunden.
    """
    return _describe(visual, comparison_measures, language(locale), kpi_namen=kpi_namen)


def _describe(visual: Dict[str, Any], comparison_measures: Iterable[str], lang: str,
              kpi_namen: Optional[KpiNamen] = None, card_form: bool = True) -> Optional[str]:
    """`card_form=False`: Kacheln wie vor dem 02.10.2026 (blosse Measure-Liste), nur um solchen
    erzeugten Alt-Text beim Sprach- oder Formwechsel wiederzuerkennen."""
    ph = PHRASES[lang]
    visual_cfg = visual.get("visual")
    if not isinstance(visual_cfg, dict):
        return None  # visualGroup: kein eigenes Visual
    vtype = str(visual_cfg.get("visualType") or "")
    if not vtype or vtype in ALT_TEXT_EXEMPT_TYPES:
        return None
    if vtype == "textbox":
        text = _textbox_text(visual_cfg)
        return _shorten(text) if text else None
    measures, columns, goals = _fields(visual_cfg, lang, kpi_namen)
    if vtype == "slicer":
        return _shorten(f"{ph['filter_by']} " + _join(columns, lang)) if columns else None
    if not measures:
        return _shorten(_join(columns, lang)) if columns else None
    refs = {localized_name(m, lang, kpi_namen) for m in comparison_measures} | set(goals)
    compared = [m for m in measures if m in refs]
    primary = [m for m in measures if m not in refs]
    if not primary:  # nur Referenzreihen gebunden: dann ist nichts "verglichen"
        primary, compared = measures, []
    tail = (f" {ph['by']} " + _join(columns, lang)) if columns else ""
    return _measures_phrase(primary, compared, tail, lang, card=card_form and vtype in CARD_TYPES)


def _alt_literal(visual: Dict[str, Any]) -> Optional[str]:
    """Der Alt-Text als Klartext, wenn er ein Literal ist; sonst None (fehlt oder Ausdruck)."""
    vco = (visual.get("visual") or {}).get("visualContainerObjects") or {}
    for entry in vco.get("general") or []:
        value = ((((entry or {}).get("properties") or {}).get("altText") or {}).get("expr") or {}) \
            .get("Literal", {}).get("Value")
        if isinstance(value, str) and len(value) >= 2 and value[0] == value[-1] == "'":
            return value[1:-1].replace("''", "'")
    return None


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


def apply_alt_text(visual: Dict[str, Any], comparison_measures: Iterable[str] = (),
                   locale: Optional[str] = None, replace_generated: bool = False,
                   kpi_namen: Optional[KpiNamen] = None) -> Dict[str, Any]:
    """Setzt den Alt-Text als Literal, wenn das Visual noch keinen traegt. Gibt das Visual zurueck.

    `replace_generated`: einen vorhandenen Alt-Text ersetzen, aber nur, wenn er woertlich dem
    entspricht, was dieses Modul in einer der Sprachen aus `PHRASES` erzeugt (Sprachwechsel eines
    schon erzeugten Reports) oder in der Kachelform vor dem 02.10.2026. Von Hand geschriebener
    Alt-Text und Ausdruecke bleiben unberuehrt.
    """
    comparison_measures = tuple(comparison_measures)
    lang = language(locale)
    if has_alt_text(visual):
        current = _alt_literal(visual)
        if not replace_generated or current is None:
            return visual
        generated = {_describe(visual, comparison_measures, other, kpi_namen, form)
                     for other in PHRASES for form in (True, False)}
        if current not in generated:
            return visual
    text = _describe(visual, comparison_measures, lang, kpi_namen)
    if not text or text == _alt_literal(visual):
        return visual
    literal = "'" + text.replace("'", "''") + "'"
    vco = visual["visual"].setdefault("visualContainerObjects", {})
    general = vco.setdefault("general", [{"properties": {}}])
    if not general:
        general.append({"properties": {}})
    general[0].setdefault("properties", {})["altText"] = {"expr": {"Literal": {"Value": literal}}}
    return visual


def _replace_literal(raw: str, original: Dict[str, Any], updated: Dict[str, Any]) -> Optional[str]:
    """Ersetzt nur den Alt-Text-Wert textuell, wenn das sein einziger Unterschied ist und er genau
    einmal in `raw` steht (Sprachwechsel in handformatierten Dateien). Sonst None."""
    old, new = _alt_literal(original), _alt_literal(updated)
    if old is None or new is None:
        return None
    for ascii_only in (False, True):
        old_tok = json.dumps("'" + old.replace("'", "''") + "'", ensure_ascii=ascii_only)
        new_tok = json.dumps("'" + new.replace("'", "''") + "'", ensure_ascii=ascii_only)
        if raw.count(old_tok) == 1:
            text = raw.replace(old_tok, new_tok)
            if json.loads(text) == updated:
                return text
    return None


def _serialize_like(raw: str, original: Dict[str, Any], updated: Dict[str, Any]) -> str:
    """Schreibt `updated` so, dass sich gegenueber `raw` nur die Alt-Text-Zeilen aendern.

    Passt `raw` zu einer json.dumps-Form (indent 2/4, mit/ohne ensure_ascii), wird in derselben Form
    geschrieben. Sonst (von Hand kompakt formatierte Objekte) wird der neue
    `visualContainerObjects`-Block textuell vor dem Ende des `visual`-Objekts eingefuegt, wenn
    `visual` der letzte Schluessel ist und noch keinen solchen Block hat; sonst Neuformatierung.
    """
    replaced = _replace_literal(raw, original, updated)
    if replaced is not None:
        return replaced
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


def apply_to_report(report_dir: Path, locale: Optional[str] = None) -> List[Path]:
    """Alt-Text in einen bestehenden PBIR-Report schreiben (fuer Reports ohne Generatorpfad).

    Ueberschreibt keinen von Hand geschriebenen Alt-Text; einen von diesem Modul erzeugten bringt
    er in die Sprache `locale` (`replace_generated`). Gibt die geaenderten visual.json zurueck.
    """
    lang = language(locale)  # einmal warnen, nicht je Visual
    changed: List[Path] = []
    for path in sorted((report_dir / "definition" / "pages").glob("*/visuals/*/visual.json")):
        raw = path.read_text(encoding="utf-8")
        original = json.loads(raw)
        updated = apply_alt_text(json.loads(raw), locale=lang, replace_generated=True)
        if updated == original:
            continue
        text = _serialize_like(raw, original, updated)
        if json.loads(text) != updated:
            raise RuntimeError(f"Alt-Text-Einfuegung in {path} ergibt anderes JSON")
        path.write_text(text, encoding="utf-8", newline="\n")
        changed.append(path)
    return changed


_USE_CASE_ID = re.compile(r"^([A-Z]{2,4}-\d{3})(?=[_.]|$)")


def report_locale(report_dir: Path, repo_root: Optional[Path] = None) -> str:
    """Locale eines Reports aus dem Bracket seines Use Case (Ordnername `<UC-ID>_...Report`).

    Ohne erkennbare Use-Case-ID oder Bracket: `DEFAULT_LOCALE` mit Warnung.
    """
    match = _USE_CASE_ID.match(report_dir.name)
    if match:
        from .config_loader import ConfigLoader  # lazy: config_loader ist schwer, describe() nicht
        try:
            root = repo_root or Path(__file__).resolve().parents[5]
            bracket = ConfigLoader(root).load_use_case_bracket(match.group(1))
        except FileNotFoundError:
            bracket = None
        if bracket is not None:
            return bracket_locale(bracket)
    warnings.warn(f"Alt-Text: kein UseCase_Bracket fuer {report_dir.name}; Locale {DEFAULT_LOCALE}.",
                  UnknownLocaleWarning, stacklevel=2)
    return DEFAULT_LOCALE


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Alt-Text in bestehende PBIR-Reports schreiben (Reports ohne Generatorpfad, "
                    "z. B. FIN-001 und COM-001_Sales_Performance_vs_Plan_LY). Sprache aus "
                    "ux_layout_rules.report_locale des Brackets.")
    parser.add_argument("reports", nargs="+", type=Path, help="Pfad(e) zu <Name>.Report")
    parser.add_argument("--locale", default=None,
                        help="Sprache statt der aus dem Bracket (z. B. de-DE); nur fuer Reports "
                             "ohne Bracket gedacht, die Quelle ist das Bracket.")
    args = parser.parse_args(argv)
    for report in args.reports:
        if not (report / "definition" / "pages").is_dir():
            print(f"ERROR: kein PBIR-Report: {report}", file=sys.stderr)
            return 1
        locale = args.locale or report_locale(report)
        changed = apply_to_report(report, locale)
        print(f"{report.name}: {len(changed)} visual.json mit Alt-Text (Locale {locale})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
