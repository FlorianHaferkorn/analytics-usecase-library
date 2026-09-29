"""Tests for tooling/health_scorecard.py"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from health_scorecard import (
    _extract_section,
    _scan_action_code_kpi_refs,
    _scan_measure_dictionaries_for_kpis,
    compute_h1,
    compute_h2,
    compute_h3,
    compute_h4,
    compute_h5,
    compute_h8,
    compute_h9,
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
    (tmp_path / "VERSION").write_text("0.0.1-test", encoding="utf-8")

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
        """), encoding="utf-8")

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
        ac_file.write_text(yaml.dump(ac_data), encoding="utf-8")

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
        """), encoding="utf-8")

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
            }), encoding="utf-8")

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
        """), encoding="utf-8")
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
        }), encoding="utf-8")
        result = _scan_action_code_kpi_refs(tmp_repo)
        assert result == {"sales.net_sales.amount", "sales.margin.pct", "sales.growth.pct"}

    def test_skips_decision_spines(self, tmp_repo):
        ds_dir = tmp_repo / "core" / "action_codes" / "Commercial" / "decision_spines"
        ds_dir.mkdir()
        (ds_dir / "DecisionSpine_COM.yaml").write_text("id: DEC-SPINE-COM\nkpis:\n  trigger_kpis:\n    - should.not.appear", encoding="utf-8")
        result = _scan_action_code_kpi_refs(tmp_repo)
        assert result == set()

    def test_empty_kpis(self, tmp_repo):
        import yaml
        ac_file = tmp_repo / "core" / "action_codes" / "Commercial" / "C-M1.1.yaml"
        ac_file.write_text(yaml.dump({
            "id": "C-M1.1",
            "kpis": {"trigger_kpis": [], "guardrail_kpis": [], "outcome_kpis": []},
        }), encoding="utf-8")
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
        """), encoding="utf-8")
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
        """), encoding="utf-8")
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
        }), encoding="utf-8")
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
        }), encoding="utf-8")
        result = compute_h4(tmp_repo)
        assert result["score"] == 0.0
        assert "operational_execution" in result["details"]["incomplete"]["C-M1.1"]
        assert "trigger_kpis" in result["details"]["incomplete"]["C-M1.1"]

    def test_skips_decision_spines(self, tmp_repo):
        ds_dir = tmp_repo / "core" / "action_codes" / "Commercial" / "decision_spines"
        ds_dir.mkdir()
        (ds_dir / "DecisionSpine_COM.yaml").write_text("id: DEC-SPINE-COM\n", encoding="utf-8")
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
        """), encoding="utf-8")
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
        """), encoding="utf-8")
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
# H8 — AI-Readiness / Linguistic Coverage
# ---------------------------------------------------------------------------

class TestComputeH8:
    """H8 gates governed synonyms reaching the model linguistic schema."""

    def test_passes_on_real_commercial(self):
        """Every governed synonym across the enriched domains is in the linguistic schema."""
        repo_root = Path(__file__).resolve().parents[2]
        result = compute_h8(repo_root)
        assert result["metric"] == "H8"
        assert result["status"] == "pass"
        assert result["score"] == 100.0
        # All governed synonyms present (count grows as domains are enriched, so don't hardcode).
        assert result["details"]["present"] == result["details"]["governed_synonyms"]
        assert result["details"]["governed_synonyms"] >= 7  # Commercial alone contributes 7
        assert "Commercial" in result["details"]["domains"]
        # Epic C: hygiene folded into the gate, clean across the enriched domains
        hyg = result["details"]["hygiene"]
        assert hyg["visible_keys"] == {} and hyg["weak_descriptions"] == {}

    def test_consumer_is_copilot_after_qna_retirement(self):
        """W3.3: Q&A ends Feb 2027; H8 names Copilot as its consumer, with dated Learn evidence."""
        repo_root = Path(__file__).resolve().parents[2]
        details = compute_h8(repo_root)["details"]
        assert details["consumers"] == ["copilot"]
        assert details["evidence"]["qna_end"] == "2027-02"
        assert details["evidence"]["checked"] == "2026-09-29"
        assert all(u.startswith("https://learn.microsoft.com/") for u in details["evidence"]["sources"])

    def test_red_when_a_visible_key_is_reintroduced(self, tmp_path):
        # Coverage is complete, but a visible surrogate key fails the hygiene half.
        self._seed(tmp_path, ["Sales Region", "Geo"])
        tdir = tmp_path / "products" / "fabric" / "powerbi" / "dist" / "Commercial.SemanticModel" / "definition" / "tables"
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "fact_x.tmdl").write_text(
            "table fact_x\n\tcolumn OrgKey\n\t\tdataType: int64\n\t\tsourceColumn: OrgKey\n",
            encoding="utf-8",
        )
        result = compute_h8(tmp_path)
        assert result["status"] == "below_target"
        assert result["details"]["hygiene"]["visible_keys"]["Commercial"] == ["fact_x.OrgKey"]

    def _seed(self, root: Path, culture_synonyms):
        """Write a Commercial contract (Region has 2 synonyms) and a culture file whose
        Region entity carries `culture_synonyms`."""
        contracts = root / "core" / "data_contracts" / "domains"
        contracts.mkdir(parents=True)
        (contracts / "commercial_sales.yaml").write_text(
            "domain: commercial_sales\n"
            "dimension:\n"
            "  - name: dim_org\n"
            "    columns:\n"
            "      - {name: Region, type: text, synonyms: [Sales Region, Geo]}\n"
            "fact: []\n",
            encoding="utf-8",
        )
        from tooling.generator_core.ai_description import ColumnDescription, TableDescription
        from products.fabric.powerbi.tooling.linguistic_schema import (
            build_linguistic_schema, render_culture_tmdl,
        )
        tables = [TableDescription(
            name="dim_org",
            columns=[ColumnDescription(name="Region", synonyms=list(culture_synonyms))],
        )]
        cdir = root / "products" / "fabric" / "powerbi" / "dist" / "Commercial.SemanticModel" / "definition" / "cultures"
        cdir.mkdir(parents=True)
        (cdir / "en-US.tmdl").write_text(
            render_culture_tmdl(build_linguistic_schema(tables)), encoding="utf-8"
        )

    def test_pass_when_all_synonyms_present(self, tmp_path):
        self._seed(tmp_path, ["Sales Region", "Geo"])
        result = compute_h8(tmp_path)
        assert result["status"] == "pass"
        assert (result["details"]["present"], result["details"]["governed_synonyms"]) == (2, 2)

    def test_red_when_governed_synonym_dropped(self, tmp_path):
        # Contract governs [Sales Region, Geo]; culture only carries [Sales Region].
        self._seed(tmp_path, ["Sales Region"])
        result = compute_h8(tmp_path)
        assert result["status"] == "below_target"
        assert result["score"] < 100.0
        assert result["details"]["missing"]["Commercial:dim_org.Region"] == ["Geo"]

    def test_red_when_culture_file_absent(self, tmp_path):
        # Governed synonyms exist but no linguistic schema was emitted at all.
        contracts = tmp_path / "core" / "data_contracts" / "domains"
        contracts.mkdir(parents=True)
        (contracts / "commercial_sales.yaml").write_text(
            "domain: c\ndimension:\n  - name: dim_org\n    columns:\n"
            "      - {name: Region, type: text, synonyms: [Sales Region, Geo]}\nfact: []\n",
            encoding="utf-8",
        )
        result = compute_h8(tmp_path)
        assert result["status"] == "below_target"
        assert result["details"]["present"] == 0


# ---------------------------------------------------------------------------
# run_scorecard integration
# ---------------------------------------------------------------------------

class TestRunScorecard:
    @staticmethod
    def _ensure_registry(repo_root: Path) -> None:
        """Generate master_registry.json if not present (output dir is in .gitignore)."""
        registry_path = repo_root / "tooling" / "ontology" / "out" / "master_registry.json"
        if not registry_path.exists():
            import subprocess, sys
            result = subprocess.run(
                [sys.executable, str(repo_root / "tooling" / "ontology" / "registry_builder.py"),
                 "--repo-root", str(repo_root)],
                capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace")
            if result.returncode != 0 or not registry_path.exists():
                pytest.skip(f"registry_builder.py failed: {result.stderr[:200]}")

    def test_runs_against_real_repo(self):
        """Integration test: runs against the actual repository."""
        repo_root = Path(__file__).resolve().parents[2]
        self._ensure_registry(repo_root)
        results = run_scorecard(repo_root)
        assert "metrics" in results
        assert len(results["metrics"]) == 9
        assert {m["metric"] for m in results["metrics"]} >= {"H1", "H7", "H8", "H9"}
        for m in results["metrics"]:
            assert "score" in m
            assert "target" in m
            assert 0.0 <= m["score"] <= 100.0

    def test_json_output_format(self):
        repo_root = Path(__file__).resolve().parents[2]
        self._ensure_registry(repo_root)
        results = run_scorecard(repo_root)
        # Verify JSON-serializable
        output = json.dumps(results)
        parsed = json.loads(output)
        assert parsed["meta"]["version"] != "unknown"
        assert "generated_at_utc" in parsed["meta"]


# ---------------------------------------------------------------------------
# H9 — Cross-UC Dependency Coverage
# ---------------------------------------------------------------------------

class TestComputeH9:
    """H9 measures whether use_case_links edges are reciprocal."""

    @staticmethod
    def _write_bracket(repo_root: Path, uc_id: str, dir_name: str, links) -> None:
        import yaml as _yaml
        d = repo_root / "core" / "usecases" / "core" / dir_name
        d.mkdir(parents=True, exist_ok=True)
        body = {"id": uc_id}
        if links is not None:
            body["use_case_links"] = [
                {"use_case_id": t, "link_type": "feeds_into", "reason": "test dependency edge"}
                for t in links
            ]
        (d / "UseCase_Bracket.yaml").write_text(
            _yaml.safe_dump(body, sort_keys=False), encoding="utf-8"
        )

    def test_no_links_returns_no_links_status(self, tmp_repo):
        self._write_bracket(tmp_repo, "COM-001", "COM-001_Sales_Performance", None)
        result = compute_h9(tmp_repo)
        assert result["metric"] == "H9"
        assert result["status"] == "no_links"
        assert result["score"] == 0.0

    def test_reciprocal_pair_scores_100(self, tmp_repo):
        self._write_bracket(tmp_repo, "COM-001", "COM-001_Sales_Performance", ["FIN-002"])
        self._write_bracket(tmp_repo, "FIN-002", "FIN-002_Cost_Performance", ["COM-001"])
        result = compute_h9(tmp_repo)
        assert result["score"] == 100.0
        assert result["status"] == "pass"
        assert result["details"]["reciprocal_pairs"] == 1
        assert result["details"]["total_unique_pairs"] == 1

    def test_one_way_link_flagged_as_missing(self, tmp_repo):
        self._write_bracket(tmp_repo, "COM-001", "COM-001_Sales_Performance", ["FIN-002"])
        self._write_bracket(tmp_repo, "FIN-002", "FIN-002_Cost_Performance", None)
        result = compute_h9(tmp_repo)
        assert result["score"] == 0.0
        assert result["status"] == "below_target"
        assert result["details"]["missing_reciprocals"] == ["COM-001<->FIN-002"]
