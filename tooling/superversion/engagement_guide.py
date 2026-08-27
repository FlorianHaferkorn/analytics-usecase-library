"""engagement_guide — the consultant's side of the sheet: what to ask when, and where it lands.

`open_questions` says **what** is open. `answers` says **where** an answer goes. Neither
says in what order to ask, what exists afterwards, or what has to hold before the next
conversation is worth having. That is this module, and it is the consultant-facing half of
`SHARED_SUBSTANCE.md` **class C** — the same capability as Meridian's `beraterleitfaden`,
cut along ALUCA's own axis rather than translated from it.

## Why the sessions are cut this way

Meridian cuts by sales stage, because its questions come from a sales-shaped intake. ALUCA's
questions come from its own input contract, and that contract has three natural strata,
which the ledger already carries in the `origin` field:

* what the deriver **needs and did not get** — nothing can be derived without it;
* what the deriver **decided silently** — everything works, and the customer may disagree;
* the **mirrored shared decisions** — they belong to the architecture, not to the input shape.

Cutting anywhere else would mean maintaining a second classification beside `origin`, and a
second classification is the thing that drifts. So the session of a question is a function of
the ledger, not a list somebody keeps in step by hand.

## The agenda is derived, not written

Each session's length follows from what is actually open: an opener, a per-question budget
that differs by how much work the question is, and a close. A hand-written agenda says forty
minutes whether there are three questions or thirty. This one cannot.

## Two pledges, both gated

* **Every row carries a source.** Where the question comes from, file and field. Without it
  this document becomes the second question catalogue and the first one starts to rot.
* **Every row carries a target.** Where the answer lands, read from `answers.TARGETS` — the
  same map the return path uses, so the guide cannot promise a destination the write path
  does not have.

`rows_without_provenance` is the gate for both.

No durations beyond the minutes inside a session. What is scheduled is the next session, and
the condition for it is the gate, not an estimate.
"""
from __future__ import annotations

from typing import Any

from tooling.superversion.answers import (
    ABSENT,
    RECORD,
    STRUCTURAL,
    address,
    target_for,
)
from tooling.superversion.open_questions import (
    ORIGIN_DEFAULT,
    ORIGIN_INPUTS,
    ORIGIN_MIRROR,
    STATUS_PROPOSED,
)

SCHEMA_VERSION = "0.1.0"
GUIDE_PATH = "ENGAGEMENT_GUIDE.md"

S1, S2, S3 = "S1", "S2", "S3"

#: The three sessions. `origin` is the selector, so a question added to the ledger lands in a
#: session without anyone editing this table.
SESSIONS: tuple[dict[str, Any], ...] = (
    {
        "id": S1,
        "origin": ORIGIN_INPUTS,
        "name": "Scope",
        "purpose": "Establish what the platform is being built out of: which domains own "
                   "data, what each publishes, and what feeds it. Nothing downstream can "
                   "be derived before this holds.",
        "who": ("The sponsor", "One person per candidate domain who answers for its numbers",
                "Whoever administers the current gateway or data platform"),
        "produces": "A complete inputs.json for derive_blueprint",
        "command": "python -m tooling.superversion.architecture_blueprint_cli "
                   "--inputs inputs.json --dest out/",
        "gate": "derive_blueprint reports no HITL gaps, and the run writes a schema-valid "
                "blueprint.json.",
    },
    {
        "id": S2,
        "origin": ORIGIN_DEFAULT,
        "name": "Defaults review",
        "purpose": "Walk the decisions the deriver made without asking. Each one already "
                   "has a value and already works; the session exists so the customer can "
                   "disagree while disagreeing is still cheap.",
        "who": ("The domain owners", "Whoever fields the complaint when two numbers disagree",
                "For the platform choice: whoever owns the Microsoft agreement"),
        "produces": "An answer document (aluca/open-question-answers/v1)",
        "command": "python -m tooling.superversion.answers_cli --answers answers.json "
                   "--inputs inputs.json --dest out/            # dry run, prints the diff",
        "gate": "Every default is either confirmed or contradicted with a value, and the "
                "answer document applies without a blocker.",
    },
    {
        "id": S3,
        "origin": ORIGIN_MIRROR,
        "name": "Architecture and security decisions",
        "purpose": "Take the shared decision set: access, classification, retention, "
                   "network, capacity. Most arrive with a proposal, so the work is "
                   "confirming or overriding rather than starting from a blank page. The "
                   "rows below are German: they are byte-identical to Meridian's, and "
                   "translating them on this side would fork a shared asset into two "
                   "wordings that drift.",
        "who": ("IT and platform", "Security and identity", "Data protection",
                "Whoever signs for capacity"),
        "produces": "decisions.json beside the run",
        "command": "python -m tooling.superversion.answers_cli --answers answers.json "
                   "--inputs inputs.json --dest out/ --release",
        "gate": "No proposal is left unanswered. A proposal nobody contradicted is a "
                "decision only if somebody said so.",
    },
)

_SESSION_BY_ORIGIN = {s["origin"]: s for s in SESSIONS}

#: Minutes per question, by how much work the question actually is. An input question opens
#: a discussion; a default is a yes or a correction; a proposal is read out and confirmed.
_BUDGET_DEFAULT = 5
_BUDGET = {
    ORIGIN_INPUTS: 15,
    ORIGIN_DEFAULT: 5,
    ORIGIN_MIRROR: 8,
}
#: A mirrored decision without a proposal starts from nothing and costs the difference.
_NO_PROPOSAL_SURCHARGE = 4
_OPENER = 10
_CLOSER = 10


def _minutes(question: dict[str, Any]) -> int:
    cost = _BUDGET.get(question.get("origin", ""), _BUDGET_DEFAULT)
    if question.get("origin") == ORIGIN_MIRROR and question.get("status") != STATUS_PROPOSED:
        cost += _NO_PROPOSAL_SURCHARGE
    return cost


def _clock(start: str, offset_minutes: int) -> str:
    hh, _, mm = start.partition(":")
    total = int(hh) * 60 + int(mm) + offset_minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def _row(question: dict[str, Any]) -> dict[str, Any]:
    """One ledger question as a guide row: what to ask, where it came from, where it goes."""
    target = target_for(question)
    return {
        "id": question.get("id", ""),
        "topic": question.get("topic", ""),
        "question": question.get("question", ""),
        "status": question.get("status", ""),
        "origin": question.get("origin", ""),
        "source": question.get("source", ""),
        "target": address(target, "<scope>") if target["kind"] not in (RECORD, ABSENT)
                  else target["field"],
        "target_kind": target["kind"],
        "proposal": question.get("proposal") or "",
        "minutes": _minutes(question),
        "prepare": _prepare(question, target),
    }


def _prepare(question: dict[str, Any], target: dict[str, Any]) -> str:
    """What we bring to the session, so the customer corrects a hypothesis instead of
    filling in a blank. Derived from what the ledger already holds about the question."""
    if question.get("proposal"):
        return "A proposal with its reasoning; the customer confirms or overrides."
    if question.get("status") == "preset" and question.get("applied"):
        return f"The value already applied: `{question['applied']}`. Read it out, then ask."
    if target["kind"] == STRUCTURAL:
        return ("The existing report landscape as the starting list — what is refreshed on a "
                "schedule is the honest inventory.")
    way = question.get("way") or {}
    if way.get("where"):
        return f"Where to look, agreed beforehand: {way['where']}"
    return "No prepared position — this one is genuinely open."


def build_guide(ledger: dict[str, Any], *, customer: str = "",
                start_time: str = "09:00") -> dict[str, Any]:
    """Ledger → the guide. Deterministic, pure reads, no I/O."""
    rows = [_row(q) for q in ledger.get("questions", []) if q.get("source")]
    sessions: list[dict[str, Any]] = []
    for spec in SESSIONS:
        mine = [r for r in rows if r["origin"] == spec["origin"]]
        # Proposals first inside a session: a row that only needs confirming is cheaper to
        # work through, and a reader who runs out of patience should run out of it late.
        mine.sort(key=lambda r: (not r["proposal"], r["id"]))
        blocks, offset = [], 0
        blocks.append({"start": _clock(start_time, offset), "minutes": _OPENER,
                       "title": "Opener",
                       "outcome": "Purpose of the session and the gate it has to clear, "
                                  "stated before the first question."})
        offset += _OPENER
        for r in mine:
            blocks.append({"start": _clock(start_time, offset), "minutes": r["minutes"],
                           "title": f"{r['id']} · {r['topic']}", "outcome": r["question"],
                           "row": r["id"]})
            offset += r["minutes"]
        blocks.append({"start": _clock(start_time, offset), "minutes": _CLOSER,
                       "title": "Close",
                       "outcome": "The gate walked through, and either the next session "
                                  "scheduled or the reason it is not."})
        offset += _CLOSER
        sessions.append({**{k: spec[k] for k in
                            ("id", "name", "purpose", "who", "produces", "command", "gate")},
                         "rows": mine, "blocks": blocks, "minutes": offset,
                         "ends": _clock(start_time, offset)})

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tooling.superversion.engagement_guide",
        "customer": customer,
        "start_time": start_time,
        "sessions": sessions,
        "structural": [r for r in rows if r["target_kind"] == STRUCTURAL],
        "mirror_note": ledger.get("mirror_note", ""),
        "summary": {
            "rows": len(rows),
            "unplaced": len([q for q in ledger.get("questions", [])
                             if q.get("origin") not in _SESSION_BY_ORIGIN]),
            "minutes": sum(s["minutes"] for s in sessions),
            "without_provenance": len(rows_without_provenance(
                {"sessions": sessions, "structural": []})),
        },
    }


def rows_without_provenance(guide: dict[str, Any]) -> list[str]:
    """The gate: rows that do not say where the question came from or where the answer goes.

    Both halves matter and for opposite reasons. Without a source this becomes a second
    question catalogue. Without a target it promises the customer a destination the write
    path does not have — which is exactly the defect measured on 26.08.2026, when three of
    the seven defaults could not be contradicted at all.
    """
    return sorted(r["id"] for s in guide.get("sessions", []) for r in s.get("rows", [])
                  if not r.get("source") or r.get("target_kind") == ABSENT)


def guide_markdown(guide: dict[str, Any]) -> str:
    """The document the consultant works down."""
    who = f" — {guide['customer']}" if guide.get("customer") else ""
    s = guide["summary"]
    out = [f"# Engagement guide{who}", "",
           f"{s['rows']} questions over {len(guide['sessions'])} sessions, "
           f"{s['minutes']} minutes of question time in total. Every row says where the "
           f"question comes from and where its answer lands; a row that cannot say both is "
           f"not printed.", ""]
    if s["unplaced"]:
        out += [f"{s['unplaced']} questions carry an origin no session claims. They are "
                "missing from this guide, not answered.", ""]

    for sess in guide["sessions"]:
        out += [f"## {sess['id']} · {sess['name']}", "", sess["purpose"], "",
                f"**Who is in the room:** {'; '.join(sess['who'])}", "",
                f"**What exists afterwards:** {sess['produces']}", "",
                "```", sess["command"], "```", "",
                f"**Before the next session:** {sess['gate']}", ""]
        if not sess["rows"]:
            out += ["Nothing open in this stratum for this engagement — the session is not "
                    "needed.", ""]
            continue
        out += [f"### Agenda ({sess['minutes']} minutes, ends {sess['ends']})", "",
                "| Time | Min | Block | Outcome |", "|---|---|---|---|"]
        out += [f"| {b['start']} | {b['minutes']} | {b['title']} | {b['outcome']} |"
                for b in sess["blocks"]]
        out += ["", "### Questions", ""]
        for r in sess["rows"]:
            out += _row_block(r)
    if guide["structural"]:
        out += ["## Answers that need a new input document", "",
                "These do not go into a field. Collect them as a list and re-run the "
                "derivation; writing them mechanically would mean inventing the parts the "
                "answer did not supply.", ""]
        out += [f"- {r['id']} · {r['topic']}: {r['question']}" for r in guide["structural"]]
        out.append("")
    if guide.get("mirror_note"):
        out += ["## Not in this guide", "",
                f"The mirrored decision set could not be read: {guide['mirror_note']}. "
                "Session S3 is incomplete, not empty.", ""]
    return "\n".join(out).rstrip() + "\n"


def _row_block(r: dict[str, Any]) -> list[str]:
    block = [f"#### {r['id']} · {r['topic']}", "", f"**{r['question']}**", ""]
    if r["proposal"]:
        block += [f"Our proposal: {r['proposal']}", ""]
    block += [f"Bring to the table: {r['prepare']}", "",
              f"Answer lands in: `{r['target']}`"
              if r["target_kind"] != RECORD else
              "Answer lands in: `decisions.json` beside the run — this contract has no "
              "field for a shared decision.", "",
              f"<sub>Source: {r['source']}</sub>", ""]
    return block
