"""Deterministic variance/status measures (not narrative prose)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_scaffold_generator.status_measures import title_measure, variance_measures


def _by_role(defs):
    return {d.role: d for d in defs}


def test_no_target_emits_nothing():
    # ADR-0009: no target ⇒ no status, never a fabricated verdict
    assert variance_measures("OTIF %", None, "higher_is_better") == []


def test_no_direction_emits_nothing():
    assert variance_measures("OTIF %", "[OTIF % Plan]", None) == []


def test_measure_name_target_used_as_is():
    d = _by_role(variance_measures("OTIF %", "[OTIF % Plan]", "higher_is_better"))
    assert d["variance"].dax == "[OTIF %] - [OTIF % Plan]"
    assert "DIVIDE([OTIF %] - [OTIF % Plan], [OTIF % Plan])" == d["variance_pct"].dax


def test_numeric_target_becomes_literal():
    d = _by_role(variance_measures("OEE %", 85.0, "higher_is_better"))
    assert "85.0" in d["variance"].dax


def test_status_direction_higher_is_better():
    d = _by_role(variance_measures("OTIF %", "[OTIF % Plan]", "higher_is_better"))
    # good when actual >= target
    assert "[OTIF %] >= [OTIF % Plan]" in d["status"].dax
    assert d["status_color"].dax.startswith('IF([OTIF %] >= [OTIF % Plan], "#107C10"')


def test_status_direction_lower_is_better_flips():
    d = _by_role(variance_measures("Attrition %", "[Attrition % Target]", "lower_is_better"))
    # good when actual <= target (flipped)
    assert "[Attrition %] <= [Attrition % Target]" in d["status"].dax
    # bad branch is the governed negative hex
    assert d["status_color"].dax.rstrip().endswith('"#A4262C"))')


def test_title_measure_is_context_safe_string_measure():
    td = title_measure("EBITDA Margin %", "[EBITDA Margin % Plan]", "higher_is_better", fmt="0.0%")
    assert td is not None and td.role == "title"
    # references only scalar aggregates ([KPI] and its Δ) — no axis/Top-N dependency
    assert "[EBITDA Margin %]" in td.dax and "[EBITDA Margin % Δ vs Target]" in td.dax
    assert td.dax.startswith("FORMAT(")           # returns a string
    assert 'vs Plan"' in td.dax


def test_title_measure_none_without_target_or_direction():
    assert title_measure("X", None, "higher_is_better") is None
    assert title_measure("X", "[X Plan]", None) is None


def test_semantic_colors_are_governed_tokens():
    d = _by_role(variance_measures("OTIF %", 95.0, "higher_is_better",
                                   colors={"positive": "#0A0", "warning": "#0B0", "negative": "#0C0"}))
    assert '"#0A0"' in d["status_color"].dax and '"#0C0"' in d["status_color"].dax
