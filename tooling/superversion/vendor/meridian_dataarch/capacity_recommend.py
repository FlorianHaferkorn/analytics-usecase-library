"""capacity_recommend — a deterministic Fabric capacity (F-SKU) floor recommender. Readiness-Gate.

Honest by construction: **Microsoft publishes no hard "N users / X GB → SKU" formula** — it explicitly
frames capacity sizing as iterative/measured ("start small, measure via the Capacity Metrics app, scale")
and the SKU Estimator's output as "a starting point, not an absolute answer". So this tool does NOT
invent a formula. Instead it computes the **smallest F-SKU that satisfies every HARD, published
constraint** for the given workload — the defensible *floor* — and states which constraint set it, plus
advisories. The final purchase decision stays a measured, human call.

The hard constraints (all MS-published, cited below):
  * **Direct Lake HARD guardrails per SKU** — max model size on disk/OneLake (GB) and max rows per table
    (millions). Exceeding these on F1024 exceeds the ladder → escalate, never fake an in-ladder SKU.
  * **Feature minimums** — Direct Lake / Copilot / Fabric Data Agents all need a paid **F2+**; Copilot is
    *not* F64. **F64+** is required for **Free-license viewers** to consume Power BI content.
  * **Concurrency** — the per-SKU max concurrent DirectQuery connections (when a DQ workload is declared).

One SOFT limit, deliberately NOT treated as a hard cap: the per-SKU **Direct Lake max in-memory (GB)**.
MS states *Max Memory* is not a guardrail for Direct Lake — exceeding it pages columns in/out (and can
fall back to DirectQuery), it does not hard-block. So memory drives a *recommended* floor and a paging
advisory, but a model larger than F1024's working set still lands on **F1024** (not ``>F1024``).

Agnostic: this is a Fabric-capacity concern, source/stack-neutral (not SAP-specific). Deterministic; pure
function; it plans, never provisions. Sibling of ``recommend.py`` / ``handover_recommend.py``.

Grounding date: 2026-07-24. Sources (Microsoft Learn):
  - CU ladder + PBI equivalence: learn.microsoft.com/fabric/enterprise/licenses#core-building-blocks
  - Direct Lake guardrails per SKU: learn.microsoft.com/fabric/fundamentals/direct-lake-overview#fabric-capacity-requirements
  - Copilot min F2 (not F64): learn.microsoft.com/fabric/enterprise/fabric-copilot-capacity
  - Data Agent min F2 (preview): learn.microsoft.com/fabric/data-science/concept-data-agent#prerequisites
  - Free-viewer needs F64+: learn.microsoft.com/fabric/enterprise/licenses#per-user-or-individual-licenses
  - DirectQuery/semantic-model limits per SKU: learn.microsoft.com/fabric/enterprise/powerbi/service-premium-what-is#semantic-model-sku-limitation
  - Sizing is measured, not formulaic: learn.microsoft.com/fabric/enterprise/capacity-planning-plan-deployment
"""
from __future__ import annotations

from typing import Any

# Ordered F-SKU ladder with the HARD per-SKU ceilings. disk_gb=None → unlimited (F64+). Numbers are the
# MS-published guardrails (grounding 2026-07-24); F2048+ share the F1024 model ceilings, omitted here
# because a workload needing >F1024 warrants a measured, account-team-assisted sizing anyway.
_SKUS: list[dict[str, Any]] = [
    {"sku": "F2",    "cu": 2,    "dl_mem_gb": 3,   "disk_gb": 10,   "rows_m": 300,   "dq_conn": 5,   "pbi_equiv": None},
    {"sku": "F4",    "cu": 4,    "dl_mem_gb": 3,   "disk_gb": 10,   "rows_m": 300,   "dq_conn": 5,   "pbi_equiv": None},
    {"sku": "F8",    "cu": 8,    "dl_mem_gb": 3,   "disk_gb": 10,   "rows_m": 300,   "dq_conn": 10,  "pbi_equiv": "EM1/A1"},
    {"sku": "F16",   "cu": 16,   "dl_mem_gb": 5,   "disk_gb": 20,   "rows_m": 300,   "dq_conn": 10,  "pbi_equiv": "EM2/A2"},
    {"sku": "F32",   "cu": 32,   "dl_mem_gb": 10,  "disk_gb": 40,   "rows_m": 300,   "dq_conn": 10,  "pbi_equiv": "EM3/A3"},
    {"sku": "F64",   "cu": 64,   "dl_mem_gb": 25,  "disk_gb": None, "rows_m": 1500,  "dq_conn": 50,  "pbi_equiv": "P1"},
    {"sku": "F128",  "cu": 128,  "dl_mem_gb": 50,  "disk_gb": None, "rows_m": 3000,  "dq_conn": 75,  "pbi_equiv": "P2"},
    {"sku": "F256",  "cu": 256,  "dl_mem_gb": 100, "disk_gb": None, "rows_m": 6000,  "dq_conn": 100, "pbi_equiv": "P3"},
    {"sku": "F512",  "cu": 512,  "dl_mem_gb": 200, "disk_gb": None, "rows_m": 12000, "dq_conn": 200, "pbi_equiv": "P4"},
    {"sku": "F1024", "cu": 1024, "dl_mem_gb": 400, "disk_gb": None, "rows_m": 24000, "dq_conn": 200, "pbi_equiv": "P5"},
]
_FREE_VIEWER_MIN = "F64"        # F64+ lets Fabric (Free) viewers consume Power BI content
_FEATURE_MIN = "F2"            # Direct Lake / Copilot / Data Agents: paid F2+
GROUNDING_DATE = "2026-07-24"

_INDEX = {s["sku"]: i for i, s in enumerate(_SKUS)}

# Case-insensitive rank lookup incl. the ladder's own P/EM/A equivalents (a real tenant may report a legacy
# P-SKU or a lowercased F-SKU) — derived from _SKUS' pbi_equiv so it stays in sync.
_RANK_ALIAS: dict[str, int] = {}
for _i, _s in enumerate(_SKUS):
    _RANK_ALIAS[_s["sku"].upper()] = _i
    if _s["pbi_equiv"]:
        for _tok in _s["pbi_equiv"].split("/"):
            _RANK_ALIAS[_tok.strip().upper()] = _i


def _floor_by(predicate) -> int | None:
    """Index of the smallest SKU satisfying predicate(sku_row), or None if none in the ladder do."""
    return next((i for i, s in enumerate(_SKUS) if predicate(s)), None)


def sku_rank(sku: str) -> int | None:
    """Ladder position of a SKU (higher = larger capacity), or None for an unknown / off-ladder SKU
    (e.g. ``">F1024"``). Accepts F-SKUs case-insensitively plus the documented P/EM/A equivalents
    (``P1`` == ``F64``). Lets callers compare an assigned SKU against a recommended floor."""
    if not isinstance(sku, str):
        return None
    return _RANK_ALIAS.get(sku.strip().upper())


def recommend_capacity(workload: dict[str, Any]) -> dict[str, Any]:
    """Return the defensible **F-SKU floor** for a workload + the binding constraints + advisories.

    Workload keys (all optional; unknown fields ignored):
      * ``model_size_gb`` (float)         — the semantic model's in-memory footprint (Direct Lake).
      * ``max_table_rows_millions`` (num) — rows of the largest fact table (millions).
      * ``free_license_viewers`` (bool)   — will Fabric (Free)-licensed users consume Power BI content?
      * ``copilot`` (bool)                — Copilot in Fabric/Power BI needed?
      * ``data_agents`` (bool)            — Fabric Data Agents needed? (preview)
      * ``directquery_connections`` (int) — peak concurrent DirectQuery connections, if a DQ workload.
      * ``headroom_pct`` (int, default 20)— advisory head-room over the memory ceiling.

    Returns ``{recommended_sku, capacity_units, pbi_equivalent, binding_constraints[], floors{},
    advisories[], grounding_date, note}``. Floor = max over all constraint floors; ``binding_constraints``
    are the ones that set it. ``recommended_sku`` may be ``">F1024"`` when the workload exceeds the ladder.
    """
    floors: dict[str, str] = {}          # constraint → the SKU it requires (for transparency)
    idxs: list[tuple[str, int]] = []     # (constraint, ladder index) — the floor is the max index
    over_ladder: list[tuple[str, str]] = []   # (constraint, why) — HARD guardrails that exceed even F1024

    # every workload needs a paid F2+ for any of these Fabric features
    idxs.append(("feature_minimum_F2", _INDEX[_FEATURE_MIN]))
    floors["feature_minimum"] = _FEATURE_MIN

    mem = workload.get("model_size_gb")
    mem_pages = False
    if mem is not None:
        # Direct Lake in-memory working set. MS is explicit that *Max Memory* is NOT a hard guardrail for a
        # Direct Lake model (Direct Lake overview, note ¹): exceeding it PAGES columns in/out (and can fall
        # back to DirectQuery), it does not hard-block. So memory drives a RECOMMENDED floor but never
        # escalates the workload off-ladder — at >400 GB we still land on F1024 (the largest working set)
        # and flag the paging risk, rather than declaring the workload impossible.
        i = _floor_by(lambda s: s["dl_mem_gb"] >= mem)
        if i is None:
            i = len(_SKUS) - 1                           # cap at F1024; memory is soft, not a hard ceiling
            mem_pages = True
        idxs.append(("direct_lake_memory", i)); floors["direct_lake_memory"] = _SKUS[i]["sku"]
        # Max model size on disk/OneLake IS a hard guardrail (F2-F32: 10/20/40 GB; F64+ unlimited). Using
        # the in-memory size as a conservative lower bound on the on-disk footprint (on-disk ≥ compressed).
        di = _floor_by(lambda s: s["disk_gb"] is None or s["disk_gb"] >= mem)
        if di is None:
            over_ladder.append(("model_size_on_disk",
                                f"model_size_gb={mem} exceeds F1024's on-disk/OneLake guardrail"))
        else:
            idxs.append(("model_size_on_disk", di)); floors["model_size_on_disk"] = _SKUS[di]["sku"]

    rows = workload.get("max_table_rows_millions")
    if rows is not None:
        i = _floor_by(lambda s: s["rows_m"] >= rows)
        if i is None:
            over_ladder.append(("rows_per_table",
                                f"max_table_rows_millions={rows} exceeds F1024's 24000 M rows/table "
                                "Direct Lake guardrail"))
        else:
            idxs.append(("rows_per_table", i)); floors["rows_per_table"] = _SKUS[i]["sku"]

    if workload.get("free_license_viewers"):
        idxs.append(("free_license_viewers", _INDEX[_FREE_VIEWER_MIN])); floors["free_license_viewers"] = _FREE_VIEWER_MIN

    dq = workload.get("directquery_connections")
    if dq is not None:
        i = _floor_by(lambda s: s["dq_conn"] >= dq)
        if i is None:
            over_ladder.append(("directquery_concurrency",
                                f"directquery_connections={dq} exceeds F1024's 200-connection ceiling"))
        else:
            idxs.append(("directquery_concurrency", i)); floors["directquery_concurrency"] = _SKUS[i]["sku"]

    top = max(i for _, i in idxs)
    chosen = _SKUS[top]
    binding = sorted(c for c, i in idxs if i == top)

    advisories: list[str] = [
        "MS publishes no hard users/data→SKU formula; this is the constraint FLOOR, not the final size — "
        "validate on a trial/PAYG capacity, measure peak 30-second CU in the Capacity Metrics app, then "
        "pick the smallest SKU whose 30s CU budget (CU×30) covers the peak with headroom, and commit reserved.",
    ]
    headroom = workload.get("headroom_pct", 20)
    if not over_ladder and not mem_pages and mem is not None and chosen["dl_mem_gb"] \
            and mem > chosen["dl_mem_gb"] * (100 - headroom) / 100 and top + 1 < len(_SKUS):
        advisories.append(
            f"model_size_gb={mem} uses >{100 - headroom}% of {chosen['sku']}'s {chosen['dl_mem_gb']} GB "
            f"in-memory working set — consider {_SKUS[top + 1]['sku']} for head-room.")
    if mem_pages:                                        # memory exceeded the ladder → capped at F1024, will page
        advisories.append(
            f"model_size_gb={mem} exceeds F1024's {_SKUS[-1]['dl_mem_gb']} GB in-memory working set — "
            "Direct Lake will page columns in/out (MS: Max Memory is a performance limit, not a hard "
            "guardrail); consider table partitioning / an aggregations model, and validate with the "
            "Microsoft account team.")
    if workload.get("copilot") or workload.get("data_agents"):
        advisories.append("Copilot/Data Agents also require: the tenant Copilot switch ON, a supported "
                          "region (Azure OpenAI US/EU boundary; cross-geo needs a tenant setting), and a "
                          "PAID SKU (trial SKUs never qualify). Data Agents are in preview.")
    if workload.get("free_license_viewers"):
        data_top = max([i for c, i in idxs if c != "free_license_viewers"], default=0)
        if data_top < _INDEX[_FREE_VIEWER_MIN]:          # the non-viewer constraints alone fit a smaller SKU
            advisories.append("Free-license viewers force F64+ even though the data volume alone would fit a "
                              "smaller SKU — or license those viewers Pro/PPU on a smaller SKU instead.")

    result: dict[str, Any] = {
        # over a HARD guardrail (rows / disk / DQ), the ladder can't answer — never fake an in-ladder SKU:
        # blank the SKU-specific fields and name the over-ladder constraint(s) as binding.
        "recommended_sku": ">F1024" if over_ladder else chosen["sku"],
        "capacity_units": None if over_ladder else chosen["cu"],
        "pbi_equivalent": None if over_ladder else chosen["pbi_equiv"],
        "binding_constraints": sorted(c for c, _ in over_ladder) if over_ladder else binding,
        "floors": floors,
        "advisories": advisories,
        "grounding_date": GROUNDING_DATE,
        "note": "Defensible F-SKU floor from hard published constraints; final size is a measured decision.",
    }
    if over_ladder:
        result["exceeds_ladder"] = [why for _, why in over_ladder]
        result["advisories"].insert(0, "Workload exceeds the F1024 Direct Lake guardrail on: "
                                    + "; ".join(why for _, why in over_ladder)
                                    + " — engage the Microsoft account team (F2048+ / partitioning / "
                                    "DirectQuery-fallback design).")
    return result
