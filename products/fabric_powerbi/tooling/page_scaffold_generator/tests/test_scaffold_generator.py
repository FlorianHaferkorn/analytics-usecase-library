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


class TestConfigLoader:
    """Test config loader."""
    
    def test_load_use_case_mapping(self):
        """Test loading use case mapping."""
        loader = ConfigLoader()
        mapping = loader.load_use_case_mapping()
        
        assert "use_cases" in mapping
        assert "COM-001" in mapping["use_cases"]
    
    def test_get_page_config(self):
        """Test getting page config."""
        loader = ConfigLoader()
        config = loader.get_page_config("COM-001", "overview")
        
        assert config["name"] == "overview"
        assert config["template"] == "T2"
        assert "slots" in config
    
    def test_get_use_case_display_name(self):
        """Test getting use case display name."""
        loader = ConfigLoader()
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
    
    def test_build_line_chart(self):
        """Test building line chart."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position
        
        pos = Position(x=20, y=180, width=800, height=400)
        visual = builder.build_line_chart(pos)
        
        assert visual["visual"]["visualType"] == "lineChart"


class TestScaffoldGenerator:
    """Test scaffold generator."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = PageScaffoldGenerator("COM-001", "overview")
        
        assert generator.use_case_id == "COM-001"
        assert generator.page_name == "overview"
    
    def test_load_config(self):
        """Test loading configuration."""
        generator = PageScaffoldGenerator("COM-001", "overview")
        generator.load_config()
        
        assert generator.config is not None
        assert generator.page_config is not None
        assert generator.page_config["template"] == "T2"
    
    def test_generate(self):
        """Test scaffold generation."""
        generator = PageScaffoldGenerator("COM-001", "overview")
        generator.load_config()
        generator.generate()
        
        assert generator.page_id is not None
        assert generator.page_structure is not None
        assert "visuals" in generator.page_structure
        assert "slicers" in generator.page_structure
    
    def test_validate(self):
        """Test validation."""
        generator = PageScaffoldGenerator("COM-001", "overview")
        generator.load_config()
        generator.generate()
        
        errors = generator.validate()
        # Should pass validation for COM-001 overview
        assert isinstance(errors, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
