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
