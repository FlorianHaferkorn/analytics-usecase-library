"""WB-002: the capability-pack contract is closed, and the fixtures prove it."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO / "tooling/validation/check_capability_packs.py"
FIXTURES = REPO / "core/fixtures/neutral/minimal-fabric-foundation"
PACK = REPO / "core/capabilities/fabric-foundation/capability.yaml"


def _load_validator():
    spec = importlib.util.spec_from_file_location("check_capability_packs", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _expectations() -> dict:
    return yaml.safe_load((FIXTURES / "expectations.yaml").read_text(encoding="utf-8"))


def _schema():
    pytest.importorskip("jsonschema")
    return validator.load_schema(REPO)


def _validate(path: Path):
    return validator.validate_capability_pack(validator.load_document(path), _schema())


def test_the_contract_is_a_valid_json_schema():
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(validator.load_schema(REPO))


def test_the_fabric_foundation_pack_passes_all_three_dimensions():
    assert _validate(PACK) == []


def test_the_fabric_foundation_pack_pre_selects_no_option():
    pack = yaml.safe_load(PACK.read_text(encoding="utf-8"))["capability"]
    for decision in pack["decisions"]:
        assert decision["recommendation_option_ref"] is None, decision["id"]
        assert len(decision["options"]) >= 2, decision["id"]
        assert decision["state"] in {"draft", "proposed", "ready_for_decision"}, decision["id"]


@pytest.mark.parametrize("name", _expectations()["valid"])
def test_valid_fixtures_are_accepted(name):
    assert _validate(FIXTURES / "valid" / name) == []


@pytest.mark.parametrize("name,category", sorted(_expectations()["invalid"].items()))
def test_invalid_fixtures_are_rejected_for_the_stated_reason(name, category):
    findings = _validate(FIXTURES / "invalid" / name)
    assert findings, f"{name} was accepted although it must fail with a {category} finding"
    assert category in {f.category for f in findings}, [str(f) for f in findings]


def test_every_fixture_carries_an_expectation():
    expected = set(_expectations()["valid"]) | set(_expectations()["invalid"])
    on_disk = {
        path.name
        for path in list((FIXTURES / "valid").glob("*.yaml")) + list((FIXTURES / "invalid").glob("*.yaml"))
    }
    assert on_disk == expected, "a fixture without an expectation would be silently skipped"


def test_the_neutrality_scan_catches_a_customer_token():
    document = {
        "schema_version": "1.0.0",
        "capability": {"id": "x", "version": "1.0.0", "note": "derived from the HTF engagement"},
    }
    findings = validator.check_neutrality(document)
    assert any(f.category == validator.CATEGORY_NEUTRALITY for f in findings)


def test_the_cli_reports_the_core_packs_as_green():
    pytest.importorskip("jsonschema")
    assert validator.main(["--root", str(REPO)]) == 0
