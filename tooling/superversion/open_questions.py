"""open_questions — ALUCA's own path from an open question to its answer.

`SHARED_SUBSTANCE.md` **class C**: the same capability as Meridian's `open_points.py`,
deliberately in ALUCA's own shape. Meridian's question catalogue lives in
`named_profiles.py`, which is **class B and is never ported**. ALUCA therefore derives
its questions from its *own* input contract (`architecture_blueprint.derive_blueprint`)
and renders them under its own names — English fields, ALUCA's cut, ALUCA's wording.

Three sources, one list:

  1. **inputs the deriver needs and did not get** → ``status="open"``
  2. **defaults the deriver applies without asking** → ``status="preset"``
  3. **the mirrored Meridian decisions** (class A, already under `vendor/`) → the status
     they were proposed with

Why (2) is in here at all, measured 17.08.2026 against a minimal input (one domain, one
source, one gold product): `derive_blueprint` reported **one** HITL gap and silently set
**seven** things — the stack, the per-source access mode, the endorsement, the intended
audience, the grounding surface, the retrieval strategy and all three ownership
boundaries. `access_mode` came out as ``mirror``, which duplicates the data, and it was
chosen by a substring match on the source system name. None of that reached anyone. A
default is a decision; the only honest difference to an open question is that we already
wrote an answer next to it.

**The rule this module enforces** (`questions_without_a_way`): every question a customer
is expected to answer carries a way to that answer — where to look, who knows it, and
what holds if it stays unclear. A question without one is a blank text box, and a blank
text box comes back blank.

Public API:
  - ``collect_open_questions(inputs, derived) -> dict``  (the ledger)
  - ``questions_without_a_way(ledger) -> list[str]``     (the gate)
  - ``open_questions_markdown(ledger) -> str``           (the sheet)
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "0.1.0"

# The three fields that make a way to an answer usable. All three or none — "ask someone"
# without saying who is not a way, and neither is "look it up" without saying where.
WAY_FIELDS = ("where", "who", "if_unclear")

# Where a question came from. Every question carries one; the renderer refuses to print a
# question without a `source`, so a future catalogue cannot quietly grow a question that
# nobody can trace back to a contract.
ORIGIN_INPUTS = "aluca_inputs"          # the deriver needs it and did not get it
ORIGIN_DEFAULT = "aluca_default"        # the deriver decided it without asking
ORIGIN_MIRROR = "mirrored_decision"     # class A, from vendor/meridian_dataarch

STATUS_OPEN = "open"
STATUS_PRESET = "preset"
STATUS_PROPOSED = "proposed"


def _way(where: str, who: str, if_unclear: str) -> dict[str, str]:
    return {"where": where, "who": who, "if_unclear": if_unclear}


# --- 1. Inputs the deriver needs ---------------------------------------------------
# One entry per field of the `derive_blueprint` inputs contract that a customer has to
# supply. The `source` column is the contract itself, so this catalogue cannot drift from
# the deriver without the drift being visible in one place.

_INPUT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "IN-DOMAINS",
        "topic": "Domain cut",
        "question": "Which business domains should own their own data products?",
        "why": "The domain cut decides the workspace layout and who may publish what. "
               "Everything downstream — workspaces, endorsement, access — hangs off it.",
        "if_unanswered": "Nothing can be derived: without domains there is no mesh and no gold layer.",
        "way": _way(
            where="The existing reporting landscape. Whatever is already delivered as a separate "
                  "report pack for a separate audience is a domain boundary that exists in "
                  "practice; it is usually just not written down anywhere.",
            who="Whoever signs off the reports today — typically the department heads, not IT.",
            if_unclear="Start with the domains that already have a named report owner. A domain "
                       "can be added later; a wrong cut is expensive to undo because workspace "
                       "names and permissions follow it.",
        ),
        "source": "architecture_blueprint.derive_blueprint inputs.domains",
    },
    {
        "id": "IN-GOLD",
        "topic": "Gold data products",
        "question": "Which tables should the domain publish as its finished products?",
        "why": "Gold products are what consumers are allowed to build on. They set the grain "
               "and therefore what the semantic model can answer.",
        "if_unanswered": "The gold layer of that domain stays empty and the domain publishes nothing.",
        "way": _way(
            where="The reports in use today: every table or query a report reads directly is a "
                  "candidate. Look at what is refreshed on a schedule, not at what exists.",
            who="The report authors and the people who maintain the current extracts.",
            if_unclear="Name the two or three tables the domain would miss most if they vanished "
                       "tomorrow, and treat the rest as later additions.",
        ),
        "source": "architecture_blueprint.derive_blueprint inputs.domains[].gold_products",
    },
    {
        "id": "IN-SOURCES",
        "topic": "Source systems",
        "question": "Which source systems feed this domain?",
        "why": "Each source becomes one ingestion entry with its own access mode, and the "
               "access mode decides whether data is copied or read where it lies.",
        "if_unanswered": "The domain has no ingestion and stays empty in the delivery.",
        "way": _way(
            where="The refresh settings of the existing reports and the connection list of the "
                  "current gateway. Both name their sources explicitly.",
            who="Whoever administers the gateway or the current data platform.",
            if_unclear="List the systems by name even when the technical connection is unknown — "
                       "the connection is a lookup, the list of systems is not.",
        ),
        "source": "architecture_blueprint.derive_blueprint inputs.domains[].sources",
    },
    {
        "id": "IN-SILVER-CONTRACT",
        "topic": "Silver data contract",
        "question": "Which data contract does the cleaned (silver) layer have to satisfy?",
        "why": "The contract is what makes the silver layer checkable. Without it, "
               "'cleaned' means whatever the last person to touch it thought it meant.",
        "if_unanswered": "The silver layer is delivered without a contract reference and nothing "
                         "downstream can be validated against an agreed shape.",
        "way": _way(
            where="An existing interface description, a field list agreed with the source owner, "
                  "or an ODCS contract if one is already in use. ALUCA can generate one from a "
                  "source introspection — see `odcs.import_sql_table`.",
            who="The owner of the source system together with whoever consumes the data today.",
            if_unclear="Deliver without it and record it as open. This is the one gap ALUCA has "
                       "always reported; it is worth answering, but it does not block the build.",
        ),
        "source": "architecture_blueprint.derive_blueprint inputs.silver_contract_ref",
    },
    {
        "id": "IN-DATA-CONTRACT",
        "topic": "Domain data contract",
        "question": "Does this domain already have an agreed contract for what it publishes?",
        "why": "A domain contract fixes what consumers may rely on, so the domain can change "
               "internals without breaking them.",
        "if_unanswered": "Consumers rely on whatever they happen to see, and every internal change "
                         "becomes a potential outage for someone we never spoke to.",
        "way": _way(
            where="Existing service or interface agreements between the department and its "
                  "consumers — often informal, often in a mail thread rather than a document.",
            who="The domain owner and the largest consumer of that domain's data.",
            if_unclear="Leave it open. ALUCA emits an ODCS contract from the derived gold layer, "
                       "which is a defensible starting point to agree on.",
        ),
        "source": "architecture_blueprint.derive_blueprint inputs.domains[].data_contract_ref",
    },
]


# --- 2. The defaults the deriver applies without asking -----------------------------
# Measured 17.08.2026 (see the module docstring). These are decisions; they are shown with
# the value we picked so the customer can contradict, not so he can admire our defaults.

_DEFAULT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "DEF-STACK",
        "topic": "Target platform",
        "question": "Is Microsoft Fabric the target platform?",
        "why": "Every emitted artifact is stack-specific. The choice is cheap now and expensive "
               "after the first workspace exists.",
        "if_unanswered": "We build on Fabric.",
        "way": _way(
            where="The existing licence agreement and what the organisation already runs. An "
                  "existing Power BI Premium or Fabric capacity usually settles it.",
            who="Whoever owns the Microsoft agreement — typically IT purchasing, not the "
                "department.",
            if_unclear="Fabric holds. ALUCA emits for Databricks and Snowflake from the same "
                       "core, so the decision is reversible at the cost of a re-render.",
        ),
        "source": "architecture_blueprint.derive_blueprint inputs.stack (default 'fabric')",
    },
    {
        "id": "DEF-ACCESS",
        "topic": "Access mode per source",
        "question": "Should this source be copied into the lake, or read where it lies?",
        "why": "A copy costs storage and goes stale between refreshes; reading in place keeps one "
               "version but puts load on the source system. ALUCA picks by a keyword match on the "
               "system name, which is a guess dressed as a rule.",
        "if_unanswered": "Databases are mirrored (copied), everything else is shortcut (read in place).",
        "way": _way(
            where="The source system's own load profile and its maintenance windows. A system that "
                  "is already under pressure at month end should not also serve reporting reads.",
            who="The administrator of the source system.",
            if_unclear="Keep the default and record it. This one is genuinely reversible — the "
                       "access mode can be changed per source without touching anything else.",
        ),
        "source": "architecture_blueprint._access_mode (keyword match on source_system)",
    },
    {
        "id": "DEF-ENDORSEMENT",
        "topic": "Endorsement",
        "question": "Should the domain's data products be marked as promoted, or certified?",
        "why": "Certification is a statement that someone stands behind the numbers. Promotion says "
               "'we think this is good'. Users read the badge and act on it.",
        "if_unanswered": "Everything is published as promoted.",
        "way": _way(
            where="Whether a certification process exists at all today. Certification without a "
                  "named reviewer and a review rhythm is a label, not a control.",
            who="Data governance, or whoever would have to defend a number in front of management.",
            if_unclear="Promoted holds. Certifying something nobody reviews is worse than not "
                       "certifying it.",
        ),
        "source": "architecture_blueprint.derive_blueprint domains[].endorsement (default 'promoted')",
    },
    {
        "id": "DEF-AUDIENCE",
        "topic": "Intended audience",
        "question": "Who is allowed to see this domain's data products?",
        "why": "The audience decides how far the data may travel — internal, partners, or public. "
               "It is the cheapest control we have and the one most often left unset.",
        "if_unanswered": "Everything is internal.",
        "way": _way(
            where="The current distribution list of the reports that carry the same numbers. Who "
                  "receives the report today is who sees the data today.",
            who="The domain owner; for anything leaving the organisation, also legal or data "
                "protection.",
            if_unclear="Internal holds. Widening the audience later is a setting; narrowing it "
                       "after people have grown used to the data is a conversation.",
        ),
        "source": "architecture_blueprint.derive_blueprint domains[].intended_audience (default 'internal')",
    },
    {
        "id": "DEF-GROUNDING",
        "topic": "AI grounding surface",
        "question": "Which layers may an AI assistant read — gold only, or gold and silver?",
        "why": "The grounding surface is what an assistant can quote back to a user. Silver is "
               "cleaned but not yet agreed, so an answer from silver can be defensible and still "
               "contradict the official report.",
        "if_unanswered": "Assistants ground on gold and silver. Bronze is never exposed.",
        "way": _way(
            where="Whether the silver layer already has a contract (see IN-SILVER-CONTRACT). "
                  "Grounding on an uncontracted layer is what produces two different right answers.",
            who="The domain owner together with whoever will field the complaint when two numbers "
                "disagree.",
            if_unclear="Restrict to gold. It is the narrower answer and the one that is easy to "
                       "widen once silver has a contract.",
        ),
        "source": "architecture_blueprint.derive_blueprint ai_grounding.grounding_surface",
    },
    {
        "id": "DEF-RETRIEVAL",
        "topic": "Retrieval strategy",
        "question": "Should assistants use the platform's built-in retrieval?",
        "why": "Built-in retrieval keeps the permission model of the platform. A separate index "
               "means a second permission model that has to be kept in step with the first.",
        "if_unanswered": "Built-in retrieval, authentication required.",
        "way": _way(
            where="Whether a search or vector index is already in use elsewhere in the "
                  "organisation, and whether it carries user identity.",
            who="Whoever runs the existing AI or search tooling.",
            if_unclear="Built-in holds. It is the only option that cannot silently show someone "
                       "data they may not see.",
        ),
        "source": "architecture_blueprint.derive_blueprint ai_grounding.retrieval[].strategy",
    },
    {
        "id": "DEF-OWNERSHIP",
        "topic": "Ownership boundaries",
        "question": "Should ingestion, transformation and serving all run on the same platform?",
        "why": "Splitting them across platforms is legitimate — an existing ETL tool may keep "
               "ingestion — but each split is a handover that needs an owner and a monitor.",
        "if_unanswered": "All three run on the target platform.",
        "way": _way(
            where="The tools already under contract and already staffed. An ETL tool with a team "
                  "around it is a reason to split; one that a single person maintains is not.",
            who="The platform owner on the customer side.",
            if_unclear="Keep all three on one platform. Every boundary added here is a boundary "
                       "somebody has to operate afterwards.",
        ),
        "source": "architecture_blueprint.derive_blueprint platform.ownership_boundaries",
    },
]


# --- The HITL gaps ALUCA already reported -------------------------------------------
# The deriver emits gaps as flat strings. They stay strings there (that is the deriver's
# own honesty contract and other code reads it), and they are matched by prefix here so a
# gap cannot appear on the sheet without a way to answer it. Prefix, not equality: two of
# the four carry a domain name.

_HITL_TO_QUESTION: tuple[tuple[str, str], ...] = (
    ("no domains supplied", "IN-DOMAINS"),
    ("gold.data_products underspecified", "IN-GOLD"),
    ("medallion.silver.data_contract_ref not supplied", "IN-SILVER-CONTRACT"),
    ("data-vault: silver business-vault modeling", "IN-DOMAINS"),
)


def _question_for_gap(gap: str) -> str | None:
    for prefix, qid in _HITL_TO_QUESTION:
        if gap.startswith(prefix):
            return qid
    return None


# --- 3. The mirrored decisions ------------------------------------------------------
# The vendored module is byte-identical to Meridian's and carries German field names. It
# is **not** edited to suit ALUCA — that would break the integrity pin and the whole point
# of mirroring. The translation happens here, on ALUCA's side of the boundary.

_MIRROR_FIELD_MAP = {"wo": "where", "wen": "who", "wenn_unklar": "if_unclear"}


def _translate_decision(dec: dict[str, Any]) -> dict[str, Any]:
    """One mirrored proposal → one ALUCA question. Pure renaming, no re-judgement."""
    way_de = dec.get("ermittlung") or {}
    way = {en: str(way_de.get(de, "")).strip() for de, en in _MIRROR_FIELD_MAP.items()}
    return {
        "id": dec["id"],
        "topic": dec.get("topic", ""),
        "question": dec.get("gap", ""),
        "why": dec.get("derived_from", ""),
        "if_unanswered": dec.get("if_undecided", ""),
        "way": way if any(way.values()) else {},
        "options": list(dec.get("alternatives") or []),
        "proposal": dec.get("proposal"),
        "decider": dec.get("decider", ""),
        "origin": ORIGIN_MIRROR,
        "status": STATUS_PROPOSED if dec.get("proposal") else STATUS_OPEN,
        "source": f"vendor/meridian_dataarch/decision_proposals.py::{dec['id']}",
    }


def _mirrored_decisions(blueprint: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """The class-A decisions, or an empty list plus the reason the mirror is unusable.

    Soft-skip by design: ALUCA must deliver without the mirror (the mirror is a bonus half,
    not a dependency), and a missing mirror is reported rather than silently absent.
    """
    try:
        from tooling.superversion._dataarch_vendor import VendorUnavailable, load_emitters
    except ImportError as exc:  # pragma: no cover - loader ships with the repo
        return [], f"vendor loader unavailable ({exc})"
    try:
        api = load_emitters()
    except VendorUnavailable as exc:
        return [], str(exc)
    return [_translate_decision(d) for d in api["propose_all"](blueprint)], ""


# --- The ledger ---------------------------------------------------------------------


def collect_open_questions(inputs: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
    """Build ALUCA's question ledger from its own inputs, its own defaults and the mirror.

    ``inputs`` is what went into `derive_blueprint`; ``derived`` is what came out
    (``{"blueprint": …, "hitl": […]}``). Both are needed: the inputs say what was *not*
    supplied, the blueprint says what we filled in instead.
    """
    blueprint = derived.get("blueprint", {})
    gaps = list(derived.get("hitl", []))
    domains_in = list(inputs.get("domains", []))

    questions: list[dict[str, Any]] = []

    # (1) Inputs. A question is open when the field is missing; when it was supplied it does
    # not appear at all — an answered question on a sheet is noise the reader has to skip.
    supplied_gold = all(d.get("gold_products") for d in domains_in) if domains_in else False
    supplied_sources = all(d.get("sources") for d in domains_in) if domains_in else False
    supplied_contract = all(d.get("data_contract_ref") for d in domains_in) if domains_in else False
    have = {
        "IN-DOMAINS": bool(domains_in),
        "IN-GOLD": supplied_gold,
        "IN-SOURCES": supplied_sources,
        "IN-SILVER-CONTRACT": bool(inputs.get("silver_contract_ref")),
        "IN-DATA-CONTRACT": supplied_contract,
    }
    for q in _INPUT_QUESTIONS:
        if have.get(q["id"], False):
            continue
        entry = dict(q)
        entry.update({"origin": ORIGIN_INPUTS, "status": STATUS_OPEN, "options": []})
        # A gap the deriver itself reported is evidence, not a second question: it is
        # attached to the question it belongs to instead of appearing beside it.
        entry["reported_gaps"] = [g for g in gaps if _question_for_gap(g) == q["id"]]
        questions.append(entry)

    # (2) Defaults. Always shown, with the value we actually used, so "we decided this for
    # you" is a sentence the customer reads rather than one he later discovers.
    applied = _applied_defaults(inputs, blueprint)
    for q in _DEFAULT_QUESTIONS:
        entry = dict(q)
        entry.update({
            "origin": ORIGIN_DEFAULT,
            "status": STATUS_PRESET,
            "options": [],
            "applied": applied.get(q["id"], ""),
        })
        questions.append(entry)

    # (3) The mirrored decisions.
    decisions, mirror_note = _mirrored_decisions(blueprint)
    questions.extend(decisions)

    without_way = questions_without_a_way({"questions": questions})
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tooling.superversion.open_questions",
        "stack": blueprint.get("platform", {}).get("stack", ""),
        "questions": questions,
        "mirror_note": mirror_note,
        "summary": {
            "total": len(questions),
            "open": sum(1 for q in questions if q["status"] == STATUS_OPEN),
            "preset": sum(1 for q in questions if q["status"] == STATUS_PRESET),
            "proposed": sum(1 for q in questions if q["status"] == STATUS_PROPOSED),
            "without_a_way": len(without_way),
            "unreported_gaps": [g for g in gaps if _question_for_gap(g) is None],
        },
    }


def _applied_defaults(inputs: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, str]:
    """What the deriver actually filled in — read off the blueprint, never restated."""
    mesh = blueprint.get("mesh", {}).get("domains", [])
    grounding = blueprint.get("ai_grounding", {})
    ingestion = blueprint.get("ingestion", [])
    publishing = mesh[0].get("publishing", {}) if mesh else {}
    retrieval = grounding.get("retrieval") or [{}]
    owners = sorted({o.get("owner_platform", "") for o in blueprint.get("platform", {}).get(
        "ownership_boundaries", [])})
    return {
        "DEF-STACK": blueprint.get("platform", {}).get("stack", ""),
        "DEF-ACCESS": "; ".join(f"{e.get('source')}: {e.get('access_mode')}" for e in ingestion),
        "DEF-ENDORSEMENT": str(publishing.get("endorsement", "")),
        "DEF-AUDIENCE": str(publishing.get("intended_audience", "")),
        "DEF-GROUNDING": ", ".join(grounding.get("grounding_surface") or []),
        "DEF-RETRIEVAL": str(retrieval[0].get("strategy", "")),
        "DEF-OWNERSHIP": ", ".join(owners),
    }


def questions_without_a_way(ledger: dict[str, Any]) -> list[str]:
    """The gate: ids of questions the customer is expected to answer with no way to answer.

    A proposal counts as a way — confirming a concrete suggestion is something anyone can
    do. So does a complete set of options. What does not count is a question with an empty
    `way` and nothing to react to, which is a blank text box.
    """
    offenders: list[str] = []
    for q in ledger.get("questions", []):
        way = q.get("way") or {}
        complete_way = all(str(way.get(f, "")).strip() for f in WAY_FIELDS)
        if complete_way or q.get("proposal") or q.get("options"):
            continue
        offenders.append(q.get("id", "?"))
    return offenders


# --- The sheet ----------------------------------------------------------------------


# Sections are cut by *origin* first and status second, for one reason that is visible the
# moment you read the emitted sheet: the mirrored decisions are German. They are class A,
# byte-identical to Meridian's, and translating them on this side would fork a shared asset
# into two wordings that drift — the exact failure the mirror exists to prevent. So they get
# their own section with the language switch explained, instead of being scattered through
# the English ones where the switch looks like an oversight.
_NATIVE_SECTIONS = (
    (STATUS_OPEN, "What we still need from you",
     "These are not answerable from anything we hold. Each one says where to look and who "
     "usually knows."),
    (STATUS_PRESET, "What we decided for you",
     "Sensible defaults, already applied. Read them; contradict any that do not fit. Silence "
     "means the value below stands."),
)

_MIRROR_HEADING = "Architecture and security decisions"
_MIRROR_BLURB = (
    "These come from the shared decision set that ALUCA and Meridian keep byte-identical, so "
    "they are worded in German. Each one carries either a proposal to confirm or a way to get "
    "to the answer."
)


def open_questions_markdown(ledger: dict[str, Any]) -> str:
    """Render the ledger as the sheet a customer actually reads."""
    out: list[str] = ["# Open questions", ""]
    s = ledger.get("summary", {})
    out.append(f"{s.get('total', 0)} points: {s.get('open', 0)} need an answer from you, "
               f"{s.get('preset', 0)} are already decided and can be contradicted, "
               f"{s.get('proposed', 0)} carry a proposal.")
    out.append("")

    questions = ledger.get("questions", [])
    native = [q for q in questions if q.get("origin") != ORIGIN_MIRROR]
    mirrored = [q for q in questions if q.get("origin") == ORIGIN_MIRROR]

    for status, heading, blurb in _NATIVE_SECTIONS:
        rows = [q for q in native if q.get("status") == status]
        if not rows:
            continue
        out += [f"## {heading}", "", blurb, ""]
        for q in rows:
            out += _question_block(q)
    if mirrored:
        out += [f"## {_MIRROR_HEADING}", "", _MIRROR_BLURB, ""]
        # Proposals first: a card you only have to confirm is cheaper to work through than one
        # that starts empty, and a reader who runs out of patience should run out of it late.
        for q in sorted(mirrored, key=lambda x: (x.get("status") != STATUS_PROPOSED, x.get("id", ""))):
            out += _question_block(q)
    if ledger.get("mirror_note"):
        out += ["## Not included", "",
                f"The mirrored decision set could not be read: {ledger['mirror_note']}. "
                "Those points are missing from this sheet, not answered.", ""]
    return "\n".join(out).rstrip() + "\n"


def _question_block(q: dict[str, Any]) -> list[str]:
    # No source, no print. Without this the catalogue grows questions nobody can trace back
    # to a contract, and in three months there is a second question silo next to this one.
    if not q.get("source"):
        return []
    block = [f"### {q['id']} · {q.get('topic', '')}", "", f"**{q.get('question', '')}**", ""]
    if q.get("applied"):
        block += [f"Applied: `{q['applied']}`", ""]
    if q.get("proposal"):
        block += [f"Our proposal: {q['proposal']}", ""]
    if q.get("why"):
        block += [f"Why it matters: {q['why']}", ""]
    if q.get("if_unanswered"):
        block += [f"If this stays open: {q['if_unanswered']}", ""]
    if q.get("options"):
        block += ["Alternatives:", ""] + [f"- {o}" for o in q["options"]] + [""]
    way = q.get("way") or {}
    if any(str(way.get(f, "")).strip() for f in WAY_FIELDS):
        block += ["How to get to the answer:", "",
                  f"- Where to look: {way.get('where', '')}",
                  f"- Who knows it: {way.get('who', '')}",
                  f"- If it stays unclear: {way.get('if_unclear', '')}", ""]
    if q.get("decider"):
        block += [f"Decided by: {q['decider']}", ""]
    if q.get("reported_gaps"):
        block += ["Reported by the deriver:", ""] + [f"- `{g}`" for g in q["reported_gaps"]] + [""]
    block += [f"<sub>Source: {q['source']}</sub>", ""]
    return block
