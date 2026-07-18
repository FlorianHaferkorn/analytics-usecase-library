# Aurora Synthetic Data Gaps — tables & columns to generate

**Purpose.** The four gap-closing use cases (HR-001, COM-005, FIN-003, SCM-004) are
spec-complete and validated (KPIs, standards, storyline, action codes all green), but their
KPIs are `hitl`/`planned` because the backing **Aurora synthetic data does not exist yet**.
This doc is the single, precise source for what to generate — *realistic but synthetic* — so
those KPIs compute and their reports render. It also records a pre-existing gap in **COM-001**.

**Method.** Each KPI's required source is recorded in its catalog entry
(`technical.calculation.reason`) and mirrored here as concrete table/column specs. Aurora gold
lives under `showcases/aurora_group/data/gold/`; generators are the `generate_*_gold.py` scripts
there. Grain keys follow the existing convention (`DateKey`, `OrgKey`, `ProductKey`, …).

Legend: 🟥 **new table** · 🟧 **new columns on an existing table** · 🟦 **new dimension**.

---

## COM-001 — Sales Performance vs Plan (pre-existing gap, the flagged example)

COM-001's page-2 evidence and its 30-second PVM waterfall bind a **price/volume/mix driver
dimension** that the semantic model defines (`dim_pvm_driver`, added this session) but which has
**no backing table in Aurora gold**. The measures resolve at model level, but there is nothing to
populate the driver axis from data.

- 🟦 **`dim_pvm_driver`** — MISSING in `gold/dims`. Columns: `PVMDriverKey`, `Driver`
  (`Price` | `Volume` | `Mix`), `Sort Order`, `Sign Convention`. A static 3-row bridge; it lets the
  waterfall decompose `Net Sales Δ vs Plan` into the three governed effects
  (`sales.pvm.price_effect` / `volume_effect` / `mix_effect`).
- Source columns already present in `fact_sales` (`Plan Quantity`, `List/Net Price Amount`,
  `Plan Sales Amount`, …) — no new fact columns needed; only the driver dimension + the bridge rows.

> This is the pattern for every gap below: the governed KPI/measure exists, the **table behind it
> does not** — synthesize the table, don't redefine the KPI.

---

## HR-001 — Workforce Performance & Retention (ISO 30414)

`fact_workforce_management` exists but is the **call-center capacity** table (Talk/Wrap/Overtime
minutes for XD-002) — it has no headcount, leavers, absence, cost or engagement. Net: a real HR
fact is missing.

- 🟥 **`fact_workforce`** — grain `DateKey × OrgKey × EmployeeSegmentKey` (monthly snapshot).
  Columns: `Headcount FTE`, `Voluntary Leavers`, `Involuntary Leavers`, `Hires`,
  `Absence Days`, `Scheduled Working Days`, `Workforce Cost Amount`.
  → feeds `people.attrition.pct`, `people.absence.pct`, `people.cost.per_fte.amount`, `people.headcount.fte`.
- 🟥 **`fact_engagement_survey`** — grain `DateKey × OrgKey × EmployeeSegmentKey` (quarterly).
  Columns: `Engagement Score` (0–100 or eNPS −100..+100), `Respondents`, `Invited`.
  → feeds `people.engagement.index`.
- 🟥 **`fact_recruiting`** — grain `DateKey × OrgKey × RoleKey`, one row per filled requisition.
  Columns: `Requisition Open Date`, `Filled Date`, `Positions Filled`.
  → feeds `people.timetofill.days`.
- 🟦 **`dim_employee_segment`** (`EmployeeSegmentKey`, `Segment`, `Function`, `Tenure Band`) and
  🟦 **`dim_role`** (`RoleKey`, `Role`, `Job Family`, `Level`).

**Realism:** voluntary attrition ~8–14 % p.a. with 2–3 hotspot segments elevated; engagement
inversely correlated with attrition (the governed driver); absence ~2–5 %; time-to-fill 30–70 days.

---

## COM-005 — Sales Pipeline & Conversion (convention)

No opportunity/pipeline table exists in Aurora — the whole forward-looking funnel is absent.

- 🟥 **`fact_pipeline`** — grain: one row per opportunity (`OpportunityID`), plus a stage-history
  variant if stage conversion is modelled over time. Columns: `OrgKey`, `SalesRepKey`, `StageKey`,
  `Create Date`, `Stage Entered Date`, `Close Date`, `Opportunity Value Amount`, `Won Flag`,
  `Lost Flag`, `Qualified Flag`.
  → feeds `sales.win_rate.pct`, `sales.conversion.pct`, `sales.sales_cycle.days`,
  `sales.velocity.amount`, `sales.pipeline.value.amount`.
- 🟥 **`fact_sales_target`** (or reuse `fact_sales_budget`) — `DateKey × OrgKey`,
  `Remaining Target Amount` → the denominator of `sales.pipeline.coverage.ratio`.
- 🟦 **`dim_sales_stage`** (`StageKey`, `Stage`, `Stage Order`, `Is Won`, `Is Lost`) and
  🟦 **`dim_salesrep`** (`SalesRepKey`, `Rep`, `Team`, `Region`).

**Realism:** coverage 2.0–3.5× (below the 3× rule in the segments the storyline flags); win rate
20–35 % with a weak-conversion mid-stage; cycle 45–120 days, lengthening in the target segment.

---

## FIN-003 — Earnings Performance vs Plan (IFRS / ESMA-APM)

`fact_finance` exists with `Net Sales / COGS / OpEx / Plan OpEx / EBIT / Net Income` — closest of
all four, but missing the EBITDA add-back and the full plan side, and it is `OrgKey`-grain (the UC
steers at **cost-center**).

- 🟧 **`fact_finance` new columns:** `D&A Amount` (depreciation & amortisation, to derive
  EBITDA = EBIT + D&A), `Plan Net Sales Amount`, `Plan COGS Amount`, `Plan EBITDA Amount`,
  and a `CostCenterKey`.
  → feeds `margin.ebitda.amount`, `margin.ebitda.pct`, `margin.ebitda.delta_pct.plan`
  (reused: `margin.gm.pct`, `cost.opex.vs_plan.pct`, `sales.net_sales.delta_pct.plan`).
- 🟦 **`dim_cost_center`** (`CostCenterKey`, `Cost Center`, `Entity`, `Business Unit`,
  `Account Group`).

**Realism:** EBITDA margin ~1–3 pp below plan, with the gap **opex-led** (opex above plan) while
gross margin holds — matching the governed storyline; a few cost centres carry most of the overrun.

---

## SCM-004 — Procurement & Supplier Performance (SCOR Source + convention)

`fact_procurement` exists (`Procurement Amount`, `Savings Amount`, `Vendor Count`, `PO Count`) but
lacks target, contract-compliance, price-variance and inbound-delivery detail.

- 🟧 **`fact_procurement` new columns:** `Savings Target Amount`, `On-Contract Amount`,
  `Addressable Amount`, `Baseline Price Amount`, `Actual Price Amount`, `Quantity`, `CategoryKey`.
  → feeds `procurement.savings.realized.pct`, `procurement.oncontract.pct`, `procurement.ppv.pct`,
  `procurement.spend.managed.amount`.
- 🟥 **`fact_procurement_receipts`** — grain: one row per inbound receipt. Columns: `DateKey`,
  `VendorKey`, `CategoryKey`, `Promise Date`, `Receipt Date`, `On-Time Flag`.
  → feeds `procurement.supplier.otd.pct`.
- 🟦 **`dim_category`** (`CategoryKey`, `Category`, `Category Group`) and
  🟦 **`dim_supplier`** (from existing `VendorKey`: `Supplier`, `Region`, `Tier`).
  Reused: `scm.supplier_risk.score` ← existing `fact_supplier_risk`.

**Realism:** realised savings 40–80 % of target; on-contract spend ~70–85 % with 2–3 leaking
categories; PPV climbing in those same categories (the governed cross-signal); supplier OTD 88–96 %.

---

## Consolidated generation checklist (for the Aurora synthetic generator)

| # | Artifact | Type | Serves |
|---|----------|------|--------|
| 1 | `dim_pvm_driver` (+ 3 bridge rows) | 🟦 dim | COM-001 (existing report) |
| 2 | `fact_workforce` | 🟥 fact | HR-001 |
| 3 | `fact_engagement_survey` | 🟥 fact | HR-001 |
| 4 | `fact_recruiting` | 🟥 fact | HR-001 |
| 5 | `dim_employee_segment`, `dim_role` | 🟦 dim | HR-001 |
| 6 | `fact_pipeline` | 🟥 fact | COM-005 |
| 7 | `fact_sales_target` (or extend `fact_sales_budget`) | 🟥/🟧 | COM-005 |
| 8 | `dim_sales_stage`, `dim_salesrep` | 🟦 dim | COM-005 |
| 9 | `fact_finance` + `D&A`, plan cols, `CostCenterKey` | 🟧 cols | FIN-003 |
| 10 | `dim_cost_center` | 🟦 dim | FIN-003 |
| 11 | `fact_procurement` + target/contract/price/`CategoryKey` | 🟧 cols | SCM-004 |
| 12 | `fact_procurement_receipts` | 🟥 fact | SCM-004 |
| 13 | `dim_category`, `dim_supplier` | 🟦 dim | SCM-004 |

**After generation** (Desktop/Fabric-gated, per `CLAUDE_CLI_PBI_DESKTOP_TASKS.md`): add the DAX
measures to each domain `SemanticModel`, remove the 19 `planned.yaml` entries as each lands,
generate the four `.Report` folders (they then drop out of the report-pending exemption in
`test_dist_report_coverage.py`), and the KPIs move from UNCOMPUTED to computed/value-verified.
