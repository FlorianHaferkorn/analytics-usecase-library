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
    # B1: the optional few-shot grounding question is projected when present
    assert d.example_question
    assert f"/// Example question: {d.example_question}" in sl

    viz = d.render_viz()
    assert "higher is better" in viz
    assert "Top drivers:" in viz


def test_render_omits_missing_facets():
    d = AIDescription(kpi_id="x.y", name="X", definition="A thing.")
    assert d.render_semantic_layer() == "/// A thing."
    assert "Formula" not in d.render_semantic_layer()
    assert "Owner" not in d.render_semantic_layer()
    assert "Example question" not in d.render_semantic_layer()  # B1: omitted, never guessed
    assert d.render_viz() == "A thing."


def test_synonyms_render_when_present():
    d = AIDescription(kpi_id="x.y", name="X", definition="A thing.",
                      synonyms=["Alpha", "Beta", "Gamma"])
    sl = d.render_semantic_layer()
    assert "/// Synonyms: Alpha, Beta, Gamma" in sl
    # omitted when absent (never guessed)
    assert "Synonyms" not in AIDescription(kpi_id="x.y", name="X", definition="A thing.").render_semantic_layer()


def test_example_question_renders_as_last_facet():
    d = AIDescription(
        kpi_id="x.y", name="X", definition="A thing.",
        example_question="How did X move last quarter?",
    )
    lines = d.render_semantic_layer().splitlines()
    assert lines[0] == "/// A thing."
    assert lines[-1] == "/// Example question: How did X move last quarter?"


def test_unknown_kpi_returns_none():
    assert build_description("nonexistent.kpi.id", _repo_root()) is None


def test_loaders_are_best_effort(tmp_path: Path):
    from generator_core.ai_description import (
        build_table_descriptions,
        load_fact_grains,
        load_kpi_catalog,
        load_measure_dictionary,
    )

    assert load_kpi_catalog(tmp_path / "missing.md") == {}
    assert load_measure_dictionary(tmp_path / "missing") == {}
    assert load_fact_grains(tmp_path / "missing") == {}
    assert build_table_descriptions(tmp_path / "missing.yaml") == []


def test_aurora_tables_and_columns_render_with_context():
    from generator_core.ai_description import build_table_descriptions

    contract = _repo_root() / "core" / "data_contracts" / "domains" / "commercial_sales.yaml"
    by = {t.name: t for t in build_table_descriptions(contract)}
    assert "fact_sales" in by and "dim_org" in by

    fs = by["fact_sales"]
    assert fs.kind == "fact" and fs.grain == "invoice_line"
    assert fs.render_semantic_layer().startswith("/// ")
    # foreign-key column resolves its target
    org_fk = next(c for c in fs.columns if c.name == "OrgKey")
    assert org_fk.role == "foreign_key" and org_fk.ref == "dim_org"
    # currency measure column carries a unit
    ns = next(c for c in fs.columns if c.name == "Net Sales Amount")
    assert ns.role == "measure" and ns.unit == "EUR"

    # categorical column carries allowed values + synonyms (the NL->column lever)
    region = next(c for c in by["dim_org"].columns if c.name == "Region")
    assert "DACH" in region.allowed_values
    sl = region.render_semantic_layer()
    assert "Values:" in sl and "Synonyms:" in sl


def test_column_render_omits_missing_facets():
    from generator_core.ai_description import ColumnDescription

    c = ColumnDescription(name="Foo", data_type="text")
    rendered = c.render_semantic_layer()
    assert rendered == "/// Foo. Type: text"
    assert "Values:" not in rendered and "FK->" not in rendered


def test_generator_emits_standard_doc_block_for_catalog_kpi():
    """The TMDL measure writer projects the standard /// block from the catalog."""
    from products.fabric.powerbi.tooling.adapters.pbip import _build_tmdl_measures
    from generator_core.ir.specs import MeasureSpec

    m = MeasureSpec(
        kpi_id="margin.gm.pct",
        name="Gross Margin %",
        dax="DIVIDE([Gross Margin Amount],[Net Sales Amount])",
        format_string="0.0%",
        display_folder="02_Margin",
    )
    tmdl = _build_tmdl_measures([m])
    assert "/// Formula:" in tmdl
    assert "Drivers:" in tmdl
    assert "Owner:" in tmdl
    assert "/// Purpose:" not in tmdl  # the standard block supersedes the bland Purpose line


def test_generator_falls_back_to_purpose_for_unknown_kpi():
    from products.fabric.powerbi.tooling.adapters.pbip import _build_tmdl_measures
    from generator_core.ir.specs import MeasureSpec

    m = MeasureSpec(kpi_id="x.y.z", name="Alpha", dax="0", format_string="#,0", description="Tracks alpha")
    tmdl = _build_tmdl_measures([m])
    assert "/// Purpose: Tracks alpha" in tmdl


_SAMPLE_TMDL = (
    "table _Measures\n"
    "\t/// stale hand-written comment\n"
    "\tmeasure 'Gross Margin %' = DIVIDE ( [a], [b] )\n"
    '\t\tformatString: "0.0%"\n'
    "\t/// Purpose: A bespoke non-catalog helper\n"
    "\tmeasure 'Some Bespoke Helper' = 1\n"
    '\t\tformatString: "#,0"\n'
)


def test_enricher_projects_standard_and_preserves_non_catalog():
    from generator.enrich_measure_docs import enrich_text

    out = enrich_text(_SAMPLE_TMDL, _repo_root())
    # the catalog KPI gets the rendered standard block; its stale doc is gone
    assert "/// Formula:" in out
    # B1: the enricher delegates to the standard renderer, so example_question flows through
    assert "/// Example question:" in out
    assert "/// stale hand-written comment" not in out
    # the non-catalog measure keeps its existing doc untouched
    assert "/// Purpose: A bespoke non-catalog helper" in out
    # measure lines + formatString are preserved verbatim
    assert "measure 'Gross Margin %' = DIVIDE ( [a], [b] )" in out
    assert "measure 'Some Bespoke Helper' = 1" in out


def test_enricher_is_idempotent():
    from generator.enrich_measure_docs import enrich_text

    once = enrich_text(_SAMPLE_TMDL, _repo_root())
    assert enrich_text(once, _repo_root()) == once
