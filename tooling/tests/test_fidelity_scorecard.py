"""Treue-Dimension je Ziel-Werkzeug (Task L11).

Was hier NICHT getestet wird — und warum das der wichtigere Teil ist
-------------------------------------------------------------------
Es gibt keinen Test „Ziel X erreicht Y %". Ein eingefrorener Zahlenwert waere eine
Zusicherung ueber den Ausbaustand, nicht ueber die Logik: sobald L9 den Vega-Konnektor
anbindet, steigt sein Wert — und ein Test, der 10 % festschreibt, wuerde den Fortschritt
als Fehler melden. Getestet wird deshalb die **Einstufungslogik** und ihre Monotonie.

Die eine Ausnahme ist `powerbi`: dort ist der Boden vertraglich (jedes Block muss dort
darstellbar sein, `check-floor --required powerbi`), also ist 100 % keine Momentaufnahme,
sondern die Zusicherung selbst.
"""
from __future__ import annotations

import pytest

from tooling.report_quality.report_scorecard import (
    FIDELITY_TIERS,
    BlockFidelity,
    _classify_block,
    fidelity_by_target,
)
from tooling.superversion.layer_tools.visual_library import VisualLibrary


@pytest.fixture(scope="module")
def lib():
    return VisualLibrary.load()


def test_powerbi_is_fully_native(lib):
    """Der Pflicht-Konnektor bildet jede Absicht mit ihrer Erstwahl nativ ab.

    Das ist kein Momentwert: `check-floor` erzwingt den Boden fuer `powerbi`. Faellt
    dieser Test, ist entweder der Boden gebrochen oder ein Block hat seine Erstwahl
    auf eine Eskalation (SVG) umgestellt — beides gehoert gesehen, nicht geschluckt.
    """
    pbi = next(t for t in fidelity_by_target(lib) if t.target == "powerbi")
    assert pbi.score == 100, [f"{d.block_id}: {d.tier}" for d in pbi.deductions]


def test_every_deduction_carries_a_reason(lib):
    """DoD: „Score je (Use Case x Ziel-Tool) mit Begruendung je Abzug."

    Ein Abzug ohne Grund ist eine Zahl, mit der niemand etwas anfangen kann — genau
    die Sorte Scorecard, die man nach zwei Wochen ignoriert.
    """
    for tf in fidelity_by_target(lib):
        for d in tf.deductions:
            assert d.reason and len(d.reason) > 20, f"{tf.target}/{d.block_id}"
            assert d.tier in FIDELITY_TIERS


def test_tiers_are_strictly_ordered():
    """nativ > Ersatz > Eskalation > gar nicht — sonst bewertet die Skala nichts."""
    werte = [FIDELITY_TIERS[t] for t in
             ("native_default", "native_substitute", "escalation", "none")]
    assert werte == sorted(werte, reverse=True)
    assert len(set(werte)) == 4


def test_missing_target_scores_zero_and_names_the_block(lib):
    """Ein Ziel, das es nicht gibt, bekommt 0 % — und sagt, welche Absichten fehlen.

    Wichtiger als die Null ist die Begruendung: eine stille 0 waere von „noch nicht
    gemessen" nicht zu unterscheiden.
    """
    for _, block in lib.blocks.items():
        bf = _classify_block(block, "gibt_es_nicht")
        assert isinstance(bf, BlockFidelity)
        assert bf.tier == "none" and bf.via is None
        assert "keine Darstellung" in bf.reason


def test_escalation_ranks_below_native(lib):
    """Ein per SVG erreichbarer Block darf nicht wie ein nativer zaehlen.

    Das ist die Zeile, die §3.4 in eine Zahl uebersetzt: die Eskalationsleiter
    nativ → SVG → anderes Ziel ist eine Rangfolge, keine Gleichwertigkeit.
    """
    assert FIDELITY_TIERS["escalation"] < FIDELITY_TIERS["native_default"]
    assert FIDELITY_TIERS["escalation"] < FIDELITY_TIERS["native_substitute"]


def test_scores_are_deterministic(lib):
    a = [(t.target, t.score) for t in fidelity_by_target(lib)]
    b = [(t.target, t.score) for t in fidelity_by_target(lib)]
    assert a == b


def test_floor_gaps_and_zero_fidelity_agree(lib):
    """Die Treue-Sicht darf der Boden-Sicht nicht widersprechen.

    `floor_gaps()` und die Stufe `none` beantworten dieselbe Frage aus zwei Richtungen.
    Liefen sie auseinander, haetten wir zwei Wahrheiten ueber die Abdeckung — genau das,
    was ADR-0018 eine Ebene hoeher gerade beendet hat.
    """
    for tf in fidelity_by_target(lib):
        ohne_darstellung = {d.block_id for d in tf.blocks if d.tier == "none"}
        assert ohne_darstellung == set(lib.floor_gaps(tf.target)), tf.target
