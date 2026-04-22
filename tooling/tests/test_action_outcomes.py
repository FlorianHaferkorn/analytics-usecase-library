"""
test_action_outcomes.py — Week 5 acceptance gate for the action-code outcome loop.

Validates:
1. fact_action_outcome Parquet exists and has the expected schema
2. All 15 Impactful action codes appear in the data
3. Every Impactful 15 action code has at least one non-BLANK outcome row
4. Outcome measures exist in every domain _Measures.tmdl
5. XD-004 bracket references all Impactful 15 action codes
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FACT_PATH = REPO_ROOT / "showcases/aurora_group/data/gold/facts/fact_action_outcome"
DIST_ROOT = REPO_ROOT / "products/fabric/powerbi/dist"
IMPACTFUL_15_PATH = REPO_ROOT / "core/action_codes/impactful_15.yaml"
XD004_BRACKET = REPO_ROOT / "core/usecases/core/XD-004_Executive_Action_Governance/UseCase_Bracket.yaml"

DOMAIN_MODELS = [
    "Commercial.SemanticModel",
    "Experience.SemanticModel",
    "Finance.SemanticModel",
    "Operations.SemanticModel",
    "SupplyChain.SemanticModel",
]

EXPECTED_OUTCOME_MEASURES = [
    "Actions Executed Count",
    "Action Outcome Rate %",
    "Avg Time-to-Outcome Days",
    "Action ROI %",
]

EXPECTED_COLUMNS = {
    "action_code_id",
    "use_case_id",
    "domain",
    "execution_date",
    "outcome_status",
    "days_to_outcome",
    "impact_value",
    "cost_to_execute",
    "severity_level",
    "fiscal_year",
}


def _impactful_15_ids() -> list[str]:
    data = yaml.safe_load(IMPACTFUL_15_PATH.read_text(encoding="utf-8"))
    return [e["id"] for e in data["action_code_ids"]]


# ── Parquet data tests ────────────────────────────────────────────────────────

class TestFactActionOutcome:
    def test_directory_exists(self):
        assert FACT_PATH.is_dir(), f"fact_action_outcome directory missing: {FACT_PATH}"

    def test_has_five_year_partitions(self):
        partitions = [d.name for d in FACT_PATH.iterdir() if d.is_dir() and d.name.startswith("Fiscal Year=")]
        assert len(partitions) == 5, f"Expected 5 Fiscal Year partitions, got {partitions}"

    def test_parquet_files_readable(self):
        try:
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("pyarrow not installed")

        files = list(FACT_PATH.rglob("*.parquet"))
        assert len(files) >= 5, "Expected at least 5 Parquet files (one per year)"
        for f in files[:1]:
            table = pq.read_table(f)
            assert table.num_rows > 0

    def test_schema_has_required_columns(self):
        try:
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("pyarrow not installed")

        files = list(FACT_PATH.rglob("*.parquet"))
        assert files, "No Parquet files found"
        schema = pq.read_schema(files[0])
        col_names = set(schema.names)
        missing = EXPECTED_COLUMNS - col_names
        assert not missing, f"Missing columns in fact_action_outcome: {missing}"

    def test_all_impactful_15_present(self):
        try:
            import pyarrow.parquet as pq
            import pyarrow.compute as pc
        except ImportError:
            pytest.skip("pyarrow not installed")

        files = list(FACT_PATH.rglob("*.parquet"))
        all_ids: set[str] = set()
        for f in files:
            t = pq.read_table(f, columns=["action_code_id"])
            all_ids.update(t.column("action_code_id").to_pylist())

        impactful_ids = set(_impactful_15_ids())
        missing = impactful_ids - all_ids
        assert not missing, f"Impactful 15 IDs missing from data: {missing}"

    def test_each_impactful_action_has_non_blank_outcome(self):
        try:
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("pyarrow not installed")

        files = list(FACT_PATH.rglob("*.parquet"))
        achieved: dict[str, int] = {}
        for f in files:
            t = pq.read_table(f, columns=["action_code_id", "outcome_status"])
            for row in t.to_pylist():
                if row["outcome_status"] in ("achieved", "partial"):
                    achieved[row["action_code_id"]] = achieved.get(row["action_code_id"], 0) + 1

        impactful_ids = _impactful_15_ids()
        blank = [ac for ac in impactful_ids if achieved.get(ac, 0) == 0]
        assert not blank, f"Impactful action codes with no non-BLANK outcome: {blank}"


# ── TMDL outcome measure tests ────────────────────────────────────────────────

class TestOutcomeMeasuresInTMDL:
    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_outcome_measures_present(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        assert tmdl_path.exists(), f"{tmdl_path} does not exist"
        content = tmdl_path.read_text(encoding="utf-8")
        for measure in EXPECTED_OUTCOME_MEASURES:
            assert f"measure '{measure}" in content, \
                f"'{measure}' (or suffixed proxy) missing from {domain_model}/_Measures.tmdl"

    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_outcome_measures_reference_fact_action_outcome(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        content = tmdl_path.read_text(encoding="utf-8")
        assert "fact_action_outcome" in content, \
            f"fact_action_outcome not referenced in {domain_model}/_Measures.tmdl"

    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_outcome_measures_in_action_outcomes_folder(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        content = tmdl_path.read_text(encoding="utf-8")
        assert '"8_Action_Outcomes"' in content, \
            f"8_Action_Outcomes display folder missing from {domain_model}"


# ── XD-004 bracket tests ──────────────────────────────────────────────────────

class TestXD004Bracket:
    def test_bracket_exists(self):
        assert XD004_BRACKET.exists(), f"XD-004 bracket not found: {XD004_BRACKET}"

    def test_strategic_kpi_is_outcome_rate(self):
        data = yaml.safe_load(XD004_BRACKET.read_text(encoding="utf-8"))
        strategic = data.get("orchestration", {}).get("strategic_kpi_id")
        assert strategic == "enterprise.action_outcome_rate.pct", \
            f"XD-004 strategic KPI should be enterprise.action_outcome_rate.pct, got {strategic}"

    def test_all_impactful_15_wired(self):
        data = yaml.safe_load(XD004_BRACKET.read_text(encoding="utf-8"))
        wired = set(data.get("orchestration", {}).get("action_code_ids", []))
        impactful = set(_impactful_15_ids())
        missing = impactful - wired
        assert not missing, f"XD-004 bracket missing Impactful 15 IDs: {missing}"

    def test_no_deprecated_kpis(self):
        deprecated = {
            "fin.liquidity.payables.amount",
            "ops.planned.hours",
            "cost.base_volume.amount",
            "cost.opex.base.amount",
            "plan.replan.count",
            "enterprise.action_routed.count",
        }
        content = XD004_BRACKET.read_text(encoding="utf-8")
        found = [d for d in deprecated if d in content]
        assert not found, f"XD-004 bracket references deprecated KPIs: {found}"

    def test_primary_kpi_ids_present(self):
        data = yaml.safe_load(XD004_BRACKET.read_text(encoding="utf-8"))
        assert "primary_kpi_ids" in data, "XD-004 bracket missing primary_kpi_ids"
        assert len(data["primary_kpi_ids"]) >= 1
