"""Evaluate a capability pack against project facts and questionnaire answers.

The result is deterministic compiler input. It does not approve decisions, invent
answers or treat a generated recommendation as customer acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from .hashes import canonical_sha256


VERSION = "1.0.0"


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _condition(condition: dict[str, Any], facts: dict[str, Any]) -> bool | None:
    fact = condition["fact"]
    operator = condition["operator"]
    if fact not in facts:
        return True if operator == "not_exists" else False if operator == "exists" else None
    actual = facts[fact]
    expected = condition.get("value")
    if operator == "exists":
        return True
    if operator == "not_exists":
        return False
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected
    raise ValueError(f"Unsupported applicability operator {operator!r}")


def _conditions(conditions: list[dict[str, Any]], facts: dict[str, Any]) -> bool | None:
    results = [_condition(item, facts) for item in conditions]
    if False in results:
        return False
    if None in results:
        return None
    return True


def evaluate_capability(pack_document: dict[str, Any], state_document: dict[str, Any]) -> dict[str, Any]:
    pack = pack_document["capability"]
    if state_document["capability_ref"] != pack["id"]:
        raise ValueError("Capability state refers to a different capability pack")
    if state_document["capability_version"] != pack["version"]:
        raise ValueError("Capability state version does not match the locked capability pack")

    fact_rows = state_document["facts"]
    answer_rows = state_document["answers"]
    facts = {item["id"]: item["value"] for item in fact_rows}
    answers = {item["question_ref"]: item for item in answer_rows}
    if len(facts) != len(fact_rows):
        raise ValueError("Capability state contains duplicate facts")
    if len(answers) != len(answer_rows):
        raise ValueError("Capability state contains duplicate question answers")

    applicability = {
        item["id"]: _condition(item["condition"], facts)
        for item in pack["applicability"]
    }
    blockers: list[str] = []
    question_results: list[dict[str, Any]] = []
    active_decisions: set[str] = set()
    required_evidence: set[str] = set()
    compiled_answers: dict[str, Any] = {}
    known_questions = {item["id"] for item in pack["questions"]}
    unknown_answers = sorted(set(answers) - known_questions)
    if unknown_answers:
        raise ValueError(f"Capability state contains unknown question refs {unknown_answers}")

    for question in pack["questions"]:
        refs = question["applicability_refs"]
        states = [applicability[ref] for ref in refs]
        applicable = False if False in states else None if None in states else True
        answer = answers.get(question["id"])
        state = answer["state"] if answer else "open"
        provenance = answer["evidence"]["provenance"] if answer else None
        row_blockers: list[str] = []
        if applicable is None and question["blocking"]:
            row_blockers.append("applicability_fact_missing")
        if applicable is True:
            required_evidence.update(question["evidence_requirement_refs"])
            if question["decision_ref"]:
                active_decisions.add(question["decision_ref"])
            if question["blocking"] and state != "answered":
                row_blockers.append("answer_required")
            if state == "answered":
                compiled_answers[question["id"]] = answer["response"]
                if state_document["scope_level"] in {"design", "implement", "operate"} and provenance == "proposed":
                    row_blockers.append("proposed_answer_not_sufficient")
        if row_blockers:
            blockers.extend(f"{question['id']}:{item}" for item in row_blockers)
        question_results.append(
            {
                "id": question["id"],
                "text": question["text"],
                "applicable": applicable,
                "blocking": question["blocking"],
                "answer_state": state,
                "provenance": provenance,
                "decision_ref": question["decision_ref"],
                "evidence_requirement_refs": question["evidence_requirement_refs"],
                "blockers": row_blockers,
            }
        )

    recommendations = []
    for rule in pack["recommendation_rules"]:
        matches = _conditions(rule["when"], facts)
        if matches is True and rule["decision_ref"] in active_decisions:
            recommendations.append(
                {
                    "decision_ref": rule["decision_ref"],
                    "option_ref": rule["recommend_option_ref"],
                    "rationale": rule["rationale"],
                    "rule_ref": rule["id"],
                    "status": "recommendation_not_approval",
                }
            )

    scoped_out = state_document["scope_level"] == "not_in_scope"
    if scoped_out:
        blockers = []
        active_decisions.clear()
        required_evidence.clear()
        compiled_answers.clear()
    identity = {
        "engine_version": VERSION,
        "capability_ref": pack["id"],
        "capability_version": pack["version"],
        "scope_level": state_document["scope_level"],
        "pack_sha256": canonical_sha256(pack_document),
        "state_sha256": canonical_sha256(state_document),
    }
    return {
        "schema_version": VERSION,
        **identity,
        "evaluation_sha256": canonical_sha256(identity),
        "applicability": applicability,
        "questions": question_results,
        "active_decision_refs": sorted(active_decisions),
        "required_evidence_refs": sorted(required_evidence),
        "recommendations": sorted(recommendations, key=lambda item: (item["decision_ref"], item["option_ref"])),
        "compiled_inputs": {"facts": facts, "answers": compiled_answers},
        "questionnaire_complete": not blockers,
        "build_input_ready": not scoped_out and state_document["scope_level"] in {"implement", "operate"} and not blockers,
        "blockers": sorted(blockers),
        "limitations": [
            "Recommendations are not customer decisions.",
            "Questionnaire completeness is not tenant apply, runtime verification or acceptance evidence.",
            "Decision approvals remain in the Project Package decision set.",
        ],
    }


def render_questionnaire(result: dict[str, Any]) -> str:
    lines = [
        f"# Capability intake: {result['capability_ref']}",
        "",
        f"Scope level: `{result['scope_level']}`  ",
        f"Questionnaire complete: `{'yes' if result['questionnaire_complete'] else 'no'}`  ",
        f"Build input ready: `{'yes' if result['build_input_ready'] else 'no'}`",
        "",
        "| Question | Applicable | Blocking | Answer | Provenance | Decision | Gap |",
        "|---|---|---|---|---|---|---|",
    ]
    for question in result["questions"]:
        applicable = "pending" if question["applicable"] is None else "yes" if question["applicable"] else "no"
        lines.append(
            f"| {question['text']} | {applicable} | {'yes' if question['blocking'] else 'no'} | "
            f"{question['answer_state']} | {question['provenance'] or '—'} | {question['decision_ref'] or '—'} | "
            f"{', '.join(question['blockers']) or '—'} |"
        )
    lines.extend(["", "## Recommended options", ""])
    if result["recommendations"]:
        lines.extend(["| Decision | Option | Rationale | Status |", "|---|---|---|---|"])
        for recommendation in result["recommendations"]:
            lines.append(
                f"| `{recommendation['decision_ref']}` | `{recommendation['option_ref']}` | "
                f"{recommendation['rationale']} | {recommendation['status']} |"
            )
    else:
        lines.append("No recommendation can be derived from the supplied facts.")
    lines.extend(["", "## Blocking gaps", ""])
    lines.extend(f"- `{item}`" for item in result["blockers"])
    if not result["blockers"]:
        lines.append("- None in the questionnaire contract. Decision, apply and evidence gates remain separate.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    result = evaluate_capability(_load(args.pack), _load(args.state))
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_questionnaire(result), encoding="utf-8", newline="\n")
    if not args.output:
        print(payload, end="")
    return 0 if result["questionnaire_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
