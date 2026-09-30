"""Bar geometry and data labels, measured on the rendered SVG (A-31 R6, 30.09.2026).

Sources (research corpus): IBCS UN 3.1 (ibcs2-un-3-1) bar/column = 2/3 of the category, gap 1/3;
Urban Institute "bar about twice the gap", data labels 11 px, label columns only below 10;
IBCS SI 3.1 data labels instead of a value axis, SI 5.3 label only first/last/extrema when many
points, UN 2.3 labels horizontal, positive above/right, negative below/left.
Measured before the fix: Vega-Lite's default drew bars at 0.90 of the category in four profiles,
axis labels were 10 px next to 11 px data labels, and only the IBCS profile labelled values."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

CATS = ["Nord", "West", "Süd", "Mitte", "Ost"]


def _spec(idiom: str, pid: str, cols: dict, rows: list[dict]) -> dict:
    spec = json.loads(render.render_target(idiom, "html_vegalite", pid, bindings=cols)[0])
    spec["data"] = {"values": rows}
    spec["width"], spec["height"] = 300, 200
    return spec


def _svg(idiom: str, pid: str, cols: dict, rows: list[dict]) -> str:
    vlc = pytest.importorskip("vl_convert")
    return vlc.vegalite_to_svg(_spec(idiom, pid, cols, rows))


def _bars(idiom: str, pid: str, cols: dict, rows: list[dict]) -> list[tuple[float, float, float, float]]:
    """Every drawn bar (rect item of a bar mark) as (x, y, w, h) in chart coordinates, from Vega's
    scenegraph — robust to rounded ends, which Vega-Lite draws as clipped groups."""
    vlc = pytest.importorskip("vl_convert")
    sg = vlc.vegalite_to_scenegraph(_spec(idiom, pid, cols, rows))
    out: list[tuple[float, float, float, float]] = []

    def walk(node, ox=0.0, oy=0.0):
        if isinstance(node, dict):
            if node.get("marktype") == "rect" and node.get("role") == "mark":
                for it in node.get("items", []):
                    if it.get("width", 0) > 0 and it.get("height", 0) > 0:
                        out.append((ox + it.get("x", 0), oy + it.get("y", 0), it["width"], it["height"]))
                return
            if node.get("marktype") == "group":
                for it in node.get("items", []):
                    walk({"_g": it.get("items", [])}, ox + it.get("x", 0), oy + it.get("y", 0))
                return
            for v in node.values():
                walk(v, ox, oy)
        elif isinstance(node, list):
            for v in node:
                walk(v, ox, oy)

    walk(sg.get("scenegraph", sg))
    return out


@pytest.mark.parametrize("pid", ["house_default", "print_safe", "fluent", "editorial", "minimal"])
def test_columns_and_bars_take_two_thirds_of_the_category(pid):
    cases = [("bar_absolute", {"category": "Region", "value": "Umsatz"}, "y"),
             ("column_time", {"time": "Monat", "value": "Umsatz"}, "x")]
    for idiom, cols, axis in cases:
        if pid not in render.target_profiles(idiom):
            continue
        rows = ([{"Region": c, "Umsatz": v} for c, v in zip(CATS, [1240, 1105, 980, 890, 760])] if axis == "y"
                else [{"Monat": f"2026-0{i + 1}", "Umsatz": v} for i, v in enumerate([12, 15, 11, 14, 13])])
        bars = _bars(idiom, pid, cols, rows)
        assert len(bars) == 5, f"{idiom}@{pid}: {len(bars)} bars"
        if axis == "y":
            pos, size = sorted(b[1] for b in bars), bars[0][3]
        else:
            pos, size = sorted(b[0] for b in bars), bars[0][2]
        step = min(b - a for a, b in zip(pos, pos[1:]))
        assert abs(size / step - 2 / 3) < 0.03, f"{idiom}@{pid}: bar {size / step:.2f} of the category"


def test_every_profile_resolves_the_two_thirds_band():
    for pid in render.all_profiles():
        cfg = render.vegalite_config(pid)
        assert abs(cfg["scale"]["bandPaddingInner"] - 1 / 3) < 0.001, pid


def test_axis_labels_are_never_smaller_than_data_labels():
    for pid in render.all_profiles():
        cfg = render.vegalite_config(pid)
        data_px = cfg.get("text", {}).get("fontSize", 11)
        axis_px = cfg["axis"].get("labelFontSize", 10)
        assert axis_px >= data_px, f"{pid}: axis {axis_px}px < data {data_px}px"


def test_bars_columns_and_waterfalls_label_their_values_below_ten_categories():
    for idiom in ("bar_absolute", "column_time", "bar_ranking",
                  "waterfall_pvm", "waterfall_variance", "waterfall_buildup"):
        spec = json.loads(render.render_target(idiom, "fabric_app", "house_default")[0])["spec"]
        texts = [lay for lay in spec.get("layer", []) if (lay.get("mark") or {}).get("type") == "text"]
        assert texts, f"{idiom}: no data labels"
        assert any("datum._n < 10" in json.dumps(t) for t in texts), f"{idiom}: labels without the <10 rule"
        assert all(t["mark"].get("angle", 0) == 0 for t in texts), f"{idiom}: rotated labels (UN 2.3)"


def test_waterfall_labels_sit_above_positive_and_below_negative_steps():
    svg = _svg("waterfall_pvm", "house_default", {"step": "Treiber", "variance": "Effekt"},
               [{"Treiber": t, "Effekt": e} for t, e in (("Preis", 3.1), ("Menge", -4.6), ("Mix", 1.2))])
    assert "+3,1" in svg or "+3.1" in svg
    assert "−4,6" in svg or "−4.6" in svg


def test_ibcs_line_labels_only_first_last_and_extrema_when_many_points():
    vals = [412, 398, 425, 431, 418, 440, 452, 447, 461]
    rows = [{"Monat": f"2026-0{i + 1}-01", "Umsatz": v} for i, v in enumerate(vals)]
    svg = _svg("line", "ibcs", {"time": "Monat", "value": "Umsatz"}, rows)
    labels = set(re.findall(r'aria-roledescription="text mark"[^>]*>(\d{3})<', svg))
    assert labels == {"412", "398", "461"}, labels    # first, min, last (= max)
    vlc = pytest.importorskip("vl_convert")
    vega = vlc.vegalite_to_vega(_spec("line", "ibcs", {"time": "Monat", "value": "Umsatz"}, rows))
    vega = json.loads(vega) if isinstance(vega, str) else vega
    assert not [a for a in vega.get("axes", []) if a.get("orient") in ("left", "right") and a.get("labels", True)
                and a.get("aria") is not False and a.get("scale") == "y"], "IBCS: value axis next to data labels (SI 3.1)"
