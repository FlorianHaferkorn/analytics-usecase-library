# Recommend Fabric Capacity

Derive a Fabric capacity recommendation for a customer: SKU floor, procurement model, region, and split. Two distinct questions that are often conflated — **sizing** (which SKU is technically sufficient) and **procurement** (reserved vs pay-as-you-go, which region, one capacity or several).

Fills `platform.capacity_sku` in the architecture blueprint IR, or states a recommended FLOOR when no SKU is assigned.

## Workflow

1. **Fetch current prices — never quote from memory.**
   ```bash
   curl -s "https://prices.azure.com/api/retail/prices?\$filter=serviceName%20eq%20'Microsoft%20Fabric'%20and%20armRegionName%20eq%20'westeurope'"
   ```
   - PAYG per CU/hour: meter `Power BI Capacity Usage CU`, `type: Consumption`. All ~59 CU meters of a capacity carry the same base rate; any of them works.
   - Reserved: meter `Fabric Capacity CU`, `type: Reservation`, `reservationTerm: 1 Year`.
   - **Trap:** the reservation `retailPrice` is the **total for the whole term**, not an hourly rate, despite `unitOfMeasure: "1 Hour"`. Divide by 8760 to compare. Proof: the 3-year price is exactly 3× the 1-year price.
   - Add `&currencyCode=EUR` when quoting in EUR; do not convert yourself.

2. **Size the SKU (technical floor).** Drive this from model size, Direct Lake guardrails and viewer licensing, not from expected load.

3. **Choose the procurement model.** Break-even is 59.5 % runtime ≈ **100 hours per week**, identical across SKUs and regions because the discount is proportional.

4. **Choose the region.** Same discount everywhere; only the base rate differs. Then check the region against the functions the customer needs: `capacity.recommend(bp, features={...})` returns `region_features` from the mirrored Meridian table (`stack_capabilities`, Learn `admin/region-availability`, data as of 2026-10-01). As of that date: Ontology is missing only in South Central US; Fabric Apps are missing in North Europe, Poland Central, Spain Central, Switzerland West and UK West, among others, but available in Germany West Central and West Europe; Database Hub is missing in West and North Europe. Never quote a region from memory — the table changed between 29.09. and 01.10.2026.

5. **Choose the split.** Production and non-production always separate (R6, D-596); within each, one larger capacity or several smaller ones.

6. **Ask the overage question** (see *Capacity overage*): off, or threshold X CU hours per rolling 24 h. Never leave the Microsoft default unmentioned.

7. **Write the result to the IR** (`platform.capacity_sku`), or state the floor explicitly when the customer has not assigned a capacity yet.

## Sizing: what changes between SKUs

| Limit | F4 | F8 | F16 | F64 |
|---|---|---|---|---|
| Max memory per semantic model | 3 GB | 3 GB | 5 GB | 25 GB |
| Direct Lake rows per table | 300 M | 300 M | 300 M | 1500 M |
| Direct Lake model size (OneLake) | 10 GB | 10 GB | 20 GB | 100 GB |
| Spark vCores, baseline / burst | 8 / 24 | 16 / 48 | 32 / 96 | 128 / 384 |
| Parallel semantic model refreshes | 2 | 5 | 10 | 40 |
| Parallel DirectQuery connections | 5 | 10 | 20 | 80 |
| Free-licence viewers | no | no | no | **yes** |

Two conclusions that come up in almost every conversation:

- **F4 to F8 does not raise any model-size limit.** Memory per model, Direct Lake rows and model size are identical. The first jump is F16. Anyone moving to F8 out of model-size concern gains nothing; what they gain is parallelism and burst headroom.
- **F64 is a licensing threshold, not a performance one.** Below F64 every viewer needs a Pro licence. With more than roughly 30 to 40 viewers this usually decides the SKU on its own.
- **Copilot and data agents start at F2, not F64.** Any paid capacity from F2 (or P1) runs Copilot in Fabric and Power BI; trial capacities do not. A Fabric Copilot capacity (at least F2, home region only) can bill all Copilot use of assigned users, including Pro/PPU workspaces and Power BI Desktop. `recommend()` returns this under `copilot` (Learn `fabric/fundamentals/copilot-enable-fabric` and `fabric/enterprise/fabric-copilot-capacity`, read 2026-10-07; ALUCA D-686, SIG-2609-010).

## Procurement rules

**R1 — Reserve above 100 operating hours per week.** Break-even is 59.5 % runtime. In practice: seven-day operation needs only ~14 hours per day to justify a reservation; weekday-only operation would need ~20 hours per day. Weekend operation means reserve; weekday-only usually means pay-as-you-go.

**R2 — Do not pause production capacities; do pause dev and test.** Pausing saves real money on the compute meter, but Fabric is fully unavailable during the pause and **scheduled runs falling into the pause window are not caught up** (no documented catch-up). There is no built-in scheduler; it takes an Azure Automation runbook, roughly one day of work.

**R3 — Reserve the floor, never the forecast.** Consumption above the reservation runs at pay-as-you-go, costing only the forgone discount. Reserved CU that go unused expire hourly and cannot be carried forward. The risk is one-sided.

**R4 — Never commit longer than one year.** The three-year reservation costs exactly three times the one-year reservation; the hourly rate is identical. There is no volume discount for longer terms.

**R5 — Only discuss region below F16 if the customer raises it.** European regions differ by up to 13.6 % in base rate. On small capacities that is one to two thousand USD per year, less than the cost of deviating from a corporate standard region. At F64 it is around ten thousand USD, which is worth the discussion. Cross-region egress is 0.02 USD/GB and negligible at typical volumes; do **not** use it as an argument without doing the arithmetic first.

**R6 — Production and non-production on separate capacities; beyond that, separate only for chargeback.** Smoothing and throttling act per capacity, so development and test load on a shared capacity throttles production. Microsoft recommends a capacity per environment (Learn `enterprise/capacity-planning-*` and the CI/CD best-practice guide, read 2026-09-29); D-596 (30.09.2026) adopts the middle way: **one production and one non-production capacity**, dev and test consolidated on the non-production one, which can be paused and sized small (its price is an extra line, quoted from current prices only). Within each stage group the chargeback rule decides: the Azure invoice breaks down per capacity resource, not per workspace (Fabric workspaces are not ARM resources and cannot carry tags), so customers who charge costs back to business units need a capacity per unit; everyone else keeps one capacity per stage group, because parallelism limits and burst budget apply per capacity. A dedicated capacity per Tier-1 workload (D-596 option c) is an offer, surfaced for workspaces with `surge_class = mission_critical`, never a default. Workspace-level surge protection is a soft cap checked every five minutes, not a substitute for separation. In the blueprint, `platform.capacities[].stages` assigns a capacity to stages; `split()` in `capacity.py` returns `stage_groups`, `per_group` and `tier1_option`. In the deployment configuration, `infrastructure.json` names the non-production capacity and `infrastructure.prd.json` overrides it with the production one.

**R7 — Always cost storage separately.** OneLake storage is billed per GB, is **not** covered by the reservation, and keeps running while the capacity is paused. It never changes the reserved-vs-PAYG decision but is added on top in every scenario. Mirroring includes 1 TB free per CU, and the replication itself consumes no CU.

## Capacity overage (GA Sep 2026)

Learn `enterprise/capacity-overage-overview` and `enable-capacity-overage`, read 2026-09-29:

- **On by default** for every newly created F capacity; default threshold **25 %** of the daily CU hours (slider in 5 % steps or absolute CU hours). Only F SKUs.
- Only usage that would otherwise be throttled is billed, on a separate meter at **3× the PAYG rate**. No standing charge.
- The threshold is a **rolling 24-hour value in CU hours, not a hard cap**: evaluated every 5 minutes, running operations continue, so charges can exceed it.
- Quota needed = threshold / 24 CU (48 CU h → 2 CU).
- Daily CU hours = CU × 24 (F2 48, F8 192, F64 1,536). Learn: keep the threshold **below one third** of that; above it, scaling up costs about the same.

**R8 — Overage is a customer decision, not a default.** Ask “overage off, or threshold X?” in every sizing conversation. Quote the derived ceiling: maximum overage cost per day ≈ threshold × 3 × PAYG per CU hour — derived, not measured, and a lower bound of the worst case because of the 5-minute evaluation. `tooling/superversion/capacity.py` (`overage_profile`) computes it; `recommend()` returns the open question in `customer_questions`; `internal/proposal_costing` prints it in the quote.

## Resizing a running capacity (scale up, split, scale down)

Learn `enterprise/capacity-planning-manage-capacity-growth-governance`, read 2026-10-01. Use these after go-live, from the Capacity Metrics app, not at initial sizing:

- **80 % — scale up or split.** A capacity that runs consistently above ~80 % at peak times gets split (a workload moves to its own capacity) or upgraded. If peak usage rises steadily (Learn's example: 60 % → 75 % → 90 %), move to the next SKU **before** full utilization. Scaling up always **doubles** the SKU.
- **30 % — consolidate or scale down.** Peak usage consistently below 30 % means consolidate workloads onto it or scale down, **provided the SLAs still hold**.
- **Size by the measured 30-second peak.** On a trial or pay-as-you-go capacity, read the highest 30-second timepoint in the Capacity Metrics app; a SKU offers CU × 30 CU-seconds per timepoint. `peak_floor(peak_cu_seconds)` in `capacity.py` returns the smallest SKU whose budget covers the peak at 80 % (`recommend(..., measured={"peak_cu_seconds": n})` raises the floor and names the reason). The value is a measurement passed alongside the blueprint, not a blueprint field.
- **Scale-down check (formula).** Background operations are smoothed over 24 hours, so judge the smoothed usage, not the peak of a single job. Usage at the target size = current usage × CU current / CU target; it must stay at or below the 80 % threshold:

  `u_current ≤ 0.80 × CU_target / CU_current`

  Halving the SKU (F128 → F64) therefore needs u_current **< 40 %** — the example on the Learn page. The general form is derived from that example, not stated by Learn.
- **Reservation plus pay-as-you-go for surges.** Reserve the base and add a pay-as-you-go capacity for peaks (Learn: F64 reserved, F128 on Mondays by adding a PAYG F64); if the extra capacity is needed **more than four days a week**, reserving it is better value. Four days of 24 h are 96 h per week — consistent with R1's ~100 h break-even (derived, not stated by Learn). `surge_procurement(extra_sku, days_per_week)` in `capacity.py` applies the four-day rule; `recommend(..., measured={"surge": {"extra_sku": "F64", "days_per_week": 1}})` adds it under `procurement.surge` (Plan I-21 W5.3, 01.10.2026).
- **Optimize before scaling**, and avoid frequent resizes: running operations can be delayed; schedule resizes for low-activity periods.

## Fabric Planning sessions

Learn `iq/plan/resources/billing-fabric-plan`, read 2026-09-29: a session lasts 30 days (730 h), cannot be ended early and is counted per tenant + user + capacity. It consumes CU of the capacity: **Planner 847, Stakeholder 168, Viewer 37 CU hours** per session. Keep an estimated **30 % buffer** for the other workloads a planning deployment uses. Automation jobs are billed per successful job (“2 CU”, time unit not stated — do not quote a number). Pausing or deleting the capacity bills the remaining session CU at once. `planning_load()` in `capacity.py` returns load and share of a SKU. Since D-595 (30.09.2026) planning is a blueprint option (`platform.planning`); `recommend()` computes the load from `platform.planning.sessions` and turns missing role counts into a customer question. Plan sessions on only one stage group: a user working on both capacities has two sessions. Release status read 2026-09-30: Learn lists Plan as generally available since July 2026 while the IQ workload is still marked preview — state both in an offer.

## Guardrails

- Never quote a price from memory or from an older conversation. Fetch it.
- When `platform.capacity_sku` is absent, state a recommended **floor** with its reason. Do not silently assume a SKU.
- Reservation and pausing are mutually exclusive: the discount is settled hourly and is lost for paused hours.
- Pausing settles accumulated smoothed usage immediately. That is a pulled-forward charge, not an extra one, but it shows as a spike.
- Do not mix storage into the reserved-vs-PAYG comparison; it cancels out.
- Scaling a capacity is never blocked by a reservation. Exchanges are free and unlimited, but the new reservation must be at least equal in commitment and restarts the term.
- Microsoft has announced networking billing for Fabric with at least 90 days' notice, no price and no date. Treat cross-region setups as carrying an unquantified future cost, and say so rather than inventing a number.

## Reference values

Fetched 2026-08-04, USD, for plausibility only — re-fetch before quoting:

| Region | PAYG per CU/hour | Reservation 1 yr per CU/year | Discount |
|---|---|---|---|
| West Europe | 0.22 | 1,146 | 40.5 % |
| Germany West Central | 0.22 | 1,146 | 40.5 % |
| North Europe | 0.19 | 990 | 40.5 % |
| Sweden Central | 0.19 | 990 | 40.5 % |

Germany West Central carries **no premium** over West Europe. Sweden Central lacks BCDR by default for Power BI; prefer North Europe at the same rate.

## Key paths

- IR field: `tooling/generator/schemas/architecture_blueprint.schema.json` → `platform.capacity_sku`
- Fabric architecture target: `tooling/superversion/arch_targets/`
- Provisioning: `products/fabric/orchestrator/orchestrator.py`

## Sources

Overage and Fabric Planning figures verified against learn.microsoft.com on 2026-09-29 (pages named in their sections). Resizing thresholds (80 %/30 %, 24-hour smoothing example F128 < 40 % → F64, four-day rule) read on learn.microsoft.com on 2026-10-01 (`enterprise/capacity-planning-manage-capacity-growth-governance`). All other figures verified against learn.microsoft.com and the Azure Retail Prices API on 2026-08-04: capacity reservations and discount mechanics, throttling and smoothing policy, SKU limits for semantic models and Direct Lake, region availability, pause and resume behaviour, mirroring cost, OneLake consumption.
