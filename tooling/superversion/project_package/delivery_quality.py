"""Assess a Project Package against the governed E2E delivery reference model.

The score is diagnostic. Readiness is fail-closed per gate and never inferred
from the weighted percentage alone.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .hashes import canonical_sha256
from .validator import _validate_identity_access, validate_project_package


VERSION = "1.0.0"
GATE_ORDER = ("build_ready", "apply_ready", "acceptance_ready")


def _now(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("A timezone-aware assessment time is required")
    return value.astimezone(timezone.utc)


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("Invalid assurance timestamp") from error
    return _now(parsed)


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _modules(package_root: Path, manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest["modules"]:
        result.setdefault(entry["module_type"], []).append(_load(package_root / entry["path"]))
    return result


def assess_reference_review(model_document: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Return the review status of every authoritative source in the model."""
    assessment_time = _now(now)
    overdue_sources: list[str] = []
    next_reviews: list[datetime] = []
    for dimension in model_document["dimensions"]:
        for control in dimension["controls"]:
            source = control["source"]
            due = _time(source["reviewed_at"]) + timedelta(days=source["review_interval_days"])
            next_reviews.append(due)
            if due < assessment_time:
                overdue_sources.append(control["id"])
    if not next_reviews:
        raise ValueError("The delivery quality model contains no reference sources")
    return {
        "current": not overdue_sources,
        "overdue_controls": sorted(overdue_sources),
        "next_due_at": min(next_reviews).isoformat().replace("+00:00", "Z"),
    }


def _detect(kind: str, module_type: str | None, manifest: dict[str, Any], modules: dict[str, list[dict[str, Any]]], now: datetime) -> tuple[bool, str]:
    if kind == "module_present":
        passed = bool(module_type and modules.get(module_type))
        return passed, f"Module {module_type!r} {'is recorded' if passed else 'is missing'}"
    if kind == "package_approved":
        passed = manifest["state"] == "approved"
        return passed, f"Package state is {manifest['state']!r}"
    if kind == "approved_decisions_evidenced":
        sets = modules.get("decision_set", [])
        if not sets:
            return False, "Decision set is missing"
        document = sets[0]
        definitions = {item["id"]: item for item in document["definitions"]}
        if not document["instances"]:
            return False, "No project decisions are recorded"
        gaps: list[str] = []
        for instance in document["instances"]:
            if instance["approval"]["state"] == "superseded":
                continue
            definition = definitions.get(instance["definition_ref"], {})
            approval = instance["approval"]
            if approval["state"] != "approved":
                gaps.append(f"{instance['id']}:state={approval['state']}")
            elif not definition.get("adr"):
                gaps.append(f"{instance['id']}:adr_missing")
            elif not approval.get("decided_at") or not approval.get("evidence_refs"):
                gaps.append(f"{instance['id']}:approval_evidence_missing")
        return not gaps, "All active decisions are accepted ADRs" if not gaps else "; ".join(gaps)
    if kind == "capability_questions_resolved":
        states = modules.get("capability_state", [])
        if not states:
            return False, "Capability state is missing"
        gaps: list[str] = []
        for capability in states[0]["capabilities"]:
            if capability["scope_level"] not in {"implement", "operate"}:
                continue
            for answer in capability["answers"]:
                if answer["state"] not in {"answered", "not_applicable"}:
                    gaps.append(f"{capability['id']}:{answer['question_ref']}={answer['state']}")
                elif answer["state"] == "answered" and answer["evidence"]["provenance"] == "proposed":
                    gaps.append(f"{capability['id']}:{answer['question_ref']}=proposed")
        return not gaps, "Applicable capability questions are resolved" if not gaps else "; ".join(gaps)
    if kind == "identity_contract_ready":
        states = modules.get("identity_access", [])
        if not states:
            return False, "Identity and access contract is missing"
        document = states[0]
        gaps = _validate_identity_access(document, "identity_access")
        if not document["accounts"]:
            gaps.append("no required accounts recorded")
        if not document["groups"]:
            gaps.append("no security groups recorded")
        gaps.extend(
            f"account {item['id']} is only {item['lifecycle_state']}"
            for item in document["accounts"]
            if item["lifecycle_state"] not in {"provisioned", "verified"}
        )
        gaps.extend(
            f"group {item['id']} is only {item['lifecycle_state']}"
            for item in document["groups"]
            if item["lifecycle_state"] not in {"provisioned", "verified"}
        )
        gaps.extend(
            f"assignment {item['id']} is only {item['state']}"
            for item in document["role_assignments"]
            if item["state"] not in {"approved", "applied", "verified"}
        )
        gaps.extend(
            f"separation rule {item['id']} is only {item['state']}"
            for item in document["separation_rules"]
            if item["state"] not in {"enforced", "exception_approved"}
        )
        return not gaps, "Identity and access contract is apply-ready" if not gaps else "; ".join(gaps)
    if kind == "architecture_maintenance_ready":
        states = modules.get("architecture_maintenance", [])
        if not states:
            return False, "Architecture maintenance contract is missing"
        document = states[0]
        gaps: list[str] = []
        if document["state"] != "active":
            gaps.append(f"maintenance state is {document['state']}")
        review = document["review"]
        if _time(review["last_reviewed_at"]) + timedelta(days=review["cadence_days"]) < now:
            gaps.append("architecture review is overdue")
        for technology in document["technology_watch"]:
            if _time(technology["reviewed_at"]) + timedelta(days=technology["review_interval_days"]) < now:
                gaps.append(f"technology review {technology['id']} is overdue")
        observed_by_environment = {
            item["environment"]: item for item in modules.get("observed_state", [])
        }
        policy = document["reconciliation"]
        if _time(policy["last_reconciled_at"]) + timedelta(hours=policy["cadence_hours"]) < now:
            gaps.append("architecture reconciliation is overdue")
        if policy["last_result"] == "drift" and policy["drift_action"] == "block_release":
            gaps.append("unresolved architecture drift blocks release")
        for environment in policy["environments"]:
            observed = observed_by_environment.get(environment)
            if not observed or observed.get("collection_state") != "collected" or not observed.get("captured_at"):
                gaps.append(f"{environment} observed state is missing")
            elif _time(observed["captured_at"]) + timedelta(hours=policy["observed_state_max_age_hours"]) < now:
                gaps.append(f"{environment} observed state is stale")
        return not gaps, "Architecture review, technology watch and observed-state reconciliation are current" if not gaps else "; ".join(gaps)
    if kind == "observed_evidence_collected":
        observed = modules.get("observed_state", [])
        passed_rows = []
        for document in observed:
            operational = document.get("operational_evidence") or {}
            proofs = [proof for values in operational.values() for proof in values]
            if document.get("collection_state") == "collected" and any(proof.get("outcome") == "passed" for proof in proofs):
                passed_rows.append(document.get("environment"))
        return bool(passed_rows), f"Passed observed evidence: {', '.join(passed_rows)}" if passed_rows else "No collected environment contains passed operational evidence"
    raise ValueError(f"Unsupported delivery quality detector {kind!r}")


def assess_delivery_quality(package_root: Path, schema_root: Path, model_document: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    assessment_time = _now(now)
    errors = validate_project_package(package_root, schema_root)
    if errors:
        raise ValueError("invalid project package: " + "; ".join(errors))
    model_schema = _load(schema_root / "delivery_quality_model.schema.json")
    validation = sorted(
        Draft202012Validator(model_schema, format_checker=FormatChecker()).iter_errors(model_document),
        key=lambda item: list(item.absolute_path),
    )
    if validation:
        raise ValueError("invalid delivery quality model: " + "; ".join(item.message for item in validation))
    manifest = _load(package_root / "package.yaml")
    modules = _modules(package_root, manifest)
    dimensions: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    for dimension in model_document["dimensions"]:
        rows = []
        for control in dimension["controls"]:
            detector = control["detector"]
            passed, evidence = _detect(detector["kind"], detector.get("module_type"), manifest, modules, assessment_time)
            row = {
                "id": control["id"], "title": control["title"], "requirement": control["requirement"],
                "gate": control["gate"], "weight": control["weight"], "status": "passed" if passed else "gap",
                "evidence": evidence, "source": control["source"],
            }
            rows.append(row)
            controls.append(row)
        dimensions.append({
            "id": dimension["id"], "title": dimension["title"], "intent": dimension["intent"],
            "score": round(100 * sum(row["weight"] for row in rows if row["status"] == "passed") / sum(row["weight"] for row in rows)),
            "controls": rows,
        })
    total = sum(row["weight"] for row in controls)
    achieved = sum(row["weight"] for row in controls if row["status"] == "passed")
    gates: dict[str, dict[str, Any]] = {}
    inherited: list[str] = []
    for gate in GATE_ORDER:
        inherited.extend(row["id"] for row in controls if row["gate"] == gate and row["status"] == "gap")
        gates[gate] = {"ready": not inherited, "blockers": sorted(set(inherited))}
    return {
        "schema_version": VERSION,
        "project_ref": manifest["project_ref"],
        "package_revision": manifest["revision"],
        "package_sha256": canonical_sha256(manifest),
        "model": {"id": model_document["id"], "version": model_document["version"], "sha256": canonical_sha256(model_document)},
        "reference_review": assess_reference_review(model_document, now=assessment_time),
        "weighted_score": round(100 * achieved / total),
        "score_interpretation": "Diagnostic comparison only; readiness is determined by mandatory gates, not by the percentage.",
        "gates": gates,
        "dimensions": dimensions,
    }


def render_assessment(result: dict[str, Any]) -> str:
    reference_review = result["reference_review"]
    lines = [
        "# Delivery quality assessment", "",
        f"Project: `{result['project_ref']}`  ",
        f"Package revision: `{result['package_revision']}`  ",
        f"Reference model: `{result['model']['id']}@{result['model']['version']}`  ",
        f"Diagnostic weighted score: `{result['weighted_score']}%`", "",
        f"Reference-source review: `{'current' if reference_review['current'] else 'overdue'}`  ",
        f"Next source review due: `{reference_review['next_due_at']}`  ",
        f"Overdue controls: `{', '.join(reference_review['overdue_controls']) or 'none'}`", "",
        f"> {result['score_interpretation']}", "", "## Mandatory gates", "",
        "| Gate | Ready | Blocking controls |", "|---|---|---|",
    ]
    for gate, state in result["gates"].items():
        lines.append(f"| {gate} | {'yes' if state['ready'] else 'no'} | {', '.join(state['blockers']) or '—'} |")
    for dimension in result["dimensions"]:
        lines.extend(["", f"## {dimension['title']} · {dimension['score']}%", "", dimension["intent"], "", "| Control | Status | Gate | Evidence | Adopted strength |", "|---|---|---|---|---|"])
        for control in dimension["controls"]:
            lines.append(
                f"| {control['title']} | {control['status']} | {control['gate']} | {control['evidence']} | "
                f"[{control['source']['name']}]({control['source']['url']}): {control['source']['strength_adopted']} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    result = assess_delivery_quality(args.package, args.schemas, _load(args.model))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_assessment(result), encoding="utf-8", newline="\n")
    if not args.output:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["gates"]["build_ready"]["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
