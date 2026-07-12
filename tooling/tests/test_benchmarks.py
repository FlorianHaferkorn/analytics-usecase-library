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
    check_bracket_links, _benchmarked_kpi_ids,
)

REPO = Path(__file__).resolve().parents[2]
_REGISTRY = REPO / "core/kpi_catalog/benchmarks.yaml"
_SCHEMA = REPO / "tooling/generator/schemas/benchmark.schema.json"

_ALLOWED = {"industry_standard", "market_report"}


def _src(**over):
    s = dict(citation="SQM Group 2024 — world-class FCR 80%+ (industry avg 70%).",
             source_type="market_report", tier="large_sample", as_of="2026-07-11")
    s.update(over)
    return s


def _entry(**over):
    base = dict(
        kpi_id="ops.oee.pct", scope="Manufacturing", benchmark_class="normative",
        metric="world_class", value=85.0, unit="pct", direction="higher_is_better",
        sources=[_src(tier="primary"), _src()],   # ≥2, ≥1 authoritative
    )
    base.update(over)
    return base


def _empirical(**over):
    segs = over.pop("segments", [{"industry": "Retail", "value": 45.0},
                                 {"industry": "SaaS", "value": 35.0}])
    return _entry(benchmark_class="empirical", kpi_id="crm.nps.index", unit="index",
                  metric="median", value=44.0, segments=segs, **over)


def test_valid_normative_entry_has_no_violations():
    assert validate_entry(_entry(), _ALLOWED) == []


def test_valid_empirical_entry_has_no_violations():
    assert validate_entry(_empirical(), _ALLOWED) == []


def test_unknown_kpi_is_flagged():
    assert any("Golden Thread" in e for e in validate_entry(_entry(kpi_id="does.not.exist"), _ALLOWED))


def test_single_source_is_flagged():
    assert any("corroborating" in e for e in validate_entry(_entry(sources=[_src(tier="primary")]), _ALLOWED))


def test_no_authoritative_source_is_flagged():
    errs = validate_entry(_entry(sources=[_src(tier="secondary"), _src(tier="secondary")]), _ALLOWED)
    assert any("authoritative" in e for e in errs)


def test_empirical_without_segments_is_flagged():
    errs = validate_entry(_empirical(segments=[]), _ALLOWED)
    assert any("segment" in e for e in errs)


def test_empirical_needs_two_segments():
    errs = validate_entry(_empirical(segments=[{"industry": "Retail", "value": 45.0}]), _ALLOWED)
    assert any("segment" in e for e in errs)


def test_bad_benchmark_class_is_flagged():
    assert any("benchmark_class" in e for e in validate_entry(_entry(benchmark_class="guess"), _ALLOWED))


def test_bad_as_of_is_flagged():
    assert any("as_of" in e for e in validate_entry(_entry(sources=[_src(tier="primary"), _src(as_of="July 2026")]), _ALLOWED))


def test_committed_empirical_benchmarks_have_segments():
    """Every committed empirical benchmark is peer-relative (has ≥2 industry segments)."""
    data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
    for b in data["benchmarks"]:
        if b.get("benchmark_class") == "empirical":
            assert len(b.get("segments", [])) >= 2, b["kpi_id"]
        assert any(s.get("tier") in ("primary", "large_sample") for s in b["sources"]), b["kpi_id"]


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


def test_benchmark_axis_links_are_intact():
    """Every hero card opting into the benchmark axis has a governed benchmark."""
    assert check_bracket_links() == []


def test_ops001_hero_opts_into_benchmark_axis():
    """The OPS-001 pilot wires OEE's hero to the world-class benchmark."""
    ops = yaml.safe_load((REPO / "core/usecases/core/OPS-001_Operations_Performance/UseCase_Bracket.yaml").read_text())
    card = ops["ux_layout_rules"]["page_1_summary"]["component_3s"]
    assert card["benchmark"] is True
    assert card["kpi_id"] in _benchmarked_kpi_ids()
    # additive — the primary comparison is preserved
    assert card["comparison"] == "vs_target"
