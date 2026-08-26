"""ALUCA's own answer-path ledger (SHARED_SUBSTANCE class C).

Flo, 17.08.2026: „meridian und aluca müssen austauschbar sein. Je Frage müssen wir eine
Methode haben wie wir den Kunden zu Antworten führen können bei Bedarf."

The decision on that was **Fähigkeits-Parität**: each repo can run an engagement on its
own, ALUCA gets its own shape of the question layer rather than a port. `named_profiles.py`
is class B and stays in Meridian, so these tests check ALUCA's own catalogue — and check
that the class-A half it mirrors arrives intact rather than being re-typed here.
"""
from __future__ import annotations

import pytest

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.open_questions import (
    ORIGIN_DEFAULT,
    ORIGIN_INPUTS,
    ORIGIN_MIRROR,
    STATUS_OPEN,
    STATUS_PRESET,
    WAY_FIELDS,
    collect_open_questions,
    open_questions_markdown,
    questions_without_a_way,
)

# One domain, one source, one gold product — deliberately the thinnest input that still
# derives, because that is the state a real engagement starts in.
_INPUTS = {
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [{"name": "dim_kunde", "kind": "dimension"}],
            "sources": [{"source": "crm", "source_system": "Dynamics 365"}],
        }
    ]
}


@pytest.fixture(scope="module")
def ledger() -> dict:
    return collect_open_questions(_INPUTS, derive_blueprint(_INPUTS))


def test_every_question_carries_a_way_to_its_answer(ledger):
    """The rule Flo asked for, as a gate rather than an intention.

    Measured 17.08.2026 against the input above: 26 questions, **0** without a way. A way is
    the three fields together (where to look, who knows, what holds if it stays unclear); a
    concrete proposal or a set of alternatives counts too, because confirming or picking is
    something a customer can actually do. An empty card is none of those.
    """
    assert questions_without_a_way(ledger) == []


def test_the_gate_fires_when_the_way_is_missing():
    """Counter-check: without this, the test above measures nothing.

    Same card twice — once with a way, once stripped of all three routes to an answer. The
    second must be reported, or the gate is decoration.
    """
    mit = {"questions": [{"id": "X", "way": {"where": "a", "who": "b", "if_unclear": "c"}}]}
    ohne = {"questions": [{"id": "X", "way": {"where": "a", "who": "", "if_unclear": "c"}}]}
    assert questions_without_a_way(mit) == []
    assert questions_without_a_way(ohne) == ["X"], "a partial way is not a way"


def test_the_silent_defaults_are_all_on_the_sheet(ledger):
    """The seven things the deriver decides without being asked.

    Measured 17.08.2026: on the input above `derive_blueprint` reports **one** HITL gap and
    silently sets **seven** values — stack, per-source access mode, endorsement, intended
    audience, grounding surface, retrieval strategy, ownership boundaries. Before this
    module the customer saw the one and none of the seven. Each now appears with the value
    we actually applied, read off the blueprint rather than restated.
    """
    presets = [q for q in ledger["questions"] if q["origin"] == ORIGIN_DEFAULT]
    assert len(presets) == 7
    assert all(q["status"] == STATUS_PRESET for q in presets)
    ohne_wert = [q["id"] for q in presets if not str(q.get("applied", "")).strip()]
    assert not ohne_wert, f"preset without the value we applied: {ohne_wert}"


def test_the_applied_value_is_read_from_the_blueprint_not_restated(ledger):
    """A default shown from a constant would keep saying 'mirror' after the code stopped.

    `access_mode` is derived by a keyword match on the source system name, so it is the one
    that can actually change under us. The sheet must echo the blueprint.
    """
    bp = derive_blueprint(_INPUTS)["blueprint"]
    tatsaechlich = bp["ingestion"][0]["access_mode"]
    karte = next(q for q in ledger["questions"] if q["id"] == "DEF-ACCESS")
    assert tatsaechlich in karte["applied"]
    assert "crm" in karte["applied"]


def test_every_reported_gap_is_attached_to_a_question(ledger):
    """A HITL gap with no question beside it is a sentence with no next step.

    The deriver's gap list stays exactly what it was — other code reads it. Each gap is
    matched by prefix to the question it belongs to; anything unmatched is reported in the
    summary instead of disappearing.
    """
    assert ledger["summary"]["unreported_gaps"] == []
    silber = next(q for q in ledger["questions"] if q["id"] == "IN-SILVER-CONTRACT")
    assert "medallion.silver.data_contract_ref not supplied" in silber["reported_gaps"]


def test_a_supplied_input_does_not_become_a_question(ledger):
    """Domains, gold products and sources were supplied, so they are not asked again.

    An answered question on a sheet is noise the reader has to skip, and skipping trains the
    reader to skip the ones that matter.
    """
    gefragt = {q["id"] for q in ledger["questions"] if q["origin"] == ORIGIN_INPUTS}
    assert gefragt == {"IN-SILVER-CONTRACT", "IN-DATA-CONTRACT"}
    leer = collect_open_questions({}, derive_blueprint({}))
    assert "IN-DOMAINS" in {q["id"] for q in leer["questions"]}


def test_the_mirrored_decisions_arrive_with_their_ways(ledger):
    """The class-A half reaches ALUCA's sheet — including what Meridian added on its side.

    Measured 20.08.2026: 19 mirrored decisions, 7 of them carrying a complete way. Those
    seven are exactly the ones Meridian gained an `ermittlung` block for on 17.08.2026;
    they arrived here through `--write` on the mirror sensor, not by being typed again.
    German field names are translated at this boundary — the vendored file itself is never
    edited, because a local edit breaks the integrity pin by design.

    17 → 18: `GOV-DOMAIN` (who owns a Fabric domain) arrived with Meridian's BK-W02 work.
    18 → 19: `SEC-SHARE` (which ways out of the platform stay open) with BK-Z06, on the same
    day. Both are pre-filled, so neither needs an `ermittlung` block and the second count
    stays at 7.
    """
    mirrored = [q for q in ledger["questions"] if q["origin"] == ORIGIN_MIRROR]
    assert len(mirrored) == 19
    mit_weg = [q for q in mirrored
               if all(str(q["way"].get(f, "")).strip() for f in WAY_FIELDS)]
    assert len(mit_weg) == 7
    assert all(q["source"].startswith("vendor/meridian_dataarch/") for q in mirrored)


def test_a_missing_mirror_is_reported_and_does_not_break_the_run(monkeypatch):
    """ALUCA delivers without the mirror. The mirror is a second half, not a dependency.

    What must not happen is that the eighteen decisions are quietly absent — an incomplete
    sheet that looks complete is worse than one that says what is missing.
    """
    import tooling.superversion.open_questions as oq

    monkeypatch.setattr(oq, "_mirrored_decisions", lambda bp: ([], "vendor pin mismatch"))
    L = oq.collect_open_questions(_INPUTS, derive_blueprint(_INPUTS))
    assert not [q for q in L["questions"] if q["origin"] == ORIGIN_MIRROR]
    assert L["mirror_note"] == "vendor pin mismatch"
    assert "vendor pin mismatch" in oq.open_questions_markdown(L)
    assert "Not included" in oq.open_questions_markdown(L)


def test_a_question_without_a_source_is_never_printed(ledger):
    """The one rule that stops this catalogue becoming the silo it replaces.

    Every question names the file and field it came from. The renderer drops anything that
    does not, so a hand-added question cannot reach a customer untraceable.
    """
    assert all(q.get("source") for q in ledger["questions"])
    md = open_questions_markdown(
        {"questions": [{"id": "NOSRC", "status": STATUS_OPEN, "origin": ORIGIN_INPUTS,
                        "topic": "t", "question": "q"}], "summary": {}})
    assert "NOSRC" not in md


def test_the_sheet_separates_the_mirrored_section(ledger):
    """The German cards get their own heading instead of being scattered through English ones.

    Translating them on this side would fork a byte-identical class-A asset into two
    wordings that then drift — the failure the mirror exists to prevent. Explaining the
    switch is the honest option; hiding it is not available.
    """
    md = open_questions_markdown(ledger)
    assert "## Architecture and security decisions" in md
    assert "byte-identical" in md
    for heading in ("What we still need from you", "What we decided for you"):
        assert f"## {heading}" in md
