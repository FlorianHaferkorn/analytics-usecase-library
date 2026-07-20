# ALUCA Report Design & Storytelling Specification

> **Provenance.** `generated_by: powerbi-report-design` · `contract_version: 1` · renderer-agnostic (Power BI / Web / PDF).
> **Scope.** A per-use-case design **and storytelling** brief for all 17 governed reports. It decides *what each report should look like and why*; it does **not** write PBIR (that is `powerbi-report-authoring`).
> **Alignment.** This is the human-readable **K1 (boutique bar) → K2 (intent/design-spec)** layer for the storytelling axis of [`KONZEPT_REPORT_QUALITAET.md`](../../../../../KONZEPT_REPORT_QUALITAET.md). It **operationalises**, and does not replace, the existing authorities:
> [`Storytelling_Principles.md`](../../../../../core/templates/page_templates/Storytelling_Principles.md) ·
> [`Layout_Grid_System.md`](../../../../../core/templates/page_templates/governance/Layout_Grid_System.md) ·
> [`Color_Semantics_Formatting.md`](../../../../../core/templates/page_templates/governance/Color_Semantics_Formatting.md) ·
> [`Boutique_Craft_Rubric.md`](../../../../../core/templates/page_templates/governance/Boutique_Craft_Rubric.md) ·
> [`Page_Spec_3_30_300.md`](../../../../../core/templates/page_templates/Page_Spec_3_30_300.md) ·
> [`Visual_Whitelist.md`](../../../../../core/templates/page_templates/governance/Visual_Whitelist.md).
>
> The per-report thesis and per-visual sentences below are the **grounded** form of the governed
> `ux_layout_rules` (`big_idea` / `message` / `so_what`) already in each `UseCase_Bracket.yaml` — closing
> the concept's diagnosed gap ("storytelling is templated, not grounded") and the reference report's
> open **BC-NARR-01** knock-out (titles are labels, not conclusions).

---

## Part A — Shared design system

### A.1 Design identity

- **Tone — *Boutique controlling brief*:** IBCS / ISO 24896-disciplined, editorial, calm-confident. It argues a thesis; it does not merely display numbers.
- **Signature — the recurring move on every report:** a **Big-Idea header band** (Zone-0 message) at the top of each page, and a **variance anchor** (PVM/vs-plan waterfall or a vs-target bridge) as the 30-second centre of gravity. Statement titles throughout, one highlight colour per page, direct labels over legends, target reference lines.

### A.2 The storytelling contract (the governing rule)

**Every report tells one story. Every visual has one purpose and contributes one sentence to that story.**

| Level | Field | Rule |
|---|---|---|
| Report | **`report_thesis`** (= governed `big_idea`) | One sentence the whole report argues — a *claim with a consequence*, not a status line. Passes the 5-second **thesis test**. |
| Visual | **`purpose`** | The single analytical question the visual answers. If two visuals answer the same question, one is cut ("no redundant charts"). |
| Visual | **`statement_title`** (= governed `message`) | The visual's *conclusion*, rendered as its title — never a label. This is the BC-NARR-01 fix. |
| Visual | **`story_sentence`** (= governed `so_what`) | The clause this visual adds to the report's argument. |

The `story_sentence`s must **chain** the repo's storytelling logic across the report:

> **Signal** (KPI band: *is it on track?*) → **Driver** (trend: *is the move durable?*) → **Cause** (bridge/ranking: *what moved it, and where?*) → **Consequence** (matrix: *where exactly to intervene?*) → **Decision** (ActionPanel: *what to do, by whom, expected impact?*).

A report passes the storytelling axis when its visuals' `story_sentence`s, read top-to-bottom, form that chain and land on an owned decision.

### A.3 Statement-title rule (primary upgrade — BC-NARR-01)

Today every page is titled with a **label** — *"Commercial Summary & Insights"*, *"Finance Execution"*. Those are removed. Each page's rendered title becomes a **condensed statement of its `big_idea`**; each visual's title becomes its `message`. Rules:

- A title states a **finding + its direction/consequence** ("Availability is the component pulling OEE below target"), not a topic ("OEE Breakdown").
- The page-level statement is the report thesis in ≤ ~12 words; the strategic KPI and its value live in the hero card beneath it, not in the title.
- No visual ships with a database field name on a title, axis, legend, or header (set human display names; format rates as `0.0%`, not `0.53`).

### A.4 Page model & archetype map

Two pages per report (repo 3-30-300). Page-type (T1–T4, already governed) maps to the design archetype and to a `powerbi-report-design` variant:

| Governed page_type | Page role | Archetype | Overview intent |
|---|---|---|---|
| **T1 Strategic Overview** | Overview "Pulse" | Executive Summary | Portfolio health at a glance; "is it on track?" |
| **T2 Tactical Variance** | Overview "Pulse" | Analytical (Driver-Bridge) | Variance vs plan; "why are we off?" |
| **T3 Operational Monitoring** | Overview "Pulse" | Operational Monitor | Exception queue; "what's breaking now?" |
| **T4 Prescriptive Recommendation** | Detail "Action Matrix" | Narrative + ActionPanel | Evidence → owned next step |

- **Overview — "The Pulse" (3–30 s):** `KPI_Cards` band (3 s signal) → `Main_1` trend (30 s) → `Main_2` variance/bridge (30 s) → `Main_3` driver/ranking (30 s). No actions here — signal and explanation only.
- **Detail — "The Action Matrix" (300 s):** `Smart_Narrative` (context sentence) → `Detail_Matrix` (worst-first Top-N evidence at the use case's `evidence_grain`) → `ActionPanel` (from the use case's action codes). Configured as the drill-through target of the Overview.

### A.5 Chart & colour guardrails (whitelist + the 5 knock-outs)

Only whitelist visuals: `kpi_card · trend_line · bar_chart · column_chart · waterfall · matrix · ranking · smart_narrative · slicer`. The five knock-outs are hard constraints on every brief below:

| Knock-out | Rule applied in every brief |
|---|---|
| **BC-CHART-01** | Never mix scale families on one axis. Amounts (€) and rates (%) go on **separate visuals or dual, labelled axes** — never one shared axis. |
| **BC-CHART-10** | Every `Detail_Matrix` is **sorted worst-first** and curated to **Top-N** (not the full table). |
| **BC-NARR-01** | Every page and visual title is a **statement** (A.3). |
| **BC-BRAND-01** | One **composed** cross-report theme; never the renderer default. |
| **BC-COLOR-02** | Colour is **semantic only** (actual vs plan/LY, favourable/unfavourable per IBCS); **one** highlight per page; no decorative hues to separate equal-rank categories. |

Comparison encodings follow the governed `comparison` field (`vs_plan` / `vs_target` / `vs_py`): actual as solid, the comparison base as an outline/reference line, variance as a signed, colour-coded delta.

---

## Part B — Per-use-case design & storytelling briefs

Each brief gives the **report thesis**, the two pages with their **statement titles**, and each visual's **purpose · statement_title · story_sentence**, grounded in the use case's governed strategic + influencing KPIs and action codes. The `story_sentence` column, read down each page, is the report's argument.

---

### COM-001 · Sales Performance vs Plan & LY — Commercial · strategic KPI `margin.gm.pct`

**Report thesis:** *Net Sales is above plan but GM% is below target — adverse mix in DACH is the primary driver, and the lead is narrowing, so act on price/mix now, not volume.*

**Overview — "The Pulse"** · T2 Tactical Variance / Driver-Bridge · **title:** *"Ahead on sales, behind on margin — mix is the reason"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — GM % (hero, +Δplan/+ΔLY), Net Sales, COGS | Signal: status vs target | *"GM% is below target while Net Sales beats plan"* | We're winning the top line and losing the margin line. |
| `trend_line` — Net Sales vs Plan vs LY (ref-line) | Is the beat durable? | *"Net Sales leads plan and prior year, but the lead has narrowed recently"* | The cushion is real but shrinking. |
| `waterfall` (PVM, vs_plan) — Price / Volume / Mix bridge | What moved the gap? | *"Price and mix, not volume, explain the swing between plan and actual"* | It's a commercial-mix problem, not a demand shortfall. |
| `bar_chart` — Net Sales Δ vs plan by Region (one highlight) | Broad or concentrated? | *"Plan gaps concentrate in a handful of regions, not evenly"* | Targeted regional action beats a blanket push. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: invoice_line` · **title:** *"DACH and CEE own 80% of the plan gap"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context for the slice | *(dynamic)* *"In {Region}, mix cost {x} and price added {y} vs plan"* | Restates the thesis for the filtered view. |
| `matrix` — invoice-lines worst-first Top-20; Net Sales, GM%, Δvs plan (data bars + deviation colour), P/V/M | Where exactly to intervene | *"Six SKUs drive most of the plan-margin gap"* | Names the accounts to act on. |
| `ActionPanel` — `C-M2.1` margin defense, `C-S1.1/C-S1.2` sales | Decision | *"Defend list-to-net on the two eroding categories"* | The report ends on an owned next step. |

---

### COM-002 · Margin & Price Performance — Commercial · strategic KPI `margin.gm.pct`

**Report thesis:** *Gross Margin is under pressure — price concessions and adverse SKU mix are compressing contribution; price discipline and mix are the levers, not volume.* *(Reference exemplar — this brief closes its BC-NARR-01 gap.)*

**Overview — "The Pulse"** · T2 Tactical Variance / Driver-Bridge · **title:** *"Margin is eroding on price and mix, not demand"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — GM% (hero), GM% vs plan, Price realization %, GM amount | Signal | *"GM% sits below plan and keeps sliding"* | Contribution is compressing. |
| `trend_line` (vs_plan) — GM% over time | One-off or trend? | *"Gross margin has slid below plan through the period"* | It compounds month over month — a trend, not a dip. |
| `waterfall` (vs_plan, by PVM driver) — margin bridge | What's compressing it? | *"Price concessions and adverse mix drive GM below plan, not volume"* | The levers are commercial — price and mix. |
| `bar_chart` — GM% by business unit (one highlight) | Where? | *"A few business units sit below target and drag the portfolio"* | Focused intervention beats a thin, broad program. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: invoice_line` · **title:** *"Contribution leaks in a short list of SKUs"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — SKUs worst-first Top-N; net price, GM%, Δvs plan (deviation colour), mix effect | Where to act | *"Price realization below list explains most of the gap"* | Pinpoints the concession leaks. |
| `ActionPanel` — `C-M2.2`, `C-P4.1`, `C-S1.2` | Decision | *"Reinstate price guardrails on the leaking SKUs"* | Owned corrective action. |

---

### COM-003 · Customer Value — Commercial/CustomerValue · strategic KPI `crm.clv.amount`

**Report thesis:** *CLV growth has stalled — churn is accelerating in the mid-tier segment, eroding the base; targeted retention spend there stops the erosion before it compounds.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"CLV growth has stalled — the mid-tier is churning"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — CLV (hero), Lifetime Revenue, Retention %, Revenue-at-Risk | Signal | *"CLV growth has flattened while revenue-at-risk climbs"* | The base is eroding. |
| `trend_line` (vs_py) — Lifetime revenue by segment | Where's the decline? | *"Lifetime revenue is eroding, led by the mid-tier segment"* | Retention spend in mid-tier stops the erosion. |
| `bar_chart` — Retention % by segment (ranked) | Uneven where? | *"Retention slips unevenly across segments, concentrating CLV risk"* | Ranking pinpoints where to spend before churn compounds. |
| `bar_chart` — Revenue-at-risk by segment (one highlight) | Concentration | *"Revenue at risk concentrates in a few segments"* | Protects more CLV per dollar. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: customer_month` · **title:** *"A short list of mid-tier accounts carries the risk"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — customers worst-first Top-N; CLV, retention, revenue-at-risk (data bars), NPS | Who to retain | *"High-value, low-retention accounts top the risk list"* | Names the retention targets. |
| `ActionPanel` — `C-C3.1`, `C-C3.2` | Decision | *"Deploy retention offers to the top-risk mid-tier accounts"* | Owned next step. |

---

### COM-004 · Promotion Effectiveness — Commercial · strategic KPI `sales.promo.roi.pct`

**Report thesis:** *Promo ROI is below threshold — cannibalization and thin incremental lift mean the mechanics need redesign before the next cycle, not more spend.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Promo ROI misses — spend is subsidising baseline sales"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Promo ROI% (hero), Incremental Sales, Promo GM%, Cannibalization % | Signal | *"Promo ROI is below threshold"* | The programme isn't paying back. |
| `bar_chart` — Incremental lift by campaign (ranked, one highlight) | Is lift enough? | *"Incremental lift is too low to justify the spend behind it"* | Low lift means promo subsidises sales that would have happened anyway. |
| `waterfall` — Baseline → incremental → cannibalized → net | What erodes ROI? | *"Thin promo margins are eroded by cannibalization, pulling ROI below target"* | Cannibalization on thin margin is the ROI killer — redesign, don't overspend. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: promo_product_period` · **title:** *"A handful of mechanics destroy value"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — promos worst-first Top-N; ROI, incremental, cannibalization, promo GM% (deviation colour) | Which to cut/fix | *"Deep-discount mechanics show the worst ROI and highest cannibalization"* | Identifies mechanics to redesign. |
| `ActionPanel` — `C-P4.1`, `C-M2.1`, `C-M2.2` | Decision | *"Redesign the loss-making mechanics before next cycle"* | Owned decision. |

---

### COM-IND-R001 · Basket & Category Cross-Sell — Commercial/Retail · strategic KPI `retail.category.crosssell_rate.pct`

> *Industry-variant (retail tier). KPIs are planned/not yet materialised in the model — brief is design-ready; charts bind once measures land.*

**Report thesis:** *Cross-sell attachment is below potential — a few high-traffic categories under-attach, so the lever is targeted basket bundling, not blanket promotion.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Cross-sell under-attaches in high-traffic categories"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Cross-sell rate (hero), Items/transaction, Avg basket value, Attachment rate | Signal | *"Cross-sell rate trails potential"* | Baskets are shallower than they should be. |
| `bar_chart` — Attachment rate by category (ranked, one highlight) | Where under-attaching? | *"A few high-traffic categories under-attach the most"* | Bundling effort concentrates there. |
| `column_chart` — Items per transaction by segment (RFM frequency) | Which shoppers? | *"Frequent shoppers already bundle; occasional shoppers don't"* | Target the occasional-shopper segment. |

**Detail — "The Action Matrix"** · T4/T3 · **title:** *"Category pairs with the biggest untapped attach"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — category pairs worst-first Top-N; attach rate, basket lift, frequency | Which pairs to bundle | *"Top pairs show high co-purchase but low attach"* | Names the bundles. |
| `ActionPanel` — `C-M3.1` | Decision | *"Launch targeted bundles on the top under-attached pairs"* | Owned decision. |

---

### FIN-001 · Cash & Liquidity Performance — Finance · strategic KPI `wc.ccc.days`

**Report thesis:** *Cash conversion is deteriorating — DSO extension and payables compression squeeze liquidity headroom; the fix is receivables and inventory days, not stretching payables further.*

**Overview — "The Pulse"** · T1 Strategic Overview / Trend · **title:** *"Cash conversion is slipping toward the safety margin"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — CCC days (hero), Cash balance, OCF, Cash vs plan % | Signal | *"CCC is lengthening and cash is drifting toward its threshold"* | Liquidity headroom is shrinking. |
| `trend_line` (vs_target) — Cash balance vs safety margin | How urgent? | *"Cash balance is drifting toward its safety-margin threshold"* | Without action the margin erodes before quarter-end. |
| `trend_line` (vs_plan) — OCF vs plan | What's behind it? | *"OCF trails plan, driven by collections, not cost"* | The fix is collections/conversion, not cost control. |
| `waterfall` (vs_target) — DSO / DIO / DPO → CCC bridge | Which lever? | *"CCC decomposes into DSO, DIO, and DPO days"* | The lever is receivables and inventory days — not delaying suppliers. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: entity_month` · **title:** *"Overdue receivables concentrate in a few accounts"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — entities worst-first Top-N; DSO, overdue AR, DIO (data bars, deviation colour) | Where to collect | *"A short list of accounts carries most of the DSO extension"* | Names the collections targets. |
| `ActionPanel` — `F-C1.1`, `F-C1.2`, `F-C1.4`, `S-I1.2` | Decision | *"Prioritise collections on the top overdue accounts; hold payables"* | Owned decision. |

---

### FIN-002 · Cost Performance — Finance/Operations · strategic KPI `cost.unit.amount`

**Report thesis:** *Input-cost inflation is outpacing pricing recovery — COGS% is expanding and will erode operating margin within two quarters unless productivity or pricing responds.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Input inflation is outrunning pricing — margin has ~2 quarters"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Unit cost (hero), COGS%, OpEx vs plan %, Labor productivity % | Signal | *"Unit cost is rising and COGS% is expanding"* | Cost is outpacing recovery. |
| `trend_line` — COGS % of sales over time | How fast? | *"COGS is rising as a share of sales, eroding margin quarter over quarter"* | At this pace, ~2 more quarters of erosion without a response. |
| `waterfall` (vs_plan) — OpEx / material / productivity → unit cost | Which lever? | *"Opex, material cost, and labor productivity are the three unit-cost levers"* | Productivity isn't offsetting material inflation. |
| `bar_chart` — Unit cost Δ vs plan by plant/line (one highlight) | Where? | *"A few lines drive most of the unit-cost variance"* | Concentrate cost action there. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: plant_line_product_month` · **title:** *"A short list of lines drives the cost variance"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — lines worst-first Top-N; unit cost, material %, productivity, yield (deviation colour) | Where to act | *"High material cost meets low productivity on the worst lines"* | Names the cost targets. |
| `ActionPanel` — `F-K2.1`–`F-K2.4` | Decision | *"Attack material cost and productivity on the top-variance lines"* | Owned decision. |

---

### OPS-001 · Operations Performance — Operations · strategic KPI `ops.oee.pct`

**Report thesis:** *OEE is below target and the gap is widening — availability losses are 70% of the shortfall, so maintenance action moves the needle faster than performance or quality tweaks.*

**Overview — "The Pulse"** · T3 Operational Monitoring / Exception Queue · **title:** *"OEE is below target — availability is the culprit"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — OEE (hero), Availability, Performance, Quality | Signal | *"OEE is below target"* | Output is leaking. |
| `trend_line` (vs_target) — OEE over time | Getting worse? | *"OEE runs below target and the gap is widening week over week"* | The gap compounds into missed output if action doesn't land now. |
| `waterfall` (vs_target) — Availability / Performance / Quality → OEE | Which component? | *"Availability is the component pulling OEE below target, not performance or quality"* | Maintenance fixes move the needle fastest. |
| `bar_chart` — Unplanned downtime by line (ranked, one highlight) | Where? | *"Two lines account for most unplanned downtime"* | Focus maintenance there. |

**Detail — "The Action Matrix"** · T3 Operational Monitoring · `evidence_grain: line_day` · **title:** *"Line 3 and Line 7 own 65% of unplanned downtime"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — lines worst-first Top-N; downtime, MTBF, MTTR, PM compliance (deviation colour) | Where to act | *"Maintenance backlog on Lines 3 and 7 is the root cause"* | Names the assets. |
| `ActionPanel` — `O-O1.1`–`O-O1.4` | Decision | *"Clear the maintenance backlog on Lines 3 and 7 this week"* | Owned decision. |

---

### OPS-002 · Asset Performance — Operations · strategic KPI `ops.mtbf.hours`

**Report thesis:** *Asset availability is declining — maintenance backlog accumulates faster than it clears, and at this trajectory availability drops below the level needed to hold the production plan.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Availability is trending below what the plan needs"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — MTBF (hero), Availability, MTTR, Unplanned downtime % | Signal | *"MTBF is falling and availability is drifting down"* | Reliability is degrading. |
| `trend_line` (vs_plan) — Availability vs plan threshold | How close to risk? | *"Availability is trending toward the threshold needed to hold the plan"* | At this trajectory it drops below plan-holding level. |
| `bar_chart` — Unplanned downtime by asset (ranked, one highlight) | Which assets? | *"Unplanned downtime and spare-parts stockout are the leading failure signals"* | Ranking downtime by asset targets maintenance where it protects the plan most. |

**Detail — "The Action Matrix"** · T3 Process Control · `evidence_grain: failure_event` · **title:** *"A few assets generate most failures"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — assets worst-first Top-N; failures, MTBF, MTTR, PM compliance, spare stockout (deviation colour) | Where to act | *"Low PM compliance tracks the highest-failure assets"* | Names the assets and the PM gap. |
| `ActionPanel` — `O-A2.1`–`O-A2.5` | Decision | *"Raise PM compliance and pre-stock spares on the top-failure assets"* | Owned decision. |

---

### OPS-003 · Quality & Yield — Operations · strategic KPI `quality.fpy.pct`

**Report thesis:** *Scrap is trending above target — yield loss concentrates on two lines, so line-level root-cause containment beats a plant-wide quality program.*

**Overview — "The Pulse"** · T3 Operational Monitoring / Process Control · **title:** *"Scrap is above target — two lines drive it"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — FPY (hero), Scrap %, Rework %, COPQ | Signal | *"First-pass yield is below target as scrap rises"* | Quality is leaking money. |
| `trend_line` (vs_target) — Scrap % over time | Where's it rising? | *"Rising scrap is concentrated on a couple of lines, not plant-wide"* | Containing two lines is faster than a plant-wide program. |
| `bar_chart` — COPQ by line (ranked, one highlight) | Cost concentration | *"Rework and complaints are the downstream cost signals"* | Ranking COPQ by line prioritises where the money is. |

**Detail — "The Action Matrix"** · T3 Process Control · `evidence_grain: line_day` · **title:** *"Two lines carry the yield loss"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — lines worst-first Top-N; scrap, rework, defect density, COPQ (deviation colour) | Where to contain | *"Defect density on the two lines drives most COPQ"* | Names the lines and defect modes. |
| `ActionPanel` — `O-Q3.1`–`O-Q3.5` | Decision | *"Run root-cause containment on the two scrap-driving lines this quarter"* | Owned decision. |

---

### SCM-001 · Inventory Performance — Supply Chain · strategic KPI `inv.dio.days`

**Report thesis:** *Turnover is deteriorating — dead stock in three SKU clusters ties up working capital and masks demand; the root cause is forecast accuracy, not capacity.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Turnover is falling — dead stock is the cause, not demand"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — DIO days (hero), Turnover, Stockout %, OTIF % | Signal | *"DIO is rising and turnover is falling"* | Working capital is tied up. |
| `trend_line` (vs_target) — Turnover over time | What's the cost? | *"Inventory turnover is falling, tying up working capital in slow stock"* | That capital could fund faster-moving SKUs. |
| `bar_chart` — Stockout / obsolescence risk by cluster (ranked) | Which risk? | *"Stockout, OTIF, and obsolescence are the three inventory-health signals"* | Rising stockouts *and* obsolescence together = a demand-signal problem. |
| `bar_chart` (vs_target) — Forecast accuracy by cluster (one highlight) | Root cause | *"Forecast accuracy below target is the root behind the stockout/obsolescence swing"* | Fixing forecast addresses the root, not the symptoms. |

**Detail — "The Action Matrix"** · T3 Exception Queue · `evidence_grain: location_sku_month` · **title:** *"Three SKU clusters hold the dead stock"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — SKUs worst-first Top-N; DIO, turnover, obsolescence, forecast error (deviation colour) | Where to act | *"High-DIO SKUs share poor forecast accuracy"* | Names the SKUs and the forecast link. |
| `ActionPanel` — `S-I1.1`–`S-I1.5` | Decision | *"Recalibrate forecasts and clear the three dead-stock clusters"* | Owned decision. |

---

### SCM-002 · Supply Reliability & OTIF — Supply Chain · strategic KPI `supply.otif.pct`

**Report thesis:** *OTIF is declining — on-time is the dragging component (not in-full), and delivery failures concentrate in two categories, so carrier/lane fixes matter more than stock buffers.*

**Overview — "The Pulse"** · T3 Operational Monitoring / Process Control · **title:** *"OTIF is down — on-time is the drag, not in-full"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — OTIF % (hero), On-time %, In-full %, Stockout impact % | Signal | *"OTIF is below target"* | Delivery reliability is slipping. |
| `trend_line` (vs_target) — OTIF split into on-time vs in-full | Which component? | *"On-time delivery is the component dragging OTIF below target, not in-full"* | Carrier and lane fixes beat in-full stock buffers. |
| `bar_chart` — Penalty/expedite cost by supplier (ranked, one highlight) | Where's the leak? | *"In-full and stockout impact are the other two OTIF components"* | Ranking penalty by supplier focuses the push where money leaks. |

**Detail — "The Action Matrix"** · T3 Exception Queue · `evidence_grain: shipment_line` · **title:** *"Two supplier categories create the failures"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — suppliers/lanes worst-first Top-N; OTIF, on-time, penalty, expedite (deviation colour) | Where to act | *"A short list of lanes drives the on-time misses"* | Names the lanes/suppliers. |
| `ActionPanel` — `S-R2.1`–`S-R2.5` | Decision | *"Re-route or re-contract the worst on-time lanes"* | Owned decision. |

---

### SCM-003 · Forecast vs Actual — Supply Chain/Planning · strategic KPI `plan.forecast.accuracy.pct`

**Report thesis:** *Forecast error is above threshold and it's systematic bias (not noise) in the mid-range SKU cluster — so model recalibration removes more of the gap than manual overrides.*

**Overview — "The Pulse"** · T2 Tactical Variance / Comparative · **title:** *"Forecast error is systematic bias, not noise"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Forecast accuracy (hero), MAPE, Bias, Service impact | Signal | *"Forecast accuracy is below threshold"* | Planning is mis-calibrated. |
| `trend_line` (vs_target) — Bias over time | Bias or noise? | *"Forecast error is a systematic bias, not random noise"* | Recalibration fixes more than manual overrides. |
| `bar_chart` — Bias by SKU cluster (ranked, one highlight) | Where? | *"Forecast bias and service impact are the two forecast-quality signals"* | Ranking bias by cluster isolates where recalibration removes most replanning load. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: sku_location_month` · **title:** *"The mid-range cluster drives the overstock"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — SKU-locations worst-first Top-N; bias, MAPE, overstock, service impact (deviation colour) | Where to recalibrate | *"Consistent positive bias concentrates in the mid-range cluster"* | Names the clusters/regions. |
| `ActionPanel` — `S-F3.1`–`S-F3.4` | Decision | *"Recalibrate the model on the biased cluster; retire manual overrides"* | Owned decision. |

---

### XD-001 · Service Level Performance — Experience/Service · strategic KPI `svc.sla.attainment.pct`

**Report thesis:** *Backlog is building toward SLA breaches — declining first-contact resolution and rising escalations point to a capability gap, so fixing FCR cuts escalations and backlog at once.*

**Overview — "The Pulse"** · T3 Operational Monitoring / Process Control · **title:** *"Backlog is building toward SLA breaches"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — SLA attainment (hero), Backlog, FCR %, Escalation % | Signal | *"SLA attainment is at risk as backlog grows"* | Service is falling behind. |
| `trend_line` (vs_target) — Backlog + SLA over time | How urgent? | *"Case backlog is building unchecked toward SLA breaches next cycle"* | Unchecked, it converts to missed SLAs within a cycle. |
| `bar_chart` — FCR by case type (ranked, one highlight) | Root cause | *"FCR, handle time, and escalation are the three service-quality signals"* | Ranking FCR by case type shows where a capability fix cuts escalations and backlog at once. |

**Detail — "The Action Matrix"** · T3 Exception Queue · `evidence_grain: case` · **title:** *"A few case types drive the escalations"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — case types worst-first Top-N; FCR, AHT, escalation, backlog age (deviation colour) | Where to act | *"Low-FCR case types generate most escalations and aged backlog"* | Names the case types. |
| `ActionPanel` — `X-S1.1`–`X-S1.4` | Decision | *"Close the capability gap on the low-FCR case types"* | Owned decision. |

---

### XD-002 · Resource Utilization — Experience/Service · strategic KPI `res.utilization.pct`

**Report thesis:** *Utilization is above sustainable levels — occupancy peaks in two teams create burnout risk that overtime is masking; that overtime is the early signal of a capacity shortfall.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Two teams are overloaded — overtime is masking it"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Utilization (hero), Occupancy, Overtime %, Shrinkage % | Signal | *"Utilization is above the sustainable threshold"* | The system is running hot. |
| `trend_line` (vs_plan) — Occupancy by team | Where's the overload? | *"Resource occupancy is running at sustained overload in a few teams"* | Sustained overload threatens the service-quality the SLA depends on. |
| `bar_chart` — Overtime % by team (ranked, one highlight) | Hidden cost | *"SLA, overtime, and shrinkage are utilization's three quality trade-offs"* | Overtime absorbing the gap is the early signal of the shortfall to come. |

**Detail — "The Action Matrix"** · T3 Process Control · `evidence_grain: agent_day` · **title:** *"The overload concentrates in two teams"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — teams worst-first Top-N; occupancy, overtime, shrinkage, SLA (deviation colour) | Where to rebalance | *"The two hottest teams also carry the most overtime"* | Names the teams to rebalance. |
| `ActionPanel` — `X-R2.1`–`X-R2.4` | Decision | *"Rebalance workload and add capacity to the two overloaded teams"* | Owned decision. |

---

### XD-003 · Executive KPI Overview — Executive/Cross-Functional · strategic KPI `enterprise.value_at_risk.index`

**Report thesis:** *Revenue growth is on track, but GM% compression and OTIF decline signal execution risk — two business units below threshold on both margin and service need executive escalation.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"On track on growth, exposed on margin and delivery"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Value-at-Risk index (hero), GM%, Net Sales ΔLY, OTIF %, CCC days | Signal | *"Growth holds, but margin and OTIF flash risk"* | The headline hides execution exposure. |
| `trend_line` (vs_target) — Net Sales growth vs LY | Is growth durable? | *"Net sales growth versus last year is softening quarter to quarter"* | Softening growth is the first sign the story could reverse. |
| `bar_chart` — Normalized risk by strategic KPI / unit (ranked, one highlight) | Where's the exposure? | *"OTIF is uneven across the portfolio, flagging where delivery risk concentrates"* | A normalized index makes KPIs comparable, so attention goes to the biggest exposure. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: entity_month` · **title:** *"Two units are below threshold on margin and service"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — units worst-first Top-N; GM%, OTIF, CCC, attrition risk (deviation colour) | Who to escalate | *"Two business units are below threshold on both GM% and service level"* | Names the units for escalation. |
| `ActionPanel` — `X-E3.2` (+ cross-domain) | Decision | *"Escalate and reallocate resources to the two at-risk units"* | Owned decision. |

---

### XD-004 · Executive Action Governance — Experience · strategic KPI `enterprise.action_outcome_rate.pct`

**Report thesis:** *Governance must prove impact, not activity — verified action-outcome rate is the honesty check, and value-at-risk is concentrated where follow-through is weakest, so that's where governance attention goes.*

**Overview — "The Pulse"** · T1 Strategic Overview / Portfolio · **title:** *"Governance is measured by verified outcomes, not actions closed"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `kpi_card` band — Action outcome rate (hero), Effectiveness delta, Value-at-Risk index | Signal | *"Action outcome rate verifies whether governance closes on real impact"* | Tracking verified outcomes keeps the cycle honest. |
| `bar_chart` — Value-at-risk by domain (ranked, one highlight) | Where's follow-through weak? | *"Value at risk concentrates where action follow-through is weakest"* | Prioritising high-risk domains directs governance where it matters. |
| `trend_line` — Effectiveness delta over time | Is it improving? | *"Realised action effectiveness is trending against the plan"* | Confirms whether governance is compounding value. |

**Detail — "The Action Matrix"** · T4 Prescriptive · `evidence_grain: action_outcome` · **title:** *"The weakest follow-through carries the most risk"*

| Visual | purpose | statement_title | story_sentence |
|---|---|---|---|
| `smart_narrative` | Context | *(dynamic)* | Restates for the slice. |
| `matrix` — domains/actions worst-first Top-N; outcome rate, effectiveness delta, value-at-risk (deviation colour) | Where to intervene | *"High-value domains show the lowest verified-outcome rates"* | Names the domains to press. |
| `ActionPanel` — cross-domain Impactful-15 codes | Decision | *"Reopen and re-own the high-value actions with weak follow-through"* | Owned decision. |

---

## Part C — Cross-report consistency & handoff

- **One theme, one identity (BC-BRAND-01/02).** All 17 share the composed theme, the Big-Idea header band, tabular numerals, hero ≥ 2×, and the semantic colour map (K3 brand-theme cut).
- **Statement titles everywhere (BC-NARR-01).** The page/visual titles above replace the current `"<Domain> Summary & Insights"` / `"<Domain> Execution"` labels. These titles are the `big_idea` / `message` fields, rendered.
- **Evidence discipline (BC-CHART-10).** Every Detail matrix is worst-first Top-N at the stated `evidence_grain`.
- **Scale discipline (BC-CHART-01).** € and % are never on one axis; bridges use one unit; comparison base is a reference line.
- **Grounding (K4).** Each hero KPI should carry a benchmark/context reference-label once the `benchmark_catalog` lands, so the thesis reads expert, not templated.
- **Handoff.** For any report to be built/restyled to this spec, hand this brief to `powerbi-report-authoring` for the page/visual/theme mechanics and PBIR emission, then validate (Stage-1 + boutique scorecard) and Desktop-check.
