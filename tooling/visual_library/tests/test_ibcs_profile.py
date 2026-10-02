"""The `ibcs` profile against IBCS Standards 2.0 (A-31 R2.4).

Every test names the rule it checks (ids as catalogued in
docs/architecture/research/2026-09-30_visual-stack-r1/ibcs_v2.yaml, taken from the original).
IBCS prescribes relations, not hex values (UN 4.1) — so the tests check relations and the
profile's own tokens, never an invented IBCS colour. What the Vega-Lite spec cannot show
(SAY/STRUCTURE, legibility thresholds) is out of scope here.
"""
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

CATALOG = REPO_ROOT / "docs" / "architecture" / "research" / "2026-09-30_visual-stack-r1" / "ibcs_v2.yaml"
TOK = render.profile_def("ibcs")["tokens"]
RATED = ("deviation_bar", "waterfall_pvm", "waterfall_variance", "variance_pin",
         "multi_tier_column")   # idioms that show variances
BANDED_BARS = ("column_time", "bar_ranking", "waterfall_pvm", "waterfall_variance", "waterfall_buildup",
               "multi_tier_column")
PINNED = ("variance_pin", "multi_tier_column")   # idioms that show relative variances as pins (UN 4.1)
PIN_BAND_MAX = 0.25   # a pin takes at most 1/4 of the absolute bar's band (the original says only "very thin")


def _ibcs_idioms() -> list[str]:
    impl = yaml.safe_load((render.LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]
    return [i for i in impl if "ibcs" in render.target_profiles(i)]


def _app(idiom: str) -> dict:
    return json.loads(render.render_target(idiom, "fabric_app", "ibcs")[0])


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _marks(spec: dict) -> list[dict]:
    return [n["mark"] if isinstance(n["mark"], dict) else {"type": n["mark"]}
            for n in _walk(spec) if "mark" in n]


def _is_pin(mark: dict) -> bool:
    """A pin is a bar whose width is a fraction of the band (UN 4.1: a very thin column)."""
    return mark.get("type") == "bar" and isinstance(mark.get("width"), dict) and "band" in mark["width"]


def _without_tooltips(node):
    if isinstance(node, dict):
        return {k: _without_tooltips(v) for k, v in node.items() if k != "tooltip"}
    if isinstance(node, list):
        return [_without_tooltips(v) for v in node]
    return node


def _svg_bars(idiom: str, rows: list[dict]) -> list[dict]:
    """Render the ibcs fabric_app spec with its own config and return every drawn bar as
    {fields from aria-label, w, h} — the MEASURED geometry, not the spec's intent."""
    vlc = pytest.importorskip("vl_convert")
    app = _app(idiom)
    spec = _without_tooltips(app["spec"])   # aria-labels name the ENCODED fields; tooltips add all columns
    spec["config"] = app["configVegaLite"]
    spec["data"] = {"values": rows}
    if "vconcat" not in spec:
        spec["width"], spec["height"] = 400, 200
    svg = vlc.vegalite_to_svg(spec)
    out = []
    for label, d in re.findall(r'<path aria-label="([^"]*)"[^>]*aria-roledescription="bar" d="([^"]*)"', svg):
        m = re.match(r"M[-\d.e]+,[-\d.e]+h([-\d.e]+)v([-\d.e]+)h", d)
        fields = dict(kv.split(": ", 1) for kv in label.split("; "))
        out.append({**fields, "w": abs(float(m.group(1))), "h": abs(float(m.group(2)))})
    return out


def test_rule_refs_exist_in_the_catalog():
    ids = {e.get("rule_id") for e in yaml.safe_load(CATALOG.read_text(encoding="utf-8"))}
    refs = set(render.profile_def("ibcs").get("rule_refs") or [])
    for idiom in _ibcs_idioms():
        refs |= set(render.load_entry(idiom)["profiles"]["ibcs"].get("rule_refs") or [])
    missing = sorted(r for r in refs if r not in ids)
    assert not missing, f"rule ids not in IBCS 2.0 catalog: {missing}"


def test_ibcs_set_is_complete():
    assert len(_ibcs_idioms()) >= 8


def test_ch_1_1_value_axes_start_at_zero():
    """CH 1.1 — no quantitative scale may switch zero off (indexed data is the only exception
    and no ibcs idiom is indexed)."""
    for idiom in _ibcs_idioms():
        app = _app(idiom)
        assert app["configVegaLite"]["scale"]["zero"] is True
        for n in _walk(app["spec"]):
            if isinstance(n.get("scale"), dict):
                assert n["scale"].get("zero", True) is not False, f"{idiom}: truncated axis (CH 1.1)"


def test_si_2_1_no_frames_shadows_or_rounded_data():
    """SI 2.1 / SI 2.2 — no frame around the plot, no rounded data ends."""
    for idiom in _ibcs_idioms():
        app = _app(idiom)
        assert app["configVegaLite"]["view"]["stroke"] is None
        assert app["configVegaLite"]["bar"]["cornerRadius"] == 0
        for m in _marks(app["spec"]):
            for k in ("cornerRadius", "cornerRadiusEnd"):
                assert not m.get(k), f"{idiom}: {k} on a mark (SI 2.1)"


def test_si_2_2_only_semantic_colours():
    """SI 2.2 — every colour in the spec has a role in the profile: AC, ink, the three
    variance ratings, white (hollow markers). No decorative colour."""
    allowed = {TOK["ac"].upper(), TOK["reference_ink"].upper(), TOK["good"].upper(),
               TOK["bad"].upper(), TOK["neutral"].upper(), "#605E5C", "#E1DFDD"}
    for idiom in _ibcs_idioms():
        spec = json.dumps(_app(idiom)["spec"])
        used = {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}", spec)}
        assert used <= allowed, f"{idiom}: colours without a role {sorted(used - allowed)} (SI 2.2)"


def test_si_3_1_data_labels_replace_value_axes():
    """SI 3.1 — where values are labelled, the compiled chart has no axis on a quantitative
    scale and no grid. Checked on the compiled Vega, because layered axes merge."""
    vlc = pytest.importorskip("vl_convert")
    for idiom in _ibcs_idioms():
        app = _app(idiom)
        has_labels = any(m.get("type") == "text" for m in _marks(app["spec"]))
        if not has_labels:
            continue
        spec = dict(app["spec"])
        spec["config"] = app["configVegaLite"]
        spec["data"] = {"values": []}
        vega = vlc.vegalite_to_vega(spec)
        linear = {s["name"] for s in vega.get("scales", []) if s.get("type") in ("linear", "log", "sqrt", "pow")}
        axes = [a for a in vega.get("axes", []) if a.get("scale") in linear]
        assert not axes, f"{idiom}: value axis despite data labels (SI 3.1)"
        assert not any(a.get("grid") for a in vega.get("axes", [])), f"{idiom}: grid lines (SI 3.1)"


def test_un_3_1_absolute_bars_take_two_thirds_of_the_category():
    """UN 3.1 — absolute measures: bar width 2/3 of the category. The profile sets the band
    padding to 1/3; a banded bar must not override its width."""
    cfg = render.vegalite_config("ibcs")
    assert abs(cfg["scale"]["bandPaddingInner"] - 1 / 3) < 0.01
    for idiom in BANDED_BARS:
        for m in _marks(_app(idiom)["spec"]):
            if m.get("type") == "bar" and not _is_pin(m):   # pins are thin by rule (UN 4.1), tested below
                for k in ("size", "width", "height"):
                    assert k not in m, f"{idiom}: bar sets {k}, overriding the 2/3 band (UN 3.1)"


def test_un_3_2_scenarios_by_fill_not_by_colour():
    """UN 3.2 — AC dark solid; PY lighter solid of the same colour; PL outlined (hollow)."""
    from contrast import relative_luminance  # noqa: PLC0415
    assert relative_luminance(TOK["ac"]) < 0.1, "AC must be dark"
    ranking = _app("bar_ranking")["spec"]["layer"]
    py, ac = ranking[0]["mark"], ranking[1]["mark"]
    assert py["color"] == ac["color"] == TOK["ac"]
    assert py.get("opacity", 1) < ac.get("opacity", 1), "PY must be lighter than AC"
    # line: layers found by the series they draw, not by position (PY sits behind AC, BO-052)
    p = render.load_entry("line")["profiles"]["ibcs"]["param_overrides"]
    canon = render.load_entry("line")["canonical_params"]
    by_field = {lay["encoding"]["y"]["field"]: lay["mark"] for lay in _app("line")["spec"]["layer"]
                if (lay.get("mark") or {}).get("type") == "line" and "field" in lay["encoding"]["y"]}
    pl, ac_line = by_field[p["plan_field"]]["point"], by_field[canon["field"]]["point"]
    assert pl["filled"] is False and pl["stroke"] == TOK["ac"], "PL marker must be outlined"
    assert ac_line["filled"] is True, "AC marker must be solid"
    py_line = by_field[canon["py_field"]]
    assert py_line["color"] == TOK["ac"] and py_line.get("opacity") == TOK["py_tint_alpha"], \
        "PY line: AC colour, lighter by the governed tint (UN 3.2)"
    assert "strokeDash" not in py_line, "PY is solid — dashed is FC"
    assert by_field[canon["fc_field"]].get("strokeDash"), "FC is dashed"


def test_un_4_1_variances_coloured_by_rating_not_by_sign():
    """UN 4.1 — good bright green, bad dark red, neutral blue, decided by the rating (polarity),
    never by the sign alone; positive variance labels carry '+'."""
    from contrast import relative_luminance  # noqa: PLC0415
    assert relative_luminance(TOK["good"]) > relative_luminance(TOK["bad"]), "good must be the brighter one"
    for idiom in RATED:
        spec = _app(idiom)["spec"]
        colors = [n["color"] for n in _walk(spec) if isinstance(n.get("color"), dict)]
        assert colors, f"{idiom}: no colour encoding"
        for c in colors:
            assert c.get("field") == "rating", f"{idiom}: colour not driven by the rating (UN 4.1)"
            assert c["scale"]["domain"] == ["good", "bad", "neutral"]
            assert c["scale"]["range"] == [TOK["good"], TOK["bad"], TOK["neutral"]]
        calc = [t["calculate"] for t in spec.get("transform", []) if t.get("as") == "rating"]
        assert calc and "* 1" in calc[0], f"{idiom}: rating ignores the polarity"
        fmts = [n["format"] for n in _walk(spec) if isinstance(n.get("format"), str)]
        assert any(f.startswith("+") for f in fmts), f"{idiom}: positive variance without '+' (UN 4.1)"


def test_un_4_1_polarity_flips_the_rating():
    """A lower-is-better measure (polarity -1) must turn a negative variance good."""
    entry = render.load_entry("deviation_bar")
    params = dict(render._effective_params(entry, "ibcs"), polarity="-1")
    real = render._realization(entry, "deneb_vegalite", "ibcs")
    spec = json.loads(render.fill(real["template"], params))
    calc = next(t["calculate"] for t in spec["transform"] if t.get("as") == "rating")
    # the first clause of the Vega expression, evaluated for a variance of -2
    first = calc.split("?")[0].replace("datum['gm_vs_plan']", "(-2)")
    assert eval(first) is True, "polarity -1 must rate a negative variance good"  # noqa: S307 — own frozen template


def test_fabric_app_switches_off_runtime_rewrites():
    """VegaVisual rewrites specs at runtime (nice bounds, min bar size, 10K formatting);
    under IBCS those would change what the notation shows."""
    caps = _app("column_time")["capabilities"]
    for flag in ("disableNiceAxisBounds", "disableMinBarSize", "disableCompactNumberFormatting"):
        assert caps.get(flag) is True, f"ibcs must set {flag}"


def test_un_4_1_relative_variances_are_thin_pins_with_a_head():
    """UN 4.1 (p. 54-55) / EX 1.1 (p. 102): a relative variance is a very thin column (pin) with a
    head marker in the minuend's notation (AC = solid dark); pins carry no value axis (SI 3.1).
    Checked on the spec: a pin exists, is at most PIN_BAND_MAX of the band, and has a solid
    square AC head drawn on the same field."""
    for idiom in PINNED:
        spec = _app(idiom)["spec"]
        layers = [n for n in _walk(spec) if isinstance(n.get("mark"), dict)]
        pins = [n for n in layers if _is_pin(n["mark"])]
        assert pins, f"{idiom}: no pin layer (UN 4.1)"
        for pin in pins:
            band = pin["mark"]["width"]["band"]
            assert 0 < band <= PIN_BAND_MAX, f"{idiom}: pin width {band} of the band is not thin (UN 4.1)"
            assert pin["encoding"]["y"].get("axis", {}) is None, f"{idiom}: pin with a value axis (SI 3.1)"
            field = pin["encoding"]["y"]["field"]
            heads = [n["mark"] for n in layers if n["mark"].get("type") == "point"
                     and n.get("encoding", {}).get("y", {}).get("field") == field]
            assert heads, f"{idiom}: pin without a head marker (UN 4.1)"
            head = heads[0]
            assert head.get("filled") is True and head.get("color") == TOK["ac"], \
                f"{idiom}: pin head does not show AC solid dark (UN 4.1 minuend notation)"


def test_un_4_1_pins_measured_thinner_than_the_base_bar():
    """The same rule, measured in the rendered SVG: every pin is at most PIN_BAND_MAX of the
    width of an absolute bar in the same band (multi_tier_column: the AC column next to it;
    variance_pin: the 2/3 band an absolute column would take, from the pin spacing)."""
    mt = _svg_bars("multi_tier_column", [{"month": f"2026-0{i + 1}", "sales": a, "sales_py": p}
                                         for i, (a, p) in enumerate([(6.5, 5.9), (5.2, 4.9), (4.9, 5.6)])])
    col = [b["w"] for b in mt if "sales" in b and "d_rel" not in b]
    pins = [b["w"] for b in mt if "d_rel" in b]
    assert col and len(pins) == 3, "multi_tier_column: columns or pins missing in the SVG"
    assert max(pins) <= PIN_BAND_MAX * min(col) + 0.01, f"pins {pins} not thin against columns {col}"
    vp = _svg_bars("variance_pin", [{"month": f"2026-0{i + 1}", "delta_pl_pct": v}
                                    for i, v in enumerate([0.12, -0.08, 0.3, -0.2])])
    assert len(vp) == 4, "variance_pin: pins missing in the SVG"
    step = 400 / 4          # four categories across the 400 px plot, band = (1 - 1/3) of the step
    base_bar = step * (1 - render.vegalite_config("ibcs")["scale"]["bandPaddingInner"])
    assert max(b["w"] for b in vp) <= PIN_BAND_MAX * base_bar + 0.01, "variance_pin: pins not thin"


def test_un_4_1_co_4_2_absolute_variance_tier_same_width_and_scale():
    """UN 4.1 / CO 4.2 (p. 149): absolute variances as bars of the same width and on the same
    scale as the values they compare. Measured: ΔPY bar width == AC column width, and pixels
    per unit are equal for AC and ΔPY."""
    rows = [{"month": f"2026-0{i + 1}", "sales": a, "sales_py": p}
            for i, (a, p) in enumerate([(6.5, 5.9), (5.2, 4.9), (4.9, 5.6)])]
    bars = _svg_bars("multi_tier_column", rows)
    ac = [b for b in bars if set(b) >= {"sales"} and "tier_end" not in b and "d_rel" not in b]
    var = [b for b in bars if "tier_end" in b]
    assert len(ac) == 3 and len(var) == 3, "multi_tier_column: AC columns or ΔPY bars missing"
    assert {round(b["w"], 3) for b in ac} == {round(b["w"], 3) for b in var}, "ΔPY width != AC width"
    px_ac = ac[0]["h"] / 6.5
    for b, r in zip(var, rows):
        assert abs(b["h"] / abs(r["sales"] - r["sales_py"]) - px_ac) < 0.02 * px_ac, \
            "ΔPY drawn on another scale than AC (CO 4.2 same unit, same scale)"


def test_ex_1_1_waterfall_connectors_end_at_the_last_step():
    """EX 1.1 — connector lines between steps; the last step has no successor, so its
    connector must be filtered, not drawn to a 'null' category (found in R3, 30.09.2026)."""
    vlc = pytest.importorskip("vl_convert")
    for idiom in ("waterfall_pvm", "waterfall_variance", "waterfall_buildup"):
        app = _app(idiom)
        spec = dict(app["spec"], config=app["configVegaLite"],
                    data={"values": [{"driver": "A", "part": "A", "value": 5},
                                     {"driver": "B", "part": "B", "value": -2}]})
        vega = vlc.vegalite_to_vega(spec)
        svg = vlc.vega_to_svg(vega)
        assert ">null<" not in svg, f"{idiom}: a 'null' category on the axis (EX 1.1 connector)"
