"""
test_architecture_blueprint_schema.py — ADR-0015 / T2.

Guards the shared ArchitectureBlueprint IR contract:
  - the schema file is a valid JSON Schema (draft 2020-12);
  - the worked example in the mirrored spec validates against it;
  - the AI-grounding surface rejects bronze (never a grounding source);
  - PARITY: the schema file is identical (canonicalized) to the ```json schema
    block embedded in architecture-blueprint-ir-spec.md. Because that spec is
    maintained byte-identical across the ALUCA and Meridian repos, this in-repo
    check transitively guarantees the schema is field-identical across mirrors.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_FILE = _REPO_ROOT / "tooling" / "generator" / "schemas" / "architecture_blueprint.schema.json"
_SPEC_FILE = _REPO_ROOT / "docs" / "architecture" / "research" / "architecture-blueprint-ir-spec.md"

_JSON_BLOCK = re.compile(r"```json\n(.*?)```", re.DOTALL)


def _load_schema() -> dict:
    return json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))


def _spec_json_blocks() -> list[dict]:
    blocks = []
    for raw in _JSON_BLOCK.findall(_SPEC_FILE.read_text(encoding="utf-8")):
        blocks.append(json.loads(raw))
    return blocks


def _spec_schema_block() -> dict:
    for obj in _spec_json_blocks():
        if isinstance(obj, dict) and "$schema" in obj and obj.get("title") == "ArchitectureBlueprint":
            return obj
    raise AssertionError("no ArchitectureBlueprint schema block found in the IR spec")


def _spec_example_block() -> dict:
    for obj in _spec_json_blocks():
        if isinstance(obj, dict) and "$schema" not in obj and "platform" in obj:
            return obj
    raise AssertionError("no worked-example instance found in the IR spec")


def _canon(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def test_schema_is_valid_jsonschema():
    Draft202012Validator.check_schema(_load_schema())


def test_worked_example_validates():
    validator = Draft202012Validator(_load_schema())
    validator.validate(_spec_example_block())  # raises on failure


def test_grounding_surface_rejects_bronze():
    """AI agents ground on gold/silver, never bronze (ADR-0015 / ai_readiness §3.6)."""
    instance = _spec_example_block()
    instance["ai_grounding"]["grounding_surface"] = ["gold", "bronze"]
    with pytest.raises(ValidationError):
        Draft202012Validator(_load_schema()).validate(instance)


def test_gold_name_pattern_enforced():
    instance = _spec_example_block()
    instance["medallion"]["gold"]["data_products"][0]["name"] = "customers"  # missing dim_/fact_/agg_
    with pytest.raises(ValidationError):
        Draft202012Validator(_load_schema()).validate(instance)


def test_schema_parity_with_spec_block():
    """The schema file must match the spec's embedded schema block (cross-mirror parity)."""
    assert _canon(_load_schema()) == _canon(_spec_schema_block()), (
        "architecture_blueprint.schema.json has drifted from the IR spec's schema block; "
        "they must stay identical (and the spec is mirrored byte-identical across repos)."
    )
