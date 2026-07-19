# Aurora Synthetic Data Gaps — tables & columns to generate

**Purpose.** The four gap-closing use cases (HR-001, COM-005, FIN-003, SCM-004) are
spec-complete and validated (KPIs, standards, storyline, action codes all green). This doc is
the single, precise source for the backing Aurora data — *realistic but synthetic* — so those
KPIs compute and their reports render. It also records a pre-existing gap in **COM-001**.

> **STATUS — data generated ✅ (2026-07-19).** All 13 checklist artefacts below are now written
> to `showcases/aurora_group/data/gold/` by
> [`generate_gapfill_gold.py`](../../showcases/aurora_group/data/gold/generate_gapfill_gold.py),
> realistic and consistent with the existing gold (same OrgKeys, DateKey convention, growth
> model, seeded RandomState; existing `fact_finance`/`fact_procurement` columns byte-identical,
> new columns appended). Storyline realism verified in-data: FIN-003 EBITDA margin 12.2 % actual
> vs 13.6 % plan (−1.4 pp, opex-led); SCM-004 realised savings 58 % of target · on-contract 80 % ·
> supplier OTD 92 %; HR-001 voluntary attrition 13.3 % p.a. with Sales/Retail/Logistics hotspots ·
> absence 3.5 % · time-to-fill 44 d; COM-005 win rate 28.8 % · coverage 2.1–3.4× per country.
>
> The **tool-agnostic KPI measures** are wired too: 17 of the 19 KPIs now carry real neutral-DSL
> `calculation` blocks (incl. the plan/target maths — EBITDA-margin-vs-plan as a Δ of ratios,
> pipeline coverage as open-qualified ÷ remaining target, PPV as actual-vs-baseline price,
> annualised attrition, supplier-OTD rate). The 2 composites (`sales.conversion.pct` per-stage,
> `sales.velocity.amount`) stay `hitl` with lineage pointing at the real columns — they need a
> multi-input DAX assembly beyond the single-op DSL. **Still CLI-gated** (below): the TMDL/DAX
> named measures and the four `.Report` folders — see `CLAUDE_CLI_PBI_DESKTOP_TASKS.md`.
>
> **Ontology registered ✅ (2026-07-19).** Verified end-to-end: all 26 fact→dim FK relationships
> resolve (0 orphans/nulls), formatting/types/ranges clean (EBITDA = EBIT + D&A holds), every KPI
> lineage column exists. The new tables/dims/columns are now declared in the governed domain data
> contracts (`core/data_contracts/domains/{people,commercial_sales,finance,supply_chain}.yaml`) so
> the ontology reflects reality — contract validator green, H8 AI-readiness green.
>
> **People stub facts — keep, do not retire.** `fact_hr`/`fact_it`/`fact_survey` have no physical
> Aurora table, but they are **not** dead: they still back two other governed KPIs whose data is
> genuinely absent — `people.digital_adoption.pct` (`fact_it[Digital Users]`, `fact_hr[Headcount]`)
> and `people.attrition_risk.pct` (`fact_hr[Attrition Risk %]`), plus a `BLANK()` placeholder in the
> Experience model. `fact_workforce`/`fact_engagement_survey`/`fact_recruiting` supersede only the
> **retention/headcount/absence/cost** slice, not Digital Users or the attrition-risk score. Closing
> those two would be a *new* data gap (a `fact_it`-style adoption fact + an attrition-risk model
> output) — out of scope here, tracked as future work.

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

- 🟦 **`dim_pvm_driver`** — now written to `gold/dimensions`. Columns: `PVMDriverKey`, `Driver`
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
  🟦 **`dim_vendor`** (from existing `VendorKey`: `Vendor`, `Region`, `Tier`).
  Named `dim_vendor` (not `dim_supplier`) on purpose: the finance/risk supplier master
  (`dim_supplier` / `SupplierKey`, 4 rows in `fact_supplier_risk`) is a **different**
  population and key space — see the conformance note below.
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
| 13 | `dim_category`, `dim_vendor` | 🟦 dim | SCM-004 |

All 13 are **written** (status banner above). Regenerate anytime with
`python3 showcases/aurora_group/data/gold/generate_gapfill_gold.py` (deterministic).

**Still to do — CLI/Desktop-gated** (per `CLAUDE_CLI_PBI_DESKTOP_TASKS.md`, and because the base
stays viz-tool-agnostic): add the DAX named measures to each domain `SemanticModel` (the neutral
`calculation` blocks in the catalog are the source — synthesise via `tooling/superversion`),
remove the 19 `planned.yaml` entries as each measure lands, generate the four `.Report` folders
(they then drop out of the report-pending exemption in `test_dist_report_coverage.py`), and flip
each UC's `readiness.data_availability` off `not_available`. Only then do the KPIs move from
UNCOMPUTED to computed/value-verified in a live model.

---

## Data sourcing reality — how "fetchable" is each fact, really?

The gold tables read as easy because they are the **post-ETL gold layer**: already conformed,
keyed, and pre-aggregated. Raw source fetch is messier and varies a lot by domain. This matters
when scoping a real client: don't imply a metric is a simple export when it needs a system the
client may not have.

| Fact | Real-world fetch | Typical source system |
|---|---|---|
| `fact_finance` (+plan), `fact_sales_target` | **Easy** | GL/ERP + FP&A budget — every finance function has this |
| `fact_pipeline` | **Easy — *if B2B*** | CRM opportunity object (Salesforce/HubSpot/Dynamics) |
| `fact_workforce`, `fact_recruiting`, `fact_engagement_survey` | **Moderate** | HRIS + ATS + survey tool; needs PII governance |
| `fact_procurement_receipts` (OTD) | **Moderate** | ERP goods-receipt vs promise date (SAP MM) |
| `fact_procurement` savings / on-contract / PPV | **Hard** | Needs mature spend analytics: spend taxonomy, contract register, standard prices — the fields companies most struggle to source |

Two realism tensions to state to a client rather than paper over:
- **Aurora is a retail group (495 stores)** yet COM-005 models a **B2B sales pipeline** — realistic
  only for a wholesale / key-account arm, not pure B2C retail.
- **Procurement savings / on-contract / PPV** are exactly the fields real companies *lack* cleanly;
  the synthetic data makes them look readily available. Frame them as "assumes a category-management
  system," not "simple ERP export."

## Known modelling caveats (deliberate simplifications, documented not hidden)

1. **`fact_workforce` is multi-grain on a parent-child hierarchy** — rows at `Country`, `Region` and
   `Group` levels of `dim_org` (a real ParentOrgKey tree). A defensible "reporting-unit snapshot",
   but additive measures (`Headcount FTE`) need level-awareness; a cleaner design snapshots at one
   (leaf) grain and rolls up. *Production-clean follow-up if wanted.*
2. **`fact_finance.CostCenterKey` is degenerate** — exactly 1 cost centre per `OrgKey`, so it is
   fully derivable from `OrgKey`. Harmless, but strictly it belongs as a `dim_org` attribute / a
   role-playing lookup rather than a fact column.
3. **`procurement.ppv.pct` is approximate** — `fact_procurement` is `dc_vendor_month`, so
   `Actual/Baseline Price` is a **blended monthly** price and PPV = `Σactual − Σbaseline` over blends.
   True PPV is per-PO-line `(actual_unit − standard_unit) × qty`; rebuilding to PO-line grain would
   ~50× the row count. Flagged as directional, not auditable.
4. **`dim_vendor` vs `dim_supplier` are not conformed** — procurement vendors (`VendorKey`, 40) and
   the finance/risk supplier master (`SupplierKey`, 4) are different populations & key spaces. Named
   distinctly to remove the false-conformance collision; a true single supplier/vendor master is a
   future conformance task.
