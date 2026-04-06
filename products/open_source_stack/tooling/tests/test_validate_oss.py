"""Tests for the OSS validation runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_oss import check_evidence_pages, check_metrics_vs_kpi


def _write_ir(root: Path, use_cases: dict[str, object]) -> None:
    ir_dir = root / "tooling" / "ir" / "out"
    ir_dir.mkdir(parents=True, exist_ok=True)
    ir = {
        "ir_version": "1.0",
        "generated_at_utc": "2026-04-02T00:00:00Z",
        "source": {
            "core_abi": {
                "master_registry_path": "registry.json",
                "value_map_path": "value_map.json",
            }
        },
        "objects": {
            "use_cases": use_cases,
            "kpis": {},
            "action_codes": {},
        },
    }
    (ir_dir / "ir_v1.json").write_text(json.dumps(ir), encoding="utf-8")


def _write_metrics(root: Path, content: str) -> None:
    metrics_dir = root / "products" / "open_source_stack" / "dbt_project" / "models" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / "_metrics.yml").write_text(content, encoding="utf-8")


class TestCheckEvidencePages:
    def test_fails_when_pages_missing(self, tmp_path: Path):
        result = check_evidence_pages(tmp_path)
        assert result.passed is False
        assert any("pages directory" in error for error in result.errors)


class TestCheckMetricsVsKpi:
    def test_passes_when_every_orchestrated_kpi_has_metric(self, tmp_path: Path):
        _write_ir(
            tmp_path,
            {
                "COM-001": {
                    "id": "COM-001",
                    "orchestration": {
                        "strategic_kpi_id": "sales.net.amount",
                        "influencing_kpi_ids": ["sales.margin.pct"],
                        "action_code_ids": [],
                    },
                }
            },
        )
        _write_metrics(
            tmp_path,
            """
version: 2
metrics:
  - name: sales_net_amount
    type: simple
    type_params:
      measure: sum_amount
    meta:
      kpi_id: sales.net.amount
  - name: sales_margin_pct
    type: simple
    type_params:
      measure: avg_margin_pct
    meta:
      kpi_id: sales.margin.pct
""".strip(),
        )

        result = check_metrics_vs_kpi(tmp_path)
        assert result.passed is True
        assert result.errors == []

    def test_fails_when_metric_missing_or_manual_review(self, tmp_path: Path):
        _write_ir(
            tmp_path,
            {
                "COM-001": {
                    "id": "COM-001",
                    "orchestration": {
                        "strategic_kpi_id": "sales.net.amount",
                        "influencing_kpi_ids": ["sales.margin.pct"],
                        "action_code_ids": [],
                    },
                }
            },
        )
        _write_metrics(
            tmp_path,
                        "\n".join(
                                [
                                        "version: 2",
                                        "metrics:",
                                        "  - name: sales_net_amount",
                                        '    description: "TODO: translate complex DAX"',
                                        "    type: derived",
                                        "    type_params:",
                                        '      expr: "1"',
                                        "    meta:",
                                        "      kpi_id: sales.net.amount",
                                        "      needs_manual_review: true",
                                ]
                        ),
        )

        result = check_metrics_vs_kpi(tmp_path)
        assert result.passed is False
        assert any("sales.net.amount" in error for error in result.errors)
        assert any("sales.margin.pct" in error for error in result.errors)