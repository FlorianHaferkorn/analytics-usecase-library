"""Tests for the main Evidence page generator orchestrator."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from page_generator.generator import EvidencePageGenerator


@pytest.fixture
def sample_ir(tmp_path):
    """Create a minimal IR for testing."""
    ir = {
        "meta": {"version": "1.0", "generated": "2026-03-28T00:00:00Z"},
        "nodes": [
            {
                "id": "COM-001",
                "type": "use_case",
                "label": "Sales Performance",
            },
            {
                "id": "KPI-COM-001",
                "type": "kpi",
                "label": "Net Sales",
                "domain": "Commercial",
                "measure_spec": {
                    "dax_expression": "SUM(fact_sales[net_sales_amount])",
                    "formatString": "#,##0",
                },
            },
            {
                "id": "KPI-COM-002",
                "type": "kpi",
                "label": "Gross Margin",
                "domain": "Commercial",
                "measure_spec": {
                    "dax_expression": "DIVIDE(SUM(fact_sales[profit]), SUM(fact_sales[revenue]))",
                    "formatString": "0.0%",
                },
            },
        ],
        "edges": [
            {"source": "COM-001", "target": "KPI-COM-001", "target_type": "kpi", "relation": "strategic_kpi"},
            {"source": "COM-001", "target": "KPI-COM-002", "target_type": "kpi", "relation": "influencing_kpi"},
        ],
    }
    ir_path = tmp_path / "ir_v1.json"
    ir_path.write_text(json.dumps(ir), encoding="utf-8")
    return ir_path


@pytest.fixture
def sample_bracket(tmp_path):
    """Create a minimal UseCase_Bracket.yaml for testing."""
    bracket_content = """\
schema_version: "2.0"
use_case_id: COM-001
ux_layout:
  report_pages:
    - page_id: overview
      page_type: overview
    - page_id: detail
      page_type: detail
"""
    # Create the bracket in the expected location
    uc_dir = tmp_path / "core" / "usecases" / "core" / "COM-001_Sales_Performance"
    uc_dir.mkdir(parents=True)
    bracket_file = uc_dir / "UseCase_Bracket.yaml"
    bracket_file.write_text(bracket_content, encoding="utf-8")
    return tmp_path


@pytest.fixture
def generator(sample_ir, sample_bracket, tmp_path):
    """Create a configured generator with test data."""
    output_dir = tmp_path / "output"
    gen = EvidencePageGenerator(
        use_case_id="COM-001",
        ir_path=sample_ir,
        repo_root=sample_bracket,
        output_dir=output_dir,
    )
    return gen


class TestEvidencePageGenerator:
    def test_load_ir_and_bracket(self, generator):
        generator.load()
        assert generator._ir is not None
        assert generator._bracket is not None
        assert generator._bracket["use_case_id"] == "COM-001"

    def test_generate_creates_pages(self, generator):
        generator.load()
        pages = generator.generate()
        assert len(pages) == 2  # overview + detail
        assert all(p.exists() for p in pages)

    def test_overview_page_has_kpis(self, generator):
        generator.load()
        pages = generator.generate()
        overview = [p for p in pages if "overview" in p.name][0]
        content = overview.read_text()
        assert "# Sales Performance" in content
        assert "Net Sales" in content
        assert "```sql" in content
        assert "<BigValue" in content

    def test_detail_page_has_diagnostics(self, generator):
        generator.load()
        pages = generator.generate()
        detail = [p for p in pages if "detail" in p.name][0]
        content = detail.read_text()
        assert "300-Second Layer" in content
        assert "<DataTable" in content

    def test_page_has_frontmatter(self, generator):
        generator.load()
        pages = generator.generate()
        content = pages[0].read_text()
        assert "---" in content
        assert "use_case: COM-001" in content
        assert "generated: true" in content

    def test_page_has_trend_section(self, generator):
        generator.load()
        pages = generator.generate()
        overview = [p for p in pages if "overview" in p.name][0]
        content = overview.read_text()
        assert "30-Second Layer" in content
        assert "<LineChart" in content

    def test_filenames_follow_convention(self, generator):
        generator.load()
        pages = generator.generate()
        names = [p.name for p in pages]
        assert "com_001_overview.md" in names
        assert "com_001_detail.md" in names


class TestGeneratorFallback:
    def test_no_report_pages_generates_overview(self, sample_ir, tmp_path):
        """If bracket has no report_pages, generate a single overview."""
        bracket_content = """\
schema_version: "2.0"
use_case_id: COM-001
ux_layout: {}
"""
        uc_dir = tmp_path / "core" / "usecases" / "core" / "COM-001_Sales_Performance"
        uc_dir.mkdir(parents=True)
        (uc_dir / "UseCase_Bracket.yaml").write_text(bracket_content)

        gen = EvidencePageGenerator(
            use_case_id="COM-001",
            ir_path=sample_ir,
            repo_root=tmp_path,
            output_dir=tmp_path / "out",
        )
        gen.load()
        pages = gen.generate()
        assert len(pages) == 1
        assert "overview" in pages[0].name
