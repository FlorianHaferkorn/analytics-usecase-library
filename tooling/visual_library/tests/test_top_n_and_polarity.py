"""Top N with a rest row and the polarity of the measure, measured on the rendered chart (A-31 R7).

Sources (research corpus): market-009/market-027 Top N + "Others" as one aggregated row; BC-CHART-10
(the idiom's `top_n` limit); market-028 cost KPIs flip the variance colour. Before R7 the Cockpit cut
breakdowns to `max_items` without a trace, and `bar_ranking` coloured "below target" red even for a
lower-is-better measure such as the cash conversion cycle (Aurora KPI-FIN-006).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

VALUES = [12, 30, 7, 22, 15, 9, 40, 5]
ROWS = [{"Region": f"R{i}", "Wert": v} for i, v in enumerate(VALUES)]
COLS = {"category": "Region", "value": "Wert"}


def _scene(idiom: str, pid: str, params: dict, rows: list[dict] = ROWS) -> dict:
    """Axis labels (top to bottom), data labels and bars (y, width, fill) from Vega's scenegraph."""
    vlc = pytest.importorskip("vl_convert")
    spec = json.loads(render.render_target(idiom, "html_vegalite", pid, bindings=COLS, params=params)[0])
    spec["data"] = {"values": rows}
    spec["width"], spec["height"] = 300, 200
    out: dict = {"axis": [], "labels": [], "bars": []}

    def walk(node):
        if isinstance(node, dict):
            if node.get("marktype") == "text":
                for it in node.get("items", []):
                    if node.get("role") == "axis-label":
                        out["axis"].append((it.get("y", 0), it.get("text")))
                    elif node.get("role") == "mark" and it.get("text") not in (None, ""):
                        out["labels"].append(it.get("text"))
            if node.get("marktype") == "rect" and node.get("role") == "mark":
                out["bars"] += [(it.get("y", 0), it.get("width", 0), it.get("fill")) for it in node.get("items", [])
                                if it.get("width", 0) > 0]
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    out["categories"] = [t for _, t in sorted(out["axis"]) if not str(t).replace(".", "").isdigit()]
    return out


def test_rest_without_sum_names_the_folded_rows_and_draws_no_value():
    s = _scene("bar_ranking", "house_default", {"top_n": 5, "rest": "none"})
    assert s["categories"] == ["R7", "R2", "R5", "R0", "R4", "Übrige (3)"], "worst five first, rest last"
    assert len(s["bars"]) == 5, "the rest of a rate has no bar: its sum would be a wrong number"
    assert sorted(s["labels"], key=float) == ["5", "7", "9", "12", "15"]


def test_rest_with_sum_is_one_bar_last_and_neutral():
    s = _scene("bar_ranking", "house_default", {"top_n": 5, "rest": "sum", "target_val": 15})
    assert s["categories"][-1] == "Übrige (3)"
    assert "92" in s["labels"], "30 + 22 + 40 folded into the rest"
    rest = max(s["bars"])                       # lowest on the chart = last row
    assert rest[2] == "#94A0AC", "a rest is not rated against the per-item target"
    assert len(s["bars"]) == 6


def test_no_rest_row_when_everything_fits():
    s = _scene("bar_ranking", "house_default", {"top_n": 20})
    assert not any(str(c).startswith("Übrige") for c in s["categories"])
    assert len(s["bars"]) == len(VALUES)


def test_bound_data_gets_the_declared_limit_by_default():
    rows = [{"Region": f"K{i:02d}", "Wert": i + 1} for i in range(25)]
    s = _scene("bar_absolute", "house_default", {}, rows)
    assert len(s["categories"]) == 21 and s["categories"][-1] == "Übrige (5)", "top_n default 20 (BC-CHART-10)"


def test_lower_is_better_ranks_the_highest_first_and_colours_above_target():
    s = _scene("bar_ranking", "house_default", {"top_n": 5, "polarity": -1, "target_val": 15})
    assert s["categories"][:5] == ["R6", "R1", "R3", "R4", "R0"], "worst first = highest first"
    red = sorted(w for _, w, f in s["bars"] if f == "#A4262C")
    ink = sorted(w for _, w, f in s["bars"] if f == "#0F2430")
    assert len(red) == 3 and len(ink) == 2, "40, 30, 22 are above 15 and therefore bad"
    assert min(red) > max(ink)


def test_higher_is_better_stays_as_before():
    s = _scene("bar_ranking", "house_default", {"top_n": 8, "target_val": 15})
    assert s["categories"][0] == "R7", "lowest first"
    assert sum(1 for *_, f in s["bars"] if f == "#A4262C") == 4, "12, 7, 9, 5 below 15"


def test_canonical_sample_is_not_folded():
    spec = json.loads(render.render_target("bar_ranking", "fabric_app", "house_default")[0])["spec"]
    assert "_rank" not in json.dumps(spec), "goldens show the frozen sample, untouched"


def test_unknown_rest_mode_fails_loudly():
    with pytest.raises(ValueError):
        render.render_target("bar_ranking", "fabric_app", "house_default", bindings=COLS,
                             params={"rest": "average"})
