"""
Generate Supply Chain gold data (dim_lane, fact_inventory, fact_cogs, fact_fulfillment, fact_stockout, fact_forecast).
Contract-compliant per supply_chain.yaml. Uses shared utilities for realistic names, seasonality, and consistent time periods.

Run from repo root: py showcases/aurora_group/data/gold/generate_supply_chain_gold.py
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import random

# Import shared utilities
gold = Path(__file__).parent
sys_path = str(gold)
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from _company_profile import get_company_profile
from _generator_utils import (
    get_fact_date_range,
    get_fact_date_keys,
    apply_monthly_seasonality,
    apply_combined_seasonality,
    get_monthly_date_keys,
    write_fact_delta,
    FACTS_START,
    FACTS_END,
)
from _model_columns import fact_inventory_spalten  # A-24: COGS Amount aus fact_cogs

# Initialize
RANDOM_SEED = 12345
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

profile = get_company_profile("aurora")
dims = gold / "dimensions"
facts = gold / "facts"

# Resolve OrgKey, DateKey, ProductKey from existing gold if present
org_keys = [1, 2]
date_keys = get_fact_date_keys()  # Use standard 2020-2024 period
product_keys = [1, 2]

try:
    for p in (dims / "dim_org").rglob("*.parquet"):
        df = pd.read_parquet(p)
        if "OrgKey" in df.columns:
            org_keys = df["OrgKey"].dropna().unique().astype(int).tolist()[:20] or org_keys
        break
except Exception:
    pass

try:
    for p in (dims / "dim_product").rglob("*.parquet"):
        df = pd.read_parquet(p)
        if "ProductKey" in df.columns:
            product_keys = df["ProductKey"].dropna().unique().astype(int).tolist()[:50] or product_keys
        break
except Exception:
    pass

# dim_lane - Generate realistic lanes between DCs and countries
dim_lane_dir = dims / "dim_lane"
dim_lane_dir.mkdir(parents=True, exist_ok=True)
rows_lane = []

# Get DCs and countries from org structure
dc_orgs = []
country_codes = []
try:
    for p in (dims / "dim_org").rglob("*.parquet"):
        df = pd.read_parquet(p)
        if "OrgType" in df.columns and "OrgCode" in df.columns:
            dc_df = df[df["OrgType"] == "DC"]
            dc_orgs = dc_df["OrgCode"].tolist()[:10] or ["DC-NL", "DC-DE"]
            country_df = df[df["OrgType"] == "Country"]
            country_codes = country_df["Country"].dropna().unique().tolist()[:10] or ["DE", "AT", "NL"]
        break
except Exception:
    dc_orgs = ["DC-NL", "DC-DE", "DC-SE", "DC-IT", "DC-PL"]
    country_codes = ["DE", "AT", "NL", "BE", "SE", "NO", "IT", "ES", "PL", "CZ"]

modes = ["Road", "Rail", "Sea", "Air"]
lane_key = 1

# Generate lanes: each DC to multiple countries
for dc in dc_orgs[:8]:  # Use up to 8 DCs
    # Each DC serves 3-5 countries
    destinations = random.sample(country_codes, min(random.randint(3, 5), len(country_codes)))
    for dest in destinations:
        rows_lane.append({
            "LaneKey": lane_key,
            "Origin": dc,
            "Destination": dest,
            "Mode": random.choice(modes),
        })
        lane_key += 1

pd.DataFrame(rows_lane).to_parquet(dim_lane_dir / "part-00000.parquet", index=False)
print(f"Written dim_lane ({len(rows_lane)} lanes)")
lane_keys = [r["LaneKey"] for r in rows_lane]

# fact_inventory (location_sku_month) - Monthly snapshots with seasonality
fact_inv_dir = facts / "fact_inventory"
fact_inv_dir.mkdir(parents=True, exist_ok=True)
rows_inv = []

# Use month-end dates for inventory snapshots
fact_dates = get_fact_date_range()
month_end_dates = [d for d in fact_dates if d.is_month_end]

print(f"Generating fact_inventory for {len(month_end_dates)} months × {len(org_keys[:10])} orgs × {len(product_keys[:30])} products...")

for date_obj in month_end_dates:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # Apply seasonality to inventory levels (higher before peak seasons)
    seasonality_factor = apply_monthly_seasonality(
        date_obj,
        base_factor=1.0,
        seed=RANDOM_SEED,
    )
    # Inventory builds up before peak (1-2 months ahead)
    inventory_factor = seasonality_factor * random.uniform(1.0, 1.3)
    
    for ok in org_keys[:10]:  # Sample orgs (DCs and stores)
        for pk in product_keys[:30]:  # Sample products
            # Base inventory values
            base_units = 1000.0
            base_amount = 50000.0
            
            avg_inventory_units = max(10, int(base_units * inventory_factor * random.uniform(0.7, 1.3)))
            avg_inventory_amount = base_amount * inventory_factor * random.uniform(0.7, 1.3)
            
            # Obsolete inventory (2-5% of total)
            obsolete_pct = random.uniform(0.02, 0.05)
            obsolete_units = int(avg_inventory_units * obsolete_pct)
            obsolete_amount = avg_inventory_amount * obsolete_pct
            
            rows_inv.append({
                "DateKey": date_key,
                "OrgKey": ok,
                "ProductKey": pk,
                "Average Inventory Amount": round(avg_inventory_amount, 2),
                "Average Inventory Units": float(avg_inventory_units),
                "Obsolete Inventory Amount": round(obsolete_amount, 2),
                "Obsolete Inventory Units": float(obsolete_units),
            })

# fact_inventory wird erst nach fact_cogs geschrieben: die Finance-Sicht liest dort `COGS Amount`
# derselben Koernung (A-24). Schreiben zieht keine Zufallszahlen, die Reihenfolge der Ziehungen bleibt.

# fact_cogs (location_sku_month) - Monthly COGS with seasonality
fact_cogs_dir = facts / "fact_cogs"
fact_cogs_dir.mkdir(parents=True, exist_ok=True)
rows_cogs = []

print(f"Generating fact_cogs for {len(month_end_dates)} months × {len(org_keys[:10])} orgs × {len(product_keys[:30])} products...")

for date_obj in month_end_dates:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # COGS follows sales seasonality
    seasonality_factor = apply_monthly_seasonality(
        date_obj,
        base_factor=1.0,
        seed=RANDOM_SEED,
    )
    
    for ok in org_keys[:10]:
        for pk in product_keys[:30]:
            base_cogs = 40000.0
            cogs_amount = base_cogs * seasonality_factor * random.uniform(0.85, 1.15)
            
            rows_cogs.append({
                "DateKey": date_key,
                "OrgKey": ok,
                "ProductKey": pk,
                "COGS Amount": round(cogs_amount, 2),
            })

fmt = write_fact_delta(fact_cogs_dir, pd.DataFrame(rows_cogs), partition_by=["Fiscal Year"])
print(f"Written fact_cogs ({len(rows_cogs):,} records) [{fmt}]")

fmt = write_fact_delta(fact_inv_dir, fact_inventory_spalten(pd.DataFrame(rows_inv), pd.DataFrame(rows_cogs)),
                       partition_by=["Fiscal Year"])
print(f"Written fact_inventory ({len(rows_inv):,} records) [{fmt}]")

# fact_fulfillment (order grain) - Daily orders with seasonality
fact_fulfill_dir = facts / "fact_fulfillment"
fact_fulfill_dir.mkdir(parents=True, exist_ok=True)
rows_fulfill = []

# Sample dates (daily or every few days)
sampled_dates_fulfill = fact_dates[::1]  # Daily

print(f"Generating fact_fulfillment for {len(sampled_dates_fulfill)} dates × {len(org_keys[:5])} orgs × {len(product_keys[:15])} products × {len(lane_keys[:5])} lanes...")

for date_obj in sampled_dates_fulfill:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # Apply seasonality to order volume
    seasonality_factor = apply_combined_seasonality(
        date_obj,
        base_factor=1.0,
        monthly_weight=0.6,
        weekly_weight=0.4,
        seed=RANDOM_SEED,
    )
    
    # Number of orders per day varies with seasonality
    orders_per_day = max(1, int(5 * seasonality_factor))
    
    for _ in range(orders_per_day):
        ok = random.choice(org_keys[:5])
        pk = random.choice(product_keys[:15])
        lk = random.choice(lane_keys[:5])
        
        # OTIF metrics (85-95% success rates)
        otif_flag = random.random() < 0.90
        on_time_flag = random.random() < 0.92
        in_full_flag = random.random() < 0.95
        order_correct_flag = random.random() < 0.98
        
        order_qty = max(10, int(100 * seasonality_factor * random.uniform(0.7, 1.3)))
        
        # Penalties and expedite costs only if not OTIF
        penalty_amount = random.uniform(100, 500) if not otif_flag else 0.0
        expedite_cost = random.uniform(200, 800) if not on_time_flag else 0.0
        
        rows_fulfill.append({
            "DateKey": date_key,
            "OrgKey": ok,
            "ProductKey": pk,
            "LaneKey": lk,
            "OTIF Flag": otif_flag,
            "On-Time Flag": on_time_flag,
            "In-Full Flag": in_full_flag,
            "Order Correct Flag": order_correct_flag,
            "Order Qty": float(order_qty),
            "Penalty Amount": round(penalty_amount, 2),
            "Expedite Cost": round(expedite_cost, 2),
        })

fmt = write_fact_delta(fact_fulfill_dir, pd.DataFrame(rows_fulfill), partition_by=["Fiscal Year"])
print(f"Written fact_fulfillment ({len(rows_fulfill):,} records) [{fmt}]")

# fact_stockout (location_sku_day) - Daily stockout tracking with seasonality
fact_stock_dir = facts / "fact_stockout"
fact_stock_dir.mkdir(parents=True, exist_ok=True)
rows_stock = []

# Sample dates (daily)
sampled_dates_stock = fact_dates[::1]  # Daily

print(f"Generating fact_stockout for {len(sampled_dates_stock)} dates × {len(org_keys[:8])} orgs × {len(product_keys[:20])} products...")

for date_obj in sampled_dates_stock:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # Apply seasonality to demand
    seasonality_factor = apply_combined_seasonality(
        date_obj,
        base_factor=1.0,
        monthly_weight=0.6,
        weekly_weight=0.4,
        seed=RANDOM_SEED,
    )
    
    for ok in org_keys[:8]:
        for pk in product_keys[:20]:
            # Stockout occurs 2-5% of the time
            stockout_flag = random.random() < random.uniform(0.02, 0.05)
            
            demand_units = max(100, int(500 * seasonality_factor * random.uniform(0.8, 1.2)))
            lost_demand_units = int(demand_units * random.uniform(0.1, 0.3)) if stockout_flag else 0.0
            
            rows_stock.append({
                "DateKey": date_key,
                "OrgKey": ok,
                "ProductKey": pk,
                "Stockout Flag": stockout_flag,
                "Lost Demand Units": float(lost_demand_units),
                "Demand Units": float(demand_units),
            })

fmt = write_fact_delta(fact_stock_dir, pd.DataFrame(rows_stock), partition_by=["Fiscal Year"])
print(f"Written fact_stockout ({len(rows_stock):,} records) [{fmt}]")

# fact_forecast (sku_month) - Monthly forecasts for full period with seasonality
fact_forecast_dir = facts / "fact_forecast"
fact_forecast_dir.mkdir(parents=True, exist_ok=True)
rows_forecast = []

# Use month-end dates for forecasts (FIXED: was only using 6 dates, now uses full period)
forecast_versions = ["v1", "v2", "v3"]  # Multiple forecast versions

print(f"Generating fact_forecast for {len(month_end_dates)} months × {len(product_keys[:40])} products × {len(org_keys[:10])} orgs × {len(forecast_versions)} versions...")

for date_obj in month_end_dates:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # Apply seasonality to forecast
    seasonality_factor = apply_monthly_seasonality(
        date_obj,
        base_factor=1.0,
        seed=RANDOM_SEED,
    )
    
    for pk in product_keys[:40]:  # More products
        for ok in org_keys[:10]:  # More orgs
            base_forecast = 800.0
            forecast_units = max(10, int(base_forecast * seasonality_factor * random.uniform(0.8, 1.2)))
            
            # Generate multiple forecast versions
            for version in forecast_versions:
                # Version variation: v2 is +5%, v3 is +10% (optimistic)
                version_factor = 1.0 if version == "v1" else (1.05 if version == "v2" else 1.10)
                version_forecast = int(forecast_units * version_factor)
                
                rows_forecast.append({
                    "DateKey": date_key,
                    "ProductKey": pk,
                    "OrgKey": ok,
                    "Forecast Units": float(version_forecast),
                    "Forecast Version": version,
                })

fmt = write_fact_delta(fact_forecast_dir, pd.DataFrame(rows_forecast), partition_by=["Fiscal Year"])
print(f"Written fact_forecast ({len(rows_forecast):,} records) [{fmt}]")

# fact_procurement — OWNED BY generate_gapfill_gold.py (SCM-004).
# It is now generated at purchase_order_line grain there (auditable PPV), superseding the
# former dc_vendor_month block that lived here. Do not re-add a monthly fact_procurement here.

print("\n[OK] Supply Chain gold data generation complete!")
