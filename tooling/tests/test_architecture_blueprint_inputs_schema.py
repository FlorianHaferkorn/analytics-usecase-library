"""
test_architecture_blueprint_inputs_schema.py — ADR-0024.

The derivation inputs are ALUCA's own contract (the IR schema is Meridian's, byte-identical,
and has no field for the gold target). The one choice typed strictly there is
`domains[].gold_target`; everything else stays open so existing input files keep loading.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from tooling.superversion.architecture_blueprint import (
    DEFAULT_GOLD_TARGET,
    GOLD_TARGETS,
    gold_targets,
    validate_inputs,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "tooling" / "generator" / "schemas" / "architecture_blueprint_inputs.schema.json"
AURORA = REPO / "showcases" / "aurora_group" / "architecture" / "aurora_architecture_inputs.json"


def _inputs(**dom):
    return {"domains": [{"name": "Commercial", **dom}]}


def test_schema_enum_matches_the_code():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    field = schema["properties"]["domains"]["items"]["properties"]["gold_target"]
    assert tuple(field["enum"]) == GOLD_TARGETS
    assert field["default"] == DEFAULT_GOLD_TARGET == "warehouse_dbt"


@pytest.mark.parametrize("value", ["warehouse_dbt", "mlv"])
def test_valid_targets_pass(value):
    validate_inputs(_inputs(gold_target=value))


@pytest.mark.parametrize("value", ["MLV", "lakeview", "warehouse", "", None, 1])
def test_invalid_targets_are_rejected(value):
    with pytest.raises(ValidationError):
        validate_inputs(_inputs(gold_target=value))


def test_absent_field_means_default_and_is_not_forwarded():
    assert gold_targets(_inputs()) == {}
    assert gold_targets(_inputs(gold_target="warehouse_dbt")) == {}
    assert gold_targets(_inputs(gold_target="mlv")) == {"Commercial": "mlv"}


def test_gold_targets_validates_before_it_reads():
    with pytest.raises(ValidationError):
        gold_targets(_inputs(gold_target="MLV"))


def test_unknown_keys_stay_open():
    """The deriver reads more keys than the schema types (architecture_concept, …); an input
    file written before ADR-0024 must still validate."""
    validate_inputs({"stack": "fabric", "architecture_concept": "medallion",
                     "domains": [{"name": "X", "endorsement": "certified", "whatever": 1}]})


def test_aurora_showcase_inputs_are_valid_and_choose_mlv():
    inputs = json.loads(AURORA.read_text(encoding="utf-8"))
    validate_inputs(inputs)
    assert gold_targets(inputs) == {"Commercial": "mlv"}
