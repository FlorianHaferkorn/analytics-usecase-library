"""The way back: an answered question becomes an input, or it says why not.

The defect these tests were written against is measurable and was real. Before
26.08.2026, three of the seven defaults `open_questions` presented as "contradict any that
do not fit" had no input field at all: four attempts to steer the grounding surface, the
retrieval strategy and the ownership boundaries left the derived blueprint byte-identical.
`test_the_three_defaults_that_could_not_be_contradicted` is that measurement, kept as a
test so the sheet cannot drift back into asking a question with nowhere to put the answer.
"""
from __future__ import annotations

import json

import pytest

from tooling.superversion import answers as A
from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion.open_questions import ORIGIN_MIRROR, collect_open_questions

_INPUTS = {
    "stack": "fabric",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [{"name": "fact_sales", "kind": "fact", "grain": "order line"}],
            "sources": [{"source": "crm", "source_system": "Dynamics 365"},
                        {"source": "erp", "source_system": "SAP S/4HANA"}],
        }
    ],
}


@pytest.fixture()
def ledger():
    return collect_open_questions(_INPUTS, derive_blueprint(_INPUTS))


def _doc(*rows):
    return {"document": A.ANSWER_DOCUMENT, "answers": list(rows)}


# --- the measured defect -------------------------------------------------------------

def test_the_three_defaults_that_could_not_be_contradicted():
    """Grounding surface, retrieval strategy and ownership now reach the blueprint."""
    steered = dict(_INPUTS, grounding_surface=["gold"], retrieval_strategy="both",
                   ownership_overrides={"ingestion": "informatica"})
    bp = derive_blueprint(steered)["blueprint"]
    assert bp["ai_grounding"]["grounding_surface"] == ["gold"]
    assert {r["strategy"] for r in bp["ai_grounding"]["retrieval"]} == {"both"}
    owners = {o["workload_class"]: o["owner_platform"]
              for o in bp["platform"]["ownership_boundaries"]}
    assert owners == {"ingestion": "informatica", "transformation": "fabric",
                      "serving": "fabric"}


def test_unset_reproduces_the_previous_output():
    """The three inputs are additive. Unset, the deriver answers exactly as before."""
    bp = derive_blueprint(_INPUTS)["blueprint"]
    assert bp["ai_grounding"]["grounding_surface"] == ["gold", "silver"]
    assert {r["strategy"] for r in bp["ai_grounding"]["retrieval"]} == {"builtin"}
    assert {o["owner_platform"] for o in bp["platform"]["ownership_boundaries"]} == {"fabric"}


def test_bronze_is_refused_rather_than_honoured():
    """A widened grounding surface is the one mistake nobody notices until an assistant
    quotes uncleaned data back at a customer."""
    bp = derive_blueprint(dict(_INPUTS, grounding_surface=["bronze"]))["blueprint"]
    assert bp["ai_grounding"]["grounding_surface"] == ["gold", "silver"]


def test_every_question_of_our_own_has_a_target(ledger):
    assert A.questions_without_a_target(ledger) == []


def test_mirrored_questions_are_recorded_not_written(ledger):
    mirrored = [q for q in ledger["questions"] if q["origin"] == ORIGIN_MIRROR]
    assert mirrored, "the mirror is expected to be readable in this checkout"
    assert {A.target_for(q)["kind"] for q in mirrored} == {A.RECORD}


# --- the plan ------------------------------------------------------------------------

def test_planning_never_touches_the_disk(ledger, tmp_path):
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(_INPUTS), encoding="utf-8")
    before = path.read_bytes()
    A.plan_answers(_doc({"id": "DEF-STACK", "answer": "databricks"}), ledger, _INPUTS)
    assert path.read_bytes() == before


def test_a_foreign_document_is_refused_by_name(ledger):
    with pytest.raises(ValueError, match="not an answer document"):
        A.plan_answers({"document": "something/else", "answers": []}, ledger, _INPUTS)


def test_a_scoped_answer_resolves_to_one_address(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-ACCESS", "scope": "erp", "answer": "shortcut"}),
                          ledger, _INPUTS)
    assert [a["address"] for a in plan["applies"]] == ["domains[].sources[erp].access_mode"]


def test_a_scope_that_names_nothing_blocks(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-ACCESS", "scope": "nope", "answer": "shortcut"}),
                          ledger, _INPUTS)
    assert plan["applies"] == []
    assert "no source named" in plan["blockers"][0]["reason"]


def test_a_missing_scope_blocks_rather_than_picking_a_domain(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-ENDORSEMENT", "answer": "certified"}),
                          ledger, _INPUTS)
    assert "needs a scope" in plan["blockers"][0]["reason"]


def test_a_map_constrains_its_keys_and_not_its_values(ledger):
    """The workload classes are fixed; the platform that owns one is not a closed list."""
    plan = A.plan_answers(_doc({"id": "DEF-OWNERSHIP", "scope": "ingestion",
                                "answer": "informatica"},
                               {"id": "DEF-OWNERSHIP", "scope": "kitchen", "answer": "x"}),
                          ledger, _INPUTS)
    assert [a["value"] for a in plan["applies"]] == ["informatica"]
    assert "scope must be one of" in plan["blockers"][0]["reason"]


def test_a_value_outside_the_options_blocks(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-RETRIEVAL", "answer": "telepathy"}),
                          ledger, _INPUTS)
    assert "not one of" in plan["blockers"][0]["reason"]


def test_an_answer_to_a_question_we_did_not_ask_blocks(ledger):
    """The sheet and the answers being out of step is the failure; guessing is not a fix."""
    plan = A.plan_answers(_doc({"id": "IN-DOMAINS", "answer": "three more"}),
                          ledger, _INPUTS)
    assert "out of step" in plan["blockers"][0]["reason"]


def test_a_supplied_value_is_not_overwritten(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-STACK", "answer": "databricks"}), ledger, _INPUTS)
    assert plan["applies"] == []
    assert "does not overwrite a supplied value" in plan["blockers"][0]["reason"]


def test_the_same_value_is_a_confirmation_and_not_a_change(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-STACK", "answer": "fabric"}), ledger, _INPUTS)
    assert plan["applies"] == [] and len(plan["already"]) == 1


def test_two_different_answers_to_one_address_block(ledger):
    plan = A.plan_answers(_doc({"id": "DEF-ACCESS", "scope": "erp", "answer": "shortcut"},
                               {"id": "DEF-ACCESS", "scope": "erp", "answer": "copy"}),
                          ledger, _INPUTS)
    assert len(plan["applies"]) == 1
    assert "a second, different answer" in plan["blockers"][0]["reason"]


def test_structural_answers_are_reported_and_not_guessed_at():
    """A domain with no gold products asks IN-GOLD; the answer is a document, not a value."""
    thin = {"stack": "fabric", "domains": [{"name": "Commercial", "sources": [
        {"source": "crm", "source_system": "Dynamics 365"}]}]}
    led = collect_open_questions(thin, derive_blueprint(thin))
    plan = A.plan_answers(_doc({"id": "IN-GOLD", "answer": "fact_sales, dim_customer"}),
                          led, thin)
    assert plan["applies"] == [] and plan["blockers"] == []
    assert [q["id"] for q in plan["structural"]] == ["IN-GOLD"]


# --- the write -----------------------------------------------------------------------

def _write_inputs(tmp_path):
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(_INPUTS), encoding="utf-8")
    return path


def test_a_dry_run_refuses_to_write(ledger, tmp_path):
    path = _write_inputs(tmp_path)
    before = path.read_bytes()
    plan = A.plan_answers(_doc({"id": "IN-SILVER-CONTRACT", "answer": "x.yaml"}),
                          ledger, _INPUTS)
    with pytest.raises(A.AnswerError, match="dry run"):
        A.write_inputs(path, plan, release=False)
    assert path.read_bytes() == before


def test_a_blocked_plan_writes_nothing_at_all(ledger, tmp_path):
    """Not even the answers that would have applied. Half a file is worse than none."""
    path = _write_inputs(tmp_path)
    before = path.read_bytes()
    plan = A.plan_answers(_doc({"id": "IN-SILVER-CONTRACT", "answer": "x.yaml"},
                               {"id": "DEF-RETRIEVAL", "answer": "telepathy"}),
                          ledger, _INPUTS)
    assert len(plan["applies"]) == 1 and len(plan["blockers"]) == 1
    with pytest.raises(A.AnswerError, match="blocked"):
        A.write_inputs(path, plan, release=True)
    assert path.read_bytes() == before


def test_a_released_plan_writes_exactly_what_it_promised(ledger, tmp_path):
    path = _write_inputs(tmp_path)
    plan = A.plan_answers(_doc({"id": "IN-SILVER-CONTRACT", "answer": "commercial.yaml"},
                               {"id": "DEF-ACCESS", "scope": "erp", "answer": "shortcut"},
                               {"id": "DEF-GROUNDING", "answer": "gold"},
                               {"id": "DEF-OWNERSHIP", "scope": "ingestion",
                                "answer": "informatica"},
                               {"id": "DEF-ENDORSEMENT", "scope": "Commercial",
                                "answer": "certified"}),
                          ledger, _INPUTS)
    A.write_inputs(path, plan, release=True)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["silver_contract_ref"] == "commercial.yaml"
    assert written["grounding_surface"] == ["gold"]
    assert written["ownership_overrides"] == {"ingestion": "informatica"}
    dom = written["domains"][0]
    assert dom["endorsement"] == "certified"
    assert {s["source"]: s.get("access_mode") for s in dom["sources"]} == {
        "crm": None, "erp": "shortcut"}


def test_the_written_answers_reach_the_blueprint(ledger, tmp_path):
    """The point of the return path: the next derivation is a different one."""
    path = _write_inputs(tmp_path)
    plan = A.plan_answers(_doc({"id": "DEF-GROUNDING", "answer": "gold"},
                               {"id": "DEF-ACCESS", "scope": "erp", "answer": "shortcut"}),
                          ledger, _INPUTS)
    A.write_inputs(path, plan, release=True)
    bp = derive_blueprint(json.loads(path.read_text(encoding="utf-8")))["blueprint"]
    assert bp["ai_grounding"]["grounding_surface"] == ["gold"]
    assert {e["source"]: e["access_mode"] for e in bp["ingestion"]}["erp"] == "shortcut"


def test_an_answered_question_leaves_the_sheet(ledger, tmp_path):
    path = _write_inputs(tmp_path)
    plan = A.plan_answers(_doc({"id": "IN-SILVER-CONTRACT", "answer": "commercial.yaml"}),
                          ledger, _INPUTS)
    A.write_inputs(path, plan, release=True)
    after = json.loads(path.read_text(encoding="utf-8"))
    again = collect_open_questions(after, derive_blueprint(after))
    assert "IN-SILVER-CONTRACT" not in {q["id"] for q in again["questions"]}


def test_the_shared_decisions_survive_the_session(ledger, tmp_path):
    plan = A.plan_answers(_doc({"id": "SEC-RLS", "answer": "Ja, nach Vertriebsregion",
                                "answered_by": "IT-Leitung"}), ledger, _INPUTS)
    out = tmp_path / "decisions.json"
    assert A.write_decisions(out, plan, release=True) == ["SEC-RLS"]
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["decisions"][0]["answer"] == "Ja, nach Vertriebsregion"


# --- the template --------------------------------------------------------------------

def test_the_template_covers_every_question_exactly_once(ledger):
    rows = A.answers_template(ledger)["answers"]
    ids = [r["id"] for r in rows]
    assert sorted(ids) == sorted(q["id"] for q in ledger["questions"])
    assert len(ids) == len(set(ids))


def test_the_template_addresses_each_row_but_guesses_no_scope(ledger):
    for row in A.answers_template(ledger)["answers"]:
        assert row["_target"], f"{row['id']} has no target"
        if "scope" in row:
            assert row["scope"].startswith("<"), "a guessed scope is the one error the plan " \
                                                 "cannot catch — it resolves"


def test_a_filled_template_plans_without_blockers(ledger):
    filled = A.answers_template(ledger)
    for row in filled["answers"]:
        if row["id"] == "DEF-ACCESS":
            row["scope"], row["answer"] = "erp", "shortcut"
    filled["answers"] = [r for r in filled["answers"] if r["answer"]]
    plan = A.plan_answers(filled, ledger, _INPUTS)
    assert plan["blockers"] == [] and plan["summary"]["applies"] == 1
