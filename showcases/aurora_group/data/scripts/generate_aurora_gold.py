"""
Generate all Aurora gold data from a single entry point.

Creates dimensions and facts for Commercial, Operations, Supply Chain, Experience, and Finance
in showcases/aurora_group/data/gold/ using final table names (e.g. dim_case_queue,
fact_support_cases, fact_accounts_payable, fact_cash_position, fact_cash_flow).

Uses shared utilities for realistic names, seasonality, and consistent time periods.

Run from repo root:
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain dims
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain operations
  py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain supply_chain,experience,finance

Domains: dims, commercial, operations, supply_chain, experience, finance (default: all).
  dims – enriches dim_org and dim_date with domain-specific columns (run first).
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import random
import subprocess
import sys

gold = (Path(__file__).resolve().parent.parent / "gold")
# Repo root (for running standalone scripts that expect cwd=repo root)
repo_root = gold.parent.parent.parent.parent
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
    write_fact_delta,
    FACTS_START,
    FACTS_END,
)

# Initialize
RANDOM_SEED = 12345
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
profile = get_company_profile("aurora")

DOMAINS = frozenset({"dims", "commercial", "operations", "supply_chain", "experience", "finance"})


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


def run_dims():
    """Enrich dim_org (domain columns) and dim_date (CalendarYearMonth, MonthNumber, Week)."""
    script = (gold / "generate_dims.py").resolve()
    if not script.exists():
        raise FileNotFoundError(f"Dims generator not found: {script}")
    print("Running generate_dims.py …", flush=True)
    subprocess.run([sys.executable, str(script)], cwd=str(repo_root.resolve()), check=True)


def run_finance(_org_keys, _date_keys, _product_keys):
    """Generate Finance facts: fact_finance, fact_cost, fact_labor, fact_output."""
    script = (gold / "generate_finance_gold.py").resolve()
    if not script.exists():
        raise FileNotFoundError(f"Finance generator not found: {script}")
    print("Running generate_finance_gold.py …", flush=True)
    subprocess.run([sys.executable, str(script)], cwd=str(repo_root.resolve()), check=True)


def run_operations(_org_keys, _date_keys, _product_keys):
    """Delegate to standalone script for consistent quality: realistic asset names, seasonality, variation (2020-2024 daily)."""
    script = (gold / "generate_operations_gold.py").resolve()
    if not script.exists():
        raise FileNotFoundError(f"Operations generator not found: {script}")
    print("Delegating operations to generate_operations_gold.py (daily data 2020-2024)...", flush=True)
    subprocess.run([sys.executable, str(script)], cwd=str(repo_root.resolve()), check=True)


def run_supply_chain(_org_keys, _date_keys, _product_keys):
    """Delegate to standalone script for consistent quality: seasonality, org-derived lanes, variation (2020-2024)."""
    script = (gold / "generate_supply_chain_gold.py").resolve()
    if not script.exists():
        raise FileNotFoundError(f"Supply chain generator not found: {script}")
    print("Delegating supply_chain to generate_supply_chain_gold.py (2020-2024)...", flush=True)
    subprocess.run([sys.executable, str(script)], cwd=str(repo_root.resolve()), check=True)


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
    
    df_experience = pd.DataFrame(rows_experience)
    fmt = write_fact_delta(facts / "fact_experience", df_experience, partition_by=["Fiscal Year"])
    print(f"Written fact_experience ({len(rows_experience):,} complaints) [{fmt}]")

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

    # fact_accounts_payable - Monthly AP with seasonality (Delta, partitioned by Fiscal Year)
    supplier_keys = [1, 2, 3, 4, 5, 6, 7, 8]
    rows = []
    month_end_dates = [d for d in fact_dates if d.is_month_end]
    print(f"Generating fact_accounts_payable for {len(month_end_dates)} months...")
    for date_obj in month_end_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        seasonality_factor = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)
        for ok in org_keys[:10]:
            for sk in supplier_keys:
                base_ap = 10000.0 + sk * 1000
                ap_amount = base_ap * seasonality_factor * random.uniform(0.85, 1.15)
                cogs_amount = ap_amount * random.uniform(0.75, 0.90)
                rows.append({
                    "DateKey": date_key, "OrgKey": ok, "SupplierKey": sk,
                    "AP Amount": round(ap_amount, 2), "COGS Amount": round(cogs_amount, 2),
                })
    df_ap = pd.DataFrame(rows)
    df_ap["Fiscal Year"] = df_ap["DateKey"].astype(str).str[:4]
    fmt = write_fact_delta(facts / "fact_accounts_payable", df_ap, partition_by=["Fiscal Year"])
    print(f"Written fact_accounts_payable ({len(rows):,} records) [{fmt}]")

    # fact_accounts_receivable - Monthly AR with seasonality (Delta, partitioned by Fiscal Year)
    rows = []
    print(f"Generating fact_accounts_receivable for {len(month_end_dates)} months...")
    for date_obj in month_end_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        seasonality_factor = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)
        for ok in org_keys[:10]:
            for ck in customer_keys[:20]:
                base_ar = 5000.0 + ck * 200
                ar_amount = base_ar * seasonality_factor * random.uniform(0.85, 1.15)
                revenue_amount = ar_amount * random.uniform(1.1, 1.3)
                rows.append({
                    "DateKey": date_key, "OrgKey": ok, "CustomerKey": ck,
                    "AR Amount": round(ar_amount, 2), "Revenue Amount": round(revenue_amount, 2),
                })
    df_ar = pd.DataFrame(rows)
    df_ar["Fiscal Year"] = df_ar["DateKey"].astype(str).str[:4]
    fmt = write_fact_delta(facts / "fact_accounts_receivable", df_ar, partition_by=["Fiscal Year"])
    print(f"Written fact_accounts_receivable ({len(rows):,} records) [{fmt}]")

    # fact_cash_position - Daily cash with seasonality (Delta, partitioned by Fiscal Year)
    rows = []
    print(f"Generating fact_cash_position for {len(sampled_dates)} dates...")
    for date_obj in sampled_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        seasonality_factor = apply_combined_seasonality(
            date_obj, base_factor=1.0, monthly_weight=0.6, weekly_weight=0.4, seed=RANDOM_SEED
        )
        for ok in org_keys[:10]:
            base_cash = 250000.0
            cash_balance = base_cash * seasonality_factor * random.uniform(0.90, 1.10)
            plan_cash = cash_balance * random.uniform(0.92, 0.98)
            rows.append({
                "DateKey": date_key, "OrgKey": ok,
                "Cash Balance Amount": round(cash_balance, 2), "Plan Cash Amount": round(plan_cash, 2),
            })
    df_cp = pd.DataFrame(rows)
    df_cp["Fiscal Year"] = df_cp["DateKey"].astype(str).str[:4]
    fmt = write_fact_delta(facts / "fact_cash_position", df_cp, partition_by=["Fiscal Year"])
    print(f"Written fact_cash_position ({len(rows):,} records) [{fmt}]")

    # fact_cash_flow - Monthly cash flow (Delta, partitioned by Fiscal Year)
    cash_flow_orgs = org_keys[:40] if len(org_keys) > 10 else org_keys
    rows = []
    print(f"Generating fact_cash_flow for {len(month_end_dates)} months × {len(cash_flow_orgs)} orgs...")
    for date_obj in month_end_dates:
        date_key = int(date_obj.strftime('%Y%m%d'))
        seasonality_factor = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)
        for ok in cash_flow_orgs:
            base_ocf = 30000.0 + (ok % 10) * 8000.0
            ocf_amount = base_ocf * seasonality_factor * random.uniform(0.80, 1.20)
            capex_amount = ocf_amount * random.uniform(0.12, 0.28)
            plan_ocf = ocf_amount * random.uniform(0.90, 1.00)
            rows.append({
                "DateKey": date_key, "OrgKey": ok,
                "Operating Cash Flow Amount": round(ocf_amount, 2),
                "CapEx Amount": round(capex_amount, 2),
                "Plan OCF Amount": round(plan_ocf, 2),
            })
    df_cf = pd.DataFrame(rows)
    df_cf["Fiscal Year"] = df_cf["DateKey"].astype(str).str[:4]
    fmt = write_fact_delta(facts / "fact_cash_flow", df_cf, partition_by=["Fiscal Year"])
    print(f"Written fact_cash_flow ({len(rows):,} records) [{fmt}]")


def run_commercial_derived_facts():
    """
    Derive Commercial semantic model facts from existing gold tables.
    fact_plan_sales from fact_sales_budget; fact_customer_events from fact_customer_interactions;
    fact_customer_value from fact_sales. Runs when --domain commercial (or all) so these tables
    are created in the same pipeline as other synthetic data.
    """
    def _parquet_files(path):
        return sorted(path.rglob("*.parquet"))

    def _month_end_datekey(series):
        dt = pd.to_datetime(series.astype(str), format="%Y%m%d")
        return (dt.dt.to_period("M").dt.to_timestamp("M").dt.strftime("%Y%m%d")).astype(int)

    # fact_plan_sales from fact_sales_budget
    budget_path = facts / "fact_sales_budget"
    if budget_path.is_dir():
        files = _parquet_files(budget_path)
        if files:
            df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
            out = df[["MonthEnd DateKey", "OrgKey", "ProductKey", "Budget Sales Amount", "Budget COGS Amount"]].copy()
            out = out.rename(columns={
                "MonthEnd DateKey": "DateKey",
                "Budget Sales Amount": "Plan Net Sales Amount",
                "Budget COGS Amount": "Plan Cost of Goods Sold Amount",
            })
            out["Plan Gross Margin Amount"] = out["Plan Net Sales Amount"] - out["Plan Cost of Goods Sold Amount"]
            (facts / "fact_plan_sales").mkdir(parents=True, exist_ok=True)
            out.to_parquet(facts / "fact_plan_sales" / "plan.parquet", index=False)
            print(f"Written fact_plan_sales ({len(out):,} rows) from fact_sales_budget")

    # fact_customer_events from fact_customer_interactions
    interactions_path = facts / "fact_customer_interactions"
    if interactions_path.is_dir():
        files = _parquet_files(interactions_path)
        if files:
            df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
            df["DateKey"] = _month_end_datekey(df["DateKey"])
            agg = (
                df.groupby(["DateKey", "CustomerKey"], as_index=False)
                .agg(OrgKey=("OrgKey", "first"))
                .assign(**{"Activity Flag": True, "Churn Flag": False, "Attrition Risk %": 0.1})
            )
            (facts / "fact_customer_events").mkdir(parents=True, exist_ok=True)
            agg.to_parquet(facts / "fact_customer_events" / "events.parquet", index=False)
            print(f"Written fact_customer_events ({len(agg):,} rows) from fact_customer_interactions")

    # fact_customer_value from fact_sales
    sales_path = facts / "fact_sales"
    if sales_path.is_dir():
        files = _parquet_files(sales_path)
        if files:
            dfs = [pd.read_parquet(f) for f in files[:12]]
            df = pd.concat(dfs, ignore_index=True)
            df["DateKey"] = _month_end_datekey(df["DateKey"])
            df["Margin"] = df["Net Sales Amount"] - df["Cost of Goods Sold Amount"]
            margin = df.groupby(["DateKey", "CustomerKey"], as_index=False)["Margin"].sum()
            margin["CLV Amount"] = (margin["Margin"] * 3).round(2)
            margin["CLV Remaining Amount"] = (margin["CLV Amount"] * 0.6).round(2)
            agg = margin[["DateKey", "CustomerKey", "CLV Amount", "CLV Remaining Amount"]]
            (facts / "fact_customer_value").mkdir(parents=True, exist_ok=True)
            agg.to_parquet(facts / "fact_customer_value" / "value.parquet", index=False)
            print(f"Written fact_customer_value ({len(agg):,} rows) from fact_sales")


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

    # dims must run before any domain so domain facts reference correct keys
    if "dims" in selected or selected == DOMAINS:
        run_dims()
    if "operations" in selected:
        run_operations(org_keys, date_keys, product_keys)
    if "supply_chain" in selected:
        run_supply_chain(org_keys, date_keys, product_keys)
    if "experience" in selected or "commercial" in selected:
        run_experience_promo(org_keys, date_keys, customer_keys)
    if "finance" in selected or "experience" in selected:
        run_xd_finance(org_keys, date_keys, customer_keys)
    if "finance" in selected or selected == DOMAINS:
        run_finance(org_keys, date_keys, product_keys)
    if "commercial" in selected:
        run_commercial_derived_facts()

    print("Done.")


if __name__ == "__main__":
    main()
