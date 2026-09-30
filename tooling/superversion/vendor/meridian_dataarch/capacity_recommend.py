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
    {"sku": "F2",    "cu": 2,    "dl_mem_gb": 3,   "disk_gb": 10,   "rows_m": 300, "dl_files": 1000, "dl_row_groups": 1000,   "dq_conn": 5,   "pbi_equiv": None},
    {"sku": "F4",    "cu": 4,    "dl_mem_gb": 3,   "disk_gb": 10,   "rows_m": 300, "dl_files": 1000, "dl_row_groups": 1000,   "dq_conn": 5,   "pbi_equiv": None},
    {"sku": "F8",    "cu": 8,    "dl_mem_gb": 3,   "disk_gb": 10,   "rows_m": 300, "dl_files": 1000, "dl_row_groups": 1000,   "dq_conn": 10,  "pbi_equiv": "EM1/A1"},
    {"sku": "F16",   "cu": 16,   "dl_mem_gb": 5,   "disk_gb": 20,   "rows_m": 300, "dl_files": 1000, "dl_row_groups": 1000,   "dq_conn": 10,  "pbi_equiv": "EM2/A2"},
    {"sku": "F32",   "cu": 32,   "dl_mem_gb": 10,  "disk_gb": 40,   "rows_m": 300, "dl_files": 1000, "dl_row_groups": 1000,   "dq_conn": 10,  "pbi_equiv": "EM3/A3"},
    {"sku": "F64",   "cu": 64,   "dl_mem_gb": 25,  "disk_gb": None, "rows_m": 1500, "dl_files": 5000, "dl_row_groups": 5000,  "dq_conn": 50,  "pbi_equiv": "P1"},
    {"sku": "F128",  "cu": 128,  "dl_mem_gb": 50,  "disk_gb": None, "rows_m": 3000, "dl_files": 5000, "dl_row_groups": 5000,  "dq_conn": 75,  "pbi_equiv": "P2"},
    {"sku": "F256",  "cu": 256,  "dl_mem_gb": 100, "disk_gb": None, "rows_m": 6000, "dl_files": 5000, "dl_row_groups": 5000,  "dq_conn": 100, "pbi_equiv": "P3"},
    {"sku": "F512",  "cu": 512,  "dl_mem_gb": 200, "disk_gb": None, "rows_m": 12000, "dl_files": 10000, "dl_row_groups": 10000, "dq_conn": 200, "pbi_equiv": "P4"},
    {"sku": "F1024", "cu": 1024, "dl_mem_gb": 400, "disk_gb": None, "rows_m": 24000, "dl_files": 10000, "dl_row_groups": 10000, "dq_conn": 200, "pbi_equiv": "P5"},
]
_FREE_VIEWER_MIN = "F64"        # F64+ lets Fabric (Free) viewers consume Power BI content
_FEATURE_MIN = "F2"            # Direct Lake / Copilot / Data Agents: paid F2+
GROUNDING_DATE = "2026-07-24"

_INDEX = {s["sku"]: i for i, s in enumerate(_SKUS)}

# SKUs ABOVE the recommendation ladder. Two different questions were being answered by one list:
# "which SKU do we *recommend*?" (stops at F1024 on purpose — see above) and "which SKU can we
# *recognise* when the customer already runs one?". Those sets aren't the same, and collapsing them
# made a real, documented SKU look unknown: an assigned F2048 yielded rank None → capacity readiness
# UNKNOWN, and ``sku_budget`` returned {} → the Direct Lake guardrail runbook was emitted EMPTY for
# exactly the largest customers. So: recognition continues past the ladder, recommendation does not.
# MS publishes identical Direct Lake ceilings for F2048/F4096/F8192 as for F1024 — nothing is guessed
# here. ``dq_conn``/``pbi_equiv`` are deliberately absent (no P-SKU exists above P5 and the DQ limit
# isn't published for these) and no consumer of this table needs them.
_ABOVE_LADDER: list[dict[str, Any]] = [
    {"sku": "F2048", "cu": 2048, "dl_mem_gb": 400, "disk_gb": None, "rows_m": 24000,
     "dl_files": 10000, "dl_row_groups": 10000},
    {"sku": "F4096", "cu": 4096, "dl_mem_gb": 400, "disk_gb": None, "rows_m": 24000,
     "dl_files": 10000, "dl_row_groups": 10000},
    {"sku": "F8192", "cu": 8192, "dl_mem_gb": 400, "disk_gb": None, "rows_m": 24000,
     "dl_files": 10000, "dl_row_groups": 10000},
]

# Case-insensitive rank lookup incl. the ladder's own P/EM/A equivalents (a real tenant may report a legacy
# P-SKU or a lowercased F-SKU) — derived from _SKUS' pbi_equiv so it stays in sync. The above-ladder SKUs
# get ranks beyond the ladder; since _floor_by only ever indexes into _SKUS, a recommended floor can never
# land there — the extra ranks widen what we can *compare against*, not what we propose.
_RANK_ALIAS: dict[str, int] = {}
for _i, _s in enumerate(_SKUS):
    _RANK_ALIAS[_s["sku"].upper()] = _i
    if _s["pbi_equiv"]:
        for _tok in _s["pbi_equiv"].split("/"):
            _RANK_ALIAS[_tok.strip().upper()] = _i
for _j, _s in enumerate(_ABOVE_LADDER):
    _RANK_ALIAS[_s["sku"].upper()] = len(_SKUS) + _j

#: Alle F-SKUs, die sich **anlegen** lassen (F2 … F8192), aufsteigend. Anders als ``sku_rank`` ohne
#: P/EM/A-Aliasse: eine Kapazitaets-Anlage per ARM (``Microsoft.Fabric/capacities``, ``sku.tier =
#: Fabric``) kennt nur F-Namen. Gegenprobe: Learn ``enterprise/capacity-overage-overview``, Tabelle
#: „Capacity overage thresholds" (gelesen 30.09.2026), fuehrt genau diese 13 SKUs. F512 und groesser
#: gibt es nicht in jeder Region (``enterprise/licenses``) — das prueft erst Azure beim Anlegen.
F_SKUS: tuple[str, ...] = tuple(s["sku"] for s in (*_SKUS, *_ABOVE_LADDER))


def sku_ceilings(sku: str) -> dict[str, Any] | None:
    """The published per-SKU ceilings for ``sku`` — ladder **or** above it — or None if unrecognised.

    The single home for "what are this SKU's hard limits", so callers (``direct_lake_guardrails``,
    readiness) never have to know that the recommendation ladder ends earlier than the SKU list does.
    Resolves through ``sku_rank``, so a tenant that reports a legacy ``P3`` gets F256's ceilings instead
    of nothing — the alias table already knew the mapping; only this lookup didn't use it.
    """
    rank = sku_rank(sku)
    if rank is None:
        return None
    return (*_SKUS, *_ABOVE_LADDER)[rank]


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
      * ``planning_sessions`` (dict)      — active Fabric Planning sessions per 30 days,
        ``{"planner": n, "stakeholder": n, "viewer": n}`` (I-21 W4.7, see ``planning_last``).

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

    # I-21 W4.7: Fabric Planning rechnet je 30-Tage-Sitzung ab (Learn, gelesen 29.09.2026). Das ist
    # eine Mittelwertlast, keine Spitze — deshalb bindet sie nur, wenn sie den Rest uebersteigt.
    planung = workload.get("planning_sessions")
    if isinstance(planung, dict) and any(planung.get(r) for r in PLANNING_CU_STUNDEN_JE_SITZUNG):
        pl = planning_last(**{r: int(planung.get(r) or 0) for r in PLANNING_CU_STUNDEN_JE_SITZUNG})
        i = _floor_by(lambda s: s["cu"] >= pl["mit_puffer_cu"])
        if i is None:
            over_ladder.append(("planning_sessions",
                                f"planning sessions need {pl['mit_puffer_cu']} CU on average "
                                "(incl. buffer), more than F1024 provides"))
        else:
            idxs.append(("planning_sessions", i)); floors["planning_sessions"] = _SKUS[i]["sku"]

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
    if isinstance(planung, dict) and "planning_sessions" in floors:
        advisories.append(
            "Fabric Planning bills per 30-day session (Planner 847, Stakeholder 168, Viewer 37 CU-h; "
            "Learn billing-fabric-plan, read 2026-09-29). The planning floor is DERIVED (average load "
            "over 730 h plus the 30 % buffer Learn suggests), not measured. Pausing or deleting the "
            "capacity bills the remaining CUs of all active sessions at once.")
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


# ---------------------------------------------------------------- I-21 Kapazitaet (29.09.2026)
# Ein Block, damit parallele Pakete ihn beim Zusammenfuehren nicht zerschneiden. Alles hier ist
# gegen learn.microsoft.com gelesen am 29.09.2026; was hergeleitet ist, sagt das Ergebnis selbst
# (``herkunft``), damit keine Rechnung als Messung in ein Kundendokument wandert.

#: Overage kostet den dreifachen Pay-as-you-go-Satz je CU-Stunde (``enterprise/capacity-overage-
#: overview``, „three times the pay-as-you-go rate").
OVERAGE_PREISFAKTOR = 3
#: Microsoft empfiehlt die Schwelle unter einem Drittel der Tages-CU-Stunden — dort kostet Overage
#: so viel wie die naechstgroessere SKU (dieselbe Seite, Abschnitt „Capacity overage thresholds").
OVERAGE_EMPFEHLUNG_NENNER = 3
#: Voreinstellung bei neuen F-Kapazitaeten: Overage **an**, Schwelle 25 % (``enterprise/enable-
#: capacity-overage``). Worauf sich die 25 % beziehen, nennt Learn nur als „extra daily capacity
#: consumption" — ANNAHME, ungeprueft: Anteil an den Tages-CU-Stunden der SKU.
OVERAGE_VOREINSTELLUNG_PCT = 25
#: Die Schwelle braucht Fabric-Kontingent in Hoehe von Schwelle/24 CU (dieselbe Seite:
#: „a 48 CU hour threshold adds 2 CUs to your quota").
OVERAGE_KONTINGENT_TEILER = 24


def tages_cu_stunden(sku: str) -> int | None:
    """CU-Stunden je Tag einer SKU (CU × 24) — die Groesse, an der Learn die Overage-Schwelle misst.

    Gegenprobe gegen die Learn-Tabelle (29.09.2026): F2 = 48, F8 = 192, F64 = 1 536,
    F8192 = 196 608 — alle vier folgen aus ``cu * 24`` ohne Sonderfall.
    """
    zeile = sku_ceilings(sku)
    return None if zeile is None else int(zeile["cu"]) * 24


def overage_kalkulation(sku: str, schwelle_cuh: float,
                        payg_preis_je_cu_stunde: float | None = None) -> dict[str, Any]:
    """Was eine Overage-Schwelle auf einer SKU bedeutet: Kontingent, Empfehlung, Tagesobergrenze.

    Die Kostenzeile ist **hergeleitet**, nicht gemessen: Schwelle × 3 × PAYG-Preis je CU-Stunde. Sie
    ist keine harte Grenze — Learn: Fabric prueft alle 5 Minuten, laufende Operationen und bis zu
    5 Minuten danach werden weiter zum Overage-Satz abgerechnet. Ohne Preis bleibt die Zeile leer,
    statt einen Listenpreis zu raten (Preise sind regional).
    """
    tages = tages_cu_stunden(sku)
    if tages is None:
        raise ValueError(f"unbekannte SKU {sku!r} — Overage gibt es nur auf F-SKUs")
    if schwelle_cuh < 0:
        raise ValueError("Overage-Schwelle darf nicht negativ sein")
    empfehlung = tages // OVERAGE_EMPFEHLUNG_NENNER
    kontingent = -(-int(round(schwelle_cuh)) // OVERAGE_KONTINGENT_TEILER)  # aufrunden
    kosten = (None if payg_preis_je_cu_stunde is None
              else round(schwelle_cuh * OVERAGE_PREISFAKTOR * payg_preis_je_cu_stunde, 2))
    return {
        "sku": sku.strip().upper(),
        "tages_cu_stunden": tages,
        "schwelle_cu_stunden": schwelle_cuh,
        "empfehlung_max_cu_stunden": empfehlung,
        "ueber_empfehlung": schwelle_cuh > empfehlung,
        "voreinstellung_cu_stunden": tages * OVERAGE_VOREINSTELLUNG_PCT // 100,
        "kontingent_bedarf_cu": kontingent,
        "max_kosten_je_tag": kosten,
        "herkunft": "hergeleitet",
        "hinweis": "Keine harte Kostengrenze: Pruefung alle 5 min, laufende Operationen und bis "
                   "zu 5 min danach werden weiter abgerechnet.",
    }


#: Fabric Planning: CU-Stunden je 30-Tage-Sitzung und Rolle (Learn ``iq/plan/resources/billing-
#: fabric-plan``, gelesen 29.09.2026). Eine Sitzung laeuft 730 Stunden und endet nicht vorzeitig.
PLANNING_CU_STUNDEN_JE_SITZUNG: dict[str, int] = {"planner": 847, "stakeholder": 168, "viewer": 37}
PLANNING_SITZUNG_STUNDEN = 730
#: Learn nennt „an estimated 30% capacity buffer" fuer die uebrigen Fabric-Lasten neben Planning.
PLANNING_PUFFER_PCT = 30


def planning_last(planner: int = 0, stakeholder: int = 0, viewer: int = 0) -> dict[str, Any]:
    """CU-Last aktiver Planning-Sitzungen je 30 Tage — Summe, Mittel und Mittel mit Puffer.

    Hergeleitet, nicht gemessen: die Sitzung wird laut Learn „periodically" abgerechnet; dass sie
    sich gleichmaessig ueber 730 h verteilt, ist ANNAHME, ungeprueft. Automatisierungsjobs (je
    erfolgreichem Job „2 CU" laut Learn, Einheit dort nicht naeher bestimmt) sind nicht enthalten.
    """
    anzahl = {"planner": planner, "stakeholder": stakeholder, "viewer": viewer}
    if any(v < 0 for v in anzahl.values()):
        raise ValueError("Sitzungszahlen duerfen nicht negativ sein")
    summe = sum(PLANNING_CU_STUNDEN_JE_SITZUNG[r] * n for r, n in anzahl.items())
    mittel = summe / PLANNING_SITZUNG_STUNDEN
    return {
        "sitzungen": anzahl,
        "cu_stunden_30_tage": summe,
        "mittlere_cu": round(mittel, 2),
        "mit_puffer_cu": round(mittel * (100 + PLANNING_PUFFER_PCT) / 100, 2),
        "herkunft": "hergeleitet",
    }
