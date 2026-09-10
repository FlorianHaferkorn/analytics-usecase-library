"""answers — the way back: an answered question becomes an input, or it says why not.

`open_questions` builds the sheet a customer reads. Until now the sheet had no return
path: a customer could contradict a default, and the contradiction landed in a document
nobody re-read. This module is the return path, and it is the second half of
`SHARED_SUBSTANCE.md` **class C** — Meridian solves the same problem against a flat
profile of eighteen intake fields, ALUCA solves it against its own nested input contract,
where an answer is rarely a scalar. "Read this source in place instead of copying it" is
an answer to *one source of one domain*, not to a field.

## What is measured here rather than assumed

Three of the seven defaults the sheet presented as contradictable could not be
contradicted. Measured 26.08.2026 against `derive_blueprint` before this change: four
attempts to steer the grounding surface, the retrieval strategy and the ownership
boundaries left the derived blueprint byte-identical. Those three now have input fields
(`grounding_surface`, `retrieval_strategy`, `ownership_overrides`), so every question this
repo asks of its own accord has somewhere for its answer to land. `questions_without_a_target`
is the gate that keeps it that way — a question on the sheet with no target is the same
defect as a question with no way to the answer, one step later.

## What deliberately does not get written

* **Structural answers.** "We have three more domains" is not a value in a field, it is a
  different input document. Reported as such, never guessed at.
* **The mirrored decisions.** They are class A and belong to Meridian's profile, which
  ALUCA does not have. Their answers are *recorded* in a sidecar (`decisions.json`) so they
  survive the session, rather than being written into a contract that has no room for them.

## Two hard rules

* Only `write_inputs` and `write_decisions` touch the disk. `plan_answers` is pure and is
  held to it by `test_planning_never_touches_the_disk`.
* A conflict blocks the **whole** write. Applying half the answers leaves a file nobody can
  reason about, and the half that failed is the half that mattered.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tooling.superversion.open_questions import ORIGIN_MIRROR

SCHEMA_VERSION = "0.1.0"

#: The document a filled-in sheet comes back as. Named so a wrong file is refused by name
#: instead of by the first field that fails to parse.
ANSWER_DOCUMENT = "aluca/open-question-answers/v1"

# --- Target kinds -------------------------------------------------------------------
# `scope` is the second half of an address. A scalar needs none; a per-domain value needs a
# domain name; a per-source value needs a source name; a map needs its key.
SCALAR = "scalar"            # inputs.<field>
SCALAR_LIST = "scalar_list"  # inputs.<field>, a list of allowed items
MAP = "map"                  # inputs.<field>[<scope>]
PER_DOMAIN = "per_domain"    # inputs.domains[<scope>].<field>
PER_SOURCE = "per_source"    # inputs.domains[].sources[<scope>].<field>
STRUCTURAL = "structural"    # the answer changes the shape of the input, not a value in it
RECORD = "record"            # no field in this contract; recorded in the sidecar
ABSENT = "absent"            # the question has no target at all — the gate's only offender

SCOPED = (MAP, PER_DOMAIN, PER_SOURCE)


def _t(kind: str, field: str, *, options: tuple[str, ...] = (),
       scopes: tuple[str, ...] = (), note: str = "") -> dict[str, Any]:
    """`options` constrains the answer, `scopes` constrains the address.

    They are separate because a map constrains only its keys: the workload classes are
    fixed, the platform that owns one is whatever the customer runs. Folding both into one
    list refused `informatica` as an owner because it is not a workload class.
    """
    return {"kind": kind, "field": field, "options": options, "scopes": scopes, "note": note}


#: Question id → where its answer lands. One map, read by both this module and the
#: engagement guide, for the same reason `open_questions` keeps one question catalogue: two
#: mappings onto the same question age separately, and the second one ages unnoticed.
TARGETS: dict[str, dict[str, Any]] = {
    "IN-DOMAINS": _t(STRUCTURAL, "domains",
                     note="A new domain is a new input document, not a value in a field."),
    "IN-GOLD": _t(STRUCTURAL, "domains[].gold_products",
                  note="Each product carries a name, a kind and a grain — three fields, "
                       "supplied together or not at all."),
    "IN-SOURCES": _t(STRUCTURAL, "domains[].sources",
                     note="A source brings its own system, access mode and sensitivity."),
    "IN-SILVER-CONTRACT": _t(SCALAR, "silver_contract_ref"),
    "IN-DATA-CONTRACT": _t(PER_DOMAIN, "data_contract_ref"),
    "DEF-STACK": _t(SCALAR, "stack",
                    options=("fabric", "databricks", "snowflake", "eu_sovereign", "air_gap")),
    "DEF-ACCESS": _t(PER_SOURCE, "access_mode", options=("shortcut", "mirror", "copy")),
    "DEF-ENDORSEMENT": _t(PER_DOMAIN, "endorsement", options=("none", "promoted", "certified")),
    "DEF-AUDIENCE": _t(PER_DOMAIN, "intended_audience",
                       options=("internal", "partner", "public")),
    "DEF-GROUNDING": _t(SCALAR_LIST, "grounding_surface", options=("gold", "silver"),
                        note="Bronze is not an option: the deriver drops it and the schema "
                             "refuses it."),
    "DEF-RETRIEVAL": _t(SCALAR, "retrieval_strategy", options=("builtin", "mcp", "both")),
    "DEF-OWNERSHIP": _t(MAP, "ownership_overrides",
                        scopes=("ingestion", "transformation", "serving"),
                        note="The scope is the workload class; the answer is the platform "
                             "that owns it, and that is not a closed list."),
}


def target_for(question: dict[str, Any]) -> dict[str, Any]:
    """The target of one ledger question. Mirrored decisions are recorded, not written."""
    if question.get("origin") == ORIGIN_MIRROR:
        return _t(RECORD, "decisions.json",
                  note="A shared decision. ALUCA's input contract has no field for it, so the "
                       "answer is recorded beside the run instead of written into it.")
    return TARGETS.get(question.get("id", ""), _t(ABSENT, ""))


def questions_without_a_target(ledger: dict[str, Any]) -> list[str]:
    """The gate: ids this repo asks of its own accord and cannot take an answer for.

    Mirrored questions are out of scope on purpose — they have a home, it is just not this
    contract. A question of ALUCA's own with target kind `absent` is a text box that leads
    nowhere, which is the defect this module exists to prevent.
    """
    return sorted(q.get("id", "?") for q in ledger.get("questions", [])
                  if q.get("origin") != ORIGIN_MIRROR
                  and target_for(q)["kind"] == ABSENT)


# --- Reading the inputs -------------------------------------------------------------

def _domain(inputs: dict[str, Any], name: str) -> dict[str, Any] | None:
    for d in inputs.get("domains", []) or []:
        if d.get("name") == name:
            return d
    return None


def _source(inputs: dict[str, Any], name: str) -> tuple[dict[str, Any] | None, str]:
    """The source entry and the domain it sits in. Sources are addressed across all domains
    because that is how the customer names them; a duplicate name is a blocker, not a pick."""
    hits = [(s, d.get("name", "")) for d in inputs.get("domains", []) or []
            for s in d.get("sources", []) or [] if s.get("source") == name]
    if len(hits) > 1:
        return None, f"the source {name!r} exists in {len(hits)} domains — address it per domain"
    if not hits:
        return None, f"no source named {name!r} in the inputs"
    return hits[0][0], ""


def _current(inputs: dict[str, Any], target: dict[str, Any], scope: str) -> tuple[Any, str]:
    """The value the inputs carry today, or the reason the address does not resolve."""
    kind, field = target["kind"], target["field"]
    if kind in (SCALAR, SCALAR_LIST):
        return inputs.get(field), ""
    if kind == MAP:
        return (inputs.get(field) or {}).get(scope), ""
    if kind == PER_DOMAIN:
        dom = _domain(inputs, scope)
        if dom is None:
            return None, f"no domain named {scope!r} in the inputs"
        return dom.get(field), ""
    if kind == PER_SOURCE:
        src, err = _source(inputs, scope)
        if err:
            return None, err
        return src.get(field), ""
    return None, ""


def address(target: dict[str, Any], scope: str) -> str:
    """The human-readable address of a target. Public because the engagement guide
    prints it: guide and write path must name the same place or the guide lies."""
    kind, field = target["kind"], target["field"]
    if kind == PER_DOMAIN:
        return f"domains[{scope}].{field}"
    if kind == PER_SOURCE:
        return f"domains[].sources[{scope}].{field}"
    if kind == MAP:
        return f"{field}[{scope}]"
    return field


def _answer_value(target: dict[str, Any], raw: Any) -> tuple[Any, str]:
    """The answer as the contract wants it, or the reason it is not usable."""
    options = target.get("options") or ()
    if target["kind"] == SCALAR_LIST:
        items = raw if isinstance(raw, list) else [x.strip() for x in str(raw).split(",")]
        items = [str(i).strip() for i in items if str(i).strip()]
        if not items:
            return None, "empty list"
        bad = [i for i in items if options and i not in options]
        if bad:
            return None, f"not allowed here: {', '.join(sorted(set(bad)))}"
        return items, ""
    value = raw if isinstance(raw, str) else str(raw)
    value = value.strip()
    if not value:
        return None, "empty answer"
    if options and value not in options:
        return None, f"not one of {', '.join(options)}"
    return value, ""


# --- The plan -----------------------------------------------------------------------

def plan_answers(doc: dict[str, Any], ledger: dict[str, Any],
                 inputs: dict[str, Any]) -> dict[str, Any]:
    """Answers × ledger × inputs → what would change. Pure: reads three dicts, writes none.

    Every answer ends up in exactly one bucket, so the counts add up and nothing is quietly
    dropped between the sheet and the file.
    """
    if doc.get("document") != ANSWER_DOCUMENT:
        raise ValueError(f"not an answer document: expected {ANSWER_DOCUMENT!r}, "
                         f"got {doc.get('document')!r}")

    by_id = {q.get("id"): q for q in ledger.get("questions", [])}
    applies: list[dict[str, Any]] = []
    already: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    structural: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    seen: dict[str, Any] = {}

    for entry in doc.get("answers", []) or []:
        qid = str(entry.get("id", "")).strip()
        scope = str(entry.get("scope", "")).strip()
        raw = entry.get("answer")
        question = by_id.get(qid)
        if question is None:
            blockers.append({"id": qid or "?", "scope": scope,
                             "reason": "no such question in this ledger — the sheet and the "
                                       "answers are out of step"})
            continue

        target = target_for(question)
        row = {"id": qid, "scope": scope, "topic": question.get("topic", ""),
               "kind": target["kind"], "address": address(target, scope)}

        if target["kind"] == RECORD:
            records.append({**row, "answer": raw, "note": str(entry.get("note", "")),
                            "answered_by": str(entry.get("answered_by", ""))})
            continue
        if target["kind"] == STRUCTURAL:
            structural.append({**row, "answer": raw, "why": target["note"]})
            continue
        if target["kind"] == ABSENT:
            blockers.append({**row, "reason": "this question has no target field"})
            continue
        if target["kind"] in SCOPED and not scope:
            blockers.append({**row, "reason": f"needs a scope ({target['kind']}) and got none"})
            continue
        if target.get("scopes") and scope not in target["scopes"]:
            blockers.append({**row, "reason": f"scope must be one of "
                                              f"{', '.join(target['scopes'])}"})
            continue

        value, why = _answer_value(target, raw)
        if why:
            blockers.append({**row, "reason": why})
            continue
        current, err = _current(inputs, target, scope)
        if err:
            blockers.append({**row, "reason": err})
            continue

        slot = row["address"]
        if slot in seen and seen[slot] != value:
            blockers.append({**row, "reason": f"a second, different answer for {slot}"})
            continue
        seen[slot] = value

        if current == value:
            already.append({**row, "value": value})
        elif current not in (None, "", [], {}):
            blockers.append({**row, "reason": f"the inputs already say {current!r}; an answer "
                                              f"does not overwrite a supplied value"})
        else:
            applies.append({**row, "current": current, "value": value,
                            "field": target["field"]})

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tooling.superversion.answers",
        "applies": applies,
        "already": already,
        "records": records,
        "structural": structural,
        "blockers": blockers,
        "summary": {
            "answers": len(doc.get("answers", []) or []),
            "applies": len(applies),
            "already": len(already),
            "records": len(records),
            "structural": len(structural),
            "blockers": len(blockers),
            "writable": not blockers and bool(applies or records),
        },
    }


def answers_markdown(plan: dict[str, Any], *, released: bool = False) -> str:
    """The diff a human reads before releasing it. Same text before and after the write —
    only the opening line changes, so the two can be compared without re-reading both."""
    s = plan["summary"]
    out = ["# Answers applied" if released else "# Answers — dry run", ""]
    out.append(f"{s['answers']} answers: {s['applies']} would change an input, "
               f"{s['already']} already say what the inputs say, {s['records']} are recorded "
               f"beside the run, {s['structural']} need a new input document, "
               f"{s['blockers']} are blocked."
               if not released else
               f"{s['answers']} answers: {s['applies']} written, {s['already']} already in "
               f"place, {s['records']} recorded, {s['structural']} left for a new input "
               f"document.")
    out.append("")
    if plan["blockers"]:
        out += ["## Blocked", "",
                "Nothing is written while one of these stands. A half-applied answer file is "
                "worse than an unapplied one.", "",
                "| Question | Address | Why |", "|---|---|---|"]
        out += [f"| {b['id']}{(' · ' + b['scope']) if b.get('scope') else ''} "
                f"| `{b.get('address', '')}` | {b['reason']} |" for b in plan["blockers"]]
        out.append("")
    if plan["applies"]:
        out += ["## Changes", "", "| Question | Address | Now | Becomes |", "|---|---|---|---|"]
        out += [f"| {a['id']} · {a['topic']} | `{a['address']}` | "
                f"{'(unset)' if a['current'] in (None, '', [], {}) else repr(a['current'])} | "
                f"`{a['value']}` |" for a in plan["applies"]]
        out.append("")
    if plan["already"]:
        out += ["## Already in place", "",
                "Confirmed rather than changed. They are listed so a confirmation is visible "
                "as an answer and not as silence.", ""]
        out += [f"- {a['id']}{(' · ' + a['scope']) if a.get('scope') else ''}: "
                f"`{a['address']}` is `{a['value']}`" for a in plan["already"]]
        out.append("")
    if plan["records"]:
        out += ["## Recorded beside the run", "",
                "Shared decisions. This contract has no field for them, so they are kept in "
                "`decisions.json` rather than dropped.", ""]
        out += [f"- {r['id']} · {r.get('topic', '')}: {r['answer']}" for r in plan["records"]]
        out.append("")
    if plan["structural"]:
        out += ["## Needs a new input document", "",
                "These answers add or remove structure. Writing them mechanically would mean "
                "inventing the fields the answer did not supply.", ""]
        out += [f"- {q['id']} · {q.get('topic', '')}: {q['why']}" for q in plan["structural"]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --- The write ----------------------------------------------------------------------

class AnswerError(ValueError):
    """The write is not permitted. No partial write, no guess."""


def _guard(plan: dict[str, Any], release: bool) -> None:
    if not release:
        raise AnswerError("dry run: pass release=True to write. Read the diff first.")
    if plan["blockers"]:
        raise AnswerError(f"{len(plan['blockers'])} blocked answers — nothing is written until "
                          "they are resolved")


def write_inputs(path: Path, plan: dict[str, Any], *, release: bool = False) -> list[str]:
    """Apply the plan to the inputs JSON at ``path``. The only function that changes it."""
    _guard(plan, release)
    inputs = json.loads(Path(path).read_text(encoding="utf-8"))
    written: list[str] = []
    for a in plan["applies"]:
        kind, field, scope, value = a["kind"], a["field"], a["scope"], a["value"]
        if kind in (SCALAR, SCALAR_LIST):
            inputs[field] = value
        elif kind == MAP:
            inputs.setdefault(field, {})[scope] = value
        elif kind == PER_DOMAIN:
            dom = _domain(inputs, scope)
            if dom is None:  # pragma: no cover - the plan resolved it against these inputs
                raise AnswerError(f"domain {scope!r} vanished between plan and write")
            dom[field] = value
        elif kind == PER_SOURCE:
            src, err = _source(inputs, scope)
            if err:  # pragma: no cover - same
                raise AnswerError(err)
            src[field] = value
        written.append(f"{a['address']} = {value}")
    Path(path).write_text(
        json.dumps(inputs, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    return written


def write_decisions(path: Path, plan: dict[str, Any], *, release: bool = False) -> list[str]:
    """Write the recorded shared decisions beside the run."""
    _guard(plan, release)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "document": "aluca/recorded-decisions/v1",
        "note": "Answers to the mirrored class-A decisions. They have no field in ALUCA's "
                "input contract; kept here so the session is not lost.",
        "decisions": [{k: r[k] for k in ("id", "topic", "answer", "note", "answered_by")}
                      for r in plan["records"]],
    }
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    return [r["id"] for r in plan["records"]]


def answers_template(ledger: dict[str, Any]) -> dict[str, Any]:
    """An empty answer document with one pre-addressed row per question.

    A blank file makes the consultant look up ids and scopes; a pre-addressed one comes
    back filled in. Scopes are left as a marker rather than guessed, because guessing the
    wrong domain is the one error the plan cannot catch — it resolves.
    """
    rows: list[dict[str, Any]] = []
    for q in ledger.get("questions", []):
        target = target_for(q)
        row: dict[str, Any] = {"id": q.get("id", ""), "answer": ""}
        if target["kind"] in SCOPED:
            row["scope"] = f"<{'workload class' if target['kind'] == MAP else target['kind'][4:]}>"
        row["_question"] = q.get("question", "")
        row["_target"] = address(target, row.get("scope", ""))
        if target.get("options"):
            row["_options"] = list(target["options"])
        if target.get("scopes"):
            row["_scopes"] = list(target["scopes"])
        rows.append(row)
    return {"schema_version": SCHEMA_VERSION, "document": ANSWER_DOCUMENT, "answers": rows}
