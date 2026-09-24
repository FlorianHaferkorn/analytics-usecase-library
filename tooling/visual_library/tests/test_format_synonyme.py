"""AP-8 (24.09.2026): Alltagssprache → Formatierungseigenschaft, belegt am offiziellen Katalog.

Die linke Seite (`begriffe`) ist handgepflegt, alles rechts davon kommt aus dem eingefrorenen
Katalogauszug `catalog_facts.json` (Pin 0.1.1). Jeder Eintrag wird fuer jeden genannten
Visualtyp aufgeloest; ein falsch geschriebenes Objekt oder eine erfundene Eigenschaft wird rot.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import catalog_facts  # noqa: E402
import resolve  # noqa: E402

FACTS = catalog_facts.lade()
EINTRAEGE = resolve.load_format_synonyms()


def _typen(e: dict) -> list[str]:
    return sorted(FACTS["anzeige"]) if e["visuals"] == "alle" else e["visuals"]


@pytest.mark.parametrize("e", EINTRAEGE, ids=lambda e: e["begriffe"][0])
def test_every_entry_resolves_in_the_official_catalog(e):
    for vt in _typen(e):
        pfad = catalog_facts.format_pfad(vt, e["objekt"], e["property"], FACTS)
        assert " › " in pfad, (vt, e)


def test_container_objects_are_declared_for_all_visuals_and_visual_objects_are_not():
    for e in EINTRAEGE:
        ist_vco = e["objekt"] in FACTS["vco_anzeige"]
        assert (e["visuals"] == "alle") == ist_vco, e["begriffe"][0]


def test_terms_are_unique_and_lowercase():
    alle = [b for e in EINTRAEGE for b in e["begriffe"]]
    assert len(alle) == len(set(alle))
    assert all(b == b.lower() for b in alle)


def test_the_same_object_is_named_by_orientation():
    """Warum man mit Visualtyp aufloest: die Kategorieachse ist beim Balken die Y-Achse."""
    bar = resolve.format_begriff("axis label size", "clusteredBarChart")
    col = resolve.format_begriff("axis label size", "clusteredColumnChart")
    assert bar["objekt"] == col["objekt"] == "categoryAxis"
    assert bar["pfad"] == "Y axis › Text size" and col["pfad"] == "X axis › Text size"


def test_a_term_for_another_visual_type_does_not_resolve():
    assert resolve.format_begriff("linienstaerke", "clusteredBarChart") is None
    assert resolve.format_begriff("linienstaerke", "lineChart")["property"] == "strokeWidth"


def test_an_invented_property_is_caught():
    """Gegenprobe: der Aufloeser akzeptiert nichts, was der Katalog nicht kennt."""
    with pytest.raises(KeyError):
        catalog_facts.format_pfad("clusteredBarChart", "dataPoint", "barColour", FACTS)
