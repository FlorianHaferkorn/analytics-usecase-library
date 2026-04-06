"""Tests for the preflight validator."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ..preflight.validator import PreflightValidator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env(tmp_path: Path):
    """Minimal environment with KPI catalog + action codes + bracket."""
    kpi_root = tmp_path / "kpi_catalog"
    kpi_root.mkdir()
    ac_root = tmp_path / "action_codes" / "commercial"
    ac_root.mkdir(parents=True)
    uc_root = tmp_path / "usecases"
    uc_root.mkdir()

    # KPI
    kpi = {
        "id": "com.sales.net_sales_amount",
        "name": "Net Sales Amount",
        "dax_expression": "SUM ( fact_sales[Net Sales Amount] )",
        "format_string": "#,0",
    }
    (kpi_root / "com.sales.net_sales_amount.yaml").write_text(yaml.dump(kpi))

    # Action code
    ac = {"id": "C-S1.1", "name": "Test Action", "owner": "Sales VP"}
    (ac_root / "C-S1.1.yaml").write_text(yaml.dump(ac))

    # Valid bracket
    bracket = {
        "id": "COM-001",
        "title": "Sales Performance",
        "primary_kpi_ids": ["com.sales.net_sales_amount"],
        "influencing_kpi_ids": [],
        "orchestration": {"action_code_ids": ["C-S1.1"]},
        "ux_layout_rules": {
            "page_1_summary": {
                "page_type": "T1",
                "component_30s": [
                    {"visual_type": "trend_line", "category": "dim_date.Date"},
                ],
            },
            "page_2_execution": {
                "component_300s": {"action_panel": True}
            },
        },
    }
    bracket_dir = uc_root / "COM-001_Sales_Performance"
    bracket_dir.mkdir()
    bracket_path = bracket_dir / "UseCase_Bracket.yaml"
    bracket_path.write_text(yaml.dump(bracket))

    return {
        "tmp": tmp_path,
        "kpi_root": kpi_root,
        "ac_root": ac_root,
        "uc_root": uc_root,
        "bracket": bracket_path,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPreflightValidator:
    def test_valid_bracket_passes(self, env):
        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        assert report.passed, f"Expected pass, got errors: {report.errors}"

    def test_missing_kpi_fails(self, env):
        bracket = yaml.safe_load(env["bracket"].read_text())
        bracket["primary_kpi_ids"].append("nonexistent.kpi")
        env["bracket"].write_text(yaml.dump(bracket))

        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        assert not report.passed
        assert any("MISSING_KPI" in e for e in report.errors)

    def test_missing_action_code_fails(self, env):
        bracket = yaml.safe_load(env["bracket"].read_text())
        bracket["orchestration"]["action_code_ids"].append("C-NONEXISTENT.1")
        env["bracket"].write_text(yaml.dump(bracket))

        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        assert not report.passed
        assert any("MISSING_ACTION_CODE" in e for e in report.errors)

    def test_action_panel_without_codes_fails(self, env):
        bracket = yaml.safe_load(env["bracket"].read_text())
        bracket["orchestration"]["action_code_ids"] = []
        # action_panel still enabled
        env["bracket"].write_text(yaml.dump(bracket))

        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        assert not report.passed
        assert any("ACTION_PANEL_NO_CODES" in e for e in report.errors)

    def test_missing_primary_kpis_fails(self, env):
        bracket = yaml.safe_load(env["bracket"].read_text())
        bracket["primary_kpi_ids"] = []
        env["bracket"].write_text(yaml.dump(bracket))

        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        assert not report.passed
        assert any("NO_PRIMARY_KPIS" in e for e in report.errors)

    def test_missing_bracket_file_fails(self, env):
        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(Path("/nonexistent/UseCase_Bracket.yaml"))
        assert not report.passed
        assert any("FILE_NOT_FOUND" in e for e in report.errors)

    def test_quick_mode_skips_action_code_check(self, env):
        # In quick mode, action code file existence is not checked
        bracket = yaml.safe_load(env["bracket"].read_text())
        bracket["orchestration"]["action_code_ids"] = ["C-GHOST.99"]
        # But at least one real KPI so action panel validation passes
        bracket["primary_kpi_ids"] = ["com.sales.net_sales_amount"]
        env["bracket"].write_text(yaml.dump(bracket))

        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
            mode="quick",
        )
        report = validator.run(env["bracket"])
        # Quick mode doesn't run check_action_code_refs_exist
        assert not any("MISSING_ACTION_CODE" in e for e in report.errors)

    def test_report_has_suggestions(self, env):
        bracket = yaml.safe_load(env["bracket"].read_text())
        bracket["primary_kpi_ids"].append("missing.kpi.id")
        env["bracket"].write_text(yaml.dump(bracket))

        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        assert len(report.suggestions) > 0

    def test_run_all_returns_list(self, env):
        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        reports = validator.run_all([env["bracket"]])
        assert len(reports) == 1

    def test_report_to_dict(self, env):
        validator = PreflightValidator(
            kpi_catalog_root=env["kpi_root"],
            action_codes_root=env["ac_root"],
        )
        report = validator.run(env["bracket"])
        d = report.to_dict()
        assert "passed" in d
        assert "errors" in d
        assert "warnings" in d
        assert "checks_run" in d
