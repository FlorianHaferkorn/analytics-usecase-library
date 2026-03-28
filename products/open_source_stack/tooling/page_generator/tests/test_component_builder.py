"""Tests for the Evidence component builder."""

import pytest
from page_generator.component_builder import ComponentBuilder, COMPONENT_MAP


@pytest.fixture
def builder():
    return ComponentBuilder()


class TestComponentMap:
    """Verify the slot → component mapping is complete."""

    def test_all_slot_types_have_components(self):
        expected_slots = {
            "kpi_card", "kpi_card_delta", "trend_line", "bar_chart",
            "area_chart", "matrix", "data_table", "slicer_dropdown",
            "slicer_button", "smart_narrative", "action_panel",
        }
        assert expected_slots == set(COMPONENT_MAP.keys())

    def test_evidence_components_are_valid(self):
        valid = {"BigValue", "LineChart", "BarChart", "AreaChart", "DataTable",
                 "Dropdown", "ButtonGroup", "Value", "Alert"}
        assert set(COMPONENT_MAP.values()) == valid


class TestSqlBlock:
    def test_basic_sql_block(self, builder):
        sql = builder.build_sql_block(
            "revenue", "gold.fact_sales", ["SUM(amount)"], ["period"]
        )
        assert "```sql revenue" in sql
        assert "FROM gold.fact_sales" in sql
        assert "period" in sql
        assert "SUM(amount)" in sql

    def test_sql_block_with_filter_and_limit(self, builder):
        sql = builder.build_sql_block(
            "top_10", "gold.fact_sales", ["amount"],
            filters="region = 'EMEA'", limit=10
        )
        assert "WHERE region = 'EMEA'" in sql
        assert "LIMIT 10" in sql


class TestBuildComponent:
    def test_known_slot_type(self, builder):
        result = builder.build_component("trend_line", "my_data", {"x": "period", "y": "value"})
        assert "<LineChart" in result
        assert "data={my_data}" in result
        assert 'x="period"' in result

    def test_unknown_slot_type(self, builder):
        result = builder.build_component("unknown_widget", "q")
        assert "<!-- Unknown slot type" in result

    def test_kpi_card(self, builder):
        result = builder.build_kpi_card("revenue_q", title="Revenue")
        assert "<BigValue" in result
        assert "data={revenue_q}" in result
        assert '"Revenue"' in result

    def test_kpi_card_with_comparison(self, builder):
        result = builder.build_kpi_card("rev", comparison_col="prev_value")
        assert "comparison" in result

    def test_chart_with_series(self, builder):
        result = builder.build_chart("bar_chart", "sales", x="month", y="amount", series="region")
        assert "<BarChart" in result
        assert 'series="region"' in result

    def test_data_table(self, builder):
        result = builder.build_data_table("detail")
        assert "<DataTable" in result
        assert "data={detail}" in result

    def test_slicer_dropdown(self, builder):
        result = builder.build_slicer("slicer_dropdown", "regions", name="region_filter", value_col="region")
        assert "<Dropdown" in result
        assert 'name="region_filter"' in result
