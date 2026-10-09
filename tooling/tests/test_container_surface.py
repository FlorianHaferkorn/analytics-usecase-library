"""Tests fuer BC-LAYOUT-02 und den geschlossenen blinden Fleck von BC-CHART-04.

Der Wert dieser Tests liegt nicht im gruenen Bestand, sondern im Nachweis, dass die
sanktionierte Grundlinie eine GRENZE ist und keine Erlaubnis: alles bis zum
beschlossenen Kartensystem ist still, alles darueber feuert.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tooling" / "validation"))
sys.path.insert(0, str(REPO))

import check_container_surface as ccs  # noqa: E402
import check_declutter as cd           # noqa: E402

_TOKENS = REPO / "core/templates/page_templates/tokens"


def test_baseline_is_declared_not_assumed():
    """Fehlt die Grundlinie, wirft es — statt jede Dekoration durchzulassen.

    Eine fehlende Obergrenze als „nichts verboten" zu lesen waere derselbe stille
    Fallback wie eine leere Pflichtliste, die aussieht wie „alles erfuellt".
    """
    basis = ccs.grundlinie()
    assert basis.get("never"), "keine `never`-Liste — dann waere Verlauf erlaubt"
    assert "allowed" in (basis.get("drop_shadow") or {}), "Schatten nicht entschieden"
    assert (basis.get("border") or {}).get("width_max_px") is not None
    assert basis.get("source") and basis.get("decided"), "Grundlinie ohne Herkunft"


def test_baseline_matches_the_decided_theme():
    """Die Grundlinie ist die Erhebung des BESCHLOSSENEN Themes, kein Wunschwert.

    Seit 08.10.2026 (Meridian D-685/D-710) gemessen am WIRKSAMEN Theme: Rahmen und Schatten
    kommen aus dem Basistheme Fluent2-CY26SU10, der Innenabstand aus dem eigenen Theme. Faellt
    dieser Test, sind Theme und Grundlinie auseinandergelaufen — das braucht eine Entscheidung
    statt einer stillen Anpassung.
    """
    report = sorted((REPO / "products/fabric/powerbi/dist").glob("*.Report"))[0]
    stern = ccs.wirksamer_stern(report)
    basis = ccs.grundlinie()
    rahmen = (stern.get("border") or [{}])[0]
    assert rahmen.get("show") is True
    assert rahmen.get("width") == basis["border"]["width_max_px"]
    assert rahmen.get("radius") == basis["border"]["radius_max_px"]
    assert rahmen["color"]["solid"]["color"].upper() == basis["border"]["color"]
    schatten = (stern.get("dropShadow") or [{}])[0]
    assert basis["drop_shadow"]["allowed"] is False and schatten.get("show") is False
    pad = (stern.get("padding") or [{}])[0]
    for seite in ("top", "right", "bottom", "left"):
        assert pad.get(seite) == basis["padding"][f"{seite}_max_px"], seite


def _mutierte_kopie(tmp_path: Path, mutation) -> Path:
    import shutil

    from check_palette_monochrome import aktives_theme

    src = sorted((REPO / "products/fabric/powerbi/dist").glob("*.Report"))[0]
    dist = tmp_path / "dist"
    ziel = dist / src.name
    shutil.copytree(src, ziel)
    thf = aktives_theme(ziel)
    theme = json.loads(thf.read_text(encoding="utf-8"))
    mutation(theme["visualStyles"]["*"]["*"])
    thf.write_text(json.dumps(theme), encoding="utf-8")
    return dist


@pytest.mark.parametrize("mutation,erwartet", [
    (lambda st: st.__setitem__("border", [{"show": True, "width": 2}]), "Rahmen-width 2"),
    (lambda st: st.__setitem__("dropShadow", [{"show": True}]), "Schatten sichtbar"),
    (lambda st: st.__setitem__("padding", [{"top": 10, "right": 12, "bottom": 8, "left": 12}]),
     "padding.top 10"),
], ids=["rahmen_2px", "schatten_an", "padding_oben_10"])
def test_gegenprobe_wirksames_theme_feuert(tmp_path, mutation, erwartet):
    """Gegenprobe: was das eigene Theme ueber das Basistheme legt, wird gemessen."""
    dist = _mutierte_kopie(tmp_path, mutation)
    treffer, _ = ccs.pruefe_dist(dist)
    assert any(erwartet in t for t in treffer), treffer


def test_gegenprobe_basistheme_wird_gelesen(tmp_path):
    """Ein Basistheme mit Schatten an muss feuern, obwohl das eigene Theme keinen setzt."""
    dist = _mutierte_kopie(tmp_path, lambda st: None)
    # Alle Basistheme-Dateien aller Berichte; welche report.json nennt, entscheidet der Prüfer.
    # Nur die erste per glob zu nehmen hing von der Dateisystem-Reihenfolge ab (CI rot am
    # 09.10.2026: das verwaiste Base_Theme_Template_V1.json ohne dropShadow lag dort vorne).
    for bt in dist.glob("*.Report/StaticResources/SharedResources/BaseThemes/*.json"):
        basis = json.loads(bt.read_text(encoding="utf-8"))
        stern = basis.setdefault("visualStyles", {}).setdefault("*", {}).setdefault("*", {})
        stern["dropShadow"] = [{"show": True}]
        bt.write_text(json.dumps(basis), encoding="utf-8")
    treffer, _ = ccs.pruefe_dist(dist)
    assert any("Schatten sichtbar" in t for t in treffer), treffer


@pytest.mark.parametrize("objekte,erwartet", [
    ({"dropShadow": [{"properties": {"transparency": 40}}]}, "transparency"),
    ({"dropShadow": [{"properties": {"shadowDistance": 6}}]}, "shadowDistance"),
    ({"border": [{"properties": {"width": 3}}]}, "width"),
    ({"gradient": [{"properties": {}}]}, "gradient"),
    ({"glow": [{"properties": {}}]}, "glow"),
    ({"padding": [{"properties": {"left": 24}}]}, "padding.left"),
])
def test_beyond_the_card_system_fires(objekte, erwartet):
    treffer = ccs.pruefe_container(objekte, ccs.grundlinie(), "T")
    assert treffer and erwartet in treffer[0], treffer


def test_the_sanctioned_card_system_stays_silent():
    """Genau der beschlossene Stand darf nicht anschlagen — sonst waere Weg A wirkungslos."""
    basis = ccs.grundlinie()
    sanktioniert = {
        "dropShadow": [{"properties": {"show": False, "transparency": 86}}],
        "border": [{"properties": {"width": basis["border"]["width_max_px"],
                                   "radius": basis["border"]["radius_max_px"]}}],
        "padding": [{"properties": {s: basis["padding"][f"{s}_max_px"]
                                    for s in ("top", "right", "bottom", "left")}}],
    }
    assert ccs.pruefe_container(sanktioniert, basis, "T") == []


def test_whitespace_order_is_checked():
    spacing = (yaml.safe_load((_TOKENS / "layout_grid.yaml").read_text(encoding="utf-8"))
               or {}).get("spacing") or {}
    assert ccs.pruefe_weissraum(spacing) == [], "gelebte Ordnung verletzt"
    assert ccs.pruefe_weissraum({"zone_gap": 8, "gutter": 16, "internal_padding": 40})
    assert ccs.pruefe_weissraum({"zone_gap": 40}), "fehlende Werte muessen auffallen"


def test_declutter_now_reads_the_theme(tmp_path):
    """Der geschlossene blinde Fleck: BC-CHART-04 sah bis 03.08.2026 nur visual.json.

    Das Theme setzte fuer JEDES Visual Hintergrund/Rahmen/Schatten, 0 von 188 Visuals
    ueberschrieben das — der Pruefer war gruen und hat nichts geprueft.
    """
    import shutil

    from check_palette_monochrome import aktives_theme

    src = sorted((REPO / "products/fabric/powerbi/dist").glob("*.Report"))[0]
    ziel = tmp_path / "X.Report"
    shutil.copytree(src, ziel)
    assert cd.theme_chartjunk(ziel) == [], "der gelebte Stand darf nicht feuern"

    thf = aktives_theme(ziel)
    theme = json.loads(thf.read_text(encoding="utf-8"))
    theme["visualStyles"]["*"]["*"]["gradient"] = [{"properties": {"show": True}}]
    thf.write_text(json.dumps(theme), encoding="utf-8")
    befunde = cd.theme_chartjunk(ziel)
    assert befunde and "gradient" in befunde[0], befunde


def test_dist_containers_are_within_the_baseline():
    treffer, geprueft = ccs.pruefe_dist()
    assert geprueft > 10, f"nur {geprueft} Ebenen geprueft"
    assert not treffer, f"{len(treffer)} Verstoss/Verstoesse: {treffer[:2]}"
