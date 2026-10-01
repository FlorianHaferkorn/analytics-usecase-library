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
    value_axes = [a for a in vega.get("axes", []) if a.get("orient") in ("left", "right") and a.get("labels", True)
                  and a.get("aria") is not False and a.get("scale") == "y"]
    assert not value_axes, "IBCS: value axis next to data labels (SI 3.1)"


def test_ranking_stays_sorted_by_value_with_a_label_layer():
    """Measured 30.09.2026: a second layer made `sort: "x"` ambiguous and Vega fell back to A-Z."""
    rows = [{"Region": c, "Umsatz": v} for c, v in zip(CATS, [1240, 1105, 980, 890, 760])]
    for pid in ("house_default", "ibcs"):
        bars = _bars("bar_ranking", pid, {"category": "Region", "value": "Umsatz"}, rows)
        ac = sorted((b for b in bars), key=lambda b: b[1])        # top to bottom
        widths = [b[2] for b in ac if b[2] > 0]
        order = widths[:5] if pid == "house_default" else widths[1::2][:5]
        assert order == sorted(order) or order == sorted(order, reverse=True), f"{pid}: not sorted {order}"


def test_ibcs_bar_label_sits_right_of_the_longer_of_ac_and_py():
    """UN 2.3: a label must not sit on the PY bar where PY is longer than AC."""
    rows = [{"Region": "Ost", "Umsatz": 760, "Vorjahr": 820}, {"Region": "Nord", "Umsatz": 1240, "Vorjahr": 1180}]
    spec = _spec("bar_ranking", "ibcs", {"category": "Region", "value": "Umsatz", "prior": "Vorjahr"}, rows)
    assert any(t.get("as") == "_lx" for t in spec.get("transform", []))
    no_py = _spec("bar_ranking", "ibcs", {"category": "Region", "value": "Umsatz"}, rows)
    texts = [lay for lay in no_py["layer"] if (lay.get("mark") or {}).get("type") == "text"]
    assert texts, "without PY the value labels must stay"
    assert "null" in json.dumps(no_py.get("transform", [])), "missing PY must read as null in the expression"


def test_house_pins_are_labelled():
    spec = json.loads(render.render_target("variance_pin", "fabric_app", "house_default")[0])["spec"]
    assert any((lay.get("mark") or {}).get("type") == "text" for lay in spec["layer"])


def test_no_profile_lets_the_host_shorten_data_labels():
    """Text marks are values. VegaVisual's default shortened "74,4" at the plot edge to "…"
    (Cockpit, 01.10.2026) — the number was gone. Every profile switches that off (A-31 R7)."""
    for pid in render.all_profiles():
        doc = json.loads(render.render_target("bar_ranking", "fabric_app", pid)[0]) \
            if pid in render.target_profiles("bar_ranking") or render.profile_def(pid).get("kind") == "style" \
            else None
        if doc is None:
            continue
        assert doc["capabilities"].get("disableTextTruncation") is True, pid


def _ibcs_line_texts(vals: list[float], width: int = 300) -> list[tuple[str, float, float]]:
    """(label, x, y) of the IBCS line's data labels from Vega's scenegraph at a given width."""
    vlc = pytest.importorskip("vl_convert")
    rows = [{"Monat": f"2026-{i // 28 + 1:02d}-{i % 28 + 1:02d}", "Wert": v} for i, v in enumerate(vals)]
    spec = _spec("line", "ibcs", {"time": "Monat", "value": "Wert"}, rows)
    spec["width"] = width
    out: list[tuple[str, float, float]] = []

    def walk(node, ox=0.0, oy=0.0):
        if isinstance(node, dict):
            if node.get("marktype") == "text" and node.get("role") == "mark":
                out.extend((it["text"], ox + it.get("x", 0), oy + it.get("y", 0)) for it in node.get("items", [])
                           if it.get("text") not in (None, ""))
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

    walk(vlc.vegalite_to_scenegraph(spec).get("scenegraph"))
    return out


def _ibcs_line_labels(vals: list[float], width: int = 300) -> list[str]:
    return [t for t, _, _ in _ibcs_line_texts(vals, width)]


def _overlaps(texts: list[tuple[str, float, float]]) -> list[tuple[str, str]]:
    """Centred labels, 11 px font: about 6.2 px per character wide, 12 px high (G14 in Freelancing
    measures the same on the rendered page)."""
    hits = []
    for a in range(len(texts)):
        for b in range(a + 1, len(texts)):
            (ta, xa, ya), (tb, xb, yb) = texts[a], texts[b]
            if abs(xa - xb) < 3.1 * (len(ta) + len(tb)) and abs(ya - yb) < 12:
                hits.append((ta, tb))
    return hits


# Diagnosis series of the Aurora cockpit (01.10.2026): near-flat on a zero-based IBCS axis, where
# extrema sit next to the first point or each other — G14 found their labels on top of each other.
COCKPIT_SERIES = {
    "COM-001": [28.0, 28.24, 28.1, 27.95, 28.05, 27.85] + [28.0 + 0.01 * (i % 5) for i in range(14)] + [27.95],
    "FIN-001": [38.28, 38.2, 38.33, 38.13] + [38.2 + 0.01 * (i % 4) for i in range(16)] + [38.3],
    "OPS-002": [75.84, 75.9, 76.0, 76.1, 76.2, 76.3, 76.53, 75.66] + [76.0 + 0.02 * (i % 5) for i in range(12)] + [76.08],
}


@pytest.mark.parametrize("width", [300, 900])
@pytest.mark.parametrize("name", sorted(COCKPIT_SERIES))
def test_ibcs_line_labels_never_cover_each_other(name, width):
    texts = _ibcs_line_texts(COCKPIT_SERIES[name], width)
    assert len(texts) >= 2, f"first and last always labelled: {texts}"
    assert not _overlaps(texts), f"{name} @ {width}px: {_overlaps(texts)}"


def test_ibcs_line_labels_a_tied_extremum_once():
    """Cockpit 01.10.2026 (ESG-002): a flat tail at the maximum put 31 identical labels on top of
    each other — every tied point was 'the' extremum. Only its first occurrence is labelled."""
    vals = [10.0, 12.0, 11.0, 13.0, 14.1, 14.1, 14.1, 14.1, 14.1, 14.1, 13.5, 12.8]
    labels = _ibcs_line_labels(vals)
    assert labels.count("14,1") == 1, labels
    assert len(labels) == 3, f"first, max, last: {labels}"


def test_ibcs_line_keeps_extrema_that_stand_apart():
    """The rule drops only what would collide: a clear peak in the middle stays labelled."""
    vals = [28.2, 28.0, 31.0, 33.0, 35.0, 36.0, 34.0, 40.0, 37.0, 36.0]
    labels = _ibcs_line_labels(vals, 600)
    assert "28,2" in labels and "40" in labels and "36" in labels, labels
