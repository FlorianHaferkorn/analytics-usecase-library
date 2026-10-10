"""
Tests for design_rules_enforcer (R2.3, Cut C2)

Covers both DoD-required directions: a violating Bracket/output produces an
error string carrying the correct rule ID, and a conformant Bracket/output
produces zero errors. Also regression-checks the real design_rules.yaml (5
rules) and the real, now-migrated COM-002 Bracket end-to-end.

Run with: python -m pytest tests/test_design_rules_enforcer.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from page_scaffold_generator import design_rules_enforcer as dre
from page_scaffold_generator.config_loader import ConfigLoader

REPO_ROOT = Path(__file__).resolve().parents[6]  # -> analytics-usecase-library


# ---------------------------------------------------------------------------
# design_rules.yaml loading
# ---------------------------------------------------------------------------

class TestLoadDesignRules:
    def test_loads_five_real_rules(self):
        rules = dre.load_design_rules()
        ids = {r["id"] for r in rules}
        assert ids == {
            "ONE_MESSAGE_PER_CHART",
            "MAX_SEMANTIC_COLORS_PER_PAGE",
            "MAX_EVIDENCE_COLUMNS",
            "MANDATORY_SORT_RENDERED",
            "BIG_IDEA_HEADER_ZONE",
        }

    def test_missing_file_returns_empty_list(self, tmp_path):
        rules = dre.load_design_rules(tmp_path / "does_not_exist.yaml")
        assert rules == []


# ---------------------------------------------------------------------------
# check_bracket_rules -- gating on intent_rules_version
# ---------------------------------------------------------------------------

class TestBracketRulesGating:
    def test_noop_when_intent_rules_version_not_2(self):
        rules = dre.load_design_rules()
        bracket = {"ux_layout_rules": {"page_1_summary": {"component_30s": [
            {"slot_id": "Main_1", "unit": "amount", "kpi_id": "KPI-COM-013"},
        ]}}}
        errors = dre.check_bracket_rules(rules, bracket, {"KPI-COM-013": "ratio"})
        assert errors == []

    def test_noop_when_ux_layout_rules_missing(self):
        rules = dre.load_design_rules()
        errors = dre.check_bracket_rules(rules, {}, {})
        assert errors == []


# ---------------------------------------------------------------------------
# ONE_MESSAGE_PER_CHART
# ---------------------------------------------------------------------------

class TestOneMessagePerChart:
    RULE = next(r for r in dre.load_design_rules() if r["id"] == "ONE_MESSAGE_PER_CHART")

    def test_violation_flags_mismatched_calc_type(self):
        component_30s = [
            {"slot_id": "Main_3", "unit": "amount", "kpi_id": "KPI-COM-013"},
        ]
        errors = dre.check_single_unit_family_per_component(
            self.RULE, component_30s, {"KPI-COM-013": "ratio"}
        )
        assert len(errors) == 1
        assert errors[0].startswith("ONE_MESSAGE_PER_CHART:")
        assert "KPI-COM-013" in errors[0]

    def test_conformant_when_calc_type_matches_unit(self):
        component_30s = [
            {"slot_id": "Main_3", "unit": "ratio", "kpi_id": "KPI-COM-013"},
        ]
        errors = dre.check_single_unit_family_per_component(
            self.RULE, component_30s, {"KPI-COM-013": "ratio"}
        )
        assert errors == []

    def test_unknown_kpi_id_is_skipped_not_a_violation(self):
        """kpi_ids not found in the catalog (e.g. a raw measure name) are
        skipped, not treated as violations -- e.g. Main_2's "Plan GM Amount"."""
        component_30s = [
            {"slot_id": "Main_2", "unit": "amount", "kpi_ids": ["Plan GM Amount", "KPI-COM-019"]},
        ]
        errors = dre.check_single_unit_family_per_component(
            self.RULE, component_30s, {"KPI-COM-019": "amount"}
        )
        assert errors == []

    def test_entry_without_unit_is_skipped(self):
        component_30s = [{"slot_id": "Main_1", "kpi_id": "KPI-COM-013"}]
        errors = dre.check_single_unit_family_per_component(
            self.RULE, component_30s, {"KPI-COM-013": "ratio"}
        )
        assert errors == []


# ---------------------------------------------------------------------------
# MAX_EVIDENCE_COLUMNS / MAX_SEMANTIC_COLORS_PER_PAGE (max_count)
# ---------------------------------------------------------------------------

class TestMaxCount:
    RULES = dre.load_design_rules()
    EVIDENCE_RULE = next(r for r in RULES if r["id"] == "MAX_EVIDENCE_COLUMNS")

    def test_violation_over_max(self):
        errors = dre.check_max_count(self.EVIDENCE_RULE, 9)
        assert len(errors) == 1
        assert errors[0].startswith("MAX_EVIDENCE_COLUMNS:")
        assert "9" in errors[0] and "8" in errors[0]

    def test_conformant_at_max(self):
        assert dre.check_max_count(self.EVIDENCE_RULE, 8) == []

    def test_conformant_under_max(self):
        assert dre.check_max_count(self.EVIDENCE_RULE, 3) == []

    def test_check_bracket_rules_flags_too_many_evidence_columns(self):
        bracket = {
            "ux_layout_rules": {
                "intent_rules_version": 2,
                "page_1_summary": {"component_30s": []},
                "page_2_execution": {"component_300s": {"evidence_columns": [f"col_{i}" for i in range(9)]}},
            }
        }
        errors = dre.check_bracket_rules(self.RULES, bracket, {})
        assert any(e.startswith("MAX_EVIDENCE_COLUMNS:") for e in errors)

    def test_check_bracket_rules_conformant_evidence_columns(self):
        bracket = {
            "ux_layout_rules": {
                "intent_rules_version": 2,
                "page_1_summary": {"component_30s": []},
                "page_2_execution": {"component_300s": {"evidence_columns": [f"col_{i}" for i in range(7)]}},
            }
        }
        errors = dre.check_bracket_rules(self.RULES, bracket, {})
        assert not any(e.startswith("MAX_EVIDENCE_COLUMNS:") for e in errors)


# ---------------------------------------------------------------------------
# MANDATORY_SORT_RENDERED
# ---------------------------------------------------------------------------

class TestMandatorySortRendered:
    RULE = next(r for r in dre.load_design_rules() if r["id"] == "MANDATORY_SORT_RENDERED")
    SORT_BY = {"measure": "Gross Margin % vs Plan", "direction": "ascending"}

    def test_noop_when_no_sort_by_declared(self):
        assert dre.check_output_matches_declared_sort(self.RULE, None, None) == []

    def test_violation_when_no_visual_generated(self):
        errors = dre.check_output_matches_declared_sort(self.RULE, self.SORT_BY, None)
        assert len(errors) == 1
        assert errors[0].startswith("MANDATORY_SORT_RENDERED:")

    def test_violation_when_sort_definition_missing(self):
        visual = {"visual": {"query": {}}}
        errors = dre.check_output_matches_declared_sort(self.RULE, self.SORT_BY, visual)
        assert len(errors) == 1
        assert errors[0].startswith("MANDATORY_SORT_RENDERED:")

    def test_violation_when_rendered_measure_differs(self):
        visual = {
            "visual": {
                "query": {
                    "sortDefinition": {
                        "sort": [{"field": {"Measure": {"Property": "Some Other Measure"}}}],
                        "isDefaultSort": True,
                    }
                }
            }
        }
        errors = dre.check_output_matches_declared_sort(self.RULE, self.SORT_BY, visual)
        assert len(errors) == 1
        assert "Some Other Measure" in errors[0]

    def test_conformant_when_rendered_matches_declared(self):
        visual = {
            "visual": {
                "query": {
                    "sortDefinition": {
                        "sort": [{"field": {"Measure": {"Property": "Gross Margin % vs Plan"}}}],
                        "isDefaultSort": True,
                    }
                }
            }
        }
        errors = dre.check_output_matches_declared_sort(self.RULE, self.SORT_BY, visual)
        assert errors == []


# ---------------------------------------------------------------------------
# BIG_IDEA_HEADER_ZONE
# ---------------------------------------------------------------------------

class TestBigIdeaHeaderZone:
    RULE = next(r for r in dre.load_design_rules() if r["id"] == "BIG_IDEA_HEADER_ZONE")
    BIG_IDEA = "Gross Margin is under pressure."

    def _header(self, text: str) -> dict:
        return {
            "name": "Header",
            "visual": {"objects": {"text": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{text}'"}}}}}]}},
        }

    def test_noop_when_no_big_idea_declared(self):
        assert dre.check_header_text_equals_big_idea(self.RULE, None, []) == []

    def test_violation_when_no_header_visual(self):
        errors = dre.check_header_text_equals_big_idea(self.RULE, self.BIG_IDEA, [])
        assert len(errors) == 1
        assert errors[0].startswith("BIG_IDEA_HEADER_ZONE:")

    def test_violation_when_text_differs(self):
        errors = dre.check_header_text_equals_big_idea(
            self.RULE, self.BIG_IDEA, [self._header("Something else entirely")]
        )
        assert len(errors) == 1
        assert errors[0].startswith("BIG_IDEA_HEADER_ZONE:")

    def test_conformant_when_text_matches_verbatim(self):
        errors = dre.check_header_text_equals_big_idea(
            self.RULE, self.BIG_IDEA, [self._header(self.BIG_IDEA)]
        )
        assert errors == []

    @staticmethod
    def _paragraph_header(text: str) -> dict:
        """PBIR textbox shape the generator emits since 07.10.2026 (general.paragraphs)."""
        return {
            "name": "Header",
            "visual": {"objects": {"general": [{"properties": {
                "paragraphs": [{"textRuns": [{"value": text}]}]}}]}},
        }

    def test_conformant_with_paragraph_textbox(self):
        errors = dre.check_header_text_equals_big_idea(
            self.RULE, self.BIG_IDEA, [self._paragraph_header("Q?  ·  Expected finding — " + self.BIG_IDEA)]
        )
        assert errors == []

    def test_violation_with_paragraph_textbox_text_differs(self):
        errors = dre.check_header_text_equals_big_idea(
            self.RULE, self.BIG_IDEA, [self._paragraph_header("Something else entirely")]
        )
        assert len(errors) == 1 and errors[0].startswith("BIG_IDEA_HEADER_ZONE:")


# ---------------------------------------------------------------------------
# Real-data regression: COM-002 is the migrated, conformant reference Bracket
# ---------------------------------------------------------------------------

class TestCOM002RealBracketIsConformant:
    def test_com002_bracket_passes_all_pre_generation_rules(self):
        loader = ConfigLoader(REPO_ROOT)
        bracket = loader.load_use_case_bracket("COM-002")
        kpi_id_to_calc_type = loader.load_kpi_id_to_calc_type_map()
        rules = dre.load_design_rules()

        errors = dre.check_bracket_rules(rules, bracket, kpi_id_to_calc_type)
        assert errors == [], f"Reference Bracket COM-002 must be design-rule-clean: {errors}"

    def test_com002_bracket_opted_into_intent_rules_version_2(self):
        loader = ConfigLoader(REPO_ROOT)
        bracket = loader.load_use_case_bracket("COM-002")
        assert bracket["ux_layout_rules"]["intent_rules_version"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
