"""Tests for the OSS validation runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_oss import check_evidence_app, check_evidence_pages, check_metrics_vs_kpi


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

REPO_ROOT = Path(__file__).resolve().parents[4]
_PEERS = {"svelte": "4.2.19", "typescript": "5.4.2"}


def _write_app(
    root: Path,
    *,
    config: str = "plugins:\n  components:\n    x: {}\n  datasources:\n    y: {}\n",
    declared: dict[str, str] | None = None,
    with_source: bool = True,
) -> Path:
    app = root / "products" / "open_source_stack" / "evidence_app"
    (app / "pages").mkdir(parents=True)
    (app / "evidence.config.yaml").write_text(config, encoding="utf-8")
    (app / "pages" / "p.md").write_text(
        "# P\n\n```sql q\nSELECT period\nFROM gold.metric_observations\n```\n", encoding="utf-8"
    )
    if with_source:
        (app / "sources" / "gold").mkdir(parents=True)
        (app / "sources" / "gold" / "connection.yaml").write_text("name: gold\n", encoding="utf-8")
        (app / "sources" / "gold" / "metric_observations.sql").write_text("SELECT 1\n", encoding="utf-8")
    deps = {"@evidence-dev/evidence": "40.1.8", **(_PEERS if declared is None else declared)}
    (app / "package.json").write_text(json.dumps({"dependencies": deps}), encoding="utf-8")
    lock = {"packages": {"node_modules/@evidence-dev/evidence": {"peerDependencies": _PEERS}}}
    (app / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")
    return app


class TestCheckEvidenceApp:
    def test_repo_app_passes_and_reads_gold_tables(self):
        result = check_evidence_app(REPO_ROOT)
        assert result.errors == []
        pages = sorted((REPO_ROOT / "products/open_source_stack/evidence_app/pages").glob("*.md"))
        assert len(pages) == 4
        assert all("FROM gold." in page.read_text(encoding="utf-8") for page in pages)

    def test_minimal_app_passes(self, tmp_path: Path):
        _write_app(tmp_path)
        assert check_evidence_app(tmp_path).passed is True

    def test_pre40_config_fails(self, tmp_path: Path):
        _write_app(tmp_path, config="data_sources:\n  - name: default\n    type: duckdb\n")
        result = check_evidence_app(tmp_path)
        assert result.passed is False
        assert any("data_sources" in error for error in result.errors)
        assert any("plugins.components" in error for error in result.errors)

    def test_missing_source_for_page_table_fails(self, tmp_path: Path):
        _write_app(tmp_path, with_source=False)
        result = check_evidence_app(tmp_path)
        assert result.errors == ["pages read gold.metric_observations, but sources/gold/connection.yaml is missing"]

    def test_unpinned_or_drifted_peer_fails(self, tmp_path: Path):
        _write_app(tmp_path, declared={"svelte": "4.2.19", "typescript": "^7.0.0"})
        result = check_evidence_app(tmp_path)
        assert result.errors == ["typescript: package.json has ^7.0.0, @evidence-dev/evidence expects 5.4.2"]
        _write_app(tmp_path / "b", declared={"svelte": "4.2.19"})
        result = check_evidence_app(tmp_path / "b")
        assert result.errors == [
            "peer dependency typescript@5.4.2 of @evidence-dev/evidence not declared in package.json"
        ]

    def test_missing_lockfile_fails(self, tmp_path: Path):
        app = _write_app(tmp_path)
        (app / "package-lock.json").unlink()
        assert check_evidence_app(tmp_path).errors == ["package.json and package-lock.json are both required (npm ci)"]
