from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "tooling/generator/schemas/consulting_operating_profile.schema.json"
PROFILE = REPO / "core/engagement_profiles/nagarro_consulting.yaml"


def test_nagarro_profile_conforms_to_the_operating_contract():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    profile = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(profile)


def test_nagarro_profile_is_team_based_and_contains_no_customer_default():
    profile = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    raw = PROFILE.read_text(encoding="utf-8").lower()

    assert profile["provider"]["operating_model"] == "consulting_organization"
    assert profile["staffing"]["execution_model"] == "resource_plan"
    assert profile["commercial"]["pricing_model"] == "organization_project_commercials"
    assert profile["commercial"]["customer_price_values_in_profile"] is False
    assert "hochtief" not in raw and "htf" not in raw
