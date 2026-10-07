"""IBCS 2.0 EX 2.1 bis EX 2.5 in der Verbotsliste (`ForbiddenVisualTypes`).

Jede Regel mit Treffer und Gegenprobe; die Seitenzahlen der Verbotsliste werden gegen den
IBCS-2.0-Katalog gelesen (eine Konstante ohne Nachbarn wird von nichts gegengelesen).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tooling.report_quality.structural_validator import (
    AUSNAHME_ANNOTATION,
    EX_2_1,
    EX_2_2,
    EX_2_3_RADAR,
    EX_2_3_TRICHTER,
    EX_2_4,
    EX_2_5,
    HAUS_TREEMAP,
    ReportSpec,
    ForbiddenVisualTypes,
    check_report,
)

REPO = Path(__file__).resolve().parents[2]
KATALOG = REPO / "docs/architecture/research/2026-09-30_visual-stack-r1/ibcs_v2.yaml"
SPEC = ReportSpec(invariants=[ForbiddenVisualTypes()])


def _report(tmp_path: Path, visual: dict) -> Path:
    rep = tmp_path / "UC-TEST.Report"
    vdir = rep / "definition" / "pages" / "P" / "visuals" / "v"
    vdir.mkdir(parents=True)
    body = {"name": "v", "position": {"x": 0, "y": 0, "width": 100, "height": 100}}
    body.update(visual)
    (vdir / "visual.json").write_text(json.dumps(body), encoding="utf-8")
    (rep / "definition" / "pages" / "P" / "page.json").write_text(
        json.dumps({"name": "P", "width": 1280, "height": 720}), encoding="utf-8")
    (rep / "definition" / "pages" / "pages.json").write_text(
        json.dumps({"pageOrder": ["P"]}), encoding="utf-8")
    return rep


def _befunde(tmp_path: Path, visual: dict) -> list:
    return check_report(_report(tmp_path, visual), SPEC)


def _typ(vt: str, **extra) -> dict:
    return {"visual": {"visualType": vt, **extra}}


def _ausnahme(wert: str) -> dict:
    return {"annotations": [{"name": AUSNAHME_ANNOTATION, "value": wert}]}


def _proj(n: int) -> dict:
    return {"projections": [{"queryRef": f"m{i}"} for i in range(n)]}


# ── Katalog als Nachbar ────────────────────────────────────────────────────────

def test_seiten_stimmen_mit_katalog():
    katalog = {r["rule_id"]: r["seite"] for r in yaml.safe_load(KATALOG.read_text(encoding="utf-8"))}
    for regel in (EX_2_1, EX_2_2, EX_2_3_RADAR, EX_2_3_TRICHTER, EX_2_4, EX_2_5):
        assert katalog[regel.regel_id] == regel.seite, regel
        assert regel.severity == "warning", regel  # IBCS: "replace" mit Ausnahmen
    assert HAUS_TREEMAP.seite is None and HAUS_TREEMAP.severity == "critical"


def test_ausnahmen_wie_im_katalog():
    katalog = {r["rule_id"]: r["parameters"] for r in yaml.safe_load(KATALOG.read_text(encoding="utf-8"))}
    # EX 2.1: Ausnahme nur auf Kartenpunkt, max. 3 Werte -> fuer pieChart/donutChart nicht erklaerbar
    assert katalog["EX 2.1"]["max_values_per_pie"] == 3 and EX_2_1.ausnahme is None
    assert len(katalog["EX 2.2"]["exception_all_of"]) == 3 and "alle drei" in EX_2_2.ausnahme
    assert "radar_exception" in katalog["EX 2.3"] and EX_2_3_TRICHTER.ausnahme is None


# ── EX 2.1 Torte/Ring ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("vt", ["pieChart", "donutChart"])
def test_ex21_torte_und_ring_warnung(tmp_path, vt):
    (b,) = _befunde(tmp_path, _typ(vt))
    assert b.severity == "warning" and "IBCS 2.0 EX 2.1, S. 136" in b.message
    assert "Forbidden visual type" in b.message  # Signatur in tooling/quality/known_errors.yaml


def test_ex21_annotation_hebt_nicht_auf(tmp_path):
    # Gegenprobe: eine erklaerte Ausnahme zaehlt nur, wo der Katalog eine kennt.
    (b,) = _befunde(tmp_path, {**_typ("pieChart"), **_ausnahme("EX 2.1: Kartenpunkt")})
    assert b.severity == "warning"


def test_ex21_karte_ist_frei(tmp_path):
    # EX 2.1 greift nicht bei Karten. Seit 07.10.2026 ist der Bing-`map` aber von Microsoft
    # abgekuendigt (MS-DEPRECATED, Ersatz azureMap); das ist der einzige Befund, kein IBCS.
    (b,) = _befunde(tmp_path, _typ("map"))
    assert "IBCS" not in b.message and "azureMap" in b.expected
    assert _befunde(tmp_path / "azure", _typ("azureMap")) == []


# ── EX 2.2 Tacho ───────────────────────────────────────────────────────────────

def test_ex22_tacho_warnung(tmp_path):
    (b,) = _befunde(tmp_path, _typ("gauge"))
    assert b.severity == "warning" and "EX 2.2, S. 136" in b.message


def test_ex22_tacho_custom_visual_per_teilwort(tmp_path):
    (b,) = _befunde(tmp_path, _typ("linearGauge1234ABCD"))
    assert "EX 2.2" in b.message


def test_ex22_echtzeit_ausnahme_wird_info(tmp_path):
    (b,) = _befunde(tmp_path, {**_typ("gauge"), **_ausnahme("EX 2.2: Leitstand, live")})
    assert b.severity == "info" and b.actual == "EX 2.2: Leitstand, live"


def test_ex22_ausnahme_einer_anderen_regel_zaehlt_nicht(tmp_path):
    (b,) = _befunde(tmp_path, {**_typ("gauge"), **_ausnahme("EX 2.4: Hoehenvergleich")})
    assert b.severity == "warning"


# ── EX 2.3 Radar und Trichter ──────────────────────────────────────────────────

def test_ex23_trichter_warnung_ohne_ausnahme(tmp_path):
    (b,) = _befunde(tmp_path, {**_typ("funnel"), **_ausnahme("EX 2.3: egal")})
    assert b.severity == "warning" and "EX 2.3, S. 137" in b.message


@pytest.mark.parametrize("vt", ["RadarChart1446119667547", "spiderChartXYZ"])
def test_ex23_radar_custom_visual(tmp_path, vt):
    (b,) = _befunde(tmp_path, _typ(vt))
    assert b.severity == "warning" and "EX 2.3" in b.message


def test_ex23_radar_himmelsrichtung_ausnahme(tmp_path):
    (b,) = _befunde(tmp_path, {**_typ("RadarChart1"), **_ausnahme("EX 2.3: Windrichtung")})
    assert b.severity == "info"


# ── EX 2.4 Spaghetti ───────────────────────────────────────────────────────────

def test_ex24_fuenf_linien_warnung(tmp_path):
    vis = _typ("lineChart", query={"queryState": {"Category": _proj(1), "Y": _proj(5)}})
    (b,) = _befunde(tmp_path, vis)
    assert b.severity == "warning" and "EX 2.4, S. 138" in b.message and "5 Linien" in b.message


def test_ex24_vier_linien_frei(tmp_path):
    vis = _typ("lineChart", query={"queryState": {"Category": _proj(1), "Y": _proj(3), "Y2": _proj(1)}})
    assert _befunde(tmp_path, vis) == []


def test_ex24_small_multiples_sind_der_ersatz(tmp_path):
    vis = _typ("lineChart", query={"queryState": {"Y": _proj(6), "Rows": _proj(1)}})
    assert _befunde(tmp_path, vis) == []


def test_ex24_series_feld_ist_info_nicht_still(tmp_path):
    vis = _typ("lineChart", query={"queryState": {"Y": _proj(1), "Series": _proj(1)}})
    (b,) = _befunde(tmp_path, vis)
    assert b.severity == "info" and "datenabhaengig" in b.message


def test_ex24_hoehenvergleich_ausnahme(tmp_path):
    vis = {**_typ("lineChart", query={"queryState": {"Y": _proj(6)}}), **_ausnahme("EX 2.4: exakt")}
    (b,) = _befunde(tmp_path, vis)
    assert b.severity == "info"


# ── EX 2.5 Ampel ───────────────────────────────────────────────────────────────

def _icons(*werte: str) -> dict:
    cases = [{"Value": {"Literal": {"Value": w}}} for w in werte]
    return {"values": [{"properties": {"icon": {"value": {"Conditional": {"Cases": cases}}}}}]}


def test_ex25_dreistufige_ampel_warnung(tmp_path):
    (b,) = _befunde(tmp_path, _typ("tableEx", objects=_icons("'red'", "'yellow'", "'green'")))
    assert b.severity == "warning" and "EX 2.5, S. 138" in b.message


def test_ex25_binaer_ist_ausnahme(tmp_path):
    assert _befunde(tmp_path, _typ("tableEx", objects=_icons("'red'", "'green'"))) == []


def test_ex25_measure_gesteuert_warnung(tmp_path):
    objects = {"values": [{"properties": {"iconSet": {"solid": {"color": {"expr": {
        "Measure": {"Property": "Trend Icon"}}}}}}}]}
    (b,) = _befunde(tmp_path, _typ("tableEx", objects=objects))
    assert b.severity == "warning" and "Measure-gesteuert" in b.message


def test_ex25_schwellen_compliance_ausnahme(tmp_path):
    vis = {**_typ("tableEx", objects=_icons("'a'", "'b'", "'c'")), **_ausnahme("EX 2.5: SLA erfuellt")}
    (b,) = _befunde(tmp_path, vis)
    assert b.severity == "info"


def test_ohne_symbole_frei(tmp_path):
    assert _befunde(tmp_path, _typ("tableEx", objects={"values": [{"properties": {}}]})) == []


# ── Hausregel ──────────────────────────────────────────────────────────────────

def test_treemap_bleibt_kritisch(tmp_path):
    (b,) = _befunde(tmp_path, _typ("treemap"))
    assert b.severity == "critical" and "BC-CHART-08" in b.message
