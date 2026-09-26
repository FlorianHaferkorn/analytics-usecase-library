"""Schema and pinned-fixture checks for the neutral AI data-handling contract.

The executable policy evaluator lives in Studio, not in the Python compiler or
Meridian runtime. This test only validates the cross-product contract surface.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "tooling/generator/schemas/ai_data_handling_policy.schema.json"
FIXTURE = ROOT / "core/fixtures/neutral/ai-data-handling-policy/data_handling_cases.json"
MIRROR = FIXTURE.with_name("MIRROR.json")


def test_ai_data_handling_schema_and_pinned_neutral_fixture():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    mirror = json.loads(MIRROR.read_text(encoding="utf-8"))

    jsonschema.Draft7Validator.check_schema(schema)
    assert fixture["contract_version"] == mirror["contract_version"] == "ai-data-handling-policy/1.0.0"
    assert mirror["shared_executable_runtime"] is False
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == mirror["sha256"]
    assert len(fixture["cases"]) == 14
    validator = jsonschema.Draft7Validator(schema)
    for case in fixture["cases"]:
        if case["allowed"]:
            validator.validate({
                "contract_version": fixture["contract_version"],
                "profile": case["profile"],
                "context": case["context"],
            })


def test_ai_data_handling_schema_rejects_training_and_missing_boundary_evidence():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]}
    validator = jsonschema.Draft7Validator(schema)

    missing_evidence = cases["customer-managed-without-evidence"]
    assert not validator.is_valid({
        "contract_version": "ai-data-handling-policy/1.0.0",
        "profile": missing_evidence["profile"], "context": missing_evidence["context"],
    })
    with_training = json.loads(json.dumps(cases["public-external"]))
    with_training["profile"]["data_handling"]["provider_training_allowed"] = True
    assert not validator.is_valid({
        "contract_version": "ai-data-handling-policy/1.0.0",
        "profile": with_training["profile"], "context": with_training["context"],
    })
