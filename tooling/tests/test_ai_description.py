"""Tests for the standard AI-description renderer (catalog -> semantic layer + viz).

Proven against Aurora COM-001 / margin.gm.pct.
"""

from __future__ import annotations

from pathlib import Path

from generator_core.ai_description import AIDescription, build_description


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_aurora_margin_gm_pct_renders_optimal_depth():
    d = build_description("margin.gm.pct", _repo_root())
    assert d is not None
    assert d.name == "Gross Margin %"
    # Pulled from the measure dictionary + data contract + catalog.
    assert "Net Sales Amount" in d.formula
    assert d.unit == "%"
    assert d.grain  # grain present
    assert d.good_is == "higher"
    assert d.owner and d.status == "active"
    assert d.action_codes  # action codes from the catalog
    assert d.drivers  # causal drivers from causal_links

    sl = d.render_semantic_layer()
    assert sl.splitlines()[0].startswith("/// ")
    assert "Formula:" in sl
    assert "Drivers:" in sl
    assert "higher_is_better" in sl
    assert "Owner:" in sl

    viz = d.render_viz()
    assert "higher is better" in viz
    assert "Top drivers:" in viz


def test_render_omits_missing_facets():
    d = AIDescription(kpi_id="x.y", name="X", definition="A thing.")
    assert d.render_semantic_layer() == "/// A thing."
    assert "Formula" not in d.render_semantic_layer()
    assert "Owner" not in d.render_semantic_layer()
    assert d.render_viz() == "A thing."


def test_unknown_kpi_returns_none():
    assert build_description("nonexistent.kpi.id", _repo_root()) is None


def test_loaders_are_best_effort(tmp_path: Path):
    from generator_core.ai_description import (
        load_fact_grains,
        load_kpi_catalog,
        load_measure_dictionary,
    )

    assert load_kpi_catalog(tmp_path / "missing.md") == {}
    assert load_measure_dictionary(tmp_path / "missing") == {}
    assert load_fact_grains(tmp_path / "missing") == {}
