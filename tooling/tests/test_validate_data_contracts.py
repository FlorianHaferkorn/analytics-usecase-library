"""
test_validate_data_contracts.py — structural validator of the domain data contracts.

Covers the structured quality fields added with A-20/A-23 (table ``showcase``, column
``nullable``/``target_state``/``unknown_member``/``checks``) and that every committed
contract passes the validator.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tooling.validation.check_validate_data_contracts import (
    check_column, check_entry, validate_contract,
)

REPO = Path(__file__).resolve().parents[2]
COLS = {"Good Units", "Output Units", "PromoKey"}


def _contract(columns, **table):
    return {"domain": "t", "fact": [{"name": "fact_x", "grain": "row", "columns": columns, **table}]}


def test_committed_contracts_are_valid():
    for path in sorted((REPO / "core" / "data_contracts" / "domains").glob("*.yaml")):
        errors = validate_contract(yaml.safe_load(path.read_text(encoding="utf-8")))
        assert errors == [], f"{path.name}: {errors}"


@pytest.mark.parametrize("entry", [
    {"gte": 0}, {"gt": 0.5}, {"lte": 100}, {"lt": -1},
    {"between": [0, 10]}, {"between": [1, 1]},
    {"in": ["A", "B"]}, {"in": [1, 2]},
    {"lte_column": "Output Units"}, {"gte_column": "Output Units", "when_present": True},
])
def test_valid_check_entries(entry):
    assert check_entry(entry, "Good Units", COLS) == []


@pytest.mark.parametrize("entry, fragment", [
    ({}, "exactly one rule key"),
    ({"gte": 0, "lte": 5}, "exactly one rule key"),
    ({"min": 0}, "unknown key"),
    ({"gte": "0"}, "needs a number"),
    ({"gte": True}, "needs a number"),
    ({"between": [0]}, "between needs"),
    ({"between": [5, 1]}, "lower bound"),
    ({"in": []}, "non-empty list"),
    ({"in": [["a"]]}, "non-empty list"),
    ({"lte_column": "Missing Units"}, "not a column of this table"),
    ({"lte_column": "Good Units"}, "column itself"),
    ({"gte": 0, "when_present": False}, "when_present must be true"),
    ("gte 0", "must be a mapping"),
])
def test_invalid_check_entries(entry, fragment):
    errors = check_entry(entry, "Good Units", COLS)
    assert errors and any(fragment in e for e in errors), errors


def test_unknown_member_rules():
    ok = {"name": "PromoKey", "type": "int", "ref": "dim_promo", "nullable": False, "unknown_member": -1}
    assert check_column(ok, COLS) == []
    no_ref = {"name": "PromoKey", "unknown_member": -1}
    assert any("needs ref" in e for e in check_column(no_ref, COLS))
    nullable = {**ok, "nullable": True}
    assert any("never NULL" in e for e in check_column(nullable, COLS))
    not_scalar = {**ok, "unknown_member": [-1]}
    assert any("scalar" in e for e in check_column(not_scalar, COLS))


def test_boolean_fields_and_checks_list():
    assert any("target_state" in e for e in check_column({"name": "x", "target_state": "yes"}, COLS))
    assert any("nullable" in e for e in check_column({"name": "x", "nullable": 1}, COLS))
    assert any("non-empty list" in e for e in check_column({"name": "x", "checks": []}, COLS))
    assert any("non-empty list" in e for e in check_column({"name": "x", "checks": {"gte": 0}}, COLS))


def test_validate_contract_reports_table_and_column():
    good = _contract([{"name": "Output Units", "type": "int"},
                      {"name": "Good Units", "type": "int", "checks": [{"gte": 0}, {"lte_column": "Output Units"}]}],
                     showcase=False)
    assert validate_contract(good) == []
    bad = _contract([{"name": "Good Units", "checks": [{"lte_column": "Output Units"}]}], showcase="no")
    errors = validate_contract(bad)
    assert any(e.startswith("fact_x: showcase must be a boolean") for e in errors)
    assert any(e.startswith("fact_x.Good Units: lte_column 'Output Units'") for e in errors)


def test_structure_rules_unchanged():
    assert validate_contract(None) == ["not a YAML object"]
    assert validate_contract({"version": 1}) == ["missing domain, dimension, or fact"]
    assert validate_contract({"domain": "d", "fact": [{"name": "f"}]}) == ["fact 'f' missing grain"]
    assert validate_contract({"domain": "d", "dimension": [{"columns": []}]}) == ["dimension entry missing name"]


def test_source_column_separates_model_name_from_gold_column():
    """`{name: Sales Units, source_column: Quantity}` — Modellname und physische Gold-Spalte getrennt,
    wie TMDL `column` + `sourceColumn` (29.09.2026)."""
    assert check_column({"name": "Sales Units", "source_column": "Quantity"}, COLS) == []
    assert any("non-empty string" in e for e in check_column({"name": "x", "source_column": ""}, COLS))
    assert any("equals name" in e for e in check_column({"name": "x", "source_column": "x"}, COLS))
