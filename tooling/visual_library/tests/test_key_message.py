"""Kernaussage je Visual (D-623 Nachtrag in Freelancing, feat-109): Regeln und Hervorhebung.

Gemessen wird am gezeichneten Chart (Vega-Szenengraph): mit `kernaussage` aus ist jede Marke voll
deckend, mit an nur die Treffer. Gegenprobe: ohne den Parameter bleibt die Spec unverändert.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import key_message as K  # noqa: E402
import render  # noqa: E402

REGIONS = {"columns": [{"name": "Region"}, {"name": "Wert"}],
           "rows": [["DACH", 24.4], ["Benelux", 27.8], ["Nordics", 31.4], ["Southern Europe", 34.5]]}
CAUSES = {"columns": [{"name": "Ursache"}, {"name": "Beitrag"}],
          "rows": [["Conversion", 34], ["Out-of-Stock", 27], ["Saison", 16], ["Kampagne", 13], ["Sonstige", 10]]}
WEEKS = {"columns": [{"name": "Periode"}, {"name": "Ist"}, {"name": "Plan"}],
         "rows": [["2025-12-22", 33.5, 45.0], ["2025-12-29", 33.9, 45.0], ["2026-01-05", 33.6, 45.0]]}


# --- Regeln ------------------------------------------------------------------------------------

def test_quote_nennt_schwaechsten_und_staerksten_wert_nach_richtung():
    m = K.key_message(REGIONS, {"category": "Region", "value": "Wert"}, unit="%")
    assert K.plain_text(m) == "Am schwächsten: DACH mit 24,4 %, am stärksten: Southern Europe mit 34,5 %."
    assert m["highlight"] == {"field": "Region", "values": ["DACH"], "temporal": False}
    # Gegenprobe: weniger ist besser (Kosten) dreht die Aussage
    low = K.key_message(REGIONS, {"category": "Region", "value": "Wert"}, polarity=-1, unit="%")
    assert low["highlight"]["values"] == ["Southern Europe"]


def test_beitrag_nennt_den_groessten_mit_anteil():
    m = K.key_message(CAUSES, {"category": "Ursache", "value": "Beitrag"}, additive=True)
    assert K.plain_text(m) == "Größter Beitrag: Conversion mit 34, das sind 34 % der Summe."
    assert [s["text"] for s in m["segments"] if s["strong"]] == ["Conversion", "34", "34 %"]


def test_zeit_gegen_plan_in_prozentpunkten():
    m = K.key_message(WEEKS, {"time": "Periode", "value": "Ist", "plan": "Plan"}, unit="%", weekly=True)
    assert K.plain_text(m) == "KW 02: Ist 33,6 % gegen Plan 45,0 %, 11,4 PP unter Plan."
    assert m["highlight"] == {"field": "Periode", "values": ["2026-01-05"], "temporal": True}


def test_zeit_ohne_plan_erste_gegen_letzte_periode():
    m = K.key_message(WEEKS, {"time": "Periode", "value": "Ist"}, unit="%", weekly=True)
    assert K.plain_text(m) == "KW 52 bis KW 02: 33,5 % auf 33,6 %, +0,1 PP."


def test_eine_nachkommastelle_wie_am_chart_und_unveraendert_statt_null():
    t = {"columns": WEEKS["columns"], "rows": [["2025-12-22", 27.95, 35.0], ["2026-01-05", 27.95, 35.0]]}
    m = K.key_message(t, {"time": "Periode", "value": "Ist", "plan": "Plan"}, unit="%", weekly=True)
    assert "Ist 27,9\u00a0% gegen Plan 35,0\u00a0%, 7,1\u00a0PP" in K.plain_text(m), "eine Stelle, gerundet wie Vega"
    flat = K.key_message(t, {"time": "Periode", "value": "Ist"}, unit="%", weekly=True)
    assert K.plain_text(flat) == "KW 52 bis KW 02: unverändert bei 27,9\u00a0%."


def test_keine_regel_keine_aussage():
    assert K.key_message(REGIONS, {"value": "Wert"}) is None
    flat = {"columns": REGIONS["columns"], "rows": [["A", 1], ["B", 1]]}
    assert K.key_message(flat, {"category": "Region", "value": "Wert"}) is None, "ohne Unterschied keine Aussage"


def test_deutsche_zahlen():
    assert K.de_number(1234.5, 1) == "1.234,5"
    assert K.de_number(-0.4, 1) == "−0,4"
    assert K.de_number(-0.01, 1) == "0,0"
    assert K.de_number(2, 0, signed=True) == "+2"


# --- Hervorhebung am gezeichneten Chart --------------------------------------------------------

def _opacities(idiom: str, roles: dict, rows: list[dict], highlight: dict | None, on: bool) -> dict:
    vlc = pytest.importorskip("vl_convert")
    params = {"highlight": highlight} if highlight else None
    spec = json.loads(render.render_target(idiom, "html_vegalite", "ibcs", bindings=roles, params=params)[0])
    spec["data"] = {"values": rows}
    spec["width"], spec["height"] = 300, 200
    if highlight:
        spec["params"] = [{**p, "value": on} if p["name"] == render.KEY_PARAM else p for p in spec["params"]]
    out: dict = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("role") == "mark" and node.get("marktype") in ("rect", "symbol"):
                for it in node.get("items", []):
                    out.setdefault(node["marktype"], []).append(round(it.get("opacity", 1), 2))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    return out


BARS = [{"Region": r, "Wert": v} for r, v in REGIONS["rows"]]


def test_balken_aus_alle_deckend_an_nur_der_treffer():
    h = {"field": "Region", "values": ["DACH"], "temporal": False}
    roles = {"category": "Region", "value": "Wert"}
    assert set(_opacities("bar_ranking", roles, BARS, h, on=False)["rect"]) == {1}
    on = _opacities("bar_ranking", roles, BARS, h, on=True)["rect"]
    assert sorted(on) == [render.KEY_DIM] * 3 + [1], on


def test_zeitreihe_hebt_die_letzte_periode_hervor():
    rows = [{"Periode": p, "Ist": a, "Plan": pl} for p, a, pl in WEEKS["rows"]]
    roles = {"time": "Periode", "value": "Ist", "plan": "Plan"}
    h = {"field": "Periode", "values": ["2026-01-05"], "temporal": True}
    sym = _opacities("line", roles, rows, h, on=True).get("symbol", [])
    # zwei Reihen (Ist, Plan) je drei Punkte: je Reihe genau einer deckend
    assert sorted(sym) == [render.KEY_DIM] * 4 + [1, 1], sym


def test_ohne_parameter_bleibt_die_spec_unveraendert():
    roles = {"category": "Region", "value": "Wert"}
    plain = render.render_target("bar_ranking", "fabric_app", "ibcs", bindings=roles)[0]
    assert render.KEY_PARAM not in plain
