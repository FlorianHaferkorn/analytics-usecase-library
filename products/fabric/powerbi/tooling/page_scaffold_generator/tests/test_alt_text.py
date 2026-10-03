"""Alt-Text aus dem Generator (Entscheidung 01.10.2026: ENSURE_ALTTEXT aktiv, Design_Spec §9).

Learn, "Design Power BI reports for accessibility" (gelesen 01.10.2026): "Ensure alt text is added to
all non-decorative visuals on the page." und "The Alt Text textbox has a limit of 250 characters."

Gegenprobe: `test_generator_ohne_alt_text_faellt_durch` schaltet die Erzeugung ab und verlangt, dass
dieselbe Pruefung dann Befunde liefert -- der Stand vor dem 01.10.2026 (kein altText) faellt durch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_PKG = Path(__file__).resolve().parents[1]
if str(_PKG.parent) not in sys.path:
    sys.path.insert(0, str(_PKG.parent))

from page_scaffold_generator import alt_text as at  # noqa: E402
from page_scaffold_generator import page_builder as pb  # noqa: E402
from page_scaffold_generator import scaffold_generator as sg  # noqa: E402

BPA = REPO / "tooling" / "linters" / "powerbi" / "bpa-rules-report.json"
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"

#: Use Cases mit Generatorpfad (FIN-001 und COM-001LY sind handgebaut, R5.1 vom 23.09.2026).
GENERATOR_UCS = ["COM-001", "COM-002", "COM-003", "COM-004", "FIN-002", "OPS-001", "OPS-002", "OPS-003",
                 "SCM-001", "SCM-002", "SCM-003", "XD-001", "XD-002", "XD-003", "XD-004"]


def _alt(visual: Dict[str, Any]) -> str | None:
    vco = (visual.get("visual") or {}).get("visualContainerObjects") or {}
    for entry in vco.get("general") or []:
        value = (((entry.get("properties") or {}).get("altText") or {}).get("expr") or {}).get("Literal", {})
        if value.get("Value"):
            return value["Value"][1:-1].replace("''", "'")
    return None


def befunde(visuals: List[Dict[str, Any]]) -> List[str]:
    """Verstoesse gegen die Learn-Checkliste: fehlend/leer/zu lang, oder Alt-Text auf `shape`."""
    out = []
    for v in visuals:
        if "visual" not in v:
            continue  # visualGroup
        vtype, text = v["visual"].get("visualType"), _alt(v)
        if vtype in at.ALT_TEXT_EXEMPT_TYPES:
            if text:
                out.append(f"{v['name']}: dekorativ ({vtype}), traegt aber Alt-Text")
        elif not text or not text.strip():
            out.append(f"{v['name']} ({vtype}): kein Alt-Text")
        elif len(text) > at.ALT_TEXT_MAX_CHARS:
            out.append(f"{v['name']}: {len(text)} Zeichen > {at.ALT_TEXT_MAX_CHARS}")
    return out


_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _generiert(uc: str) -> List[Dict[str, Any]]:
    """Generatorlauf je Use Case einmal pro Testsitzung (ca. 3 s je Use Case)."""
    if uc not in _CACHE:
        _CACHE[uc] = _generiere(uc)
    return _CACHE[uc]


def _generiere(uc: str) -> List[Dict[str, Any]]:
    visuals: List[Dict[str, Any]] = []
    for page in ("overview", "detail"):
        gen = sg.PageScaffoldGenerator(use_case_id=uc, page_name=page, repo_root=REPO)
        gen.load_config()
        gen.generate()
        s = gen.get_page_structure()
        visuals += s["visuals"] + s.get("slicers", [])
    return visuals


# --- Generator -----------------------------------------------------------------------------------


@pytest.mark.parametrize("uc", GENERATOR_UCS)
def test_jedes_nicht_dekorative_visual_hat_alt_text(uc: str) -> None:
    visuals = _generiert(uc)
    assert visuals
    assert befunde(visuals) == []


def test_generator_ohne_alt_text_faellt_durch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gegenprobe: ohne apply_alt_text (Stand vor 01.10.2026) meldet dieselbe Pruefung jedes Visual."""
    monkeypatch.setattr(pb, "apply_alt_text", lambda v, *a, **k: v)
    monkeypatch.setattr(sg, "apply_alt_text", lambda v, *a, **k: v)
    visuals = _generiere("COM-001")
    assert len(befunde(visuals)) == len(visuals)


def test_vergleichsreihe_heisst_compared_with() -> None:
    """R6.1: die aus `comparison` gezeichnete Referenzreihe wird im Alt-Text als Vergleich benannt."""
    found = []
    for uc in GENERATOR_UCS:
        for v in _generiert(uc):
            text = _alt(v) or ""
            if " compared with " in text:
                ys = [p["nativeQueryRef"] for p in v["visual"]["query"]["queryState"]["Y"]["projections"]]
                found.append((uc, v["name"], text, ys))
    # Gemessen 01.10.2026: FIN-002 Main_1, OPS-001 Main_1, SCM-001 Main_3 zeichnen eine Referenzreihe.
    assert len(found) >= 3, found
    for uc, name, text, ys in found:
        ref = text.split(" compared with ")[1].split(" by ")[0]
        assert ref in ys and ref != ys[0], (uc, name, text, ys)


# --- dist: alle 17 Reports ------------------------------------------------------------------------


@pytest.mark.parametrize("report", sorted(p.name for p in DIST.glob("*.Report")))
def test_dist_report_traegt_alt_text(report: str) -> None:
    visuals = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((DIST / report / "definition" / "pages").glob("*/visuals/*/visual.json"))]
    assert visuals
    assert befunde(visuals) == []


def test_siebzehn_dist_reports() -> None:
    assert len(list(DIST.glob("*.Report"))) == 17


# --- Regeln aus Learn / BPA ----------------------------------------------------------------------


def test_ausnahmen_gleich_der_bpa_regel() -> None:
    """ALT_TEXT_EXEMPT_TYPES ist die Ausschlussliste von ENSURE_ALTTEXT, nicht eine zweite Meinung."""
    rule = next(r for r in json.loads(BPA.read_text(encoding="utf-8"))["rules"] if r["id"] == "ENSURE_ALTTEXT")
    flt = rule["test"][0]["map"][0]["filter"][1]["and"][0]["!"][0]["in"]
    assert flt[0] == {"var": "visual.visualType"}
    assert set(flt[1]) == set(at.ALT_TEXT_EXEMPT_TYPES)
    assert rule["disabled"] is False


def test_learn_grenze_250() -> None:
    assert at.ALT_TEXT_MAX_CHARS == 250


def _v(vtype: str, state: Dict[str, Any] | None = None, objects: Dict[str, Any] | None = None) -> Dict[str, Any]:
    vis: Dict[str, Any] = {"visualType": vtype}
    if state is not None:
        vis["query"] = {"queryState": state}
    if objects is not None:
        vis["objects"] = objects
    return {"name": "V", "visual": vis}


def _m(name: str) -> Dict[str, Any]:
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}},
            "queryRef": f"_Measures.{name}", "nativeQueryRef": name}


def _c(table: str, col: str) -> Dict[str, Any]:
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}},
            "queryRef": f"{table}.{col}", "nativeQueryRef": col}


def test_chart_kennzahl_achse_vergleich() -> None:
    v = _v("lineChart", {"Category": {"projections": [_c("dim_date", "CalendarYearMonth")]},
                         "Y": {"projections": [_m("OEE %"), _m("OEE % Target")]}})
    assert at.describe(v, ["OEE % Target"]) == "OEE % compared with OEE % Target by Calendar Year Month"
    assert at.describe(v) == "OEE % and OEE % Target by Calendar Year Month"


def test_kein_titel_und_kein_visualtyp_im_alt_text() -> None:
    """Learn: der Screenreader liest Titel und Typ selbst; der Alt-Text ist nur die Beschreibung."""
    v = _v("clusteredBarChart", {"Category": {"projections": [_c("dim_org", "Region")]},
                                 "Y": {"projections": [_m("Net Sales Amount")]}})
    v["visual"]["visualContainerObjects"] = {"title": [{"properties": {"text": {"expr": {"Literal": {
        "Value": "'Which regions lag?'"}}}}}]}
    text = at.describe(v)
    assert text == "Net Sales Amount by Region"
    assert "lag" not in text and "bar" not in text.lower()


def test_slicer_card_textbox_shape() -> None:
    assert at.describe(_v("slicer", {"Values": {"projections": [_c("dim_org", "OrgName")]}})) == "Filter by Org Name"
    assert at.describe(_v("cardVisual", {"Data": {"projections": [_m("A"), _m("B"), _m("C")]}})) == \
        "Current values of A, B and C"
    tb = _v("textbox", objects={"text": [{"properties": {"text": {"expr": {"Literal": {"Value": "'It''s on'"}}}}}]})
    assert at.describe(tb) == "It's on"
    assert at.describe(_v("shape")) is None
    assert at.describe({"name": "G", "visualGroup": {"displayName": "G"}}) is None


def test_nichts_gebunden_kein_platzhalter() -> None:
    assert at.describe(_v("tableEx", {"Values": {"projections": []}})) is None


def test_lange_listen_bleiben_unter_der_grenze() -> None:
    ms = [_m(f"Measure Number {i} With A Long Name") for i in range(20)]
    text = at.describe(_v("tableEx", {"Values": {"projections": [_c("dim_org", "Region")] + ms}}))
    assert len(text) <= at.ALT_TEXT_MAX_CHARS
    assert text.endswith("more measures by Region")
    long_tb = _v("textbox", objects={"text": [{"properties": {"text": {"expr": {"Literal": {
        "Value": "'" + "word " * 100 + "'"}}}}}]})
    assert len(at.describe(long_tb)) <= at.ALT_TEXT_MAX_CHARS


def test_vorhandener_alt_text_bleibt_und_hochkomma_wird_verdoppelt() -> None:
    v = _v("cardVisual", {"Data": {"projections": [_m("Owner's Margin")]}})
    at.apply_alt_text(v)
    assert v["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"] == {
        "expr": {"Literal": {"Value": "'Owner''s Margin: current value'"}}}
    v["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"]["expr"]["Literal"]["Value"] = "'x'"
    at.apply_alt_text(v)
    assert _alt(v) == "x"


def test_apply_to_report_aendert_nur_alt_text(tmp_path: Path) -> None:
    """Handgebaute Reports (kompakt formatiert): nur der altText-Block kommt dazu."""
    raw = ('{\n  "name": "V",\n  "visual": {\n    "visualType": "cardVisual",\n    "query": {\n'
           '      "queryState": { "Data": { "projections": [ { "field": { "Measure": { "Expression": '
           '{ "SourceRef": { "Entity": "_Measures" } }, "Property": "Cash" } } } ] } }\n    }\n  }\n}\n')
    p = tmp_path / "R.Report" / "definition" / "pages" / "P" / "visuals" / "V" / "visual.json"
    p.parent.mkdir(parents=True)
    p.write_text(raw, encoding="utf-8")
    with pytest.warns(at.UnknownModelWarning):  # kein definition.pbir: Text-Measures unbekannt
        assert at.apply_to_report(tmp_path / "R.Report") == [p]
    new = p.read_text(encoding="utf-8")
    old_lines, new_lines = raw.splitlines(), new.splitlines()
    removed = [line for line in old_lines if line not in new_lines]
    assert all(line + "," in new_lines for line in removed)
    assert _alt(json.loads(new)) == "Cash: current value"
    with pytest.warns(at.UnknownModelWarning):
        assert at.apply_to_report(tmp_path / "R.Report") == []  # zweiter Lauf: nichts mehr zu tun


# --- Sprache (ux_layout_rules.report_locale, 01.10.2026) -----------------------------------------

SCHEMA = REPO / "tooling" / "generator" / "schemas" / "usecase_bracket.schema.json"
FIN001 = DIST / "FIN-001_Cash_Liquidity_Performance.Report"
_DEUTSCH = (" und ", " nach ", " im Vergleich zu ", "Filtern nach ", " weitere Kennzahl")
_ENGLISCH = (" and ", " by ", " compared with ", "Filter by ", " more measure")

_FAELLE = [  # (Visual, Vergleichsreihen, en, de) je Visualtyp
    (_v("lineChart", {"Category": {"projections": [_c("dim_date", "CalendarYearMonth")]},
                      "Y": {"projections": [_m("OEE %"), _m("OEE % Target")]}}), ["OEE % Target"],
     "OEE % compared with OEE % Target by Calendar Year Month",
     "OEE % im Vergleich zu OEE % Target nach Calendar Year Month"),
    (_v("clusteredBarChart", {"Category": {"projections": [_c("dim_org", "Region")]},
                              "Y": {"projections": [_m("Net Sales Amount")]}}), [],
     "Net Sales Amount by Region", "Net Sales Amount nach Region"),
    (_v("slicer", {"Values": {"projections": [_c("dim_org", "OrgName")]}}), [],
     "Filter by Org Name", "Filtern nach Org Name"),
    (_v("cardVisual", {"Data": {"projections": [_m("A"), _m("B"), _m("C")]}}), [],
     "Current values of A, B and C", "Aktuelle Werte von A, B und C"),
    (_v("tableEx", {"Values": {"projections": [_c("dim_org", "OrgName"), _c("dim_org", "Region"),
                                               _m("Cash")]}}), [],
     "Cash by Org Name and Region", "Cash nach Org Name und Region"),
    (_v("textbox", objects={"text": [{"properties": {"text": {"expr": {"Literal": {"Value": "'On track'"}}}}}]}),
     [], "On track", "On track"),
]


@pytest.mark.parametrize("visual,refs,en,de", _FAELLE, ids=[f[0]["visual"]["visualType"] for f in _FAELLE])
def test_de_und_en_je_visualtyp(visual: Dict[str, Any], refs: List[str], en: str, de: str) -> None:
    assert at.describe(visual, refs, locale="en-US") == en
    assert at.describe(visual, refs, locale="de-DE") == de
    assert at.describe(visual, refs) == en  # Gegenprobe: ohne Einstellung Englisch


def test_lange_liste_deutsch() -> None:
    ms = [_m(f"Measure Number {i} With A Long Name") for i in range(20)]
    text = at.describe(_v("tableEx", {"Values": {"projections": [_c("dim_org", "Region")] + ms}}), locale="de-DE")
    assert len(text) <= at.ALT_TEXT_MAX_CHARS
    assert text.endswith("weitere Kennzahlen nach Region")


def test_sprachen_haben_dieselben_bausteine() -> None:
    assert set(at.PHRASES) >= {"en", "de"}
    keys = set(at.PHRASES["en"])
    assert all(set(p) == keys for p in at.PHRASES.values())


@pytest.mark.parametrize("locale,lang", [("de-DE", "de"), ("de", "de"), ("de_AT", "de"),
                                         ("en-GB", "en"), ("en-US", "en"), (None, "en")])
def test_locale_zu_sprache(locale: str | None, lang: str, recwarn: pytest.WarningsRecorder) -> None:
    assert at.language(locale) == lang
    assert not [w for w in recwarn if issubclass(w.category, at.UnknownLocaleWarning)]


def test_unbekannte_locale_warnt_und_faellt_auf_englisch() -> None:
    v = _FAELLE[0][0]
    with pytest.warns(at.UnknownLocaleWarning, match="fr-FR"):
        text = at.describe(v, ["OEE % Target"], locale="fr-FR")
    assert text == "OEE % compared with OEE % Target by Calendar Year Month"


def test_sprachwechsel_ersetzt_nur_erzeugten_alt_text() -> None:
    v = _FAELLE[1][0]
    at.apply_alt_text(v)
    assert _alt(v) == "Net Sales Amount by Region"
    at.apply_alt_text(v, locale="de-DE")  # ohne replace_generated: bleibt
    assert _alt(v) == "Net Sales Amount by Region"
    at.apply_alt_text(v, locale="de-DE", replace_generated=True)
    assert _alt(v) == "Net Sales Amount nach Region"
    v["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"]["expr"]["Literal"]["Value"] = "'Hand'"
    at.apply_alt_text(v, locale="en-US", replace_generated=True)
    assert _alt(v) == "Hand"  # von Hand geschrieben: unberuehrt


# --- Schema ---------------------------------------------------------------------------------------


def _schema_fehler(bracket: Dict[str, Any]) -> List[str]:
    import jsonschema
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return [e.message for e in jsonschema.Draft7Validator(schema).iter_errors(bracket)]


def _bracket(uc_dir: str) -> Dict[str, Any]:
    import yaml
    return yaml.safe_load((REPO / "core" / "usecases" / "core" / uc_dir / "UseCase_Bracket.yaml")
                          .read_text(encoding="utf-8"))


def test_schema_feld_report_locale() -> None:
    ux = json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["ux_layout_rules"]
    prop = ux["properties"]["report_locale"]
    assert prop["default"] == at.DEFAULT_LOCALE == "en-US"
    fin = _bracket("FIN-001_Cash_Liquidity_Performance")
    assert fin["ux_layout_rules"]["report_locale"] == "de-DE"
    assert _schema_fehler(fin) == []
    for bad in ("German", "de_DE", "DE-de", 7):
        fin["ux_layout_rules"]["report_locale"] = bad
        assert _schema_fehler(fin), bad
    del fin["ux_layout_rules"]["report_locale"]
    assert _schema_fehler(fin) == []  # optional
    assert at.bracket_locale(fin) == "en-US"


# --- Generator und dist ---------------------------------------------------------------------------


def test_generator_folgt_der_bracket_sprache() -> None:
    """FIN-002 (Generatorpfad, zeichnet eine Vergleichsreihe): de aus der Einstellung, sonst en."""
    def texte(locale: str | None) -> List[str]:
        out = []
        for page in ("overview", "detail"):
            gen = sg.PageScaffoldGenerator(use_case_id="FIN-002", page_name=page, repo_root=REPO)
            gen.load_config()
            assert gen.page_config["report_locale"] == "en-US"  # Bracket deklariert nichts
            if locale:
                gen.page_config["report_locale"] = locale
            gen.generate()
            s = gen.get_page_structure()
            # Textboxen tragen ihren (im Bracket englisch verfassten) Text, keine Satzbausteine.
            out += [_alt(v) or "" for v in s["visuals"] + s.get("slicers", [])
                    if (v.get("visual") or {}).get("visualType") != "textbox"]
        return out
    de, en = " ".join(texte("de-DE")), " ".join(texte(None))
    assert " im Vergleich zu " in de and "Filtern nach " in de and " nach " in de
    assert not any(p in de for p in (" compared with ", "Filter by ", " by "))
    assert " compared with " in en and not any(p in en for p in _DEUTSCH)


def _dist_alt(report: Path) -> List[str]:
    return [_alt(json.loads(p.read_text(encoding="utf-8"))) or ""
            for p in sorted((report / "definition" / "pages").glob("*/visuals/*/visual.json"))]


def test_fin001_dist_traegt_deutschen_alt_text() -> None:
    texte = _dist_alt(FIN001)
    assert sum(any(p in t for p in _DEUTSCH) for t in texte) >= 9  # gemessen 01.10.2026: 9 von 13
    assert not any(p in t for t in texte for p in (" compared with ", "Filter by ", " by "))
    texte = at.text_measures(at.report_model_dir(FIN001))  # Text-Kacheln ohne "aktueller Wert"
    for path in sorted((FIN001 / "definition" / "pages").glob("*/visuals/*/visual.json")):
        v = json.loads(path.read_text(encoding="utf-8"))
        assert (_alt(v) == at.describe(v, locale="de-DE", text_measures=texte)
                or v["visual"]["visualType"] == "shape"), path


@pytest.mark.parametrize("report", sorted(p.name for p in DIST.glob("*.Report") if p != FIN001))
def test_uebrige_dist_reports_englisch(report: str) -> None:
    """Gegenprobe: ohne report_locale bleibt der Alt-Text englisch."""
    texte = _dist_alt(DIST / report)
    assert not any(p in t for t in texte for p in (" im Vergleich zu ", "Filtern nach ", " nach ")), report


def test_werkzeug_liest_sprache_aus_dem_bracket(tmp_path: Path) -> None:
    import shutil
    kopie = tmp_path / FIN001.name
    shutil.copytree(FIN001, kopie)
    # byPath-Nachbar: ohne Modell bricht das Werkzeug ab (Text-Measures unbekannt)
    shutil.copytree(DIST / "Finance.SemanticModel", tmp_path / "Finance.SemanticModel")
    assert at.report_locale(kopie) == "de-DE"
    assert at.main([str(kopie)]) == 0
    assert _dist_alt(kopie) == _dist_alt(FIN001)  # dist ist schon erzeugt: nichts zu tun
    assert at.main([str(kopie), "--locale", "en-US"]) == 0
    en = _dist_alt(kopie)
    assert any(" by " in t for t in en) and not any(p in t for t in en for p in _DEUTSCH)
    # nur die Alt-Text-Zeile wechselt (handformatierte Dateien bleiben unberuehrt)
    for p in sorted(kopie.rglob("visual.json")):
        alt, neu = (FIN001 / p.relative_to(kopie)).read_text(encoding="utf-8").splitlines(), \
            p.read_text(encoding="utf-8").splitlines()
        assert len(alt) == len(neu)
        assert all(a == b or '"Value"' in a for a, b in zip(alt, neu)), p


# --- Kacheln und lokalisierte Kennzahlnamen (02.10.2026) -------------------------------------------


def test_kachel_nennt_kennzahl_und_aktuellen_wert() -> None:
    card = _v("cardVisual", {"Data": {"projections": [_m("Net Sales")]}})
    assert at.describe(card) == "Net Sales: current value"
    assert at.describe(card, locale="de-DE") == "Net Sales: aktueller Wert"
    assert at.describe(_v("cardVisual", {"Data": {"projections": [_m("Net Sales"), _m("Net Sales PY")]}}),
                       ["Net Sales PY"]) == "Net Sales: current value compared with Net Sales PY"
    # Gegenprobe: ein Chart mit derselben Bindung bekommt keine Kachelform
    assert at.describe(_v("clusteredBarChart", {"Y": {"projections": [_m("Net Sales")]}})) == "Net Sales"


def test_kpi_visual_zielwert_ist_vergleich() -> None:
    kpi = _v("kpi", {"Indicator": {"projections": [_m("OTIF %")]}, "Goal": {"projections": [_m("OTIF Target")]},
                     "TrendLine": {"projections": [_c("dim_date", "Month")]}})
    assert at.describe(kpi) == "OTIF %: current value compared with OTIF Target by Month"


def test_alte_kachelform_wird_ersetzt_handtext_nicht() -> None:
    card = _v("cardVisual", {"Data": {"projections": [_m("Cash")]}})
    card["visual"]["visualContainerObjects"] = {"general": [{"properties": {"altText": {
        "expr": {"Literal": {"Value": "'Cash'"}}}}}]}
    at.apply_alt_text(card, replace_generated=True)
    assert _alt(card) == "Cash: current value"
    card["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"]["expr"]["Literal"]["Value"] = "'Hand'"
    at.apply_alt_text(card, replace_generated=True)
    assert _alt(card) == "Hand"


def test_ausdruck_als_alt_text_bleibt() -> None:
    """Learn: dynamischer Alt-Text per Measure (bedingte Formatierung) -- nie ueberschreiben."""
    card = _v("cardVisual", {"Data": {"projections": [_m("Cash")]}})
    expr = {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Cash Alt"}}}
    card["visual"]["visualContainerObjects"] = {"general": [{"properties": {"altText": expr}}]}
    at.apply_alt_text(card, replace_generated=True)
    assert card["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"] == expr


def test_lokalisierter_kennzahlname_nur_wenn_gefuehrt() -> None:
    card = _v("cardVisual", {"Data": {"projections": [_m("Net Sales"), _m("Net Sales PY")]}})
    namen = {"Net Sales": {"de": "Nettoumsatz"}}
    assert at.describe(card, ["Net Sales PY"], locale="de-DE", kpi_namen=namen) == \
        "Nettoumsatz: aktueller Wert im Vergleich zu Net Sales PY"
    assert at.describe(card, ["Net Sales PY"], locale="en-US", kpi_namen=namen) == \
        "Net Sales: current value compared with Net Sales PY"


def test_katalog_fuehrt_keine_namen_je_sprache() -> None:
    """Lueckenmessung: kein KPI im Katalog fuehrt einen Namen je Sprache. Wird dieser Test rot,
    gibt es die Quelle -- dann `kpi_namen` aus dem Katalog an den Generator anschliessen."""
    import yaml
    sprachfelder = []
    for f in sorted((REPO / "core" / "kpi_catalog" / "kpis").glob("*.yaml")):
        kpi = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for teil in (kpi, kpi.get("business") or {}, kpi.get("technical") or {}):
            sprachfelder += [f"{f.name}:{k}" for k in teil
                             if any(t in k.lower() for t in ("_de", "_en", "i18n", "locale", "translation"))]
    assert sprachfelder == []


# --- Text-Measures auf Kacheln (03.10.2026) ------------------------------------------------------

COMMERCIAL = DIST / "Commercial.SemanticModel"


def test_text_measures_aus_dem_modell() -> None:
    """formatString @ im TMDL ist die Quelle; Kennzahlen mit Zahlformat sind keine Text-Measures."""
    texte = at.text_measures(COMMERCIAL)
    assert {"Narrative Text (COM)", "Last Refresh (COM)", "Active Actions Text"} <= texte
    assert "Net Sales Amount" not in texte
    assert at.text_measures(None) == frozenset()
    gesamt = sum(len(at.text_measures(m)) for m in DIST.glob("*.SemanticModel"))
    assert gesamt == 70  # gemessen 03.10.2026, fuenf dist-Modelle


def test_kachel_mit_text_measure_nennt_nur_den_namen() -> None:
    card = _v("cardVisual", {"Data": {"projections": [_m("Narrative Text (COM)")]}})
    texte = {"Narrative Text (COM)"}
    assert at.describe(card, text_measures=texte) == "Narrative Text (COM)"
    assert at.describe(card, locale="de-DE", text_measures=texte) == "Narrative Text (COM)"
    # Gegenprobe: ein Kennzahl-Measure auf derselben Kachelart behaelt "aktueller Wert"
    zahl = _v("cardVisual", {"Data": {"projections": [_m("Net Sales")]}})
    assert at.describe(zahl, locale="de-DE", text_measures=texte) == "Net Sales: aktueller Wert"
    # gemischt: nicht nur Text -> Kachelform bleibt
    gemischt = _v("cardVisual", {"Data": {"projections": [_m("Net Sales"), _m("Narrative Text (COM)")]}})
    assert at.describe(gemischt, text_measures=texte) == "Current values of Net Sales and Narrative Text (COM)"


def test_erzeugte_kachelform_wird_fuer_text_measure_ersetzt() -> None:
    card = _v("cardVisual", {"Data": {"projections": [_m("Last Refresh (COM)")]}})
    card["visual"]["visualContainerObjects"] = {"general": [{"properties": {"altText": {
        "expr": {"Literal": {"Value": "'Last Refresh (COM): current value'"}}}}}]}
    at.apply_alt_text(card, replace_generated=True, text_measures={"Last Refresh (COM)"})
    assert _alt(card) == "Last Refresh (COM)"


def test_generator_text_kacheln_ohne_aktuellen_wert() -> None:
    texte = {v["name"]: _alt(v) for v in _generiert("COM-001")}
    assert texte["Smart_Narrative"] == "Narrative Text (COM)"
    assert texte["Last_Refresh"] == "Last Refresh (COM)"


def _dist_kacheln():
    for report in sorted(DIST.glob("*.Report")):
        texte = at.text_measures(at.report_model_dir(report))
        for p in sorted((report / "definition" / "pages").glob("*/visuals/*/visual.json")):
            v = json.loads(p.read_text(encoding="utf-8"))
            if (v.get("visual") or {}).get("visualType") in at.CARD_TYPES:
                yield report, p, v, texte


def test_dist_text_kacheln_ohne_aktuellen_wert() -> None:
    nur_text = [(p, _alt(v)) for _r, p, v, texte in _dist_kacheln()
                if all(m in texte for m in at._measure_properties(v["visual"]))]
    assert len(nur_text) == 50  # gemessen 03.10.2026: Narrative, Last Refresh, Active Actions in 17 Reports
    falsch = [(str(p), t) for p, t in nur_text if not t or "current value" in t or "aktueller Wert" in t]
    assert falsch == []
    # Gegenprobe: Kacheln mit Kennzahlen behalten die Kachelform
    zahl = [_alt(v) for _r, _p, v, texte in _dist_kacheln()
            if not all(m in texte for m in at._measure_properties(v["visual"]))]
    assert zahl and all("current value" in t or "aktueller Wert" in t or "Current values" in t
                        or "Aktuelle Werte" in t for t in zahl)


def test_report_model_dir_folgt_definition_pbir() -> None:
    assert at.report_model_dir(DIST / "COM-001_Sales_Performance.Report") == COMMERCIAL.resolve()


def test_werkzeug_ohne_modell_bricht_ab(tmp_path: Path) -> None:
    """Ohne Semantikmodell sind Text-Measures unbekannt: das Werkzeug raet nicht, es bricht ab."""
    import shutil
    kopie = tmp_path / FIN001.name
    shutil.copytree(FIN001, kopie)
    assert at.main([str(kopie)]) == 1
    assert _dist_alt(kopie) == _dist_alt(FIN001)
    assert at.main([str(kopie), "--model", str(DIST / "Finance.SemanticModel")]) == 0
