"""
test_action_effectiveness_delta.py — Unit tests for Action Effectiveness Delta
measure and the check_action_outcome_reconciliation validator.

Tests cover:
1. Happy path: all checks pass on clean synthetic data
2. Null impact_value on achieved row — should fail
3. Out-of-window outcome (actual days > days_to_outcome) — should fail
4. Zero-delta-only for one action code — should fail
5. Insufficient coverage (< 12 of 15 codes have achieved rows) — should fail
6. Exactly 12 covered codes — should pass (boundary)
7. Missing outcome_date on achieved row — should not crash (skip window check)
8. Non-achieved rows (pending/partial) — should not affect delta or coverage
9. Action Effectiveness Delta measure present in all 5 domain TMDL files
10. Action Effectiveness Delta in 8_Action_Outcomes folder
11. Catalog entry exists for enterprise.action_effectiveness_delta.amount
12. Reconciliation validator passes on real fact_action_outcome data
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import io

# pandas is optional — tests that need it are marked with _needs_pandas
try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    pd = None  # type: ignore[assignment]
    _HAS_PANDAS = False


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_MODULE = REPO_ROOT / "tooling/generator/validation/check_action_outcome_reconciliation.py"
FACT_PATH = REPO_ROOT / "showcases/aurora_group/data/gold/facts/fact_action_outcome"
DIST_ROOT = REPO_ROOT / "products/fabric/powerbi/dist"
CATALOG_PATH = REPO_ROOT / "core/kpi_catalog/KPI_Catalog.md"

DOMAIN_MODELS = [
    "Commercial.SemanticModel",
    "Experience.SemanticModel",
    "Finance.SemanticModel",
    "Operations.SemanticModel",
    "SupplyChain.SemanticModel",
]

# ---------------------------------------------------------------------------
# Import the validator module under test
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT / "tooling/generator/validation"))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "check_action_outcome_reconciliation", str(VALIDATOR_MODULE)
)
_mod = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_mod)
    run_checks = _mod.run_checks
    _VALIDATOR_AVAILABLE = True
except (SystemExit, ImportError):
    # Validator raises ImportError (or, in older versions, sys.exit(2))
    # when pandas/yaml are not installed.
    run_checks = None  # type: ignore[assignment]
    _VALIDATOR_AVAILABLE = False

_needs_pandas = pytest.mark.skipif(
    not _VALIDATOR_AVAILABLE or not _HAS_PANDAS,
    reason="pandas not installed"
)


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

IMPACTFUL_15 = [
    "C-C3.1", "C-C3.2", "C-M2.1", "C-M2.2", "C-P4.1",
    "F-C1.1", "F-K2.1", "O-A2.1", "O-Q3.1", "O-Q3.2",
    "S-F3.1", "S-I1.2", "S-R2.1", "X-S1.1", "X-S1.2",
]


def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Create a DataFrame from a list of row dicts with all required columns."""
    defaults = {
        "action_code_id": "C-C3.1",
        "use_case_id": "COM-001",
        "domain": "Commercial",
        "execution_date": "2023-01-01",
        "outcome_date": "2023-01-31",
        "outcome_status": "achieved",
        "days_to_outcome": 30.0,
        "impact_value": 10000.0,
        "cost_to_execute": 500.0,
        "severity_level": "L1",
        "fiscal_year": 2023,
    }
    full_rows = [{**defaults, **r} for r in rows]
    return pd.DataFrame(full_rows)


def _all_15_achieved() -> pd.DataFrame:
    """Build a minimal clean DataFrame with one achieved row per Impactful-15 code."""
    rows = [
        {
            "action_code_id": code,
            "execution_date": "2023-01-01",
            "outcome_date": "2023-01-31",
            "outcome_status": "achieved",
            "days_to_outcome": 30.0,
            "impact_value": float(5000 + i * 1000),
        }
        for i, code in enumerate(IMPACTFUL_15)
    ]
    return _make_df(rows)


# ---------------------------------------------------------------------------
# Test 1: Happy path — all checks pass on clean synthetic data
# ---------------------------------------------------------------------------

@_needs_pandas
class TestHappyPath:
    def test_clean_data_has_no_violations(self):
        df = _all_15_achieved()
        violations = run_checks(df, IMPACTFUL_15)
        assert violations == [], f"Expected no violations, got: {violations}"


# ---------------------------------------------------------------------------
# Test 2: Null impact_value on achieved row
# ---------------------------------------------------------------------------

@_needs_pandas
class TestNullImpactValue:
    def test_null_impact_value_triggers_violation(self):
        df = _all_15_achieved()
        df.loc[0, "impact_value"] = None
        violations = run_checks(df, IMPACTFUL_15)
        assert any("NULL_IMPACT_VALUE" in v for v in violations), (
            f"Expected NULL_IMPACT_VALUE violation, got: {violations}"
        )

    def test_null_impact_value_identifies_correct_code(self):
        df = _all_15_achieved()
        df.loc[0, "action_code_id"] = "C-C3.1"
        df.loc[0, "impact_value"] = None
        violations = run_checks(df, IMPACTFUL_15)
        null_violations = [v for v in violations if "NULL_IMPACT_VALUE" in v]
        assert len(null_violations) == 1
        assert "C-C3.1" in null_violations[0]


# ---------------------------------------------------------------------------
# Test 3: Out-of-window outcome
# ---------------------------------------------------------------------------

@_needs_pandas
class TestOutOfWindow:
    def test_over_window_triggers_violation(self):
        df = _all_15_achieved()
        # Set execution 2023-01-01, outcome 2023-04-01 = 89 days, window = 30
        df.loc[0, "execution_date"] = "2023-01-01"
        df.loc[0, "outcome_date"] = "2023-04-01"
        df.loc[0, "days_to_outcome"] = 30.0
        violations = run_checks(df, IMPACTFUL_15)
        assert any("OVER_WINDOW" in v for v in violations), (
            f"Expected OVER_WINDOW violation, got: {violations}"
        )

    def test_exactly_on_window_boundary_is_ok(self):
        df = _all_15_achieved()
        # 30 actual days, 30 window = boundary, should pass
        df.loc[0, "execution_date"] = "2023-01-01"
        df.loc[0, "outcome_date"] = "2023-01-31"
        df.loc[0, "days_to_outcome"] = 30.0
        violations = run_checks(df, IMPACTFUL_15)
        over_window = [v for v in violations if "OVER_WINDOW" in v]
        assert over_window == [], f"Boundary should not trigger OVER_WINDOW: {violations}"


# ---------------------------------------------------------------------------
# Test 4: Zero-delta-only for an action code
# ---------------------------------------------------------------------------

@_needs_pandas
class TestZeroDeltaOnly:
    def test_all_zero_delta_triggers_violation(self):
        df = _all_15_achieved()
        # Force ALL rows for C-C3.1 to have zero impact
        df.loc[df["action_code_id"] == "C-C3.1", "impact_value"] = 0.0
        violations = run_checks(df, IMPACTFUL_15)
        assert any("ZERO_DELTA_ONLY" in v for v in violations), (
            f"Expected ZERO_DELTA_ONLY violation, got: {violations}"
        )

    def test_at_least_one_nonzero_satisfies_check(self):
        rows = [
            {"action_code_id": "C-C3.1", "outcome_status": "achieved", "impact_value": 0.0},
            {"action_code_id": "C-C3.1", "outcome_status": "achieved", "impact_value": 5000.0},
        ]
        # Add the remaining 14 codes
        for code in IMPACTFUL_15[1:]:
            rows.append({"action_code_id": code, "outcome_status": "achieved", "impact_value": 1000.0})
        df = _make_df(rows)
        violations = run_checks(df, IMPACTFUL_15)
        zero_violations = [v for v in violations if "ZERO_DELTA_ONLY" in v]
        assert zero_violations == [], f"At least one nonzero row should satisfy check: {violations}"


# ---------------------------------------------------------------------------
# Test 5: Insufficient coverage (< 12 of 15 codes)
# ---------------------------------------------------------------------------

@_needs_pandas
class TestInsufficientCoverage:
    def test_only_11_codes_fails(self):
        only_11 = IMPACTFUL_15[:11]
        rows = [
            {"action_code_id": code, "outcome_status": "achieved", "impact_value": 1000.0}
            for code in only_11
        ]
        # Add some pending rows for the other 4 codes (should not count toward coverage)
        for code in IMPACTFUL_15[11:]:
            rows.append({"action_code_id": code, "outcome_status": "pending", "impact_value": None})
        df = _make_df(rows)
        violations = run_checks(df, IMPACTFUL_15)
        assert any("INSUFFICIENT_COVERAGE" in v for v in violations), (
            f"Expected INSUFFICIENT_COVERAGE violation with 11 codes, got: {violations}"
        )


# ---------------------------------------------------------------------------
# Test 6: Exactly 12 covered codes — should pass (boundary tolerance)
# ---------------------------------------------------------------------------

@_needs_pandas
class TestBoundaryCoverage:
    def test_exactly_12_codes_passes(self):
        rows = [
            {"action_code_id": code, "outcome_status": "achieved", "impact_value": 1000.0}
            for code in IMPACTFUL_15[:12]
        ]
        # Add pending for the remaining 3
        for code in IMPACTFUL_15[12:]:
            rows.append({"action_code_id": code, "outcome_status": "pending", "impact_value": None})
        df = _make_df(rows)
        violations = run_checks(df, IMPACTFUL_15)
        coverage_fail = [v for v in violations if "INSUFFICIENT_COVERAGE" in v]
        assert coverage_fail == [], f"12/15 coverage should be tolerated, got: {violations}"


# ---------------------------------------------------------------------------
# Test 7: Missing outcome_date — should not crash
# ---------------------------------------------------------------------------

@_needs_pandas
class TestMissingOutcomeDate:
    def test_missing_outcome_date_does_not_crash(self):
        df = _all_15_achieved()
        df.loc[0, "outcome_date"] = None
        # Should not raise; window check is skipped for rows missing dates
        violations = run_checks(df, IMPACTFUL_15)
        # The row with None outcome_date is excluded from window check — no crash expected
        # (It should not introduce an OVER_WINDOW violation for a None date)
        over_window = [v for v in violations if "OVER_WINDOW" in v]
        assert over_window == [], f"Missing outcome_date should not trigger OVER_WINDOW: {violations}"


# ---------------------------------------------------------------------------
# Test 8: Non-achieved rows do not pollute achieved-only checks
# ---------------------------------------------------------------------------

@_needs_pandas
class TestNonAchievedRowsIgnored:
    def test_pending_rows_do_not_affect_delta_check(self):
        rows = [
            # Only C-C3.1 achieved with non-zero delta
            {"action_code_id": "C-C3.1", "outcome_status": "achieved", "impact_value": 5000.0},
        ]
        # Add pending rows for C-C3.1 with zero delta (should not trigger ZERO_DELTA_ONLY)
        rows.append(
            {"action_code_id": "C-C3.1", "outcome_status": "pending", "impact_value": 0.0}
        )
        # Fill remaining 14 codes with achieved rows
        for code in IMPACTFUL_15[1:]:
            rows.append({"action_code_id": code, "outcome_status": "achieved", "impact_value": 1000.0})
        df = _make_df(rows)
        violations = run_checks(df, IMPACTFUL_15)
        zero_violations = [v for v in violations if "ZERO_DELTA_ONLY" in v]
        assert zero_violations == [], f"Pending zero-delta rows should not trigger ZERO_DELTA_ONLY: {violations}"


# ---------------------------------------------------------------------------
# Test 9: Action Effectiveness Delta present in all 5 domain TMDL files
# ---------------------------------------------------------------------------

class TestMeasureInTMDL:
    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_action_effectiveness_delta_present(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        assert tmdl_path.exists(), f"{tmdl_path} does not exist"
        content = tmdl_path.read_text(encoding="utf-8")
        assert "measure 'Action Effectiveness Delta" in content, (
            f"'Action Effectiveness Delta' measure missing from {domain_model}/_Measures.tmdl"
        )

    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_action_effectiveness_delta_in_correct_folder(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        content = tmdl_path.read_text(encoding="utf-8")
        # Locate the measure block and verify it's in 8_Action_Outcomes
        idx = content.find("measure 'Action Effectiveness Delta")
        assert idx >= 0
        snippet = content[idx: idx + 400]
        assert '"8_Action_Outcomes"' in snippet, (
            f"Action Effectiveness Delta not in 8_Action_Outcomes folder in {domain_model}"
        )

    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_action_effectiveness_delta_uses_achieved_filter(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        content = tmdl_path.read_text(encoding="utf-8")
        idx = content.find("measure 'Action Effectiveness Delta")
        snippet = content[idx: idx + 600]
        assert '"achieved"' in snippet, (
            f"Action Effectiveness Delta should filter outcome_status = 'achieved' in {domain_model}"
        )
        assert "impact_value" in snippet, (
            f"Action Effectiveness Delta should reference impact_value in {domain_model}"
        )

    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_action_effectiveness_delta_has_format_string(self, domain_model):
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        content = tmdl_path.read_text(encoding="utf-8")
        idx = content.find("measure 'Action Effectiveness Delta")
        snippet = content[idx: idx + 400]
        assert "formatString" in snippet, (
            f"Action Effectiveness Delta is missing formatString in {domain_model}"
        )

    @pytest.mark.parametrize("domain_model", DOMAIN_MODELS)
    def test_action_effectiveness_delta_has_doc_block(self, domain_model):
        # After the enricher re-baseline, the bespoke "/// Purpose:" line is replaced by
        # the governed AI-description block (definition · Formula · Grain · Owner). The
        # standard supersedes the literal Purpose: keyword — assert a /// doc block exists.
        tmdl_path = DIST_ROOT / domain_model / "definition/tables/_Measures.tmdl"
        content = tmdl_path.read_text(encoding="utf-8")
        idx = content.find("measure 'Action Effectiveness Delta")
        assert idx >= 0
        snippet = content[max(0, idx - 400): idx]
        assert "///" in snippet, (
            f"Action Effectiveness Delta missing a /// doc block in {domain_model}"
        )


# ---------------------------------------------------------------------------
# Test 10 (in TestMeasureInTMDL above, folder already covered)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Test 11: Catalog entry exists
# ---------------------------------------------------------------------------

class TestCatalogEntry:
    def test_catalog_has_action_effectiveness_delta_entry(self):
        assert CATALOG_PATH.exists(), f"Catalog not found: {CATALOG_PATH}"
        content = CATALOG_PATH.read_text(encoding="utf-8")
        assert "enterprise.action_effectiveness_delta.amount" in content, (
            "KPI catalog missing enterprise.action_effectiveness_delta.amount entry"
        )

    def test_catalog_entry_has_correct_measure_name(self):
        # KPI_Catalog.md is a generated view; assert on parsed data, not on the
        # incidental YAML quoting of the rendered block.
        import yaml
        block = CATALOG_PATH.read_text(encoding="utf-8").split("```yaml", 1)[1].rsplit("```", 1)[0]
        entries = {e["kpi_id"]: e for e in yaml.safe_load(block)}
        entry = entries["enterprise.action_effectiveness_delta.amount"]
        assert entry["technical"]["measure_name"] == "Action Effectiveness Delta", (
            "KPI catalog entry for action_effectiveness_delta missing correct measure_name"
        )

    def test_catalog_entry_references_impact_value_lineage(self):
        content = CATALOG_PATH.read_text(encoding="utf-8")
        assert "fact_action_outcome.impact_value" in content, (
            "KPI catalog entry missing fact_action_outcome.impact_value in lineage"
        )


# ---------------------------------------------------------------------------
# Test 12: Reconciliation validator passes on real data
# ---------------------------------------------------------------------------

@_needs_pandas
class TestRealDataReconciliation:
    def test_real_fact_action_outcome_passes_all_checks(self):
        """End-to-end: load real Parquet, load real Impactful-15, run checks."""
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            pytest.skip("pyarrow not installed")

        assert FACT_PATH.is_dir(), f"fact_action_outcome directory missing: {FACT_PATH}"

        impactful_path = REPO_ROOT / "core/action_codes/impactful_15.yaml"
        try:
            import yaml
            data = yaml.safe_load(impactful_path.read_text(encoding="utf-8"))
            impactful_ids = [e["id"] for e in data["action_code_ids"]]
        except Exception as exc:
            pytest.skip(f"Could not load impactful_15.yaml: {exc}")

        files = list(FACT_PATH.rglob("*.parquet"))
        assert files, "No Parquet files found"
        df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

        violations = run_checks(df, impactful_ids)
        assert violations == [], (
            f"Real fact_action_outcome data failed reconciliation: {violations}"
        )
