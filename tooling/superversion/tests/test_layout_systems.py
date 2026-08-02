"""Tests fuer die Herkunftssicht auf die governten Regeln (L6).

Die Sicht legt keinen Regelspeicher an — sie liest die drei vorhandenen. Getestet
wird deshalb die Klassifikation (was ist IBCS, was Fremdstandard, was Hausregel),
nicht der Regelinhalt.
"""
from __future__ import annotations

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
    assert not tufte.ibcs and tufte.success_gruppe is None
    assert tufte.fremdstandard == "Tufte"

    echt = ls._klassifiziere("y", "f.yaml", "S9 — IBCS UNIFY U4")
    assert echt.ibcs and echt.success_gruppe == "UNIFY" and echt.ibcs_code == "U4"

    ohne_code = ls._klassifiziere("z", "f.yaml", "S9 — IBCS scenario notation")
    assert ohne_code.ibcs and ohne_code.ibcs_code is None


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
    ohne = [r.rule_id for r in ls.sammle() if r.ibcs and not r.success_gruppe]
    assert ohne == [], f"IBCS-Regeln ohne SUCCESS-Gruppe: {ohne}"


def test_bare_code_resolves_only_from_repo_evidence():
    """„IBCS U4" ohne Gruppe wird aufgeloest — aber nur aus im Repo Belegtem.

    Aus dem Anfangsbuchstaben zu raten waere unzulaessig: S ist SAY, SIMPLIFY ODER
    STRUCTURE; C ist CONDENSE ODER CHECK. Die Tabelle wird deshalb aus Stellen
    gelernt, die BEIDES nennen.
    """
    ls._lerne_codes(["S9 — IBCS UNIFY U4"])
    aufgeloest = ls._klassifiziere("a", "f.yaml", "S9 — IBCS U4")
    assert aufgeloest.success_gruppe == "UNIFY" and aufgeloest.ibcs_code == "U4"

    unbelegt = ls._klassifiziere("b", "f.yaml", "S9 — IBCS Z9")
    assert unbelegt.success_gruppe is None and unbelegt.ibcs_code is None


def test_repo_source_numbering_is_not_mistaken_for_an_ibcs_code():
    """Der Falschtreffer, den der erste Fix erzeugt hat.

    „S9 — IBCS; S11 — Tufte" enthaelt hinter „IBCS" das repo-eigene Quellenkuerzel
    S11. Ohne Beleg in der gelernten Tabelle darf es kein IBCS-Regelcode werden —
    sonst meldet die Sicht Abdeckung, die es nicht gibt.
    """
    ls._lerne_codes(["S9 — IBCS UNIFY U4", "S9 — IBCS EXPRESS E3"])
    r = ls._klassifiziere("c", "f.yaml", "S9 — IBCS; S11 — Tufte")
    assert r.ibcs
    assert r.ibcs_code is None, f"S11 faelschlich als IBCS-Code uebernommen: {r.ibcs_code}"


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
