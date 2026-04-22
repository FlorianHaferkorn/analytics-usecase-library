#!/usr/bin/env python3
"""
check_action_outcome_reconciliation.py — Action-outcome reconciliation gate.

Reads fact_action_outcome Parquet (partitioned by Fiscal Year) and asserts:

1. Every "achieved" row has non-null impact_value (proxy for kpi delta).
2. Every "achieved" row has actual days-to-outcome <= days_to_outcome window.
3. For every unique action_code_id, at least one "achieved" row has a non-zero delta.
4. At least 12 of the 15 Impactful action codes have >= 1 "achieved" row
   (tolerates up to 3 codes with only pending executions).

Exits 0 on success, 1 on any assertion failure.

Usage:
    python3 tooling/generator/validation/check_action_outcome_reconciliation.py
    python3 tooling/generator/validation/check_action_outcome_reconciliation.py --strict
    python3 tooling/generator/validation/check_action_outcome_reconciliation.py \
        --fact-dir showcases/aurora_group/data/gold/facts/fact_action_outcome \
        --impactful-15 core/action_codes/impactful_15.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas pyarrow", file=sys.stderr)
    sys.exit(2)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def load_fact(fact_dir: Path) -> pd.DataFrame:
    """Load all Parquet partitions from fact_action_outcome directory."""
    if not fact_dir.exists():
        print(f"ERROR: fact_action_outcome directory not found: {fact_dir}", file=sys.stderr)
        sys.exit(2)

    files = sorted(fact_dir.rglob("*.parquet"))
    if not files:
        print(f"ERROR: No Parquet files found in: {fact_dir}", file=sys.stderr)
        sys.exit(2)

    frames = []
    for f in files:
        try:
            frames.append(pd.read_parquet(f))
        except Exception as exc:
            print(f"ERROR: Could not read {f}: {exc}", file=sys.stderr)
            sys.exit(2)

    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df)} rows from {len(files)} Parquet file(s) in {fact_dir}")
    return df


def load_impactful_15(yaml_path: Path) -> list[str]:
    """Return list of Impactful 15 action code IDs from YAML."""
    if not yaml_path.exists():
        print(f"ERROR: impactful_15.yaml not found: {yaml_path}", file=sys.stderr)
        sys.exit(2)
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return [e["id"] for e in data["action_code_ids"]]


def run_checks(df: pd.DataFrame, impactful_ids: list[str]) -> list[str]:
    """
    Execute all reconciliation checks.
    Returns a list of violation strings (empty = pass).
    """
    violations: list[str] = []

    achieved = df[df["outcome_status"] == "achieved"].copy()
    print(f"  Achieved rows: {len(achieved)} / {len(df)} total")

    # ── Check 1: No null impact_value in achieved rows ─────────────────────────
    null_impact = achieved[achieved["impact_value"].isna()]
    if not null_impact.empty:
        for _, row in null_impact.iterrows():
            violations.append(
                f"[NULL_IMPACT_VALUE] action_code_id={row['action_code_id']} "
                f"use_case_id={row.get('use_case_id','?')} "
                f"execution_date={row.get('execution_date','?')} — "
                "impact_value is NULL on an achieved row"
            )

    # ── Check 2: outcome within time window ───────────────────────────────────
    # actual_days <= days_to_outcome (both columns available)
    rows_with_dates = achieved.dropna(subset=["execution_date", "outcome_date", "days_to_outcome"])
    if not rows_with_dates.empty:
        exec_dt = pd.to_datetime(rows_with_dates["execution_date"], errors="coerce")
        outc_dt = pd.to_datetime(rows_with_dates["outcome_date"], errors="coerce")
        actual_days = (outc_dt - exec_dt).dt.days
        window_days = rows_with_dates["days_to_outcome"]
        over_window = rows_with_dates[actual_days > window_days]
        for idx, row in over_window.iterrows():
            a_days = int((pd.to_datetime(row["outcome_date"]) - pd.to_datetime(row["execution_date"])).days)
            violations.append(
                f"[OVER_WINDOW] action_code_id={row['action_code_id']} "
                f"execution_date={row['execution_date']} outcome_date={row['outcome_date']} — "
                f"actual days {a_days} exceeds window {int(row['days_to_outcome'])}"
            )

    # ── Check 3: non-zero delta for each unique action_code_id × impactful ────
    # For every unique action_code_id in achieved rows, at least one row must
    # have impact_value != 0 (proves the loop is active, not just instrumented)
    unique_codes_achieved = achieved["action_code_id"].unique()
    for code in unique_codes_achieved:
        code_rows = achieved[achieved["action_code_id"] == code]
        if (code_rows["impact_value"] == 0).all():
            violations.append(
                f"[ZERO_DELTA_ONLY] action_code_id={code} — "
                "all achieved rows have impact_value = 0; loop appears only instrumented, not active"
            )

    # ── Check 4: coverage — at least 12 of 15 Impactful codes have achieved rows
    codes_with_achieved = set(achieved["action_code_id"].unique())
    impactful_set = set(impactful_ids)
    covered = impactful_set & codes_with_achieved
    not_covered = impactful_set - codes_with_achieved
    coverage_count = len(covered)
    print(f"  Impactful-15 coverage: {coverage_count}/15 codes have >= 1 achieved row")
    if coverage_count < 12:
        violations.append(
            f"[INSUFFICIENT_COVERAGE] Only {coverage_count}/15 Impactful action codes have "
            f"achieved rows (minimum required: 12). Missing codes: {sorted(not_covered)}"
        )
    elif not_covered:
        # Report which codes have no achieved rows (informational in non-strict mode)
        print(
            f"  INFO: {len(not_covered)} code(s) have no achieved rows (within tolerance): "
            f"{sorted(not_covered)}"
        )

    return violations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Action-outcome reconciliation gate for fact_action_outcome"
    )
    parser.add_argument(
        "--fact-dir",
        default="showcases/aurora_group/data/gold/facts/fact_action_outcome",
        help="Path to fact_action_outcome partitioned directory",
    )
    parser.add_argument(
        "--impactful-15",
        default="core/action_codes/impactful_15.yaml",
        help="Path to impactful_15.yaml",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any violation (default behavior; flag kept for CI explicitness)",
    )
    args = parser.parse_args()

    fact_dir = Path(args.fact_dir)
    impactful_path = Path(args.impactful_15)

    print("=== Action-Outcome Reconciliation Check ===")
    df = load_fact(fact_dir)
    impactful_ids = load_impactful_15(impactful_path)
    print(f"  Impactful-15 action codes loaded: {len(impactful_ids)}")

    violations = run_checks(df, impactful_ids)

    if violations:
        print(f"\nFAILED — {len(violations)} violation(s) found:\n")
        for v in violations:
            print(f"  VIOLATION: {v}")
        sys.exit(1)

    # Summary metrics
    achieved = df[df["outcome_status"] == "achieved"]
    codes_with_achieved = achieved["action_code_id"].nunique()
    print(
        f"\nPASSED — {codes_with_achieved}/15 codes reconciled, "
        f"{len(achieved)} achieved rows, 0 violations."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
