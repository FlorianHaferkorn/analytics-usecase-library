"""Tests for the dbt metric generator."""

import json
import pytest
import sys
from pathlib import Path

# Allow imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from metric_generator.generate_dbt_metrics import (
    kpi_to_metric,
    generate_metrics_yaml,
    _parse_dax_agg,
)


class TestParseDaxAgg:
    def test_sum(self):
        func, table, col = _parse_dax_agg("SUM(fact_sales[amount])")
        assert func == "SUM"
        assert table == "fact_sales"
        assert col == "amount"

    def test_average(self):
        func, table, col = _parse_dax_agg("AVERAGE(fact_orders[unit_price])")
        assert func == "AVERAGE"
        assert col == "unit_price"

    def test_complex_dax(self):
        func, table, col = _parse_dax_agg("CALCULATE(SUM(Sales[Amount]))")
        assert func == ""


class TestKpiToMetric:
    def test_simple_sum(self):
        kpi = {
            "id": "KPI-COM-001",
            "label": "Net Sales",
            "measure_spec": {"dax_expression": "SUM(fact_sales[net_sales_amount])"},
        }
        metric = kpi_to_metric(kpi)
        assert metric is not None
        assert metric["name"] == "kpi_com_001"
        assert metric["label"] == "Net Sales"
        assert metric["type"] == "simple"
        assert metric["type_params"]["measure"] == "sum_net_sales_amount"
        assert metric["meta"]["kpi_id"] == "KPI-COM-001"

    def test_complex_dax_produces_placeholder(self):
        kpi = {
            "id": "KPI-FIN-001",
            "label": "YTD Revenue",
            "measure_spec": {"dax_expression": "CALCULATE(SUM(Sales[Amount]), DATESYTD(Date[Date]))"},
        }
        metric = kpi_to_metric(kpi)
        assert metric is not None
        assert metric["type"] == "derived"
        assert metric["meta"]["needs_manual_review"] is True

    def test_empty_dax_returns_none(self):
        kpi = {"id": "KPI-X", "measure_spec": {"dax_expression": ""}}
        assert kpi_to_metric(kpi) is None

    def test_no_measure_spec_returns_none(self):
        kpi = {"id": "KPI-X"}
        assert kpi_to_metric(kpi) is None


class TestGenerateMetricsYaml:
    def test_generates_from_ir(self, tmp_path):
        ir = {
            "nodes": [
                {
                    "id": "KPI-COM-001",
                    "type": "kpi",
                    "label": "Net Sales",
                    "measure_spec": {"dax_expression": "SUM(fact_sales[amount])"},
                },
                {
                    "id": "COM-001",
                    "type": "use_case",
                    "label": "Sales",
                },
            ],
            "edges": [],
        }
        ir_path = tmp_path / "ir_v1.json"
        ir_path.write_text(json.dumps(ir))

        result = generate_metrics_yaml(ir_path)
        assert result["version"] == 2
        assert len(result["metrics"]) == 1
        assert result["metrics"][0]["name"] == "kpi_com_001"

    def test_skips_non_kpi_nodes(self, tmp_path):
        ir = {
            "nodes": [{"id": "UC-001", "type": "use_case", "label": "X"}],
            "edges": [],
        }
        ir_path = tmp_path / "ir_v1.json"
        ir_path.write_text(json.dumps(ir))
        result = generate_metrics_yaml(ir_path)
        assert result["metrics"] == []
