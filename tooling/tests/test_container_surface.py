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
    assert (basis.get("drop_shadow") or {}).get("transparency_min_pct") is not None


def test_baseline_matches_the_decided_theme():
    """Die Grundlinie ist die Erhebung des BESCHLOSSENEN Themes, kein Wunschwert.

    Faellt dieser Test, sind Theme und Grundlinie auseinandergelaufen — dann ist
    entweder das Theme veraendert worden oder die Grundlinie, und beides braucht eine
    Entscheidung statt einer stillen Anpassung.
    """
    from check_palette_monochrome import aktives_theme

    report = sorted((REPO / "products/fabric/powerbi/dist").glob("*.Report"))[0]
    theme = json.loads(aktives_theme(report).read_text(encoding="utf-8"))
    stern = theme["visualStyles"]["*"]["*"]
    basis = ccs.grundlinie()
    schatten = (stern.get("dropShadow") or [{}])[0]
    assert schatten.get("transparency") == basis["drop_shadow"]["transparency_min_pct"]
    assert schatten.get("shadowDistance") == basis["drop_shadow"]["distance_max_px"]
    rahmen = (stern.get("border") or [{}])[0]
    assert rahmen.get("width") == basis["border"]["width_max_px"]
    assert rahmen.get("radius") == basis["border"]["radius_max_px"]


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
        "dropShadow": [{"properties": {
            "transparency": basis["drop_shadow"]["transparency_min_pct"],
            "shadowDistance": basis["drop_shadow"]["distance_max_px"],
            "shadowBlur": basis["drop_shadow"]["blur_max_px"],
            "shadowSpread": basis["drop_shadow"]["spread_max"]}}],
        "border": [{"properties": {"width": basis["border"]["width_max_px"],
                                   "radius": basis["border"]["radius_max_px"]}}],
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
