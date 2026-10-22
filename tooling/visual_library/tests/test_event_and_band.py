"""Datenrollen event (Ereignismarker) und fc_band (Prognoseband P10-P90) im Idiom line (2.1.0, 22.10.2026).

Meridian BO-401 und BO-402 (Entscheidung Florian 22.10.2026): Ereignisse aus einer governten Tabelle erscheinen als
senkrechte Regel mit Text (Gestaltungsregel ereignismarker), die Unsicherheit der Prognose als statisches Band mit
beschrifteten Perzentilen (Regel prognoseband). Gemessen wird am Vega-Szenengraphen (vl_convert): gebunden gibt es
die Marken, ungebunden oder mit leerer Spalte keine (Gegenprobe; ohne Ereignis keine Scheinkausalität).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import gestaltung  # noqa: E402
import render  # noqa: E402

PROFILES = ["house_default", "print_safe", "ibcs"]
BASIS = {"time": "P", "value": "I", "forecast": "F"}
ROWS = [
    {"P": "2026-01-05", "I": 30.0, "F": None, "L": None, "H": None, "E": None},
    {"P": "2026-01-12", "I": 31.0, "F": None, "L": None, "H": None, "E": "Preisaktion Nord"},
    {"P": "2026-01-19", "I": 32.0, "F": 32.0, "L": 32.0, "H": 32.0, "E": None},
    {"P": "2026-01-26", "I": None, "F": 33.0, "L": 30.5, "H": 35.5, "E": None},
    {"P": "2026-02-02", "I": None, "F": 34.0, "L": 30.0, "H": 38.0, "E": None},
]


def _spec(profile: str, roles: dict, rows: list | None = None) -> dict:
    spec = json.loads(render.render_target("line", "html_vegalite", profile, bindings=roles)[0])
    spec["data"] = {"values": rows if rows is not None else ROWS}
    return spec


def _marks(spec: dict) -> list[dict]:
    vlc = pytest.importorskip("vl_convert")
    out: list[dict] = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("role") == "mark":
                out.append(n)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    return out


def _items(spec: dict, marktype: str) -> list[dict]:
    return [it for m in _marks(spec) if m.get("marktype") == marktype for it in m.get("items", [])]


def _texts(spec: dict) -> list[str]:
    return [str(it.get("text")) for it in _items(spec, "text")]


def test_slots_declare_event_and_band_with_parts():
    slots = render.data_slots("line")
    assert slots["event_field"] == {"role": "event", "required": False}
    assert slots["fc_lo_field"] == {"role": "fc_band", "part": "lo", "required": False}
    assert slots["fc_hi_field"] == {"role": "fc_band", "part": "hi", "required": False}
    assert render.SLOT_PARTS["fc_band"] == ("lo", "hi")


def test_bind_takes_the_band_as_parts():
    got = render.bind("line", {**BASIS, "fc_band": {"lo": "L", "hi": "H"}, "event": "E"})
    assert (got["fc_lo_field"], got["fc_hi_field"], got["event_field"]) == ("L", "H", "E")
    with pytest.raises(ValueError):
        render.bind("line", {**BASIS, "fc_band": "L"})
    # ein fehlender Teil ist ungebunden, nicht der Name der anderen Spalte
    assert "fc_hi_field" not in render.bind("line", {**BASIS, "fc_band": {"lo": "L"}})


@pytest.mark.parametrize("profile", PROFILES)
def test_event_is_a_rule_with_its_text(profile):
    mit = _spec(profile, {**BASIS, "event": "E"})
    ohne = _spec(profile, BASIS)
    regel = gestaltung.regel("ereignismarker")
    def senkrecht(spec: dict) -> list[dict]:   # sichtbar, volle Höhe, ohne x2 (die Hover-Regel hat Deckkraft 0)
        return [it for it in _items(spec, "rule") if str(it.get("stroke", "")).lower() == regel["farbe"].lower()
                and it.get("strokeWidth") == regel["strich_px"] and it.get("x2") is None and it.get("y") == 0
                and it.get("opacity") != 0]
    assert len(senkrecht(mit)) == 1 and not senkrecht(ohne), (senkrecht(mit), senkrecht(ohne))
    assert senkrecht(mit)[0]["x"] > 0      # an der zweiten Woche, nicht am Rand
    assert "Preisaktion Nord" in _texts(mit)
    assert "Preisaktion Nord" not in _texts(ohne)
    marke = next(it for it in _items(mit, "text") if it.get("text") == "Preisaktion Nord")
    assert marke["fontSize"] == regel["text_px"]


@pytest.mark.parametrize("profile", PROFILES)
def test_empty_event_column_draws_no_marker(profile):
    """Ohne Tabelle oder mit leerer Tabelle: keine Marke (keine Scheinkausalität)."""
    leer = [{**r, "E": None} for r in ROWS]
    leer[1]["E"] = ""
    spec = _spec(profile, {**BASIS, "event": "E"}, leer)
    ohne = _spec(profile, BASIS, leer)
    assert len(_items(spec, "rule")) == len(_items(ohne, "rule"))
    assert len(_texts(spec)) == len(_texts(ohne))


@pytest.mark.parametrize("profile", PROFILES)
def test_unbound_roles_leave_no_layer(profile):
    dump = json.dumps(_spec(profile, BASIS))
    for sample in ("gm_event", "gm_fc_p10", "gm_fc_p90", "Prognoseband"):
        assert sample not in dump, sample


@pytest.mark.parametrize("profile", PROFILES)
def test_band_is_a_static_area_with_labelled_percentiles(profile):
    regel = gestaltung.regel("prognoseband")
    mit = _spec(profile, {**BASIS, "fc_band": {"lo": "L", "hi": "H"}})
    ohne = _spec(profile, BASIS)
    flaechen = [m for m in _marks(mit) if m.get("marktype") == "area"]
    assert len(flaechen) == len([m for m in _marks(ohne) if m.get("marktype") == "area"]) + 1
    band = flaechen[-1]["items"][0]
    assert band["opacity"] == regel["deckkraft"]
    assert not band.get("stroke"), "Band ohne Kontur"
    texte = _texts(mit)
    for label in regel["beschriftung"]:
        assert texte.count(label) == 1, (label, texte)
    assert "transition" not in json.dumps(mit), "statisch, keine Animation (BO-300)"


def test_band_is_inside_the_value_axis():
    """Haus: die Achse umfasst das Band (P90 38 über dem höchsten Ist 32), sonst schnitte die Fläche ab."""
    spec = _spec("house_default", {**BASIS, "fc_band": {"lo": "L", "hi": "H"}})
    calc = {t["as"]: t["calculate"] for t in spec["transform"] if "calculate" in t}
    assert "datum['H']" in calc["_yo_z"] and "datum['L']" in calc["_yu_z"]
    ys = [it["y"] for it in _items(spec, "text") if it.get("text") == "P90"]
    assert ys and ys[0] >= 0, ys


def test_tooltip_lists_band_and_event():
    spec = json.loads(render.render_target("line", "html_vegalite", "house_default",
                                           bindings={**BASIS, "fc_band": {"lo": "L", "hi": "H"}, "event": "E"})[0])
    felder = [f["field"] for f in spec["layer"][-1]["encoding"].get("tooltip") or []] or \
        [f["field"] for lay in spec["layer"] for f in (lay.get("encoding") or {}).get("tooltip") or []]
    assert {"L", "H", "E"} <= set(felder), felder
