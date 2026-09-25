"""Validate and render project-specific end-to-end use-case delivery specifications."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ACCEPTED_EVIDENCE_STATES = {"confirmed", "measured"}
PLATFORM_DEPENDENCY_KINDS = {
    "gateways": "gateway",
    "connections": "connection",
    "workspaces": "workspace",
    "targets": "target",
}


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def _status(value: dict[str, Any]) -> str:
    note = value.get("note")
    evidence = ", ".join(value.get("evidence_refs", [])) or "none"
    return f"{value['state']} (evidence: {evidence})" + (f" — {note}" if note else "")


def _list(values: list[str]) -> str:
    return ", ".join(values) if values else "—"


def _threshold(value: dict[str, Any] | None) -> str:
    if value is None:
        return "—"
    return f"{value['operator']} {value['value']} {value['unit']} ({value['provenance']})"


def _platform_index(document: dict[str, Any]) -> tuple[dict[str, tuple[str, dict[str, Any]]], list[str]]:
    dependencies = document.get("platform_dependencies")
    if dependencies is None:
        return {}, []
    occurrences: dict[str, list[str]] = {}
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection, kind in PLATFORM_DEPENDENCY_KINDS.items():
        for dependency in dependencies[collection]:
            logical_id = dependency["id"]
            occurrences.setdefault(logical_id, []).append(kind)
            index[logical_id] = (kind, dependency)
    errors = [
        f"platform_dependencies: ambiguous or duplicate logical ref {logical_id!r} in {kinds}"
        for logical_id, kinds in sorted(occurrences.items())
        if len(kinds) > 1
    ]
    return index, errors


def _dependency_ref_error(
    label: str,
    owner: str,
    reference: str | None,
    expected_kind: str,
    index: dict[str, tuple[str, dict[str, Any]]],
) -> str | None:
    resolved = index.get(reference or "")
    if resolved is None:
        return f"{label}: {owner} has unresolved {expected_kind}_ref {reference!r}"
    if resolved[0] != expected_kind:
        return (
            f"{label}: {owner} {expected_kind}_ref {reference!r} resolves to "
            f"{resolved[0]!r}, not {expected_kind!r}"
        )
    return None


def _validate_delivery_assurance(use_case: dict[str, Any]) -> list[str]:
    """Validate cross-field assurances that JSON Schema cannot express clearly."""
    label = use_case["id"]
    assurance = use_case.get("delivery_assurance")
    state = use_case["delivery_state"]
    states_requiring_assurance = {"design_ready", "build_ready", "apply_ready", "verified"}
    if assurance is None:
        return [f"{label}: delivery_assurance is required for delivery_state {state!r}"] if state in states_requiring_assurance else []

    errors: list[str] = []
    source = assurance["source_behavior"]
    incremental_mode = source["incremental_mode"]
    if incremental_mode in {"watermark", "native_cdc", "delta_cdf"} and not source["cursor_field"]:
        errors.append(f"{label}: incremental mode {incremental_mode!r} requires cursor_field")
    if incremental_mode != "open" and not source["reconciliation_cadence"]:
        errors.append(f"{label}: selected incremental mode requires reconciliation_cadence")
    if incremental_mode == "append_only" and source["delete_handling"] not in {"not_applicable", "open"}:
        errors.append(f"{label}: append_only conflicts with delete_handling {source['delete_handling']!r}")

    quality = assurance["data_quality"]
    rules = quality["rules"]
    rule_ids = [rule["id"] for rule in rules]
    if len(rule_ids) != len(set(rule_ids)):
        errors.append(f"{label}: duplicate delivery-assurance quality-rule id")
    if any(rule["severity"] == "block" for rule in rules) and not quality["last_approved_output_retained"] and state != "contract_pending":
        errors.append(f"{label}: blocking quality rules require last_approved_output_retained before design_ready")
    for rule in rules:
        if rule["threshold"]["provenance"] == "accepted" and rule["status"]["state"] not in ACCEPTED_EVIDENCE_STATES:
            errors.append(f"{label}: quality rule {rule['id']!r} has an accepted threshold without accepted evidence")

    observability = assurance["observability"]
    signals = observability["signals"]
    signal_ids = [signal["id"] for signal in signals]
    if len(signal_ids) != len(set(signal_ids)):
        errors.append(f"{label}: duplicate delivery-assurance monitoring-signal id")

    reliability = assurance["reliability"]
    failure_classes = [rule["failure_class"] for rule in reliability["retry_policy"]]
    if len(failure_classes) != len(set(failure_classes)):
        errors.append(f"{label}: retry_policy contains duplicate failure classes")
    for rule in reliability["retry_policy"]:
        if rule["action"] in {"stop", "reconcile"} and rule["max_attempts"] != 0:
            errors.append(f"{label}: retry rule {rule['failure_class']!r} must use zero attempts for {rule['action']!r}")
        if rule["action"] in {"retry", "retry_after"} and rule["max_attempts"] < 1:
            errors.append(f"{label}: retry rule {rule['failure_class']!r} requires at least one attempt")

    mature_states = {"build_ready", "apply_ready", "verified"}
    if state in mature_states:
        if observability["stale_after_minutes"] is None:
            errors.append(f"{label}: {state} requires a measured or approved stale-after threshold")
        for signal in signals:
            missing_route = [
                field for field in (
                    "recipient_ref", "channel", "response_slo", "runbook_ref", "retention_days", "test_method"
                ) if signal[field] is None
            ]
            if missing_route:
                errors.append(
                    f"{label}: {state} monitoring signal {signal['id']!r} has unresolved operating fields {missing_route}"
                )
        if incremental_mode == "open" or source["delete_handling"] == "open":
            errors.append(f"{label}: {state} requires selected incremental and delete-handling strategies")
        if not any(rule["severity"] == "block" for rule in rules):
            errors.append(f"{label}: {state} requires at least one blocking data-quality rule")
        required_signals = {"job_failure", "data_quality_failure", "freshness", "capacity"}
        missing_signals = sorted(required_signals - {signal["type"] for signal in signals})
        if missing_signals:
            errors.append(f"{label}: {state} delivery assurance misses monitoring signal types {missing_signals}")
        required_failure_classes = {"transient", "authentication", "schema", "data_quality", "unknown"}
        missing_classes = sorted(required_failure_classes - set(failure_classes))
        if missing_classes:
            errors.append(f"{label}: {state} retry policy misses failure classes {missing_classes}")
        retry_actions = {rule["failure_class"]: rule["action"] for rule in reliability["retry_policy"]}
        for failure_class in ("authentication", "schema", "data_quality"):
            if retry_actions.get(failure_class) != "stop":
                errors.append(f"{label}: non-retryable failure class {failure_class!r} must stop")
        if retry_actions.get("unknown") != "reconcile":
            errors.append(f"{label}: unknown mutation outcomes must reconcile by readback")
    if state == "verified":
        for component, value in (
            ("delivery_assurance", assurance),
            ("source_behavior", source),
            ("data_quality", quality),
            ("observability", observability),
            ("reliability", reliability),
        ):
            if value["status"]["state"] not in ACCEPTED_EVIDENCE_STATES:
                errors.append(f"{label}: verified delivery requires confirmed or measured {component} evidence")
    return errors


def validate_delivery_document(document: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]
    if errors:
        return errors

    dependency_index, dependency_errors = _platform_index(document)
    errors.extend(dependency_errors)
    dependencies_enabled = "platform_dependencies" in document
    if dependencies_enabled:
        for connection in document["platform_dependencies"]["connections"]:
            if connection["gateway_ref"] is not None:
                error = _dependency_ref_error(
                    "platform_dependencies",
                    f"connection {connection['id']!r}",
                    connection["gateway_ref"],
                    "gateway",
                    dependency_index,
                )
                if error:
                    errors.append(error)
        for target in document["platform_dependencies"]["targets"]:
            error = _dependency_ref_error(
                "platform_dependencies",
                f"target {target['id']!r}",
                target["workspace_ref"],
                "workspace",
                dependency_index,
            )
            if error:
                errors.append(error)

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
        errors.extend(_validate_delivery_assurance(use_case))
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

        declared_platform_refs = set(use_case.get("platform_dependency_refs", []))
        if dependencies_enabled and "platform_dependency_refs" not in use_case:
            errors.append(f"{label}: platform_dependency_refs required when platform_dependencies are declared")
        for reference in sorted(declared_platform_refs):
            if reference not in dependency_index:
                errors.append(f"{label}: unresolved platform_dependency_ref {reference!r}")

        wired_platform_refs: set[str] = set()
        for source in sources:
            connection_ref = source.get("connection_ref")
            if source in use_case["source_contract"]["excluded"] and connection_ref is None:
                continue
            if dependencies_enabled and connection_ref is None:
                errors.append(f"{label}: source {source['id']!r} requires connection_ref")
                continue
            if connection_ref is not None:
                error = _dependency_ref_error(
                    label,
                    f"source {source['id']!r}",
                    connection_ref,
                    "connection",
                    dependency_index,
                )
                if error:
                    errors.append(error)
                else:
                    wired_platform_refs.add(connection_ref)
                    gateway_ref = dependency_index[connection_ref][1]["gateway_ref"]
                    if gateway_ref is not None:
                        wired_platform_refs.add(gateway_ref)

        for product in use_case["data_products"]:
            target_ref = product.get("target_ref")
            if dependencies_enabled and target_ref is None:
                errors.append(f"{label}: data product {product['id']!r} requires target_ref")
                continue
            if target_ref is not None:
                error = _dependency_ref_error(
                    label,
                    f"data product {product['id']!r}",
                    target_ref,
                    "target",
                    dependency_index,
                )
                if error:
                    errors.append(error)
                else:
                    wired_platform_refs.add(target_ref)
                    wired_platform_refs.add(dependency_index[target_ref][1]["workspace_ref"])

        if dependencies_enabled:
            missing_refs = sorted(wired_platform_refs - declared_platform_refs)
            unused_refs = sorted(declared_platform_refs - wired_platform_refs)
            if missing_refs:
                errors.append(f"{label}: platform_dependency_refs omit wired refs {missing_refs}")
            if unused_refs:
                errors.append(f"{label}: platform_dependency_refs contain unwired refs {unused_refs}")

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
        if dependencies_enabled:
            acceptance = use_case["acceptance"]
            acceptance_state = acceptance["status"]["state"]
            runtime_refs = acceptance.get("runtime_proof_refs", [])
            if acceptance_state in ACCEPTED_EVIDENCE_STATES and not runtime_refs:
                errors.append(f"{label}: accepted acceptance status requires runtime_proof_refs")
            if use_case["delivery_state"] == "verified" and acceptance_state not in ACCEPTED_EVIDENCE_STATES:
                errors.append(
                    f"{label}: delivery_state 'verified' requires confirmed or measured acceptance; "
                    f"{acceptance_state!r} evidence does not satisfy acceptance"
                )
            if acceptance_state in ACCEPTED_EVIDENCE_STATES:
                acceptance_platform_refs: set[str] = set()
                for source in use_case["source_contract"]["canonical"]:
                    connection_ref = source.get("connection_ref")
                    if connection_ref in dependency_index:
                        acceptance_platform_refs.add(connection_ref)
                        gateway_ref = dependency_index[connection_ref][1]["gateway_ref"]
                        if gateway_ref is not None:
                            acceptance_platform_refs.add(gateway_ref)
                for product in use_case["data_products"]:
                    target_ref = product.get("target_ref")
                    if target_ref in dependency_index:
                        acceptance_platform_refs.add(target_ref)
                        acceptance_platform_refs.add(dependency_index[target_ref][1]["workspace_ref"])
                for reference in sorted(acceptance_platform_refs):
                    dependency = dependency_index.get(reference)
                    if dependency and dependency[1]["status"]["state"] not in ACCEPTED_EVIDENCE_STATES:
                        errors.append(
                            f"{label}: platform dependency {reference!r} has "
                            f"{dependency[1]['status']['state']!r} evidence, which does not satisfy acceptance"
                        )
        elif use_case["acceptance"].get("runtime_proof_refs"):
            errors.append(f"{label}: runtime_proof_refs require platform_dependencies")
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
    ]
    dependencies = use_case.get("platform_dependency_refs", [])
    if dependencies:
        lines.extend(
            [
                "",
                f"**Logical platform dependencies:** {_list(dependencies)}",
            ]
        )
    lines.extend(
        [
            "",
            "| Report | Purpose | Modes | Pages | Bindings | Status |",
            "|---|---|---|---:|---:|---|",
        ]
    )
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
                "| ID | Source | Purpose | Availability | Grain | Keys | Required for | Connection | Status |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for source in use_case["source_contract"][boundary]:
            lines.append(
                f"| `{source['id']}` | {source['source_system']}.{source['source_object']} | {source['purpose']} | "
                f"{source['availability']} | {source.get('expected_grain') or '—'} | {_list(source.get('key_fields', []))} | "
                f"{_list(source['required_for'])} | {source.get('connection_ref') or '—'} | "
                f"{_status(source['status'])} |"
            )
        if not use_case["source_contract"][boundary]:
            lines.append("| — | — | — | — | — | — | — | — | — |")
        lines.append("")

    lines.extend(
        [
            "## 4. Target data products",
            "",
            "| Layer | Product | Grain | Business keys | Sources | Target | History | Status |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for product in use_case["data_products"]:
        lines.append(
            f"| {product['layer']} | `{product['name']}` | {product.get('grain') or '—'} | "
            f"{_list(product['business_keys'])} | {_list(product['source_refs'])} | "
            f"{product.get('target_ref') or '—'} | {product['history']} | {_status(product['status'])} |"
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

    assurance = use_case.get("delivery_assurance")
    lines.extend(["", "## 8. Delivery assurance", ""])
    if assurance is None:
        lines.extend(["Delivery assurance is not yet contracted.", ""])
    else:
        source = assurance["source_behavior"]
        lines.extend(
            [
                "### Source behavior and incremental processing",
                "",
                "| Profile | Publication | Freshness | Initial rows | Daily changes | Mode | Cursor | Deletes | Late arrivals | Reconciliation | Status |",
                "|---|---|---:|---:|---:|---|---|---|---|---|---|",
                f"| {source.get('profile_ref') or '—'} | {source.get('publication_cadence') or '—'} | "
                f"{source.get('freshness_slo_minutes') or '—'} | {source.get('initial_volume_rows') if source.get('initial_volume_rows') is not None else '—'} | "
                f"{source.get('daily_change_rows') if source.get('daily_change_rows') is not None else '—'} | {source['incremental_mode']} | "
                f"{source.get('cursor_field') or '—'} | {source['delete_handling']} | {source.get('late_arrival_window') or '—'} | "
                f"{source.get('reconciliation_cadence') or '—'} | {_status(source['status'])} |",
                "",
                "### Executable data-quality rules",
                "",
                "| Rule | Layer | Dimension | Assertion | Severity | Threshold | Owner | Remediation | Evidence | Status |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for rule in assurance["data_quality"]["rules"]:
            lines.append(
                f"| `{rule['id']}` | {rule['layer']} | {rule['dimension']} | {rule['assertion']} | {rule['severity']} | "
                f"{_threshold(rule['threshold'])} | {rule['owner_ref']} | {rule['remediation']} | "
                f"{_list(rule['evidence_required'])} | {_status(rule['status'])} |"
            )
        quality = assurance["data_quality"]
        lines.extend(
            [
                "",
                f"**Failed-run recording:** `{quality['failed_run_recording']}`  ",
                f"**Last approved output retained:** `{'yes' if quality['last_approved_output_retained'] else 'no'}`  ",
                f"**Quarantine target:** `{quality.get('quarantine_target_ref') or '—'}`  ",
                f"**Data-quality status:** {_status(quality['status'])}",
                "",
                "### Product health and alert routes",
                "",
                f"**Correlation ID:** `{assurance['observability']['correlation_id_field']}`  ",
                f"**Stale after:** {assurance['observability']['stale_after_minutes'] or 'open'} minutes  ",
                f"**Health components:** {_list(assurance['observability']['product_health_components'])}",
                "",
                "| Signal | Type | Trigger | Threshold | Recipient | Channel | Response | Runbook | Retention | Test | Status |",
                "|---|---|---|---|---|---|---|---|---:|---|---|",
            ]
        )
        for signal in assurance["observability"]["signals"]:
            lines.append(
                f"| `{signal['id']}` | {signal['type']} | {signal['trigger']} | {_threshold(signal.get('threshold'))} | "
                f"{signal['recipient_ref'] or 'open'} | {signal['channel'] or 'open'} | {signal['response_slo'] or 'open'} | {signal['runbook_ref'] or 'open'} | "
                f"{str(signal['retention_days']) + ' days' if signal['retention_days'] is not None else 'open'} | {signal['test_method'] or 'open'} | {_status(signal['status'])} |"
            )
        reliability = assurance["reliability"]
        lines.extend(
            [
                "",
                "### Reliability and recovery",
                "",
                f"**Concurrency control:** {reliability['concurrency_control']}  ",
                f"**Idempotency key:** `{reliability['idempotency_key']}`  ",
                f"**Uncertain mutation:** `{reliability['uncertain_mutation_strategy']}`  ",
                f"**Rollback:** `{reliability['rollback_procedure_ref']}`  ",
                f"**Environment bootstrap:** `{reliability['bootstrap_procedure_ref']}`",
                "",
                "| Failure class | Action | Attempts | Backoff | Jitter |",
                "|---|---|---:|---|---|",
            ]
        )
        for rule in reliability["retry_policy"]:
            lines.append(
                f"| {rule['failure_class']} | {rule['action']} | {rule['max_attempts']} | {rule['backoff']} | "
                f"{'yes' if rule['jitter'] else 'no'} |"
            )
        lines.extend(["", f"**Delivery-assurance status:** {_status(assurance['status'])}", ""])

    lines.extend(
        [
            "",
            "## 9. Security, quality, release and operational controls",
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
            "## 10. Acceptance and regression",
            "",
            f"**Snapshot rule:** {acceptance['snapshot_rule']}",
            "",
            f"**Regression scope:** {_list(acceptance['regression_scope'])}",
            "",
            f"**Required evidence:** {_list(acceptance['evidence_required'])}",
            "",
            "**Runtime proof references:** "
            + _list(
                [
                    f"{reference['environment']}:{reference['proof_ref']}"
                    for reference in acceptance.get("runtime_proof_refs", [])
                ]
            ),
            "",
            f"**Status:** {_status(acceptance['status'])}",
            "",
            "## 11. Open gates",
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
