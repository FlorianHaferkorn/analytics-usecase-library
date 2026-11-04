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


@pytest.mark.parametrize("bounds", [("#BFEFEC", "#FFFFFF"), ("#0C100E", "#26354D")])
@pytest.mark.parametrize("lang", ["de", "en"])
def test_static_glass_forecast_uses_original_bounds_contract_and_transparent_ground(bounds, lang, monkeypatch):
    original = render.render_target
    seen = {}
    def capture(*args, **kwargs):
        seen.update(kwargs)
        return original(*args, **kwargs)
    monkeypatch.setattr(render, "render_target", capture)
    svg = render.render_svg("line", [
        {"Date":"2026-01-01","AC":20,"FC":None,"Low":None,"High":None},
        {"Date":"2026-02-01","AC":None,"FC":24,"Low":18,"High":30},
        {"Date":"2026-03-01","AC":None,"FC":28,"Low":20,"High":36}],
        bindings={"time":"Date","value":"AC","forecast":"FC","fc_band":{"lo":"Low","hi":"High"}},
        params={"flaeche_deckkraft":0,"lang":lang}, width=600,height=240,
        background_bounds=bounds, outline_forecast_band=True)
    assert seen["background_bounds"] is bounds and seen["outline_forecast_band"] is True
    root = ET.fromstring(svg)
    assert not any(n.get("fill") in ("white", "#FFFFFF", "#ffffff")
                   for n in root.iter() if n.tag.endswith("rect"))
    edge_label = "Forecast band boundary" if lang == "en" else "Prognoseband Grenze"
    assert svg.count(f'aria-label="{edge_label}"') == 2
    assert "P10" in svg and "P90" in svg


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


def _line_fit_spec():
    spec = json.loads(render.render_target('line', 'html_vegalite',
        bindings={'time': 'd', 'value': 'v'})[0])
    spec.update(datasets={'dataset': [{'d': '2026-08-02', 'v': 3}, {'d': '2026-09-06', 'v': 5}]},
                width=440, height=180, autosize={'type': 'fit', 'contains': 'padding'})
    return spec


def _line_metric_fixture(item):
    # Explicit provider-contract fixture, not a claim about the host font.
    return {'ascent': 1984, 'descent': 494, 'units_per_em': 2048}


def test_native_line_fit_off_is_negative_control_and_on_converges_without_resizing():
    import copy
    import vl_convert as vlc
    spec = _line_fit_spec()
    saved = copy.deepcopy(spec)
    before = vlc.vegalite_to_svg(spec)
    off = render._vertical_plaintext_overflow(vlc, spec, 440, 180, _line_metric_fixture, before)
    assert off['measured'] > 0 and off['top'] + off['bottom'] > 0
    fitted = render._vertical_fit_svg(vlc, spec, 440, 180, _line_metric_fixture)
    on = render._vertical_plaintext_overflow(vlc, spec, 440, 180, _line_metric_fixture, fitted)
    assert on['measured'] == off['measured'] and on['top'] == on['bottom'] == 0
    assert fitted == render._vertical_fit_svg(vlc, copy.deepcopy(saved), 440, 180, _line_metric_fixture)
    assert set(k for k in spec if spec[k] != saved[k]) == {'padding'}
    a, b = ET.fromstring(before), ET.fromstring(fitted)
    assert [a.get(k) for k in ('width', 'height', 'viewBox')] == [b.get(k) for k in ('width', 'height', 'viewBox')]
    def texts(root):
        return [n.text for n in root.iter() if n.tag.endswith('text')]
    assert texts(a) == texts(b)
    def marks(root):
        return [n.get('aria-label') for n in root.iter() if n.get('role') == 'graphics-symbol']
    assert marks(a) == marks(b)


def test_native_metric_provider_resolves_embedded_face_without_family_alias():
    metric = render.native_font_line_metrics({'font': 'sans-serif', 'fontSize': 11, 'text': 'August'})
    assert metric['font_name'] and metric['ascent'] > 0
    assert metric['descent'] >= 0 and metric['units_per_em'] > 0


@pytest.mark.parametrize('metrics', [None, {}, {'ascent': 10, 'descent': 2, 'units_per_em': 0},
    {'ascent': -1, 'descent': 2, 'units_per_em': 1000},
    {'ascent': 10, 'descent': -2, 'units_per_em': 1000},
    {'ascent': float('nan'), 'descent': 2, 'units_per_em': 1000},
    {'ascent': 10, 'descent': 2, 'units_per_em': float('inf')}])
def test_native_line_fit_unknown_invalid_metrics_fail_closed(metrics):
    import vl_convert as vlc
    with pytest.raises(ValueError, match='font metrics|font line metrics'):
        render._vertical_fit_svg(vlc, _line_fit_spec(), 440, 180, lambda item: metrics)


def test_exported_svg_operand_precision_matches_native_browser_transform_composition():
    svg = ('<svg><g transform="translate(112,1.0172413793065136)">'
        '<g transform="translate(0.5,0.5)"><text transform="translate(-2,9.48275862068978)" '
        'font-size="11px">DC Hamburg</text></g></g></svg>')
    # This exact original export is below 11; rounding the sum would conceal it.
    assert render._svg_text_positions(svg)[0]['baseline_y'] == 10.99999988079071


@pytest.mark.parametrize('attribute', ['stroke="red"', 'filter="url(#f)"', 'clip-path="url(#c)"',
    'transform="scale(2)"', 'style="font-size:11px"'])
def test_line_fit_rejects_unsupported_checked_node_paint_and_transforms(attribute):
    from types import SimpleNamespace
    graph = {'width': 100, 'height': 100, 'scenegraph': {'marktype': 'text', 'items': [{'text': 'x'}]}}
    vlc = SimpleNamespace(vegalite_to_scenegraph=lambda spec: graph)
    svg = '<svg><g ' + attribute + '><text transform="translate(5,12)">x</text></g></svg>'
    # Inline style on an ancestor must also fail closed, rather than overriding font metadata.
    with pytest.raises(ValueError, match='unsupported'):
        render._vertical_plaintext_overflow(vlc, {}, 100, 100, _line_metric_fixture, svg)


def test_line_fit_skips_rotated_nodes_and_no_text_needs_no_font_metadata():
    from types import SimpleNamespace
    graph = {'width': 100, 'height': 100, 'scenegraph': {'marktype': 'text', 'items': [{'text': 'x', 'angle': 90}]}}
    svg = '<svg><text transform="rotate(90)">x</text></svg>'
    vlc = SimpleNamespace(vegalite_to_scenegraph=lambda spec: graph, vegalite_to_svg=lambda spec: svg)
    result = render._vertical_plaintext_overflow(vlc, {}, 100, 100, lambda item: pytest.fail('rotated measured'), svg)
    assert result == {'top': 0, 'bottom': 0, 'measured': 0, 'skipped_rotated': 1}
    graph['scenegraph']['items'] = []
    vlc.vegalite_to_svg = lambda spec: '<svg/>'
    assert render._vertical_fit_svg(vlc, {}, 100, 100, lambda item: pytest.fail('no text')) == '<svg/>'


def test_line_fit_nonconvergence_is_red_with_measured_trace(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(render, '_vertical_plaintext_overflow',
                        lambda *args: {'top': 0.1, 'bottom': 0, 'measured': 1, 'skipped_rotated': 0})
    calls = []
    vlc = SimpleNamespace(vegalite_to_svg=lambda spec: calls.append(dict(spec)) or '<svg/>')
    with pytest.raises(ValueError, match='did not converge.*measured'):
        render._vertical_fit_svg(vlc, {}, 100, 100, _line_metric_fixture)
    assert len(calls) == 8


def test_static_native_line_fit_is_explicit_optin_and_legacy_bytes_equal():
    data = [{'c': 'North', 'v': 12}]
    kwargs = dict(bindings={'category': 'c', 'value': 'v'}, width=440, height=180)
    legacy = render.render_svg('bar_ranking', data, **kwargs)
    assert legacy == render.render_svg('bar_ranking', data, fit_text_lines=False, **kwargs)
    fitted = render.render_svg('bar_ranking', data, fit_text_lines=True, **kwargs)
    assert ET.fromstring(fitted).get('width') == '440'
    with pytest.raises(ValueError, match='requires fit_text_lines'):
        render.render_svg('bar_ranking', data, font_metrics_provider=_line_metric_fixture, **kwargs)



def test_line_fit_exhausted_canvas_is_red():
    # The metadata provider must not turn an impossible layout into success.
    import vl_convert
    with pytest.raises(ValueError, match='consume the canvas'):
        render._vertical_fit_svg(vl_convert, _line_fit_spec(), 440, 180,
            lambda item: {'ascent': 100000, 'descent': 100000, 'units_per_em': 1})


@pytest.mark.parametrize('flag', ['yes', 1, None])
def test_native_fit_flag_is_strict_boolean(flag):
    with pytest.raises(ValueError, match='must be boolean'):
        render.render_svg('bullet', [], fit_text_lines=flag)


@pytest.mark.parametrize('width', [280, 440])
def test_parent_above_label_native_tspans_keep_all_lines_and_original_layout(width):
    import copy
    import vl_convert as vlc
    name = 'Household supplies and international cleaning equipment'
    data = [{'k': name, 'v': -20}, {'k': 'Zero', 'v': 0},
            {'k': 'Missing', 'v': None}, {'k': 'Positive', 'v': 40}]
    kwargs = dict(bindings={'category': 'k', 'value': 'v'}, params={'label_position': 'above'},
                  width=width, height=240)
    legacy = render.render_svg('bar_ranking', data, **kwargs)
    assert legacy == render.render_svg('bar_ranking', data, fit_text_lines=False, **kwargs)
    fitted = render.render_svg('bar_ranking', data, fit_text_lines=True, **kwargs)
    lines = [n.text for n in ET.fromstring(fitted).iter() if n.tag.endswith('tspan')]
    assert len(lines) >= 2 and ' '.join(lines) == name
    spec = json.loads(render.render_target('bar_ranking', 'html_vegalite',
        bindings=kwargs['bindings'], params=kwargs['params'])[0])
    spec.update(width=width, height=240, datasets={'dataset': data},
                autosize={'type': 'fit', 'contains': 'padding'})
    saved = copy.deepcopy(spec)
    raw = render._vertical_fit_svg(vlc, spec, width, 240, render.native_font_line_metrics)
    overflow = render._vertical_plaintext_overflow(vlc, spec, width, 240, render.native_font_line_metrics, raw)
    assert overflow['measured'] == 8 and overflow['top'] == overflow['bottom'] == 0
    # Parent's wrapper, line height, anchors and all governed encodings survive.
    assert {key: value for key, value in spec.items() if key != 'padding'} == {
        key: value for key, value in saved.items() if key != 'padding'}


def test_tspan_baselines_use_exported_y_and_dy_not_scenegraph_lineheight():
    svg = ('<svg><g transform="translate(0,10.25)"><text transform="translate(0,2.5)" font-size="11px">'
           '<tspan>A</tspan><tspan x="0" dy="18">B</tspan>'
           '<tspan x="0" y="4" dy="2">C</tspan></text></g></svg>')
    record = render._svg_text_positions(svg)[0]
    assert not record['unsupported']
    assert [line['baseline_y'] for line in record['lines']] == [12.75, 30.75, 18.75]


@pytest.mark.parametrize('span', ['<tspan font-size="20px">x</tspan>',
    '<tspan font-weight="700">x</tspan>', '<tspan style="fill:red">x</tspan>',
    '<tspan><tspan>x</tspan></tspan>', '<tspan transform="translate(0,2)">x</tspan>'])
def test_mixed_or_arbitrary_tspan_blocks_fail_closed(span):
    from types import SimpleNamespace
    graph = {'width': 100, 'height': 100, 'scenegraph': {
        'marktype': 'text', 'items': [{'text': ['x']}]}}
    vlc = SimpleNamespace(vegalite_to_scenegraph=lambda spec: graph)
    with pytest.raises(ValueError, match='unsupported'):
        render._vertical_plaintext_overflow(vlc, {}, 100, 100, _line_metric_fixture,
            '<svg><text transform="translate(0,12)" font-size="11px">' + span + '</text></svg>')


def test_actual_native_default_provider_fit_off_is_a_line_edge_negative_control():
    import vl_convert as vlc
    spec = _line_fit_spec()
    off = render._vertical_plaintext_overflow(vlc, spec, 440, 180,
        render.native_font_line_metrics, vlc.vegalite_to_svg(spec))
    assert off['measured'] > 0 and off['top'] + off['bottom'] > 0
    fitted = render._vertical_fit_svg(vlc, spec, 440, 180, render.native_font_line_metrics)
    on = render._vertical_plaintext_overflow(vlc, spec, 440, 180, render.native_font_line_metrics, fitted)
    assert on['measured'] == off['measured'] and on['top'] == on['bottom'] == 0
