"""Profil story (D-623 in Freelancing, BO-001): Datenmarken grau, nur die Treffer der Kernaussage im Akzent.

Gemessen am Vega-Szenengraph (vl-convert). Gegenprobe: dieselbe Spec unter house_default trägt die
Bewertungsfarben, und ohne eingeschaltete Kernaussage ist keine Marke im Akzent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

ROWS = [{"Region": r, "Wert": v} for r, v in (("DACH", 24.4), ("Benelux", 27.8), ("Nordics", 31.4))]
ROLES = {"category": "Region", "value": "Wert"}
ACCENT, GREY = "#0E7C8C", "#8A8A8A"


def _fills(profile: str, params: dict, on: bool | None = None) -> dict:
    vlc = pytest.importorskip("vl_convert")
    spec = json.loads(render.render_target("bar_ranking", "html_vegalite", profile, bindings=ROLES, params=params)[0])
    spec["data"] = {"values": ROWS}
    spec["width"], spec["height"] = 300, 200
    if on is not None:
        spec["params"] = [{**p, "value": on} if p["name"] == render.KEY_PARAM else p for p in spec["params"]]
    out: dict = {"rect": [], "text": []}

    def walk(node):
        if isinstance(node, dict):
            if node.get("role") == "mark" and node.get("marktype") in ("rect", "text"):
                out[node["marktype"]] += [str(it.get("fill", "")).upper() for it in node.get("items", [])
                                          if node["marktype"] == "text" or it.get("width", 0) > 0]
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    return out


def test_story_zeichnet_alle_datenmarken_grau():
    f = _fills("story", {"focus_grey": GREY})
    assert f["rect"] and set(f["rect"]) == {GREY}, f["rect"]
    # Gegenprobe: unter house_default trägt die Bewertung Farbe
    assert set(_fills("house_default", {})["rect"]) != {GREY}


def test_kernaussage_faerbt_nur_die_treffer_im_akzent():
    params = {"focus_grey": GREY, "accent": ACCENT, "highlight": {"field": "Region", "values": ["DACH"]}}
    an = _fills("story", params, on=True)
    assert sorted(an["rect"]) == sorted([ACCENT, GREY, GREY]), an["rect"]
    assert ACCENT not in an["text"], "Beschriftung trägt Textfarbe, nie den Akzent"
    aus = _fills("story", params, on=False)
    assert ACCENT not in aus["rect"], "ohne eingeschaltete Kernaussage kein Akzent"


def test_akzent_nur_unter_focus_profil():
    """Unter IBCS bleibt die Hervorhebung das Dämpfen; ein mitgegebener Akzent ändert nichts."""
    params = {"accent": ACCENT, "highlight": {"field": "Region", "values": ["DACH"]}}
    spec = render.render_target("bar_ranking", "fabric_app", "ibcs", bindings=ROLES, params=params)[0]
    assert ACCENT not in spec and str(render.KEY_DIM) in spec


def test_linien_bleiben_grau_nur_der_punkt_der_periode_im_akzent():
    vlc = pytest.importorskip("vl_convert")
    roles = {"time": "Periode", "value": "Ist", "plan": "Plan"}
    rows = [{"Periode": p, "Ist": a, "Plan": 45.0} for p, a in (("2025-12-22", 33.5), ("2025-12-29", 33.9),
                                                                  ("2026-01-05", 33.6))]
    params = {"focus_grey": GREY, "accent": ACCENT,
              "highlight": {"field": "Periode", "values": ["2026-01-05"], "temporal": True}}
    spec = json.loads(render.render_target("line", "html_vegalite", "story", bindings=roles, params=params)[0])
    spec["data"] = {"values": rows}
    spec["params"] = [{**p, "value": True} if p["name"] == render.KEY_PARAM else p for p in spec["params"]]
    hits: list = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("role") == "mark":
                hits.extend((n.get("marktype"), round(it.get("x", 0))) for it in n.get("items", [])
                            if ACCENT.lower() in (str(it.get("fill", "")).lower(), str(it.get("stroke", "")).lower()))
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    assert hits and {m for m, _ in hits} == {"symbol"}, hits
    assert len({x for _, x in hits}) == 1, "nur die eine Periode"
