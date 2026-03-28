"""Tests for tooling/health_scorecard.py"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure tooling/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from health_scorecard import (
    _extract_section,
    _scan_action_code_kpi_refs,
    _scan_measure_dictionaries_for_kpis,
    compute_h1,
    compute_h2,
    compute_h3,
    compute_h4,
    compute_h5,
    run_scorecard,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_repo(tmp_path):
    """Create a minimal repo layout for testing."""
    # KPI catalog (not used directly but referenced via registry)
    (tmp_path / "core" / "kpi_catalog").mkdir(parents=True)

    # Action codes
    ac_dir = tmp_path / "core" / "action_codes" / "Commercial"
    ac_dir.mkdir(parents=True)

    # Measure dictionaries
    md_dir = tmp_path / "core" / "semantic_models" / "domains" / "commercial"
    md_dir.mkdir(parents=True)

    # Use case factsheets
    uc_dir = tmp_path / "core" / "usecases" / "core" / "COM-001_Sales_Performance"
    uc_dir.mkdir(parents=True)

    # VERSION
    (tmp_path / "VERSION").write_text("0.0.1-test")

    return tmp_path


@pytest.fixture
def sample_registry():
    """Minimal registry for testing."""
    return {
        "objects": {
            "kpis": {
                "sales.net_sales.amount": {
                    "kpi_role": "strategic",
                    "linked_domain_contracts": ["commercial_sales"],
                },
                "sales.growth.pct": {
                    "kpi_role": "strategic",
                    "linked_domain_contracts": [],
                },
                "ops.efficiency.ratio": {
                    "kpi_role": "operational",
                    "linked_domain_contracts": ["operations"],
                },
            },
            "use_cases": {
                "COM-001": {"orchestration": {"required_facts": ["fact_sales"]}},
            },
        },
        "edges": [
            {"type": "use_case_strategic_kpi", "from": "COM-001", "to": "sales.net_sales.amount"},
            {"type": "use_case_strategic_kpi", "from": "COM-001", "to": "sales.growth.pct"},
        ],
        "issues": [],
    }


# ---------------------------------------------------------------------------
# H1 — Golden Thread Coverage
# ---------------------------------------------------------------------------

class TestComputeH1:
    def test_empty_registry(self):
        result = compute_h1({"objects": {"kpis": {}}, "edges": []}, Path("/nonexistent"))
        assert result["score"] == 0.0
        assert result["status"] == "no_data"

    def test_partial_coverage(self, tmp_repo, sample_registry):
        # Create measure dictionary with one KPI ref
        md_file = tmp_repo / "core" / "semantic_models" / "domains" / "commercial" / "Measure_Dictionary_Commercial.md"
        md_file.write_text(textwrap.dedent("""\
            ```yaml
            - measure_name: Net Sales
              kpi_id_ref: sales.net_sales.amount
              governance:
                status: active
            ```
        """))

        # Create action code referencing one KPI
        ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / "C-M1.1.yaml"
        import yaml
        ac_data = {
            "id": "C-M1.1",
            "trigger": {"type": "threshold", "evaluation": {"levels": [{"level": "warning"}]}},
            "impact": {"category": "revenue"},
            "operational_execution": {"steps": ["step1"]},
            "kpis": {"trigger_kpis": ["sales.net_sales.amount"], "guardrail_kpis": [], "outcome_kpis": []},
        }
        ac_file.write_text(yaml.dump(ac_data))

        result = compute_h1(sample_registry, tmp_repo)
        # sales.net_sales.amount: all 5 layers present (catalog, bracket, measure_dict, data_contract, action_code)
        # sales.growth.pct: missing measure_dict, data_contract, action_code
        assert result["details"]["strategic_kpis"] == 2
        assert result["details"]["covered"] == 1
        assert result["score"] == 50.0

    def test_full_coverage(self, tmp_repo, sample_registry):
        # Give sales.growth.pct a data contract
        sample_registry["objects"]["kpis"]["sales.growth.pct"]["linked_domain_contracts"] = ["commercial_sales"]

        # Create measure dictionary referencing both KPIs
        md_file = tmp_repo / "core" / "semantic_models" / "domains" / "commercial" / "Measure_Dictionary_Commercial.md"
        md_file.write_text(textwrap.dedent("""\
            ```yaml
            - measure_name: Net Sales
              kpi_id_ref: sales.net_sales.amount
            - measure_name: Sales Growth
              kpi_id_ref: sales.growth.pct
            ```
        """))

        # Action codes for both KPIs
        import yaml
        for idx, kpi in enumerate(["sales.net_sales.amount", "sales.growth.pct"]):
            ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / f"C-M{idx+1}.1.yaml"
            ac_file.write_text(yaml.dump({
                "id": f"C-M{idx+1}.1",
                "trigger": {"type": "threshold", "evaluation": {"levels": []}},
                "impact": {"category": "revenue"},
                "operational_execution": {"steps": ["step1"]},
                "kpis": {"trigger_kpis": [kpi]},
            }))

        result = compute_h1(sample_registry, tmp_repo)
        assert result["details"]["covered"] == 2
        assert result["score"] == 100.0
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# Measure Dictionary Scanner
# ---------------------------------------------------------------------------

class TestScanMeasureDictionaries:
    def test_finds_kpi_id_ref(self, tmp_repo):
        md_file = tmp_repo / "core" / "semantic_models" / "domains" / "commercial" / "Measure_Dictionary_Commercial.md"
        md_file.write_text(textwrap.dedent("""\
            ```yaml
            - measure_name: Net Sales
              kpi_id_ref: sales.net_sales.amount
              is_kpi_measure: true
            - measure_name: Helper Measure
              is_kpi_measure: false
            - measure_name: Growth Rate
              kpi_id_ref: sales.growth.pct
            ```
        """))
        result = _scan_measure_dictionaries_for_kpis(tmp_repo)
        assert result == {"sales.net_sales.amount", "sales.growth.pct"}

    def test_empty_dir(self, tmp_repo):
        result = _scan_measure_dictionaries_for_kpis(tmp_repo)
        assert result == set()

    def test_nonexistent_dir(self, tmp_path):
        result = _scan_measure_dictionaries_for_kpis(tmp_path / "no_such_repo")
        assert result == set()


# ---------------------------------------------------------------------------
# Action Code Scanner
# ---------------------------------------------------------------------------

class TestScanActionCodeKpiRefs:
    def test_finds_all_kpi_types(self, tmp_repo):
        import yaml
        ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / "C-M1.1.yaml"
        ac_file.write_text(yaml.dump({
            "id": "C-M1.1",
            "kpis": {
                "trigger_kpis": ["sales.net_sales.amount"],
                "guardrail_kpis": ["sales.margin.pct"],
                "outcome_kpis": ["sales.growth.pct"],
            },
        }))
        result = _scan_action_code_kpi_refs(tmp_repo)
        assert result == {"sales.net_sales.amount", "sales.margin.pct", "sales.growth.pct"}

    def test_skips_decision_spines(self, tmp_repo):
        ds_dir = tmp_repo / "core" / "action_codes" / "Commercial" / "decision_spines"
        ds_dir.mkdir()
        (ds_dir / "DecisionSpine_COM.yaml").write_text("id: DEC-SPINE-COM\nkpis:\n  trigger_kpis:\n    - should.not.appear")
        result = _scan_action_code_kpi_refs(tmp_repo)
        assert result == set()

    def test_empty_kpis(self, tmp_repo):
        import yaml
        ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / "C-M1.1.yaml"
        ac_file.write_text(yaml.dump({
            "id": "C-M1.1",
            "kpis": {"trigger_kpis": [], "guardrail_kpis": [], "outcome_kpis": []},
        }))
        result = _scan_action_code_kpi_refs(tmp_repo)
        assert result == set()


# ---------------------------------------------------------------------------
# H2 — Semantic Model Stability
# ---------------------------------------------------------------------------

class TestComputeH2:
    def test_all_active(self, tmp_repo):
        md_file = tmp_repo / "core" / "semantic_models" / "domains" / "commercial" / "Measure_Dictionary_Commercial.md"
        md_file.write_text(textwrap.dedent("""\
            ```yaml
            - measure_name: M1
              governance:
                status: active
            - measure_name: M2
              governance:
                status: active
            ```
        """))
        result = compute_h2(tmp_repo)
        assert result["score"] == 100.0
        assert result["details"]["active"] == 2

    def test_mixed_status(self, tmp_repo):
        md_file = tmp_repo / "core" / "semantic_models" / "domains" / "commercial" / "Measure_Dictionary_Commercial.md"
        md_file.write_text(textwrap.dedent("""\
            ```yaml
            - measure_name: M1
              governance:
                status: active
            - measure_name: M2
              governance:
                status: draft
            - measure_name: M3
              governance:
                status: active
            ```
        """))
        result = compute_h2(tmp_repo)
        assert result["details"]["total_measures"] == 3
        assert result["details"]["active"] == 2
        assert abs(result["score"] - 66.7) < 0.1

    def test_no_measures(self, tmp_repo):
        result = compute_h2(tmp_repo)
        assert result["score"] == 0.0


# ---------------------------------------------------------------------------
# H3 — Data Contract Coverage
# ---------------------------------------------------------------------------

class TestComputeH3:
    def test_no_issues(self, sample_registry):
        result = compute_h3(sample_registry)
        assert result["score"] == 100.0

    def test_with_evidence_issues(self, sample_registry):
        sample_registry["issues"] = [
            {"code": "evidence_grain_missing", "use_case": "COM-001"},
        ]
        # Clear required_facts to trigger fallback path
        sample_registry["objects"]["use_cases"]["COM-001"]["orchestration"]["required_facts"] = []
        result = compute_h3(sample_registry)
        assert result["details"]["evidence_grain_issues"] == 1


# ---------------------------------------------------------------------------
# H4 — Action Code Completeness
# ---------------------------------------------------------------------------

class TestComputeH4:
    def test_complete_action_code(self, tmp_repo):
        import yaml
        ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / "C-M1.1.yaml"
        ac_file.write_text(yaml.dump({
            "id": "C-M1.1",
            "trigger": {"type": "threshold", "evaluation": {"levels": [{"level": "critical"}]}},
            "impact": {"category": "revenue", "expected_range": "1-5%"},
            "operational_execution": {"steps": ["Review pricing", "Adjust"]},
            "kpis": {"trigger_kpis": ["sales.net_sales.amount"]},
        }))
        result = compute_h4(tmp_repo)
        assert result["score"] == 100.0
        assert result["details"]["complete"] == 1

    def test_incomplete_action_code(self, tmp_repo):
        import yaml
        ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / "C-M1.1.yaml"
        ac_file.write_text(yaml.dump({
            "id": "C-M1.1",
            "trigger": {"type": "threshold", "evaluation": {"levels": []}},
            "impact": {"category": "revenue"},
            # Missing operational_execution and trigger_kpis
            "kpis": {"trigger_kpis": []},
        }))
        result = compute_h4(tmp_repo)
        assert result["score"] == 0.0
        assert "operational_execution" in result["details"]["incomplete"]["C-M1.1"]
        assert "trigger_kpis" in result["details"]["incomplete"]["C-M1.1"]

    def test_skips_decision_spines(self, tmp_repo):
        ds_dir = tmp_repo / "core" / "action_codes" / "Commercial" / "decision_spines"
        ds_dir.mkdir()
        (ds_dir / "DecisionSpine_COM.yaml").write_text("id: DEC-SPINE-COM\n")
        result = compute_h4(tmp_repo)
        assert result["details"]["total_action_codes"] == 0

    def test_no_action_codes_dir(self, tmp_path):
        result = compute_h4(tmp_path)
        assert result["status"] == "no_data"


# ---------------------------------------------------------------------------
# H5 — Factsheet Quality Score
# ---------------------------------------------------------------------------

class TestComputeH5:
    def test_perfect_factsheet(self, tmp_repo):
        fs = tmp_repo / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "Business_Factsheet.md"
        fs.write_text(textwrap.dedent("""\
            # COM-001 Sales Performance

            ## 1. Business Summary

            This use case tracks net sales performance across all regions.

            ## 2. Core Business Questions

            - What is the current net sales trend?
            - Which regions are underperforming?
            - What actions should be taken for declining markets?
            - How does seasonality affect sales?

            ## 5. 3-30-300 Page Layout

            KPI cards: Net Sales, Growth Rate, Margin %
            Visual: Line chart showing monthly trend
            Visual: Bar chart by region
            Visual: Waterfall of period-over-period

            ## 8. Success Criteria

            Impact: 5% reduction in decision latency
            Adoption: 80% of regional managers using within 3 months

            ## 10. Decision Scenarios

            ### Scenario 1: Declining Sales
            Trigger: Net sales < target by 5%

            ### Scenario 2: Growth Opportunity
            Trigger: Market share increase > 2%
        """))
        result = compute_h5(tmp_repo)
        assert result["score"] == 100.0
        assert result["details"]["per_factsheet"]["COM-001"] == 5

    def test_minimal_factsheet(self, tmp_repo):
        fs = tmp_repo / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "Business_Factsheet.md"
        fs.write_text(textwrap.dedent("""\
            # COM-001

            ## 1. Business Summary

            TBD

            ## 2. Core Business Questions

            - What?
        """))
        result = compute_h5(tmp_repo)
        assert result["details"]["per_factsheet"]["COM-001"] == 0

    def test_no_factsheets(self, tmp_path):
        result = compute_h5(tmp_path)
        assert result["status"] == "no_data"


# ---------------------------------------------------------------------------
# _extract_section
# ---------------------------------------------------------------------------

class TestExtractSection:
    def test_extracts_numbered_section(self):
        content = "## 1. Intro\nHello\n## 2. Details\nWorld\n## 3. End\nBye"
        assert "Hello" in _extract_section(content, 1)
        assert "World" in _extract_section(content, 2)

    def test_returns_none_for_missing(self):
        assert _extract_section("## 1. Intro\nHello", 5) is None

    def test_last_section_gets_rest(self):
        content = "## 1. Intro\nA\n## 2. Details\nB\nC\nD"
        section = _extract_section(content, 2)
        assert "B" in section
        assert "D" in section


# ---------------------------------------------------------------------------
# run_scorecard integration
# ---------------------------------------------------------------------------

class TestRunScorecard:
    def test_runs_against_real_repo(self):
        """Integration test: runs against the actual repository."""
        repo_root = Path(__file__).resolve().parents[2]
        registry_path = repo_root / "tooling" / "ontology" / "out" / "master_registry.json"
        if not registry_path.exists():
            pytest.skip("master_registry.json not found — run registry_builder.py first")
        results = run_scorecard(repo_root)
        assert "metrics" in results
        assert len(results["metrics"]) == 5
        for m in results["metrics"]:
            assert "score" in m
            assert "target" in m
            assert 0.0 <= m["score"] <= 100.0

    def test_json_output_format(self):
        repo_root = Path(__file__).resolve().parents[2]
        registry_path = repo_root / "tooling" / "ontology" / "out" / "master_registry.json"
        if not registry_path.exists():
            pytest.skip("master_registry.json not found")
        results = run_scorecard(repo_root)
        # Verify JSON-serializable
        output = json.dumps(results)
        parsed = json.loads(output)
        assert parsed["meta"]["version"] != "unknown"
        assert "generated_at_utc" in parsed["meta"]
