"""superversion.capacity — Fabric capacity floor + procurement recommendation.

The blueprint schema already carries the doctrine: ``platform.capacity_sku`` absent means
"not assigned", and consumers must then *state a recommended FLOOR instead of assuming
one*. Nobody computed that floor, so every consumer either guessed or stayed silent. This
module computes it.

Two questions are answered separately because they have different inputs and different
owners:

* **Sizing** — which SKU is technically sufficient. Driven by model size, Direct-Lake
  guardrails and viewer licensing. Owned by the architect.
* **Procurement** — reservation vs pay-as-you-go, and one capacity or several. Driven by
  operating hours and whether costs are charged back. Owned by the customer.

Conflating the two is the most common error in these conversations: F4 → F8 raises no
model-size limit at all (identical memory and Direct-Lake guardrails; the first jump is
F16), while F64 is a *licensing* threshold rather than a performance one.

Deterministic and offline by design. Prices change and must not be baked in, so the
break-even arithmetic that needs them takes them as an argument; without prices the module
emits the formula and records the gap rather than substituting a plausible number. Same
rule for missing sizing inputs: they land in ``unknowns``, never in a default.

Grounding: all limit tables verified against learn.microsoft.com on 2026-08-05; overage
and Fabric Planning figures on 2026-09-29. See
``docs/agent/skills/recommend-fabric-capacity.md`` for the source list.
"""
from __future__ import annotations

# --- SKU limit tables (learn.microsoft.com, verified 2026-08-05) ---------------------
# service-premium-what-is#semantic-model-sku-limitation
SKU_ORDER = ("F2", "F4", "F8", "F16", "F32", "F64",
             "F128", "F256", "F512", "F1024", "F2048")

CU: dict[str, int] = {
    "F2": 2, "F4": 4, "F8": 8, "F16": 16, "F32": 32, "F64": 64,
    "F128": 128, "F256": 256, "F512": 512, "F1024": 1024, "F2048": 2048,
}

# Max memory per semantic model, GB.
MAX_MODEL_MEMORY_GB: dict[str, int] = {
    "F2": 3, "F4": 3, "F8": 3, "F16": 5, "F32": 10, "F64": 25,
    "F128": 50, "F256": 100, "F512": 200, "F1024": 400, "F2048": 400,
}

# direct-lake-overview#fabric-capacity-requirements
# None = unlimited per docs.
DIRECT_LAKE_ROWS_M: dict[str, int] = {
    "F2": 300, "F4": 300, "F8": 300, "F16": 300, "F32": 300, "F64": 1500,
    "F128": 3000, "F256": 6000, "F512": 12000, "F1024": 24000, "F2048": 24000,
}
DIRECT_LAKE_MODEL_GB: dict[str, int | None] = {
    "F2": 10, "F4": 10, "F8": 10, "F16": 20, "F32": 40, "F64": None,
    "F128": None, "F256": None, "F512": None, "F1024": None, "F2048": None,
}

# spark-job-concurrency-and-queueing#spark-capacity-sku-limits (burst factor is 3x)
SPARK_VCORES_BASELINE: dict[str, int] = {
    "F2": 4, "F4": 8, "F8": 16, "F16": 32, "F32": 64, "F64": 128,
    "F128": 256, "F256": 512, "F512": 1024, "F1024": 2048, "F2048": 4096,
}

MODEL_REFRESH_PARALLELISM: dict[str, int] = {
    "F2": 1, "F4": 2, "F8": 5, "F16": 10, "F32": 20, "F64": 40,
    "F128": 80, "F256": 160, "F512": 320, "F1024": 640, "F2048": 1280,
}

# licenses#workspace-types — below F64 every Power BI viewer needs a Pro licence.
FREE_VIEWER_MIN_SKU = "F64"

# --- Capacity overage (learn.microsoft.com, verified 2026-09-29) --------------------
# enterprise/capacity-overage-overview + enterprise/enable-capacity-overage; GA Sep 2026
# per fundamentals/whats-new. Overage is ON by default for every newly created F capacity,
# so a proposal that does not ask the customer silently carries an open-ended cost line.
# CU hours per day as published in the overage-threshold table (= CU x 24).
CU_HOURS_PER_DAY: dict[str, int] = {
    "F2": 48, "F4": 96, "F8": 192, "F16": 384, "F32": 768, "F64": 1536,
    "F128": 3072, "F256": 6144, "F512": 12288, "F1024": 24576, "F2048": 49152,
}
# Overage CU hours are billed on a separate meter at three times the pay-as-you-go rate.
OVERAGE_PRICE_MULTIPLIER = 3
# Default rolling 24-h threshold at capacity creation: 25 % of the daily CU hours
# (slider in 5 % steps, or an absolute CU-hour value).
OVERAGE_DEFAULT_THRESHOLD_PCT = 25
# Learn: keep the threshold below one third of the daily CU hours — above that, scaling up
# the SKU costs about the same (3x rate x 1/3 = 1x the daily capacity cost).
OVERAGE_RECOMMENDED_MAX_FRACTION = 1 / 3
# Quota needed = threshold / 24 CUs (the threshold is spread across 24 hours).
OVERAGE_QUOTA_DIVISOR = 24
# The threshold is evaluated every 5 minutes and running operations continue, so real
# charges can exceed it: threshold x 3 x PAYG is a derived figure, not a hard cap.
OVERAGE_EVALUATION_INTERVAL_MIN = 5

# --- Fabric Planning (learn.microsoft.com, verified 2026-09-29) ----------------------
# iq/plan/resources/billing-fabric-plan. A session lasts 730 h (30 days), cannot be ended
# early and is tracked per tenant + user + capacity; it consumes CU of the capacity it runs
# on (meters "Fabric Planning - Planner/Stakeholder/Viewer Sessions").
PLANNING_SESSION_HOURS = 730
PLANNING_SESSION_CU_HOURS: dict[str, int] = {"planner": 847, "stakeholder": 168, "viewer": 37}
# Learn recommends an estimated 30 % buffer for the other Fabric workloads (SQL, OneLake,
# XMLA) that planning deployments use besides the sessions themselves.
PLANNING_WORKLOAD_BUFFER_PCT = 30

# Reservation costs 59.5 % of the pay-as-you-go rate, so it pays off above 59.5 % runtime.
# 0.595 * 168 h = 99.96 h/week. Identical across SKUs and regions (proportional discount).
RESERVATION_BREAKEVEN_HOURS_PER_WEEK = 100.0
HOURS_PER_WEEK = 168.0


def _rank(sku: str) -> int:
    return SKU_ORDER.index(sku)


def _max_sku(*skus: str | None) -> str | None:
    present = [s for s in skus if s]
    return max(present, key=_rank) if present else None


def _smallest_where(table: dict[str, int | None], needed: float) -> str | None:
    """Smallest SKU whose limit covers ``needed``; None if no SKU does."""
    for sku in SKU_ORDER:
        limit = table[sku]
        if limit is None or limit >= needed:
            return sku
    return None


def sizing_floor(sizing: dict) -> tuple[str | None, list[str], list[str]]:
    """Smallest technically sufficient SKU, its reasons, and the missing inputs.

    Every driver is optional. A driver that is absent produces an entry in ``unknowns``
    and contributes no floor — it must not be silently treated as zero, because a floor
    derived from half the inputs looks as authoritative as a complete one.
    """
    reasons: list[str] = []
    unknowns: list[str] = []
    floor: str | None = None

    model_gb = sizing.get("largest_model_gb")
    if model_gb is None:
        unknowns.append("largest_model_gb — size of the biggest semantic model")
    else:
        sku = _smallest_where(MAX_MODEL_MEMORY_GB, model_gb)
        if sku is None:
            reasons.append(f"largest_model_gb={model_gb} exceeds every F-SKU "
                           f"(max {MAX_MODEL_MEMORY_GB[SKU_ORDER[-1]]} GB) — split the model")
        else:
            floor = _max_sku(floor, sku)
            reasons.append(f"{sku}: memory per semantic model {MAX_MODEL_MEMORY_GB[sku]} GB "
                           f"covers largest_model_gb={model_gb}")

    rows_m = sizing.get("largest_table_rows_millions")
    if rows_m is None:
        unknowns.append("largest_table_rows_millions — rows in the biggest fact table")
    else:
        sku = _smallest_where(DIRECT_LAKE_ROWS_M, rows_m)
        if sku is None:
            reasons.append(f"largest_table_rows_millions={rows_m} exceeds every F-SKU — "
                           "partition the table or accept DirectQuery fallback")
        else:
            floor = _max_sku(floor, sku)
            reasons.append(f"{sku}: Direct Lake allows {DIRECT_LAKE_ROWS_M[sku]} M rows per "
                           f"table, needed {rows_m} M")

    viewers = sizing.get("viewers")
    if viewers is None:
        unknowns.append("viewers — people consuming reports (drives the F64 licence threshold)")
    elif viewers > 0:
        reasons.append(f"{viewers} viewer(s) need a Pro licence each below "
                       f"{FREE_VIEWER_MIN_SKU}; see licence_breakeven for when "
                       f"{FREE_VIEWER_MIN_SKU} becomes the cheaper option")

    return floor, reasons, unknowns


def licence_breakeven(floor: str, prices: dict | None) -> dict:
    """Viewer count above which ``FREE_VIEWER_MIN_SKU`` beats ``floor`` plus Pro licences.

    Without prices this returns the formula and the required inputs instead of a number.
    The result is routinely counter-intuitive — the jump to F64 is large enough that
    several hundred viewers are needed before it pays off — which is exactly why it should
    be computed rather than asserted.
    """
    formula = ("(cost(F64) - cost(floor)) / pro_licence_per_user_per_year; "
               "fetch capacity prices from the Azure Retail Prices API and the Pro price "
               "from the Power BI pricing page")
    if _rank(floor) >= _rank(FREE_VIEWER_MIN_SKU):
        return {"applicable": False,
                "reason": f"floor {floor} is already at or above {FREE_VIEWER_MIN_SKU}"}
    if not prices:
        return {"applicable": True, "viewers": None, "formula": formula,
                "missing": ["capacity_cu_year", "pro_licence_user_year"]}

    cu_year = prices.get("capacity_cu_year")
    pro_year = prices.get("pro_licence_user_year")
    if not cu_year or not pro_year:
        return {"applicable": True, "viewers": None, "formula": formula,
                "missing": [k for k in ("capacity_cu_year", "pro_licence_user_year")
                            if not prices.get(k)]}

    delta = (CU[FREE_VIEWER_MIN_SKU] - CU[floor]) * cu_year
    return {"applicable": True,
            "viewers": int(delta // pro_year) + 1,
            "basis": f"({CU[FREE_VIEWER_MIN_SKU]} - {CU[floor]}) CU x {cu_year}/CU/year "
                     f"/ {pro_year} per Pro licence/year",
            "prices_are_inputs": True}


def procurement(sizing: dict) -> dict:
    """Reservation or pay-as-you-go, from operating hours alone."""
    hours = sizing.get("operating_hours_per_week")
    if hours is None:
        return {"model": None,
                "unknown": "operating_hours_per_week — hours the capacity must be available",
                "threshold_hours_per_week": RESERVATION_BREAKEVEN_HOURS_PER_WEEK,
                "note": "A capacity is billed by provisioned size, not by usage. An idle "
                        "capacity costs the same as a busy one, so this is the only input "
                        "that decides the model."}
    if hours >= RESERVATION_BREAKEVEN_HOURS_PER_WEEK:
        return {"model": "reservation",
                "reason": f"{hours} h/week is at or above the {RESERVATION_BREAKEVEN_HOURS_PER_WEEK} h "
                          "break-even (59.5 % runtime)",
                "term": "1 year — a 3-year reservation costs exactly 3x the 1-year one, "
                        "so a longer commitment buys nothing",
                "caveat": "Reservation and pausing are mutually exclusive: the discount is "
                          "settled hourly and is lost for paused hours."}
    return {"model": "pay-as-you-go",
            "reason": f"{hours} h/week is below the {RESERVATION_BREAKEVEN_HOURS_PER_WEEK} h break-even",
            "requires": "Automated pause and resume (Azure Automation runbook; Fabric has no "
                        "built-in scheduler). Fabric is fully unavailable while paused and "
                        "scheduled runs falling into the pause window are not caught up.",
            "caveat": "Only worth it for dev and test capacities. For a production capacity "
                      "the outage risk usually outweighs the saving."}


#: D-596 (Meridian decision register, 30.09.2026): stage -> stage group. Production and
#: non-production run on separate capacities, consolidated within each group.
STAGE_GROUP: dict[str, str] = {"prod": "prod", "test": "non_prod", "dev": "non_prod"}


def split(sizing: dict, domain_count: int, stages: list[str] | None = None,
          tier1_workspaces: list[str] | None = None) -> dict:
    """How many capacities: stage separation (D-596) times the chargeback requirement.

    Two independent axes. **Stages** decide the stage groups: with production and at least
    one non-production stage there are two groups (``prod`` and ``non_prod``), because
    smoothing and throttling act per capacity and development and test load would
    otherwise throttle production (Learn ``enterprise/capacity-planning-*`` and the CI/CD
    best-practice guide recommend a capacity per environment; D-596 consolidates dev and
    test into one pausable non-production capacity). **Chargeback** decides the count
    within a group: one per domain when costs are charged back, otherwise one. Tier-1
    workspaces (``surge_class = mission_critical``) are reported as an option for a
    dedicated capacity (D-596 option c), never added to the count.
    """
    groups = sorted({STAGE_GROUP[s] for s in (stages or []) if s in STAGE_GROUP},
                    key=("prod", "non_prod").index) or ["prod"]
    if "non_prod" in groups and "prod" not in groups:
        groups = ["non_prod"]
    stage_note = ("Production and non-production run on separate capacities (D-596): "
                  "smoothing and throttling act per capacity, so development and test load "
                  "cannot throttle production. The non-production capacity can be paused "
                  "and sized small; its price is an extra line, quoted from current prices "
                  "only.") if len(groups) == 2 else (
                  "One stage group only (no staged workspaces), so there is nothing to "
                  "separate by stage.")
    chargeback = sizing.get("chargeback_per_use_case")
    base: dict = {"stage_groups": groups, "stage_separation": stage_note}
    if tier1_workspaces:
        base["tier1_option"] = {
            "workspaces": sorted(tier1_workspaces),
            "note": "Mission-critical workspaces may get a capacity of their own (D-596 "
                    "option c). That is an offer with extra cost and a customer decision, "
                    "not part of the count."}
    if chargeback is None:
        return {**base, "capacities": None, "per_group": None,
                "unknown": "chargeback_per_use_case — are costs charged back per use case?",
                "note": "The Azure invoice breaks down per capacity resource only. Fabric "
                        "workspaces are not ARM resources and cannot carry tags, so "
                        "per-workspace attribution needs the Fabric Chargeback app."}
    per_group = max(1, domain_count) if chargeback else 1
    out = {**base, "capacities": per_group * len(groups),
           "per_group": {g: per_group for g in groups}}
    if chargeback:
        out.update({
            "reason": "Costs are charged back per use case, and only separate capacities "
                      "appear separately on the Azure invoice",
            "cost": "Parallelism limits and burst budget apply per capacity, so several "
                    "small capacities have less headroom than one large one of the same "
                    "total size."})
    else:
        out.update({
            "reason": "No chargeback requirement, so one capacity per stage group is "
                      "preferable",
            "cost": "All workspaces of a stage group share one throttling budget; a runaway "
                    "workload can slow the others. Workspace-level surge protection is a soft "
                    "cap checked every five minutes, not isolation."})
    return out


OVERAGE_CUSTOMER_QUESTION = (
    "Capacity overage: switch it off, or set a rolling 24-hour threshold of X CU hours? "
    "It is on by default for new F capacities (threshold {default_pct} % = {default_cu_h} "
    "CU hours/day on {sku}) and is billed at {mult}x the pay-as-you-go rate."
)


def overage_profile(sku: str, threshold_cu_hours: float | None = None,
                    payg_usd_per_cu_hour: float | None = None) -> dict:
    """Overage figures for one F-SKU: daily CU hours, threshold, quota, cost ceiling.

    ``threshold_cu_hours`` None means the customer has not decided; the Microsoft default
    (25 % of the daily CU hours) is then shown as what will happen *unless* they decide,
    and the decision is returned as an open customer question — never as an assumption.
    The cost figure is derived (threshold x 3 x PAYG per CU hour), not measured, and is a
    lower bound of the worst case: the threshold is checked every five minutes and
    operations already running continue, so real charges can exceed it.
    """
    if sku not in CU_HOURS_PER_DAY:
        raise KeyError(f"Unknown F-SKU: {sku}")
    daily = CU_HOURS_PER_DAY[sku]
    default_threshold = daily * OVERAGE_DEFAULT_THRESHOLD_PCT / 100
    decided = threshold_cu_hours is not None
    threshold = float(threshold_cu_hours) if decided else default_threshold
    out: dict = {
        "sku": sku,
        "cu_hours_per_day": daily,
        "default_threshold_cu_hours": default_threshold,
        "threshold_cu_hours": threshold,
        "threshold_source": "customer" if decided else "microsoft_default",
        "recommended_max_threshold_cu_hours": round(daily * OVERAGE_RECOMMENDED_MAX_FRACTION, 2),
        "quota_cu_required": round(threshold / OVERAGE_QUOTA_DIVISOR, 2),
        "above_recommended_max": threshold > daily * OVERAGE_RECOMMENDED_MAX_FRACTION,
        "max_cost_per_day_formula": (f"threshold_cu_hours x {OVERAGE_PRICE_MULTIPLIER} x "
                                     "payg_usd_per_cu_hour"),
        "evidence": "derived",
        "caveat": (f"Not a hard cap: evaluated every {OVERAGE_EVALUATION_INTERVAL_MIN} "
                   "minutes and running operations continue, so real charges can exceed "
                   "the derived maximum."),
    }
    if payg_usd_per_cu_hour is not None:
        out["max_cost_per_day_usd"] = round(
            threshold * OVERAGE_PRICE_MULTIPLIER * float(payg_usd_per_cu_hour), 2)
    if not decided:
        out["customer_question"] = OVERAGE_CUSTOMER_QUESTION.format(
            default_pct=OVERAGE_DEFAULT_THRESHOLD_PCT, default_cu_h=f"{default_threshold:g}",
            sku=sku, mult=OVERAGE_PRICE_MULTIPLIER)
    return out


def planning_load(sessions: dict, sku: str | None = None) -> dict:
    """CU load of Fabric Planning sessions over one 30-day session window.

    ``sessions`` maps role (planner/stakeholder/viewer) to the number of users active in
    the window. The result is capacity consumption, not a separate price: sessions burn CU
    of the capacity they run on. Against ``sku`` it reports the share of that capacity's
    CU hours in the same 730-hour window and whether the Learn-recommended 30 % buffer for
    the other workloads still fits. Automation jobs (billed per successful job) are not
    included — Learn states the rate as "2 CU" without a time unit.
    """
    unknown_roles = sorted(set(sessions) - set(PLANNING_SESSION_CU_HOURS))
    if unknown_roles:
        raise ValueError(f"Unknown planning role(s): {unknown_roles}; "
                         f"valid: {sorted(PLANNING_SESSION_CU_HOURS)}")
    cu_hours = sum(PLANNING_SESSION_CU_HOURS[r] * int(n) for r, n in sessions.items())
    out: dict = {
        "sessions": {r: int(n) for r, n in sorted(sessions.items())},
        "cu_hours_per_session_window": cu_hours,
        "session_window_hours": PLANNING_SESSION_HOURS,
        "average_cu": round(cu_hours / PLANNING_SESSION_HOURS, 2),
        "not_included": "automation jobs (Learn: '2 CU' per successful job, unit unclear)",
    }
    if sku:
        if sku not in CU:
            raise KeyError(f"Unknown F-SKU: {sku}")
        window_capacity = CU[sku] * PLANNING_SESSION_HOURS
        share = round(100 * cu_hours / window_capacity, 1)
        out["sku"] = sku
        out["share_of_capacity_pct"] = share
        out["fits_with_buffer"] = share <= 100 - PLANNING_WORKLOAD_BUFFER_PCT
    return out


def recommend(blueprint: dict, prices: dict | None = None) -> dict:
    """Full capacity recommendation for a blueprint. Deterministic, no network access."""
    platform = blueprint.get("platform", {})
    sizing = platform.get("sizing", {}) or {}
    assigned = platform.get("capacity_sku")
    domains = blueprint.get("mesh", {}).get("domains", [])
    stages = (blueprint.get("governance") or {}).get("stages") or []
    tier1 = sorted({ws.get("name", "") for d in domains for ws in d.get("workspaces", []) or []
                    if ws.get("surge_class") == "mission_critical"
                    and STAGE_GROUP.get(ws.get("stage") or "prod", "prod") == "prod"})

    floor, reasons, unknowns = sizing_floor(sizing)
    proc = procurement(sizing)
    spl = split(sizing, len(domains), stages, tier1)
    for section in (proc, spl):
        if section.get("unknown"):
            unknowns.append(section["unknown"])

    out: dict = {
        "stack": platform.get("stack"),
        "assigned_sku": assigned,
        "recommended_floor": floor,
        "floor_reasons": reasons,
        "procurement": proc,
        "split": spl,
        "unknowns": unknowns,
    }
    overage_sku = assigned if assigned in CU_HOURS_PER_DAY else floor
    if overage_sku:
        payg = (prices or {}).get("payg_usd_per_cu_hour")
        # The blueprint schema has no threshold field yet (sizing is closed), so the
        # decision is always open here and surfaces as a customer question.
        out["overage"] = overage_profile(overage_sku, None, payg)
        if out["overage"].get("customer_question"):
            out["customer_questions"] = [out["overage"]["customer_question"]]
    # D-595: Fabric Planning as a blueprint option. Sessions come from the customer; a
    # missing role count is an open question, never a default.
    planning = platform.get("planning") or {}
    if planning.get("enabled"):
        sessions = planning.get("sessions") or {}
        missing = [r for r in sorted(PLANNING_SESSION_CU_HOURS) if sessions.get(r) is None]
        if missing:
            unknowns.append("platform.planning.sessions — active users per role in 30 days: "
                            + ", ".join(missing))
            out["customer_questions"] = out.get("customer_questions", []) + [
                "Fabric Planning: how many people work as planner, stakeholder and viewer "
                "in a 30-day window? Their sessions consume capacity CU; the euro amount "
                "follows from the capacity price and is not stated without it."]
        else:
            out["planning"] = planning_load(
                {r: int(sessions[r]) for r in PLANNING_SESSION_CU_HOURS},
                assigned if assigned in CU else (floor if floor in CU else None))
    if floor:
        out["licence_breakeven"] = licence_breakeven(floor, prices)
        out["headroom_at_floor"] = {
            "spark_vcores_baseline": SPARK_VCORES_BASELINE[floor],
            "spark_vcores_burst": SPARK_VCORES_BASELINE[floor] * 3,
            "parallel_model_refreshes": MODEL_REFRESH_PARALLELISM[floor],
        }
    if assigned and floor and _rank(assigned) < _rank(floor):
        out["conflict"] = (f"assigned capacity_sku={assigned} is below the derived floor "
                           f"{floor} — the sizing inputs do not fit the assigned capacity")
    if not floor and not assigned:
        out["verdict"] = ("No SKU assigned and no floor derivable. State what is missing "
                          "rather than assuming a SKU.")
    return out
