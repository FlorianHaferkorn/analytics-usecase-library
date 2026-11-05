"""Profile axis and derived targets (A-31 R2).

A profile is either a NOTATION (house_default, ibcs, print_safe: how an idiom is drawn, per
idiom opt-in) or a STYLE (fluent, editorial, minimal: a Vega-Lite config for every idiom).
`fabric_app` and `html_vegalite` are derived from the `deneb_vegalite` track: one Vega-Lite
source, three runtimes. These tests prove the registry is well-formed, the derived targets
are deterministic and frozen, and every idiom x profile actually rasterizes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
CORPUS = REPO_ROOT / "docs" / "architecture" / "research" / "2026-09-30_visual-stack-r1"


@pytest.mark.parametrize("bounds", [("#CCDDEE", "#F0FAFF"), ("#101820", "#304050")])
def test_background_bounds_native_palette_covers_interior_and_text_roles(bounds):
    """Independent dense RGB samples, including conditional PY/FC and default text ink."""
    import copy
    import itertools
    import contrast

    spec = {"layer": [
        {"mark": {"type": "line", "color": "#008092"}},
        {"mark": {"type": "text", "text": "FC", "color": "#008092"}},
        {"mark": {"type": "line"}, "encoding": {"color": {
            "condition": {"test": "datum.py", "value": "#A0A0A0"}, "value": "#605E5C"}}},
        {"mark": {"type": "point", "fill": "white", "stroke": "#008092"}},
    ]}
    original = copy.deepcopy(spec)
    out, config = render.on_background_bounds(spec, render.vegalite_config("house_default"), bounds)
    assert spec == original
    assert out["layer"][1]["mark"]["text"] == "FC"
    assert out["layer"][3]["mark"]["fill"] == "transparent"
    assert config["background"] == "transparent"
    lo, hi = map(contrast.hex_to_rgb, bounds)
    for fractions in itertools.product((0, .25, .5, .75, 1), repeat=3):
        bg = contrast.rgb_to_hex(tuple(a + (b-a)*f for a, b, f in zip(lo, hi, fractions)))
        assert contrast.contrast_ratio_exact(out["layer"][0]["mark"]["color"], bg) >= 3
        assert contrast.contrast_ratio_exact(out["layer"][1]["mark"]["color"], bg) >= 4.5
        for field in ("labelColor", "titleColor"):
            assert contrast.contrast_ratio_exact(config["axis"][field], bg) >= 4.5
        cond = out["layer"][2]["encoding"]["color"]
        assert contrast.contrast_ratio_exact(cond["value"], bg) >= 3
        assert contrast.contrast_ratio_exact(cond["condition"]["value"], bg) >= 3


@pytest.mark.parametrize("opacity", [0.25, {"condition": {"test": "datum.dim", "value": .25}, "value": 1}])
def test_background_bounds_refuses_unprovable_selection_opacity_without_rewriting(opacity):
    import copy
    spec = {"mark": {"type": "line", "color": "#008092"}, "encoding": {"opacity": opacity}}
    original = copy.deepcopy(spec)
    with pytest.raises(render.BackgroundContrastError, match="opacity"):
        render.on_background_bounds(spec, {}, ("#DDEEFF", "#FFFFFF"))
    assert spec == original


@pytest.mark.parametrize("bounds", [[], ["#fff", "#FFFFFF"], ["#FFFFFF", "#000000"], [None, "#FFFFFF"]])
def test_background_bounds_rejects_invalid_envelopes(bounds):
    with pytest.raises(ValueError, match="background_bounds"):
        render.on_background_bounds({}, {}, bounds)


def test_background_bounds_dynamic_colour_and_alpha_fail_closed():
    for spec in ({"mark": "line", "encoding": {"color": {"field": "value"}}},
                 {"mark": {"type": "line", "opacity": {"expr": "datum.alpha"}}},
                 {"mark": {"type": "line", "color": "red"}}):
        with pytest.raises(render.BackgroundContrastError, match="opaque surface"):
            render.on_background_bounds(spec, {}, ("#DDEEFF", "#FFFFFF"))


def test_background_bounds_default_bytes_are_unchanged():
    for idiom in ("line", "bar_ranking"):
        assert render.render_target(idiom, "fabric_app") == render.render_target(
            idiom, "fabric_app", background_bounds=None)


@pytest.mark.parametrize("bounds", [("#CCDDEE", "#F0FAFF"), ("#101820", "#304050")])
def test_background_bounds_native_line_hover_does_not_dim_unrelated_text(bounds):
    doc = json.loads(render.render_target("line", "fabric_app", bindings={
        "time": "Date", "value": "AC", "plan": "PL", "prior": "PY", "forecast": "FC"},
        params={"flaeche_deckkraft": 0}, background_bounds=bounds)[0])
    assert doc["configVegaLite"]["background"] == "transparent"
    assert "Serienlabel" in json.dumps(doc["spec"])
    assert "pointerover" in json.dumps(doc["spec"])
    # Uncertainty is information, not decorative fill: never delete it to make glass pass.
    with pytest.raises(render.BackgroundContrastError, match="opacity"):
        render.render_target("line", "fabric_app", bindings={
            "time": "Date", "value": "AC", "fc_band": {"lo": "Low", "hi": "High"}},
            params={"flaeche_deckkraft": 0}, background_bounds=bounds)


@pytest.mark.parametrize("bounds", [("#BFEFEC", "#FFFFFF"), ("#0C100E", "#26354D")])
def test_outlined_glass_forecast_preserves_band_and_proves_edges_on_blends(bounds):
    import itertools
    import math
    import contrast

    bindings = {"time": "Date", "value": "AC", "forecast": "FC", "fc_band": {"lo": "Low", "hi": "High"}}
    doc = json.loads(render.render_target("line", "fabric_app", bindings=bindings,
        params={"flaeche_deckkraft": 0}, background_bounds=bounds, outline_forecast_band=True)[0])
    layers = doc["spec"]["layer"]
    band = next(x for x in layers if x.get("mark", {}).get("type") == "area"
                and str(x["mark"].get("description", "")).startswith("Prognoseband "))
    edges = [x for x in layers if x.get("mark", {}).get("description") == "Prognoseband Grenze"]
    forecast = next(x for x in layers if x.get("encoding", {}).get("y", {}).get("field") == "FC"
                    and x.get("mark", {}).get("type") == "line")
    assert band["mark"]["opacity"] == .12 and len(edges) == 2
    assert {x["encoding"]["y"]["field"] for x in edges} == {"Low", "High"}
    assert forecast["mark"].get("strokeDash") and all("strokeDash" not in edge["mark"] for edge in edges)
    assert doc["configVegaLite"]["background"] == "transparent"
    assert all(label in json.dumps(doc["spec"]) for label in ("P10", "P90", "FC"))
    lo, hi = map(contrast.hex_to_rgb, bounds)
    lo = tuple(math.floor(.88 * c) for c in lo)
    hi = tuple(math.ceil(.88 * c + .12 * 255) for c in hi)
    for fractions in itertools.product((0, .5, 1), repeat=3):
        bg = contrast.rgb_to_hex(tuple(a + (b-a)*f for a, b, f in zip(lo, hi, fractions)))
        for line in [*edges, forecast]:
            assert contrast.contrast_ratio_exact(line["mark"]["color"], bg) >= 3


def test_outlined_glass_forecast_requires_opt_in_and_a_canonical_band():
    with pytest.raises(render.BackgroundContrastError, match="exactly one"):
        render.render_target("line", "fabric_app", bindings={"time": "Date", "value": "AC"},
            params={"flaeche_deckkraft": 0}, background_bounds=("#CCDDEE", "#F0FAFF"),
            outline_forecast_band=True)
    with pytest.raises(ValueError, match="requires background_bounds"):
        render.render_target("line", "fabric_app", outline_forecast_band=True)


def test_house_forecast_lower_label_keeps_gap_without_moving_upper_event_strip():
    doc = json.loads(render.render_target("line", "fabric_app", bindings={
        "time":"Date", "value":"AC", "fc_band":{"lo":"Low","hi":"High"}})[0])
    labels = {layer["mark"].get("text"): layer["mark"] for layer in doc["spec"]["layer"]
              if layer.get("mark", {}).get("type") == "text"}
    assert (labels["P10"]["baseline"], labels["P10"]["dy"]) == ("top", 8)
    assert labels["P90"]["dy"] == -7 and "baseline" not in labels["P90"]


@pytest.mark.parametrize("idiom", ["line", "bar_absolute", "bar_ranking"])
def test_house_value_axis_title_can_hide_without_removing_tooltip_unit(idiom):
    params = {"value_unit":"days", "show_value_axis_title":False}
    doc = json.loads(render.render_target(idiom, "html_vegalite", params=params)[0])
    axes = [n["axis"] for n in render._dict_nodes(doc) if isinstance(n.get("axis"), dict)]
    assert axes and all(a.get("title") != "days" for a in axes)
    tooltips = [n["tooltip"] for n in render._dict_nodes(doc) if "tooltip" in n]
    assert "(days)" in json.dumps(tooltips)
    if "ibcs" in render.profiles(idiom):
        bindings = {"value":"v", "time":"t"} if idiom == "line" else {"value":"v", "category":"c"}
        baseline = render.render_target(idiom, "fabric_app", "ibcs", bindings=bindings)[0]
        assert render.render_target(idiom, "fabric_app", "ibcs", bindings=bindings,
                                    params={"show_value_axis_title":False})[0] == baseline


def test_house_value_axis_title_rejects_non_boolean():
    with pytest.raises(ValueError, match="show_value_axis_title must be a boolean"):
        render.render_target("line", "html_vegalite", params={"show_value_axis_title":0})


def test_background_bounds_implicit_text_opacity_and_overlapping_envelope_refuse():
    with pytest.raises(render.BackgroundContrastError, match="opacity"):
        render.on_background_bounds({"mark": {"type": "text", "text": "AC", "opacity": .25}}, {},
                                    ("#DDEEFF", "#FFFFFF"))
    with pytest.raises(render.BackgroundContrastError):
        render.on_background_bounds({"mark": {"type": "line", "color": "#008092"}}, {},
                                    ("#000000", "#FFFFFF"))


def test_background_bounds_bar_binary_axis_visibility_is_not_alpha_dimming():
    doc = json.loads(render.render_target("bar_ranking", "fabric_app", bindings={
        "value": "AC", "category": "Category"}, background_bounds=("#CCDDEE", "#F0FAFF"))[0])
    assert doc["configVegaLite"]["background"] == "transparent"
    for opacity in ({"expr": "show ? .5 : 1"}, {"expr": "datum.alpha"}):
        with pytest.raises(render.BackgroundContrastError, match="opacity role"):
            render.on_background_bounds({"mark": "bar", "encoding": {
                "y": {"axis": {"labelOpacity": opacity}}}}, {}, ("#CCDDEE", "#F0FAFF"))


def _implemented() -> list[str]:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]


def test_every_profile_declares_a_valid_kind():
    for pid in render.all_profiles():
        d = render.profile_def(pid)
        assert d.get("kind") in ("notation", "style"), f"{pid}: kind must be notation or style"
        if d["kind"] == "style":
            base = d.get("base_notation")
            assert base in render.all_profiles("notation"), f"{pid}: base_notation '{base}' is no notation profile"
            assert d.get("vegalite_config"), f"{pid}: a style profile without vegalite_config does nothing"


def test_style_profiles_cite_the_corpus():
    """Every source of a style profile names an entry id that exists in the R1 corpus
    (or the corpus summary, which is marked experimental)."""
    ids = set()
    for f in ("product", "editorial", "fabric", "ibcs_v2"):
        ids |= {e["id"] for e in yaml.safe_load((CORPUS / f"{f}.yaml").read_text(encoding="utf-8"))}
    for pid in render.all_profiles("style"):
        d = render.profile_def(pid)
        for src in d.get("source") or []:
            ref = str(src).split(" ")[0]
            if d.get("status") == "experimental" and "summary" in src:
                continue
            if d.get("basis") == "derivation" and str(src).startswith("derivation:"):
                continue  # ADR-0026: a derived rule names its basis and says it is not a corpus entry
            assert ref in ids, f"{pid}: source '{ref}' is not an entry of the R1 corpus"


def test_capabilities_are_known_vegavisual_flags():
    for pid in render.all_profiles():
        caps = render.profile_def(pid).get("vegavisual_capabilities") or {}
        unknown = set(caps) - set(render.VEGAVISUAL_CAPABILITIES)
        assert not unknown, f"{pid}: unknown flags {sorted(unknown)}"
        assert all(isinstance(v, bool) for v in caps.values()), f"{pid}: capability values must be booleans"


def test_profiles_carry_no_brand_colours_in_style():
    """Brand colours are Klasse C (SHARED_SUBSTANCE §2.3) and come from the brand tokens —
    a style profile must not set a categorical range."""
    for pid in render.all_profiles("style"):
        cfg = render.profile_def(pid).get("vegalite_config") or {}
        assert "range" not in cfg, f"{pid}: a style profile sets range colours; those belong to the brand"


def test_style_config_is_the_baseline_overlaid():
    base = render.vegalite_config(render.default_profile())
    for pid in render.all_profiles("style"):
        cfg = render.vegalite_config(pid)
        own = render.profile_def(pid)["vegalite_config"]
        for k, v in own.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    assert cfg[k][kk] == vv, f"{pid}: {k}.{kk} not taken from the profile"
            else:
                assert cfg[k] == v
        for k in base:
            assert k in cfg, f"{pid}: lost baseline key '{k}'"


#: Keys only full Vega knows at the top level; Vega-Lite has none of them there. `@microsoft/fabric-visuals`
#: 4.0.0 accepts Vega-Lite or Flint only (`VisualizationSpec = VegaLiteSpecWithOptionalData | FlintSpec`,
#: dist/index.d.ts:37), so a full-Vega spec would not render in the Fabric App (Meridian D-642).
VEGA_ONLY_TOP_LEVEL = ("signals", "scales", "axes", "legends", "marks", "projections")
VEGA_LITE_SCHEMA = "https://vega.github.io/schema/vega-lite/"


def is_vega_lite(spec: dict) -> bool:
    return str(spec.get("$schema", "")).startswith(VEGA_LITE_SCHEMA) and not any(k in spec for k in VEGA_ONLY_TOP_LEVEL)


def test_every_fabric_app_target_is_vega_lite():
    """D-642: the Fabric App renders Vega-Lite only. Every idiom x notation profile the cockpit can ask for is
    Vega-Lite; an idiom Vega-Lite cannot draw is reported as not mappable, never emitted as full Vega or D3."""
    seen = 0
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            if render.profile_def(pid).get("kind", "notation") != "notation":
                continue
            spec = json.loads(render.render_target(idiom, "fabric_app", pid)[0])["spec"]
            assert is_vega_lite(spec), f"{idiom}@{pid}: fabric_app target is not Vega-Lite"
            seen += 1
    assert seen >= 30, f"expected the Vega-Lite set under its notation profiles, got {seen}"


def test_vega_lite_check_rejects_full_vega():
    """Counter-check: a full-Vega spec (signals/marks at the top) and a v5 Vega schema fail the check."""
    assert not is_vega_lite({"$schema": "https://vega.github.io/schema/vega/v5.json", "marks": []})
    assert not is_vega_lite({"$schema": VEGA_LITE_SCHEMA + "v5.json", "signals": [], "mark": "bar"})
    assert is_vega_lite({"$schema": VEGA_LITE_SCHEMA + "v5.json", "mark": "bar"})


def test_fabric_app_targets_match_golden_and_are_idempotent():
    frozen = 0
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            if render.profile_def(pid).get("kind", "notation") != "notation":
                continue
            out, _ = render.render_target(idiom, "fabric_app", pid)
            assert out == render.render_target(idiom, "fabric_app", pid)[0], f"{idiom}@{pid}: not idempotent"
            gp = render.target_golden_path(idiom, "fabric_app", pid)
            assert gp.exists(), f"freeze it: render.py write-targets {idiom}"
            assert out == gp.read_text(encoding="utf-8"), f"{idiom}@{pid}: fabric_app drifted from golden"
            doc = json.loads(out)
            assert doc["data_name"] == "dataset" and doc["spec"]["data"] == {"name": "dataset"}
            frozen += 1
    assert frozen >= 30, f"expected the Vega-Lite set under its notation profiles, got {frozen}"


def test_html_target_embeds_the_profile_config():
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            spec = json.loads(render.render_target(idiom, "html_vegalite", pid)[0])
            assert spec["config"] == render.vegalite_config(pid), f"{idiom}@{pid}: config not embedded"


def test_every_idiom_rasterizes_under_every_profile():
    """The real gate: the Vega-Lite a Fabric App or an HTML page would receive draws, for
    every idiom x profile (style profiles included)."""
    pytest.importorskip("vl_convert")
    sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library" / "acceptance"))
    import render_acceptance  # noqa: E402
    import vl_convert as vlc  # noqa: E402

    drawn = 0
    for idiom in _implemented():
        for pid in render.target_profiles(idiom):
            spec = json.loads(render.render_target(idiom, "html_vegalite", pid)[0])
            spec = render_acceptance._sized_with_data(spec, render_acceptance._field_covering_sample())
            png = vlc.vegalite_to_png(spec, scale=1)
            assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 1000, f"{idiom}@{pid}: drew nothing"
            drawn += 1
    assert drawn >= 90, f"expected every idiom x profile to draw, got {drawn}"


def test_dark_background_keeps_salience_and_contrast():
    """A-31 R6: the library's inks are chosen for light cards (#0F2430 measures 1.1:1 on the
    Fabric-App dark card #292929). `background=` maps each colour by salience (contrast.for_dark_ground):
    marks >= 3:1, text >= 4.5:1, gridlines stay quieter than the data, PY stays quieter than AC."""
    import contrast

    dark = "#292929"
    for idiom in ("line", "bar_ranking", "deviation_bar", "waterfall_pvm"):
        for pid in ("house_default", "ibcs", "editorial"):
            if pid not in render.target_profiles(idiom):
                continue
            light = json.loads(render.render_target(idiom, "fabric_app", pid)[0])
            doc = json.loads(render.render_target(idiom, "fabric_app", pid, background=dark)[0])
            assert light != doc, f"{idiom}@{pid}: nothing changed on a dark ground"
            assert '"white"' not in json.dumps(doc), f"{idiom}@{pid}: white hollow fill on a dark ground"
            for node, parent in _hex_literals(doc["spec"]) + _hex_literals(doc["configVegaLite"]):
                if parent == "gridColor" or (parent == "fill" and node == dark):
                    continue
                assert contrast.contrast_ratio(node, dark) >= 3.0, f"{idiom}@{pid}: {parent}={node}"
            for key in ("labelColor", "titleColor"):
                for node, parent in _hex_literals(doc["configVegaLite"]):
                    if parent == key:
                        assert contrast.contrast_ratio(node, dark) >= 4.5, f"{idiom}@{pid}: {key}={node}"


def test_dark_mapping_keeps_the_order_of_emphasis():
    """Measured 30.09.2026: lifting to a floor only made the #E1DFDD grid brighter than the data."""
    import contrast

    dark = "#292929"
    ink, grid = contrast.for_dark_ground("#0F2430", dark), contrast.for_dark_ground("#E1DFDD", dark)
    assert contrast.contrast_ratio(ink, dark) > 2 * contrast.contrast_ratio(grid, dark)
    ac = contrast.for_dark_ground("#404040", dark, min_ratio=3.0)
    py = contrast.for_dark_ground("#A0A0A0", dark, min_ratio=3.0)
    assert contrast.contrast_ratio(ac, dark) > contrast.contrast_ratio(py, dark), "PY louder than AC"
    red = contrast.hex_to_oklch(contrast.for_dark_ground("#A4262C", dark))[2]
    assert abs(red - contrast.hex_to_oklch("#A4262C")[2]) < 3.0


def _hex_literals(node, key=None):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out += _hex_literals(v, k)
    elif isinstance(node, list):
        for v in node:
            out += _hex_literals(v, key)
    elif isinstance(node, str) and len(node) == 7 and node.startswith("#"):
        out.append((node, key))
    return out


@pytest.mark.parametrize("idiom", ["line", "bar_absolute", "bar_ranking"])
def test_house_presentation_controls_preserve_ibcs_and_default_goldens(idiom):
    """Opt-in presentation never changes the frozen default or the IBCS reading."""
    for profile in ["house_default", *render.profiles(idiom)]:
        doc, _ = render.render_target(idiom, "fabric_app", profile)
        assert doc == render.target_golden_path(idiom, "fabric_app", profile).read_text(encoding="utf-8")
    if "ibcs" not in render.profiles(idiom):
        return
    opts = {"axis_grid_opacity": 0.3, "axis_grid_dash": [], "value_tick_count": 4, "end_marker_size": 16,
            "show_phase_annotations": False, "show_axis_break": False}
    bindings = {"value": "v", "time": "t", "category": "c"}
    baseline, _ = render.render_target(idiom, "fabric_app", "ibcs", bindings=bindings)
    changed, _ = render.render_target(idiom, "fabric_app", "ibcs", bindings=bindings, params=opts)
    assert changed == baseline


def test_house_line_presentation_is_resolved_in_original_template():
    opts = {"axis_grid_opacity": 0.3, "axis_grid_dash": [], "value_tick_count": 4, "end_marker_size": 16}
    doc = json.loads(render.render_target("line", "fabric_app", "house_default",
                                         bindings={"value": "v", "time": "t"}, params=opts)[0])
    layers = doc["spec"]["layer"]
    hero = next(layer for layer in layers if layer.get("mark", {}).get("type") == "line"
                and "axis" in layer.get("encoding", {}).get("y", {}))
    assert hero["encoding"]["y"]["axis"]["gridOpacity"] == 0.3
    assert hero["encoding"]["y"]["axis"]["gridDash"] == []
    assert hero["encoding"]["y"]["axis"]["tickCount"] == 4
    endpoint = next(layer for layer in layers if layer.get("mark", {}).get("filled") is True)
    assert endpoint["mark"]["size"] == 16
    assert hero["encoding"]["y"]["field"] == "v"


@pytest.mark.parametrize("idiom", ["bar_absolute", "bar_ranking"])
def test_house_bar_tick_density_keeps_direct_label_suppression(idiom):
    doc = json.loads(render.render_target(idiom, "fabric_app", "house_default",
                                         bindings={"value": "v", "category": "c"}, params={"value_tick_count": 4})[0])
    # The base value axis remains at zero and direct labels still remove its ticks.
    text = json.dumps(doc["spec"])
    assert "_beschriftet ? 0 : 4" in text
    assert "ceil(width/40)" not in text
    # No false zero-baseline scale is introduced for any bar channel.
    def scales(node):
        if isinstance(node, dict):
            if "scale" in node:
                yield node["scale"]
            for value in node.values():
                yield from scales(value)
        elif isinstance(node, list):
            for value in node:
                yield from scales(value)
    assert not any(scale.get("zero") is False for scale in scales(doc["spec"]))


@pytest.mark.parametrize("key,value", [("axis_grid_opacity", 1.1), ("axis_grid_opacity", True),
                                     ("axis_grid_dash", [-1]), ("end_marker_size", -2),
                                     ("value_tick_count", 1), ("value_tick_count", 4.5)])
def test_house_presentation_rejects_invalid_inputs(key, value):
    with pytest.raises(ValueError):
        render.render_target("line", "fabric_app", "house_default", params={key: value})


def test_house_annotation_switches_preserve_event_tooltip_and_scale():
    doc = json.loads(render.render_target("line", "fabric_app", "house_default",
        bindings={"value": "v", "time": "t", "event": "phase", "current": "running"},
        params={"show_phase_annotations": False, "show_axis_break": False, "label_current": ""})[0])
    layers = doc["spec"]["layer"]
    event_layers = [layer for layer in layers
                    if layer.get("mark", {}).get("description") in ("Ereignis", "Ereignisnummer")]
    assert len(event_layers) == 2
    assert all("&& false" in layer["transform"][0]["filter"] for layer in event_layers)
    axis_break = next(layer for layer in layers if layer.get("mark", {}).get("text") == "≈")
    assert axis_break["transform"][0]["filter"] == "datum._yangepasst && false"
    hero = next(layer for layer in layers if layer.get("mark", {}).get("type") == "line"
                and "axis" in layer.get("encoding", {}).get("y", {}))
    assert hero["encoding"]["y"]["scale"] == {"zero": False}
    assert {"field": "phase", "type": "nominal", "title": "phase"} in hero["encoding"]["tooltip"]
    caption = next(layer for layer in layers if layer.get("mark", {}).get("description") == "laufende Periode"
                   and layer["mark"]["type"] == "text")
    assert caption["mark"]["text"] == ""


def test_emitted_dark_forecast_text_keeps_text_contrast_separate_from_mark():
    """A line pixel is not a text color: the original dark mapper enforces each role."""
    bg = "#17181B"
    doc = json.loads(render.render_target("line", "fabric_app", "house_default",
        bindings={"value": "v", "time": "t", "forecast": "fc"},
        params={"col_line": "#008092"}, background=bg)[0])
    layers = doc["spec"]["layer"]
    line = next(layer["mark"] for layer in layers if layer.get("mark", {}).get("type") == "line")
    label = next(layer["mark"] for layer in layers if layer.get("mark", {}).get("text") == "FC")
    contrast = render._contrast()
    assert contrast.contrast_ratio_exact(line["color"], bg) >= 3.0
    assert contrast.contrast_ratio_exact(label["color"], bg) >= 4.5
    assert line["color"] != label["color"], "The mapper must distinguish mark and text floors"


@pytest.mark.parametrize("domain", [None, [], [0], [0, 0], [40, 0], [0, True], [0, float("inf")], [float("nan"), 40]])
def test_value_domain_rejects_invalid_bounds(domain):
    with pytest.raises(ValueError, match="value_domain"):
        render.render_target("line", "fabric_app", params={"value_domain": domain})


@pytest.mark.parametrize("idiom", ["line", "bar_absolute", "bar_ranking"])
def test_requested_domain_native_union_retains_data_and_zero_reference(idiom):
    """A finite reference range must expand to actual/prior/plan data, never clip it."""
    vl = pytest.importorskip("vl_convert")
    doc = json.loads(render.render_target(idiom, "fabric_app", "house_default",
        bindings={"time": "t", "value": "v", "category": "c", "plan": "pl", "prior": "py"},
        params={"value_domain": [0, 40], "value_unit": "%", "value_format": ",.1~f"})[0])
    spec = doc["spec"]
    spec["data"] = {"values": [{"t": "2024-01-01", "c": "A", "v": 32.2, "pl": 55, "py": 65},
                                 {"t": "2024-02-01", "c": "B", "v": 51.4, "pl": 56, "py": 66}]}
    spec["config"] = doc["configVegaLite"]
    spec["width"], spec["height"] = 400, 200
    compiled = vl.vegalite_to_vega(spec)
    scale = next(item for item in compiled["scales"] if item["name"] == ("y" if idiom == "line" else "x"))
    fields = scale["domain"]["fields"]
    assert [0, 40] in fields
    assert any(isinstance(item, dict) and item.get("field", "").startswith("v") for item in fields)
    if idiom == "line":
        assert any(isinstance(item, dict) and item.get("field") == "pl" for item in fields)
    if idiom != "bar_absolute":
        assert any(isinstance(item, dict) and item.get("field", "").startswith("py") for item in fields)
    assert scale["nice"] is False
    if idiom != "line":
        assert scale["zero"] is True
    scene = vl.vegalite_to_scenegraph(spec)
    def text_values(node):
        if isinstance(node, dict):
            if "text" in node:
                yield node["text"]
            for value in node.values():
                yield from text_values(value)
        elif isinstance(node, list):
            for value in node:
                yield from text_values(value)
    assert "0" in list(text_values(scene)), "The zero reference remains visible on directly labelled bars"


def test_requested_domain_keeps_static_target_outside_reference_range():
    vl = pytest.importorskip("vl_convert")
    doc = json.loads(render.render_target("line", "fabric_app", "house_default",
        bindings={"time": "t", "value": "v"}, params={"value_domain": [0, 40], "target_val": 75})[0])
    spec = doc["spec"]
    spec["data"] = {"values": [{"t": "2024-01-01", "v": 32.2}]}
    spec["config"] = doc["configVegaLite"]
    scale = next(item for item in vl.vegalite_to_vega(spec)["scales"] if item["name"] == "y")
    assert [75] in scale["domain"]["fields"]


def test_value_unit_format_is_explicit_and_does_not_rescale_data():
    doc = json.loads(render.render_target("line", "fabric_app", "house_default",
        bindings={"time": "t", "value": "v", "plan": "pl"},
        params={"value_domain": [0, .4], "value_unit": "%", "value_format": ".1~%"})[0])
    hero = next(layer for layer in doc["spec"]["layer"]
                if layer.get("mark", {}).get("type") == "line" and "axis" in layer.get("encoding", {}).get("y", {}))
    assert hero["encoding"]["y"]["field"] == "v"
    assert hero["encoding"]["y"]["axis"]["title"] == "%"
    assert hero["encoding"]["tooltip"][1] == {"field": "v", "type": "quantitative", "title": "v (%)", "format": ".1~%"}
    assert doc["configVegaLite"]["axisQuantitative"]["format"] == ".1~%"
    for profile in ("ibcs", "print_safe"):
        baseline = render.render_target("line", "fabric_app", profile, bindings={"time": "t", "value": "v"})
        styled = render.render_target("line", "fabric_app", profile, bindings={"time": "t", "value": "v"},
            params={"value_domain": [0, 40], "value_unit": "%", "value_format": ".1~%"})
        assert baseline == styled
