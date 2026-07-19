"""
Generate gap-fill gold data for HR-001, COM-005, FIN-003, SCM-004 (+ COM-001 bridge)
====================================================================================

These four use cases were spec-complete (KPIs, standards, storyline, action codes all
green) but their KPIs were `hitl`/`planned` because the backing Aurora synthetic data
did not exist. This script produces exactly the tables/columns recorded in
`internal/project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md` — *realistic but synthetic*, and
consistent with the existing Aurora gold (same OrgKeys, DateKey convention, growth
model, seeded RandomState).

What it writes (see the gaps doc for the full rationale):
  dims  : dim_pvm_driver, dim_employee_segment, dim_role, dim_sales_stage,
          dim_salesrep, dim_cost_center, dim_category, dim_supplier
  facts : fact_workforce, fact_engagement_survey, fact_recruiting            (HR-001)
          fact_pipeline, fact_sales_target                                    (COM-005)
          fact_finance   (+ D&A, plan side, CostCenterKey — existing cols kept) (FIN-003)
          fact_procurement (+ target/contract/price/CategoryKey — existing kept),
          fact_procurement_receipts                                           (SCM-004)

Design decisions that keep it honest & consistent:
  • fact_finance / fact_procurement are EXTENDED by reading the existing parquet and
    adding columns deterministically — existing columns stay byte-identical.
  • Storyline realism is baked into the numbers, not the titles:
      HR-001  voluntary attrition ~13 % p.a., 2-3 hotspot segments elevated, engagement
              inversely correlated; absence ~2-5 %; time-to-fill 30-70 d.
      COM-005 coverage 2.0-3.5x, win rate 20-35 %, weak mid-stage, cycle 45-120 d.
      FIN-003 EBITDA margin ~1-3 pp below plan, opex-led (gross margin holds).
      SCM-004 realised savings 40-80 % of target, on-contract 70-85 % with a few
              leaking categories, PPV climbing there, supplier OTD 88-96 %.

Run from repo root:
  python3 showcases/aurora_group/data/gold/generate_gapfill_gold.py
"""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

GOLD = Path(__file__).resolve().parent
if str(GOLD) not in sys.path:
    sys.path.insert(0, str(GOLD))

from _generator_utils import FACTS_END, FACTS_START, apply_monthly_seasonality, write_fact_delta

DIMS = GOLD / "dimensions"
FACTS = GOLD / "facts"

RANDOM_SEED = 12345
_GROWTH = {2020: 1.00, 2021: 1.04, 2022: 1.08, 2023: 1.14, 2024: 1.20}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load_dim(name: str) -> pd.DataFrame:
    files = sorted((DIMS / name).rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"{DIMS / name} has no parquet files")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _load_fact(name: str) -> pd.DataFrame:
    files = sorted((FACTS / name).rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"{FACTS / name} has no parquet files")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _rng(*ints: int) -> np.random.RandomState:
    seed = RANDOM_SEED
    for i in ints:
        seed = (seed * 31 + int(i)) % (2**31 - 1)
    return np.random.RandomState(seed)


def _month_ends() -> list[pd.Timestamp]:
    return [d for d in pd.date_range(FACTS_START, FACTS_END, freq="D") if d.is_month_end]


def _quarter_ends() -> list[pd.Timestamp]:
    return [d for d in _month_ends() if d.month in (3, 6, 9, 12)]


def _write_dim(name: str, df: pd.DataFrame) -> None:
    d = DIMS / name
    d.mkdir(parents=True, exist_ok=True)
    df.to_parquet(d / "part-00000.parquet", index=False)
    print(f"  dim {name:24s} {len(df):>6,} rows")


# ===========================================================================
# 1. COM-001 bridge — dim_pvm_driver
# ===========================================================================

def build_dim_pvm_driver() -> None:
    rows = [
        {"PVMDriverKey": 1, "Driver": "Price",  "Sort Order": 1, "Sign Convention": "As-is"},
        {"PVMDriverKey": 2, "Driver": "Volume", "Sort Order": 2, "Sign Convention": "As-is"},
        {"PVMDriverKey": 3, "Driver": "Mix",    "Sort Order": 3, "Sign Convention": "As-is"},
    ]
    _write_dim("dim_pvm_driver", pd.DataFrame(rows))


# ===========================================================================
# 2. HR-001 dims + facts
# ===========================================================================

_HR_FUNCTIONS = ["Retail Frontline", "Logistics", "Sales", "Corporate Functions", "IT & Digital"]
_TENURE_BANDS = ["<1y", "1-3y", "3-5y", "5y+"]
# (Function, Tenure Band) hotspots — elevated attrition, depressed engagement.
_HR_HOTSPOTS = {("Retail Frontline", "<1y"), ("Logistics", "<1y"), ("Sales", "1-3y")}


def build_dim_employee_segment() -> pd.DataFrame:
    rows, key = [], 1
    for func in _HR_FUNCTIONS:
        for band in _TENURE_BANDS:
            rows.append({
                "EmployeeSegmentKey": key,
                "Segment": f"{func} · {band}",
                "Function": func,
                "Tenure Band": band,
            })
            key += 1
    df = pd.DataFrame(rows)
    _write_dim("dim_employee_segment", df)
    return df


_ROLES = [
    ("Store Associate", "Retail", "Entry"), ("Store Manager", "Retail", "Manager"),
    ("Warehouse Operative", "Logistics", "Entry"), ("Logistics Coordinator", "Logistics", "Professional"),
    ("Sales Representative", "Sales", "Professional"), ("Key Account Manager", "Sales", "Senior"),
    ("Data Analyst", "IT & Digital", "Professional"), ("Software Engineer", "IT & Digital", "Professional"),
    ("HR Business Partner", "Corporate", "Professional"), ("Finance Analyst", "Corporate", "Professional"),
    ("Category Manager", "Commercial", "Senior"), ("Marketing Specialist", "Commercial", "Professional"),
]


def build_dim_role() -> pd.DataFrame:
    rows = [{"RoleKey": i + 1, "Role": r, "Job Family": jf, "Level": lvl}
            for i, (r, jf, lvl) in enumerate(_ROLES)]
    df = pd.DataFrame(rows)
    _write_dim("dim_role", df)
    return df


def _hr_org_keys(org_df: pd.DataFrame) -> list[int]:
    # HR reports at entity level: Country + Region + Group (rolls up store staff).
    return org_df[org_df["OrgType"].isin(["Country", "Region", "Group"])]["OrgKey"].astype(int).tolist()


# base monthly FTE per (org_type) before country weighting
_HR_BASE_FTE = {"Country": 900, "Region": 220, "Group": 380}


def build_fact_workforce(org_df: pd.DataFrame, seg_df: pd.DataFrame) -> None:
    print("Generating fact_workforce …")
    orgs = org_df[org_df["OrgType"].isin(["Country", "Region", "Group"])]
    seg_records = seg_df.to_dict("records")
    rows: list[dict] = []

    for _, org in orgs.iterrows():
        ok, otype = int(org["OrgKey"]), org["OrgType"]
        # country-size weight (deterministic): DACH entities carry more headcount
        wt = float(_rng(ok, 1).uniform(0.6, 1.5))
        if str(org.get("Country")) in ("Germany", "France", "United Kingdom"):
            wt *= 1.6
        org_base = _HR_BASE_FTE.get(otype, 300) * wt

        # split the org's headcount across segments (Pareto-ish, frontline largest)
        seg_weights = []
        for seg in seg_records:
            base = 3.0 if seg["Function"] == "Retail Frontline" else 1.0
            base *= {"<1y": 0.8, "1-3y": 1.2, "3-5y": 1.0, "5y+": 1.1}[seg["Tenure Band"]]
            seg_weights.append(base * float(_rng(ok, seg["EmployeeSegmentKey"], 2).uniform(0.8, 1.2)))
        seg_weights = np.array(seg_weights) / sum(seg_weights)

        for seg, sw in zip(seg_records, seg_weights):
            sk = seg["EmployeeSegmentKey"]
            hotspot = (seg["Function"], seg["Tenure Band"]) in _HR_HOTSPOTS
            # annual voluntary attrition: base ~11-13 %, hotspots 20-26 %
            ann_attr = float(_rng(ok, sk, 3).uniform(0.20, 0.26) if hotspot
                             else _rng(ok, sk, 3).uniform(0.09, 0.14))
            absence_rate = float(_rng(ok, sk, 4).uniform(0.02, 0.05))

            for date_obj in _month_ends():
                dk, year = int(date_obj.strftime("%Y%m%d")), date_obj.year
                growth = 1.0 + (_GROWTH.get(year, 1.0) - 1.0) * 0.5  # HC grows slower than revenue
                r = _rng(ok, sk, dk % 997)
                fte = max(1.0, org_base * float(sw) * growth * float(r.uniform(0.96, 1.04)))
                vol_leavers = fte * (ann_attr / 12.0) * float(r.uniform(0.7, 1.3))
                invol_leavers = fte * (0.02 / 12.0) * float(r.uniform(0.5, 1.5))
                hires = fte * (ann_attr / 12.0) * float(r.uniform(0.9, 1.4))  # backfill + slight growth
                sched_days = fte * 21.0  # ~21 working days / month
                absence_days = sched_days * absence_rate * float(r.uniform(0.85, 1.15))
                cost = fte * 4_050.0 * float(r.uniform(0.95, 1.06))  # fully-loaded monthly EUR/FTE

                rows.append({
                    "DateKey": dk, "OrgKey": ok, "EmployeeSegmentKey": int(sk),
                    "Headcount FTE": round(fte, 2),
                    "Voluntary Leavers": round(vol_leavers, 3),
                    "Involuntary Leavers": round(invol_leavers, 3),
                    "Hires": round(hires, 3),
                    "Absence Days": round(absence_days, 2),
                    "Scheduled Working Days": round(sched_days, 2),
                    "Workforce Cost Amount": round(cost, 2),
                })
    fmt = write_fact_delta(FACTS / "fact_workforce", pd.DataFrame(rows), partition_by=["Fiscal Year"])
    print(f"  Written fact_workforce ({len(rows):,} rows) [{fmt}]")


def build_fact_engagement_survey(org_df: pd.DataFrame, seg_df: pd.DataFrame) -> None:
    print("Generating fact_engagement_survey …")
    orgs = org_df[org_df["OrgType"].isin(["Country", "Region", "Group"])]
    seg_records = seg_df.to_dict("records")
    rows: list[dict] = []
    for _, org in orgs.iterrows():
        ok = int(org["OrgKey"])
        for seg in seg_records:
            sk = seg["EmployeeSegmentKey"]
            hotspot = (seg["Function"], seg["Tenure Band"]) in _HR_HOTSPOTS
            base_eng = float(_rng(ok, sk, 5).uniform(55, 63) if hotspot
                             else _rng(ok, sk, 5).uniform(72, 82))
            for date_obj in _quarter_ends():
                dk = int(date_obj.strftime("%Y%m%d"))
                r = _rng(ok, sk, dk % 991)
                score = float(np.clip(base_eng + r.uniform(-4, 4), 0, 100))
                invited = int(max(8, r.randint(20, 120)))
                respondents = int(invited * float(r.uniform(0.62, 0.82)))
                rows.append({
                    "DateKey": dk, "OrgKey": ok, "EmployeeSegmentKey": int(sk),
                    "Engagement Score": round(score, 1),
                    "Respondents": respondents, "Invited": invited,
                })
    fmt = write_fact_delta(FACTS / "fact_engagement_survey", pd.DataFrame(rows), partition_by=["Fiscal Year"])
    print(f"  Written fact_engagement_survey ({len(rows):,} rows) [{fmt}]")


def build_fact_recruiting(org_df: pd.DataFrame, role_df: pd.DataFrame) -> None:
    print("Generating fact_recruiting …")
    orgs = org_df[org_df["OrgType"].isin(["Country", "Region", "Group"])]
    role_keys = role_df["RoleKey"].astype(int).tolist()
    rows: list[dict] = []
    for _, org in orgs.iterrows():
        ok = int(org["OrgKey"])
        for date_obj in _month_ends():
            dk, year = int(date_obj.strftime("%Y%m%d")), date_obj.year
            r = _rng(ok, dk % 983)
            n_reqs = int(r.poisson(2.0 * _GROWTH.get(year, 1.0)))  # ~2 fills/month/entity
            for _ in range(n_reqs):
                rk = int(r.choice(role_keys))
                # time-to-fill 30-70 d; senior roles slower
                base_ttf = 55 if rk in (6, 11) else 42
                ttf = int(np.clip(r.normal(base_ttf, 12), 25, 95))
                filled = date_obj
                opened = filled - timedelta(days=ttf)
                rows.append({
                    "DateKey": dk, "OrgKey": ok, "RoleKey": rk,
                    "Requisition Open Date": int(opened.strftime("%Y%m%d")),
                    "Filled Date": int(filled.strftime("%Y%m%d")),
                    "Positions Filled": 1,
                    "Days to Fill": ttf,
                })
    fmt = write_fact_delta(FACTS / "fact_recruiting", pd.DataFrame(rows), partition_by=["Fiscal Year"])
    print(f"  Written fact_recruiting ({len(rows):,} rows) [{fmt}]")


# ===========================================================================
# 3. COM-005 dims + facts
# ===========================================================================

_STAGES = [
    (1, "Lead", 1, False, False), (2, "Qualified", 2, False, False),
    (3, "Proposal", 3, False, False), (4, "Negotiation", 4, False, False),
    (5, "Closed Won", 5, True, False), (6, "Closed Lost", 6, False, True),
]
# stage-to-stage advance probability (weak mid-stage: Proposal→Negotiation)
_ADVANCE_P = {1: 0.72, 2: 0.64, 3: 0.48, 4: 0.55}


def build_dim_sales_stage() -> pd.DataFrame:
    rows = [{"StageKey": k, "Stage": s, "Stage Order": o, "Is Won": w, "Is Lost": l}
            for (k, s, o, w, l) in _STAGES]
    df = pd.DataFrame(rows)
    _write_dim("dim_sales_stage", df)
    return df


def build_dim_salesrep(org_df: pd.DataFrame) -> pd.DataFrame:
    regions = sorted(org_df["Region"].dropna().unique().tolist())
    rows = []
    for i in range(1, 41):
        region = regions[i % len(regions)]
        rows.append({
            "SalesRepKey": i, "Rep": f"Rep {i:02d}",
            "Team": f"{region} Sales", "Region": region,
        })
    df = pd.DataFrame(rows)
    _write_dim("dim_salesrep", df)
    return df


def build_fact_pipeline(org_df: pd.DataFrame, rep_df: pd.DataFrame) -> None:
    print("Generating fact_pipeline …")
    country_orgs = org_df[org_df["OrgType"] == "Country"]["OrgKey"].astype(int).tolist()
    rep_region = dict(zip(rep_df["SalesRepKey"], rep_df["Region"]))
    org_region = dict(zip(org_df["OrgKey"].astype(int), org_df["Region"]))
    reps_by_region: dict[str, list[int]] = {}
    for rk, rg in rep_region.items():
        reps_by_region.setdefault(rg, []).append(int(rk))

    rows: list[dict] = []
    opp_id = 1
    today = FACTS_END  # snapshot "now" for open-pipeline state
    for ok in country_orgs:
        region = org_region.get(ok)
        reps = reps_by_region.get(region) or list(rep_region.keys())
        for date_obj in _month_ends():
            dk, year = int(date_obj.strftime("%Y%m%d")), date_obj.year
            r = _rng(ok, dk % 977)
            n_opps = int(r.poisson(6.0 * _GROWTH.get(year, 1.0)))
            for _ in range(n_opps):
                rk = int(r.choice(reps))
                create = date_obj
                value = float(np.round(np.exp(r.normal(11.0, 0.8)), 2))  # ~€20k-500k lognormal

                # walk the funnel
                stage = 1
                while stage in _ADVANCE_P and r.random() < _ADVANCE_P[stage]:
                    stage += 1
                if stage >= 4:  # reached Negotiation → decide win/loss (win rate ~28 %)
                    won = r.random() < 0.28
                    reached = 5 if won else 6
                else:
                    reached = stage  # still open in an early stage
                qualified = reached >= 2

                is_closed = reached in (5, 6)
                won_flag = reached == 5
                lost_flag = reached == 6
                if is_closed:
                    cycle_days = int(np.clip(r.normal(85 if not won_flag else 70, 22), 20, 160))
                    close = create + timedelta(days=cycle_days)
                    open_qualified_value = 0.0
                else:
                    cycle_days = None
                    close = None
                    # open & still within window → counts toward coverage if qualified
                    open_qualified_value = value if qualified else 0.0

                rows.append({
                    "OpportunityID": opp_id, "DateKey": dk, "OrgKey": int(ok), "SalesRepKey": rk,
                    "StageKey": int(reached),
                    "Create Date": int(create.strftime("%Y%m%d")),
                    "Close Date": int(close.strftime("%Y%m%d")) if close is not None else 0,
                    "Opportunity Value Amount": value,
                    "Open Qualified Value Amount": round(open_qualified_value, 2),
                    "Won Flag": bool(won_flag), "Lost Flag": bool(lost_flag),
                    "Qualified Flag": bool(qualified),
                    "Won Count": 1 if won_flag else 0,
                    "Decided Count": 1 if is_closed else 0,
                    "Cycle Days": cycle_days if cycle_days is not None else np.nan,
                })
                opp_id += 1
    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_pipeline", df, partition_by=["Fiscal Year"])
    print(f"  Written fact_pipeline ({len(rows):,} rows) [{fmt}]")
    # coverage anchor: open qualified pipeline per country, for target sizing
    open_by_org = df[df["Open Qualified Value Amount"] > 0].groupby("OrgKey")["Open Qualified Value Amount"].sum()
    return open_by_org


def build_fact_sales_target(org_df: pd.DataFrame, open_by_org: pd.Series) -> None:
    print("Generating fact_sales_target …")
    country_orgs = org_df[org_df["OrgType"] == "Country"]["OrgKey"].astype(int).tolist()
    months = _month_ends()
    rows: list[dict] = []
    for ok in country_orgs:
        total_open = float(open_by_org.get(ok, 0.0)) or 1.0
        # Size the remaining target so the model-level coverage ratio
        # (SUM open qualified pipeline / SUM remaining target) lands ~2.0-3.5x for
        # this org — below the 3x rule in the segments the storyline flags. Split
        # the org's total remaining target across the months with per-month noise
        # so the ratio also varies month to month.
        org_coverage = float(_rng(ok, 8).uniform(2.0, 3.5))
        total_target = total_open / org_coverage
        base_month = total_target / len(months)
        for date_obj in months:
            dk = int(date_obj.strftime("%Y%m%d"))
            noise = float(_rng(ok, dk % 967, 9).uniform(0.85, 1.15))
            rows.append({
                "DateKey": dk, "OrgKey": int(ok),
                "Remaining Target Amount": round(base_month * noise, 2),
            })
    fmt = write_fact_delta(FACTS / "fact_sales_target", pd.DataFrame(rows), partition_by=["Fiscal Year"])
    print(f"  Written fact_sales_target ({len(rows):,} rows) [{fmt}]")


# ===========================================================================
# 4. FIN-003 — dim_cost_center + extend fact_finance
# ===========================================================================

def build_dim_cost_center(org_df: pd.DataFrame) -> pd.DataFrame:
    regions = sorted(org_df["Region"].dropna().unique().tolist())
    rows, key = [], 1
    cc_map: dict[str, int] = {}
    for rg in regions:
        rows.append({"CostCenterKey": key, "Cost Center": f"Retail Ops {rg}", "Entity": rg,
                     "Business Unit": "Retail", "Account Group": "Operations"})
        cc_map[f"Retail Ops {rg}"] = key
        key += 1
    for name, bu, ag in [("Logistics & Distribution", "Supply Chain", "Operations"),
                         ("Country Management", "Corporate", "SG&A"),
                         ("Regional Overhead", "Corporate", "SG&A"),
                         ("Group G&A", "Corporate", "SG&A")]:
        rows.append({"CostCenterKey": key, "Cost Center": name, "Entity": name,
                     "Business Unit": bu, "Account Group": ag})
        cc_map[name] = key
        key += 1
    df = pd.DataFrame(rows)
    _write_dim("dim_cost_center", df)
    return df, cc_map


def _cost_center_for(org_row, cc_map: dict[str, int]) -> int:
    otype, region = org_row["OrgType"], org_row.get("Region")
    if otype == "Store":
        return cc_map.get(f"Retail Ops {region}", cc_map["Group G&A"])
    return {"DC": cc_map["Logistics & Distribution"],
            "Country": cc_map["Country Management"],
            "Region": cc_map["Regional Overhead"],
            "Group": cc_map["Group G&A"]}.get(otype, cc_map["Group G&A"])


def extend_fact_finance(org_df: pd.DataFrame, cc_map: dict[str, int]) -> None:
    print("Extending fact_finance (D&A, plan side, CostCenterKey) …")
    fin = _load_fact("fact_finance")
    org_by_key = org_df.set_index(org_df["OrgKey"].astype(int)).to_dict("index")

    # CostCenterKey per row: map each OrgKey → its cost centre (grain unchanged).
    cck = [_cost_center_for(org_by_key.get(int(ok), {"OrgType": "Group", "Region": None}), cc_map)
           for ok in fin["OrgKey"].to_numpy()]

    # everything else is vectorised over the DataFrame (column names have spaces).
    r_seed = np.random.RandomState(RANDOM_SEED)
    ns = fin["Net Sales Amount"].to_numpy(dtype=float)
    cogs = fin["COGS Amount"].to_numpy(dtype=float)
    opex = fin["OpEx Amount"].to_numpy(dtype=float)
    plan_opex = fin["Plan OpEx Amount"].to_numpy(dtype=float)
    ebit = fin["EBIT Amount"].to_numpy(dtype=float)

    n = len(fin)
    dna_ratio = r_seed.uniform(0.025, 0.040, n)                # D&A 2.5-4.0 % of net sales
    dna_arr = ns * dna_ratio
    ebitda_arr = ebit + dna_arr                                # EBITDA = EBIT + D&A
    plan_ns_arr = ns * r_seed.uniform(0.98, 1.03, n)           # roughly on-plan revenue
    # plan COGS keeps plan gross-margin ≈ actual GM (margin holds) → gap is opex-led
    gm_ratio = np.divide(cogs, ns, out=np.full(n, 0.61), where=ns > 0)
    plan_cogs_arr = plan_ns_arr * gm_ratio * r_seed.uniform(0.99, 1.01, n)
    plan_dna_arr = plan_ns_arr * dna_ratio                     # plan D&A tracks plan revenue
    plan_ebit_arr = plan_ns_arr - plan_cogs_arr - plan_opex    # actual opex > plan opex ⇒ actual EBIT below plan
    plan_ebitda_arr = plan_ebit_arr + plan_dna_arr

    out = fin.copy()
    out["D&A Amount"] = np.round(dna_arr, 2)
    out["EBITDA Amount"] = np.round(ebitda_arr, 2)
    out["Plan Net Sales Amount"] = np.round(plan_ns_arr, 2)
    out["Plan COGS Amount"] = np.round(plan_cogs_arr, 2)
    out["Plan EBITDA Amount"] = np.round(plan_ebitda_arr, 2)
    out["CostCenterKey"] = np.array(cck, dtype=int)

    fmt = write_fact_delta(FACTS / "fact_finance", out, partition_by=["Fiscal Year"])
    margin_act = float(np.sum(ebitda_arr) / np.sum(ns) * 100)
    margin_plan = float(np.sum(plan_ebitda_arr) / np.sum(plan_ns_arr) * 100)
    print(f"  Written fact_finance ({n:,} rows, +6 cols) [{fmt}] "
          f"| EBITDA margin actual {margin_act:.1f}% vs plan {margin_plan:.1f}% "
          f"({margin_act - margin_plan:+.1f} pp)")


# ===========================================================================
# 5. SCM-004 — dim_category, dim_supplier, extend fact_procurement, receipts
# ===========================================================================

_CATEGORIES = [
    (1, "Merchandise – Fashion", "Direct"), (2, "Merchandise – Home & Living", "Direct"),
    (3, "Merchandise – Electronics", "Direct"), (4, "Logistics & Freight", "Indirect"),
    (5, "Facilities & Energy", "Indirect"), (6, "Marketing Services", "Indirect"),
    (7, "IT & Software", "Indirect"), (8, "Professional Services", "Indirect"),
]
# leaking categories: low on-contract, PPV climbing over time (governed cross-signal)
_LEAKING_CATEGORIES = {5, 6, 7}


def build_dim_category() -> pd.DataFrame:
    df = pd.DataFrame([{"CategoryKey": k, "Category": c, "Category Group": g}
                       for (k, c, g) in _CATEGORIES])
    _write_dim("dim_category", df)
    return df


def build_dim_supplier(proc: pd.DataFrame, org_df: pd.DataFrame) -> dict[int, int]:
    regions = sorted(org_df["Region"].dropna().unique().tolist())
    vendor_keys = sorted(proc["VendorKey"].dropna().astype(int).unique().tolist())
    rows, vendor_cat = [], {}
    for vk in vendor_keys:
        r = _rng(vk, 21)
        cat = int(r.choice([c[0] for c in _CATEGORIES]))
        vendor_cat[vk] = cat
        tier = str(r.choice(["A", "B", "C"], p=[0.3, 0.45, 0.25]))
        rows.append({"VendorKey": vk, "Supplier": f"Supplier {vk:02d}",
                     "Region": regions[vk % len(regions)], "Tier": tier})
    _write_dim("dim_supplier", pd.DataFrame(rows))
    return vendor_cat


def extend_fact_procurement(proc: pd.DataFrame, vendor_cat: dict[int, int]) -> None:
    print("Extending fact_procurement (target/contract/price/CategoryKey) …")
    n = len(proc)
    cat = proc["VendorKey"].astype(int).map(vendor_cat).to_numpy()
    year = (proc["DateKey"].astype(int) // 10000).to_numpy()
    spend = proc["Procurement Amount"].to_numpy(dtype=float)
    savings = proc["Savings Amount"].to_numpy(dtype=float)

    r = np.random.RandomState(RANDOM_SEED + 7)
    # realised savings = 40-80 % of target ⇒ target = savings / realisation_rate
    realisation = r.uniform(0.40, 0.80, n)
    savings_target = np.divide(savings, realisation, out=savings * 1.6, where=realisation > 0)

    is_leaking = np.isin(cat, list(_LEAKING_CATEGORIES))
    on_contract_pct = np.where(is_leaking, r.uniform(0.55, 0.66, n), r.uniform(0.72, 0.85, n))
    on_contract = spend * on_contract_pct
    addressable = spend * r.uniform(0.86, 0.96, n)

    # PPV: baseline vs actual unit price. Leaking categories climb over the years.
    yr_idx = (year - 2020).astype(float)
    ppv_base = np.where(is_leaking, 0.010 + 0.012 * yr_idx, r.uniform(-0.015, 0.015, n))
    ppv = ppv_base + r.uniform(-0.006, 0.006, n)
    baseline_price = r.uniform(40.0, 160.0, n)
    actual_price = baseline_price * (1.0 + ppv)
    quantity = np.round(np.divide(spend, actual_price, out=np.ones(n), where=actual_price > 0))

    out = proc.copy()
    out["CategoryKey"] = cat.astype(int)
    out["Savings Target Amount"] = np.round(savings_target, 2)
    out["On-Contract Amount"] = np.round(on_contract, 2)
    out["Addressable Amount"] = np.round(addressable, 2)
    out["Baseline Price Amount"] = np.round(baseline_price, 4)
    out["Actual Price Amount"] = np.round(actual_price, 4)
    out["Quantity"] = quantity
    fmt = write_fact_delta(FACTS / "fact_procurement", out, partition_by=["Fiscal Year"])
    real = float(np.sum(savings) / np.sum(savings_target) * 100)
    onc = float(np.sum(on_contract) / np.sum(addressable) * 100)
    print(f"  Written fact_procurement ({n:,} rows, +7 cols) [{fmt}] "
          f"| realised savings {real:.0f}% of target · on-contract {onc:.0f}%")


def build_fact_procurement_receipts(proc: pd.DataFrame, vendor_cat: dict[int, int]) -> None:
    print("Generating fact_procurement_receipts …")
    # one receipt row per (DateKey, VendorKey) spend line, OTD ~88-96 %, leaking cats worse
    rows: list[dict] = []
    for row in proc.itertuples(index=False):
        vk = int(getattr(row, "VendorKey"))
        dk = int(getattr(row, "DateKey"))
        cat = vendor_cat.get(vk, 1)
        r = _rng(vk, dk % 953, 31)
        n_receipts = max(1, int(r.randint(2, 6)))
        otd_base = 0.90 if cat in _LEAKING_CATEGORIES else 0.94
        for _ in range(n_receipts):
            promise = pd.Timestamp(str(dk))
            on_time = r.random() < float(np.clip(otd_base + r.uniform(-0.03, 0.03), 0.80, 0.99))
            delay = 0 if on_time else int(r.randint(1, 8))
            receipt = promise + timedelta(days=delay)
            rows.append({
                "DateKey": dk, "VendorKey": vk, "CategoryKey": int(cat),
                "Promise Date": int(promise.strftime("%Y%m%d")),
                "Receipt Date": int(receipt.strftime("%Y%m%d")),
                "On-Time Flag": bool(on_time),
            })
    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_procurement_receipts", df, partition_by=["Fiscal Year"])
    otd = float(df["On-Time Flag"].mean() * 100)
    print(f"  Written fact_procurement_receipts ({len(rows):,} rows) [{fmt}] | supplier OTD {otd:.0f}%")


# ===========================================================================
# entry point
# ===========================================================================

def main() -> None:
    print("=== Gap-fill Gold Data Generation (HR-001 · COM-005 · FIN-003 · SCM-004) ===")
    org_df = _load_dim("dim_org")
    print(f"  Loaded {len(org_df):,} orgs")

    print("\n[1] COM-001 bridge")
    build_dim_pvm_driver()

    print("\n[2] HR-001")
    seg_df = build_dim_employee_segment()
    role_df = build_dim_role()
    build_fact_workforce(org_df, seg_df)
    build_fact_engagement_survey(org_df, seg_df)
    build_fact_recruiting(org_df, role_df)

    print("\n[3] COM-005")
    build_dim_sales_stage()
    rep_df = build_dim_salesrep(org_df)
    open_by_org = build_fact_pipeline(org_df, rep_df)
    build_fact_sales_target(org_df, open_by_org)

    print("\n[4] FIN-003")
    cc_df, cc_map = build_dim_cost_center(org_df)
    extend_fact_finance(org_df, cc_map)

    print("\n[5] SCM-004")
    build_dim_category()
    proc = _load_fact("fact_procurement")
    vendor_cat = build_dim_supplier(proc, org_df)
    extend_fact_procurement(proc, vendor_cat)
    build_fact_procurement_receipts(proc, vendor_cat)

    print("\n[OK] Gap-fill gold data generation complete.")


if __name__ == "__main__":
    main()
