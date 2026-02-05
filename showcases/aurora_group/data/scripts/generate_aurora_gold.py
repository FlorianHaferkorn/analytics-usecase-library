"""
Generate all Aurora gold data from a single entry point.

Creates dimensions and facts for Commercial, Operations, Supply Chain, Experience, and Finance
in showcases/aurora_group/data/gold/ using final table names (e.g. dim_case_queue,
fact_support_cases, fact_accounts_payable, fact_cash_position, fact_cash_flow).

Uses shared utilities for realistic names, seasonality, and consistent time periods.

Run from repo root:
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain operations
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain supply_chain,experience,finance

Domains: commercial, operations, supply_chain, experience, finance (default: all).
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import random
import sys

gold = (Path(__file__).resolve().parent.parent / "gold")
dims = gold / "dimensions"
facts = gold / "facts"

# Import shared utilities
sys_path = str(gold)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from _company_profile import get_company_profile
from _realistic_names import generate_promo_name
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

DOMAINS = frozenset({"commercial", "operations", "supply_chain", "experience", "finance"})


def _resolve_keys():
    org_keys = [1, 2]
    date_keys = get_fact_date_keys()  # Use standard 2020-2024 period
    product_keys = [1, 2]
    customer_keys = [1, 2]
    for p in (dims / "dim_org").rglob("*.parquet"):
        try:
            df = pd.read_parquet(p)
            if "OrgKey" in df.columns:
                org_keys = df["OrgKey"].dropna().unique().astype(int).tolist()[:20] or org_keys
            break
        except Exception:
            break
    for p in (dims / "dim_product").rglob("*.parquet"):
        try:
            df = pd.read_parquet(p)
            if "ProductKey" in df.columns:
                product_keys = df["ProductKey"].dropna().unique().astype(int).tolist()[:50] or product_keys
            break
        except Exception:
            pass
    for p in (dims / "dim_customer").rglob("*.parquet"):
        try:
            df = pd.read_parquet(p)
            if "CustomerKey" in df.columns:
                customer_keys = df["CustomerKey"].dropna().unique().astype(int).tolist()[:50] or customer_keys
            break
        except Exception:
            break
    return org_keys, date_keys, product_keys, customer_keys


def run_operations(org_keys, date_keys, product_keys):
    # dim_asset
    dim_asset_dir = dims / "dim_asset"
    dim_asset_dir.mkdir(parents=True, exist_ok=True)
    rows_asset = []
    for i, ok in enumerate(org_keys[:5]):
        rows_asset.append({
            "AssetKey": 1000 + i,
            "AssetCode": f"A{i+1:03d}",
            "AssetName": f"Line Asset {i+1}",
            "AssetClass": "Production Line",
            "Criticality": "High" if i < 2 else "Medium",
            "OrgKey": ok,
        })
    pd.DataFrame(rows_asset).to_parquet(dim_asset_dir / "part-00000.parquet", index=False)
    print("Written dim_asset")
    asset_keys = [r["AssetKey"] for r in rows_asset]

    # fact_ops
    (facts / "fact_ops").mkdir(parents=True, exist_ok=True)
    rows_ops = []
    for dk in date_keys[:6]:
        for ok in org_keys[:2]:
            for ak in asset_keys[:2]:
                rows_ops.append({
                    "DateKey": dk, "OrgKey": ok, "AssetKey": ak,
                    "Planned Time Minutes": 480.0, "Run Time Minutes": 420.0, "Downtime Minutes": 60.0,
                    "Output Units": 5000.0, "Good Units": 4800.0, "Scrap Units": 200.0,
                    "Standard Rate Units Per Minute": 12.0,
                })
    pd.DataFrame(rows_ops).to_parquet(facts / "fact_ops" / "part-00000.parquet", index=False)
    print("Written fact_ops")

    # fact_ops_failures
    base_dt = datetime(2024, 1, 15, 8, 0, 0)
    (facts / "fact_ops_failures").mkdir(parents=True, exist_ok=True)
    rows_fail = []
    for i, ak in enumerate(asset_keys[:2]):
        rows_fail.append({
            "AssetKey": ak,
            "Failure Start DateTime": base_dt,
            "Failure End DateTime": base_dt.replace(hour=10, minute=30),
            "Repair Duration Hours": 2.5, "Downtime Minutes": 150.0, "Cause Code": "Mechanical",
        })
    pd.DataFrame(rows_fail).to_parquet(facts / "fact_ops_failures" / "part-00000.parquet", index=False)
    print("Written fact_ops_failures")

    # fact_maintenance
    (facts / "fact_maintenance").mkdir(parents=True, exist_ok=True)
    rows_maint = []
    for ak in asset_keys[:3]:
        for dk in date_keys[:3]:
            rows_maint.append({
                "AssetKey": ak, "DateKey": dk,
                "Order Type": "PM", "Order Status": "Completed", "On Time Flag": True, "Parts Stockout Flag": False,
            })
    pd.DataFrame(rows_maint).to_parquet(facts / "fact_maintenance" / "part-00000.parquet", index=False)
    print("Written fact_maintenance")

    # fact_quality
    (facts / "fact_quality").mkdir(parents=True, exist_ok=True)
    rows_qual = []
    for dk in date_keys[:4]:
        for ok in org_keys[:2]:
            for pk in product_keys[:2]:
                rows_qual.append({
                    "DateKey": dk, "OrgKey": ok, "ProductKey": pk,
                    "Total Units": 1000.0, "Good Units": 950.0, "Scrap Units": 30.0,
                    "Rework Units": 20.0, "Defect Count": 5.0,
                })
    pd.DataFrame(rows_qual).to_parquet(facts / "fact_quality" / "part-00000.parquet", index=False)
    print("Written fact_quality")


def run_supply_chain(org_keys, date_keys, product_keys):
    # dim_lane
    (dims / "dim_lane").mkdir(parents=True, exist_ok=True)
    rows_lane = [
        {"LaneKey": 1, "Origin": "DC-NL", "Destination": "DE", "Mode": "Road"},
        {"LaneKey": 2, "Origin": "DC-DE", "Destination": "AT", "Mode": "Road"},
    ]
    pd.DataFrame(rows_lane).to_parquet(dims / "dim_lane" / "part-00000.parquet", index=False)
    print("Written dim_lane")
    lane_keys = [r["LaneKey"] for r in rows_lane]

    # fact_inventory, fact_cogs, fact_fulfillment, fact_stockout, fact_forecast
    for name, key_extra, rows_fn in [
        ("fact_inventory", None, lambda: [
            {"DateKey": dk, "OrgKey": ok, "ProductKey": pk,
             "Average Inventory Amount": 50000.0, "Average Inventory Units": 1000.0,
             "Obsolete Inventory Amount": 1000.0, "Obsolete Inventory Units": 20.0}
            for dk in date_keys[:6] for ok in org_keys[:2] for pk in product_keys[:3]
        ]),
        ("fact_cogs", None, lambda: [
            {"DateKey": dk, "OrgKey": ok, "ProductKey": pk, "COGS Amount": 40000.0}
            for dk in date_keys[:6] for ok in org_keys[:2] for pk in product_keys[:3]
        ]),
        ("fact_fulfillment", lane_keys, lambda: [
            {"DateKey": dk, "OrgKey": ok, "ProductKey": pk, "LaneKey": lk,
             "OTIF Flag": True, "On-Time Flag": True, "In-Full Flag": True, "Order Correct Flag": True,
             "Order Qty": 100.0, "Penalty Amount": 0.0, "Expedite Cost": 0.0}
            for dk in date_keys[:4] for ok in org_keys[:2] for pk in product_keys[:2] for lk in (lane_keys[:1])
        ]),
        ("fact_stockout", None, lambda: [
            {"DateKey": dk, "OrgKey": ok, "ProductKey": pk,
             "Stockout Flag": False, "Lost Demand Units": 0.0, "Demand Units": 500.0}
            for dk in date_keys[:6] for ok in org_keys[:2] for pk in product_keys[:2]
        ]),
        ("fact_forecast", None, lambda: [
            {"DateKey": dk, "ProductKey": pk, "OrgKey": ok, "Forecast Units": 800.0, "Forecast Version": "v1"}
            for dk in date_keys[:6] for pk in product_keys[:3] for ok in org_keys[:2]
        ]),
    ]:
        (facts / name).mkdir(parents=True, exist_ok=True)
        rows = rows_fn()
        pd.DataFrame(rows).to_parquet(facts / name / "part-00000.parquet", index=False)
        print(f"Written {name}")


def run_experience_promo(org_keys, date_keys, customer_keys):
    """Generate experience and promo facts with realistic data and seasonality."""
    # fact_experience - Customer complaints/experiences
    (facts / "fact_experience").mkdir(parents=True, exist_ok=True)
    rows_experience = []
    
    fact_dates = get_fact_date_range()
    sampled_dates = fact_dates[::7]  # Weekly sampling
    
    severity_levels = ["Low", "Medium", "High", "Critical"]
    complaint_types = ["Product Quality", "Delivery Issue", "Billing Error", "Service Complaint", "Return Request"]
    
    complaint_id = 1
    print(f"Generating fact_experience for {len(sampled_dates)} dates...")
    
    for date_obj in sampled_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # Apply seasonality: complaints increase during peak seasons (more transactions = more issues)
        seasonality_factor = apply_combined_seasonality(
            date_obj,
            base_factor=1.0,
            monthly_weight=0.6,
            weekly_weight=0.4,
            seed=RANDOM_SEED,
        )
        
        # Complaints per week: 10-50, varies with seasonality
        complaints_per_week = max(1, int(20 * seasonality_factor * random.uniform(0.7, 1.3)))
        
        for _ in range(complaints_per_week):
            rows_experience.append({
                "Complaint ID": f"CMP{complaint_id:08d}",
                "CustomerKey": random.choice(customer_keys[:50]),
                "OrgKey": random.choice(org_keys[:10]),
                "DateKey": date_key,
                "Severity": random.choices(severity_levels, weights=[0.5, 0.3, 0.15, 0.05])[0],
                "Complaint Type": random.choice(complaint_types),
            })
            complaint_id += 1
    
    pd.DataFrame(rows_experience).to_parquet(facts / "fact_experience" / "part-00000.parquet", index=False)
    print(f"Written fact_experience ({len(rows_experience):,} complaints)")

    # fact_promo - Promotion performance metrics
    (facts / "fact_promo").mkdir(parents=True, exist_ok=True)
    promo_keys = [1, 2, 3]
    dim_promo_path = dims / "dim_promo"
    if dim_promo_path.exists():
        parquets = list(dim_promo_path.glob("**/*.parquet"))
        if parquets:
            dim_promo_df = pd.read_parquet(parquets[0])
            if "PromoKey" in dim_promo_df.columns:
                promo_keys = dim_promo_df[dim_promo_df["PromoKey"] != -1]["PromoKey"].tolist()[:50] or [1]
    
    rows_promo = []
    print(f"Generating fact_promo for {len(promo_keys)} promotions...")
    
    for promo_key in promo_keys:
        # Base values with variation
        base_sales = 100000.0
        promo_cost = random.uniform(3000.0, 8000.0)
        funding_amount = promo_cost * random.uniform(0.4, 0.6)  # 40-60% funding
        
        # Baseline sales (non-promo period equivalent)
        baseline_sales = base_sales * random.uniform(0.8, 1.2)
        baseline_quantity = baseline_sales / random.uniform(80, 120)  # Unit price assumption
        baseline_non_promo = baseline_sales * random.uniform(0.75, 0.90)  # Non-promo baseline
        
        rows_promo.append({
            "PromoKey": promo_key,
            "Promo Cost": round(promo_cost, 2),
            "Funding Amount": round(funding_amount, 2),
            "Baseline Sales Amount": round(baseline_sales, 2),
            "Baseline Quantity": round(baseline_quantity, 2),
            "Baseline Non-Promo Sales Amount": round(baseline_non_promo, 2),
        })
    
    pd.DataFrame(rows_promo).to_parquet(facts / "fact_promo" / "data.parquet", index=False)
    print(f"Written fact_promo ({len(rows_promo)} promotions)")


def run_xd_finance(org_keys, date_keys, customer_keys):
    """XD (Experience) and Finance using final table names with realistic data and seasonality."""
    # dim_case_queue
    (dims / "dim_case_queue").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"QueueKey": 1, "QueueName": "Sales Support", "Channel": "Phone", "Region": "EMEA"},
        {"QueueKey": 2, "QueueName": "Technical Support", "Channel": "Email", "Region": "EMEA"},
        {"QueueKey": 3, "QueueName": "Billing", "Channel": "Chat", "Region": "EMEA"},
        {"QueueKey": 4, "QueueName": "Returns", "Channel": "Phone", "Region": "EMEA"},
        {"QueueKey": 5, "QueueName": "Sales Support", "Channel": "Phone", "Region": "Americas"},
    ]).to_parquet(dims / "dim_case_queue" / "part-00000.parquet", index=False)
    print("Written dim_case_queue")

    # dim_issue_type
    (dims / "dim_issue_type").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"IssueKey": 1, "IssueType": "Billing", "Severity": "Medium"},
        {"IssueKey": 2, "IssueType": "Technical", "Severity": "High"},
        {"IssueKey": 3, "IssueType": "Order", "Severity": "Low"},
        {"IssueKey": 4, "IssueType": "Delivery", "Severity": "Medium"},
        {"IssueKey": 5, "IssueType": "Product", "Severity": "High"},
    ]).to_parquet(dims / "dim_issue_type" / "part-00000.parquet", index=False)
    print("Written dim_issue_type")

    queue_keys = [1, 2, 3, 4, 5]
    issue_keys = [1, 2, 3, 4, 5]

    # fact_support_cases - Daily cases with seasonality
    (facts / "fact_support_cases").mkdir(parents=True, exist_ok=True)
    rows = []
    
    fact_dates = get_fact_date_range()
    sampled_dates = fact_dates[::1]  # Daily
    
    print(f"Generating fact_support_cases for {len(sampled_dates)} dates...")
    
    for date_obj in sampled_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # Apply seasonality: support cases increase with sales volume
        seasonality_factor = apply_combined_seasonality(
            date_obj,
            base_factor=1.0,
            monthly_weight=0.6,
            weekly_weight=0.4,
            seed=RANDOM_SEED,
        )
        
        cases_per_day = max(1, int(10 * seasonality_factor * random.uniform(0.8, 1.2)))
        
        for _ in range(cases_per_day):
            ok = random.choice(org_keys[:10])
            qk = random.choice(queue_keys)
            ik = random.choice(issue_keys)
            
            # SLA metrics (85-95% success rates)
            sla_met = random.random() < 0.90
            fcr_flag = random.random() < 0.75  # First contact resolution
            handle_time = random.uniform(8.0, 20.0)
            escalation = random.random() < 0.10
            backlog = random.random() < 0.05
            open_case = random.random() < 0.15
            
            rows.append({
                "DateKey": date_key, "OrgKey": ok, "QueueKey": qk, "IssueKey": ik,
                "SLA Met Flag": sla_met, "FCR Flag": fcr_flag, "Handle Time Minutes": round(handle_time, 2),
                "Escalation Flag": escalation, "Backlog Flag": backlog, "Open Case Flag": open_case,
            })
    
    pd.DataFrame(rows).to_parquet(facts / "fact_support_cases" / "part-00000.parquet", index=False)
    print(f"Written fact_support_cases ({len(rows):,} cases)")

    # fact_workforce_management - Daily workforce metrics
    (facts / "fact_workforce_management").mkdir(parents=True, exist_ok=True)
    rows = []
    
    print(f"Generating fact_workforce_management for {len(sampled_dates)} dates...")
    
    for date_obj in sampled_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # Workforce varies with seasonality (more staff during peak)
        seasonality_factor = apply_combined_seasonality(
            date_obj,
            base_factor=1.0,
            monthly_weight=0.7,
            weekly_weight=0.3,
            seed=RANDOM_SEED,
        )
        
        for ok in org_keys[:8]:
            for qk in queue_keys[:4]:
                work_time = 480.0 * seasonality_factor * random.uniform(0.95, 1.05)
                paid_time = work_time
                talk_time = work_time * random.uniform(0.70, 0.80)
                wrap_time = work_time * random.uniform(0.08, 0.12)
                idle_time = work_time * random.uniform(0.05, 0.08)
                overtime = max(0, work_time - 480.0) if work_time > 480.0 else 0.0
                shrinkage = work_time * random.uniform(0.02, 0.04)
                
                rows.append({
                    "DateKey": date_key, "OrgKey": ok, "QueueKey": qk,
                    "Work Time Minutes": round(work_time, 2), "Paid Time Minutes": round(paid_time, 2),
                    "Talk Time Minutes": round(talk_time, 2), "Wrap Time Minutes": round(wrap_time, 2),
                    "Idle Time Minutes": round(idle_time, 2), "Overtime Minutes": round(overtime, 2),
                    "Shrinkage Minutes": round(shrinkage, 2),
                })
    
    pd.DataFrame(rows).to_parquet(facts / "fact_workforce_management" / "part-00000.parquet", index=False)
    print(f"Written fact_workforce_management ({len(rows):,} records)")

    # fact_accounts_payable - Monthly AP with seasonality
    (facts / "fact_accounts_payable").mkdir(parents=True, exist_ok=True)
    supplier_keys = [1, 2, 3, 4, 5, 6, 7, 8]
    rows = []
    
    month_end_dates = [d for d in fact_dates if d.is_month_end]
    
    print(f"Generating fact_accounts_payable for {len(month_end_dates)} months...")
    
    for date_obj in month_end_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # AP follows COGS seasonality
        seasonality_factor = apply_monthly_seasonality(
            date_obj,
            base_factor=1.0,
            seed=RANDOM_SEED,
        )
        
        for ok in org_keys[:10]:
            for sk in supplier_keys:
                base_ap = 10000.0 + sk * 1000
                ap_amount = base_ap * seasonality_factor * random.uniform(0.85, 1.15)
                cogs_amount = ap_amount * random.uniform(0.75, 0.90)
                
                rows.append({
                    "DateKey": date_key, "OrgKey": ok, "SupplierKey": sk,
                    "AP Amount": round(ap_amount, 2), "COGS Amount": round(cogs_amount, 2),
                })
    
    pd.DataFrame(rows).to_parquet(facts / "fact_accounts_payable" / "part-00000.parquet", index=False)
    print(f"Written fact_accounts_payable ({len(rows):,} records)")

    # fact_accounts_receivable - Monthly AR with seasonality
    (facts / "fact_accounts_receivable").mkdir(parents=True, exist_ok=True)
    rows = []
    
    print(f"Generating fact_accounts_receivable for {len(month_end_dates)} months...")
    
    for date_obj in month_end_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # AR follows sales seasonality
        seasonality_factor = apply_monthly_seasonality(
            date_obj,
            base_factor=1.0,
            seed=RANDOM_SEED,
        )
        
        for ok in org_keys[:10]:
            for ck in customer_keys[:20]:
                base_ar = 5000.0 + ck * 200
                ar_amount = base_ar * seasonality_factor * random.uniform(0.85, 1.15)
                revenue_amount = ar_amount * random.uniform(1.1, 1.3)
                
                rows.append({
                    "DateKey": date_key, "OrgKey": ok, "CustomerKey": ck,
                    "AR Amount": round(ar_amount, 2), "Revenue Amount": round(revenue_amount, 2),
                })
    
    pd.DataFrame(rows).to_parquet(facts / "fact_accounts_receivable" / "part-00000.parquet", index=False)
    print(f"Written fact_accounts_receivable ({len(rows):,} records)")

    # fact_cash_position - Daily cash with seasonality
    (facts / "fact_cash_position").mkdir(parents=True, exist_ok=True)
    rows = []
    
    print(f"Generating fact_cash_position for {len(sampled_dates)} dates...")
    
    for date_obj in sampled_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # Cash position varies with seasonality
        seasonality_factor = apply_combined_seasonality(
            date_obj,
            base_factor=1.0,
            monthly_weight=0.6,
            weekly_weight=0.4,
            seed=RANDOM_SEED,
        )
        
        for ok in org_keys[:10]:
            base_cash = 250000.0
            cash_balance = base_cash * seasonality_factor * random.uniform(0.90, 1.10)
            plan_cash = cash_balance * random.uniform(0.92, 0.98)
            
            rows.append({
                "DateKey": date_key, "OrgKey": ok,
                "Cash Balance Amount": round(cash_balance, 2), "Plan Cash Amount": round(plan_cash, 2),
            })
    
    pd.DataFrame(rows).to_parquet(facts / "fact_cash_position" / "part-00000.parquet", index=False)
    print(f"Written fact_cash_position ({len(rows):,} records)")

    # fact_cash_flow - Monthly cash flow with seasonality
    (facts / "fact_cash_flow").mkdir(parents=True, exist_ok=True)
    rows = []
    
    print(f"Generating fact_cash_flow for {len(month_end_dates)} months...")
    
    for date_obj in month_end_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        
        # Cash flow follows sales seasonality
        seasonality_factor = apply_monthly_seasonality(
            date_obj,
            base_factor=1.0,
            seed=RANDOM_SEED,
        )
        
        for ok in org_keys[:10]:
            base_ocf = 50000.0
            ocf_amount = base_ocf * seasonality_factor * random.uniform(0.85, 1.15)
            capex_amount = ocf_amount * random.uniform(0.15, 0.25)  # 15-25% of OCF
            plan_ocf = ocf_amount * random.uniform(0.92, 0.98)
            
            rows.append({
                "DateKey": date_key, "OrgKey": ok,
                "Operating Cash Flow Amount": round(ocf_amount, 2),
                "CapEx Amount": round(capex_amount, 2),
                "Plan OCF Amount": round(plan_ocf, 2),
            })
    
    pd.DataFrame(rows).to_parquet(facts / "fact_cash_flow" / "part-00000.parquet", index=False)
    print(f"Written fact_cash_flow ({len(rows):,} records)")


def main():
    parser = argparse.ArgumentParser(description="Generate Aurora gold data (all domains or selected).")
    parser.add_argument(
        "--domain",
        type=str,
        default="all",
        help="Comma-separated domains: commercial, operations, supply_chain, experience, finance; or 'all' (default).",
    )
    args = parser.parse_args()
    if args.domain.strip().lower() == "all":
        selected = DOMAINS
    else:
        selected = frozenset(d.strip().lower() for d in args.domain.split(",") if d.strip())
        invalid = selected - DOMAINS
        if invalid:
            parser.error(f"Unknown domain(s): {invalid}. Choose from {sorted(DOMAINS)}.")

    org_keys, date_keys, product_keys, customer_keys = _resolve_keys()

    if "operations" in selected:
        run_operations(org_keys, date_keys, product_keys)
    if "supply_chain" in selected:
        run_supply_chain(org_keys, date_keys, product_keys)
    if "experience" in selected or "commercial" in selected:
        run_experience_promo(org_keys, date_keys, customer_keys)
    if "finance" in selected or "experience" in selected:
        run_xd_finance(org_keys, date_keys, customer_keys)

    print("Done.")


if __name__ == "__main__":
    main()
