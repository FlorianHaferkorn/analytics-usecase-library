# SCM KPIs — SCOR alignment & definition-drift audit

> **Standard:** [SCOR Digital Standard (ASCM)](https://scor.ascm.org/) — the industry-standard
> supply-chain metric hierarchy (Reliability RL / Responsiveness RS / Agility AG / Cost CO /
> Asset Management AM). **Method:** each governed SCM KPI is mapped to its nearest SCOR metric,
> with an explicit `alignment` (exact / partial / none) and a drift note — recorded per-KPI in
> `standard_ref` (schema `tooling/generator/schemas/kpi_definition.schema.json`). This is the
> first run of a repeatable per-domain program (finance→FIBO/IFRS, ESG→ESRS, HR→ISO-30414…).

## Headline findings

1. **OTIF is not SCOR "Perfect Order".** Our OTIF / service-level KPIs cover **2 of the 4**
   SCOR Perfect Order components (on-time RL.2.2 + in-full RL.2.1); they omit **Documentation
   Accuracy (RL.2.3)** and **Perfect Condition (RL.2.4)**. Keep them labelled *OTIF* (the common
   industry 2-component metric) — do **not** call them Perfect Order — or add the two missing
   components to earn the SCOR claim.
2. **On-time reference date is unpinned.** SCOR RL.2.2 measures to the **customer commit date**;
   our on-time definition doesn't state the reference date. Pin it to align (and to stop the
   requested-vs-commit-date debate with clients).
3. **In-full grain differs.** SCOR RL.2.1 is order-level; ours is delivery-level.
4. **Forecast metrics have no SCOR home.** Accuracy / bias / MAPE are Plan *enablers* in SCOR,
   not performance metrics — the correct external reference is the **IBF / APICS forecasting
   standards**. (A good example of "one standard per concept, not one standard for everything.")
5. **Duplicates surfaced by the mapping.** Three OTIF-formula KPIs (`KPI-SCM-007`,
   `ops.otif.pct`, `scm.service_level.pct`) and two DIO KPIs (`KPI-SCM-001`, `KPI-FIN-004`) are
   definitionally identical — consolidation candidates the standard mapping made obvious.

## Mapping table

| KPI | SCOR metric | Alignment | Drift note / recommendation |
|---|---|---|---|
| `KPI-SCM-001` | `AM.1.1` Cash-to-Cash Cycle Time — inventory-days component | **partial** | Maps to the inventory-days input of SCOR Cash-to-Cash Cycle Time (AM.1.1 = DSO + Inventory Days of Supply − DPO). Ours is COGS-based DIO. Duplicate of KPI-FIN-004 — consolidate. |
| `ops.otif.pct` | `RL.1.1` Perfect Order Fulfillment | **partial** | Same 2-of-4 gap as KPI-SCM-007. Also a duplicate formula of KPI-SCM-007 and scm.service_level.pct — consolidation candidate. |
| `scm.service_level.pct` | `RL.1.1` Perfect Order Fulfillment | **partial** | Formula is identical to OTIF (OTIF orders / total orders) → maps to SCOR Perfect Order (2-of-4). Duplicate of KPI-SCM-007 / ops.otif.pct — consolidate to one governed OTIF. |
| `KPI-SCM-022` | `AG` Agility — Value at Risk | **partial** | Loose link only: SCOR Agility (AG) measures adaptability and overall value-at-risk, not a supplier-risk composite score. Conceptual neighbour, not the same metric. |
| `KPI-SCM-010` | `CO.1.1` Total Supply Chain Management Cost | **partial** | Premium-freight / expedite is one cost component within SCOR CO.1.1 (Total SC Management Cost), not the whole metric. |
| `KPI-SCM-018` | `RL.2.1` Percentage of Orders Delivered In Full | **partial** | Grain differs: ours is delivery-level (in-full deliveries / total deliveries); SCOR RL.2.1 is order-level (% of orders delivered in full). Move to order grain to align. |
| `KPI-SCM-008` | `RL.2.2` Delivery Performance to Customer Commit Date | **partial** | Reference date is unspecified in our definition; SCOR RL.2.2 measures against the customer COMMIT date, not the requested/scheduled date. Pin the reference date to the commit date to align. |
| `KPI-SCM-007` | `RL.1.1` Perfect Order Fulfillment | **partial** | OTIF here = on-time AND in-full — 2 of SCOR Perfect Order's 4 components; omits Documentation Accuracy (RL.2.3) and Perfect Condition (RL.2.4). SCOR RL.1.1 is order-level and requires all four to pass. To claim SCOR Perfect Order, add the two missing components; otherwise label it OTIF, not Perfect Order. |
| `KPI-SCM-011` | `CO.1.1` Total Supply Chain Management Cost | **partial** | Service-failure penalties are a cost component within SCOR's Cost attribute (CO.1.1), not a named standalone SCOR metric. |
| `KPI-FIN-004` | `AM.1.1` Cash-to-Cash Cycle Time — inventory-days component | **partial** | Duplicate of KPI-SCM-001; both map to the SCOR inventory-days / Cash-to-Cash (AM.1.1) family. Consolidate to one DIO. |
| `KPI-SCM-003` | — | **none** | Excess/obsolete inventory value is an inventory-health practice concern, not a named SCOR performance metric (SCOR treats it under Asset Management practices). |
| `KPI-SCM-002` | `RL.1.1` Perfect Order Fulfillment (availability) | **none** | No direct SCOR L1–L3 metric. Stockout rate is the inverse of item availability/fill, which SCOR captures inside Perfect Order (RL) rather than as a standalone metric. |
| `ops.inventory.value.amount` | `AM.1.1` Asset Management — inventory value input | **none** | Inventory value is an input to SCOR Asset Management metrics (Cash-to-Cash inventory-days), not itself a named SCOR performance metric. |
| `KPI-SCM-005` | — | **none** | Forecast accuracy is a Plan-process ENABLER in SCOR, not a core RL/RS/AG/CO/AM performance metric. Better external references are the IBF / APICS forecasting standards (MAPE, bias, tracking signal) — a candidate standards domain of its own. |
| `KPI-SCM-006` | — | **none** | As KPI-SCM-005 — no SCOR metric home; IBF/APICS forecasting standards are the right external reference. |
| `KPI-SCM-017` | — | **none** | As KPI-SCM-005 — no SCOR metric home; MAPE is defined by IBF/APICS forecasting standards, not SCOR. |
| `KPI-SCM-009` | — | **none** | Lost-demand share is a Plan/service-loss diagnostic, not a named SCOR metric. |

**Alignment legend:** `exact` = same definition/formula/grain · `partial` = same concept, a
documented definitional difference · `none` = no SCOR equivalent (note points to the better-fitting
standard).

_Sources: SCOR Digital Standard, ASCM (scor.ascm.org); metric IDs verified against ASCM SCOR-DS
documentation. Sub-metric IDs asserted only where verified; component-level references use the
parent metric where a specific sub-ID was not confirmable from public sources._
