"""The consultant's side: what to ask when, and where it lands.

Two pledges carry this document, and both are gated rather than trusted. Every row says
where the question came from — without that this becomes the second question catalogue and
the first one starts to rot. Every row says where the answer goes — read from the same map
the write path uses, so the guide cannot promise a destination that does not exist. That
second half is the one that was actually broken: measured 26.08.2026, three of the seven
defaults on the customer sheet had no input field at all.
"""
from __future__ import annotations

import pytest

from tooling.superversion import answers as A
from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.engagement_guide import (
    SESSIONS,
    _clock,
    build_guide,
    guide_markdown,
    rows_without_provenance,
)
from tooling.superversion.open_questions import collect_open_questions

_INPUTS = {
    "stack": "fabric",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [{"name": "fact_sales", "kind": "fact", "grain": "order line"}],
            "sources": [{"source": "crm", "source_system": "Dynamics 365"}],
        }
    ],
}


@pytest.fixture()
def ledger():
    return collect_open_questions(_INPUTS, derive_blueprint(_INPUTS))


@pytest.fixture()
def guide(ledger):
    return build_guide(ledger, customer="Beispiel GmbH")


# --- the two pledges ------------------------------------------------------------------

def test_every_row_carries_a_source_and_a_target(guide):
    assert rows_without_provenance(guide) == []
    for session in guide["sessions"]:
        for row in session["rows"]:
            assert row["source"], f"{row['id']} has no source"
            assert row["target"], f"{row['id']} has no target"


def test_a_question_without_a_target_is_caught(ledger, monkeypatch):
    """The gate has to fire on the defect it was written for, not only stay green."""
    monkeypatch.setitem(A.TARGETS, "DEF-STACK", A._t(A.ABSENT, ""))
    guide = build_guide(ledger)
    assert rows_without_provenance(guide) == ["DEF-STACK"]


def test_a_question_without_a_source_is_not_printed(ledger):
    ledger["questions"][0].pop("source")
    guide = build_guide(ledger)
    ids = {r["id"] for s in guide["sessions"] for r in s["rows"]}
    assert len(ids) == len(ledger["questions"]) - 1


# --- the cut --------------------------------------------------------------------------

def test_every_question_lands_in_exactly_one_session(guide, ledger):
    placed = [r["id"] for s in guide["sessions"] for r in s["rows"]]
    assert sorted(placed) == sorted(q["id"] for q in ledger["questions"])
    assert len(placed) == len(set(placed))
    assert guide["summary"]["unplaced"] == 0


def test_the_session_follows_the_origin_and_not_a_hand_kept_list(guide):
    """The cut is a function of the ledger. A new question needs no edit here."""
    for session, spec in zip(guide["sessions"], SESSIONS):
        assert {r["origin"] for r in session["rows"]} <= {spec["origin"]}


def test_proposals_come_first_within_a_session(guide):
    for session in guide["sessions"]:
        flags = [not r["proposal"] for r in session["rows"]]
        assert flags == sorted(flags), "a row that only needs confirming is cheaper first"


# --- the agenda -----------------------------------------------------------------------

def test_the_agenda_is_derived_from_what_is_actually_open(ledger):
    """A hand-written agenda says forty minutes whether there are three questions or thirty."""
    short = build_guide(ledger)
    ledger["questions"] = [q for q in ledger["questions"] if q["id"] != "DEF-STACK"]
    shorter = build_guide(ledger)
    assert shorter["summary"]["minutes"] < short["summary"]["minutes"]


def test_the_blocks_are_contiguous_and_add_up(guide):
    for session in guide["sessions"]:
        assert sum(b["minutes"] for b in session["blocks"]) == session["minutes"]
        offset = 0
        for block in session["blocks"]:
            assert block["start"] == _clock(guide["start_time"], offset)
            offset += block["minutes"]
        assert session["ends"] == _clock(guide["start_time"], session["minutes"])


def test_every_block_has_an_outcome(guide):
    for session in guide["sessions"]:
        for block in session["blocks"]:
            assert block["outcome"].strip(), f"{block['title']} has no named outcome"


def test_a_start_time_moves_the_whole_agenda(ledger):
    late = build_guide(ledger, start_time="13:30")
    assert late["sessions"][0]["blocks"][0]["start"] == "13:30"


def test_the_guide_carries_no_effort_estimate(guide):
    """Minutes inside a session are scheduling. Project duration is not ours to state."""
    text = guide_markdown(guide).lower()
    for forbidden in ("person day", "personentag", " fte", "man-day"):
        assert forbidden not in text


# --- the document ---------------------------------------------------------------------

def test_each_session_names_the_command_and_the_gate(guide):
    text = guide_markdown(guide)
    for session in guide["sessions"]:
        assert session["command"] in text
        assert session["gate"] in text
        assert session["produces"] in text


def test_every_printed_row_shows_its_source(guide):
    text = guide_markdown(guide)
    for session in guide["sessions"]:
        for row in session["rows"]:
            assert f"Source: {row['source']}" in text


def test_the_guide_is_deterministic(ledger):
    assert guide_markdown(build_guide(ledger)) == guide_markdown(build_guide(ledger))


def test_an_unreadable_mirror_is_reported_rather_than_left_blank(ledger):
    ledger["mirror_note"] = "vendor pin mismatch"
    text = guide_markdown(build_guide(ledger))
    assert "vendor pin mismatch" in text and "incomplete, not empty" in text
