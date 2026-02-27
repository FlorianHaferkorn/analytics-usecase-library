"""
Tests for Grid Calculator (Master Grid 12×12)

Run with: python -m pytest tests/test_grid_calculator.py -v
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from page_scaffold_generator.grid_calculator import (
    GridCalculator,
    GridPosition,
    calculate_visual_rect,
)


class TestGridCalculator:
    """Test GridCalculator with 1920×1080, 32px margin, 16px gutter."""

    def test_default_canvas_and_lu(self):
        calc = GridCalculator(canvas_width=1920, canvas_height=1080, outer_margin=32, gutter=16)
        w, h = calc.get_canvas_size()
        assert w == 1920
        assert h == 1080
        lu_w, lu_h = calc.get_lu_size()
        # Content: 1920-64=1856, 1080-64=1016. LU: (1856-176)/12 = 140, (1016-176)/12 = 70
        assert 139 <= lu_w <= 141
        assert 69 <= lu_h <= 71

    def test_calculate_visual_rect_single_cell(self):
        calc = GridCalculator(canvas_width=1920, canvas_height=1080, outer_margin=32, gutter=16)
        pos = calc.calculate_visual_rect(0, 0, 1, 1)
        assert isinstance(pos, GridPosition)
        assert pos.x == 32
        assert pos.y == 32
        assert pos.width == round(calc._lu_width)
        assert pos.height == round(calc._lu_height)

    def test_calculate_visual_rect_aligned_integers(self):
        calc = GridCalculator(canvas_width=1920, canvas_height=1080, outer_margin=32, gutter=16)
        pos = calc.calculate_visual_rect(2, 3, 4, 2)
        assert pos.x == int(pos.x)
        assert pos.y == int(pos.y)
        assert pos.width == int(pos.width)
        assert pos.height == int(pos.height)
        assert pos.x >= 32
        assert pos.y >= 32
        assert pos.width > 0
        assert pos.height > 0

    def test_calculate_visual_rect_full_grid(self):
        calc = GridCalculator(canvas_width=1920, canvas_height=1080, outer_margin=32, gutter=16)
        pos = calc.calculate_visual_rect(0, 0, 12, 12)
        assert pos.x == 32
        assert pos.y == 32
        assert pos.width == 1920 - 64  # content width
        assert pos.height == 1080 - 64  # content height

    def test_set_canvas_scaling(self):
        calc = GridCalculator(canvas_width=1920, canvas_height=1080, outer_margin=32, gutter=16)
        pos1 = calc.calculate_visual_rect(0, 0, 2, 2)
        calc.set_canvas(1280, 720)
        pos2 = calc.calculate_visual_rect(0, 0, 2, 2)
        assert pos2.width < pos1.width
        assert pos2.height < pos1.height
        assert pos2.x == 32
        assert pos2.y == 32


class TestCalculateVisualRectStandalone:
    """Test standalone helper."""

    def test_returns_tuple_of_four(self):
        x, y, w, h = calculate_visual_rect(0, 0, 1, 1)
        assert len((x, y, w, h)) == 4
        assert x == 32
        assert y == 32
        assert w > 0
        assert h > 0

    def test_32px_margin_16px_gutter(self):
        x, y, w, h = calculate_visual_rect(0, 0, 12, 12, outer_margin=32, gutter=16)
        assert x == 32
        assert y == 32
        assert w == 1856
        assert h == 1016
