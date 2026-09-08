"""Validate and render project-specific end-to-end use-case delivery specifications."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _status(value: dict[str, Any]) -> str:
    note = value.get("note")
    evidence = ", ".join(value.get("evidence_refs", [])) or "none"
    return f"{value['state']} (evidence: {evidence})" + (f" — {note}" if note else "")


def _list(values: list[str]) -> str:
    return ", ".join(values) if values else "—"


def validate_delivery_document(document: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]
    if errors:
        return errors

    use_case_ids = [item["id"] for item in document["use_cases"]]
    if len(use_case_ids) != len(set(use_case_ids)):
        errors.append("use_cases: duplicate use-case id")

    gate_thresholds = {
        "discovery": set(),
        "contract_pending": set(),
        "design_ready": {"design"},
        "build_ready": {"design", "build"},
        "apply_ready": {"design", "build", "apply"},
        "verified": {"design", "build", "apply", "production", "acceptance", "verified"},
    }
    for use_case in document["use_cases"]:
        label = use_case["id"]
        sources = [
            item
            for boundary in ("canonical", "fallback", "excluded")
            for item in use_case["source_contract"][boundary]
        ]
        source_ids = [item["id"] for item in sources]
        product_ids = [item["id"] for item in use_case["data_products"]]
        object_ids = source_ids + product_ids
        if len(object_ids) != len(set(object_ids)):
            errors.append(f"{label}: duplicate source/data-product id")

        resolvable = set(object_ids)
        for product in use_case["data_products"]:
            for reference in product["source_refs"]:
                if reference not in resolvable:
                    errors.append(f"{label}: data product {product['id']!r} has unresolved source_ref {reference!r}")
        transformation_ids = [item["id"] for item in use_case["transformations"]]
        if len(transformation_ids) != len(set(transformation_ids)):
            errors.append(f"{label}: duplicate transformation id")
        for transformation in use_case["transformations"]:
            for reference in transformation["input_refs"] + transformation["output_refs"]:
                if reference not in resolvable:
                    errors.append(f"{label}: transformation {transformation['id']!r} has unresolved object ref {reference!r}")

        analytical_design = use_case["analytical_design"]
        assessments = analytical_design["relationship_assessments"]
        assessment_ids = [item["id"] for item in assessments]
        if len(assessment_ids) != len(set(assessment_ids)):
            errors.append(f"{label}: duplicate relationship-assessment id")
        for assessment in assessments:
            for reference in assessment["subject_refs"]:
                if reference not in set(product_ids):
                    errors.append(
                        f"{label}: relationship assessment {assessment['id']!r} has unresolved data-product ref {reference!r}"
                    )
            bridge_decision = assessment["bridge_decision"]
            filter_strategy = assessment["fact_filter_strategy"]
            if bridge_decision == "required" and filter_strategy == "direct_foreign_key":
                errors.append(
                    f"{label}: relationship assessment {assessment['id']!r} requires a bridge but declares a direct foreign-key filter strategy"
                )
            if bridge_decision == "replace_with_fact_fk" and filter_strategy != "direct_foreign_key":
                errors.append(
                    f"{label}: relationship assessment {assessment['id']!r} replaces the bridge with a fact key but does not declare direct_foreign_key"
                )
            if assessment["carries_weight"] and filter_strategy not in {
                "materialized_allocation_fact", "measure_logic", "open"
            }:
                errors.append(
                    f"{label}: weighted relationship assessment {assessment['id']!r} must use an allocation-fact, measure-logic or open strategy"
                )

        sequences = [item["sequence"] for item in use_case["orchestration"]["steps"]]
        if sequences != list(range(1, len(sequences) + 1)):
            errors.append(f"{label}: orchestration sequences must be ordered and contiguous from 1")

        closed_for_state = gate_thresholds[use_case["delivery_state"]]
        for gate in use_case["open_gates"]:
            if gate["status"]["state"] in {"open", "proposed", "derived"} and closed_for_state.intersection(gate["blocking_for"]):
                errors.append(
                    f"{label}: delivery_state {use_case['delivery_state']!r} conflicts with open gate "
                    f"{gate['id']!r} blocking {sorted(closed_for_state.intersection(gate['blocking_for']))}"
                )
    return errors


def render_use_case(use_case: dict[str, Any], project_ref: str) -> str:
    lines = [
        f"# {use_case['title']}",
        "",
        "## Use Case and Data Architecture Specification",
        "",
        f"**Project:** `{project_ref}`  ",
        f"**Use case:** `{use_case['id']}`  ",
        f"**Domain:** `{use_case['domain_ref']}`  ",
        f"**Delivery state:** `{use_case['delivery_state']}`  ",
        f"**Business scope:** `{use_case['business_scope_ref']}`",
        "",
        "## 1. Purpose and evidence rules",
        "",
        "This document is a deterministic projection of the project use-case delivery contract. "
        "Confirmed and measured claims require evidence references. Derived and proposed items are not customer decisions. Open items remain explicit gates.",
        "",
        "## 2. Decision and report scope",
        "",
        f"Decision references: {_list(use_case['decision_refs'])}",
        "",
        "| Report | Purpose | Modes | Pages | Bindings | Status |",
        "|---|---|---|---:|---:|---|",
    ]
    for report in use_case["reference_reports"]:
        lines.append(
            f"| {report['name']} | {report['purpose']} | {_list(report['modes'])} | "
            f"{report.get('page_count') if report.get('page_count') is not None else '—'} | "
            f"{report.get('binding_count') if report.get('binding_count') is not None else '—'} | {_status(report['status'])} |"
        )

    lines.extend(["", "## 3. Source boundary", ""])
    for boundary in ("canonical", "fallback", "excluded"):
        lines.extend(
            [
                f"### {boundary.replace('_', ' ').title()}",
                "",
                "| ID | Source | Purpose | Availability | Grain | Keys | Required for | Status |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for source in use_case["source_contract"][boundary]:
            lines.append(
                f"| `{source['id']}` | {source['source_system']}.{source['source_object']} | {source['purpose']} | "
                f"{source['availability']} | {source.get('expected_grain') or '—'} | {_list(source.get('key_fields', []))} | "
                f"{_list(source['required_for'])} | {_status(source['status'])} |"
            )
        if not use_case["source_contract"][boundary]:
            lines.append("| — | — | — | — | — | — | — | — |")
        lines.append("")

    lines.extend(
        [
            "## 4. Target data products",
            "",
            "| Layer | Product | Grain | Business keys | Sources | History | Status |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for product in use_case["data_products"]:
        lines.append(
            f"| {product['layer']} | `{product['name']}` | {product.get('grain') or '—'} | "
            f"{_list(product['business_keys'])} | {_list(product['source_refs'])} | {product['history']} | {_status(product['status'])} |"
        )

    lines.extend(
        [
            "",
            "## 5. Analytical model design",
            "",
            f"**Reuse scope:** `{use_case['analytical_design']['reuse_scope']['target']}` — "
            f"{use_case['analytical_design']['reuse_scope']['rationale']}",
            "",
            f"**Key contract:** `{use_case['analytical_design']['key_contract']['contract_ref']}` — "
            f"{_status(use_case['analytical_design']['key_contract']['status'])}",
            "",
            "| Assessment | Products | Cardinality | Time | Weight | Bridge decision | Fact-filter strategy | Double-counting control | Status |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for assessment in use_case["analytical_design"]["relationship_assessments"]:
        lines.append(
            f"| `{assessment['id']}` | {_list(assessment['subject_refs'])} | {assessment['business_cardinality']} | "
            f"{assessment['time_behavior']} | {'yes' if assessment['carries_weight'] else 'no'} | "
            f"{assessment['bridge_decision']} | {assessment['fact_filter_strategy']} | "
            f"{assessment.get('double_counting_control') or '—'} | {_status(assessment['status'])} |"
        )

    glossary = use_case["analytical_design"]["glossary"]
    lines.extend(
        [
            "",
            f"**Business metric catalog:** `{glossary['business_metric_catalog_ref']}`  ",
            f"**Measure dictionary:** `{glossary['measure_dictionary_ref']}`  ",
            f"**Technical data dictionary:** `{glossary['technical_data_dictionary_ref']}`  ",
            f"**Definition authority:** `{glossary['definition_authority']}`  ",
            f"**Analytical-design status:** {_status(use_case['analytical_design']['status'])}",
            "",
            "## 6. Transformation design",
            "",
            "| From → to | Transformation | Inputs | Outputs | Implementation | Logic | Quality rules | Status |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for transformation in use_case["transformations"]:
        lines.append(
            f"| {transformation['from_layer']} → {transformation['to_layer']} | `{transformation['id']}` | "
            f"{_list(transformation['input_refs'])} | {_list(transformation['output_refs'])} | "
            f"{transformation['implementation']} | {transformation['logic']} | {_list(transformation['quality_rules'])} | "
            f"{_status(transformation['status'])} |"
        )

    orchestration = use_case["orchestration"]
    lines.extend(
        [
            "",
            "## 7. Orchestration and operations",
            "",
            f"**Trigger:** {orchestration['trigger']}  ",
            f"**Cadence:** {orchestration['cadence']}  ",
            f"**Incremental strategy:** {orchestration['incremental_strategy']}",
            "",
            "| # | Step | Implementation | Success condition | Failure action | Status |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for step in orchestration["steps"]:
        lines.append(
            f"| {step['sequence']} | {step['name']} | {step['implementation']} | {step['success_condition']} | "
            f"{step['failure_action']} | {_status(step['status'])} |"
        )

    lines.extend(
        [
            "",
            "## 8. Security, quality, release and operational controls",
            "",
            "| Area | Requirement | Owner | Blocking for | Status |",
            "|---|---|---|---|---|",
        ]
    )
    for control in use_case["controls"]:
        lines.append(
            f"| {control['area']} | {control['requirement']} | {control.get('owner_ref') or '—'} | "
            f"{_list(control['blocking_for'])} | {_status(control['status'])} |"
        )

    acceptance = use_case["acceptance"]
    lines.extend(
        [
            "",
            "## 9. Acceptance and regression",
            "",
            f"**Snapshot rule:** {acceptance['snapshot_rule']}",
            "",
            f"**Regression scope:** {_list(acceptance['regression_scope'])}",
            "",
            f"**Required evidence:** {_list(acceptance['evidence_required'])}",
            "",
            f"**Status:** {_status(acceptance['status'])}",
            "",
            "## 10. Open gates",
            "",
            "| Gate | Question | Owner | Required by | Blocking for | Status |",
            "|---|---|---|---|---|---|",
        ]
    )
    for gate in use_case["open_gates"]:
        lines.append(
            f"| `{gate['id']}` | {gate['question']} | {gate.get('owner_ref') or '—'} | "
            f"{gate.get('required_by') or '—'} | {_list(gate['blocking_for'])} | {_status(gate['status'])} |"
        )
    if not use_case["open_gates"]:
        lines.append("| — | No open gates recorded | — | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def render_delivery_document(document: dict[str, Any]) -> dict[str, str]:
    return {
        f"{use_case['id']}_Use_Case_and_Data_Architecture.md": render_use_case(use_case, document["project_ref"])
        for use_case in document["use_cases"]
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    document = _load(args.input)
    schema = _load(args.schema)
    errors = validate_delivery_document(document, schema)
    if errors:
        raise ValueError("invalid use-case delivery specification: " + "; ".join(errors))
    if args.validate_only:
        return 0
    if args.output_dir is None:
        raise ValueError("--output-dir is required unless --validate-only is used")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in render_delivery_document(document).items():
        (args.output_dir / name).write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
