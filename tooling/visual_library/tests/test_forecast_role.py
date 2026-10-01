"""Datenrolle Prognose (FC, IBCS UN 3.2; BO-021 in Freelancing, 01.10.2026).

Vorher fehlte die Rolle: das Cockpit zeigte „Ist und Prognose“ nur mit dem Ist, denn die Prognose als Plan
zu zeichnen hieße, sie falsch zu benennen. Gemessen am Szenengraph: gebunden gibt es eine gestrichelte
Linie mehr, ungebunden entfällt sie (Gegenprobe), und sie ist nie die Plan-Linie.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

ROWS = [{"P": "2026-01-05", "I": 33.0, "F": None}, {"P": "2026-01-12", "I": None, "F": 34.0},
        {"P": "2026-01-19", "I": None, "F": 35.0}]


def _dashed_lines(profile: str, roles: dict) -> list:
    vlc = pytest.importorskip("vl_convert")
    spec = json.loads(render.render_target("line", "html_vegalite", profile, bindings=roles)[0])
    spec["data"] = {"values": ROWS}
    out: list = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("role") == "mark" and n.get("marktype") == "line" and any(it.get("strokeDash") for it in n.get("items", [])):
                out.append(n.get("name"))   # eine gestrichelte Linie je Linienmarke, nicht je Punkt
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    return out


@pytest.mark.parametrize("profile", ["house_default", "ibcs"])
def test_prognose_gebunden_ist_eine_gestrichelte_linie(profile):
    mit = _dashed_lines(profile, {"time": "P", "value": "I", "forecast": "F"})
    ohne = _dashed_lines(profile, {"time": "P", "value": "I"})
    assert len(mit) == len(ohne) + 1, (mit, ohne)


def test_prognose_ist_nicht_die_planlinie():
    entry = render.load_entry("line")
    assert entry["data_slots"]["fc_field"]["role"] == "forecast"
    assert entry["data_slots"]["plan_field"]["role"] == "plan"


def test_letzter_istwert_bleibt_beschriftet_wenn_die_prognose_weiterlaeuft():
    """Cockpit 01.10.2026: mit Prognosewochen ohne Ist zählte die Beschriftung über alle Zeilen und fand den
    letzten Istwert nicht mehr (33,6 in KW 01 fehlte)."""
    vlc = pytest.importorskip("vl_convert")
    rows = [{"P": "2025-12-22", "I": 33.5, "F": None}, {"P": "2025-12-29", "I": 33.6, "F": 33.6},
            {"P": "2026-01-05", "I": None, "F": 35.0}]
    spec = json.loads(render.render_target("line", "html_vegalite", "ibcs",
                                           bindings={"time": "P", "value": "I", "forecast": "F"})[0])
    spec["data"] = {"values": rows}
    texts: list = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("role") == "mark" and n.get("marktype") == "text":
                texts.extend(str(it.get("text")) for it in n.get("items", []))
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    assert any(t.replace(",", ".") == "33.6" for t in texts), texts
