from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion._dataarch_vendor import load_emitters
from tooling.superversion.project_package.adapters.decision_proposals import (
    FIELD_MAPPING,
    SOURCE_FIELDS,
    adapt_decision_proposals,
)
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.validator import validate_project_package


REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "tooling" / "generator" / "schemas"
PROJECT_SCHEMAS = sorted(SCHEMAS.glob("project_*.schema.json"))


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _proposal(**overrides: object) -> dict:
    base = {
        "id": "SEC-RLS",
        "topic": "Row-level security",
        "gap": "Which scope controls row access?",
        "proposal": "Use the approved organisation scope.",
        "derived_from": "governed organisation columns",
        "confidence": "hoch",
        "status": "vorbelegt",
        "alternatives": ["Use a project scope"],
        "decider": "Data Owner",
        "if_undecided": "Build remains blocked.",
        "ermittlung": {"wo": "Policy", "wen": "Data Owner", "wenn_unklar": "Escalate"},
        "kunde": {"frage": "Who may see what?", "folge": "Controls access.", "warum": "Required."},
        "faelligkeit": "vor Produktivsetzung",
        "markers": ["SECURITY_SCOPE"],
    }
    base.update(overrides)
    return base


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _minimal_modules(root: Path) -> list[dict]:
    zero_hash = "0" * 64
    documents = {
        "opportunity/opportunity.yaml": (
            "opportunity",
            {
                "schema_version": "2.0.0",
                "opportunity_id": "opp_demo",
                "customer_ref": "customer_demo",
                "objectives": ["Prove the governed delivery path"],
                "scope_status": "qualified",
            },
            None,
        ),
        "commercial/commercial.yaml": (
            "commercial",
            {
                "schema_version": "2.0.0",
                "status": "assumption",
                "authority_ref": "env:PREIS_KANON_MANDANTEN_DIR/preis_kanon.yaml",
                "currency": "EUR",
                "estimate": {"value": None, "basis_refs": []},
                "price_values_embedded": False,
            },
            None,
        ),
        "plan/plan.yaml": (
            "plan",
            {"schema_version": "2.0.0", "work_packages": [], "dependencies": []},
            None,
        ),
        "observed/dev.json": (
            "observed_state",
            {
                "schema_version": "2.0.0",
                "environment": "dev",
                "captured_at": "2026-09-04T09:00:00Z",
                "collector": "fixture",
                "resources": [
                    {
                        "logical_id": "workspace_dev",
                        "resource_type": "workspace",
                        "physical_id": "fixture-workspace",
                        "state_hash": zero_hash,
                    }
                ],
            },
            "dev",
        ),
        "discovery/decision_set.yaml": (
            "decision_set",
            adapt_decision_proposals([_proposal()]),
            None,
        ),
    }
    modules = []
    for relative, (module_type, document, environment) in documents.items():
        path = root / relative
        if path.suffix == ".json":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        else:
            _write_yaml(path, document)
        schema_id = _load_schema(f"project_{module_type}.schema.json")["$id"]
        module = {
            "module_type": module_type,
            "path": relative,
            "schema_id": schema_id,
            "sha256": canonical_sha256(document),
        }
        if environment is not None:
            module["environment"] = environment
        modules.append(module)
    return modules


def test_all_project_package_schemas_are_closed_draft_2020_12() -> None:
    assert len(PROJECT_SCHEMAS) == 7
    for path in PROJECT_SCHEMAS:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_adapter_declares_every_source_field_exactly_once() -> None:
    assert frozenset(FIELD_MAPPING) == SOURCE_FIELDS
    assert all(paths for paths in FIELD_MAPPING.values())


def test_adapter_rejects_source_contract_drift() -> None:
    changed = _proposal(new_field="silent drift")
    with pytest.raises(ValueError, match="contract drift"):
        adapt_decision_proposals([changed])


def test_preselection_is_never_approval_or_buildable() -> None:
    result = adapt_decision_proposals([_proposal()])
    instance = result["instances"][0]
    assert instance["selection"] == {
        "state": "preselected",
        "option_ref": "proposal",
        "custom_value": None,
    }
    assert instance["approval"]["state"] == "proposed"
    assert instance["approval"]["decided_by"] is None
    assert instance["delivery"]["state"] == "not_compiled"


def test_open_without_proposal_stays_draft() -> None:
    result = adapt_decision_proposals(
        [_proposal(proposal=None, status="offen", alternatives=["Customer input"])]
    )
    instance = result["instances"][0]
    assert instance["selection"]["state"] == "unselected"
    assert instance["approval"]["state"] == "draft"


def test_domain_fanout_requires_explicit_scope_mapping() -> None:
    proposal = _proposal(id="SEC-RLS·hti")
    with pytest.raises(ValueError, match="unresolved domain scope"):
        adapt_decision_proposals([proposal])
    mapped = adapt_decision_proposals([proposal], {"hti": "domain_hti"})
    assert mapped["instances"][0]["scope_refs"] == ["domain_hti"]


def test_all_current_meridian_proposals_map_and_validate() -> None:
    proposals = load_emitters()["propose_all"]({})
    assert len(proposals) == 19
    result = adapt_decision_proposals(proposals)
    schema = _load_schema("project_decision_set.schema.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)
    assert len(result["definitions"]) == len(proposals)
    assert len(result["instances"]) == len(proposals)


def test_project_package_validates_hashes_references_and_revision(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {"id": "aluca_nagarro_consulting", "version": "1.0.0", "sha256": "1" * 64},
        "capability_locks": [{"id": "fabric_platform_foundation", "version": "1.0.0", "sha256": "2" * 64}],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)
    assert validate_project_package(tmp_path, SCHEMAS) == []

    manifest["revision"] = 2
    modules[0]["sha256"] = "f" * 64
    _write_yaml(tmp_path / "package.yaml", manifest)
    errors = validate_project_package(tmp_path, SCHEMAS)
    assert "package.yaml: revision > 1 requires parent_revision_hash" in errors
    assert any("hash drift" in error for error in errors)


def test_project_package_rejects_unresolved_decision_references(tmp_path: Path) -> None:
    modules = _minimal_modules(tmp_path)
    decision_path = tmp_path / "discovery" / "decision_set.yaml"
    decisions = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
    decisions["instances"][0]["definition_ref"] = "d_missing"
    _write_yaml(decision_path, decisions)
    for module in modules:
        if module["module_type"] == "decision_set":
            module["sha256"] = canonical_sha256(decisions)
    manifest = {
        "schema_version": "2.0.0",
        "package_id": "package_demo",
        "project_ref": "project_demo",
        "revision": 1,
        "state": "working",
        "parent_revision_hash": None,
        "operating_profile_lock": {"id": "aluca_nagarro_consulting", "version": "1.0.0", "sha256": "1" * 64},
        "capability_locks": [],
        "modules": modules,
    }
    _write_yaml(tmp_path / "package.yaml", manifest)
    assert any("unresolved definition_ref" in error for error in validate_project_package(tmp_path, SCHEMAS))


def test_canonical_hash_ignores_mapping_order() -> None:
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})
