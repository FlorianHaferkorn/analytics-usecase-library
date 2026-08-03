"""Layout-Bindung im Quell-Adapter (Task L8).

Der Befund, der L8 ausgeloest hat
---------------------------------
`from_aluca` erzeugte Visuals **ohne Geometrie** — jedes `Visual` ging mit
x=y=width=height=0 heraus. Sichtbar war das in den eingecheckten Golden Snapshots
(`"width": 0`), aber es fiel nicht auf, weil kein Test danach fragte. Der Vertrag
(`canonical_contract.Visual`) fuehrt die vier Felder seit jeher.

Aufgefallen ist es erst bei L13: die Umstellung auf Logical Units bewegte KEINEN
Snapshot — und diese Stille war der Hinweis, nicht die Bestaetigung.
"""
from __future__ import annotations

import pathlib
import tempfile
from pathlib import Path

import pytest
import yaml

from tooling.superversion.from_aluca import KpiCatalog, from_bracket_file

_ROOT = Path(__file__).resolve().parents[3]
_KPIS = _ROOT / "core/kpi_catalog/kpis"
_FIN002 = _ROOT / "core/usecases/core/FIN-002_Cost_Performance/UseCase_Bracket.yaml"
_GRID = _ROOT / "core/templates/page_templates/tokens/layout_grid.yaml"


@pytest.fixture(scope="module")
def modell():
    return from_bracket_file(_FIN002, _KPIS)


def _visuals(modell):
    return [v for p in modell.report.pages for v in p.visuals]


def test_visuals_carry_geometry_at_all(modell):
    """Die Grundzusicherung von L8 — und genau die fehlte vorher.

    Nicht „die Zahlen stimmen", sondern „es gibt ueberhaupt welche". Ein Report, dessen
    Visuals alle bei (0,0) mit Groesse 0 liegen, ist kein Layout, sondern ein Stapel.
    """
    mit_geo = [v for v in _visuals(modell) if v.width > 0 and v.height > 0]
    assert mit_geo, "kein einziges Visual traegt Geometrie"
    assert len(mit_geo) == len(_visuals(modell)), (
        "Visuals ohne Geometrie: "
        f"{[v.visual_id for v in _visuals(modell) if not v.width]}"
    )


def test_main_columns_do_not_overlap(modell):
    """Zwei Hauptspalten duerfen sich nicht ueberlappen.

    Das ist der billigste Beweis, dass die Slots wirklich aus dem Raster kommen und
    nicht aus einem Default: bei kopierten oder geratenen Werten faellt genau das um.
    """
    from tooling.superversion.from_aluca import _MAIN_SLOTS

    mains = sorted((v for v in _visuals(modell) if v.visual_id in _MAIN_SLOTS),
                   key=lambda v: v.x)
    assert mains, "keine Hauptspalten gefunden — der Test prueft sonst nichts"
    for links, rechts in zip(mains, mains[1:]):
        assert links.x + links.width <= rechts.x + 1e-6, (
            f"{links.visual_id} ragt in {rechts.visual_id}")


def test_geometry_stays_inside_the_canvas(modell):
    grid = yaml.safe_load(_GRID.read_text(encoding="utf-8")) or {}
    prod = (grid.get("canvas") or {}).get("production") or {}
    w, h = prod.get("width", 1920), prod.get("height", 1080)
    for v in _visuals(modell):
        assert v.x >= 0 and v.y >= 0, v.visual_id
        assert v.x + v.width <= w + 1e-6, f"{v.visual_id} ragt rechts hinaus"
        assert v.y + v.height <= h + 1e-6, f"{v.visual_id} ragt unten hinaus"


def test_grid_change_takes_effect_without_code_change(tmp_path, monkeypatch):
    """DoD: „Aenderung an `layout_grid.yaml` wirkt ohne Codeaenderung."

    Geprueft wird die Zusicherung selbst, nicht ihre Formulierung: der Aussenrand wird
    zur Laufzeit veraendert und muss sich in der Geometrie niederschlagen. Waere die
    Tabelle im Adapter kopiert (statt gelesen), passierte hier nichts — und der Test
    faende genau das.
    """
    # Gepatcht wird der EINE Leser (`layer_tools/layout_grid.py`) — nicht mehr der
    # Compiler. Dass dieser Test beim Konsolidieren rot wurde, ist der Beleg, dass es
    # vorher zwei Stellen gab und jetzt eine gibt.
    from tooling.superversion.layer_tools import layout_grid

    original = yaml.safe_load(_GRID.read_text(encoding="utf-8"))
    vorher = from_bracket_file(_FIN002, _KPIS)
    x_vorher = min(v.x for v in _visuals(vorher))

    geaendert = dict(original)
    geaendert["spacing"] = {**original["spacing"], "outer_margin": 64}
    kopie = tmp_path / "layout_grid.yaml"
    kopie.write_text(yaml.safe_dump(geaendert), encoding="utf-8")
    monkeypatch.setattr(layout_grid, "GRID_YAML", kopie)

    nachher = from_bracket_file(_FIN002, _KPIS)
    x_nachher = min(v.x for v in _visuals(nachher))

    assert x_vorher == pytest.approx(32.0), "Ausgangswert stimmt nicht mit outer_margin 32"
    assert x_nachher == pytest.approx(64.0), (
        "Der Adapter liest das Raster nicht — eine YAML-Aenderung blieb wirkungslos")


def test_surplus_components_get_no_invented_slot():
    """Mehr als drei 30s-Komponenten bekommen KEINE vierte Spalte.

    Das Raster hat drei Hauptspalten. Eine vierte zu erfinden, waere derselbe Fehler
    wie der frueher entfernte KPI-Fallback im Page-Scaffold-Generator: sichtbar leer
    ist besser als still danebengesetzt.
    """
    from tooling.superversion.from_aluca import _MAIN_SLOTS, _slot_geometrie

    assert len(_MAIN_SLOTS) == 3
    assert _slot_geometrie("") == {}
    assert _slot_geometrie("Main_4") == {}


def test_geometry_matches_the_governed_slot_exactly(modell):
    """Die Werte stammen aus dem Raster-Template DIESER Variante, nicht aus einer Tabelle.

    Bis 02.08.2026 verglich dieser Test gegen `_OVERVIEW_LU` — die Compiler-Tabelle.
    Die war faktisch `pulse` fuer alle Varianten; FIN-002 deklariert aber eine Variante
    mit `executive_kpi`, wo `Main_1` **8** LU breit ist statt 4. Der Test hat also die
    Kopie gegen die Kopie geprueft und deshalb nie gemerkt, dass `template_variant`
    wirkungslos war.
    """
    import yaml as _yaml

    from tooling.superversion.layer_tools.layout_grid import load, to_pixels
    from tooling.superversion.layer_tools.page_templates import slot_lu

    variant = ((_yaml.safe_load(pathlib.Path(_FIN002).read_text(encoding="utf-8")) or {})
               .get("ux_layout_rules", {}).get("page_1_summary", {}).get("template_variant"))
    assert variant, "FIN-002 deklariert keine Variante — der Test prueft sonst nichts"
    lu = slot_lu(variant, "overview_slots", "Main_1")
    assert lu, f"{variant} kennt keinen Main_1 — Manifest/Template pruefen"
    erwartet = to_pixels(*lu, params=load("production"))
    main1 = next(v for v in _visuals(modell) if v.visual_id == "Main_1")
    assert main1.x == pytest.approx(erwartet["x"])
    assert main1.width == pytest.approx(erwartet["width"])


# --------------------------------------------------------------------------- #
# Pflicht-Slots: kann der Waechter ueberhaupt feuern? (02.08.2026)             #
# --------------------------------------------------------------------------- #

def test_slot_gaps_reports_one_entry_per_declared_page():
    """Jede deklarierte Seite wird geprueft — Stillschweigen ist kein Ergebnis."""
    from tooling.superversion.from_aluca import slot_luecken

    ergebnis = slot_luecken(_FIN002, _KPIS)
    assert {r["page"] for r in ergebnis} == {"page_1_summary", "page_2_execution"}
    assert all(r["variant"] for r in ergebnis), "Variante nicht durchgereicht"


def test_slot_gaps_distinguishes_unchecked_from_complete():
    """„nicht geprueft" (None) darf nie wie „nichts fehlt" ([]) aussehen.

    Genau diese Verwechslung hat `RequiredSlots` unsichtbar gemacht: es gab still `[]`
    zurueck, wenn es die Seite nicht einordnen konnte — und `[]` liest sich wie
    Entwarnung.
    """
    from tooling.superversion.from_aluca import slot_luecken

    roh = yaml.safe_load(pathlib.Path(_FIN002).read_text(encoding="utf-8"))
    roh["ux_layout_rules"]["page_1_summary"].pop("template_variant")
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "UseCase_Bracket.yaml"
        p.write_text(yaml.safe_dump(roh, allow_unicode=True), encoding="utf-8")
        ohne = next(r for r in slot_luecken(p, _KPIS) if r["page"] == "page_1_summary")
    assert ohne["missing"] is None, "fehlende Variante muss als ungeprueft gelten"


def test_slot_gaps_actually_detects_a_missing_mandatory_slot():
    """Wirksamkeitsnachweis: ein entfernter Pflicht-Slot muss auffallen.

    Ohne diesen Test koennte `slot_luecken` konstant leere Listen liefern und saehe
    von aussen aus wie ein bestandener Check — die Fehlerklasse, gegen die dieses
    ganze Modul gebaut ist.
    """
    from tooling.superversion.from_aluca import slot_luecken
    from tooling.superversion.layer_tools.page_templates import load

    ergebnis = slot_luecken(_FIN002, _KPIS)
    seite = next(r for r in ergebnis if r["page"] == "page_2_execution")
    pflicht = load(seite["variant"]).pflicht("detail_slots")
    assert pflicht, "Variante ohne Pflicht-Slots — der Test prueft sonst nichts"

    # Was emittiert wird, darf nicht als fehlend gelten; was fehlt, muss gemeldet sein.
    for slot in pflicht:
        if slot in seite["emitted"]:
            assert slot not in seite["missing"]
        else:
            assert slot in seite["missing"], f"{slot} fehlt, wird aber nicht gemeldet"


def test_visual_ids_are_slot_names_so_the_check_can_match():
    """Die `visual_id` muss der Slot-Name sein, sonst laeuft jeder Slot-Check leer."""
    from tooling.superversion.from_aluca import _MAIN_SLOTS, from_bracket_file

    modell = from_bracket_file(_FIN002, _KPIS)
    ids = {v.visual_id for p in modell.report.pages for v in p.visuals}
    assert "KPI_Cards" in ids
    assert ids & set(_MAIN_SLOTS), f"keine Hauptspalten-Slots in {sorted(ids)}"


def test_visual_ids_are_unique_per_page():
    """Doppelte `visual_id` = doppeltes PBIR-Verzeichnis = ein Visual verschwindet."""
    from tooling.superversion.from_aluca import from_bracket_file

    for p in from_bracket_file(_FIN002, _KPIS).report.pages:
        ids = [v.visual_id for v in p.visuals]
        assert len(ids) == len(set(ids)), f"{p.name}: doppelte visual_id in {ids}"


# --------------------------------------------------------------------------- #
# information_block: die Naht, die die 11 Varianten wirksam macht (02.08.2026)  #
# --------------------------------------------------------------------------- #

def test_slot_block_decides_the_visual_when_the_bracket_is_silent():
    """Schweigt das Bracket, entscheidet der `information_block` des Slots.

    Vorher stand dort ein hartes `"card"` — unabhaengig davon, ob der Slot eine
    Detailmatrix, eine Ausnahmeliste oder ein Trend war. 20 der 66 Deklarationen
    liefen darauf. Das war kein Default, sondern ein stiller Fallback.
    """
    from tooling.superversion.from_aluca import _visual_fuer_slot

    typ, konflikt = _visual_fuer_slot({}, "Detail_Matrix", "T4_ActionDecision", "detail_slots")
    assert typ == "table", f"Detail-Matrix ohne Bracket-Wahl sollte die Block-Vorgabe sein: {typ}"
    assert konflikt is None
    # Und ohne aufloesbaren Block bleibt es beim alten Verhalten — kein Raten.
    assert _visual_fuer_slot({}, "Gibt_Es_Nicht", "T4_ActionDecision", "detail_slots")[0] == "card"


def test_bracket_choice_inside_the_block_is_respected():
    """Governance grenzt ein, sie entmuendigt nicht."""
    from tooling.superversion.from_aluca import _visual_fuer_slot

    typ, konflikt = _visual_fuer_slot(
        {"visual_type": "column_chart"}, "Main_1", "T1_Portfolio", "overview_slots")
    assert typ == "column_chart" and konflikt is None


def test_bracket_choice_outside_the_block_is_reported_not_overridden():
    """Ein Widerspruch wird gemeldet — und die Wahl bleibt trotzdem stehen.

    Automatisch zu ueberschreiben hiesse zu entscheiden, dass das Bracket irrt. Bei
    den gemessenen 12 Konflikten sind **7 derselbe Fall**; das ist eher ein Hinweis auf
    die Slot-Zuweisung der Variante als auf zwoelf Autorenfehler.
    """
    from tooling.superversion.from_aluca import _visual_fuer_slot

    typ, konflikt = _visual_fuer_slot(
        {"visual_type": "waterfall_chart"}, "Main_1", "T1_Portfolio", "overview_slots")
    assert typ == "waterfall_chart", "die Wahl darf nicht still ersetzt werden"
    assert konflikt and konflikt["block"] == "time_trend"
    assert "waterfall_chart" not in konflikt["allowed"]


def test_the_variant_actually_changes_what_is_shown():
    """Der Wirksamkeitsnachweis: zwei Varianten, gleicher Slot, anderes Visual.

    Das ist der Punkt der ganzen Uebung. `PAGE_TYPE_TAXONOMY.md` hielt fest, dass sich
    T2–T4 „aehnlich anfuehlten" und nannte als Ursache einen **Engine-Gap**, keinen
    Taxonomie-Gap: der Renderer unterschied die Seitentypen nicht. Gemessen am
    02.08.2026 war das noch immer so — `information_block` hatte **0** Konsumenten.
    Schlaegt dieser Test um, ist die Naht wieder ab und die 11 Varianten sind erneut
    Metadaten ohne Wirkung.
    """
    from tooling.superversion.from_aluca import _visual_fuer_slot

    a = _visual_fuer_slot({}, "Main_2", "T2_DriverBridge", "overview_slots")[0]
    b = _visual_fuer_slot({}, "Main_2", "T3_ProcessControl", "overview_slots")[0]
    assert a != b, f"Main_2 liefert fuer beide Varianten '{a}' — die Variante wirkt nicht"
