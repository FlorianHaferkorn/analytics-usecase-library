"""Layout-Systeme als Plugin und der Schnitt-Test (Tasks L6/L7).

Warum es diese Tests gibt
-------------------------
Bis zum 02.08.2026 nannte das Konzept IBCS ein „Plugin", der Code kannte aber nur
eines: `SUCCESS` war eine Konstante. Ein Plugin-Mechanismus mit genau einer Instanz
ist keiner — er ist eine Behauptung, die beim zweiten System auffliegt. Genau deshalb
prueft L7 mit einem **zweiten** System, ob der Schnitt haelt.
"""
from __future__ import annotations

import pytest

from tooling.superversion.layer_tools.layout_systems import (
    IBCS,
    ISO_24896,
    SYSTEMS,
    LayoutSystem,
    abdeckung,
    sammle,
)


def _eigene(system: LayoutSystem) -> set[str]:
    return {r.rule_id for r in sammle(system) if r.ibcs}


def test_more_than_one_system_exists():
    """Ein Plugin-Mechanismus mit einer Instanz ist keiner."""
    assert len(SYSTEMS) >= 2
    assert {"ibcs", "iso24896"} <= set(SYSTEMS)


def test_group_vocabulary_is_per_system_not_global():
    """Die Gruppen gehoeren dem System, nicht dem Werkzeug.

    Waeren sie global, waere „Layout-System wechseln" nur ein anderes Etikett auf
    derselben Gliederung — und der Schnitt-Test wertlos.
    """
    assert IBCS.groups != ISO_24896.groups
    assert set(ISO_24896.groups) < set(IBCS.groups)


def test_the_cut_is_visible_and_costed():
    """L7-Kern: der Wechsel zeigt, welche Regeln heimatlos wuerden.

    Gemessen am 02.08.2026: 16 Regeln sind IBCS-abgeleitet, 10 davon traegt
    ISO 24896 mit — **sechs** wuerden bei einem Wechsel ohne System dastehen
    (SAY 1 + EXPRESS 5, beides Gruppen, die ISO 24896 nicht fuehrt).

    Der Test friert die Zahlen NICHT ein: sie steigen, sobald L6 die Inhalts-Luecke
    schliesst. Gesichert wird die Eigenschaft — der Schnitt ist echt, nicht leer und
    nicht total.
    """
    ibcs, iso = _eigene(IBCS), _eigene(ISO_24896)
    assert iso, "ISO 24896 traegt keine einzige Regel — die Ableitung greift nicht"
    assert iso < ibcs, "ISO 24896 muesste eine echte Teilmenge sein (engerer Scope)"
    assert ibcs - iso, "kein Unterschied — dann prueft der Schnitt-Test nichts"


def test_inheritance_covers_code_only_sources():
    """Regressionsschutz fuer einen Fehler, den erst der Schnitt-Test zeigte.

    Manche Herkunftsangaben nennen nur den Regelcode, nicht die Gruppe
    (`variance_explanation/waterfall_start_labeled` traegt „S9 — IBCS U4"). Die erste
    Fassung der Vererbung suchte ausschliesslich Gruppennamen und liess die Regel
    still fallen: der Bericht meldete UNIFY 6 statt 7. Die Differenz sah nach einer
    echten Migrationsluecke aus, war aber ein Erkennungsfehler — genau die Sorte
    Zahl, der man sonst glaubt.
    """
    ibcs_unify = set(abdeckung(sammle(IBCS), IBCS)["UNIFY"])
    iso_unify = set(abdeckung(sammle(ISO_24896), ISO_24896)["UNIFY"])
    assert ibcs_unify == iso_unify, (
        "UNIFY gehoert beiden Systemen — jede Differenz hier ist ein Erkennungsfehler, "
        f"keine Migrationsluecke. Nur bei IBCS: {sorted(ibcs_unify - iso_unify)}"
    )


def test_inheritance_respects_the_narrower_scope():
    """Geerbt wird nur, was das abgeleitete System auch fuehrt.

    Ohne diese Grenze zoege ISO 24896 auch SAY- und EXPRESS-Regeln an sich — und
    behauptete eine Abdeckung, die der Standard laut Beleglage gar nicht hat.
    """
    iso = _eigene(ISO_24896)
    fuer_fremde_gruppen = set(abdeckung(sammle(IBCS), IBCS)["SAY"]) | set(
        abdeckung(sammle(IBCS), IBCS)["EXPRESS"])
    assert not (iso & fuer_fremde_gruppen)


def test_house_rules_survive_a_system_switch():
    """Hausregeln und Fremdstandards bleiben — das ist der Zweck der Unterscheidung.

    Eine Regel aus Cleveland & McGill oder WCAG gilt unabhaengig von der gewaehlten
    Notation. Wuerde sie mitwandern, waere die Sicht wertlos: man koennte nicht mehr
    sagen, was ein Systemwechsel wirklich kostet.
    """
    for system in (IBCS, ISO_24896):
        regeln = sammle(system)
        bleibend = [r for r in regeln if not r.ibcs]
        assert len(bleibend) > len([r for r in regeln if r.ibcs])


@pytest.mark.parametrize("key", sorted(SYSTEMS))
def test_every_system_declares_its_evidence(key):
    """Jedes System sagt, worauf sein Scope beruht.

    ISO 24896s Gruppenliste stammt aus Suchauszuegen, nicht aus dem Normtext
    (`iso.org` gesperrt, Text kostenpflichtig). Ein System ohne diese Angabe wuerde
    eine Annahme wie eine Messung aussehen lassen.
    """
    assert SYSTEMS[key].note, f"{key} fuehrt keinen Belegstand"
