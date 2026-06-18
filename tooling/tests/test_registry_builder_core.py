"""Tests for core parsing/scanning functions in registry_builder.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from registry_builder import (
    FencedYamlBlock,
    Issue,
    KpiRecord,
    SourceLocation,
    build_linked_sets_from_brackets,
    extract_fenced_yaml_blocks,
    extract_frontmatter,
    find_line_containing_token,
    find_line_for_yaml_kv,
    frontmatter_get_scalar,
    scan_action_codes,
    scan_kpi_catalog,
    scan_usecase_brackets,
    validate_evidence_grains,
)


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------

class TestExtractFrontmatter:
    def test_valid_frontmatter(self):
        lines = ["---", "id: COM-001", "title: Sales", "---", "# Body"]
        result = extract_frontmatter(lines)
        assert result is not None
        start, end, fm_lines = result
        assert start == 1
        assert end == 4
        assert fm_lines == ["id: COM-001", "title: Sales"]

    def test_no_frontmatter(self):
        lines = ["# Just a heading", "Some content"]
        assert extract_frontmatter(lines) is None

    def test_empty_file(self):
        assert extract_frontmatter([]) is None

    def test_unclosed_frontmatter(self):
        lines = ["---", "id: COM-001", "no closing fence"]
        assert extract_frontmatter(lines) is None

    def test_empty_frontmatter(self):
        lines = ["---", "---", "body"]
        result = extract_frontmatter(lines)
        assert result is not None
        _, _, fm_lines = result
        assert fm_lines == []


# ---------------------------------------------------------------------------
# frontmatter_get_scalar
# ---------------------------------------------------------------------------

class TestFrontmatterGetScalar:
    def test_simple_value(self):
        lines = ["id: COM-001", "title: Sales Performance"]
        assert frontmatter_get_scalar(lines, "id") == "COM-001"

    def test_quoted_value(self):
        lines = ['id: "COM-001"', "title: Sales"]
        assert frontmatter_get_scalar(lines, "id") == "COM-001"

    def test_single_quoted(self):
        lines = ["id: 'COM-001'"]
        assert frontmatter_get_scalar(lines, "id") == "COM-001"

    def test_missing_key(self):
        lines = ["title: Sales"]
        assert frontmatter_get_scalar(lines, "id") is None


# ---------------------------------------------------------------------------
# extract_fenced_yaml_blocks
# ---------------------------------------------------------------------------

class TestExtractFencedYamlBlocks:
    def test_single_block(self):
        lines = [
            "# Header",
            "```yaml",
            "key: value",
            "list:",
            "  - item1",
            "```",
            "More text",
        ]
        blocks = extract_fenced_yaml_blocks(lines)
        assert len(blocks) == 1
        b = blocks[0]
        assert b.start_line == 2  # 1-based line of ```yaml
        assert b.end_line == 6    # 1-based line of closing ```
        assert b.yaml_start_line == 3
        assert b.yaml_lines == ["key: value", "list:", "  - item1"]

    def test_multiple_blocks(self):
        lines = [
            "```yaml",
            "a: 1",
            "```",
            "text",
            "```yaml",
            "b: 2",
            "```",
        ]
        blocks = extract_fenced_yaml_blocks(lines)
        assert len(blocks) == 2
        assert blocks[0].yaml_lines == ["a: 1"]
        assert blocks[1].yaml_lines == ["b: 2"]

    def test_no_blocks(self):
        lines = ["# Just markdown", "No yaml here"]
        assert extract_fenced_yaml_blocks(lines) == []

    def test_unclosed_block(self):
        lines = ["```yaml", "orphan: true", "no closing fence"]
        blocks = extract_fenced_yaml_blocks(lines)
        assert len(blocks) == 1
        assert blocks[0].yaml_lines == ["orphan: true", "no closing fence"]
        assert blocks[0].end_line == 3  # EOF

    def test_empty_block(self):
        lines = ["```yaml", "```"]
        blocks = extract_fenced_yaml_blocks(lines)
        assert len(blocks) == 1
        assert blocks[0].yaml_lines == []

    def test_case_insensitive(self):
        lines = ["```YAML", "x: 1", "```"]
        blocks = extract_fenced_yaml_blocks(lines)
        assert len(blocks) == 1


# ---------------------------------------------------------------------------
# find_line_for_yaml_kv / find_line_containing_token
# ---------------------------------------------------------------------------

class TestLineFinders:
    def test_find_yaml_kv(self):
        yaml_lines = ["- kpi_id: sales.net.amount", "  kpi_role: strategic"]
        result = find_line_for_yaml_kv(
            yaml_lines=yaml_lines, yaml_start_line=10,
            keys=["kpi_id"], value="sales.net.amount",
        )
        assert result == 10

    def test_find_yaml_kv_quoted(self):
        yaml_lines = ['  kpi_id: "crm.clv.amount"']
        result = find_line_for_yaml_kv(
            yaml_lines=yaml_lines, yaml_start_line=5,
            keys=["kpi_id"], value="crm.clv.amount",
        )
        assert result == 5

    def test_find_yaml_kv_not_found(self):
        yaml_lines = ["kpi_id: other.kpi"]
        result = find_line_for_yaml_kv(
            yaml_lines=yaml_lines, yaml_start_line=1,
            keys=["kpi_id"], value="missing.kpi",
        )
        assert result is None

    def test_find_line_containing_token(self):
        lines = ["orchestration:", "  action_code_ids:", "    - C-M1.1", "    - C-M1.2"]
        result = find_line_containing_token(lines, "C-M1.1")
        assert result == 3

    def test_find_line_containing_token_not_found(self):
        lines = ["nothing: here"]
        assert find_line_containing_token(lines, "missing") is None

    def test_find_line_containing_token_empty(self):
        assert find_line_containing_token(["a: b"], "") is None


# ---------------------------------------------------------------------------
# scan_action_codes
# ---------------------------------------------------------------------------

class TestScanActionCodes:
    def test_scan_valid_action_code(self, tmp_path):
        ac_dir = tmp_path / "core" / "action_codes" / "Commercial"
        ac_dir.mkdir(parents=True)
        (ac_dir / "C-M1.1.yaml").write_text(
            yaml.dump({"id": "C-M1.1", "trigger": {"type": "threshold"}}),
            encoding="utf-8",
        )
        actions, issues = scan_action_codes(tmp_path)
        assert "C-M1.1" in actions
        assert actions["C-M1.1"]["id"] == "C-M1.1"
        assert not any(i.severity == "ERROR" for i in issues)

    def test_scan_missing_id(self, tmp_path):
        ac_dir = tmp_path / "core" / "action_codes" / "Finance"
        ac_dir.mkdir(parents=True)
        (ac_dir / "bad.yaml").write_text(
            yaml.dump({"trigger": {"type": "alert"}}),
            encoding="utf-8",
        )
        actions, issues = scan_action_codes(tmp_path)
        assert len(actions) == 0
        assert any(i.code == "action_code.missing_id" for i in issues)

    def test_scan_invalid_yaml(self, tmp_path):
        ac_dir = tmp_path / "core" / "action_codes" / "Ops"
        ac_dir.mkdir(parents=True)
        (ac_dir / "broken.yaml").write_text(
            "id: O-P1.1\n  bad indent:\nyaml: [",
            encoding="utf-8",
        )
        actions, issues = scan_action_codes(tmp_path)
        assert any(i.code == "action_code.yaml_parse_failed" for i in issues)

    def test_scan_no_action_codes_dir(self, tmp_path):
        actions, issues = scan_action_codes(tmp_path)
        assert actions == {}
        assert issues == []

    def test_skips_decision_spines(self, tmp_path):
        ac_dir = tmp_path / "core" / "action_codes" / "decision_spines"
        ac_dir.mkdir(parents=True)
        (ac_dir / "spine.yaml").write_text(
            yaml.dump({"id": "SPINE-1"}),
            encoding="utf-8",
        )
        actions, issues = scan_action_codes(tmp_path)
        assert "SPINE-1" not in actions


# ---------------------------------------------------------------------------
# scan_kpi_catalog
# ---------------------------------------------------------------------------

class TestScanKpiCatalog:
    def _write_catalog(self, tmp_path, content):
        kpi_dir = tmp_path / "core" / "kpi_catalog"
        kpi_dir.mkdir(parents=True, exist_ok=True)
        (kpi_dir / "test_catalog.md").write_text(content, encoding="utf-8")

    def test_scan_single_kpi(self, tmp_path):
        self._write_catalog(tmp_path, textwrap.dedent("""\
            # Test KPI Catalog

            ```yaml
            - kpi_id: sales.net.amount
              kpi_role: strategic
              business_owner: Sales BI
              data_owner: Data Team
            ```
        """))
        kpis, issues = scan_kpi_catalog(tmp_path)
        assert "sales.net.amount" in kpis
        rec = kpis["sales.net.amount"]
        assert rec.kpi_role == "strategic"
        assert rec.governance["business_owner"] == "Sales BI"

    def test_scan_multiple_kpis(self, tmp_path):
        self._write_catalog(tmp_path, textwrap.dedent("""\
            # Catalog

            ```yaml
            - kpi_id: a.b.c
              kpi_role: strategic
            - kpi_id: x.y.z
              kpi_role: operational
            ```
        """))
        kpis, issues = scan_kpi_catalog(tmp_path)
        assert len(kpis) == 2
        assert "a.b.c" in kpis
        assert "x.y.z" in kpis

    def test_duplicate_kpi_raises_error(self, tmp_path):
        self._write_catalog(tmp_path, textwrap.dedent("""\
            # Catalog

            ```yaml
            - kpi_id: dup.kpi.id
              kpi_role: strategic
            - kpi_id: dup.kpi.id
              kpi_role: operational
            ```
        """))
        kpis, issues = scan_kpi_catalog(tmp_path)
        assert len(kpis) == 1  # first one kept
        assert any(i.code == "kpi_catalog.duplicate_kpi_id" for i in issues)

    def test_no_catalog_dir(self, tmp_path):
        kpis, issues = scan_kpi_catalog(tmp_path)
        assert kpis == {}
        assert issues == []

    def test_depends_on_measures_inline(self, tmp_path):
        self._write_catalog(tmp_path, textwrap.dedent("""\
            # Catalog

            ```yaml
            - kpi_id: test.kpi.id
              kpi_role: strategic
              technical:
                depends_on_measures: [measure_a, measure_b]
            ```
        """))
        kpis, issues = scan_kpi_catalog(tmp_path)
        rec = kpis["test.kpi.id"]
        assert "measure_a" in rec.depends_on_measures
        assert "measure_b" in rec.depends_on_measures


# ---------------------------------------------------------------------------
# scan_usecase_brackets
# ---------------------------------------------------------------------------

class TestScanUsecaseBrackets:
    def test_scan_valid_bracket(self, tmp_path):
        uc_dir = tmp_path / "core" / "usecases" / "core" / "COM-001_Sales"
        uc_dir.mkdir(parents=True)
        (uc_dir / "UseCase_Bracket.yaml").write_text(
            yaml.dump({
                "id": "COM-001",
                "schema_version": "2.0",
                "orchestration": {
                    "strategic_kpi_id": "sales.net.amount",
                    "action_code_ids": ["C-M1.1"],
                },
            }),
            encoding="utf-8",
        )
        brackets, issues = scan_usecase_brackets(tmp_path)
        assert "COM-001" in brackets
        assert not any(i.severity == "ERROR" for i in issues)

    def test_scan_missing_id(self, tmp_path):
        uc_dir = tmp_path / "core" / "usecases" / "core" / "BAD-001"
        uc_dir.mkdir(parents=True)
        (uc_dir / "UseCase_Bracket.yaml").write_text(
            yaml.dump({"schema_version": "2.0"}),
            encoding="utf-8",
        )
        brackets, issues = scan_usecase_brackets(tmp_path)
        assert len(brackets) == 0
        assert any(i.code == "usecase_bracket.missing_id" for i in issues)

    def test_scan_legacy_schema_warns(self, tmp_path):
        uc_dir = tmp_path / "core" / "usecases" / "core" / "COM-002_Marketing"
        uc_dir.mkdir(parents=True)
        (uc_dir / "UseCase_Bracket.yaml").write_text(
            yaml.dump({"id": "COM-002", "schema_version": "1.0"}),
            encoding="utf-8",
        )
        brackets, issues = scan_usecase_brackets(tmp_path)
        assert "COM-002" in brackets
        assert any(i.code == "usecase_bracket.legacy_schema_version" for i in issues)

    def test_no_usecases_dir(self, tmp_path):
        brackets, issues = scan_usecase_brackets(tmp_path)
        assert brackets == {}
        assert issues == []


# ---------------------------------------------------------------------------
# build_linked_sets_from_brackets
# ---------------------------------------------------------------------------

class TestBuildLinkedSetsFromBrackets:
    def test_active_bracket_links(self):
        brackets = {
            "COM-001": {
                "id": "COM-001",
                "source": "core/usecases/core/COM-001/UseCase_Bracket.yaml",
                "raw": {
                    "governance": {"status": "active"},
                    "orchestration": {
                        "strategic_kpi_id": "sales.net.amount",
                        "influencing_kpi_ids": ["crm.clv.amount"],
                        "action_code_ids": ["C-M1.1", "C-M1.2"],
                    },
                },
            },
        }
        uc_ids, kpi_ids, action_ids, issues = build_linked_sets_from_brackets(brackets)
        assert "COM-001" in uc_ids
        assert "sales.net.amount" in kpi_ids
        assert "crm.clv.amount" in kpi_ids
        assert "C-M1.1" in action_ids
        assert "C-M1.2" in action_ids
        assert not any(i.severity == "ERROR" for i in issues)

    def test_inactive_bracket_skipped(self):
        brackets = {
            "DRAFT-001": {
                "id": "DRAFT-001",
                "source": "test.yaml",
                "raw": {
                    "governance": {"status": "deprecated"},
                    "orchestration": {
                        "strategic_kpi_id": "should.not.appear",
                        "action_code_ids": ["X-1.1"],
                    },
                },
            },
        }
        uc_ids, kpi_ids, action_ids, issues = build_linked_sets_from_brackets(brackets)
        assert len(uc_ids) == 0
        assert len(kpi_ids) == 0
        assert len(action_ids) == 0

    def test_missing_orchestration(self):
        brackets = {
            "BAD-001": {
                "id": "BAD-001",
                "source": "test.yaml",
                "raw": {"governance": {"status": "active"}},
            },
        }
        uc_ids, kpi_ids, action_ids, issues = build_linked_sets_from_brackets(brackets)
        assert "BAD-001" in uc_ids
        assert any(i.code == "usecase_bracket.missing_orchestration" for i in issues)

    def test_missing_strategic_kpi(self):
        brackets = {
            "COM-002": {
                "id": "COM-002",
                "source": "test.yaml",
                "raw": {
                    "governance": {"status": "active"},
                    "orchestration": {
                        "action_code_ids": ["C-M1.1"],
                    },
                },
            },
        }
        uc_ids, kpi_ids, action_ids, issues = build_linked_sets_from_brackets(brackets)
        assert any(i.code == "usecase_bracket.missing_strategic_kpi_id" for i in issues)

    def test_supporting_kpi_ids(self):
        brackets = {
            "COM-003": {
                "id": "COM-003",
                "source": "test.yaml",
                "raw": {
                    "orchestration": {
                        "strategic_kpi_id": "main.kpi",
                        "supporting_kpi_ids": ["support.a", "support.b"],
                        "action_code_ids": [],
                    },
                },
            },
        }
        uc_ids, kpi_ids, action_ids, issues = build_linked_sets_from_brackets(brackets)
        assert "support.a" in kpi_ids
        assert "support.b" in kpi_ids

    def test_empty_brackets(self):
        uc_ids, kpi_ids, action_ids, issues = build_linked_sets_from_brackets({})
        assert len(uc_ids) == 0
        assert len(kpi_ids) == 0
        assert len(action_ids) == 0
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Integration: scan against real repo
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_real_repo_scan(self):
        """Smoke test: scan real repo and verify no errors in core functions."""
        repo = Path(__file__).resolve().parents[2]
        if not (repo / "core" / "action_codes").exists():
            pytest.skip("Not running from repo root")

        actions, ac_issues = scan_action_codes(repo)
        assert len(actions) > 0, "Expected at least one action code"
        errors = [i for i in ac_issues if i.severity == "ERROR"]
        assert len(errors) == 0, f"Action code scan errors: {errors}"

        kpis, kpi_issues = scan_kpi_catalog(repo)
        assert len(kpis) > 0, "Expected at least one KPI"
        errors = [i for i in kpi_issues if i.severity == "ERROR"]
        assert len(errors) == 0, f"KPI catalog scan errors: {errors}"

        brackets, br_issues = scan_usecase_brackets(repo)
        assert len(brackets) > 0, "Expected at least one bracket"
        errors = [i for i in br_issues if i.severity == "ERROR"]
        assert len(errors) == 0, f"Bracket scan errors: {errors}"

        uc_ids, kpi_ids, action_ids, link_issues = build_linked_sets_from_brackets(brackets)
        assert len(uc_ids) > 0
        assert len(kpi_ids) > 0
        assert len(action_ids) > 0


# ---------------------------------------------------------------------------
# Lifecycle gate (ADR-0004): draft vs final use cases
# ---------------------------------------------------------------------------

class TestLifecycleGate:
    """A draft use case parks unresolved references (advisory WARN); a final
    (active / default) use case enforces them (ERROR)."""

    REPO = Path(__file__).resolve().parents[2]
    ALLOWED = {"invoice_line", "customer_month"}

    @staticmethod
    def _bracket(uc_id, status, grain):
        gov = {"owner_role": "r1", "steward_role": "r2"}
        if status is not None:
            gov["status"] = status
        return {
            uc_id: {
                "id": uc_id,
                "source": "does/not/exist.yaml",
                "raw": {
                    "governance": gov,
                    "ux_layout_rules": {
                        "page_2_execution": {
                            "component_300s": {"evidence_grain": grain}
                        }
                    },
                },
            }
        }

    def _grain_issue(self, status):
        brackets = self._bracket("COM-IND-X001", status, "ungoverned_grain_xyz")
        issues = validate_evidence_grains(brackets, self.ALLOWED, self.REPO)
        gaps = [i for i in issues if i.code == "evidence_grain.governance_gap"]
        assert len(gaps) == 1, f"expected one governance_gap, got {issues}"
        return gaps[0]

    def test_final_ungoverned_grain_is_error(self):
        assert self._grain_issue("active").severity == "ERROR"

    def test_default_status_is_final(self):
        # status omitted -> treated as final/active -> blocking
        assert self._grain_issue(None).severity == "ERROR"

    def test_draft_ungoverned_grain_is_advisory(self):
        assert self._grain_issue("draft").severity == "WARN"

    def test_draft_placeholder_grain_is_advisory(self):
        brackets = self._bracket("COM-IND-X001", "draft", "transaction_line")
        issues = validate_evidence_grains(brackets, self.ALLOWED, self.REPO)
        ph = [i for i in issues if i.code == "evidence_grain.placeholder_forbidden"]
        assert len(ph) == 1 and ph[0].severity == "WARN"

    def test_governed_grain_passes_in_any_status(self):
        for status in ("active", "draft", None):
            brackets = self._bracket("COM-IND-X001", status, "invoice_line")
            issues = validate_evidence_grains(brackets, self.ALLOWED, self.REPO)
            assert issues == [], f"governed grain should be clean (status={status})"
