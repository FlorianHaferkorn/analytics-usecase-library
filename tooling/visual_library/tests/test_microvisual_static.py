"""One Library definition, interactive micro forms and offline exports."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render


def test_live_bullet_roles_expand_signed_values_and_keep_real_threshold():
    out = json.loads(render.render_target("bullet", "fabric_app", bindings={"value": "value"},
        params={"target_val": 1}, microvisual="bullet", micro_options={
            "target_field": "target", "threshold_field": "threshold", "minimal": True})[0])
    spec = out["spec"]
    assert out["idiom"] == "bullet"
    assert len(spec["layer"]) == 3
    assert spec["layer"][1]["encoding"]["x"]["field"] == "target"
    assert spec["layer"][2]["encoding"]["x"]["field"] == "threshold"
    assert spec["layer"][0]["encoding"]["x"]["scale"] == {"domain": {"unionWith": [0, 0]}, "zero": True}
    assert spec["layer"][0]["encoding"]["x"]["axis"] is None


def test_achievement_bounded_scale_omits_outside_threshold_not_clamps_it():
    spec = json.loads(render.render_target("bullet", "html_vegalite", bindings={"value":"value"},
        params={"target_val":1}, microvisual="bullet", micro_options={
            "achievement":True,"target_field":"target","threshold_field":"threshold"})[0])
    assert spec["layer"][0]["encoding"]["x"]["scale"]["domain"] == [0,1.2]
    assert spec["layer"][2]["transform"][-1]["filter"]["range"] == [0,1.2]


@pytest.mark.parametrize("profile", ["house_default", "ibcs", "print_safe"])
def test_spark_native_scenarios_no_grid_or_text_and_null_gaps_rasterize(profile):
    kw = dict(bindings={"value":"actual","time":"period","plan":"plan"},
              params={"time_type":"ordinal"}, microvisual="spark")
    spec = json.loads(render.render_target("line", "html_vegalite", profile, **kw)[0])
    assert all(layer["mark"]["type"] in ("line","point") for layer in spec["layer"])
    assert spec["encoding"]["x"]["type"] == "ordinal"
    data = [{"period":"KW 1","actual":-2,"plan":3},
            {"period":"KW 2","actual":None,"plan":4},
            {"period":"KW 3","actual":8,"plan":5}]
    svg = render.render_svg("line", data, profile, width=300,height=40, **kw)
    root = ET.fromstring(svg)
    assert root.get("data-visual-library") == "line"
    assert root.get("data-visual-profile") == profile
    assert "NaN" not in svg
    assert any(n.tag.endswith("title") for n in root.iter())


def test_static_export_does_not_mutate_input_and_preserves_category_tooltips():
    data=[{"category":"Nordics", "value":125}, {"category":"South", "value":-25}]
    saved = json.dumps(data)
    svg=render.render_svg("bar_ranking",data,bindings={"category":"category","value":"value"},
                          params={"top_n":2,"rest":"none"},width=400,height=120)
    assert json.dumps(data) == saved
    assert "Nordics" in svg and "125" in svg and ("-25" in svg or "−25" in svg)
    assert "data-visual-library" in svg


@pytest.mark.parametrize("kwargs", [dict(microvisual="other"),
    dict(microvisual="bullet",micro_options={"threshold":float("nan")}),
    dict(microvisual="bullet",micro_options={"domain":[2,1]}),
    dict(microvisual="bullet",micro_options={"target_field":"a.b"})])
def test_invalid_micro_contract_fails_closed(kwargs):
    with pytest.raises(ValueError):
        render.render_target("bullet","fabric_app",bindings={"value":"v"},params={"target_val":1},**kwargs)


def test_spark_detail_height_and_non_temporal_tooltip_use_real_labels():
    out=json.loads(render.render_target("line","html_vegalite",bindings={"time":"period","value":"v"},
        params={"time_type":"ordinal"},microvisual="spark",micro_options={"height":72})[0])
    assert out["height"] == 72
    for n in render._dict_nodes(out):
        if n.get("field") == "period":
            assert n.get("type") != "temporal"


def test_static_radius_uses_existing_notation_cap():
    spec=json.loads(render.render_target("bar_ranking","html_vegalite","ibcs",
        params={"bar_corner_radius":8})[0])
    assert spec["config"]["bar"]["cornerRadiusEnd"] == 0


def test_inline_exports_namespace_clip_ids_without_changing_references(monkeypatch):
    import vl_convert
    original = vl_convert.vegalite_to_svg
    def with_clip(spec):
        text=original(spec)
        return text.replace("</svg>",
            '<defs><clipPath id="clip123"><rect width="300" height="22"/></clipPath></defs>'
            '<g clip-path="url(#clip123)"/></svg>')
    monkeypatch.setattr(vl_convert,"vegalite_to_svg",with_clip)
    args=dict(bindings={"value":"v"},params={"target_val":1},microvisual="bullet")
    a=render.render_svg("bullet",[{"v":0.8}],**args)
    b=render.render_svg("bullet",[{"v":0.4}],**args)
    def ids(svg):
        return {n.get("id") for n in ET.fromstring(svg).iter() if n.get("id")}
    assert ids(a) and ids(b) and not ids(a).intersection(ids(b))
    assert a == render.render_svg("bullet",[{"v":0.8}],**args)


@pytest.mark.parametrize("polarity",[1,-1])
def test_dynamic_bullet_signed_target_and_requested_domain_are_not_clipped(polarity):
    kw=dict(bindings={"value":"v"},params={"target_val":1},microvisual="bullet",
        micro_options={"polarity":polarity,"domain":[-100,200],"target_field":"target","threshold_field":"threshold"})
    spec=json.loads(render.render_target("bullet","html_vegalite",**kw)[0])
    assert all(layer["encoding"]["x"]["scale"]["domain"]["unionWith"] == [-100,200]
               for layer in spec["layer"])
    svg=render.render_svg("bullet",[{"v":-25,"target":-50,"threshold":None}],width=300,height=22,**kw)
    assert "NaN" not in svg
    assert "−25" in svg or "-25" in svg


def test_ordinal_chronology_uses_input_order_not_lexical_latest():
    spec=json.loads(render.render_target("line","html_vegalite",bindings={"value":"v","time":"p"},
        params={"time_type":"ordinal"},microvisual="spark")[0])
    assert spec["transform"][0]["window"][0]["as"] == "_vl_period_order"
    for node in render._dict_nodes(spec):
        if "window" in node:
            assert all(sort["field"] != "p" for sort in node.get("sort",[]))
    svg=render.render_svg("line",[{"p":"KW 52","v":5},{"p":"KW 1","v":8}],
        bindings={"value":"v","time":"p"},params={"time_type":"ordinal"},microvisual="spark",width=300,height=40)
    points=[n for n in ET.fromstring(svg).iter() if n.get("aria-roledescription") == "point"]
    assert points and all("KW 1" in n.get("aria-label","") for n in points)


def test_micro_bullet_has_visible_paths_without_zero_width_native_clipping():
    svg=render.render_svg("bullet",[{"v":0.8,"target":1}],bindings={"value":"v"},
        params={"target_val":1},microvisual="bullet",micro_options={"target_field":"target","minimal":True},width=300,height=22)
    root=ET.fromstring(svg)
    bars=[n for n in root.iter() if n.get("aria-roledescription") == "bar"]
    assert bars and all("h0v" not in n.get("d","") for n in bars)
    for clip in (n for n in root.iter() if n.tag.endswith("clipPath")):
        for node in clip:
            if node.tag.endswith("rect"):
                assert float(node.get("width",0)) > 0 and float(node.get("height",0)) > 0
            if node.tag.endswith("path"):
                assert "L0,0Z" != node.get("d")


def test_english_native_descriptions_are_localized_at_source():
    out=json.loads(render.render_target("line","html_vegalite",bindings={"time":"p","value":"v",
        "event":"event","fc_band":{"lo":"lo","hi":"hi"}},params={"lang":"en"})[0])
    descriptions=[n["description"] for n in render._dict_nodes(out) if "description" in n]
    assert "Event" in descriptions and "Event number" in descriptions
    assert any(d.startswith("Forecast band") for d in descriptions)
    assert not any("Ereignis" in d or "Prognoseband" in d for d in descriptions)


def test_static_dark_export_paints_the_ground_used_for_contrast():
    svg=render.render_svg("bar_ranking",[{"c":"North","v":12}],
        bindings={"category":"c","value":"v"},background="#11242F",width=400,height=120)
    root=ET.fromstring(svg)
    rects=[n for n in root.iter() if n.tag.endswith("rect")]
    assert rects and rects[0].get("fill") == "#11242F"
    assert not any(n.get("fill") == "white" for n in rects)


def test_static_export_escapes_labels_and_never_creates_executable_markup():
    label='<script>alert("x")</script> & <value>'
    svg=render.render_svg("bar_ranking",[{"c":label,"v":12}],
        bindings={"category":"c","value":"v"},width=400,height=120)
    root=ET.fromstring(svg)
    assert not any(n.tag.endswith("script") for n in root.iter())
    assert any(label in (n.text or "") for n in root.iter() if n.tag.endswith("title"))


@pytest.mark.parametrize("dimensions",[{"width":True},{"height":False},{"width":0},{"height":-1}])
def test_static_dimensions_fail_closed(dimensions):
    with pytest.raises(ValueError,match="positive integers"):
        render.render_svg("bullet",[],**dimensions)


def test_static_compact_canvas_includes_axes_without_shrinking_native_font():
    svg=render.render_svg("bar_ranking",[{"c":"Consumer Electronics","v":125},{"c":"Nordics","v":-25}],
        bindings={"category":"c","value":"v"},width=440,height=180)
    root=ET.fromstring(svg)
    assert float(root.get("width")) == 440
    assert float(root.get("height")) == 180
    sizes=[float(n.get("font-size").removesuffix("px")) for n in root.iter()
           if n.tag.endswith("text") and n.get("font-size")]
    assert sizes and min(sizes) >= 10
