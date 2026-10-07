"""Vorjahr (PY) und Prognose (FC) im Idiom line (BO-052, BO-116 in Freelancing, 02.10.2026).

BO-052: line hatte keine Vorjahresrolle; das Cockpit band `prior`, die Linie zeichnete nur das Ist.
BO-116: line@ibcs powerbi_native band die Prognose nicht; der Report-Generator hätte sie neben dem
Idiom selbst bauen müssen. Gemessen am Szenengraph (Vega-Lite) und an der nativen Vorlage.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

ROWS = [{"P": "2026-01-05", "I": 33.0, "V": 30.0}, {"P": "2026-01-12", "I": 34.0, "V": 31.0},
        {"P": "2026-01-19", "I": 35.0, "V": 31.5}]


def _lines(profile: str, roles: dict) -> list[dict]:
    """Je gezeichneter Linienmarke: Farbe, Deckkraft, Strichelung."""
    vlc = pytest.importorskip("vl_convert")
    spec = json.loads(render.render_target("line", "html_vegalite", profile, bindings=roles)[0])
    spec["data"] = {"values": ROWS}
    out: list[dict] = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("role") == "mark" and n.get("marktype") == "line" and n.get("items"):
                it = n["items"][0]
                out.append({"stroke": it.get("stroke"), "opacity": it.get("opacity", 1),
                            "dashed": bool(it.get("strokeDash"))})
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    return out


def test_vorjahr_ist_eine_datenrolle_von_line():
    slots = render.load_entry("line")["data_slots"]
    assert slots["py_field"] == {"role": "prior", "required": False}
    assert render.bind("line", {"time": "P", "value": "I", "prior": "V"})["py_field"] == "V"


@pytest.mark.parametrize("profile", ["house_default", "ibcs", "story"])
def test_vorjahr_gebunden_ist_eine_linie_mehr_ungebunden_keine(profile):
    mit = _lines(profile, {"time": "P", "value": "I", "prior": "V"})
    ohne = _lines(profile, {"time": "P", "value": "I"})
    assert len(mit) == len(ohne) + 1, (mit, ohne)
    neu = [m for m in mit if m not in ohne] or mit[:1]
    assert not any(m["dashed"] for m in neu), "PY ist durchgezogen; gestrichelt ist Plan oder FC"


def test_vorjahr_unter_ibcs_ist_das_ist_mit_halber_deckkraft():
    tok = render.profile_def("ibcs")["tokens"]
    mit = _lines("ibcs", {"time": "P", "value": "I", "prior": "V"})
    py = [m for m in mit if m["opacity"] < 1]
    assert len(py) == 1, mit
    assert py[0]["stroke"].upper() == tok["ac"].upper() and py[0]["opacity"] == tok["py_tint_alpha"]


def test_vorjahr_traegt_eine_direkte_beschriftung_die_der_aufrufer_setzt():
    spec = render.render_target("line", "html_vegalite", "house_default",
                                bindings={"time": "P", "value": "I", "prior": "V"}, params={"label_py": "VJ"})[0]
    assert '"text": "VJ"' in spec
    ohne = render.render_target("line", "html_vegalite", "house_default", bindings={"time": "P", "value": "I"})[0]
    assert '"PY"' not in ohne and '"VJ"' not in ohne, "ungebunden keine Beschriftung"


# --- native Spur: FC und PY je Serie per Selektor (BO-116, BO-052) ------------------------------

def _native_ibcs() -> dict:
    return json.loads(render.render("line", "powerbi_native", "ibcs")[0])


def test_native_ibcs_bindet_ist_plan_prognose_vorjahr():
    p = render.load_entry("line")["canonical_params"]
    refs = [x["queryRef"] for x in _native_ibcs()["query"]["queryState"]["Y"]["projections"]]
    e = p["entity"]
    assert refs == [f"{e}.{p['measure']}", f"{e}.{p['target_measure']}", f"{e}.{p['fc_measure']}",
                    f"{e}.{p['prior_measure']}"]


def test_native_ibcs_linienstil_je_serie_fc_gestrichelt():
    v = _native_ibcs()
    refs = {x["queryRef"] for x in v["query"]["queryState"]["Y"]["projections"]}
    styles = {s["selector"]["metadata"]: s["properties"] for s in v["objects"]["lineStyles"]}
    assert set(styles) == refs, "jede Serie hat ihren Stil, kein Selektor zeigt ins Leere"
    colors = {s["selector"]["metadata"]: s["properties"]["fill"] for s in v["objects"]["dataPoint"]}
    assert set(colors) == refs
    p = render.load_entry("line")["canonical_params"]

    def lit(props, key):
        return props[key]["expr"]["Literal"]["Value"]

    fc = styles[f"{p['entity']}.{p['fc_measure']}"]
    assert lit(fc, "lineStyle") == "'dashed'", "FC gestrichelt (IBCS UN 3.2)"
    others = [k for k in styles if not k.endswith(p["fc_measure"])]
    assert all(lit(styles[k], "lineStyle") == "'solid'" for k in others), "nur FC gestrichelt"
    py = styles[f"{p['entity']}.{p['prior_measure']}"]
    assert lit(py, "strokeTransparency") == "50D", "PY = AC mit 50 % (py_tint_alpha)"
