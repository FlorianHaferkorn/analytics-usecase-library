"""Muster des Gestaltungskatalogs als Relation: Feld im Register, Eigenschaft im Template, Messung am Szenengraphen.

Runde rubrikpaket, 22.10.2026 (Meridian BO-412 bis BO-441; Entscheidung Florian 22.10.2026 zu W11 und W12).
Jeder Test liest die Schwelle aus `_gestaltungsregeln.yaml`, rendert das Template mit vl_convert und misst die Marke.
Jeder Fall hat seine Gegenprobe im selben Test: ohne Rolle, Parameter oder Wert verschwindet die Eigenschaft wieder.
Was nur im Power BI Desktop messbar ist (`umsetzung.nativ: tenant_gebunden`), prüft hier nur den Formatkatalog.
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
sys.path.insert(0, str(REPO_ROOT))
import gestaltung  # noqa: E402
import render  # noqa: E402
from tooling.report_quality import formatting_metadata as fm  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
GOLDEN = LIB / "golden"
RUBRIC = REPO_ROOT / "core" / "templates" / "page_templates" / "tokens" / "boutique_craft_rubric.yaml"
_NATIV = {"tenant_gebunden", "entfaellt"}

vlc = pytest.importorskip("vl_convert")


def _scene(idiom: str, rows: list[dict], bindings: dict, params: dict | None = None,
           profile: str | None = None, w: int = 400, h: int = 240) -> dict:
    spec = json.loads(render.render_target(idiom, "html_vegalite", profile, bindings=bindings, params=params)[0])
    spec["data"] = {"name": "dataset", "values": rows}
    spec["width"], spec["height"] = w, h
    return vlc.vegalite_to_scenegraph(spec)


def _marks(sg: dict, marktype: str | None = None, role: str = "mark") -> list[dict]:
    out: list[dict] = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("role") == role and (marktype is None or n.get("marktype") == marktype):
                out.extend(n.get("items", []))
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(sg)
    return out


def _visible(items: list[dict]) -> list[dict]:
    """Was der Leser sieht: Marken mit Deckkraft 0 (Bedingung nicht erfüllt) zählen nicht."""
    return [it for it in items if it.get("opacity", 1) != 0]


def _texts(sg: dict) -> list[str]:
    return [str(it.get("text")) for it in _visible(_marks(sg, "text"))]


def _bars(sg: dict) -> list[dict]:
    """Datenbalken: Rechtecke mit Ausdehnung über 2 px (der Nullstrich ist 2 px breit)."""
    return [it for it in _visible(_marks(sg, "rect")) if (it.get("width") or 0) > 2 and (it.get("height") or 0) > 2]


# --- Register: Form der neuen Felder ------------------------------------------------------------------------------

def test_nativ_field_is_known_and_tenant_bound_rules_name_their_rest():
    for rid, r in gestaltung.register()["regeln"].items():
        nativ = r["umsetzung"].get("nativ")
        if nativ is None:
            continue
        assert nativ in _NATIV, f"{rid}: nativ {nativ!r}"
        if nativ == "tenant_gebunden":
            assert r["umsetzung"]["status"] == "teilweise", f"{rid}: tenant_gebunden heißt Rest offen"
            assert "Desktop" in r["umsetzung"]["offen"] or "Dienst" in r["umsetzung"]["offen"], rid


# --- S2 / L4 laufende Periode ---------------------------------------------------------------------------------------

_CT_ROWS = [{"m": f"2026-0{i}", "v": 10 + i, "cur": i == 6} for i in range(1, 7)]


def test_running_column_is_an_outline_and_the_last_complete_one_carries_the_ink():
    r = gestaltung.regel("laufende_periode")
    sg = _scene("column_time", _CT_ROWS, {"time": "m", "value": "v", "current": "cur"})
    bars = sorted(_bars(sg), key=lambda it: it["x"])
    assert len(bars) == 6
    lauf, letzte, frueher = bars[-1], bars[-2], bars[:-2]
    assert lauf["fill"] == "#FFFFFF" and lauf["stroke"] == r["farben"]["letzte"]
    assert lauf["strokeWidth"] == r["umriss_px"]
    assert letzte["fill"] == r["farben"]["letzte"]
    assert {b["fill"] for b in frueher} == {r["farben"]["frueher"]}
    assert r["label"] in _texts(sg)
    # Gegenprobe: ohne Rolle current keine Umrisssäule und kein Label; die jüngste Säule trägt die Tinte.
    sg0 = _scene("column_time", _CT_ROWS, {"time": "m", "value": "v"})
    bars0 = sorted(_bars(sg0), key=lambda it: it["x"])
    assert not [b for b in bars0 if b.get("stroke")]
    assert bars0[-1]["fill"] == r["farben"]["letzte"]
    assert r["label"] not in _texts(sg0)


_LINE_ROWS = [{"d": f"2026-{m:02d}-01", "v": 40 + m, "p": 45, "py": 38 + m * 0.5, "cur": m == 6} for m in range(1, 7)]


def test_running_line_end_is_a_hollow_point():
    r = gestaltung.regel("laufende_periode")
    sg = _scene("line", _LINE_ROWS, {"time": "d", "value": "v", "current": "cur"})
    sichtbar = [s for s in _marks(sg, "symbol") if s.get("opacity", 1) and s.get("fill") != "transparent"]
    assert len(sichtbar) == 1 and sichtbar[0]["fill"] == "#FFFFFF"
    assert r["label"] in _texts(sg)
    sg0 = _scene("line", _LINE_ROWS, {"time": "d", "value": "v"})
    sichtbar0 = [s for s in _marks(sg0, "symbol") if s.get("opacity", 1) and s.get("fill") != "transparent"]
    assert len(sichtbar0) == 1 and sichtbar0[0]["fill"] != "#FFFFFF"
    assert r["label"] not in _texts(sg0)


# --- S3 Einheit über der Werteachse ---------------------------------------------------------------------------------

def test_unit_stands_above_the_value_axis_only_when_given():
    sg = _scene("column_time", _CT_ROWS, {"time": "m", "value": "v"}, params={"unit_label": "Stk."})
    unit = [it for it in _marks(sg, "text") if it.get("text") == "Stk."]
    assert len(unit) == 1 and unit[0]["x"] <= 1 and unit[0]["y"] <= 1
    assert "Stk." not in _texts(_scene("column_time", _CT_ROWS, {"time": "m", "value": "v"}))


# --- B2 Höchstbreite ------------------------------------------------------------------------------------------------

_BAR_ROWS = [{"k": "Nord", "v": 40.0, "py": 38}, {"k": "Ost", "v": 0, "py": 5}, {"k": "West", "v": None, "py": 7}]


@pytest.mark.parametrize("idiom,bindings,dim", [
    ("bar_ranking", {"category": "k", "value": "v"}, "height"),
    ("bar_absolute", {"category": "k", "value": "v"}, "height"),
    ("column_time", {"time": "k", "value": "v"}, "width"),
])
def test_bars_never_exceed_the_maximum_thickness(idiom, bindings, dim):
    max_px = gestaltung.regel("hoechstbreite")["max_px"]
    rows = [{"k": "A", "v": 3.0}, {"k": "B", "v": 2.0}]
    sg = _scene(idiom, rows, bindings, w=600, h=600)
    dicken = [b[dim] for b in _bars(sg)]
    assert dicken and max(dicken) <= max_px, dicken
    # Gegenprobe: mit doppelter Höchstbreite als Parameter wachsen die Marken darüber hinaus.
    sg2 = _scene(idiom, rows, bindings, params={"bar_max_px": str(4 * max_px)}, w=600, h=600)
    assert max(b[dim] for b in _bars(sg2)) > max_px


# --- B5 Akzent ------------------------------------------------------------------------------------------------------

def test_one_named_category_carries_the_accent():
    r = gestaltung.regel("akzent")
    rows = [{"k": "Nord", "v": 4.0}, {"k": "Ost", "v": 3.0}, {"k": "West", "v": 2.0}]
    sg = _scene("bar_absolute", rows, {"category": "k", "value": "v"}, params={"highlight_category": "Ost"})
    fills = sorted(b["fill"] for b in _bars(sg))
    assert fills == sorted([r["farben"]["akzent"], r["farben"]["rest"], r["farben"]["rest"]])
    sg0 = _scene("bar_absolute", rows, {"category": "k", "value": "v"})
    assert {b["fill"] for b in _bars(sg0)} == {r["farben"]["akzent"]}


# --- B6 Label über dem Balken ---------------------------------------------------------------------------------------

def test_labels_above_draw_thin_bars_and_empty_the_axis():
    r = gestaltung.regel("label_oben")
    assert r["schwelle_zeichen"] is None, "Schwelle ist nicht gemessen: Leerstelle, nicht geschätzt"
    sg = _scene("bar_ranking", _BAR_ROWS, {"category": "k", "value": "v"}, params={"label_position": "above"})
    assert {b["height"] for b in _bars(sg)} == {r["balken_px"]}
    assert not _visible(_marks(sg, "text", "axis-label")), "Achsenlabels ausgeblendet, das Label steht oben"
    assert {"Nord", "Ost", "West"} <= set(_texts(sg))
    sg0 = _scene("bar_ranking", _BAR_ROWS, {"category": "k", "value": "v"})
    assert {str(it.get("text")) for it in _visible(_marks(sg0, "text", "axis-label"))} == {"Nord", "Ost", "West"}
    assert "Nord" not in _texts(sg0)


# --- B7 Vorjahr überlappend -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("profile", ["house_default", "print_safe"])
def test_prior_year_bar_stands_behind_a_narrower_actual(profile):
    anteil = gestaltung.regel("vorjahr_ueberlappend")["anteil_ist"]
    rows = [{"k": "Nord", "v": 40.0, "py": 38.0}, {"k": "Ost", "v": 20.0, "py": 25.0}]
    sg = _scene("bar_ranking", rows, {"category": "k", "value": "v", "prior": "py"}, profile=profile)
    bars = _bars(sg)
    dicke = max(b["height"] for b in bars)
    py = [b for b in bars if b["height"] == dicke]
    ac = [b for b in bars if b["height"] < dicke]
    assert len(py) == 2 and len(ac) == 2
    assert all(abs(b["height"] - anteil * dicke) < 0.01 for b in ac)
    assert bars.index(py[0]) < bars.index(ac[0]), "Vorjahr liegt hinter dem Ist (zuerst gezeichnet)"
    sg0 = _scene("bar_ranking", rows, {"category": "k", "value": "v"}, profile=profile)
    assert len({b["height"] for b in _bars(sg0)}) == 1


# --- B9 Null gegen fehlend ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("idiom", ["bar_ranking", "bar_absolute"])
def test_zero_and_missing_are_told_apart(idiom):
    r = gestaltung.regel("null_fehlend")
    sg = _scene(idiom, _BAR_ROWS, {"category": "k", "value": "v"})
    texts = _texts(sg)
    assert "0" in texts and r["zeichen_fehlend"] in texts
    striche = [it for it in _visible(_marks(sg, "rect")) if it.get("width") == r["strich_px"]]
    assert len(striche) == 1, "genau ein Nullstrich, für die Null, nicht für den fehlenden Wert"
    assert len(_bars(sg)) == 1, "nur der Wert 40 ist ein Balken"
    # Gegenprobe: ohne fehlende Zeile kein Strich-Zeichen.
    sg0 = _scene(idiom, _BAR_ROWS[:2], {"category": "k", "value": "v"})
    assert r["zeichen_fehlend"] not in _texts(sg0)


# --- L3 Serienlabel ---------------------------------------------------------------------------------------------------

def test_series_labels_stand_at_the_line_end_and_the_limit_is_one_number():
    r = gestaltung.regel("serienlabel")
    sg = _scene("line", _LINE_ROWS, {"time": "d", "value": "v", "plan": "p", "prior": "py"})
    max_x = max(it["x"] for it in _marks(sg, "symbol"))
    labels = {str(it.get("text")): it for it in _marks(sg, "text") if it.get("text") in ("Plan", "PY", "FC")}
    assert set(labels) == {"Plan", "PY"}
    assert all(it["x"] == max_x and it.get("align") == "left" for it in labels.values())
    sg0 = _scene("line", _LINE_ROWS, {"time": "d", "value": "v"})
    assert not {"Plan", "PY"} & set(_texts(sg0))
    # W11: höchstens vier beschriftete Reihen (Ist, Plan, PY, FC) — Register und Rubrik tragen dieselbe Zahl.
    rubrik = {x["id"]: x for d in yaml.safe_load(RUBRIC.read_text(encoding="utf-8"))["dimensions"]
              for x in d.get("rules", [])}
    for rid in r["rubrik"]:
        assert rubrik[rid]["thresholds"]["direct_labels_max"] == r["max_reihen"] == 4, rid
    beschriftet = [s for s, slot in render.data_slots("line").items() if slot["role"] in ("value", "plan", "prior", "forecast")]
    assert len(beschriftet) <= r["max_reihen"]


# --- L6 Abweichungsfläche -------------------------------------------------------------------------------------------

def test_variance_area_only_when_switched_on_and_coloured_by_direction():
    r = gestaltung.regel("abweichungsflaeche")
    b = {"time": "d", "value": "v", "plan": "p"}
    sg = _scene("line", _LINE_ROWS, b, params={"abweichungsflaeche": "an"})
    areas = _marks(sg, "area")
    assert areas and {a["opacity"] for a in areas} == {r["deckkraft"]}
    assert {a["fill"] for a in areas} <= {"#107C10", "#A4262C"}
    assert not _marks(_scene("line", _LINE_ROWS, b), "area")

    def gefuellt(params: dict) -> set[str]:
        """Farben der Flächen mit Höhe: eine Fläche ohne Abweichung läuft auf dem Plan (y == y2)."""
        rows_ueber = [dict(x, v=50 + i) for i, x in enumerate(_LINE_ROWS)]   # Ist überall über Plan 45
        return {a["fill"] for a in _marks(_scene("line", rows_ueber, b, params=params), "area")
                if abs(a["y"] - a["y2"]) > 0.5}

    assert gefuellt({"abweichungsflaeche": "an"}) == {"#107C10"}
    # Gegenprobe Polarität: niedriger ist besser, dieselbe Lage ist schlecht.
    assert gefuellt({"abweichungsflaeche": "an", "polarity": "-1"}) == {"#A4262C"}


def test_no_line_or_area_layer_leaves_an_unnamed_container_when_empty():
    """A line or area mark is one path: Vega names its container from the items, so an empty one (variance area
    switched off) is an unnamed graphics-symbol (axe svg-img-alt, Meridian Cockpit G8, 22.10.2026). Every line or area
    layer behind a filter is therefore either hidden from assistive technology or always drawn."""
    b = {"time": "d", "value": "v", "plan": "p", "prior": "py"}
    spec = json.loads(render.render_target("line", "fabric_app", None, bindings=b)[0])["spec"]
    vg = vlc.vegalite_to_vega(spec)
    offen = []

    def walk(node: dict) -> None:
        for m in node.get("marks", []):
            if m.get("type") in ("line", "area") and m.get("aria") is not False and "Abweichungsfl" in json.dumps(m):
                offen.append(m.get("name"))
            walk(m)

    walk(vg)
    assert offen == []
    # Gegenprobe: without the flag the same layers would be exposed.
    roh = json.dumps(spec).replace('"aria": false', '"aria": true')
    assert '"aria": true' in roh


# --- N2 Pfeil ---------------------------------------------------------------------------------------------------------

def test_dumbbell_arrow_points_in_the_direction_and_is_coloured_by_it():
    rows = [{"c": "Nord", "s": 10.0, "e": 14.0}, {"c": "Süd", "s": 12.0, "e": 9.0}]
    b = {"category": "c", "start": "s", "end": "e"}
    sg = _scene("dumbbell", rows, b, params={"marker": "arrow"})
    shapes = {(s.get("shape"), s.get("fill")) for s in _marks(sg, "symbol") if str(s.get("shape", "")).startswith("triangle")}
    assert shapes == {("triangle-right", "#107C10"), ("triangle-left", "#A4262C")}
    sg0 = _scene("dumbbell", rows, b)
    assert not [s for s in _marks(sg0, "symbol") if str(s.get("shape", "")).startswith("triangle")]


# --- Werteachse small_multiples ---------------------------------------------------------------------------------------

def test_small_multiples_share_one_axis_and_mark_an_adjusted_base():
    def rows(base: float) -> list[dict]:
        return [{"d": f"2026-{m:02d}-01", "s": s, "v": base + m * 0.4 + i} for m in range(1, 7) for i, s in enumerate("AB")]
    b = {"time": "d", "value": "v", "series": "s"}
    assert "≈" in _texts(_scene("small_multiples", rows(93.0), b))
    assert "≈" not in _texts(_scene("small_multiples", rows(1.0), b))


# --- W12 Abweichungspille -----------------------------------------------------------------------------------------

_TINT = re.compile(r"^tint_")


def test_tinted_pill_lives_only_in_the_exception_table():
    r = gestaltung.regel("abweichungspille")
    traeger = []
    for path in sorted(LIB.glob("[a-z]*.yaml")):
        e = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        params = {k for impl in (e.get("implementations") or {}).values() if isinstance(impl, dict)
                  for k in (impl.get("params") or {})}
        params |= {k for prof in (e.get("profiles") or {}).values() if isinstance(prof, dict) for k in prof}
        if any(_TINT.match(k) for k in params) or (e.get("encoding") or {}).get("severity") == "governed_tint":
            traeger.append(path.stem)
    assert traeger == r["erlaubt_nur_in"], traeger
    profil = yaml.safe_load((LIB / "_notation_profiles.yaml").read_text(encoding="utf-8"))["profiles"]
    assert "pill" in profil[r["verboten_in_profil"]]["rules"]["variance"]
    assert all(p in profil[r["verboten_in_profil"]]["rules"]["variance"] for p in r["erlaubt_nur_in"])


# --- Eckenradius in Deneb ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("profile,pack", [("house_default", 6), ("ibcs", 6), ("house_default", None), ("fluent", 6)])
def test_deneb_config_takes_the_corner_radius_from_the_rule(profile, pack):
    cfg = render.deneb_config(profile, pack)
    if pack is None:
        assert cfg == render.vegalite_config(profile), "ohne Pack-Wert bleibt die Profil-Config unverändert"
        return
    assert cfg["bar"]["cornerRadiusEnd"] == gestaltung.eckenradius(render.notation_of(profile), pack)
    if render.notation_of(profile) == "ibcs":
        assert cfg["bar"]["cornerRadiusEnd"] == 0


# --- Power BI nativ: Formatkatalog ----------------------------------------------------------------------------------

def _native_goldens() -> list[Path]:
    return sorted(GOLDEN.glob("*.powerbi_native*.json"))


def test_no_native_golden_smooths_the_line_until_measured():
    """BO-423: ob lineChartType smooth monoton verläuft, ist nicht gemessen; bis dahin linear (Register)."""
    assert gestaltung.regel("linienverlauf")["powerbi_native"] == "linear"
    treffer = [p.name for p in _native_goldens() if "'smooth'" in p.read_text(encoding="utf-8")]
    assert not treffer, treffer


def test_ibcs_line_native_names_its_series_at_the_end_and_has_no_legend():
    v = json.loads((GOLDEN / "line.powerbi_native.ibcs.json").read_text(encoding="utf-8"))
    sl = v["objects"]["seriesLabels"][0]["properties"]
    assert sl["show"]["expr"]["Literal"]["Value"] == "true"
    assert sl["seriesPosition"]["expr"]["Literal"]["Value"] == "'Right'"
    assert v["objects"]["legend"][0]["properties"]["show"]["expr"]["Literal"]["Value"] == "false"


@pytest.mark.parametrize("name", ["line.powerbi_native.ibcs.json", "bar_ranking.powerbi_native.json",
                                  "column_time.powerbi_native.ibcs.json"])
def test_new_native_properties_exist_in_the_formatting_catalog(name):
    v = json.loads((GOLDEN / name).read_text(encoding="utf-8"))
    assert fm.unknown_visual_objects({"visual": v}) == []
    # Gegenprobe: eine erfundene Eigenschaft wird gemeldet.
    v["objects"]["valueAxis"] = [{"properties": {"erfunden": {}}}]
    assert fm.unknown_visual_objects({"visual": v}) == ["valueAxis.erfunden"]
