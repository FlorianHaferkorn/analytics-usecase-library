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


# Where each function's staff physically sit (org types). fact_workforce is a full
# ragged-hierarchy people snapshot: every employee lives at exactly one home org node
# (store frontline, DC logistics, country/region/group office), counted once, rolling
# up cleanly through dim_org's ParentOrgKey tree — no double-count, full store drill.
_FUNCTION_ORG_TYPES = {
    "Retail Frontline": {"Store"},
    "Logistics": {"DC"},
    "Sales": {"Country", "Group"},
    "Corporate Functions": {"Country", "Region", "Group"},
    "IT & Digital": {"Country", "Region", "Group"},
}
# total own-staff FTE per org (split across that org's applicable function×tenure segments)
_HR_ORG_FTE = {"Store": 24.0, "DC": 60.0, "Country": 130.0, "Region": 30.0, "Group": 90.0}
_FUNCTION_WEIGHT = {"Retail Frontline": 1.0, "Logistics": 1.0, "Sales": 1.2,
                    "Corporate Functions": 1.6, "IT & Digital": 1.0}
_TENURE_WEIGHT = {"<1y": 0.8, "1-3y": 1.2, "3-5y": 1.0, "5y+": 1.1}
# roles recruited at each org type (drives fact_recruiting requisitions)
_ROLE_ORG_TYPES = {
    "Store Associate": {"Store"}, "Store Manager": {"Store"},
    "Warehouse Operative": {"DC"}, "Logistics Coordinator": {"DC"},
    "Sales Representative": {"Country"}, "Key Account Manager": {"Country", "Group"},
    "Data Analyst": {"Country", "Region", "Group"}, "Software Engineer": {"Country", "Region", "Group"},
    "HR Business Partner": {"Country", "Region", "Group"}, "Finance Analyst": {"Country", "Region", "Group"},
    "Category Manager": {"Group"}, "Marketing Specialist": {"Country", "Group"},
}
_RECRUIT_LAMBDA = {"Store": 0.40, "DC": 0.60, "Country": 1.5, "Region": 0.5, "Group": 1.0}


def _applicable_segments(otype: str, seg_records: list[dict]) -> list[dict]:
    return [s for s in seg_records if otype in _FUNCTION_ORG_TYPES[s["Function"]]]


def _country_weight(org) -> float:
    wt = float(_rng(int(org["OrgKey"]), 1).uniform(0.7, 1.4))
    if str(org.get("Country")) in ("Germany", "France", "United Kingdom"):
        wt *= 1.6
    return wt


def build_fact_workforce(org_df: pd.DataFrame, seg_df: pd.DataFrame) -> None:
    print("Generating fact_workforce …")
    seg_records = seg_df.to_dict("records")
    rows: list[dict] = []

    for _, org in org_df.iterrows():
        ok, otype = int(org["OrgKey"]), org["OrgType"]
        segs = _applicable_segments(otype, seg_records)
        if not segs:
            continue
        org_base = _HR_ORG_FTE[otype] * (_country_weight(org) if otype != "Group" else 1.0)

        seg_weights = np.array([
            _FUNCTION_WEIGHT[s["Function"]] * _TENURE_WEIGHT[s["Tenure Band"]]
            * float(_rng(ok, s["EmployeeSegmentKey"], 2).uniform(0.8, 1.2)) for s in segs])
        seg_weights = seg_weights / seg_weights.sum()

        for seg, sw in zip(segs, seg_weights):
            sk = seg["EmployeeSegmentKey"]
            hotspot = (seg["Function"], seg["Tenure Band"]) in _HR_HOTSPOTS
            ann_attr = float(_rng(ok, sk, 3).uniform(0.20, 0.26) if hotspot
                             else _rng(ok, sk, 3).uniform(0.09, 0.14))
            absence_rate = float(_rng(ok, sk, 4).uniform(0.02, 0.05))

            for date_obj in _month_ends():
                dk, year = int(date_obj.strftime("%Y%m%d")), date_obj.year
                growth = 1.0 + (_GROWTH.get(year, 1.0) - 1.0) * 0.5
                r = _rng(ok, sk, dk % 997)
                fte = max(0.5, org_base * float(sw) * growth * float(r.uniform(0.96, 1.04)))
                vol_leavers = fte * (ann_attr / 12.0) * float(r.uniform(0.7, 1.3))
                invol_leavers = fte * (0.02 / 12.0) * float(r.uniform(0.5, 1.5))
                hires = fte * (ann_attr / 12.0) * float(r.uniform(0.9, 1.4))
                sched_days = fte * 21.0
                absence_days = sched_days * absence_rate * float(r.uniform(0.85, 1.15))
                cost = fte * 4_050.0 * float(r.uniform(0.95, 1.06))
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
    seg_records = seg_df.to_dict("records")
    rows: list[dict] = []
    for _, org in org_df.iterrows():
        ok, otype = int(org["OrgKey"]), org["OrgType"]
        for seg in _applicable_segments(otype, seg_records):
            sk = seg["EmployeeSegmentKey"]
            hotspot = (seg["Function"], seg["Tenure Band"]) in _HR_HOTSPOTS
            base_eng = float(_rng(ok, sk, 5).uniform(55, 63) if hotspot
                             else _rng(ok, sk, 5).uniform(72, 82))
            for date_obj in _quarter_ends():
                dk = int(date_obj.strftime("%Y%m%d"))
                r = _rng(ok, sk, dk % 991)
                score = float(np.clip(base_eng + r.uniform(-4, 4), 0, 100))
                # store-team surveys are smaller than office populations
                hi = 40 if otype == "Store" else 120
                invited = int(max(6, r.randint(6, hi)))
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
    role_by_key = {int(rr["RoleKey"]): rr["Role"] for _, rr in role_df.iterrows()}
    rows: list[dict] = []
    for _, org in org_df.iterrows():
        ok, otype = int(org["OrgKey"]), org["OrgType"]
        roles = [rk for rk, name in role_by_key.items() if otype in _ROLE_ORG_TYPES.get(name, set())]
        if not roles:
            continue
        lam = _RECRUIT_LAMBDA.get(otype, 0.5)
        for date_obj in _month_ends():
            dk, year = int(date_obj.strftime("%Y%m%d")), date_obj.year
            r = _rng(ok, dk % 983)
            n_reqs = int(r.poisson(lam * _GROWTH.get(year, 1.0)))
            for _ in range(n_reqs):
                rk = int(r.choice(roles))
                base_ttf = 55 if role_by_key[rk] in ("Key Account Manager", "Category Manager") else 42
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
            "SalesRepKey": i, "Rep Name": f"Rep {i:02d}",
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

# Conformed functional cost centres (shared across entities — not 1:1 with org).
_COST_CENTERS = [
    (1, "Store Operations", "Retail", "Operations"),
    (2, "Merchandising", "Retail", "Operations"),
    (3, "Marketing", "Commercial", "SG&A"),
    (4, "Supply Chain & Logistics", "Supply Chain", "Operations"),
    (5, "IT & Digital", "Corporate", "SG&A"),
    (6, "General & Admin", "Corporate", "SG&A"),
]
# which cost centres incur OpEx at each org type
_CC_BY_ORGTYPE = {
    "Store": [1, 2, 3], "DC": [4], "Country": [2, 3, 5, 6], "Region": [5, 6], "Group": [3, 5, 6],
}
# FIN-003 governed storyline: the overrun concentrates in a few cost centres (Marketing, IT).
_OVERRUN_CC = {3, 5}


def build_dim_cost_center() -> pd.DataFrame:
    df = pd.DataFrame([{"CostCenterKey": k, "Cost Center": c, "Business Unit": bu, "Account Group": ag}
                       for (k, c, bu, ag) in _COST_CENTERS])
    _write_dim("dim_cost_center", df)
    return df


def extend_fact_finance(org_df: pd.DataFrame) -> None:
    print("Extending fact_finance (D&A, plan side; entity_month grain preserved) …")
    fin = _load_fact("fact_finance")
    r_seed = np.random.RandomState(RANDOM_SEED)
    ns = fin["Net Sales Amount"].to_numpy(dtype=float)
    cogs = fin["COGS Amount"].to_numpy(dtype=float)
    plan_opex = fin["Plan OpEx Amount"].to_numpy(dtype=float)
    ebit = fin["EBIT Amount"].to_numpy(dtype=float)

    n = len(fin)
    dna_ratio = r_seed.uniform(0.025, 0.040, n)
    dna_arr = ns * dna_ratio
    ebitda_arr = ebit + dna_arr                                # EBITDA = EBIT + D&A
    plan_ns_arr = ns * r_seed.uniform(0.98, 1.03, n)
    gm_ratio = np.divide(cogs, ns, out=np.full(n, 0.61), where=ns > 0)
    plan_cogs_arr = plan_ns_arr * gm_ratio * r_seed.uniform(0.99, 1.01, n)
    plan_dna_arr = plan_ns_arr * dna_ratio
    plan_ebit_arr = plan_ns_arr - plan_cogs_arr - plan_opex    # actual opex > plan opex ⇒ EBIT below plan
    plan_ebitda_arr = plan_ebit_arr + plan_dna_arr

    out = fin.copy()
    # drop the degenerate CostCenterKey if a prior run left it on disk (it was 1:1 with
    # OrgKey). Cost-centre detail now lives in fact_opex_costcenter (a genuine finer grain).
    out = out.drop(columns=["CostCenterKey"], errors="ignore")
    out["D&A Amount"] = np.round(dna_arr, 2)
    out["EBITDA Amount"] = np.round(ebitda_arr, 2)
    out["Plan Net Sales Amount"] = np.round(plan_ns_arr, 2)
    out["Plan COGS Amount"] = np.round(plan_cogs_arr, 2)
    out["Plan EBITDA Amount"] = np.round(plan_ebitda_arr, 2)
    fmt = write_fact_delta(FACTS / "fact_finance", out, partition_by=["Fiscal Year"])
    margin_act = float(np.sum(ebitda_arr) / np.sum(ns) * 100)
    margin_plan = float(np.sum(plan_ebitda_arr) / np.sum(plan_ns_arr) * 100)
    print(f"  Written fact_finance ({n:,} rows, +5 cols) [{fmt}] "
          f"| EBITDA margin actual {margin_act:.1f}% vs plan {margin_plan:.1f}% "
          f"({margin_act - margin_plan:+.1f} pp)")


def build_fact_opex_costcenter(org_df: pd.DataFrame) -> None:
    """OpEx split across cost centres at org × cost-centre × month grain. Sums back to
    fact_finance entity OpEx / Plan OpEx (entity measures invariant); the overrun
    concentrates in the _OVERRUN_CC cost centres (Marketing, IT) — the FIN-003 drill."""
    print("Generating fact_opex_costcenter …")
    fin = _load_fact("fact_finance")
    otype_by_key = org_df.set_index(org_df["OrgKey"].astype(int))["OrgType"].to_dict()
    rows: list[dict] = []
    # itertuples over positional cols (names have spaces): (DateKey, OrgKey, OpEx, Plan OpEx)
    fin = fin[["DateKey", "OrgKey", "OpEx Amount", "Plan OpEx Amount"]].copy()
    for rec in fin.itertuples(index=False):
        ok, dk = int(rec[1]), int(rec[0])
        e_opex, e_plan = float(rec[2]), float(rec[3])
        ccs = _CC_BY_ORGTYPE.get(otype_by_key.get(ok, "Group"), [6])
        r = _rng(ok, dk % 941, 12)
        base = {cc: float(r.uniform(0.8, 1.2)) for cc in ccs}
        wa = {cc: base[cc] * (1.25 if cc in _OVERRUN_CC else 1.0) for cc in ccs}   # actual share
        wp = {cc: base[cc] * (1.00 if cc in _OVERRUN_CC else 1.12) for cc in ccs}  # plan share
        sa, sp = sum(wa.values()), sum(wp.values())
        for cc in ccs:
            rows.append({
                "DateKey": dk, "OrgKey": ok, "CostCenterKey": cc,
                "OpEx Amount": round(e_opex * wa[cc] / sa, 2),
                "Plan OpEx Amount": round(e_plan * wp[cc] / sp, 2),
            })
    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_opex_costcenter", df, partition_by=["Fiscal Year"])
    # verify overrun concentration
    g = df.groupby("CostCenterKey").apply(
        lambda d: d["OpEx Amount"].sum() - d["Plan OpEx Amount"].sum(), include_groups=False)
    top = g.sort_values(ascending=False).head(2).index.tolist()
    print(f"  Written fact_opex_costcenter ({len(rows):,} rows) [{fmt}] | top-overrun cost centres {top} (expect {sorted(_OVERRUN_CC)})")


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


_VENDOR_POOL = list(range(1, 41))
_BASE_MONTHLY_PROC = 1_200_000.0   # base monthly spend per DC (matches supply-chain scale)


def build_dim_vendor(org_df: pd.DataFrame) -> dict[int, int]:
    # Procurement vendor master (keyed VendorKey), distinct from the finance/risk
    # supplier master (dim_supplier / SupplierKey) — different population & key space.
    regions = sorted(org_df["Region"].dropna().unique().tolist())
    rows, vendor_cat = [], {}
    for vk in _VENDOR_POOL:
        r = _rng(vk, 21)
        cat = int(r.choice([c[0] for c in _CATEGORIES]))
        vendor_cat[vk] = cat
        tier = str(r.choice(["A", "B", "C"], p=[0.3, 0.45, 0.25]))
        rows.append({"VendorKey": vk, "Vendor": f"Vendor {vk:02d}",
                     "Region": regions[vk % len(regions)], "Tier": tier})
    _write_dim("dim_vendor", pd.DataFrame(rows))
    return vendor_cat


def _dc_vendor_assignment(ok: int) -> tuple[list[int], np.ndarray]:
    rng_v = np.random.RandomState(RANDOM_SEED + ok * 13)
    n_vendors = int(rng_v.randint(6, 11))
    dc_vendors = rng_v.choice(_VENDOR_POOL, size=n_vendors, replace=False).tolist()
    raw = np.exp(-rng_v.uniform(0, 0.4) * np.arange(n_vendors))
    return dc_vendors, raw / raw.sum()


def build_fact_procurement(org_df: pd.DataFrame, vendor_cat: dict[int, int]) -> None:
    """PO-line grain (one row per purchase-order line) so PPV is auditable per line —
    PPV Amount = (Actual − Standard) unit price × Quantity, and the spend-weighted PPV %
    = ΣPPV / ΣBaseline Spend. Self-contained: does not depend on the monthly fact."""
    print("Generating fact_procurement (purchase_order_line) …")
    dc_orgs = org_df[org_df["OrgType"] == "DC"]["OrgKey"].astype(int).tolist()
    rows: list[dict] = []
    for ok in dc_orgs:
        dc_vendors, vendor_wts = _dc_vendor_assignment(ok)
        for date_obj in _month_ends():
            dk, year = int(date_obj.strftime("%Y%m%d")), date_obj.year
            growth = _GROWTH.get(year, 1.0)
            seasonality = apply_monthly_seasonality(date_obj, base_factor=1.0, seed=RANDOM_SEED)
            total_proc = _BASE_MONTHLY_PROC * growth * seasonality
            yr_idx = float(year - 2020)
            for vk, wt in zip(dc_vendors, vendor_wts):
                cat = vendor_cat[vk]
                is_leaking = cat in _LEAKING_CATEGORIES
                std_price = float(_rng(vk, 40).uniform(40.0, 160.0))    # vendor standard unit price
                rr = _rng(ok, vk, dk % 900)
                vend_spend = total_proc * float(wt) * float(rr.uniform(0.88, 1.12))
                n_lines = int(rr.randint(3, 9))
                line_wts = rr.uniform(0.5, 1.5, n_lines); line_wts /= line_wts.sum()
                # per-vendor contract & savings posture (stable within the month)
                on_contract_p = float(rr.uniform(0.55, 0.66) if is_leaking else rr.uniform(0.72, 0.85))
                realisation = float(rr.uniform(0.40, 0.80))
                for li in range(n_lines):
                    line_spend = vend_spend * float(line_wts[li])
                    # PPV: leaking categories climb over the years; others small ±
                    ppv_pct = ((0.010 + 0.012 * yr_idx) if is_leaking else float(rr.uniform(-0.015, 0.015))) \
                        + float(rr.uniform(-0.006, 0.006))
                    actual_price = std_price * (1.0 + ppv_pct)
                    qty = max(1.0, float(round(line_spend / actual_price)))
                    actual_spend = qty * actual_price
                    baseline_spend = qty * std_price
                    ppv_amount = actual_spend - baseline_spend
                    on_contract = actual_spend if (rr.random() < on_contract_p) else 0.0
                    addressable = actual_spend * float(rr.uniform(0.90, 0.98))
                    savings = actual_spend * float(rr.uniform(0.02, 0.08))
                    savings_target = savings / realisation
                    rows.append({
                        "DateKey": dk, "OrgKey": int(ok), "VendorKey": int(vk), "CategoryKey": int(cat),
                        "Quantity": qty,
                        "Standard Unit Price Amount": round(std_price, 4),
                        "Actual Unit Price Amount": round(actual_price, 4),
                        "Baseline Spend Amount": round(baseline_spend, 2),
                        "Actual Spend Amount": round(actual_spend, 2),
                        "PPV Amount": round(ppv_amount, 2),
                        "On-Contract Amount": round(on_contract, 2),
                        "Addressable Amount": round(addressable, 2),
                        "Savings Amount": round(savings, 2),
                        "Savings Target Amount": round(savings_target, 2),
                        "Procurement Amount": round(actual_spend, 2),   # continuity alias for line spend
                        "Vendor Count": 1, "PO Count": 1,
                    })
    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_procurement", df, partition_by=["Fiscal Year"])
    real = float(df["Savings Amount"].sum() / df["Savings Target Amount"].sum() * 100)
    onc = float(df["On-Contract Amount"].sum() / df["Addressable Amount"].sum() * 100)
    ppv = float(df["PPV Amount"].sum() / df["Baseline Spend Amount"].sum() * 100)
    print(f"  Written fact_procurement ({len(rows):,} PO lines) [{fmt}] "
          f"| realised savings {real:.0f}% of target · on-contract {onc:.0f}% · spend-weighted PPV {ppv:+.1f}%")


def build_fact_procurement_receipts(org_df: pd.DataFrame, vendor_cat: dict[int, int]) -> None:
    print("Generating fact_procurement_receipts …")
    # one receipt row per inbound delivery at DC × vendor × month, OTD ~88-96 %, leaking worse
    dc_orgs = org_df[org_df["OrgType"] == "DC"]["OrgKey"].astype(int).tolist()
    rows: list[dict] = []
    for ok in dc_orgs:
        dc_vendors, _ = _dc_vendor_assignment(ok)
        for vk in dc_vendors:
            cat = vendor_cat.get(vk, 1)
            otd_base = 0.90 if cat in _LEAKING_CATEGORIES else 0.94
            for date_obj in _month_ends():
                dk = int(date_obj.strftime("%Y%m%d"))
                r = _rng(ok, vk, dk % 953)
                for _ in range(max(1, int(r.randint(2, 6)))):
                    promise = pd.Timestamp(str(dk))
                    on_time = r.random() < float(np.clip(otd_base + r.uniform(-0.03, 0.03), 0.80, 0.99))
                    receipt = promise + timedelta(days=0 if on_time else int(r.randint(1, 8)))
                    rows.append({
                        "DateKey": dk, "OrgKey": int(ok), "VendorKey": int(vk), "CategoryKey": int(cat),
                        "Promise Date": int(promise.strftime("%Y%m%d")),
                        "Receipt Date": int(receipt.strftime("%Y%m%d")),
                        "On-Time Flag": bool(on_time),
                    })
    df = pd.DataFrame(rows)
    fmt = write_fact_delta(FACTS / "fact_procurement_receipts", df, partition_by=["Fiscal Year"])
    print(f"  Written fact_procurement_receipts ({len(rows):,} rows) [{fmt}] | supplier OTD {df['On-Time Flag'].mean()*100:.0f}%")


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
    build_dim_cost_center()
    extend_fact_finance(org_df)
    build_fact_opex_costcenter(org_df)

    print("\n[5] SCM-004")
    build_dim_category()
    vendor_cat = build_dim_vendor(org_df)
    build_fact_procurement(org_df, vendor_cat)
    build_fact_procurement_receipts(org_df, vendor_cat)

    print("\n[OK] Gap-fill gold data generation complete.")


if __name__ == "__main__":
    main()
