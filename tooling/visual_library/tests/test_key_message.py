"""Kernaussage je Visual (D-638 Nachtrag in Freelancing, feat-109): Regeln und Hervorhebung.

Gemessen wird am gezeichneten Chart (Vega-Szenengraph): mit `kernaussage` aus ist jede Marke voll
deckend, mit an nur die Treffer. Gegenprobe: ohne den Parameter bleibt die Spec unverändert.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import key_message as K  # noqa: E402
import render  # noqa: E402

REGIONS = {"columns": [{"name": "Region"}, {"name": "Wert"}],
           "rows": [["DACH", 24.4], ["Benelux", 27.8], ["Nordics", 31.4], ["Southern Europe", 34.5]]}
CAUSES = {"columns": [{"name": "Ursache"}, {"name": "Beitrag"}],
          "rows": [["Conversion", 34], ["Out-of-Stock", 27], ["Saison", 16], ["Kampagne", 13], ["Sonstige", 10]]}
WEEKS = {"columns": [{"name": "Periode"}, {"name": "Ist"}, {"name": "Plan"}],
         "rows": [["2025-12-22", 33.5, 45.0], ["2025-12-29", 33.9, 45.0], ["2026-01-05", 33.6, 45.0]]}


# --- Regeln ------------------------------------------------------------------------------------

def test_quote_nennt_schwaechsten_und_staerksten_wert_nach_richtung():
    m = K.key_message(REGIONS, {"category": "Region", "value": "Wert"}, unit="%")
    assert K.plain_text(m) == "Am schwächsten: DACH mit 24,4 %, am stärksten: Southern Europe mit 34,5 %."
    assert m["highlight"] == {"field": "Region", "values": ["DACH"], "temporal": False}
    # Gegenprobe: weniger ist besser (Kosten) dreht die Aussage
    low = K.key_message(REGIONS, {"category": "Region", "value": "Wert"}, polarity=-1, unit="%")
    assert low["highlight"]["values"] == ["Southern Europe"]


def test_beitrag_nennt_den_groessten_mit_anteil():
    m = K.key_message(CAUSES, {"category": "Ursache", "value": "Beitrag"}, additive=True)
    assert K.plain_text(m) == "Größter Beitrag: Conversion mit 34, das sind 34 % der Summe."
    assert [s["text"] for s in m["segments"] if s["strong"]] == ["Conversion", "34", "34 %"]


def test_zeit_gegen_plan_in_prozentpunkten():
    m = K.key_message(WEEKS, {"time": "Periode", "value": "Ist", "plan": "Plan"}, unit="%", weekly=True)
    assert K.plain_text(m) == "KW 02: Ist 33,6 % gegen Plan 45,0 %, 11,4 PP unter Plan."
    assert m["highlight"] == {"field": "Periode", "values": ["2026-01-05"], "temporal": True}


def test_zeit_ohne_plan_erste_gegen_letzte_periode():
    m = K.key_message(WEEKS, {"time": "Periode", "value": "Ist"}, unit="%", weekly=True)
    assert K.plain_text(m) == "KW 52 bis KW 02: 33,5 % auf 33,6 %, +0,1 PP."


def test_eine_nachkommastelle_wie_am_chart_und_unveraendert_statt_null():
    t = {"columns": WEEKS["columns"], "rows": [["2025-12-22", 27.95, 35.0], ["2026-01-05", 27.95, 35.0]]}
    m = K.key_message(t, {"time": "Periode", "value": "Ist", "plan": "Plan"}, unit="%", weekly=True)
    assert "Ist 27,9\u00a0% gegen Plan 35,0\u00a0%, 7,1\u00a0PP" in K.plain_text(m), "eine Stelle, gerundet wie Vega"
    flat = K.key_message(t, {"time": "Periode", "value": "Ist"}, unit="%", weekly=True)
    assert K.plain_text(flat) == "KW 52 bis KW 02: unverändert bei 27,9\u00a0%."


def test_genannte_werte_in_uebrige_tragen_den_hinweis():
    """BO-007 (Entscheidung Florian 01.10.2026): das Chart zeigt Top 3, „am stärksten“ steckt in „Übrige“."""
    t = {"columns": REGIONS["columns"], "rows": [["Nordics", 43.41], ["Benelux", 38.36], ["DACH", 32.99],
                                                 ["Southern Europe", 24.49], ["CEE", 22.42]]}
    m = K.key_message(t, {"category": "Region", "value": "Wert"}, unit="%", top_n=3)
    assert K.plain_text(m) == ("Am schwächsten: CEE mit 22,4\u00a0%, am stärksten: Nordics (in „Übrige“) "
                               "mit 43,4\u00a0%.")
    alle = K.key_message(t, {"category": "Region", "value": "Wert"}, unit="%", top_n=5)
    assert "Übrige" not in K.plain_text(alle), "Gegenprobe: alle sichtbar, kein Hinweis"


def test_verteilung_nennt_median_quartile_und_ausreisser():
    t = {"columns": [{"name": "Filiale"}, {"name": "Marge"}],
         "rows": [["A", 31.2], ["B", 28.4], ["C", 30.1], ["D", 29.7], ["E", 12.5], ["F", 30.8], ["G", 29.9],
                  ["H", 31.0]]}
    m = K.key_message(t, {"category": "Filiale", "value": "Marge"}, unit="%", purpose="distribution")
    assert K.plain_text(m).startswith("Median 30,0\u00a0%, die mittlere Hälfte liegt zwischen 29,4\u00a0%")
    assert "Auffällig: E mit 12,5\u00a0%" in K.plain_text(m) and m["highlight"]["values"] == ["E"]
    # Gegenprobe: ohne Zweck „distribution“ greift der Kategorienvergleich
    assert K.key_message(t, {"category": "Filiale", "value": "Marge"})["rule"] == "schwächster Wert"


def test_zusammenhang_nennt_r_staerke_und_richtung():
    t = {"columns": [{"name": "Preis"}, {"name": "Absatz"}],
         "rows": [[10, 200], [12, 171], [14, 182], [16, 150], [18, 158], [20, 128]]}
    m = K.key_message(t, {"x": "Preis", "y": "Absatz"})
    assert K.plain_text(m) == "Zusammenhang zwischen Preis und Absatz: r = \u22120,91 (stark, negativ), 6 Punkte."


def test_keine_regel_keine_aussage():
    assert K.key_message(REGIONS, {"value": "Wert"}) is None
    flat = {"columns": REGIONS["columns"], "rows": [["A", 1], ["B", 1]]}
    assert K.key_message(flat, {"category": "Region", "value": "Wert"}) is None, "ohne Unterschied keine Aussage"


def test_deutsche_zahlen():
    assert K.de_number(1234.5, 1) == "1.234,5"
    assert K.de_number(-0.4, 1) == "−0,4"
    assert K.de_number(-0.01, 1) == "0,0"
    assert K.de_number(2, 0, signed=True) == "+2"


def test_englische_zahlen_und_saetze():
    assert K.en_number(1234.5, 1) == "1,234.5"
    assert K.en_number(-0.4, 1) == "\u22120.4"
    assert K.en_number(-0.01, 1) == "0.0"
    assert K.fmt_number(1234.5, 1, lang="de") == K.de_number(1234.5, 1), "de unverändert"
    m = K.key_message(WEEKS, {"time": "Periode", "value": "Ist", "plan": "Plan"}, unit="%", weekly=True, lang="en")
    assert K.plain_text(m) == "Week 02: actual 33.6% vs. plan 45.0%, 11.4\u00a0pp below plan."
    assert m["rule"] == "letzte Periode gegen Plan", "rule ist Schlüssel, nicht Text"
    assert K.period_label("2026-01-31", lang="en") == "2026-01-31"


def test_unbekannte_sprache_wirft():
    with pytest.raises(ValueError):
        K.key_message(REGIONS, {"category": "Region", "value": "Wert"}, lang="fr")


# --- Hervorhebung am gezeichneten Chart --------------------------------------------------------

def _opacities(idiom: str, roles: dict, rows: list[dict], highlight: dict | None, on: bool) -> dict:
    vlc = pytest.importorskip("vl_convert")
    params = {"highlight": highlight} if highlight else None
    spec = json.loads(render.render_target(idiom, "html_vegalite", "ibcs", bindings=roles, params=params)[0])
    spec["data"] = {"values": rows}
    spec["width"], spec["height"] = 300, 200
    if highlight:
        spec["params"] = [{**p, "value": on} if p["name"] == render.KEY_PARAM else p for p in spec["params"]]
    out: dict = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("role") == "mark" and node.get("marktype") in ("rect", "symbol"):
                for it in node.get("items", []):
                    out.setdefault(node["marktype"], []).append(round(it.get("opacity", 1), 2))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(spec))
    return out


BARS = [{"Region": r, "Wert": v} for r, v in REGIONS["rows"]]


def test_balken_aus_alle_deckend_an_nur_der_treffer():
    h = {"field": "Region", "values": ["DACH"], "temporal": False}
    roles = {"category": "Region", "value": "Wert"}
    assert set(_opacities("bar_ranking", roles, BARS, h, on=False)["rect"]) == {1}
    on = _opacities("bar_ranking", roles, BARS, h, on=True)["rect"]
    assert sorted(on) == [render.KEY_DIM] * 3 + [1], on


def test_zeitreihe_hebt_die_letzte_periode_hervor():
    rows = [{"Periode": p, "Ist": a, "Plan": pl} for p, a, pl in WEEKS["rows"]]
    roles = {"time": "Periode", "value": "Ist", "plan": "Plan"}
    h = {"field": "Periode", "values": ["2026-01-05"], "temporal": True}
    sym = _opacities("line", roles, rows, h, on=True).get("symbol", [])
    # zwei Reihen (Ist, Plan) je drei Punkte: je Reihe genau einer deckend
    assert sorted(sym) == [render.KEY_DIM] * 4 + [1, 1], sym


def test_ohne_parameter_bleibt_die_spec_unveraendert():
    roles = {"category": "Region", "value": "Wert"}
    plain = render.render_target("bar_ranking", "fabric_app", "ibcs", bindings=roles)[0]
    assert render.KEY_PARAM not in plain


# --- Gleichstand Python ↔ TypeScript (die Oberfläche rechnet auf der gefilterten Tabelle nach) ----

CASES = REPO_ROOT / "tooling" / "visual_library" / "key_message_cases.json"
TS = REPO_ROOT / "tooling" / "visual_library" / "key_message.ts"


def _python_results() -> dict:
    out = {}
    for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]:
        m = K.key_message(c["table"], c["roles"], **c["opts"])
        out[c["name"]] = m and {**m, "keys": K.highlight_keys(m["highlight"])}
    return out


def test_englische_faelle_tragen_den_erwarteten_satz():
    cases = [c for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"] if c["opts"].get("lang") == "en"]
    for c in cases:
        m = K.key_message(c["table"], c["roles"], **c["opts"])
        assert (m and K.plain_text(m)) == c["expect"], c["name"]
    rules = {K.key_message(c["table"], c["roles"], **c["opts"])["rule"] for c in cases if c["expect"]}
    assert rules == {"schwächster Wert", "größter Beitrag", "letzte Periode gegen Plan", "Veränderung im Zeitraum",
                     "Verteilung", "Zusammenhang"}, "jede Regel hat einen englischen Fall"
    assert any("(in \u201cOther\u201d)" in (c["expect"] or "") for c in cases), "Restzeilen-Hinweis englisch"


def _node_eval(script: str) -> "subprocess.CompletedProcess[str]":
    node = shutil.which("node")
    if not node:
        pytest.skip("node fehlt — Gleichstand nicht geprüft")
    return subprocess.run([node, "--experimental-strip-types", "--no-warnings", "--input-type=commonjs", "-e",
                           f"(async () => {{ {script} }})().catch((e) => {{ console.error(e); process.exit(1); }})"],
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def test_ts_fassung_liefert_dasselbe_wie_python():
    script = (
        f"const K = await import({json.dumps(TS.as_uri())});"
        f"const doc = JSON.parse(require('fs').readFileSync({json.dumps(str(CASES))}, 'utf8'));"
        "const out = {}; for (const c of doc.cases) { const m = K.keyMessage(c.table, c.roles, c.opts);"
        " out[c.name] = m && { ...m, keys: K.highlightKeys(m.highlight) }; }"
        "process.stdout.write(JSON.stringify(out));"
    )
    run = _node_eval(script)
    assert run.returncode == 0, run.stderr
    ts, py = json.loads(run.stdout), _python_results()
    assert set(ts) == set(py)
    for name in py:
        assert ts[name] == py[name], name
    assert sum(1 for v in py.values() if v) >= 10, "die Fälle decken alle vier Regeln mit Aussage ab"
    assert sum(1 for v in py.values() if v is None) >= 4, "und die Fälle ohne Aussage"
    assert sum(1 for n in py if n.endswith("_en")) >= 15, "die englischen Fälle laufen mit durch Node"


def test_ts_fassung_wirft_bei_unbekannter_sprache():
    script = (
        f"const K = await import({json.dumps(TS.as_uri())});"
        "const t = {columns: [{name: 'R'}, {name: 'W'}], rows: [['A', 1], ['B', 2]]};"
        "let msg = 'kein Fehler'; try { K.keyMessage(t, {category: 'R', value: 'W'}, {lang: 'fr'}); }"
        " catch (e) { msg = 'wirft'; } process.stdout.write(msg);"
    )
    run = _node_eval(script)
    assert run.returncode == 0, run.stderr
    assert run.stdout == "wirft"


def test_werte_parameter_statt_konstante():
    roles = {"category": "Region", "value": "Wert"}
    spec = json.loads(render.render_target("bar_ranking", "fabric_app", "ibcs", bindings=roles,
                                           params={"highlight": {"field": "Region", "values": ["DACH"]}})[0])["spec"]
    params = {p["name"]: p["value"] for p in spec["params"]}
    assert params == {render.KEY_PARAM: False, render.KEY_VALUES: ["DACH"]}
    assert "DACH" not in json.dumps(spec).replace('"value": ["DACH"]', ""), "kein Treffer fest im Test"


# --- Hervorhebung ohne Zeilen (BO-054: Live-Charts entstehen vor den Daten) ----------------------

def _cases() -> list:
    return json.loads(CASES.read_text(encoding="utf-8"))["cases"]


def test_hervorhebung_ohne_zeilen_ist_die_der_regel():
    """Feld und Zeitart aus Rollen und Zweck allein = die der zeilenbasierten Aussage, für jeden Fall mit Aussage.
    Gegenprobe: Rollen ohne Regel liefern keine Hervorhebung."""
    geprueft = 0
    for c in _cases():
        m = K.key_message(c["table"], c["roles"], **c["opts"])
        h = K.key_highlight(c["roles"], c["opts"].get("purpose"))
        if m:
            assert h == {**m["highlight"], "values": []}, c["name"]
            geprueft += 1
    assert geprueft >= 10
    assert K.key_highlight({"value": "Wert"}) is None
    assert K.key_highlight({"category": "Region"}) is None


def test_ts_hervorhebung_ohne_zeilen_wie_python():
    script = (
        f"const K = await import({json.dumps(TS.as_uri())});"
        f"const doc = JSON.parse(require('fs').readFileSync({json.dumps(str(CASES))}, 'utf8'));"
        "const out = {}; for (const c of doc.cases) { out[c.name] = K.keyHighlight(c.roles, c.opts.purpose ?? null); }"
        "out._ohne = K.keyHighlight({value: 'W'}, null);"
        "process.stdout.write(JSON.stringify(out));"
    )
    run = _node_eval(script)
    assert run.returncode == 0, run.stderr
    ts = json.loads(run.stdout)
    py = {c["name"]: K.key_highlight(c["roles"], c["opts"].get("purpose")) for c in _cases()}
    py["_ohne"] = None
    assert ts == py


def _scene(spec: dict, rows: list[dict]) -> dict:
    vlc = pytest.importorskip("vl_convert")
    spec = {**spec, "data": {"values": rows}, "width": 300, "height": 200}
    return vlc.vegalite_to_scenegraph(spec)


@pytest.mark.parametrize("idiom,roles,table", [
    ("line", {"time": "Periode", "value": "Ist", "plan": "Plan"}, WEEKS),
    ("bar_ranking", {"category": "Region", "value": "Wert"}, REGIONS),
])
def test_live_spec_mit_nachgereichten_treffern_zeichnet_wie_die_zeilenbasierte(idiom, roles, table):
    """Die Spec ohne Zeilen trägt die Parameter; setzt die Oberfläche die Treffer aus der Tabelle, zeichnet sie
    Marke für Marke dasselbe wie die Spec, die mit den Zeilen erzeugt wurde (Szenengraph gleich)."""
    live = json.loads(render.render_target(idiom, "html_vegalite", "ibcs", bindings=roles,
                                           params={"highlight": K.key_highlight(roles)})[0])
    assert {p["name"]: p["value"] for p in live["params"] if p["name"].startswith("kern")} == {
        render.KEY_PARAM: False, render.KEY_VALUES: []}
    m = K.key_message(table, roles, unit="%")
    built = json.loads(render.render_target(idiom, "html_vegalite", "ibcs", bindings=roles,
                                            params={"highlight": m["highlight"]})[0])
    keys = K.highlight_keys(m["highlight"])
    for spec in (live, built):
        spec["params"] = [{**p, "value": True} if p["name"] == render.KEY_PARAM
                          else {**p, "value": keys} if p["name"] == render.KEY_VALUES else p for p in spec["params"]]
    rows = [dict(zip([c["name"] for c in table["columns"]], r)) for r in table["rows"]]
    assert _scene(live, rows) == _scene(built, rows)
    # Gegenprobe: ohne nachgereichte Treffer ist mit `kernaussage` an alles gedämpft — die Treffer tragen das Bild
    leer = json.loads(json.dumps(live))
    leer["params"] = [{**p, "value": []} if p["name"] == render.KEY_VALUES else p for p in leer["params"]]
    assert _scene(leer, rows) != _scene(live, rows)

@pytest.mark.parametrize("target", ["fabric_app", "html_vegalite"])
@pytest.mark.parametrize("bounds", [("#d8e4e5", "#f4fbf7"), ("#111923", "#253944")])
def test_outline_selection_keeps_glass_and_text_and_proves_every_stroke(target, bounds):
    vlc = pytest.importorskip("vl_convert")
    import contrast
    roles = {"category": "Region", "value": "Wert"}
    h = {"field": "Region", "values": ["DACH"], "style": "outline"}
    output = json.loads(render.render_target("bar_ranking", target, bindings=roles,
        params={"label_position": "above", "target_val": 30, "highlight": h}, background_bounds=bounds)[0])
    spec = output["spec"] if target == "fabric_app" else output
    if target == "fabric_app":
        spec["config"] = output["configVegaLite"]
    assert spec["usermeta"]["selectionHighlight"] == "outline"
    assert spec["config"]["background"] == "transparent"
    spec.update(width=400, height=240, data={"name": "dataset", "values": BARS})

    def scene(enabled):
        spec["params"] = [{**p, "value": enabled} if p["name"] == render.KEY_PARAM else p for p in spec["params"]]
        result = {"rect": [], "text": []}
        def walk(node):
            if isinstance(node, dict):
                if node.get("role") == "mark" and node.get("marktype") in result:
                    result[node["marktype"]].extend(i for i in node.get("items", []) if i.get("opacity", 1) != 0)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(vlc.vegalite_to_scenegraph(spec))
        return result

    normal, selected = scene(False), scene(True)
    assert len(normal["rect"]) == len(selected["rect"]) == 4
    assert {r.get("fillOpacity", 1) for r in normal["rect"]} == {1}
    assert sorted(r.get("fillOpacity", 1) for r in selected["rect"]) == [0, 0, 0, 1]
    assert {r.get("opacity", 1) for r in selected["rect"]} == {1}
    assert {r["strokeWidth"] for r in selected["rect"]} == {0.75}
    for before, after in zip(normal["rect"], selected["rect"]):
        geometry = ("x", "x2", "y", "width", "height")
        assert tuple(before.get(k) for k in geometry) == tuple(after.get(k) for k in geometry)
        assert before["fill"] == after["fill"] == after["stroke"], "Semantic bar colour survives in the outline"
        assert min(contrast.contrast_ratio_exact(after["stroke"], b) for b in bounds) >= 3
    assert normal["text"] == selected["text"], "No dimmed or rewritten labels"
    assert all(min(contrast.contrast_ratio_exact(t["fill"], b) for b in bounds) >= 4.5 for t in selected["text"])
    # The old alpha-dim recipe still fails the same Glass proof. It is not bypassed.
    with pytest.raises(render.BackgroundContrastError):
        render.render_target("bar_ranking", target, bindings=roles,
            params={"highlight": {**h, "style": "dim"}}, background_bounds=bounds)


def test_outline_selection_rejects_unsupported_style_and_dynamic_fallback_ink():
    base = json.loads(render.render_target("bar_ranking", "html_vegalite")[0])
    with pytest.raises(ValueError, match="style"):
        render.with_highlight(base, "Region", style="glow")
    with pytest.raises(ValueError, match="hex"):
        render.with_highlight(base, "Region", style="outline", ink="datum.colour")


def _native_opacity_rows(spec):
    import vl_convert as vlc
    output = {}
    def walk(mark):
        for item in mark.get('items', []):
            if mark.get('marktype') == 'group':
                for child in item.get('items', []):
                    walk(child)
            elif mark.get('marktype') == 'rect':
                output[item['description'].rsplit('category: ', 1)[1]] = item.get('opacity', 1)
    walk(vlc.vegalite_to_scenegraph(spec)['scenegraph'])
    return output


def _opacity_bar_spec(opacity=None, mark_opacity=None):
    mark = {'type': 'bar'}
    if mark_opacity is not None:
        mark['opacity'] = mark_opacity
    encoding = {'x': {'field': 'value', 'type': 'quantitative'},
                'y': {'field': 'category', 'type': 'nominal'}}
    if opacity is not None:
        encoding['opacity'] = opacity
    return {'width': 400, 'height': 240, 'mark': mark, 'encoding': encoding,
            'data': {'values': [
                {'category': 'A', 'value': 4, 'hidden': True, 'half': False},
                {'category': 'B', 'value': 3, 'hidden': False, 'half': True},
                {'category': 'C', 'value': 2, 'hidden': False, 'half': False},
                {'category': 'D', 'value': 1, 'hidden': True, 'half': True}]}}


def _selection_state(spec, enabled, values):
    import copy
    result = copy.deepcopy(spec)
    result['params'] = [{**p, 'value': enabled} if p['name'] == render.KEY_PARAM
        else {**p, 'value': values} if p['name'] == render.KEY_VALUES else p for p in result['params']]
    return result


def test_dim_multiplies_native_conditions_in_original_order_without_waking_hidden_marks():
    import copy
    opacity = {'condition': [
        {'test': {'field': 'hidden', 'equal': True}, 'value': 0},
        {'test': 'datum.half', 'value': 0.4}], 'value': 1}
    original = _opacity_bar_spec(opacity)
    saved = copy.deepcopy(original)
    highlighted = render.with_highlight(original, 'category', ['B'])
    baseline = _native_opacity_rows(original)
    assert baseline == {'A': 0, 'B': 0.4, 'C': 1, 'D': 0}
    for enabled, selected in [(False, []), (True, ['B']), (True, ['B', 'C']),
                              (True, ['A']), (False, [])]:
        measured = _native_opacity_rows(_selection_state(highlighted, enabled, selected))
        assert measured == {name: alpha * (render.KEY_DIM if enabled and name not in selected else 1)
                            for name, alpha in baseline.items()}
    assert original == saved


@pytest.mark.parametrize('hover_values', [None, [{'category': 'B'}]])
def test_dim_preserves_native_hover_param_empty_false_mask(hover_values):
    opacity = {'condition': {'param': 'hover', 'empty': False, 'value': 0.5}, 'value': 0}
    original = _opacity_bar_spec(opacity)
    hover = {'name': 'hover', 'select': {'type': 'point', 'fields': ['category']}}
    if hover_values is not None:
        hover['value'] = hover_values
    original['params'] = [hover]
    baseline = _native_opacity_rows(original)
    assert baseline == {'A': 0, 'B': 0.5 if hover_values else 0, 'C': 0, 'D': 0}
    highlighted = render.with_highlight(original, 'category', ['A'])
    for enabled, selected in [(False, []), (True, ['A']), (True, ['A', 'B']), (False, [])]:
        assert _native_opacity_rows(_selection_state(highlighted, enabled, selected)) == {
            name: alpha * (render.KEY_DIM if enabled and name not in selected else 1)
            for name, alpha in baseline.items()}


@pytest.mark.parametrize('alpha', [0, 0.4, 0.5, 0.7, 1])
@pytest.mark.parametrize('source', ['channel', 'mark', 'expr'])
def test_dim_preserves_literal_expr_and_mark_level_opacity(alpha, source):
    opacity = {'value': {'expr': str(alpha)} if source == 'expr' else alpha} if source != 'mark' else None
    original = _opacity_bar_spec(opacity, alpha if source == 'mark' else None)
    baseline = _native_opacity_rows(original)
    assert set(baseline.values()) == {alpha}
    highlighted = render.with_highlight(original, 'category', ['B'])
    for enabled, selected in [(False, []), (True, ['B']), (True, ['A', 'C']), (False, [])]:
        assert _native_opacity_rows(_selection_state(highlighted, enabled, selected)) == {
            name: value * (render.KEY_DIM if enabled and name not in selected else 1)
            for name, value in baseline.items()}


@pytest.mark.parametrize('opacity', [{'field': 'value', 'type': 'quantitative'},
    {'datum': 0.4}, {'condition': {'test': 'datum.hidden', 'field': 'value'}, 'value': 1}])
def test_dim_unrepresented_opacity_mapping_fails_closed_instead_of_assuming_one(opacity):
    with pytest.raises(ValueError, match='value-defined'):
        render.with_highlight(_opacity_bar_spec(opacity), 'category', ['A'])


@pytest.mark.parametrize('background', [None, '#11242f'])
def test_dim_keeps_null_hidden_and_literal_data_zero_visible_in_all_selection_states(background):
    import vl_convert as vlc
    import xml.etree.ElementTree as ET
    rows = [{'category': 'North', 'value': 10}, {'category': 'Zero', 'value': 0},
            {'category': 'Null', 'value': None}]
    roles = {'category': 'category', 'value': 'value'}
    params = {'label_position': 'above', 'highlight': {'field': 'category', 'values': ['North']}}
    spec = json.loads(render.render_target('bar_ranking', 'html_vegalite', bindings=roles,
        params=params, background=background)[0])
    spec.update(width=400, height=240, datasets={'dataset': rows},
                autosize={'type': 'fit', 'contains': 'padding'})
    for enabled, selected in [(False, []), (True, ['North']), (True, ['North', 'Zero']),
                              (True, ['Null']), (False, [])]:
        current = _selection_state(spec, enabled, selected)
        svg = render._vertical_fit_svg(vlc, current, 400, 240, render.native_font_line_metrics)
        root = ET.fromstring(svg)
        texts = [node for node in root.iter() if node.tag.endswith('text')]
        nan = [node for node in texts if node.text == 'NaN']
        assert nan and all(float(node.get('opacity', '1')) == 0 for node in nan)
        zeros = [node for node in texts if node.text == '0']
        assert zeros and all(float(node.get('opacity', '1')) > 0 for node in zeros)
        assert root.get('width') == '400' and root.get('height') == '240'
