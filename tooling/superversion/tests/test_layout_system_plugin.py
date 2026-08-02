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

from tooling.superversion.layer_tools import layout_systems as ls
from tooling.superversion.layer_tools.layout_systems import (
    IBCS,
    ISO_24896,
    SYSTEMS,
    LayoutSystem,
    abdeckung,
    sammle,
)


def _eigene(system: LayoutSystem) -> set[str]:
    return {r.rule_id for r in sammle(system) if r.vom_system}


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
        bleibend = [r for r in regeln if not r.vom_system]
        assert len(bleibend) > len([r for r in regeln if r.vom_system])


@pytest.mark.parametrize("key", sorted(SYSTEMS))
def test_every_system_declares_its_evidence(key):
    """Jedes System sagt, worauf sein Scope beruht.

    ISO 24896s Gruppenliste stammt aus Suchauszuegen, nicht aus dem Normtext
    (`iso.org` gesperrt, Text kostenpflichtig). Ein System ohne diese Angabe wuerde
    eine Annahme wie eine Messung aussehen lassen.
    """
    assert SYSTEMS[key].note, f"{key} fuehrt keinen Belegstand"


# ─────────────────────────────────────────────────────────────────────────────
# Aus `test_layout_systems.py` zusammengefuehrt (02.08.2026): zwei Testdateien fuer
# EIN Modul waren dieselbe Dublette, die dieser Task ueberall sonst beseitigt.
# ─────────────────────────────────────────────────────────────────────────────
from tooling.superversion.layer_tools import layout_systems as ls


def test_reads_all_three_existing_stores():
    """Keine Quelle darf stillschweigend leer bleiben — sonst rechnet die Sicht falsch."""
    regeln = ls.sammle()
    dateien = {r.quelle_datei for r in regeln}
    assert dateien == {"visual_registry.yaml", "boutique_craft_rubric.yaml", "design_rules.yaml"}, \
        f"Quellen fehlen: {dateien}"
    assert len(regeln) >= 50, f"nur {len(regeln)} Regeln gefunden — Parser stimmt nicht"


def test_ibcs_group_is_only_read_from_the_ibcs_part_of_the_source():
    """„S11 — Tufte; CHECK" darf keine IBCS-Gruppe erfinden.

    Die Herkunftsfelder mischen Quellen in einem String. Wer stumpf nach
    SUCCESS-Woertern sucht, ordnet Tufte-Regeln IBCS zu und meldet eine Abdeckung,
    die es nicht gibt.
    """
    tufte = ls._klassifiziere("x", "f.yaml", "S11 — Tufte p.53: CHECK the baseline")
    assert not tufte.vom_system and tufte.gruppe is None
    assert tufte.fremdstandard == "Tufte"

    echt = ls._klassifiziere("y", "f.yaml", "S9 — IBCS UNIFY U4")
    assert echt.vom_system and echt.gruppe == "UNIFY" and echt.code == "U4"

    ohne_code = ls._klassifiziere("z", "f.yaml", "S9 — IBCS scenario notation")
    assert ohne_code.vom_system and ohne_code.code is None


def test_coverage_lists_every_success_group_even_when_empty():
    """Eine unbelegte Gruppe muss als 0 erscheinen, nicht fehlen — sonst ist die
    Luecke unsichtbar."""
    deckung = ls.abdeckung(ls.sammle())
    assert set(deckung) == set(ls.SUCCESS)
    assert any(not v for v in deckung.values()), \
        "Erwartung: heute sind Gruppen unbelegt. Wenn nicht mehr — Test anpassen, " \
        "das waere echter Fortschritt."


def test_cli_is_advisory_by_default_and_hard_with_strict():
    """Die Luecken sind bekannt; sie blocken erst, wenn man es verlangt."""
    assert ls.main([]) == 0
    assert ls.main(["--strict"]) == 1


def test_every_ibcs_rule_carries_a_success_group():
    """Eine IBCS-Regel ohne Gruppe faellt aus der Abdeckungsrechnung.

    Am 01.08.2026 geschlossen: 7 von 15 hatten keine. Der Test haelt den Zustand,
    damit eine neue Regel nicht wieder ungezaehlt hereinkommt.
    """
    ohne = [r.rule_id for r in ls.sammle() if r.vom_system and not r.gruppe]
    assert ohne == [], f"IBCS-Regeln ohne SUCCESS-Gruppe: {ohne}"


def test_bare_code_resolves_only_from_repo_evidence():
    """„IBCS U4" ohne Gruppe wird aufgeloest — aber nur aus im Repo Belegtem.

    Aus dem Anfangsbuchstaben zu raten waere unzulaessig: S ist SAY, SIMPLIFY ODER
    STRUCTURE; C ist CONDENSE ODER CHECK. Die Tabelle wird deshalb aus Stellen
    gelernt, die BEIDES nennen.
    """
    ls._lerne_codes(["S9 — IBCS UNIFY U4"])
    aufgeloest = ls._klassifiziere("a", "f.yaml", "S9 — IBCS U4")
    assert aufgeloest.gruppe == "UNIFY" and aufgeloest.code == "U4"

    unbelegt = ls._klassifiziere("b", "f.yaml", "S9 — IBCS Z9")
    assert unbelegt.gruppe is None and unbelegt.code is None


def test_repo_source_numbering_is_not_mistaken_for_an_ibcs_code():
    """Der Falschtreffer, den der erste Fix erzeugt hat.

    „S9 — IBCS; S11 — Tufte" enthaelt hinter „IBCS" das repo-eigene Quellenkuerzel
    S11. Ohne Beleg in der gelernten Tabelle darf es kein IBCS-Regelcode werden —
    sonst meldet die Sicht Abdeckung, die es nicht gibt.
    """
    ls._lerne_codes(["S9 — IBCS UNIFY U4", "S9 — IBCS EXPRESS E3"])
    r = ls._klassifiziere("c", "f.yaml", "S9 — IBCS; S11 — Tufte")
    assert r.vom_system
    assert r.code is None, f"S11 faelschlich als IBCS-Code uebernommen: {r.code}"


def test_empty_groups_are_a_content_gap_not_a_tagging_gap():
    """CONDENSE/SIMPLIFY/STRUCTURE sind leer — und das bleibt so, bis echte
    IBCS-Regeln dazukommen.

    Es GIBT Regeln mit aehnlichem Ziel (Miller zur Arbeitsgedaechtnisgrenze,
    Few zur Sortierung, Layout_Grid_System zur Gliederung). Sie als IBCS
    auszuzeichnen waere eine Faelschung der Herkunft: sie wuerden dann als beim
    Systemwechsel austauschbar gelten, obwohl eine perzeptuelle Regel unabhaengig
    von jeder Notation gilt. Der Test haelt diese Grenze fest.
    """
    deckung = ls.abdeckung(ls.sammle())
    for gruppe in ("CONDENSE", "SIMPLIFY", "STRUCTURE"):
        assert deckung[gruppe] == [], (
            f"{gruppe} ist belegt — falls durch echte IBCS-Regeln: Test anpassen, "
            f"das ist Fortschritt. Falls durch Umetikettierung von Miller/Few/"
            f"Craft-Core: rueckgaengig machen, das faelscht die Herkunft.")
