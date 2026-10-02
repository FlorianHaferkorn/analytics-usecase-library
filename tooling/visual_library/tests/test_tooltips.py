"""Tooltips and locale of the derived targets (A-31 R6, 30.09.2026).

Before: no idiom declared a tooltip; Fabric's VegaVisual filled in raw field names, an English
date ("Dec 30, 2024") and unformatted numbers ("27.95"), the HTML target showed none. Now every data
mark carries a tooltip built from the bound columns, formatted like the data labels, and the
profile config carries the de-DE locale. Observable Plot: tooltip = detail on demand, it
complements the direct labels (editorial corpus)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

DATA_MARKS = render._TOOLTIP_MARKS


def _vega_idioms() -> list[str]:
    impl = yaml.safe_load((render.LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]
    return [i for i in impl if "deneb_vegalite" in render.tools(i)]


def _layers(spec: dict):
    yield spec
    for lay in spec.get("layer", []):
        yield from _layers(lay)
    if isinstance(spec.get("spec"), dict):
        yield from _layers(spec["spec"])
    for key in ("vconcat", "hconcat", "concat"):
        for part in spec.get(key, []):
            yield from _layers(part)


def _mark(node: dict):
    m = node.get("mark")
    return m if isinstance(m, str) else (m or {}).get("type")


def test_every_data_mark_has_a_tooltip_of_bound_columns():
    for idiom in _vega_idioms():
        cols = {s["role"]: f"col_{s['role']}" for s in render.data_slots(idiom).values()}
        for pid in render.target_profiles(idiom):
            spec = json.loads(render.render_target(idiom, "fabric_app", pid, bindings=cols)[0])["spec"]
            marks = [n for n in _layers(spec) if _mark(n) in DATA_MARKS | {"boxplot"}]
            assert marks, f"{idiom}@{pid}: no data mark"
            for node in marks:
                tip = node.get("encoding", {}).get("tooltip")
                mark_tip = node["mark"].get("tooltip") if isinstance(node["mark"], dict) else None
                assert tip or mark_tip, f"{idiom}@{pid}: {_mark(node)} without tooltip"
                if mark_tip:
                    continue      # summarised rows (bin/aggregate): the encoded values are shown
                assert {t["field"] for t in tip} <= set(cols.values()), f"{idiom}@{pid}: tooltip reads a sample column"
                for t in tip:
                    if t["type"] == "quantitative":
                        assert t.get("format"), f"{idiom}@{pid}: unformatted {t['field']}"


def test_tooltip_lists_dimension_before_measure_and_keeps_the_label_format():
    spec = json.loads(render.render_target("variance_pin", "fabric_app", "ibcs",
                                           bindings={"time": "Monat", "variance": "Abweichung"})[0])["spec"]
    tip = next(n["encoding"]["tooltip"] for n in _layers(spec) if _mark(n) == "bar")
    assert [t["field"] for t in tip] == ["Monat", "Abweichung"]
    assert tip[0]["format"] == "%m/%Y" and "%" in tip[1]["format"]


def test_numbers_and_dates_render_in_german():
    vlc = pytest.importorskip("vl_convert")
    spec = json.loads(render.render_target("bar_absolute", "html_vegalite", "house_default",
                                           bindings={"category": "Region", "value": "Umsatz"})[0])
    spec["data"] = {"values": [{"Region": "Nord", "Umsatz": 1240.5}, {"Region": "Süd", "Umsatz": 980}]}
    svg = vlc.vegalite_to_svg(spec)
    assert re.search(r">1\.240,5<", svg), "data label not in de-DE format"
    for pid in render.all_profiles():
        assert render.vegalite_config(pid)["locale"]["number"]["decimal"] == ",", pid


def test_line_hover_follows_the_nearest_date_and_shows_actual_and_plan():
    """Power BI shows all series of the hovered date; the line carries a nearest-date hover whose
    tooltip lists period, actual and plan (no host crosshair on top: capability disabled)."""
    for pid in ("house_default", "fluent", "editorial"):
        doc = json.loads(render.render_target("line", "fabric_app", pid,
                                              bindings={"time": "Monat", "value": "Ist", "plan": "Plan"})[0])
        hover = [n for n in _layers(doc["spec"]) if n.get("params")]
        assert hover and hover[0]["params"][0]["select"].get("nearest") is True, pid
        assert [t["field"] for t in hover[0]["encoding"]["tooltip"]] == ["Monat", "Ist", "Plan"], pid
        assert doc["capabilities"].get("disableLineChartCrosshairTooltip") is True, pid


def test_labels_carry_no_tooltip():
    for idiom in ("bar_ranking", "waterfall_pvm", "line"):
        spec = json.loads(render.render_target(idiom, "fabric_app", "house_default")[0])["spec"]
        for node in _layers(spec):
            if _mark(node) == "text":
                assert node["mark"].get("tooltip", "missing") is None, idiom
