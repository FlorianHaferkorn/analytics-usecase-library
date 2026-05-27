"""
Generate synthetic Parquet data for 3 missing fact tables:
  - fact_quality_costs   (OPS-003: COPQ, Scrap/Rework/Warranty Cost)
  - fact_complaints      (OPS-003: Complaint Count per entity-month)
  - fact_supplier_risk   (FIN-001: Supplier Risk Score per supplier-month)

Uses same seed, company profile, and partition structure as existing generators.
Run from repo root: python3 showcases/aurora_group/data/gold/generate_missing_facts.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import random

# ── Setup paths ───────────────────────────────────────────────────────────────
GOLD = Path(__file__).parent
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))

from _generator_utils import (
    get_fact_date_keys,
    write_fact_delta,
    FACTS_START,
    FACTS_END,
)

RANDOM_SEED = 12345
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

FACTS_DIR = GOLD / "facts"
DIMS_DIR = GOLD / "dimensions"

# ── Resolve dimension keys ────────────────────────────────────────────────────
def load_keys(dim_name: str, key_col: str, fallback: list) -> list:
    """Load unique keys from a dimension Parquet, fall back to stub list."""
    for p in (DIMS_DIR / dim_name).rglob("*.parquet"):
        try:
            df = pd.read_parquet(p)
            if key_col in df.columns:
                keys = df[key_col].dropna().unique().astype(int).tolist()
                if keys:
                    return keys[:20]
        except Exception:
            pass
    return fallback

org_keys = load_keys("dim_org", "OrgKey", [1, 2])
product_keys = load_keys("dim_product", "ProductKey", [1, 2, 3])
supplier_keys = load_keys("dim_supplier", "SupplierKey", [1, 2, 3, 4])
date_keys = get_fact_date_keys()  # full 2020-2024 monthly DateKeys

print(f"OrgKeys: {org_keys[:5]}  ProductKeys: {product_keys[:5]}")
print(f"SupplierKeys: {supplier_keys[:5]}  DateKeys: {len(date_keys)} rows")


# ── 1. fact_quality_costs ─────────────────────────────────────────────────────
print("\n[1/3] Generating fact_quality_costs ...")

rows = []
for date_key in date_keys:
    year = date_key // 10000
    month = (date_key % 10000) // 100
    for org_key in org_keys:
        for prod_key in product_keys:
            # Scrap / Rework costs driven by quality defects
            base_scrap = np.random.lognormal(mean=8.5, sigma=0.4)
            base_rework = base_scrap * np.random.uniform(0.3, 0.6)
            warranty = base_scrap * np.random.uniform(0.05, 0.20)
            copq = base_scrap + base_rework + warranty
            # Year-over-year improvement: ~3% pa
            improvement = (1 - 0.03) ** (year - 2020)
            rows.append({
                "DateKey": date_key,
                "OrgKey": org_key,
                "ProductKey": prod_key,
                "COPQ Amount": round(copq * improvement, 2),
                "Scrap Cost Amount": round(base_scrap * improvement, 2),
                "Rework Cost Amount": round(base_rework * improvement, 2),
                "Warranty Cost Amount": round(warranty * improvement, 2),
            })

df_qc = pd.DataFrame(rows)
df_qc["Fiscal Year"] = df_qc["DateKey"].apply(
    lambda k: f"{k // 10000}" if (k % 10000) // 100 >= 4 else f"{k // 10000}"
)
print(f"  Rows: {len(df_qc):,}")
write_fact_delta(FACTS_DIR / "fact_quality_costs", df_qc, partition_by=["Fiscal Year"])
print("  ✅ fact_quality_costs written")


# ── 2. fact_complaints ────────────────────────────────────────────────────────
print("\n[2/3] Generating fact_complaints ...")

# Need CustomerKey — derive from org_keys as proxy (customer segments per org)
customer_keys = list(range(1, min(len(org_keys) * 3 + 1, 16)))

rows = []
for date_key in date_keys:
    year = date_key // 10000
    month = (date_key % 10000) // 100
    for org_key in org_keys:
        # 2-5 complaints per org per month on average
        n_complaints = int(np.random.poisson(lam=3.5))
        if n_complaints == 0:
            continue
        complaint_count = n_complaints
        resolved_count = max(0, int(complaint_count * np.random.uniform(0.7, 1.0)))
        resolution_days = round(np.random.lognormal(mean=1.8, sigma=0.5), 1)
        customer_key = random.choice(customer_keys)
        rows.append({
            "DateKey": date_key,
            "OrgKey": org_key,
            "CustomerKey": customer_key,
            "Complaint Count": complaint_count,
            "Resolved Count": resolved_count,
            "Resolution Days": resolution_days,
        })

df_comp = pd.DataFrame(rows)
df_comp["Fiscal Year"] = df_comp["DateKey"].apply(lambda k: str(k // 10000))
print(f"  Rows: {len(df_comp):,}")
write_fact_delta(FACTS_DIR / "fact_complaints", df_comp, partition_by=["Fiscal Year"])
print("  ✅ fact_complaints written")


# ── 3. fact_supplier_risk ─────────────────────────────────────────────────────
print("\n[3/3] Generating fact_supplier_risk ...")

rows = []
# Assign each supplier a base risk profile (consistent across time)
supplier_base = {
    sk: {
        "delivery": np.random.uniform(1.5, 4.5),
        "quality": np.random.uniform(1.0, 4.0),
        "financial": np.random.uniform(1.0, 5.0),
    }
    for sk in supplier_keys
}

for date_key in date_keys:
    year = date_key // 10000
    for supplier_key in supplier_keys:
        base = supplier_base[supplier_key]
        # Monthly variation ± 15%
        delivery_risk = round(min(10, max(0, base["delivery"] * np.random.uniform(0.85, 1.15))), 2)
        quality_risk = round(min(10, max(0, base["quality"] * np.random.uniform(0.85, 1.15))), 2)
        financial_risk = round(min(10, max(0, base["financial"] * np.random.uniform(0.90, 1.10))), 2)
        composite = round((delivery_risk * 0.4 + quality_risk * 0.35 + financial_risk * 0.25), 2)
        rows.append({
            "DateKey": date_key,
            "SupplierKey": supplier_key,
            "Risk Score": composite,
            "Delivery Risk Score": delivery_risk,
            "Quality Risk Score": quality_risk,
            "Financial Risk Score": financial_risk,
        })

df_sr = pd.DataFrame(rows)
df_sr["Fiscal Year"] = df_sr["DateKey"].apply(lambda k: str(k // 10000))
print(f"  Rows: {len(df_sr):,}")
write_fact_delta(FACTS_DIR / "fact_supplier_risk", df_sr, partition_by=["Fiscal Year"])
print("  ✅ fact_supplier_risk written")

print("\n✅ All 3 missing fact tables generated successfully.")
print(f"   fact_quality_costs : {FACTS_DIR / 'fact_quality_costs'}")
print(f"   fact_complaints    : {FACTS_DIR / 'fact_complaints'}")
print(f"   fact_supplier_risk : {FACTS_DIR / 'fact_supplier_risk'}")
