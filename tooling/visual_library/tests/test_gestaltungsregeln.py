"""Gestaltungsregeln als Felder (`_gestaltungsregeln.yaml`), gegen Funktion, Idiome und gerenderte Charts gestellt.

Runde visuals, 17.10.2026 (Entscheidungen W1, W2, W3, Achsen und Linienverlauf; Musterkatalog Top 15).
Jede Regel hat ihre Schwelle als Feld; dieser Test liest das Feld, rechnet die Entscheidung mit `gestaltung.py`
und misst sie am Vega-Szenengraphen des Templates (vl_convert). Funktion und Template rechnen dieselbe Zahl
zweimal; weichen sie ab, wird hier rot, nicht erst im Bericht.
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
import gestaltung  # noqa: E402
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
TOKENS = REPO_ROOT / "core" / "templates" / "page_templates" / "tokens" / "color_semantics.yaml"
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_STATUS = {"umgesetzt", "teilweise", "offen"}
_W2 = {"bar_ranking": "x", "bar_absolute": "x", "column_time": "y", "variance_pin": "y",
       "waterfall_buildup": "y", "waterfall_pvm": "y", "waterfall_variance": "y"}


def _implemented() -> list[str]:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]


def _walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for v in node.values():
            _walk(v, fn)
    elif isinstance(node, list):
        for v in node:
            _walk(v, fn)


_PAKET = {"erzwingt", "teilweise", "nein", "unklar"}


def test_every_rule_states_what_the_package_does():
    """D-832 (Meridian, Florian 28.10.2026): je Regel das Feld `paket` mit Beleg. `erzwingt` heisst: die Visual
    Library setzt die Eigenschaft ausdruecklich, sonst gewinnt der Paket-Default (Beispiel eckenradius, BO-559)."""
    reg = gestaltung.register()
    for rid, r in reg["regeln"].items():
        assert r.get("paket") in _PAKET, f"{rid}: paket {r.get('paket')!r}"
        assert str(r.get("paket_beleg") or "").strip(), f"{rid}: paket ohne Beleg"
    assert reg["regeln"]["eckenradius"]["paket"] == "erzwingt"
    assert render.vegalite_config("ibcs")["bar"]["cornerRadiusEnd"] == 0


# --- Register: Form -----------------------------------------------------------------------------------------------

def test_every_rule_has_status_and_existing_tests_or_a_reason():
    reg = gestaltung.register()
    assert reg["schema_version"] == 1
    for rid, r in reg["regeln"].items():
        u = r["umsetzung"]
        assert u["status"] in _STATUS, f"{rid}: status {u['status']!r}"
        if u["status"] != "umgesetzt":
            assert u.get("offen"), f"{rid}: {u['status']} ohne `offen` (Grund des Rests)"
        if u["status"] != "offen":
            assert u.get("test"), f"{rid}: wirkt, aber kein Test genannt"
            for t in u["test"]:
                assert (REPO_ROOT / t).is_file(), f"{rid}: Testpfad {t} fehlt"


def test_zebra_token_equals_register():
    tok = yaml.safe_load(TOKENS.read_text(encoding="utf-8"))
    z = gestaltung.regel("zebra")
    assert z["token"] == "color_semantics.surface.zebra"
    assert tok["surface"]["zebra"] == z["farbe"] == "#F3F3F3"


def test_mark_tokens_equal_register():
    tok = yaml.safe_load(TOKENS.read_text(encoding="utf-8"))
    farben = gestaltung.regel("markenkontrast")["farben"]
    assert tok["marks"]["reference"] == farben["referenz"]
    assert tok["marks"]["context"] == farben["kontext"]


# --- y_basis und werteachse je Idiom ---------------------------------------------------------------------------------

def test_every_idiom_declares_a_known_y_basis_and_value_axis():
    klassen = set(gestaltung.regel("werteachse_basis")["klassen"])
    for iid in _implemented():
        e = render.load_entry(iid)
        assert e.get("y_basis") in klassen, f"{iid}: y_basis {e.get('y_basis')!r} nicht in {sorted(klassen)}"
        assert e.get("werteachse") in {"x", "y", "xy", "keine"}, f"{iid}: werteachse {e.get('werteachse')!r}"
        if e["y_basis"] == "entfaellt":
            assert e["werteachse"] == "keine", f"{iid}: entfaellt verlangt werteachse keine"


def test_length_idioms_start_at_zero_by_field():
    """Balken, Säulen, Flächen: y_basis null; der Rendertest dazu ist test_zero_baseline_all_profiles.py."""
    for iid in ("bar_absolute", "bar_ranking", "column_time", "area_stacked", "bar_stacked", "stacked_100",
                "waterfall_buildup", "waterfall_pvm", "waterfall_variance", "histogram", "bullet"):
        assert render.load_entry(iid)["y_basis"] == "null", iid


# --- Werteachse: Schwelle 25 % als Test ------------------------------------------------------------------------------

@pytest.mark.parametrize("werte, ziel, alarm, basis", [
    ([93.1, 94.0, 92.5, 95.2, 93.8], None, None, "angepasst"),     # OTIF: Spannweite 2,8 % des Maximums
    ([10, 41, 52, 33, 27], None, None, "null"),
    ([93.1, 94.0, 92.5, 95.2, 93.8], 95, 92, "angepasst"),          # Ziel und Alarm im Band
    ([93.1, 94.0, 92.5, 95.2, 93.8], 60, None, "null"),             # das Ziel zieht die Spannweite auf
    ([75, 100], None, None, "null"),                                # genau 25 %: strikt kleiner gilt nicht
    ([76, 100], None, None, "angepasst"),                           # 24 %
    ([-100, -80], None, None, "angepasst"),                         # Betragsmaximum 100, Spannweite 20 %
    ([0, 0, 0], None, None, "null"),
    ([], None, None, "null"),
])
def test_value_axis_threshold(werte, ziel, alarm, basis):
    r = gestaltung.werteachse(werte, ziel, alarm)
    assert r["basis"] == basis
    assert r["achsenbruch"] is (basis == "angepasst")
    if basis == "angepasst":
        lo = min([*werte, *(v for v in (ziel, alarm) if v is not None)])
        assert r["untergrenze"] < lo, "die Achse schließt den kleinsten Wert ein"


def test_value_axis_classes_other_than_line():
    assert gestaltung.werteachse([93, 94], klasse="null")["untergrenze"] == 0.0
    assert gestaltung.werteachse([93, 94], klasse="angepasst")["basis"] == "daten"
    assert gestaltung.werteachse([93, 94], klasse="index")["basis"] == "index"
    with pytest.raises(KeyError):
        gestaltung.werteachse([1], klasse="unbekannt")


def _line_scene(werte, params=None, profile=None):
    vlc = pytest.importorskip("vl_convert")
    out, _ = render.render_target("line", "html_vegalite", profile,
                                  bindings={"time": "d", "value": "v"}, params=params)
    spec = json.loads(out)
    spec["data"] = {"name": "dataset", "values": [{"d": f"2026-{m:02d}-01", "v": v} for m, v in enumerate(werte, 1)]}
    spec["width"], spec["height"] = 400, 200
    labels: list[str] = []
    texts: list[str] = []

    def fn(node):
        if node.get("marktype") == "text":
            for it in node.get("items", []):
                if node.get("role") == "axis-label":
                    labels.append(str(it.get("text")))
                elif node.get("role") == "mark" and it.get("text") not in (None, ""):
                    texts.append(str(it.get("text")))

    _walk(vlc.vegalite_to_scenegraph(spec), fn)
    return labels, texts


def _zahl(s: str):
    try:
        return float(s.replace(".", "").replace(",", ".").replace("−", "-").replace("%", "").strip())
    except ValueError:
        return None


@pytest.mark.parametrize("werte, params", [
    ([93.1, 94.0, 92.5, 95.2, 93.8], None),
    ([10, 41, 52, 33, 27], None),
    ([93.1, 94.0, 92.5, 95.2, 93.8], {"target_val": 95, "alert_val": 92}),
    ([93.1, 94.0, 92.5, 95.2, 93.8], {"target_val": 60}),
    ([76, 80, 100], None),
    ([75, 80, 100], None),
])
def test_line_template_draws_what_the_function_decides(werte, params):
    p = params or {}
    soll = gestaltung.werteachse(werte, p.get("target_val"), p.get("alert_val"))
    labels, texts = _line_scene(werte, params)
    zahlen = [z for z in (_zahl(t) for t in labels) if z is not None and z < 1000]   # Monatsachse ausblenden
    bruch = gestaltung.regel("werteachse_basis")["achsenbruch"]["zeichen"]
    assert (bruch in texts) is soll["achsenbruch"], f"Achsenbruch {texts}"
    if soll["basis"] == "null":
        assert 0.0 in zahlen, f"Achse beginnt nicht bei 0: {labels}"
    else:
        assert 0.0 not in zahlen and min(zahlen) >= soll["untergrenze"] - (max(zahlen) - min(zahlen)), labels


def test_line_alarm_line_is_labelled_when_given():
    _, texts = _line_scene([93.1, 94.0, 92.5, 95.2, 93.8], {"target_val": 95, "alert_val": 92})
    assert "Alarm" in texts
    _, ohne = _line_scene([93.1, 94.0, 92.5, 95.2, 93.8])
    assert "Alarm" not in ohne, "ohne Alarmwert keine Beispiel-Alarmlinie (data_values)"


# --- W2: Beschriftung gegen Gitter ---------------------------------------------------------------------------------

def _rows(iid: str, n: int) -> tuple[dict, list[dict]]:
    """Bindet jede Pflichtrolle des Idioms an eine Spalte: Zeit d, Werte v, sonst die Kategorie k."""
    cols: dict = {}
    for slot in (render.load_entry(iid).get("data_slots") or {}).values():
        if slot.get("required", True):
            r = slot["role"]
            cols[r] = "d" if r == "time" else ("v" if r in ("value", "variance") else "k")
    rows = [{"d": f"20{10 + i}-01-01", "k": f"K{i:02d}", "v": (i % 3 - 1) * 3 + 5} for i in range(n)]
    return cols, rows


def _w2_scene(iid: str, n: int, named: bool):
    vlc = pytest.importorskip("vl_convert")
    cols, rows = _rows(iid, n)
    spec = json.loads(render.render_target(iid, "html_vegalite", "house_default", bindings=cols)[0])
    spec["data"] = {"name": "dataset", "values": rows} if named else {"values": rows}
    spec["width"], spec["height"] = 400, 260
    out = {"grid": 0, "labels": 0, "achse": 0}

    def fn(node):
        if node.get("role") == "axis-grid":
            out["grid"] += len(node.get("items", []))
        if node.get("role") == "axis-label":                 # Zahlen der Werteachse (Jahre der Zeitachse > 1000)
            out["achse"] += sum(1 for it in node.get("items", []) if it.get("opacity", 1) > 0
                                and (z := _zahl(str(it.get("text")))) is not None and abs(z) < 1000)
        if node.get("role") == "mark" and node.get("marktype") == "text":
            out["labels"] += sum(1 for it in node.get("items", []) if it.get("opacity", 1) > 0 and it.get("text"))

    _walk(vlc.vegalite_to_scenegraph(spec), fn)
    return out


@pytest.mark.parametrize("iid", sorted(_W2))
@pytest.mark.parametrize("named", [True, False], ids=["deneb_dataset", "anonym_source_0"])
def test_labels_switch_value_grid_and_axis(iid, named):
    """Unter 10 Kategorien: beschriftet, kein Wertegitter; ab 10: unbeschriftet, Wertegitter an.
    `anonym_source_0` ist die Einbettung der Cockpit-Shell (fabric-visuals: `data: {values}`)."""
    klein, gross = _w2_scene(iid, 5, named), _w2_scene(iid, 12, named)
    assert gestaltung.beschriftet(5) and not gestaltung.beschriftet(12)
    assert klein["labels"] > 0 and klein["grid"] == 0 and klein["achse"] == 0, f"{iid} 5 Zeilen: {klein}"
    assert gross["labels"] == 0 and gross["grid"] > 0 and gross["achse"] > 0, f"{iid} 12 Zeilen: {gross}"


def test_w2_rule_is_declared_on_the_value_axis_of_each_idiom():
    for iid, achse in _W2.items():
        assert render.load_entry(iid)["werteachse"] == achse, iid


def test_unknown_data_name_keeps_the_axis():
    """Findet der Zähler keine Quelle, bleibt die Werteachse: nie Beschriftung und Achse zugleich aus."""
    vlc = pytest.importorskip("vl_convert")
    cols, rows = _rows("bar_absolute", 5)
    spec = json.loads(render.render_target("bar_absolute", "html_vegalite", "house_default", bindings=cols)[0])
    spec["data"] = {"name": "fremd", "values": rows}
    grid = []
    _walk(vlc.vegalite_to_scenegraph(spec),
          lambda n: grid.extend(n.get("items", [])) if n.get("role") == "axis-grid" else None)
    assert grid, "unbekannter Datenname: Wertegitter muss stehen bleiben"


def test_profiles_put_grid_by_axis_type_not_by_axis():
    for pid in render.all_profiles():
        cfg = render.vegalite_config(pid)
        assert "grid" not in (cfg.get("axisX") or {}), f"{pid}: axisX.grid nimmt liegenden Balken das Wertegitter"
        if (cfg.get("axis") or {}).get("grid") is False:
            continue                                    # ibcs: Beschriftung statt Gitter
        assert (cfg.get("axisDiscrete") or {}).get("grid") is False, pid
        assert (cfg.get("axisTemporal") or {}).get("grid") is False, pid


# --- W3, W1 ----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("zeilen, spalten, art, soll", [
    (10, 4, None, True), (9, 4, None, False), (10, 3, None, False), (40, 8, "heatmap", False),
    (40, 8, "datenbalken", False), (40, 8, "tabelle", True),
])
def test_zebra_threshold(zeilen, spalten, art, soll):
    assert gestaltung.zebra_an(zeilen, spalten, art) is soll


def test_corner_radius_ibcs_forces_zero():
    assert gestaltung.eckenradius("ibcs", 4) == 0
    assert gestaltung.eckenradius("house_default", 2) == 2
    assert gestaltung.eckenradius("house_default", None) == 0
    assert render.vegalite_config("ibcs")["bar"]["cornerRadius"] == 0


# --- Linienverlauf ---------------------------------------------------------------------------------------------------

def test_lines_are_monotone_in_every_profile():
    r = gestaltung.regel("linienverlauf")
    for iid in ("line", "indexed_line", "small_multiples"):
        for pid in [None, *render.profiles(iid)]:
            spec = json.loads(render.render(iid, "deneb_vegalite", pid)[0])
            marks = []
            _walk(spec, lambda n: marks.append(n["mark"]) if isinstance(n.get("mark"), dict)
                  and n["mark"].get("type") == "line" else None)
            assert marks, iid
            for m in marks:
                assert m.get("interpolate") == r["interpolation"], f"{iid}/{pid}: {m}"


def test_house_line_has_no_point_per_value_and_2px_actual():
    spec = json.loads(render.render("line", "deneb_vegalite", None)[0])
    lines = []
    _walk(spec, lambda n: lines.append(n["mark"]) if isinstance(n.get("mark"), dict)
          and n["mark"].get("type") == "line" else None)
    assert all(not m.get("point") for m in lines)
    assert max(m.get("strokeWidth", 0) for m in lines) == gestaltung.regel("linienverlauf")["ist_strich_px"]


# --- Markenkontrast, Säulen, Nulllinie, KPI-Richtung -----------------------------------------------------------------

def test_marks_reach_three_to_one_except_registered_decor():
    r = gestaltung.regel("markenkontrast")
    assert gestaltung.marke_lesbar(r["farben"]["referenz"]) and gestaltung.marke_lesbar(r["farben"]["kontext"])
    for iid, ausn in r["ausnahmen"].items():
        for k, grund in ausn.items():
            assert grund in r["gruende"], f"{iid}.{k}: Grund {grund!r} fehlt"
    zu_hell = []
    for iid in _implemented():
        ausn = r["ausnahmen"].get(iid) or {}
        for k, v in (render.load_entry(iid).get("canonical_params") or {}).items():
            if k.startswith(("col_", "tint_")) and isinstance(v, str) and _HEX.match(v) and k not in ausn:
                if not gestaltung.marke_lesbar(v):
                    zu_hell.append(f"{iid}.{k} {v} {gestaltung.kontrast(v):.2f}:1")
    assert not zu_hell, zu_hell


def test_columns_over_time_are_neutral_ink():
    assert render.load_entry("column_time")["canonical_params"]["col_bar"] == "#0F2430"


def test_zero_line_is_1_5px_reference_grey():
    r = gestaltung.regel("nulllinie")
    for iid in ("deviation_bar", "variance_pin", "multi_tier_column"):
        e = render.load_entry(iid)
        assert e["canonical_params"]["col_zero"] == r["farbe"], iid
        spec = json.loads(render.render(iid, "deneb_vegalite", None)[0])
        rules = []
        _walk(spec, lambda n: rules.append(n["mark"]) if isinstance(n.get("mark"), dict)
              and n["mark"].get("type") == "rule" and n["mark"].get("color") == r["farbe"] else None)
        assert any(m.get("strokeWidth") == r["breite_px"] for m in rules), f"{iid}: {rules}"


def test_kpi_card_deviation_colours_by_polarity_not_sign():
    e = render.load_entry("kpi_card_spark")
    dax = render.render("kpi_card_spark", "powerbi_svg_dax", None)[0]
    assert "_dlt * 1 < 0" in dax, "Abweichung färbt nach polarity"
    native = render.render("kpi_card_spark", "powerbi_native", None)[0]
    assert "'High is good'" in native and "'Positive'" in native
    assert e["canonical_params"]["polarity"] == "1"
