"""Tests for the Report-Documenter Layer-Tool (task I-5.2).

DoD: a deterministic Doc-Gen snapshot (a checked-in golden Markdown that turns
red if the branded layout drifts) + standalone generation against the bare stack.
"""
from __future__ import annotations

from pathlib import Path

from tooling.superversion.canonical_contract import (
    CanonicalModel,
    Measure,
    ReportModel,
    ReportPage,
    Role,
    RoleTablePermission,
    SemanticModel,
    Table,
    Visual,
)
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import report_documenter as doc

REPO = Path(__file__).resolve().parents[3]
KPIS = REPO / "core/kpi_catalog/kpis"
COM001 = REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml"
GOLDEN = Path(__file__).resolve().parent / "golden_docs" / "COM-001.md"


def _com001():
    return from_bracket_file(COM001, KPIS)


def test_matches_golden_snapshot():
    """Regression snapshot: branded layout drift turns this red.
    Regenerate via: python -m tooling.superversion.layer_tools.report_documenter \\
        --out tooling/superversion/tests/golden_docs/COM-001.md"""
    md = doc.render_markdown(_com001())
    assert md == GOLDEN.read_text(encoding="utf-8"), "doc drifted from golden — regenerate if intended"


def test_deterministic():
    m = _com001()
    assert doc.render_markdown(m) == doc.render_markdown(m)


def test_has_business_and_technical_sections():
    md = doc.render_markdown(_com001())
    for marker in ("# COM-001", "## Business", "### KPIs & Meaning",
                   "## Technical", "### Measures (DAX dialect / HITL)", "### Row-Level Security"):
        assert marker in md, f"missing section: {marker}"


def test_branding_title_block():
    md = doc.render_markdown(_com001(), branding=doc.Branding(product_name="ACME BI", tagline="x"))
    assert "**ACME BI**" in md


def test_lists_every_page_and_measure():
    m = _com001()
    md = doc.render_markdown(m)
    for p in m.report.pages:
        assert (p.display_name or p.name) in md
    for t in m.semantic.tables:
        for measure in t.measures:
            assert measure.name in md


def test_rls_section_reflects_real_filter():
    m = CanonicalModel(
        semantic=SemanticModel(name="S", tables=[Table(name="f", measures=[Measure(name="M")])],
                               roles=[Role(name="org",
                                           table_permissions=[RoleTablePermission(
                                               table="f", filter_expression="[R]=1")])]),
        report=ReportModel(name="R", pages=[ReportPage(name="P", visuals=[Visual(visual_id="v", visual_type="card")])]),
    )
    md = doc.render_markdown(m)
    assert "**org**" in md and "[R]=1" in md


def test_hitl_dax_placeholder_shown():
    md = doc.render_markdown(_com001())
    assert "HITL: DAX dialect to be defined" in md


def test_cli_writes_file(tmp_path: Path):
    out = tmp_path / "doc.md"
    assert doc.main([str(COM001), "--out", str(out)]) == 0
    assert out.exists() and out.read_text(encoding="utf-8").startswith("# COM-001")


def test_cli_missing_bracket_returns_one():
    assert doc.main([str(REPO / "nope.yaml")]) == 1
