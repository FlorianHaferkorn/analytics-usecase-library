"""Tests fuer BC-COLOR-02 (Palette) und BC-TYPE-04 (Lesbarkeit).

Beide Regeln standen bis zum 03.08.2026 auf `check: structural` ohne Pruefer. Der Wert
dieser Tests liegt nicht im gruenen Bestand — der ist trivial — sondern im Nachweis,
dass die Pruefer ROT werden koennen und WOFUER.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tooling" / "validation"))
sys.path.insert(0, str(REPO))

import check_palette_monochrome as cpm  # noqa: E402
import check_text_legibility as ctl      # noqa: E402

_SEMANTISCH = {"good": "#519872", "bad": "#EC4E20", "neutral": "#F6AE2D"}


# ── BC-COLOR-02 ──────────────────────────────────────────────────────────────

def test_threshold_comes_from_the_theme_not_from_code():
    """Der Massstab ist der kleinste semantische Farbtonabstand des Themes selbst.

    Eine Gradzahl im Code haette die Regel im Code entschieden. Gemessen fuer das
    Aurora-Theme: bad 13.5° · neutral 38.5° · good 147.9° → kleinster Abstand 25.0°.
    """
    assert cpm.schwelle(_SEMANTISCH) == pytest.approx(25.0, abs=0.5)
    # Ohne zwei bunte semantische Tokens gibt es keinen Massstab — und dann sagt der
    # Pruefer das, statt einen zu erfinden.
    assert cpm.schwelle({"good": "#888888"}) is None


def test_rainbow_palette_is_caught():
    regen = {"dataColors": ["#FF0000", "#00FF00", "#0000FF"], **_SEMANTISCH}
    grund = cpm.pruefe(regen)
    assert grund and "Farbton" in grund


def test_monochrome_palette_passes():
    mono = {"dataColors": ["#249FB3", "#19717F", "#6A9AA2"], **_SEMANTISCH}
    assert cpm.pruefe(mono) is None


def test_grey_does_not_inflate_the_span():
    """Grau hat keinen Farbton und darf die Spanne nicht aufblaehen.

    Sonst waere jede Palette mit einem neutralen Ton ein Verstoss — ein Fehlalarm,
    der den Pruefer unbrauchbar machte.
    """
    assert cpm.pruefe({"dataColors": ["#249FB3", "#CCCCCC"], **_SEMANTISCH}) is None


def test_only_the_active_theme_is_judged():
    """Nur das in report.json benannte Theme zaehlt.

    Der erste Entwurf prueft jede registrierte Ressource und meldete 16 Verstoesse —
    alle aus `Brand_Rose__Monochromatic__…json`, einer Datei, die in jedem Report
    liegt und NICHT aktiv ist. Ein Gate, das eine nicht angewandte Datei rot macht,
    meldet etwas, das im Report nicht zu sehen ist.
    """
    dist = REPO / "products/fabric/powerbi/dist"
    reports = sorted(dist.glob("*.Report"))
    assert reports, "kein dist-Report — Test hat seinen Gegenstand verloren"
    aktiv = cpm.aktives_theme(reports[0])
    assert aktiv is not None and aktiv.is_file()
    registriert = list((reports[0] / "StaticResources/RegisteredResources").glob("*.json"))
    assert len(registriert) > 1, "nur eine Ressource — der Test prueft nichts mehr"


def test_dist_palettes_are_clean():
    treffer, geprueft = cpm.pruefe_dist()
    assert geprueft >= 10, f"nur {geprueft} Paletten geprueft"
    assert not treffer, f"{len(treffer)} Palette(n) unterscheiden nach Farbton: {treffer[:2]}"


# ── BC-TYPE-04 ───────────────────────────────────────────────────────────────

def test_size_floor_is_read_from_typography_tokens():
    """Der Boden kommt aus `typography.yaml`, nicht aus dem Code."""
    assert ctl.governter_boden() > 0
    assert ctl.pruefe_groessen({"textClasses": {"label": {"fontSize": 8}}}, 10.0)
    assert not ctl.pruefe_groessen({"textClasses": {"label": {"fontSize": 12}}}, 10.0)


def test_uppercase_sentence_is_caught_but_a_marker_is_not():
    """Die Laengengrenze trennt Fliesstext von Etikett — ohne sie waere `OK` ein Verstoss."""
    assert ctl.ist_versalien_fliesstext("GROSS MARGIN HAS BEEN SLIDING BELOW PLAN")
    assert not ctl.ist_versalien_fliesstext("YTD VS PLAN")
    assert not ctl.ist_versalien_fliesstext("OK")
    assert not ctl.ist_versalien_fliesstext("Gross margin has been sliding below plan")


def test_dist_text_is_legible():
    treffer, geprueft = ctl.pruefe_dist()
    assert geprueft > 50, f"nur {geprueft} Texte/Klassen geprueft"
    assert not treffer, f"{len(treffer)} Lesbarkeitsverstoss/-verstoesse: {treffer[:2]}"
