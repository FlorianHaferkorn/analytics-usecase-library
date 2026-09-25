<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/generator/generate_tool_configs.py -->

---
name: recommend-fabric-capacity
description: Recommend a Fabric capacity: SKU floor, reserved vs pay-as-you-go, region, and split. Use when sizing a capacity, answering reservation or pricing questions, filling platform.capacity_sku, or when a customer asks which F-SKU or region to buy.
version: "1.0.0"
---

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

4. **Choose the region.** Same discount everywhere; only the base rate differs.

5. **Choose the split.** One larger capacity or several smaller ones.

6. **Write the result to the IR** (`platform.capacity_sku`), or state the floor explicitly when the customer has not assigned a capacity yet.

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

## Procurement rules

**R1 — Reserve above 100 operating hours per week.** Break-even is 59.5 % runtime. In practice: seven-day operation needs only ~14 hours per day to justify a reservation; weekday-only operation would need ~20 hours per day. Weekend operation means reserve; weekday-only usually means pay-as-you-go.

**R2 — Do not pause production capacities; do pause dev and test.** Pausing saves real money on the compute meter, but Fabric is fully unavailable during the pause and **scheduled runs falling into the pause window are not caught up** (no documented catch-up). There is no built-in scheduler; it takes an Azure Automation runbook, roughly one day of work.

**R3 — Reserve the floor, never the forecast.** Consumption above the reservation runs at pay-as-you-go, costing only the forgone discount. Reserved CU that go unused expire hourly and cannot be carried forward. The risk is one-sided.

**R4 — Never commit longer than one year.** The three-year reservation costs exactly three times the one-year reservation; the hourly rate is identical. There is no volume discount for longer terms.

**R5 — Only discuss region below F16 if the customer raises it.** European regions differ by up to 13.6 % in base rate. On small capacities that is one to two thousand USD per year, less than the cost of deviating from a corporate standard region. At F64 it is around ten thousand USD, which is worth the discussion. Cross-region egress is 0.02 USD/GB and negligible at typical volumes; do **not** use it as an argument without doing the arithmetic first.

**R6 — Separate capacities only for chargeback or genuine isolation.** The Azure invoice breaks down per capacity resource, not per workspace: Fabric workspaces are not ARM resources and cannot carry tags. Customers who charge costs back to business units need separate capacities. Everyone else is better served by one larger capacity, because parallelism limits and burst budget apply per capacity. Workspace-level surge protection is a soft cap checked every five minutes, not a substitute for separation.

**R7 — Always cost storage separately.** OneLake storage is billed per GB, is **not** covered by the reservation, and keeps running while the capacity is paused. It never changes the reserved-vs-PAYG decision but is added on top in every scenario. Mirroring includes 1 TB free per CU, and the replication itself consumes no CU.

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

All figures verified against learn.microsoft.com and the Azure Retail Prices API on 2026-08-04: capacity reservations and discount mechanics, throttling and smoothing policy, SKU limits for semantic models and Direct Lake, region availability, pause and resume behaviour, mirroring cost, OneLake consumption.
