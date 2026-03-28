"""Tests for the CSS grid layout calculator."""

import pytest
from page_generator.layout_calculator import LayoutCalculator, GridSlot


@pytest.fixture
def calc():
    return LayoutCalculator(columns=12, rows=12)


class TestGridSlot:
    def test_css_grid_area(self):
        slot = GridSlot("kpi_cards", col_start=1, row_start=1, col_span=12, row_span=2)
        assert slot.css_grid_area == "1 / 1 / 3 / 13"

    def test_tailwind_classes(self):
        slot = GridSlot("trend", col_start=1, row_start=3, col_span=8, row_span=4)
        assert "col-start-1" in slot.tailwind_classes
        assert "col-span-8" in slot.tailwind_classes
        assert "row-start-3" in slot.tailwind_classes
        assert "row-span-4" in slot.tailwind_classes


class TestParseSlots:
    def test_parse_valid_blueprint(self, calc):
        blueprint = {
            "slots": [
                {"slot_id": "kpi_row", "grid": [1, 1, 12, 2]},
                {"slot_id": "trend", "grid": [1, 3, 8, 4]},
                {"slot_id": "slicer", "grid": [9, 3, 4, 4]},
            ]
        }
        slots = calc.parse_slots(blueprint)
        assert len(slots) == 3
        assert slots[0].slot_id == "kpi_row"
        assert slots[1].col_span == 8

    def test_skip_invalid_grid(self, calc):
        blueprint = {"slots": [{"slot_id": "bad", "grid": [1, 2]}]}
        slots = calc.parse_slots(blueprint)
        assert len(slots) == 0

    def test_empty_blueprint(self, calc):
        slots = calc.parse_slots({})
        assert slots == []


class TestValidateSlots:
    def test_valid_slots_no_errors(self, calc):
        slots = [
            GridSlot("a", 1, 1, 6, 6),
            GridSlot("b", 7, 1, 6, 6),
        ]
        errors = calc.validate_slots(slots)
        assert errors == []

    def test_exceeds_columns(self, calc):
        slots = [GridSlot("wide", 1, 1, 13, 1)]
        errors = calc.validate_slots(slots)
        assert any("exceeds 12 columns" in e for e in errors)

    def test_exceeds_rows(self, calc):
        slots = [GridSlot("tall", 1, 1, 1, 13)]
        errors = calc.validate_slots(slots)
        assert any("exceeds 12 rows" in e for e in errors)

    def test_overlap_detected(self, calc):
        slots = [
            GridSlot("a", 1, 1, 6, 6),
            GridSlot("b", 3, 3, 6, 6),  # overlaps with a
        ]
        errors = calc.validate_slots(slots)
        assert any("overlaps" in e for e in errors)

    def test_position_must_be_positive(self, calc):
        slots = [GridSlot("neg", 0, 1, 1, 1)]
        errors = calc.validate_slots(slots)
        assert any(">= 1" in e for e in errors)


class TestGenerateHtml:
    def test_grid_container_css(self, calc):
        css = calc.generate_grid_container_css()
        assert "grid-template-columns: repeat(12, 1fr)" in css

    def test_evidence_grid_html(self, calc):
        slots = [GridSlot("header", 1, 1, 12, 1)]
        html = calc.generate_evidence_grid_html(slots, {"header": "<BigValue />"})
        assert "grid-area: 1 / 1 / 2 / 13" in html
        assert "<BigValue />" in html
