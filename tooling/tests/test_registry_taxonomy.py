"""Tests for taxonomy validation in registry_builder.py"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from registry_builder import (
    Issue,
    KpiRecord,
    SourceLocation,
    load_taxonomy,
    validate_taxonomy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TAXONOMY = {
    "version": "1.0",
    "id_patterns": {
        "kpi": {
            "format": "<domain>.<entity>.<metric>",
            "regex": r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$",
        },
        "use_case": {
            "format": "<DOMAIN>-<NNN>",
            "regex": r"^[A-Z]{2,4}-\d{3}$",
        },
        "action_code": {
            "format": "<Prefix>-<Type><Seq>.<Sub>",
            "regex": r"^[A-Z]-[A-Z]\d+\.\d+$",
        },
    },
    "kpi_roles": ["strategic", "influencing", "operational"],
    "governance_statuses": ["active", "draft", "deprecated"],
}


def _make_kpi(kpi_id: str, role: str = "strategic") -> KpiRecord:
    return KpiRecord(
        kpi_id=kpi_id,
        source="core/kpi_catalog/test.md",
        line=10,
        kpi_role=role,
        governance={"owner_role": "analyst", "steward_role": "steward"},
    )


def _make_action(ac_id: str) -> dict:
    return {"id": ac_id, "source": "core/action_codes/Commercial/test.yaml", "raw": {"id": ac_id}}


def _make_bracket(uc_id: str, status: str = "active") -> dict:
    return {
        "id": uc_id,
        "source": "core/usecases/core/test/UseCase_Bracket.yaml",
        "raw": {"id": uc_id, "governance": {"status": status}},
    }


# ---------------------------------------------------------------------------
# load_taxonomy
# ---------------------------------------------------------------------------

class TestLoadTaxonomy:
    def test_loads_from_file(self, tmp_path):
        tax_dir = tmp_path / "tooling" / "validation"
        tax_dir.mkdir(parents=True)
        (tax_dir / "_index.yaml").write_text(yaml.dump(SAMPLE_TAXONOMY), encoding="utf-8")
        result = load_taxonomy(tmp_path)
        assert result["version"] == "1.0"
        assert "kpi" in result["id_patterns"]

    def test_returns_empty_if_missing(self, tmp_path):
        result = load_taxonomy(tmp_path)
        assert result == {}

    def test_returns_empty_on_invalid_yaml(self, tmp_path):
        tax_dir = tmp_path / "tooling" / "validation"
        tax_dir.mkdir(parents=True)
        (tax_dir / "_index.yaml").write_text("{{invalid yaml: [", encoding="utf-8")
        result = load_taxonomy(tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# KPI ID validation
# ---------------------------------------------------------------------------

class TestKpiIdValidation:
    def test_valid_kpi_id_no_issue(self):
        kpis = {"sales.net_sales.amount": _make_kpi("sales.net_sales.amount")}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        kpi_format_issues = [i for i in issues if i.code == "taxonomy.kpi_id_format"]
        assert len(kpi_format_issues) == 0

    def test_invalid_kpi_id_warns(self):
        kpis = {"SALES.NetSales": _make_kpi("SALES.NetSales")}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        kpi_format_issues = [i for i in issues if i.code == "taxonomy.kpi_id_format"]
        assert len(kpi_format_issues) == 1
        assert kpi_format_issues[0].severity == "WARN"

    def test_two_segment_kpi_id_warns(self):
        kpis = {"sales.amount": _make_kpi("sales.amount")}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        kpi_format_issues = [i for i in issues if i.code == "taxonomy.kpi_id_format"]
        assert len(kpi_format_issues) == 1

    def test_valid_kpi_with_underscores(self):
        kpis = {"finance.cash_flow.amount": _make_kpi("finance.cash_flow.amount")}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        kpi_format_issues = [i for i in issues if i.code == "taxonomy.kpi_id_format"]
        assert len(kpi_format_issues) == 0


# ---------------------------------------------------------------------------
# KPI role validation
# ---------------------------------------------------------------------------

class TestKpiRoleValidation:
    def test_valid_role_no_issue(self):
        kpis = {"sales.net.amount": _make_kpi("sales.net.amount", "strategic")}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        role_issues = [i for i in issues if i.code == "taxonomy.invalid_kpi_role"]
        assert len(role_issues) == 0

    def test_invalid_role_warns(self):
        kpis = {"sales.net.amount": _make_kpi("sales.net.amount", "primary")}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        role_issues = [i for i in issues if i.code == "taxonomy.invalid_kpi_role"]
        assert len(role_issues) == 1
        assert "primary" in role_issues[0].message

    def test_none_role_no_issue(self):
        rec = _make_kpi("sales.net.amount")
        rec = KpiRecord(
            kpi_id=rec.kpi_id, source=rec.source, line=rec.line,
            kpi_role=None, governance=rec.governance,
        )
        kpis = {"sales.net.amount": rec}
        issues = validate_taxonomy(kpis, {}, {}, SAMPLE_TAXONOMY)
        role_issues = [i for i in issues if i.code == "taxonomy.invalid_kpi_role"]
        assert len(role_issues) == 0


# ---------------------------------------------------------------------------
# Action code ID validation
# ---------------------------------------------------------------------------

class TestActionCodeIdValidation:
    def test_valid_action_code_no_issue(self):
        actions = {"C-M1.1": _make_action("C-M1.1")}
        issues = validate_taxonomy({}, actions, {}, SAMPLE_TAXONOMY)
        ac_issues = [i for i in issues if i.code == "taxonomy.action_code_id_format"]
        assert len(ac_issues) == 0

    def test_invalid_action_code_warns(self):
        actions = {"c-m1.1": _make_action("c-m1.1")}
        issues = validate_taxonomy({}, actions, {}, SAMPLE_TAXONOMY)
        ac_issues = [i for i in issues if i.code == "taxonomy.action_code_id_format"]
        assert len(ac_issues) == 1
        assert ac_issues[0].severity == "WARN"

    def test_missing_sub_version_warns(self):
        actions = {"C-M1": _make_action("C-M1")}
        issues = validate_taxonomy({}, actions, {}, SAMPLE_TAXONOMY)
        ac_issues = [i for i in issues if i.code == "taxonomy.action_code_id_format"]
        assert len(ac_issues) == 1


# ---------------------------------------------------------------------------
# Use case ID validation
# ---------------------------------------------------------------------------

class TestUseCaseIdValidation:
    def test_valid_usecase_id_no_issue(self):
        brackets = {"COM-001": _make_bracket("COM-001")}
        issues = validate_taxonomy({}, {}, brackets, SAMPLE_TAXONOMY)
        uc_issues = [i for i in issues if i.code == "taxonomy.usecase_id_format"]
        assert len(uc_issues) == 0

    def test_invalid_usecase_id_warns(self):
        brackets = {"com-1": _make_bracket("com-1")}
        issues = validate_taxonomy({}, {}, brackets, SAMPLE_TAXONOMY)
        uc_issues = [i for i in issues if i.code == "taxonomy.usecase_id_format"]
        assert len(uc_issues) == 1

    def test_four_letter_prefix_valid(self):
        brackets = {"XDOM-001": _make_bracket("XDOM-001")}
        issues = validate_taxonomy({}, {}, brackets, SAMPLE_TAXONOMY)
        uc_issues = [i for i in issues if i.code == "taxonomy.usecase_id_format"]
        assert len(uc_issues) == 0


# ---------------------------------------------------------------------------
# Governance status validation
# ---------------------------------------------------------------------------

class TestGovernanceStatusValidation:
    def test_valid_status_no_issue(self):
        brackets = {"COM-001": _make_bracket("COM-001", "active")}
        issues = validate_taxonomy({}, {}, brackets, SAMPLE_TAXONOMY)
        gov_issues = [i for i in issues if i.code == "taxonomy.invalid_governance_status"]
        assert len(gov_issues) == 0

    def test_invalid_status_warns(self):
        brackets = {"COM-001": _make_bracket("COM-001", "experimental")}
        issues = validate_taxonomy({}, {}, brackets, SAMPLE_TAXONOMY)
        gov_issues = [i for i in issues if i.code == "taxonomy.invalid_governance_status"]
        assert len(gov_issues) == 1
        assert "experimental" in gov_issues[0].message


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestTaxonomyEdgeCases:
    def test_empty_taxonomy_no_issues(self):
        kpis = {"bad_id": _make_kpi("bad_id")}
        issues = validate_taxonomy(kpis, {}, {}, {})
        assert len(issues) == 0

    def test_missing_regex_graceful(self):
        """Taxonomy with id_patterns but no regex for a type."""
        taxonomy = {"id_patterns": {"kpi": {"format": "something"}}, "kpi_roles": []}
        kpis = {"bad": _make_kpi("bad")}
        issues = validate_taxonomy(kpis, {}, {}, taxonomy)
        # No kpi regex → no format check → no format issue
        kpi_format_issues = [i for i in issues if i.code == "taxonomy.kpi_id_format"]
        assert len(kpi_format_issues) == 0

    def test_integration_real_repo(self):
        """Integration test: load real taxonomy and validate real registry."""
        repo_root = Path(__file__).resolve().parents[2]
        taxonomy = load_taxonomy(repo_root)
        if not taxonomy:
            pytest.skip("_index.yaml not found")

        # Import scan functions
        from registry_builder import scan_kpi_catalog, scan_action_codes, scan_usecase_brackets
        kpis, _ = scan_kpi_catalog(repo_root)
        actions, _ = scan_action_codes(repo_root)
        brackets, _ = scan_usecase_brackets(repo_root)

        issues = validate_taxonomy(kpis, actions, brackets, taxonomy)
        # All issues should be WARN (not ERROR)
        for issue in issues:
            assert issue.severity == "WARN", f"Expected WARN but got {issue.severity}: {issue.message}"
