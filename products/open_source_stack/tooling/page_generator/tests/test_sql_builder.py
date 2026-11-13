"""Tests for the SQL builder (DAX → SQL translation)."""

from pathlib import Path

import pytest
from page_generator.sql_builder import SqlBuilder

REPO_ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture
def builder():
    return SqlBuilder(schema="gold")


class TestDaxToSql:
    def test_sum(self, builder):
        result = builder.dax_to_sql_expression("SUM(fact_sales[net_sales_amount])")
        assert result == "SUM(net_sales_amount)"

    def test_average(self, builder):
        result = builder.dax_to_sql_expression("AVERAGE(fact_sales[unit_price])")
        assert result == "AVG(unit_price)"

    def test_count(self, builder):
        result = builder.dax_to_sql_expression("COUNT(fact_orders[order_id])")
        assert result == "COUNT(order_id)"

    def test_distinctcount(self, builder):
        result = builder.dax_to_sql_expression("DISTINCTCOUNT(fact_sales[customer_id])")
        assert result == "COUNT(DISTINCT customer_id)"

    def test_countrows(self, builder):
        result = builder.dax_to_sql_expression("COUNTROWS(fact_sales[id])")
        assert result == "COUNT(*)"

    def test_divide(self, builder):
        result = builder.dax_to_sql_expression(
            "DIVIDE(SUM(fact_sales[profit]), SUM(fact_sales[revenue]))"
        )
        assert "CASE WHEN" in result
        assert "SUM(profit)" in result
        assert "SUM(revenue)" in result
        assert "NULL" in result

    def test_complex_dax_returns_todo(self, builder):
        result = builder.dax_to_sql_expression(
            "CALCULATE(SUM(Sales[Amount]), FILTER(ALL(Date), Date[Year] = 2024))"
        )
        assert "TODO" in result

    def test_empty_dax(self, builder):
        result = builder.dax_to_sql_expression("")
        assert "TODO" in result


class TestQueryName:
    def test_kpi_to_query_name(self, builder):
        assert builder.kpi_to_query_name("KPI-COM-001") == "kpi_com_001"
        assert builder.kpi_to_query_name("KPI-FIN-010") == "kpi_fin_010"


class TestBuildQueries:
    def test_headline_query(self, builder):
        q = builder.build_kpi_headline_query(
            "net_sales", "gold.fact_sales", "SUM(net_sales_amount)", "Net Sales"
        )
        assert "```sql net_sales" in q
        assert "SUM(net_sales_amount) AS value" in q
        assert "'Net Sales' AS label" in q
        assert "FROM gold.fact_sales" in q

    def test_trend_query(self, builder):
        q = builder.build_trend_query(
            "sales_trend", "gold.fact_sales", "SUM(amount)"
        )
        assert "```sql sales_trend" in q
        assert "GROUP BY period" in q
        assert "ORDER BY period" in q

    def test_trend_query_with_segment(self, builder):
        q = builder.build_trend_query(
            "sales_seg", "gold.fact_sales", "SUM(amount)", segment_column="region"
        )
        assert "region" in q
        assert "GROUP BY period, region" in q

    def test_detail_query(self, builder):
        q = builder.build_detail_query(
            "detail", "gold.fact_sales", ["entity", "period", "value"]
        )
        assert "```sql detail" in q
        assert "LIMIT 500" in q
        assert "entity, period, value" in q


class TestInferTable:
    def test_infer_from_dax(self, builder):
        node = {"measure_spec": {"dax_expression": "SUM(fact_sales[amount])"}}
        assert builder.infer_table_from_kpi(node) == "gold.fact_sales"

    def test_fallback_to_domain(self, builder):
        node = {"domain": "Commercial"}
        assert builder.infer_table_from_kpi(node) == "gold.fact_commercial"

    def test_fallback_unknown(self, builder):
        node = {}
        assert builder.infer_table_from_kpi(node) == "gold.fact_unknown"


class TestMetricEvidenceContract:
    """gold.metric_evidence (long) against its neighbours: Fabric vocabulary, source SQL, brackets."""

    def test_dimensions_equal_the_fabric_token_vocabulary(self):
        import re
        import sys

        from page_generator.sql_builder import METRIC_EVIDENCE_DIMENSIONS

        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from products.fabric.powerbi.tooling.page_scaffold_generator.config_loader import EVIDENCE_DIM_TOKENS

        assert len(METRIC_EVIDENCE_DIMENSIONS) == 6
        for name, pbi_column in METRIC_EVIDENCE_DIMENSIONS.items():
            assert EVIDENCE_DIM_TOKENS[name] == pbi_column, name
        assert all(re.match(r"^[a-z][a-z0-9_]*$", name) for name in METRIC_EVIDENCE_DIMENSIONS)

    def test_source_sql_declares_exactly_the_contract_columns(self):
        import re

        from page_generator.sql_builder import METRIC_EVIDENCE_COLUMNS

        sql = (REPO_ROOT / "products/open_source_stack/evidence_app/sources/gold/metric_evidence.sql").read_text(
            encoding="utf-8"
        )
        assert tuple(re.findall(r"\bAS (\w+),?$", sql, re.MULTILINE)) == METRIC_EVIDENCE_COLUMNS

    @pytest.mark.parametrize(
        "bracket, dimensions, kpi_count",
        [
            ("COM-001_Sales_Performance", ["region", "country", "entity"], 5),
            ("COM-004_Promotion_Effectiveness", ["promotion", "product_category", "mechanic"], 5),
        ],
    )
    def test_reference_brackets_resolve(self, bracket, dimensions, kpi_count):
        import yaml

        from page_generator.sql_builder import resolve_evidence_columns

        data = yaml.safe_load((REPO_ROOT / "core/usecases/core" / bracket / "UseCase_Bracket.yaml").read_text(
            encoding="utf-8"
        ))
        tokens = data["ux_layout_rules"]["page_2_execution"]["component_300s"]["evidence_columns"]
        catalog_ids = [t for t in tokens if t.startswith("KPI-")]
        dims, kpis = resolve_evidence_columns(tokens, catalog_ids)
        assert dims == dimensions
        assert len(kpis) == kpi_count

    def test_detail_query_reads_long_table(self, builder):
        q = builder.build_metric_detail_query("d", ["KPI-COM-005", "KPI-COM-013"], ["region"])
        assert "  region, kpi_id, period, metric_value\n" in q
        assert "WHERE kpi_id IN ('KPI-COM-005', 'KPI-COM-013')" in q
        with pytest.raises(ValueError):
            builder.build_metric_detail_query("d", ["KPI-COM-005"], ["dim_org.Region"])
