"""Muster Tabelle, Matrix und Sparkline als Relation: Feld im Register, Eigenschaft im Template, Messung am Artefakt.

Runde rubrikpaket, 22.10.2026 (Meridian BO-414, 415, 416, 419, 429). Tabellen und Sparklines haben keine Vega-Spur:
gemessen wird am PBIR-Golden gegen den Formatkatalog, an der DAX-Vorlage (Formel und Parameter) und an der SVG, die
die Measure ausgibt (vl_convert). Die DAX-Auswertung selbst bleibt Desktop-gebunden (umsetzung.nativ im Register).
Jeder Fall hat seine Gegenprobe: ohne Parameter, Freigabe oder Wert verschwindet die Eigenschaft.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
sys.path.insert(0, str(REPO_ROOT))
import gestaltung  # noqa: E402
import render  # noqa: E402
import render_acceptance  # noqa: E402
from tooling.report_quality import formatting_metadata as fm  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
GOLDEN = LIB / "golden"
KPIS = REPO_ROOT / "core" / "kpi_catalog" / "kpis"
SCHEMA = REPO_ROOT / "tooling" / "generator" / "schemas" / "kpi_definition.schema.json"
_TABELLEN = {"tableEx", "pivotTable"}


def _lit(obj: dict, prop: str):
    return obj[prop]["expr"]["Literal"]["Value"]


def _dax(idiom: str, **params: str) -> str:
    """Die SVG-DAX-Vorlage mit den kanonischen Parametern, einzelne überschrieben."""
    entry = render.load_entry(idiom)
    real = render._realization(entry, "powerbi_svg_dax", render.default_profile())
    return render.fill(real["template"], {**render._effective_params(entry, render.default_profile()), **params})


def _native_tables() -> list[tuple[str, dict]]:
    out = []
    for path in sorted(GOLDEN.glob("matrix_*.powerbi_native.json")):
        v = json.loads(path.read_text(encoding="utf-8"))
        if v.get("visualType") in _TABELLEN:
            out.append((path.name, v))
    return out


# --- T2 Haarlinien ----------------------------------------------------------------------------------------------

def test_native_tables_draw_horizontal_hairlines_only():
    r = gestaltung.regel("tabellen_linien")
    tabellen = _native_tables()
    assert {n.split(".")[0] for n, _ in tabellen} >= {"matrix_evidence", "matrix_sparkline", "matrix_pivot"}
    for name, v in tabellen:
        grid = v["objects"]["grid"][0]["properties"]
        assert _lit(grid, "gridVertical") == "false", name
        assert _lit(grid, "gridHorizontal") == "true", name
        assert _lit(grid, "gridHorizontalWeight") == f"{r['linie']['staerke_px']}D", name
        assert grid["gridHorizontalColor"]["solid"]["color"]["expr"]["Literal"]["Value"] == f"'{r['linie']['farbe']}'"
        assert _lit(grid, "outlineWeight") == "0D", name
        assert fm.unknown_visual_objects({"visual": v}) == [], name
    # Gegenprobe: ohne grid-Objekt (Stand vor der Runde) fällt der Test, eine erfundene Eigenschaft meldet der Katalog.
    name, v = tabellen[0]
    v["objects"]["grid"][0]["properties"]["gridVertikal"] = {}
    assert fm.unknown_visual_objects({"visual": v}) == ["grid.gridVertikal"]


def test_hairline_colour_is_the_border_token():
    tok_pfad = REPO_ROOT / "core/templates/page_templates/tokens/color_semantics.yaml"
    tok = yaml.safe_load(tok_pfad.read_text(encoding="utf-8"))
    assert tok["border"]["default"] == gestaltung.regel("tabellen_linien")["linie"]["farbe"]


# --- T6 / SP1 gemeinsame Skala ---------------------------------------------------------------------------------------

def test_sparkline_column_shares_one_scale_by_default():
    r = gestaltung.regel("sparkline_skala")
    assert render.load_entry("matrix_sparkline")["canonical_params"]["scale"] == r["standard"] == "shared"
    geteilt = _dax("matrix_sparkline")
    assert '"shared" = "shared"' in geteilt
    assert re.search(r"VAR _alle = CALCULATETABLE \(.*ALLSELECTED \( 'dim_product'\[Category\] \)", geteilt)
    assert "VAR _lo0 = IF ( _geteilt, MINX ( _alle, [@v] )" in geteilt
    svg = render_acceptance._svg_from_dax(geteilt)
    assert "<title>" not in svg
    # per_row: Referenzlinie und Hinweis, sonst nicht
    je_zeile = _dax("matrix_sparkline", scale="per_row")
    assert '"per_row" = "shared"' in je_zeile
    hinweis = render.load_entry("matrix_sparkline")["canonical_params"][r["hinweis_param"]]
    assert f"<title>{hinweis}</title><line" in je_zeile


def test_native_sparkline_column_names_its_per_row_scale():
    """Nativ skaliert Power BI je Zeile (Register nativ: entfaellt): der Spaltenkopf trägt den Hinweis."""
    v = json.loads((GOLDEN / "matrix_sparkline.powerbi_native.json").read_text(encoding="utf-8"))
    hinweis = render.load_entry("matrix_sparkline")["canonical_params"]["label_per_row"]
    spark = [p for p in v["query"]["queryState"]["Values"]["projections"] if "SparklineData" in p["field"]]
    assert len(spark) == 1 and hinweis in spark[0]["displayName"]
    assert gestaltung.regel("sparkline_skala")["umsetzung"]["nativ"] == "entfaellt"


# --- SP2 Marken, SP6 Lücken, SP4 Größe ------------------------------------------------------------------------

@pytest.mark.parametrize("idiom,farbe", [("matrix_sparkline", "#0F2430"), ("kpi_card_spark", "#605E5C")])
def test_first_point_hollow_last_point_filled(idiom, farbe):
    r = gestaltung.regel("sparkline_marken")
    dax = _dax(idiom)
    assert f"r='2' fill='#FFFFFF' stroke='{farbe}'" in dax
    assert f"r='{r['radius_letzter']}' fill='{farbe}'" in dax
    assert "_marken" in dax.split("RETURN", 1)[1], "die Marken stehen in der ausgegebenen SVG"
    vlc = pytest.importorskip("vl_convert")
    assert vlc.svg_to_png(render_acceptance._svg_from_dax(dax))[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("idiom", ["matrix_sparkline", "kpi_card_spark"])
def test_gaps_break_starts_a_new_path_after_a_blank(idiom):
    r = gestaltung.regel("sparkline_luecken")
    entry = render.load_entry(idiom)
    assert entry["canonical_params"]["gaps"] == r["standard"] == "break"
    brk = _dax(idiom)
    assert '( [@luecke] && "break" = "break" ), " M", " L"' in brk
    assert "FILTER ( _S, NOT ISBLANK ( [@v] ) )" in brk, "leere Werte zeichnen keinen Punkt"
    # Gegenproben: connect verbindet (Bedingung nie wahr), zero setzt leer = 0.
    assert '"connect" = "break"' in _dax(idiom, gaps="connect")
    assert '"zero" = "zero", [' in _dax(idiom, gaps="zero")
    assert "<path fill='none'" in brk and "polyline" not in brk


def _viewbox(dax: str) -> tuple[float, float]:
    w, h = re.search(r"viewBox='0 0 (\d+) (\d+)'", dax).groups()
    return float(w), float(h)


def test_sparklines_meet_the_minimum_size():
    r = gestaltung.regel("sparkline_groesse")
    zelle = _dax("matrix_sparkline")
    assert gestaltung.sparkline_groesse_ok(*_viewbox(zelle), "zelle")
    karte = _dax("kpi_card_spark")
    xw = int(re.search(r'"@x", INT \( 12 \+ (\d+) \*', karte).group(1))
    yh = int(re.search(r'"@y", INT \( 96 - (\d+) \*', karte).group(1))
    assert gestaltung.sparkline_groesse_ok(xw, yh, "karte")
    assert yh >= r["min_hoehe_px"]["karte"]
    # Gegenprobe: die alte Karte (26 px hoch) fiele durch.
    assert not gestaltung.sparkline_groesse_ok(214, 26, "karte")


# --- L7 / SP5 Zielband ----------------------------------------------------------------------------------------------

_FREI = {"von": "business_owner", "am": "2026-10-22", "quelle": "Protokoll", "freigabe_quelle": "simuliert_showcase"}


def test_band_only_from_an_approved_corridor():
    assert gestaltung.zielband({"target_corridor": {"lower": 75, "upper": 85, "freigabe": _FREI}}) == \
        {"band_low": "75.0", "band_high": "85.0"}
    assert gestaltung.zielband({"target_corridor": {"lower": 75, "upper": 85,
                                                    "freigabe": {**_FREI, "quelle": None}}}) is None
    assert gestaltung.zielband({"target_corridor": {"lower": None, "upper": 85, "freigabe": _FREI}}) is None
    assert gestaltung.zielband({"target_corridor": {"lower": 85, "upper": 75, "freigabe": _FREI}}) is None
    assert gestaltung.zielband({"good_is": "band"}) is None, "keine Herleitung aus Richtung, Ziel oder Alarm"


def test_corridor_field_is_in_the_schema_and_requires_approval():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    kpi = yaml.safe_load((KPIS / "KPI-SVC-009.yaml").read_text(encoding="utf-8"))
    jsonschema.validate({**kpi, "target_corridor": {"lower": None, "upper": None,
                                                    "freigabe": {"von": None, "am": None, "quelle": None}}}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**kpi, "target_corridor": {"lower": 75, "upper": 85}}, schema)


def test_no_catalog_kpi_draws_a_band_without_approval():
    """Golden Thread: der Korridor entscheidet der Owner. Heute trägt kein KPI einen — und keiner ein Band ohne
    Freigabe."""
    for path in sorted(KPIS.glob("*.yaml")):
        kpi = yaml.safe_load(path.read_text(encoding="utf-8"))
        if "target_corridor" in kpi:
            assert gestaltung.zielband(kpi) is not None or not any(
                (kpi["target_corridor"].get(k) is not None) for k in ("lower", "upper")), path.name


def test_line_draws_the_band_behind_the_line_only_with_values():
    vlc = pytest.importorskip("vl_convert")
    farbe = gestaltung.regel("zielband")["farbe"]
    rows = [{"d": f"2026-{m:02d}-01", "v": 40 + m} for m in range(1, 7)]

    def baender(params):
        spec = json.loads(render.render_target("line", "html_vegalite", None, bindings={"time": "d", "value": "v"},
                                               params=params)[0])
        spec["data"] = {"name": "dataset", "values": rows}
        out = []

        def walk(n):
            if isinstance(n, dict):
                if n.get("marktype") == "rect":
                    out.extend(i for i in n.get("items", []) if i.get("fill") == farbe)
                for x in n.values():
                    walk(x)
            elif isinstance(n, list):
                for x in n:
                    walk(x)
        walk(vlc.vegalite_to_scenegraph(spec))
        return out

    band = gestaltung.zielband({"target_corridor": {"lower": 42, "upper": 44, "freigabe": _FREI}})
    mit = baender(band)
    assert len(mit) == 1 and mit[0]["height"] > 0 and not mit[0].get("stroke")
    assert not baender(None), "ohne freigegebenen Korridor kein Band"


@pytest.mark.parametrize("idiom", ["matrix_sparkline", "kpi_card_spark"])
def test_sparkline_band_needs_both_bounds(idiom):
    leer = _dax(idiom)
    assert "VAR _bl = BLANK ()" in leer and "NOT ISBLANK ( _bl ) && NOT ISBLANK ( _bh )" in leer
    mit = _dax(idiom, band_low_expr="[KPI Korridor unten]", band_high_expr="[KPI Korridor oben]")
    assert "VAR _bl = [KPI Korridor unten]" in mit and "fill='#ECECEC'" in mit


# --- M1 Hierarchie --------------------------------------------------------------------------------------------------

def test_matrix_pivot_carries_hierarchy_frozen_headers_and_subtotals_on_top():
    r = gestaltung.regel("matrix_hierarchie")
    v = json.loads((GOLDEN / "matrix_pivot.powerbi_native.json").read_text(encoding="utf-8"))
    assert v["visualType"] == "pivotTable"
    assert len(v["query"]["queryState"]["Rows"]["projections"]) == 2
    rh = v["objects"]["rowHeaders"][0]["properties"]
    assert _lit(rh, "stepped") == "true" and _lit(rh, "showExpandCollapseButtons") == "true"
    assert _lit(rh, "unfrozen") == "false"
    st = v["objects"]["subTotals"][0]["properties"]
    assert _lit(st, "rowSubtotals") == "true"
    assert _lit(st, "rowSubtotalsPosition") == ("'Top'" if r["zwischensumme"] == "oben" else "'Bottom'")
    assert fm.unknown_visual_objects({"visual": v}) == []
    index = yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))
    assert "matrix_pivot" in index["implemented"]
    assert "matrix_pivot" in index["purposes"]["evidence_detail"]["candidates"]
