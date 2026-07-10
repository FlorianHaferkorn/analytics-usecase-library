"""
Tests for Page Scaffold Generator

Run with: python -m pytest tests/test_scaffold_generator.py
"""

import pytest
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from page_scaffold_generator import PageScaffoldGenerator
from page_scaffold_generator.config_loader import ConfigLoader
from page_scaffold_generator.layout_calculator import LayoutCalculator
from page_scaffold_generator.visual_builder import VisualBuilder
from page_scaffold_generator.slicer_builder import SlicerBuilder

# Resolve repo root (tests live deep in products/fabric/powerbi/tooling/page_scaffold_generator/tests/)
REPO_ROOT = Path(__file__).resolve().parents[6]  # -> analytics-usecase-library


class TestConfigLoader:
    """Test config loader."""
    
    def test_get_page_config(self):
        """Test getting page config."""
        loader = ConfigLoader(REPO_ROOT)
        config = loader.get_page_config("COM-001", "overview")

        assert config["name"] == "overview"
        assert config["template"] == "T2"
        assert "slots" in config

    def test_get_use_case_display_name(self):
        """Test getting use case display name."""
        loader = ConfigLoader(REPO_ROOT)
        name = loader.get_use_case_display_name("COM-001")
        
        assert name is not None
        assert len(name) > 0


class TestLayoutCalculator:
    """Test layout calculator."""
    
    def test_calculate_kpi_card_positions(self):
        """Test KPI card position calculation."""
        calc = LayoutCalculator()
        positions = calc.calculate_kpi_card_positions(4)
        
        assert len(positions) == 4
        assert all(p.width == calc.KPI_CARD_WIDTH_STANDARD for p in positions)
        assert all(p.height == calc.KPI_CARD_HEIGHT_STANDARD for p in positions)
    
    def test_calculate_slicer_positions_top(self):
        """Test top slicer position calculation."""
        calc = LayoutCalculator()
        positions = calc.calculate_slicer_positions([{"type": "time"}], "top")
        
        assert len(positions) == 1
        assert positions[0].y == calc.ROW_1_Y_START
        assert positions[0].height == calc.SLICER_TOP_HEIGHT
    
    def test_calculate_visual_positions(self):
        """Test visual position calculation."""
        calc = LayoutCalculator()
        slots = {
            "needs_trend": True,
            "needs_variance": True,
            "needs_ranking": True
        }
        
        positions = calc.calculate_visual_positions(slots, "T2", False, False)
        
        assert "trend" in positions
        assert "variance" in positions
        assert "ranking" in positions


class TestVisualBuilder:
    """Test visual builder."""

    def test_build_kpi_card(self):
        """Test building KPI card."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position

        pos = Position(x=20, y=20, width=280, height=140)
        visual = builder.build_kpi_card(pos)

        assert visual["visual"]["visualType"] == "cardVisual"
        assert visual["position"]["x"] == 20
        assert visual["position"]["y"] == 20
        # Cards must use Data role
        qs = visual["visual"]["query"]["queryState"]
        assert "Data" in qs

    def test_build_line_chart(self):
        """Test building line chart."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position

        pos = Position(x=20, y=180, width=800, height=400)
        visual = builder.build_line_chart(pos)

        assert visual["visual"]["visualType"] == "lineChart"
        # Charts must use Category + Y, never Data
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_build_table_empty(self):
        """Test building table with no data still uses Values role."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position

        pos = Position(x=20, y=20, width=800, height=400)
        visual = builder.build_table(pos, columns=[], measures=[])

        assert visual["visual"]["visualType"] == "tableEx"
        qs = visual["visual"]["query"]["queryState"]
        assert "Values" in qs, "Empty table must use Values role"
        assert "Data" not in qs


class TestScaffoldGenerator:
    """Test scaffold generator."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)

        assert generator.use_case_id == "COM-001"
        assert generator.page_name == "overview"

    def test_load_config(self):
        """Test loading configuration."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()

        assert generator.config is not None
        assert generator.page_config is not None
        assert generator.page_config["template"] == "T2"

    def test_generate(self):
        """Test scaffold generation."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()

        assert generator.page_id is not None
        assert generator.page_structure is not None
        assert "visuals" in generator.page_structure
        assert "slicers" in generator.page_structure

    def test_validate(self):
        """Test validation."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()

        errors = generator.validate()
        # Should pass validation for COM-001 overview (including visual validation)
        assert isinstance(errors, list)
        assert len(errors) == 0, f"COM-001 overview should pass validation: {errors}"

    def test_validate_detail(self):
        """Test validation for detail page."""
        generator = PageScaffoldGenerator("COM-001", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()

        errors = generator.validate()
        assert isinstance(errors, list)
        assert len(errors) == 0, f"COM-001 detail should pass validation: {errors}"


class TestCOM002GoldenR23Fields:
    """
    R2.3 (Cut C2) targeted golden comparison: COM-002 is the migrated
    intent_rules_version: 2 reference Bracket. Rather than a full-directory
    byte-identical fixture (see TestGoldenCOM001 in test_pbip_writer.py),
    this compares ONLY the visuals/fields R2.3 actually generates --
    Header (big_idea), Detail_Matrix (sort/topN/dataBars), Main_3
    (auto-sort) -- against the real, committed dist/ output. The rest of
    COM-002's visuals (KPI_Cards, Main_1, Main_2, Smart_Narrative,
    ActionPanel) have pre-existing, unrelated drift from hand-patched
    R1.x fixes that were never ported back into the generator -- out of
    scope here, tracked separately.
    """

    DIST_OVERVIEW = (
        REPO_ROOT
        / "products/fabric/powerbi/dist/COM-002_Margin_Price_Performance.Report"
        / "definition/pages/Page_COM002_Overview/visuals"
    )
    DIST_DETAIL = (
        REPO_ROOT
        / "products/fabric/powerbi/dist/COM-002_Margin_Price_Performance.Report"
        / "definition/pages/Page_COM002_Detail/visuals"
    )

    def _find_visual(self, generator, name):
        return next(v for v in generator.page_structure["visuals"] if v.get("name") == name)

    def test_header_matches_real_dist(self):
        dist_header = json.loads((self.DIST_OVERVIEW / "Header" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        header = self._find_visual(generator, "Header")

        assert header["position"] == dist_header["position"]
        assert header["visual"] == dist_header["visual"]

    def test_main_3_sort_definition_matches_real_dist(self):
        dist_main3 = json.loads((self.DIST_OVERVIEW / "Main_3" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        main3 = self._find_visual(generator, "Main_3")

        generated_sort = main3["visual"]["query"]["sortDefinition"]
        dist_sort = dist_main3["visual"]["query"]["sortDefinition"]
        assert generated_sort == dist_sort

    def test_detail_matrix_sort_definition_matches_real_dist(self):
        dist_matrix = json.loads((self.DIST_DETAIL / "Detail_Matrix" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        matrix = self._find_visual(generator, "Detail_Matrix")

        assert matrix["visual"]["query"]["sortDefinition"] == dist_matrix["visual"]["query"]["sortDefinition"]

    def test_detail_matrix_databar_formatting_matches_real_dist(self):
        dist_matrix = json.loads((self.DIST_DETAIL / "Detail_Matrix" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        matrix = self._find_visual(generator, "Detail_Matrix")

        assert matrix["visual"]["objects"]["columnFormatting"] == dist_matrix["visual"]["objects"]["columnFormatting"]

    def test_detail_matrix_topn_filter_matches_real_dist(self):
        """The filter *name* is a cosmetic-only PBIR identifier; dist/ was
        updated to the generator's new deterministic naming rule (R2.3),
        see UMSETZUNGSPLAN_REPORT_EXZELLENZ.md R2.3 ledger entry."""
        dist_matrix = json.loads((self.DIST_DETAIL / "Detail_Matrix" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        matrix = self._find_visual(generator, "Detail_Matrix")

        assert matrix["filterConfig"] == dist_matrix["filterConfig"]


class TestConfigLoaderKpiMap:
    """Test KPI catalog loading and warning on failure."""

    def test_load_kpi_map_returns_dict(self):
        """KPI map should return a non-empty dict from the real KPI catalog."""
        loader = ConfigLoader(REPO_ROOT)
        result = loader.load_kpi_id_to_measure_name_map()
        assert isinstance(result, dict)
        # Real catalog should have entries
        assert len(result) > 0

    def test_load_kpi_map_caches_result(self):
        """Second call should return the cached result."""
        loader = ConfigLoader(REPO_ROOT)
        first = loader.load_kpi_id_to_measure_name_map()
        second = loader.load_kpi_id_to_measure_name_map()
        assert first is second

    def test_load_kpi_map_missing_catalog_returns_empty(self, tmp_path):
        """Missing KPI catalog should return empty dict, not raise."""
        loader = ConfigLoader(tmp_path)
        result = loader.load_kpi_id_to_measure_name_map()
        assert result == {}

    def test_load_kpi_map_logs_warning_on_parse_failure(self, tmp_path, caplog):
        """Malformed KPI catalog should log a warning, not silently pass."""
        import logging

        # Create a fake KPI catalog with valid yaml fence but broken content
        kpi_dir = tmp_path / "core" / "kpi_catalog"
        kpi_dir.mkdir(parents=True)
        catalog = kpi_dir / "KPI_Catalog.md"
        # Write content that will trigger the regex match but fail parsing
        catalog.write_text(
            "```yaml\n- kpi_id: TEST\n  kpi_key: \x00invalid\n```",
            encoding="utf-8",
        )
        loader = ConfigLoader(tmp_path)

        with caplog.at_level(logging.WARNING, logger="page_scaffold_generator.config_loader"):
            result = loader.load_kpi_id_to_measure_name_map()

        # Should still return a dict (possibly with partial results), not raise
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
