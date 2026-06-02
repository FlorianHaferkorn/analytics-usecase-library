"""
generate_fact_action_outcome.py — Synthetic fact_action_outcome data generator.

Creates 5-year partitioned Parquet files (Fiscal Year=20xx) matching the
partition scheme of other fact tables in the Aurora showcase dataset.

Schema:
    action_code_id      string   — references Impactful 15 action codes
    use_case_id         string   — originating use case (e.g. COM-001)
    domain              string   — Commercial | Finance | Operations | SupplyChain | Service
    execution_date      string   — ISO date when action was triggered
    outcome_date        string   — ISO date when outcome was confirmed (or null)
    outcome_status      string   — achieved | partial | not_achieved | pending
    days_to_outcome     double   — days from execution_date to outcome_date
    impact_value        double   — EUR value of confirmed impact
    cost_to_execute     double   — EUR cost to execute action
    severity_level      string   — L1 | L2 | L3
    fiscal_year         int32    — partition key (2020–2024)

Usage:
    python3 showcases/aurora_group/data/scripts/generate_fact_action_outcome.py
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = REPO_ROOT / "showcases/aurora_group/data/gold/facts/fact_action_outcome"

SEED = 42
YEARS = [2020, 2021, 2022, 2023, 2024]
ROWS_PER_YEAR = 120   # ~10 outcome events per action code per year

# Impactful 15 action codes with their domain and use case references
IMPACTFUL_15 = [
    ("C-M2.1", "Commercial",  "COM-001"),
    ("C-M2.2", "Commercial",  "COM-001"),
    ("C-S1.1", "Commercial",  "COM-001"),
    ("C-S1.2", "Commercial",  "COM-001"),
    ("C-C3.1", "Commercial",  "COM-003"),
    ("F-C1.1", "Finance",     "FIN-001"),
    ("F-C1.2", "Finance",     "FIN-001"),
    ("F-K2.1", "Finance",     "FIN-002"),
    ("O-A2.1", "Operations",  "OPS-001"),
    ("O-O1.1", "Operations",  "OPS-001"),
    ("O-O1.2", "Operations",  "OPS-001"),
    ("O-O1.3", "Operations",  "OPS-001"),
    ("O-Q3.1", "Operations",  "OPS-002"),
    ("S-I1.1", "SupplyChain", "SCM-001"),
    ("S-R2.1", "SupplyChain", "SCM-002"),
]

# Outcome status distribution by severity
STATUS_WEIGHTS = {
    "L1": {"achieved": 0.70, "partial": 0.15, "not_achieved": 0.10, "pending": 0.05},
    "L2": {"achieved": 0.55, "partial": 0.20, "not_achieved": 0.15, "pending": 0.10},
    "L3": {"achieved": 0.40, "partial": 0.25, "not_achieved": 0.20, "pending": 0.15},
}

# Typical impact value ranges by domain (EUR)
IMPACT_RANGES = {
    "Commercial":  (5_000,  80_000),
    "Finance":     (10_000, 150_000),
    "Operations":  (3_000,  50_000),
    "SupplyChain": (8_000,  100_000),
    "Service":     (2_000,  30_000),
}

# Cost to execute ranges (EUR)
COST_RANGES = {
    "Commercial":  (500,  5_000),
    "Finance":     (800,  8_000),
    "Operations":  (400,  4_000),
    "SupplyChain": (600,  6_000),
    "Service":     (300,  2_000),
}


def _fiscal_year_date_range(year: int):
    return date(year, 1, 1), date(year, 12, 31)


def _random_date(start: date, end: date, rng: random.Random) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def _weighted_choice(weights: dict[str, float], rng: random.Random) -> str:
    keys = list(weights.keys())
    vals = list(weights.values())
    return rng.choices(keys, vals)[0]


def generate_year(year: int, rng: random.Random) -> pa.Table:
    start, end = _fiscal_year_date_range(year)
    rows: dict[str, list] = {
        "action_code_id": [],
        "use_case_id": [],
        "domain": [],
        "execution_date": [],
        "outcome_date": [],
        "outcome_status": [],
        "days_to_outcome": [],
        "impact_value": [],
        "cost_to_execute": [],
        "severity_level": [],
        "fiscal_year": [],
    }

    for _ in range(ROWS_PER_YEAR):
        ac_id, domain, uc_id = IMPACTFUL_15[rng.randint(0, len(IMPACTFUL_15) - 1)]
        severity = rng.choices(["L1", "L2", "L3"], [0.4, 0.4, 0.2])[0]
        status = _weighted_choice(STATUS_WEIGHTS[severity], rng)

        exec_date = _random_date(start, end, rng)
        if status in ("achieved", "partial"):
            days = rng.randint(3, 90)
            out_date = exec_date + timedelta(days=days)
            if out_date > end:
                out_date = end
        elif status == "not_achieved":
            days = rng.randint(14, 120)
            out_date = exec_date + timedelta(days=days)
            if out_date > end:
                out_date = end
        else:
            # pending — no outcome date
            out_date = None
            days = None

        lo, hi = IMPACT_RANGES[domain]
        impact = round(rng.uniform(lo, hi), 2) if status != "not_achieved" else 0.0
        if status == "partial":
            impact = round(impact * rng.uniform(0.3, 0.7), 2)

        clo, chi = COST_RANGES[domain]
        cost = round(rng.uniform(clo, chi), 2)

        rows["action_code_id"].append(ac_id)
        rows["use_case_id"].append(uc_id)
        rows["domain"].append(domain)
        rows["execution_date"].append(str(exec_date))
        rows["outcome_date"].append(str(out_date) if out_date else None)
        rows["outcome_status"].append(status)
        rows["days_to_outcome"].append(float(days) if days is not None else None)
        rows["impact_value"].append(impact)
        rows["cost_to_execute"].append(cost)
        rows["severity_level"].append(severity)
        rows["fiscal_year"].append(year)

    schema = pa.schema([
        ("action_code_id", pa.string()),
        ("use_case_id", pa.string()),
        ("domain", pa.string()),
        ("execution_date", pa.string()),
        ("outcome_date", pa.string()),
        ("outcome_status", pa.string()),
        ("days_to_outcome", pa.float64()),
        ("impact_value", pa.float64()),
        ("cost_to_execute", pa.float64()),
        ("severity_level", pa.string()),
        ("fiscal_year", pa.int32()),
    ])
    return pa.table(rows, schema=schema)


def main() -> None:
    rng = random.Random(SEED)
    total_rows = 0

    for year in YEARS:
        table = generate_year(year, rng)
        out_path = OUT_DIR / f"Fiscal Year={year}"
        out_path.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_path / "data.parquet", compression="snappy")
        print(f"  {year}: {table.num_rows} rows → {out_path / 'data.parquet'}")
        total_rows += table.num_rows

    print(f"Generated {total_rows} rows across {len(YEARS)} years in {OUT_DIR}")


if __name__ == "__main__":
    main()
