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

Grounding: all limit tables verified against learn.microsoft.com on 2026-08-05, see
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


def split(sizing: dict, domain_count: int) -> dict:
    """One capacity or several, from the chargeback requirement."""
    chargeback = sizing.get("chargeback_per_use_case")
    if chargeback is None:
        return {"capacities": None,
                "unknown": "chargeback_per_use_case — are costs charged back per use case?",
                "note": "The Azure invoice breaks down per capacity resource only. Fabric "
                        "workspaces are not ARM resources and cannot carry tags, so "
                        "per-workspace attribution needs the Fabric Chargeback app."}
    if chargeback:
        return {"capacities": max(1, domain_count),
                "reason": "Costs are charged back per use case, and only separate capacities "
                          "appear separately on the Azure invoice",
                "cost": "Parallelism limits and burst budget apply per capacity, so several "
                        "small capacities have less headroom than one large one of the same "
                        "total size."}
    return {"capacities": 1,
            "reason": "No chargeback requirement, so one capacity is preferable",
            "cost": "All workspaces share one throttling budget; a runaway workload can "
                    "slow the others. Workspace-level surge protection is a soft cap "
                    "checked every five minutes, not isolation."}


def recommend(blueprint: dict, prices: dict | None = None) -> dict:
    """Full capacity recommendation for a blueprint. Deterministic, no network access."""
    platform = blueprint.get("platform", {})
    sizing = platform.get("sizing", {}) or {}
    assigned = platform.get("capacity_sku")
    domains = blueprint.get("mesh", {}).get("domains", [])

    floor, reasons, unknowns = sizing_floor(sizing)
    proc = procurement(sizing)
    spl = split(sizing, len(domains))
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
