"""Tests for the intelligence layer."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ..intelligence.classifier import ErrorCategory, ErrorClassifier
from ..intelligence.suggester import FixSuggester
from ..intelligence.kb import KnowledgeBase, KBEntry
from ..intelligence.telemetry import TelemetryCollector
from ..intelligence.scorer import QualityScorer, QualityScore


# ---------------------------------------------------------------------------
# ErrorClassifier
# ---------------------------------------------------------------------------

class TestErrorClassifier:
    def test_classify_missing_kpi(self):
        clf = ErrorClassifier()
        cat = clf.classify("[MISSING_KPI] KPI 'com.foo.bar' not found in catalog")
        assert cat == ErrorCategory.MISSING_KPI_REF

    def test_classify_missing_action_code(self):
        clf = ErrorClassifier()
        cat = clf.classify("[MISSING_ACTION_CODE] Action code 'C-X1.1' not found")
        assert cat == ErrorCategory.MISSING_ACTION_CODE

    def test_classify_tmdl_syntax(self):
        clf = ErrorClassifier()
        assert clf.classify("invalid indent at column 5 in .tmdl") == ErrorCategory.TMDL_SYNTAX
        assert clf.classify("formatString missing in measure") == ErrorCategory.TMDL_SYNTAX
        assert clf.classify("tabs_only violation") == ErrorCategory.TMDL_SYNTAX

    def test_classify_dax_syntax(self):
        clf = ErrorClassifier()
        assert clf.classify("DAX error: cannot evaluate column") == ErrorCategory.DAX_SYNTAX
        assert clf.classify("invalid expression :=") == ErrorCategory.DAX_SYNTAX

    def test_classify_pbip_structure(self):
        clf = ErrorClassifier()
        assert clf.classify("definition.pbir missing from report") == ErrorCategory.PBIP_STRUCTURE
        assert clf.classify("Required artifact: definition.pbism") == ErrorCategory.PBIP_STRUCTURE

    def test_classify_unknown(self):
        clf = ErrorClassifier()
        assert clf.classify("something completely unrelated xyz") == ErrorCategory.UNKNOWN

    def test_classify_batch(self):
        clf = ErrorClassifier()
        errors = [
            "[MISSING_KPI] ...",
            "invalid indent",
            "another indent error",
        ]
        buckets = clf.classify_batch(errors)
        assert ErrorCategory.MISSING_KPI_REF in buckets
        assert ErrorCategory.TMDL_SYNTAX in buckets
        assert len(buckets[ErrorCategory.TMDL_SYNTAX]) == 2

    def test_top_categories(self):
        clf = ErrorClassifier()
        errors = ["[MISSING_KPI]"] * 5 + ["invalid indent"] * 3 + ["DAX error"] * 1
        top = clf.top_categories(errors, top_n=2)
        assert top[0][0] == ErrorCategory.MISSING_KPI_REF
        assert top[0][1] == 5

    def test_priority_order(self):
        clf = ErrorClassifier()
        categories = [ErrorCategory.UNKNOWN, ErrorCategory.TMDL_SYNTAX, ErrorCategory.MISSING_KPI_REF]
        ordered = clf.priority_order(categories)
        # MISSING_KPI_REF should be before TMDL_SYNTAX, UNKNOWN last
        assert ordered[0] == ErrorCategory.MISSING_KPI_REF
        assert ordered[-1] == ErrorCategory.UNKNOWN


# ---------------------------------------------------------------------------
# KnowledgeBase
# ---------------------------------------------------------------------------

class TestKnowledgeBase:
    def test_load_bundled_kb(self):
        kb = KnowledgeBase()
        assert kb.entry_count() > 0

    def test_lookup_by_tmdl_symptom(self):
        kb = KnowledgeBase()
        entry = kb.lookup("invalid indent at column tmdl")
        assert entry is not None
        assert entry.category == "tmdl_syntax"

    def test_lookup_nonexistent_returns_none(self):
        kb = KnowledgeBase()
        entry = kb.lookup("this_message_does_not_exist_in_kb_xyz_abc_123")
        assert entry is None

    def test_lookup_by_category(self):
        kb = KnowledgeBase()
        entries = kb.lookup_by_category("tmdl_syntax")
        assert len(entries) > 0
        assert all(e.category == "tmdl_syntax" for e in entries)

    def test_append_and_save(self, tmp_path):
        kb_path = tmp_path / "test_errors.yaml"
        kb = KnowledgeBase(kb_path=kb_path, auto_append=False)
        entry = KBEntry(
            id="TEST-001",
            category="tmdl_syntax",
            symptom="test symptom",
            cause="test cause",
            fix="test fix",
            added_date="2026-04-06",
            source="test",
        )
        kb.append(entry)
        assert kb_path.is_file()

        # Reload and verify persistence
        kb2 = KnowledgeBase(kb_path=kb_path)
        found = kb2.lookup("test symptom")
        assert found is not None
        assert found.id == "TEST-001"

    def test_no_duplicate_append(self, tmp_path):
        kb_path = tmp_path / "test_errors.yaml"
        kb = KnowledgeBase(kb_path=kb_path)
        entry = KBEntry(id="DUP-001", category="unknown", symptom="dup",
                        cause="x", fix="y", added_date="2026-04-06", source="test")
        kb.append(entry)
        kb.append(entry)  # Second append should be ignored
        assert len([e for e in kb.all_entries() if e.id == "DUP-001"]) == 1

    def test_append_unknown_creates_skeleton(self, tmp_path):
        kb_path = tmp_path / "test_errors.yaml"
        kb = KnowledgeBase(kb_path=kb_path, auto_append=True)
        entry = kb.append_unknown("brand new unknown error message xyz")
        assert entry is not None
        assert "TODO" in entry.cause or "TODO" in entry.fix

    def test_categories(self):
        kb = KnowledgeBase()
        cats = kb.categories()
        assert "tmdl_syntax" in cats


# ---------------------------------------------------------------------------
# FixSuggester
# ---------------------------------------------------------------------------

class TestFixSuggester:
    def test_suggest_for_known_category(self):
        suggester = FixSuggester()
        fix = suggester.suggest("[MISSING_KPI] ...", ErrorCategory.MISSING_KPI_REF)
        assert fix is not None
        assert fix.category == ErrorCategory.MISSING_KPI_REF
        assert len(fix.description) > 0

    def test_suggest_for_tmdl(self):
        suggester = FixSuggester()
        fix = suggester.suggest("invalid indent in .tmdl", ErrorCategory.TMDL_SYNTAX)
        assert fix.auto_fixable is True
        assert len(fix.commands) > 0

    def test_suggest_for_buckets(self):
        clf = ErrorClassifier()
        suggester = FixSuggester()
        errors = ["[MISSING_KPI] com.foo", "invalid indent in tmdl"]
        buckets = clf.classify_batch(errors)
        fixes = suggester.suggest_for_buckets(buckets)
        assert len(fixes) == 2


# ---------------------------------------------------------------------------
# TelemetryCollector
# ---------------------------------------------------------------------------

class TestTelemetryCollector:
    def test_start_and_complete_run(self, tmp_path):
        tc = TelemetryCollector(runs_dir=tmp_path / "runs")
        run = tc.start_run("COM-001", adapter="pbip")
        assert run.use_case_id == "COM-001"
        assert run.overall_status == "in_progress"

        tc.record_phase(run, "preflight", "pass")
        tc.record_phase(run, "generation", "pass")
        path = tc.complete_run(run, files_generated=15)

        assert path.is_file()
        assert run.overall_status == "success"
        assert run.files_generated == 15

    def test_failed_run_status(self, tmp_path):
        tc = TelemetryCollector(runs_dir=tmp_path / "runs")
        run = tc.start_run("COM-002", adapter="pbip")
        tc.record_phase(run, "preflight", "fail", errors=["[MISSING_KPI] x"])
        tc.complete_run(run)
        assert run.overall_status == "failure"
        assert run.error_count == 1

    def test_partial_run_status(self, tmp_path):
        tc = TelemetryCollector(runs_dir=tmp_path / "runs")
        run = tc.start_run("COM-003", adapter="pbip")
        tc.record_phase(run, "preflight", "pass")
        tc.record_phase(run, "generation", "fail", errors=["some error"])
        tc.complete_run(run)
        assert run.overall_status == "partial"

    def test_load_runs(self, tmp_path):
        tc = TelemetryCollector(runs_dir=tmp_path / "runs")
        for i in range(3):
            run = tc.start_run(f"COM-00{i+1}", adapter="pbip")
            tc.record_phase(run, "generation", "pass")
            tc.complete_run(run)

        runs = tc.load_runs()
        assert len(runs) == 3

    def test_success_rate(self, tmp_path):
        tc = TelemetryCollector(runs_dir=tmp_path / "runs")
        # 2 successes, 1 failure
        for i in range(2):
            run = tc.start_run("COM-001", adapter="pbip")
            tc.record_phase(run, "gen", "pass")
            tc.complete_run(run)
        run = tc.start_run("COM-001", adapter="pbip")
        tc.record_phase(run, "gen", "fail", errors=["err"])
        tc.complete_run(run)

        rate = tc.success_rate("COM-001")
        assert abs(rate - 2/3) < 0.01

    def test_summary_stats(self, tmp_path):
        tc = TelemetryCollector(runs_dir=tmp_path / "runs")
        run = tc.start_run("COM-001", adapter="pbip")
        tc.record_phase(run, "gen", "pass")
        tc.complete_run(run)

        stats = tc.summary_stats()
        assert stats["total_runs"] == 1
        assert stats["success_rate"] == 1.0


# ---------------------------------------------------------------------------
# QualityScorer
# ---------------------------------------------------------------------------

class TestQualityScorer:
    def test_score_returns_quality_score(self, tmp_path):
        import yaml as _yaml
        bracket = {
            "id": "COM-001",
            "primary_kpi_ids": ["com.sales.net_sales_amount"],
            "ux_layout_rules": {
                "page_1_summary": {"component_30s": []},
                "page_2_execution": {"component_300s": {}},
            },
        }
        bp = tmp_path / "COM-001_test" / "UseCase_Bracket.yaml"
        bp.parent.mkdir(parents=True)
        bp.write_text(_yaml.dump(bracket))

        scorer = QualityScorer()
        score = scorer.score(bracket_path=bp)
        assert isinstance(score, QualityScore)
        assert 0.0 <= score.overall <= 1.0

    def test_grade_mapping(self):
        assert QualityScore(overall=0.97, use_case_id="X").grade() == "A"
        assert QualityScore(overall=0.87, use_case_id="X").grade() == "B"
        assert QualityScore(overall=0.72, use_case_id="X").grade() == "C"
        assert QualityScore(overall=0.52, use_case_id="X").grade() == "D"
        assert QualityScore(overall=0.30, use_case_id="X").grade() == "F"

    def test_to_dict_serialisable(self, tmp_path):
        import json
        import yaml as _yaml
        bracket = {
            "id": "COM-001",
            "primary_kpi_ids": [],
            "ux_layout_rules": {},
        }
        bp = tmp_path / "bracket.yaml"
        bp.write_text(_yaml.dump(bracket))
        scorer = QualityScorer()
        score = scorer.score(bracket_path=bp)
        d = score.to_dict()
        assert json.dumps(d)  # must be JSON-serialisable
