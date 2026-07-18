---
id: COM-004
factsheet_type: business
---

# COM-004 - Promotion Effectiveness  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-004
- **Domain:** Commercial
- **Business Owner:** CMO / Trade Marketing Lead
- **KPI Owner:** Revenue Growth Management / Commercial Controlling
- **Decision Owner:** Sales & Marketing Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/Commercial.SemanticModel (domain model for COM-*).

---

## 1. Business Summary

**Purpose:** Improve promotion ROI by measuring true incremental sales and margin, controlling leakage, and optimising promo mechanics.  
**Business Value:** Fewer unprofitable promos; higher incremental GM; better channel/product targeting; reduced cannibalization.  
**Out of Scope:** Long-term pricing strategy (COM-002); assortment optimisation; omni-channel mix (COM-009).

---

## 2. Core Business Questions

- Which promotions generated true incremental sales and gross margin?
- Which channels/products deliver the highest promo ROI and uplift?
- How much did discounts erode price realization and GM?
- What promo depth/timing/mechanics should we standardize or stop?
- Where do cannibalization or leakage offset uplift?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| sales.promo.roi.pct | Strategic |
| sales.promo.incremental.amount | Influencing |
| margin.promo.gm.pct | Influencing |
| sales.price.list.amount | Influencing |
| sales.price.net.amount | Influencing |
| sales.price.realization_pct | Influencing |
| sales.promo.cannibalization.pct | Influencing |
| cost.cogs.amount | Supporting |
| sales.promo.baseline_sales.amount | Supporting |
| sales.promo.cannibalized_sales.amount | Supporting |
| sales.promo.cost.amount | Supporting |
| sales.promo.incremental_gm.amount | Supporting |
| sales.pvm.volume_effect.amount | Supporting |

**Action Codes:** C-P4.1, C-M2.1, C-M2.2

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Promo ROI %** (`sales.promo.roi.pct`) → **Trade Promotion Management (convention)** (none): Promo ROI (incremental GM / promo cost) is a TPM convention.
- **Incremental Sales Amount** (`sales.promo.incremental.amount`) → **Trade Promotion Management (convention)** (none): Incremental (promo − baseline) uplift is a TPM convention.
- **GM % During Promo** (`margin.promo.gm.pct`) → **ESMA-APM** (none): Internal commercial / trade-promotion metric (incremental GM during promo); not an IFRS or ESMA-named measure.
- **List Price Amount** (`sales.price.list.amount`) → **IFRS 15** (none): List price is a pre-discount catalogue figure — an input to discount/realization analysis, not an IFRS 15 figure (IFRS 15 measures the transaction price actually expected).
- **Net Price Amount** (`sales.price.net.amount`) → **IFRS 15** (partial): Net price is the IFRS 15 transaction price after trade discounts and variable consideration.
- **Price Realization %** (`sales.price.realization_pct`) → **IFRS 15** (none): Price realization (net/list) is a management pricing metric, not IFRS-defined.
- **Cannibalization %** (`sales.promo.cannibalization.pct`) → **Trade Promotion Management (convention)** (none): Cannibalization (cannibalized / uplift sales) is a TPM analytics concept, not standard-defined.

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Promotion ROI %  
- Incremental Sales Amount  
- Promo Gross Margin %  
- Price Realization %  
- Cannibalization %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Promo ROI by Channel | Column | Channel | Promo ROI % | Region | Current quarter | Rank promos |
| Incremental Sales vs Baseline | Column | Promotion | Incremental Sales Amount | Category | Current period | Baseline vs actual |
| Price Realization Ladder | Waterfall | Price components | Net vs List | Channel | Current quarter | Show discount/rebate/surcharge |
| Cannibalization vs Uplift | Scatter | Cannibalization % | Incremental Sales Amount | Category/Region | Current period | Identify harmful promos |

### 5.3 Required Slicers (Mandatory)

- Date/Promo period  
- Region / Channel  
- Product Category / Subcategory  
- Promotion Type/Mechanic  

### 5.4 300-Second Layer (Diagnostics)

- Promo-level GM bridge showing uplift, cannibalized sales, promo cost, and incremental GM by campaign, channel, and category.
- Cannibalization root-cause table linking related SKUs and product families to the campaigns that shifted demand instead of creating incremental value.
- Mechanic depth, timing, and realization analysis by channel and category so trade marketing can distinguish healthy promo investment from price-leaking activity.

---

## 6. Data Requirements Summary

- Required facts: fact_promo for baseline and promo-cost logic, plus fact_sales for invoice-line uplift, realization, and GM reconstruction.
- Required dimensions: dim_date, dim_org, dim_product, dim_promo, and security_user_org.
- Required grain: promotion for campaign evaluation, with invoice-line sales retained for uplift and realization diagnostics.
- Required time range: 12-24 months of promo history with stable baseline assumptions.
- Required slicers: Date/Promo period, Region/Channel, Product Category/Subcategory, Promotion Type/Mechanic.

---

## 7. Dependencies, Assumptions & Constraints

- Baseline model for incremental sales defined and stable; uplift calculations align with COM-001/002.
- Discount components (net/list, rebates, surcharges) available to compute price realization during promos.
- Cannibalization logic depends on related items/product hierarchy.
- Conformed dims (Date, Org, Product, Promo, security_user_org) required; promo calendar/timing accurate.

---

## 8. Success Criteria

- **Benchmark Targets (world-class reference):** Promo ROI >=120% (1.2x), noting that ~59% of CPG promotions fail to break even globally and 72% in the US (McKinsey); only ~45% of gross promotional lift is truly incremental, the rest being switching/stockpiling (Ailawadi et al. 2006, JMR); promotional price elasticity averages ~-3.6 vs ~-2.6 overall, so discount depth must be justified against realization erosion (Bijmolt, Van Heerde & Pieters 2005, JMR).  
- Impact: Higher promo ROI (>=120%), higher incremental GM, reduced cannibalization.
- Adoption: Used in promo/post-event reviews; actions logged via Action Codes.
- Quality: Uplift and ROI reconcile to baseline and costs; definitions aligned with COM-001/002.
- Decision Frequency: Promo cycle (pre/post) and monthly reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Baseline mis-specified leading to overstated uplift/ROI.
- Ignoring cannibalization/halo effects distorts net benefit.
- Over-discounting to lift volume without GM guardrails.

---





## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: High Cannibalization Eroding Promo ROI

**Situation:** Promo ROI has dropped to 0.8x (below breakeven) in the latest campaign wave. Incremental sales are positive, but cannibalization rate spiked to 35%, meaning baseline sales shifted into promo windows rather than generating true uplift.

**Decision question:** Is the cannibalization structural (customers trained to wait for promos) or campaign-specific (overlapping promotions on substitutes)?

**Who decides:** Trade Marketing Lead + Category Manager.

**Consequence of inaction:** Continued promo investment destroys margin; each campaign cycle reinforces buying pattern shift.

**Action Code triggered:** C-M2.1 (Promo Mix Optimization) — activates cannibalization decomposition by product pair and campaign type.

### Scenario B: Strong Incremental Sales but Margin-Negative Promos

**Situation:** A regional promo generated €1.2M incremental sales (+18% uplift), but promo GM% is 8pp below standard GM%. Price realization dropped to 72%.

**Decision question:** Should the promo mechanic be adjusted (depth, duration, product scope) or discontinued in this format?

**Who decides:** Commercial Controlling + Regional Sales Director.

**Consequence of inaction:** Volume-positive but margin-negative promos accumulate; quarterly GM target at risk.

**Action Code triggered:** C-S1.1 (Price Realization Recovery) — activates promo-level P&L analysis and mechanic comparison.
