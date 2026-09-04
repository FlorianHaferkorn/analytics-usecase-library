from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "generator" / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def _document() -> dict:
    return {
        "schema_version": "2.0.0",
        "stack": "microsoft_fabric",
        "reference_date": "2026-09-04",
        "tenant": "Example tenant",
        "region": "West Europe",
        "ledger_ref": "deliverables/ledger.md",
        "model_ref": "architecture/model.json",
        "blueprint_ref": "generated/blueprint.json",
        "mapping_ref": "architecture/mapping.json",
        "domains": [
            {
                "id": "domain_finance",
                "key": "finance",
                "delivery_scope": "detailed",
                "capacity": "fbfinance01",
                "use_case_refs": ["uc_finance_reporting"],
            }
        ],
        "use_cases": [
            {
                "id": "uc_finance_reporting",
                "name": "Finance reporting",
                "domain_ref": "domain_finance",
                "architecture_detail": "full",
            }
        ],
        "environments": {
            "recommended": ["dev", "test", "prod"],
            "decision_ref": "decision_environment_strategy",
            "accepted": False,
        },
        "contracts": [
            {
                "id": "contract_finance_gold",
                "kind": "gold",
                "source_ref": "contracts/finance-gold.json",
                "required_for": ["architecture", "apply"],
            }
        ],
        "compiler_policy": {
            "version": "1.0.0",
            "generated_ref": "generated/current",
            "fail_closed_for_apply": True,
            "allow_review_with_blockers": True,
        },
    }


def test_architecture_input_schema_accepts_a_neutral_customer_package() -> None:
    validator = Draft202012Validator(
        _load("project_architecture_input.schema.json"),
        format_checker=FormatChecker(),
    )
    assert list(validator.iter_errors(_document())) == []


def test_architecture_input_schema_is_closed() -> None:
    document = _document()
    document["customer_specific_shortcut"] = True
    validator = Draft202012Validator(_load("project_architecture_input.schema.json"))
    assert any("Additional properties" in error.message for error in validator.iter_errors(document))
