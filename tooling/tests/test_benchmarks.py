"""Tests for the Content-Grounding §6.3 benchmark validator (K4).

Covers the pure provenance validator, schema conformance of the registry, and a
guard that the committed registry stays 100% grounded (no fabricated benchmarks).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from tooling.validation.check_benchmarks import (
    check_registry, validate_entry, _load_allowed_source_types,
)

REPO = Path(__file__).resolve().parents[2]
_REGISTRY = REPO / "core/kpi_catalog/benchmarks.yaml"
_SCHEMA = REPO / "tooling/generator/schemas/benchmark.schema.json"

_ALLOWED = {"industry_standard", "market_report"}


def _entry(**over):
    base = dict(
        kpi_id="ops.oee.pct", scope="Manufacturing", metric="world_class",
        value=85.0, unit="pct", direction="higher_is_better",
        source="Nakajima (1988), Introduction to TPM — world-class OEE.",
        source_type="industry_standard", as_of="2026-07-11",
    )
    base.update(over)
    return base


def test_valid_entry_has_no_violations():
    assert validate_entry(_entry(), _ALLOWED) == []


def test_unknown_kpi_is_flagged():
    errs = validate_entry(_entry(kpi_id="does.not.exist"), _ALLOWED)
    assert any("Golden Thread" in e for e in errs)


def test_unknown_source_type_is_flagged():
    errs = validate_entry(_entry(source_type="blog_post"), _ALLOWED)
    assert any("source_type" in e for e in errs)


def test_missing_source_is_flagged():
    errs = validate_entry(_entry(source="  "), _ALLOWED)
    assert any("source citation missing" in e for e in errs)


def test_bad_as_of_is_flagged():
    errs = validate_entry(_entry(as_of="July 2026"), _ALLOWED)
    assert any("as_of" in e for e in errs)


def test_pct_out_of_range_is_flagged():
    errs = validate_entry(_entry(value=140.0, unit="pct"), _ALLOWED)
    assert any("above sane maximum" in e for e in errs)


def test_committed_registry_is_fully_grounded():
    """The real registry must have zero provenance violations — no fabricated numbers."""
    assert check_registry() == []


def test_registry_conforms_to_schema():
    import jsonschema  # noqa: PLC0415
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)


def test_source_types_load():
    assert "industry_standard" in _load_allowed_source_types()
