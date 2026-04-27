"""
Generate Finance gold data
==========================

Produces four fact tables for the Finance and Operations semantic models:

  fact_finance    – monthly P&L per org (Net Sales, COGS, OpEx, EBIT, Net Income, …)
  fact_cost       – monthly cost detail per org × product × cost type
  fact_labor      – monthly headcount and labor cost per org
  fact_output     – daily output units and revenue per DC × product

Aurora Group SE reference scale (2024 actuals after 5 years of ~6 % CAGR):
  495 stores   × ~€5 M/yr  = ~€2.5 B revenue
  18  DCs      – throughput, not direct revenue (minimal P&L rows)
  5   regions  – consolidation entities

Growth model (compounding):
  2020 = base year index 1.00
  2021 = 1.04
  2022 = 1.08
  2023 = 1.14
  2024 = 1.20

P&L ratios (store level):
  COGS / Net Sales         = 0.59 – 0.63
  Material Cost / COGS     = 0.72 – 0.80
  OpEx / Net Sales         = 0.28 – 0.32
  EBIT = Gross Margin – OpEx
  Net Income ≈ EBIT × 0.70  (effective 30 % tax rate)

Run from repo root:
  python3 showcases/aurora_group/data/gold/generate_finance_gold.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GOLD = Path(__file__).resolve().parent
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))

from _generator_utils import (
    FACTS_END,
    FACTS_START,
    apply_monthly_seasonality,
    write_fact_delta,
)

DIMS  = GOLD / "dimensions"
FACTS = GOLD / "facts"

RANDOM_SEED = 12345
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

# Annual growth index per year (2020 baseline)
_GROWTH: dict[int, float] = {2020: 1.00, 2021: 1.04, 2022: 1.08, 2023: 1.14, 2024: 1.20}

# Base monthly revenue by OrgType (EUR, before growth/seasonality)
_BASE_MONTHLY_REVENUE: dict[str, float] = {
    "Store":   390_000,   # ~€4.7 M/yr per store
    "DC":       80_000,   # marginal own-revenue; DC cost centre
    "Country": 250_000,   # consolidation entity
    "Region":  600_000,   # regional HQ overhead / interco
    "Group":   800_000,   # group-level central functions
}

# P&L ratio ranges (low, high) – drawn deterministically per OrgKey
_COGS_RATIO   = (0.59, 0.63)
_MATL_RATIO   = (0.72, 0.80)   # Material Cost / COGS
_OPEX_RATIO   = (0.28, 0.32)
_TAX_RATE     = 0.30

# Cost types for fact_cost
_COST_TYPES = ["Direct Material", "Direct Labor", "Manufacturing Overhead", "Logistics Cost"]
_COST_TYPE_WEIGHTS = [0.52, 0.18, 0.20, 0.10]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load_parquet(name: str) -> pd.DataFrame:
    files = sorted((DIMS / name).rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"{DIMS / name} has no parquet files")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _rng_for(key: int, salt: int = 0) -> np.random.RandomState:
    return np.random.RandomState(RANDOM_SEED + key * 31 + salt)


def _pl_ratios(org_key: int) -> tuple[float, float, float]:
    """Return (cogs_ratio, matl_ratio, opex_ratio) deterministically for org."""
    rng = _rng_for(org_key, salt=1)
    cogs = float(rng.uniform(*_COGS_RATIO))
    matl = float(rng.uniform(*_MATL_RATIO))
    opex = float(rng.uniform(*_OPEX_RATIO))
    return cogs, matl, opex


def _month_end_dates() -> list[pd.Timestamp]:
    return [d for d in pd.date_range(FACTS_START, FACTS_END, freq="D") if d.is_month_end]


# ---------------------------------------------------------------------------
# fact_finance
# ---------------------------------------------------------------------------

def generate_fact_finance(org_df: pd.DataFrame) -> None:
    print("Generating fact_finance …")
    months = _month_end_dates()
    rows: list[dict] = []

    org_types = dict(zip(org_df["OrgKey"], org_df["OrgType"]))

    for date_obj in months:
        date_key = int(date_obj.strftime("%Y%m%d"))
        year     = date_obj.year
        growth   = _GROWTH.get(year, 1.0)
        seasonality = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)

        for org_key, org_type in org_types.items():
            base_rev = _BASE_MONTHLY_REVENUE.get(org_type, 390_000)
            rng      = _rng_for(org_key, salt=date_key % 1000)

            # Net Sales with growth, seasonality, and small per-org noise
            noise   = float(rng.uniform(0.92, 1.08))
            net_sales = base_rev * growth * seasonality * noise

            cogs_r, matl_r, opex_r = _pl_ratios(org_key)

            cogs_amount     = net_sales * cogs_r
            matl_cost       = cogs_amount * matl_r
            gross_margin    = net_sales - cogs_amount
            opex_amount     = net_sales * opex_r
            # Plan OpEx: budget set at start of year, slightly lower than actuals
            plan_opex       = net_sales * (opex_r - float(rng.uniform(0.005, 0.020)))
            ebit_amount     = gross_margin - opex_amount
            net_income      = ebit_amount * (1.0 - _TAX_RATE)

            rows.append({
                "DateKey":                date_key,
                "OrgKey":                 int(org_key),
                "Net Sales Amount":       round(net_sales, 2),
                "COGS Amount":            round(cogs_amount, 2),
                "Material Cost Amount":   round(matl_cost, 2),
                "OpEx Amount":            round(opex_amount, 2),
                "Plan OpEx Amount":       round(plan_opex, 2),
                "EBIT Amount":            round(ebit_amount, 2),
                "Net Income Amount":      round(net_income, 2),
            })

    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_finance", df, partition_by=["Fiscal Year"])
    print(f"  Written fact_finance ({len(rows):,} rows) [{fmt}]")


# ---------------------------------------------------------------------------
# fact_cost
# ---------------------------------------------------------------------------

def generate_fact_cost(org_df: pd.DataFrame, product_keys: list[int]) -> None:
    """Monthly cost detail at org × product × cost-type grain.

    Scope: all Store + DC orgs (operational units), up to 50 products.
    Each row is one cost-type bucket for that org-product-month.
    """
    print("Generating fact_cost …")
    months = _month_end_dates()
    rows: list[dict] = []

    operational_orgs = org_df[org_df["OrgType"].isin(["Store", "DC"])]
    selected_products = product_keys[:50]

    for date_obj in months:
        date_key    = int(date_obj.strftime("%Y%m%d"))
        year        = date_obj.year
        growth      = _GROWTH.get(year, 1.0)
        seasonality = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)

        for _, org_row in operational_orgs.iterrows():
            org_key  = int(org_row["OrgKey"])
            org_type = org_row["OrgType"]
            base_rev = _BASE_MONTHLY_REVENUE.get(org_type, 390_000)
            cogs_r, _, _ = _pl_ratios(org_key)
            total_cogs = base_rev * growth * seasonality * cogs_r

            # Split COGS across selected products (Pareto: top products carry more cost)
            n_prod = len(selected_products)
            rng_p  = _rng_for(org_key, salt=5)
            product_weights = np.exp(-rng_p.uniform(0, 0.3, n_prod) * np.arange(n_prod))
            product_weights /= product_weights.sum()

            for pk, prod_wt in zip(selected_products, product_weights):
                prod_cogs = total_cogs * float(prod_wt)
                rng_ct    = _rng_for(org_key * 100 + pk, salt=date_key % 500)
                noise     = float(rng_ct.uniform(0.93, 1.07))
                actual    = prod_cogs * noise
                plan      = actual * float(rng_ct.uniform(0.96, 1.04))

                # Pick dominant cost type per org-product (deterministic)
                ct_rng   = _rng_for(org_key * 10000 + pk, salt=7)
                cost_type = str(ct_rng.choice(_COST_TYPES, p=_COST_TYPE_WEIGHTS))

                rows.append({
                    "DateKey":          date_key,
                    "OrgKey":           org_key,
                    "ProductKey":       int(pk),
                    "Cost Type":        cost_type,
                    "COGS Amount":      round(actual, 2),
                    "Plan COGS Amount": round(plan, 2),
                })

    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_cost", df, partition_by=["Fiscal Year"])
    print(f"  Written fact_cost ({len(rows):,} rows) [{fmt}]")


# ---------------------------------------------------------------------------
# fact_labor
# ---------------------------------------------------------------------------

# Base headcount by org type (FTE)
_BASE_HEADCOUNT: dict[str, tuple[int, int]] = {
    "Store":   (18, 40),
    "DC":      (45, 90),
    "Country": (8,  20),
    "Region":  (12, 30),
    "Group":   (20, 50),
}
_MONTHLY_SALARY = 3_350.0   # EUR average fully-loaded monthly cost per FTE


def generate_fact_labor(org_df: pd.DataFrame) -> None:
    print("Generating fact_labor …")
    months = _month_end_dates()
    rows: list[dict] = []

    for date_obj in months:
        date_key    = int(date_obj.strftime("%Y%m%d"))
        year        = date_obj.year
        growth      = _GROWTH.get(year, 1.0)
        seasonality = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)

        for _, org_row in org_df.iterrows():
            org_key  = int(org_row["OrgKey"])
            org_type = org_row["OrgType"]
            hc_low, hc_high = _BASE_HEADCOUNT.get(org_type, (10, 30))

            # Base headcount for this org (stable across months, grows with revenue)
            rng_base = _rng_for(org_key, salt=9)
            base_hc  = int(rng_base.randint(hc_low, hc_high + 1))

            # Seasonality affects temporary/contract staff
            # Peak season (Nov-Dec) +15% headcount; Jan dip -5%
            hc_scale    = 1.0 + (seasonality - 1.0) * 0.15
            growth_hc   = 1.0 + (growth - 1.0) * 0.5   # headcount grows slower than revenue
            headcount   = max(1, round(base_hc * growth_hc * hc_scale))

            labor_hours = headcount * 160.0   # 160 hr / month standard
            rng_var     = _rng_for(org_key, salt=date_key % 300)
            labor_cost  = headcount * _MONTHLY_SALARY * float(rng_var.uniform(0.96, 1.04))

            rows.append({
                "DateKey":      date_key,
                "OrgKey":       org_key,
                "Headcount":    int(headcount),
                "Labor Hours":  round(labor_hours, 1),
                "Labor Cost":   round(labor_cost, 2),
            })

    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_labor", df, partition_by=["Fiscal Year"])
    print(f"  Written fact_labor ({len(rows):,} rows) [{fmt}]")


# ---------------------------------------------------------------------------
# fact_output  (daily, DC grain)
# ---------------------------------------------------------------------------

# DCs only for output (manufacturing / fulfilment output tracking)
_PRODUCTS_PER_DC = 30     # each DC handles this many SKUs
_BASE_DAILY_UNITS_DC = 800.0  # units processed per product per day baseline


def generate_fact_output(org_df: pd.DataFrame, product_keys: list[int]) -> None:
    print("Generating fact_output …")
    fact_dates = pd.date_range(FACTS_START, FACTS_END, freq="D")
    rows: list[dict] = []

    dc_orgs = org_df[org_df["OrgType"] == "DC"]
    dc_products = product_keys[:_PRODUCTS_PER_DC]

    # Pre-compute avg price per product (deterministic)
    avg_prices = {pk: float(_rng_for(pk, salt=11).uniform(18.0, 280.0)) for pk in dc_products}

    print(f"  {len(dc_orgs)} DCs × {len(dc_products)} products × {len(fact_dates)} days …")

    for date_obj in fact_dates:
        date_key    = int(date_obj.strftime("%Y%m%d"))
        year        = date_obj.year
        growth      = _GROWTH.get(year, 1.0)
        seasonality = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)

        for _, dc_row in dc_orgs.iterrows():
            org_key = int(dc_row["OrgKey"])
            rng     = _rng_for(org_key, salt=date_key % 400)

            for pk in dc_products:
                noise    = float(rng.uniform(0.80, 1.20))
                units    = max(0, int(_BASE_DAILY_UNITS_DC * growth * seasonality * noise))
                revenue  = round(units * avg_prices[pk], 2)

                rows.append({
                    "DateKey":        date_key,
                    "OrgKey":         org_key,
                    "ProductKey":     int(pk),
                    "Output Units":   float(units),
                    "Revenue Amount": revenue,
                })

    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_output", df, partition_by=["Fiscal Year"])
    print(f"  Written fact_output ({len(rows):,} rows) [{fmt}]")


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def _resolve_keys() -> tuple[pd.DataFrame, list[int]]:
    org_df = pd.concat(
        [pd.read_parquet(p) for p in sorted((DIMS / "dim_org").rglob("*.parquet"))],
        ignore_index=True,
    )
    product_keys = [1, 2]
    try:
        for p in sorted((DIMS / "dim_product").rglob("*.parquet")):
            pdf = pd.read_parquet(p)
            product_keys = pdf["ProductKey"].dropna().astype(int).tolist()
            break
    except Exception:
        pass
    return org_df, product_keys


if __name__ == "__main__":
    print("=== Finance Gold Data Generation ===")
    org_df, product_keys = _resolve_keys()
    print(f"  Loaded {len(org_df):,} orgs, {len(product_keys):,} products")

    generate_fact_finance(org_df)
    generate_fact_cost(org_df, product_keys)
    generate_fact_labor(org_df)
    generate_fact_output(org_df, product_keys)

    print("\n[OK] Finance gold data generation complete.")
