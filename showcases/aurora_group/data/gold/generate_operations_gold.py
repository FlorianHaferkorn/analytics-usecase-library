"""
Generate Operations gold data (dim_asset, fact_ops, fact_ops_failures, fact_maintenance, fact_quality).
Contract-compliant per operations.yaml. Uses shared utilities for realistic names, seasonality, and consistent time periods.

Run from repo root: py showcases/aurora_group/data/gold/generate_operations_gold.py
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

# Import shared utilities
gold = Path(__file__).parent
sys_path = str(gold)
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from _company_profile import get_company_profile
from _realistic_names import generate_asset_name
from _generator_utils import (
    get_fact_date_range,
    get_fact_date_keys,
    apply_monthly_seasonality,
    apply_combined_seasonality,
    FACTS_START,
    FACTS_END,
)

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

# dim_asset (operations.yaml)
dim_asset_dir = dims / "dim_asset"
dim_asset_dir.mkdir(parents=True, exist_ok=True)
rows_asset = []

# Generate more realistic assets (10-15 assets across orgs)
asset_classes = ["Production Line", "Packaging Station", "Quality Control", "Warehouse", "Assembly Line", "Finishing Station"]
criticality_levels = ["High", "Medium", "Low"]

asset_key = 1000
for i, ok in enumerate(org_keys[:10]):  # Use more orgs
    asset_class = random.choice(asset_classes)
    criticality = criticality_levels[0] if i < 3 else (criticality_levels[1] if i < 7 else criticality_levels[2])
    
    asset_name = generate_asset_name(
        asset_class=asset_class,
        profile=profile,
        asset_key=asset_key,
        seed=RANDOM_SEED,
    )
    
    rows_asset.append({
        "AssetKey": asset_key,
        "AssetCode": f"A{asset_key:04d}",
        "AssetName": asset_name,
        "AssetClass": asset_class,
        "Criticality": criticality,
        "OrgKey": ok,
    })
    asset_key += 1

pd.DataFrame(rows_asset).to_parquet(dim_asset_dir / "part-00000.parquet", index=False)
print(f"Written dim_asset ({len(rows_asset)} assets)")

asset_keys = [r["AssetKey"] for r in rows_asset]

# fact_ops (line_day grain) - Daily data with seasonality
fact_ops_dir = facts / "fact_ops"
fact_ops_dir.mkdir(parents=True, exist_ok=True)
rows_ops = []

# Use full date range, but sample daily (or every few days for performance)
fact_dates = get_fact_date_range()
sampled_dates = fact_dates[::1]  # Every day (can change to ::7 for weekly)

print(f"Generating fact_ops for {len(sampled_dates)} dates × {len(org_keys[:5])} orgs × {len(asset_keys[:8])} assets...")

for date_obj in sampled_dates:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # Apply seasonality to production output
    seasonality_factor = apply_combined_seasonality(
        date_obj,
        base_factor=1.0,
        monthly_weight=0.7,  # Production more affected by monthly patterns
        weekly_weight=0.3,
        seed=RANDOM_SEED,
    )
    
    for ok in org_keys[:5]:  # Sample orgs
        for ak in asset_keys[:8]:  # Sample assets
            # Base values with seasonality
            base_output = 5000.0
            base_good = 4800.0
            base_scrap = 200.0
            
            # Apply seasonality and random variation
            output_units = max(100, int(base_output * seasonality_factor * random.uniform(0.85, 1.15)))
            good_units = max(0, int(output_units * random.uniform(0.92, 0.98)))
            scrap_units = output_units - good_units
            
            # Time calculations
            planned_minutes = 480.0
            run_minutes = planned_minutes * random.uniform(0.85, 0.95)  # 85-95% utilization
            downtime_minutes = planned_minutes - run_minutes
            standard_rate = output_units / max(run_minutes, 1)
            
            rows_ops.append({
                "DateKey": date_key,
                "OrgKey": ok,
                "AssetKey": ak,
                "Planned Time Minutes": round(planned_minutes, 2),
                "Run Time Minutes": round(run_minutes, 2),
                "Downtime Minutes": round(downtime_minutes, 2),
                "Output Units": float(output_units),
                "Good Units": float(good_units),
                "Scrap Units": float(scrap_units),
                "Standard Rate Units Per Minute": round(standard_rate, 2),
            })

pd.DataFrame(rows_ops).to_parquet(fact_ops_dir / "part-00000.parquet", index=False)
print(f"Written fact_ops ({len(rows_ops):,} records)")

# fact_ops_failures (failure_event grain) - Sparse events
fact_fail_dir = facts / "fact_ops_failures"
fact_fail_dir.mkdir(parents=True, exist_ok=True)
rows_fail = []

# Generate failures across the time period (sparse: ~1-2 per asset per month)
failure_causes = ["Mechanical", "Electrical", "Software", "Material", "Operator Error"]
failure_count = 0

for ak in asset_keys[:10]:  # All assets can have failures
    # Generate 1-2 failures per month per asset
    months = pd.date_range(start=FACTS_START, end=FACTS_END, freq='MS')
    for month_start in months[:60]:  # Limit to 60 months
        if random.random() < 0.3:  # 30% chance of failure in this month
            # Random day in month
            days_in_month = (month_start + pd.offsets.MonthEnd()).day
            failure_day = random.randint(1, days_in_month)
            failure_date = month_start.replace(day=failure_day)
            
            # Random time during work hours (6 AM - 6 PM)
            hour = random.randint(6, 17)
            minute = random.randint(0, 59)
            start_dt = failure_date.replace(hour=hour, minute=minute)
            
            # Duration: 1-6 hours
            duration_hours = random.uniform(1.0, 6.0)
            end_dt = start_dt + timedelta(hours=duration_hours)
            downtime_minutes = duration_hours * 60
            
            rows_fail.append({
                "AssetKey": ak,
                "Failure Start DateTime": start_dt,
                "Failure End DateTime": end_dt,
                "Repair Duration Hours": round(duration_hours, 2),
                "Downtime Minutes": round(downtime_minutes, 2),
                "Cause Code": random.choice(failure_causes),
            })
            failure_count += 1

pd.DataFrame(rows_fail).to_parquet(fact_fail_dir / "part-00000.parquet", index=False)
print(f"Written fact_ops_failures ({len(rows_fail):,} failure events)")

# fact_maintenance (maintenance_order grain) - Monthly PM schedules
fact_maint_dir = facts / "fact_maintenance"
fact_maint_dir.mkdir(parents=True, exist_ok=True)
rows_maint = []

# Generate maintenance orders (PM schedules monthly, some ad-hoc)
order_types = ["PM", "CM", "EM"]  # Preventive, Corrective, Emergency
order_statuses = ["Completed", "In Progress", "Scheduled", "Cancelled"]
on_time_rate = 0.85  # 85% on-time

for ak in asset_keys[:10]:
    # Monthly PM schedules
    months = pd.date_range(start=FACTS_START, end=FACTS_END, freq='MS')
    for month_start in months[:60]:
        # PM order (scheduled for month-end)
        pm_date = month_start + pd.offsets.MonthEnd()
        pm_datekey = int(pm_date.strftime('%Y%m%d'))
        
        rows_maint.append({
            "AssetKey": ak,
            "DateKey": pm_datekey,
            "Order Type": "PM",
            "Order Status": "Completed" if random.random() < 0.9 else random.choice(["In Progress", "Scheduled"]),
            "On Time Flag": random.random() < on_time_rate,
            "Parts Stockout Flag": random.random() < 0.1,  # 10% stockout rate
        })
        
        # Occasional CM (corrective maintenance) - 20% chance
        if random.random() < 0.2:
            cm_date = month_start + timedelta(days=random.randint(1, 28))
            cm_datekey = int(cm_date.strftime('%Y%m%d'))
            rows_maint.append({
                "AssetKey": ak,
                "DateKey": cm_datekey,
                "Order Type": "CM",
                "Order Status": random.choice(["Completed", "In Progress"]),
                "On Time Flag": random.random() < 0.7,  # Lower on-time for CM
                "Parts Stockout Flag": random.random() < 0.15,
            })

pd.DataFrame(rows_maint).to_parquet(fact_maint_dir / "part-00000.parquet", index=False)
print(f"Written fact_maintenance ({len(rows_maint):,} maintenance orders)")

# fact_quality (line_day grain) - Daily quality metrics with seasonality
fact_qual_dir = facts / "fact_quality"
fact_qual_dir.mkdir(parents=True, exist_ok=True)
rows_qual = []

# Sample dates (can be daily or weekly)
sampled_dates_qual = fact_dates[::1]  # Daily

print(f"Generating fact_quality for {len(sampled_dates_qual)} dates × {len(org_keys[:5])} orgs × {len(product_keys[:20])} products...")

for date_obj in sampled_dates_qual:
    date_key = int(date_obj.strftime('%Y%m%d'))
    
    # Apply seasonality to production volume (affects quality metrics)
    seasonality_factor = apply_combined_seasonality(
        date_obj,
        base_factor=1.0,
        monthly_weight=0.6,
        weekly_weight=0.4,
        seed=RANDOM_SEED,
    )
    
    for ok in org_keys[:5]:
        for pk in product_keys[:20]:
            # Base values
            base_total = 1000.0
            total_units = max(100, int(base_total * seasonality_factor * random.uniform(0.9, 1.1)))
            
            # Quality metrics (good units rate varies 92-98%)
            good_rate = random.uniform(0.92, 0.98)
            good_units = int(total_units * good_rate)
            scrap_units = int(total_units * random.uniform(0.01, 0.05))
            rework_units = int(total_units * random.uniform(0.01, 0.03))
            defect_count = max(0, int(total_units * random.uniform(0.002, 0.008)))
            
            rows_qual.append({
                "DateKey": date_key,
                "OrgKey": ok,
                "ProductKey": pk,
                "Total Units": float(total_units),
                "Good Units": float(good_units),
                "Scrap Units": float(scrap_units),
                "Rework Units": float(rework_units),
                "Defect Count": float(defect_count),
            })

pd.DataFrame(rows_qual).to_parquet(fact_qual_dir / "part-00000.parquet", index=False)
print(f"Written fact_quality ({len(rows_qual):,} records)")

print("\n[OK] Operations gold data generation complete!")
