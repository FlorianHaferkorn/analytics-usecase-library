"""Smoke test for check_visual_format — the formatting/semantic-readiness governance gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    import sys
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_gate_flags_vs_target_hero_without_benchmark():
    cvf = _load("check_visual_format", "tooling/validation/check_visual_format.py")
    pol = cvf._policy()
    units = {"x.no.bench.pct": "% (1 decimal)"}
    bracket = {"id": "TST", "ux_layout_rules": {"page_1_summary": {
        "component_3s": {"kpi_id": "x.no.bench.pct", "comparison": "vs_target",
                         "status_logic": "higher_is_better"},
        "component_30s": []}}}
    problems = cvf.check_bracket(bracket, units, pol)
    assert any("no benchmark" in p for p in problems)


def test_gate_clean_hero_with_benchmark_and_status():
    cvf = _load("check_visual_format", "tooling/validation/check_visual_format.py")
    pol = cvf._policy()
    # supply.otif.pct has a benchmark; give it a unit → no advisory
    units = {"supply.otif.pct": "% (1 decimal)"}
    bracket = {"id": "TST", "ux_layout_rules": {"page_1_summary": {
        "component_3s": {"kpi_id": "supply.otif.pct", "comparison": "vs_target",
                         "status_logic": "higher_is_better"},
        "component_30s": []}}}
    assert cvf.check_bracket(bracket, units, pol) == []
