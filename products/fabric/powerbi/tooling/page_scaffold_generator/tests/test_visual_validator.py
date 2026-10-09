"""
Tests for Visual Validator

Ensures the self-validation catches common report generation errors
(wrong queryState roles, unsafe names, out-of-bounds positions).

Run with: python -m pytest tests/test_visual_validator.py -v
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from page_scaffold_generator.visual_validator import validate_visual, validate_page, validate_slot_compliance
from page_scaffold_generator.visual_builder import VisualBuilder
from page_scaffold_generator.layout_calculator import Position


@pytest.fixture
def builder():
    return VisualBuilder()


@pytest.fixture
def pos():
    return Position(x=20, y=20, width=400, height=300)


class TestQueryStateRoles:
    """Verify that each visual type uses the correct queryState roles."""

    def test_table_uses_values_role(self, builder, pos):
        visual = builder.build_table(pos, columns=[], measures=[])
        qs = visual["visual"]["query"]["queryState"]
        assert "Values" in qs, f"tableEx should use 'Values' role, got: {list(qs.keys())}"
        assert "Data" not in qs, "tableEx must NOT use 'Data' role"

    def test_table_with_data_uses_values_role(self, builder, pos):
        visual = builder.build_table(
            pos, columns=[("dim_date", "Date")], measures=["Net Sales Amount"]
        )
        qs = visual["visual"]["query"]["queryState"]
        assert "Values" in qs
        assert len(qs["Values"]["projections"]) == 2

    def test_line_chart_uses_category_y(self, builder, pos):
        visual = builder.build_line_chart(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs, f"lineChart should use 'Category' role, got: {list(qs.keys())}"
        assert "Y" in qs, f"lineChart should use 'Y' role, got: {list(qs.keys())}"
        assert "Data" not in qs

    def test_line_chart_with_measures(self, builder, pos):
        visual = builder.build_line_chart(pos, measures=["Net Sales Amount"])
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert len(qs["Y"]["projections"]) == 1

    def test_waterfall_uses_category_y(self, builder, pos):
        visual = builder.build_waterfall(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_bar_chart_uses_category_y(self, builder, pos):
        visual = builder.build_horizontal_bar(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_stacked_bar_uses_category_y(self, builder, pos):
        visual = builder.build_stacked_bar(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_scatter_uses_x_y(self, builder, pos):
        visual = builder.build_scatter_plot(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "X" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_funnel_uses_category_y(self, builder, pos):
        visual = builder.build_funnel(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_matrix_uses_rows_values(self, builder, pos):
        visual = builder.build_matrix(pos)
        qs = visual["visual"]["query"]["queryState"]
        assert "Rows" in qs
        assert "Values" in qs
        assert "Data" not in qs

    def test_kpi_card_uses_data(self, builder, pos):
        visual = builder.build_kpi_card(pos, measure_ref="Net Sales Amount")
        qs = visual["visual"]["query"]["queryState"]
        assert "Data" in qs, "cardVisual should use 'Data' role"

    def test_kpi_cards_multi_uses_data(self, builder, pos):
        visual = builder.build_kpi_cards_multi(pos, ["M1", "M2"])
        qs = visual["visual"]["query"]["queryState"]
        assert "Data" in qs


class TestValidatorDetectsErrors:
    """Verify the validator catches invalid visuals."""

    def test_detects_data_role_on_chart(self):
        """A lineChart with 'Data' role should fail validation."""
        bad_visual = {
            "$schema": "https://example.com/schema.json",
            "name": "BadChart",
            "position": {"x": 0, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {
                "visualType": "lineChart",
                "query": {"queryState": {"Data": {"projections": []}}},
                "objects": {},
            },
        }
        errors = validate_visual(bad_visual)
        assert any("Data" in e and "lineChart" in e for e in errors), f"Should detect Data role on lineChart: {errors}"

    def test_detects_missing_roles(self):
        """A tableEx with no queryState at all should fail."""
        bad_visual = {
            "$schema": "https://example.com/schema.json",
            "name": "BadTable",
            "position": {"x": 0, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {
                "visualType": "tableEx",
                "objects": {},
            },
        }
        errors = validate_visual(bad_visual)
        assert any("Values" in e for e in errors), f"Should detect missing Values role: {errors}"

    def test_accepts_correct_chart(self, builder, pos):
        """A correctly built line chart should pass validation."""
        visual = builder.build_line_chart(pos, measures=["Net Sales Amount"], name="Trend")
        errors = validate_visual(visual)
        assert len(errors) == 0, f"Correct lineChart should pass: {errors}"

    def test_accepts_correct_table(self, builder, pos):
        """A correctly built table should pass validation."""
        visual = builder.build_table(pos, columns=[], measures=[], name="DetailMatrix")
        errors = validate_visual(visual)
        assert len(errors) == 0, f"Correct tableEx should pass: {errors}"

    def test_detects_unsafe_name(self):
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "Net Sales, Delta%",
            "position": {"x": 0, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {"visualType": "textbox", "objects": {}},
        }
        errors = validate_visual(visual)
        assert any("unsafe" in e.lower() for e in errors), f"Should detect comma in name: {errors}"

    def test_detects_hex_id_name(self):
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "a1b2c3d4e5f6a7b8c9d0",
            "position": {"x": 0, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {"visualType": "textbox", "objects": {}},
        }
        errors = validate_visual(visual)
        assert any("hex" in e.lower() for e in errors), f"Should detect hex ID: {errors}"

    def test_detects_out_of_bounds(self):
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "OverflowVisual",
            "position": {"x": 1800, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {"visualType": "textbox", "objects": {}},
        }
        errors = validate_visual(visual, canvas_width=1920, canvas_height=1080)
        assert any("exceeds canvas" in e for e in errors), f"Should detect out-of-bounds: {errors}"

    def test_detects_data_role_on_textbox(self):
        """A textbox carrying a data queryState should fail (PBIR_ROLE_UNKNOWN)."""
        bad_visual = {
            "$schema": "https://example.com/schema.json",
            "name": "ActionPanel",
            "position": {"x": 0, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {
                "visualType": "textbox",
                "query": {"queryState": {"Data": {"projections": []}}},
                "objects": {},
            },
        }
        errors = validate_visual(bad_visual)
        assert any("takes no data roles" in e for e in errors), f"Should reject queryState on textbox: {errors}"

    def test_accepts_textbox_without_query(self):
        """A textbox with no query is valid."""
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "SmartNarrative",
            "position": {"x": 0, "y": 0, "z": 10000, "height": 300, "width": 400, "tabOrder": 3000},
            "visual": {"visualType": "textbox", "objects": {}},
        }
        errors = validate_visual(visual)
        assert not any("takes no data roles" in e for e in errors), f"Plain textbox should pass: {errors}"


class TestValidatePage:
    """Verify page-level validation aggregates visual errors."""

    def test_page_with_correct_visuals(self, builder, pos):
        page = {
            "visuals": [
                builder.build_line_chart(pos, name="Trend"),
                builder.build_table(pos, name="DetailMatrix"),
                builder.build_kpi_card(pos, name="KPI_1"),
            ],
            "slicers": [],
        }
        errors = validate_page(page)
        assert len(errors) == 0, f"All correct visuals should pass: {errors}"


class TestSlotCompliance:
    """Verify slot whitelist enforcement."""

    # Minimal slot mapping covering Main_1 and Main_2 for tests
    SLOT_MAPPING = {
        "slots": {
            "Main_1": {
                "allowed_templates": ["T1", "T2", "T3"],
                "visual_types": {
                    "preferred": "line_chart",
                    "disallowed": ["bar_chart_column", "stacked_bar_100pct", "waterfall",
                                   "scatter_plot", "funnel_chart"],
                },
            },
            "Main_2": {
                "allowed_templates": ["T2"],
                "visual_types": {
                    "preferred": "waterfall",
                    "disallowed": ["line_chart", "area_chart", "funnel_chart",
                                   "kpi_card", "kpi_card_hero"],
                },
            },
            "KPI_Cards": {
                "allowed_templates": ["T1", "T2", "T3", "T4"],
                "visual_types": {
                    "preferred": "kpi_card",
                    "disallowed": ["status_tile"],
                },
            },
        }
    }

    def test_globally_disallowed_type_rejected(self):
        errors = validate_slot_compliance("Main_1", "pieChart")
        assert any("globally disallowed" in e for e in errors), errors

    def test_globally_disallowed_donut_rejected(self):
        errors = validate_slot_compliance("KPI_Cards", "donutChart")
        assert any("globally disallowed" in e for e in errors), errors

    @pytest.mark.parametrize("visual_type,replacement", [
        ("filledMap", "azureMap"),
        ("map", "azureMap"),
        ("qnaVisual", "Copilot"),
        ("card", "cardVisual"),
        ("multiRowCard", "cardVisual"),
    ])
    def test_deprecated_type_rejected_with_replacement(self, visual_type, replacement):
        errors = validate_slot_compliance("Main_1", visual_type)
        assert len(errors) == 1, errors
        assert "globally disallowed" in errors[0] and replacement in errors[0], errors

    @pytest.mark.parametrize("visual_type", ["cardVisual", "azureMap"])
    def test_replacement_type_accepted(self, visual_type):
        assert validate_slot_compliance("Main_1", visual_type) == []

    def test_kpi_card_slot_maps_only_to_card_visual(self):
        from page_scaffold_generator.visual_validator import _ABSTRACT_TO_PBI
        assert _ABSTRACT_TO_PBI["kpi_card"] == {"cardVisual"}

    def test_validate_visual_rejects_legacy_card_without_slot_mapping(self):
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "KPI_1",
            "position": {"x": 0, "y": 0, "z": 0, "height": 100, "width": 200, "tabOrder": 1},
            "visual": {"visualType": "card", "query": {"queryState": {"Data": {}}}},
        }
        errors = validate_visual(visual)
        assert any("globally disallowed" in e and "cardVisual" in e for e in errors), errors

    def test_validate_visual_accepts_azure_map(self):
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "Map_1",
            "position": {"x": 0, "y": 0, "z": 0, "height": 300, "width": 400, "tabOrder": 1},
            "visual": {"visualType": "azureMap", "query": {"queryState": {"Category": {}}}},
        }
        assert validate_visual(visual) == []

    def test_line_chart_allowed_in_main1(self):
        errors = validate_slot_compliance("Main_1", "lineChart", slot_mapping=self.SLOT_MAPPING)
        assert errors == [], errors

    def test_line_chart_disallowed_in_main2(self):
        errors = validate_slot_compliance("Main_2", "lineChart", slot_mapping=self.SLOT_MAPPING)
        assert any("disallowed" in e for e in errors), errors

    def test_waterfall_allowed_in_main2(self):
        errors = validate_slot_compliance("Main_2", "waterfallChart", slot_mapping=self.SLOT_MAPPING)
        assert errors == [], errors

    def test_template_constraint_violated(self):
        # Main_2 only allowed on T2; T1 should fail
        errors = validate_slot_compliance("Main_2", "waterfallChart", template_id="T1",
                                         slot_mapping=self.SLOT_MAPPING)
        assert any("not allowed on template" in e for e in errors), errors

    def test_template_constraint_satisfied(self):
        errors = validate_slot_compliance("Main_2", "waterfallChart", template_id="T2",
                                         slot_mapping=self.SLOT_MAPPING)
        assert errors == [], errors

    def test_unknown_slot_passes(self):
        # Custom / unknown slots should not be blocked
        errors = validate_slot_compliance("CustomSlot", "lineChart", slot_mapping=self.SLOT_MAPPING)
        assert errors == [], errors

    def test_validate_visual_integrates_slot_check(self, builder, pos):
        # A pie chart should be rejected even without slot_mapping
        visual = {
            "$schema": "https://example.com/schema.json",
            "name": "Main_1",
            "position": {"x": 0, "y": 0, "z": 0, "height": 300, "width": 400, "tabOrder": 1},
            "visual": {"visualType": "pieChart", "objects": {}},
        }
        errors = validate_visual(visual, slot_mapping=self.SLOT_MAPPING)
        assert any("globally disallowed" in e for e in errors), errors

    def test_validate_visual_detects_slot_violation(self, builder, pos):
        # lineChart in Main_2 is disallowed
        chart = builder.build_line_chart(pos, name="Main_2")
        errors = validate_visual(chart, slot_mapping=self.SLOT_MAPPING)
        assert any("disallowed" in e for e in errors), errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
