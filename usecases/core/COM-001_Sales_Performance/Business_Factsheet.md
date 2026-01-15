---
id: COM-001
factsheet_type: business
---
# COM-001 - Sales Performance vs Plan & LY  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-001
- **Domain:** Commercial
- **Business Owner:** CCO / Head of Sales
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Explain Net Sales performance vs Plan and vs Last Year by price,
volume, mix, and channel/region to protect revenue and margin.  
**Business Value:** Faster detection of revenue gaps; targeted pricing and mix
actions to stabilise gross margin; focus resources on the most material
regions/channels.  
**Out of Scope:** Promotion ROI deep dives (COM-004); detailed margin leakage
diagnostics (COM-002); pipeline/win-loss (COM-010).

---

## 2. Core Business Questions

- Where do Net Sales deviate most vs Plan and vs LY by region, channel, and
  product hierarchy?
- What is the contribution of price, volume, and mix to the Net Sales gap?
- Which customer or product segments drive negative gross margin %?
- Which actions (pricing, mix, volume activation) close the largest gaps
  fastest?
- How persistent are the gaps over the last 3 months and current quarter?

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: sales.net_sales.amount
    name: Net Sales Amount
    purpose: Core revenue control
    definition_short: Sum of net sales after discounts
    unit: "EUR"
    grain: month
    agg: sum
    target: Meet/beat Plan and LY
    interpretation: Negative gap signals revenue risk
    lineage: fact_sales[Net Sales Amount] x dim_date, dim_org, dim_product

  - id: sales.net_sales.delta_pct.plan
    name: Net Sales % vs Plan
    purpose: Execution vs Plan
    definition_short: (Net Sales - Plan) / Plan
    unit: "%"
    grain: month
    agg: avg
    target: >= -2% guardrail
    interpretation: Below guardrail shows miss vs Plan
    lineage: fact_sales[Net Sales Amount], fact_sales[Plan Sales Amount]

  - id: sales.net_sales.delta_pct.ly
    name: Net Sales % vs LY
    purpose: Growth vs LY
    definition_short: (Net Sales - LY) / LY
    unit: "%"
    grain: month
    agg: avg
    target: +3% to +5%
    interpretation: Negative YoY signals deterioration
    lineage: fact_sales[Net Sales Amount], fact_sales[Last Year Sales Amount]

  - id: margin.gm.pct
    name: Gross Margin %
    purpose: Profitability quality
    definition_short: Gross Margin / Net Sales
    unit: "%"
    grain: month
    agg: avg
    target: >= 25%
    interpretation: Compression shows price/mix pressure
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount]

  - id: sales.pvm.price_effect.amount
    name: Price Effect Amount
    purpose: Driver analysis
    definition_short: Net Sales impact from price change
    unit: "EUR"
    grain: month
    agg: sum
    target: 0 unless price change
    interpretation: Negative implies price dilution
    lineage: fact_sales[Net Price Amount], fact_sales[Plan Sales Amount], fact_sales[Quantity]

  - id: sales.pvm.volume_effect.amount
    name: Volume Effect Amount
    purpose: Driver analysis
    definition_short: Net Sales impact from volume change
    unit: "EUR"
    grain: month
    agg: sum
    target: 0 unless volume change
    interpretation: Negative implies demand/availability issue
    lineage: fact_sales[Quantity], fact_sales[Plan Sales Amount]

  - id: sales.pvm.mix_effect.amount
    name: Mix Effect Amount
    purpose: Driver analysis
    definition_short: Net Sales impact from mix change
    unit: "EUR"
    grain: month
    agg: sum
    target: >= 0
    interpretation: Negative implies adverse mix
    lineage: fact_sales[Net Sales Amount], PVM decomposition residual
```

---

## 4. Business Logic & Thresholds

### 4.1 Logic Description

### 4.2 Formal Trigger Rules (Machine-Readable)

- Flag regions/channels with Net Sales % vs Plan below guardrail for 2
  consecutive months.
- Escalate where Net Sales % vs LY is negative and GM % below target.
- Use PVM drivers to isolate whether price, volume, or mix is the primary gap driver.
- Apply pricing/mix actions only where GM % guardrails hold.

```yaml
triggers:

  - kpi: sales.net_sales.delta_pct.plan
    condition: below_guardrail
    threshold: -0.02
    scope: Region/Channel, Month
    exclusion: none
    action_code: P4

  - kpi: margin.gm.pct
    condition: below_target
    threshold: 0.25
    scope: Region/Channel, Month
    exclusion: approved promos
    action_code: P2

  - kpi: sales.pvm.price_effect.amount
    condition: negative
    threshold: 0
    scope: Region/Channel
    exclusion: none
    action_code: P2

  - kpi: sales.pvm.mix_effect.amount
    condition: negative
    threshold: 0
    scope: Region/Channel
    exclusion: strategic SKUs
    action_code: M3
```

---

## 5. Action Codes (Mandatory)

- **P2 — Margin Leakage Correction**
  - Trigger (formal): GM % below target or price effect negative
  - Description: Tighten discounting, enforce floors/approvals
  - Expected KPI Impact: Improve GM %, stabilise revenue
  - Level (L1/L2/L3): L2
  - Owner: Pricing / Sales Ops

- **P4 — Price Repositioning**
  - Trigger (formal): Net Sales % vs Plan below guardrail
  - Description: Adjust price/pack/discount to recover growth without eroding
    margin
  - Expected KPI Impact: Increase Net Sales %, stable GM %
  - Level (L1/L2/L3): L2
  - Owner: Commercial

- **M3 — Mix Optimisation**
  - Trigger (formal): Mix effect negative
  - Description: Shift to higher-margin SKUs/bundles
  - Expected KPI Impact: Improve GM % and Net Sales
  - Level (L1/L2/L3): L2
  - Owner: Category Mgmt

- **D1 — Cost Take-Out / COGS Control**
  - Trigger (formal): Margin erosion due to COGS
  - Description: Negotiate terms, switch inputs/logistics
  - Expected KPI Impact: Improve GM %
  - Level (L1/L2/L3): L2
  - Owner: Procurement / Ops

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Net Sales Amount  
- Net Sales % vs Plan  
- Net Sales % vs LY  
- Gross Margin %  
- Price/Volume/Mix Effects (cards or mini-tiles)  

### 6.2 30-Second Layer (Main Visuals)

- **Net Sales vs Plan/LY**
  - Visual Type: Line + area band
  - X-Axis: Date[Month]
  - Y-Axis: Net Sales, Plan, LY
  - Segment: Region/Channel
  - Default Filter: L12M
  - Notes: Show gaps

- **PVM Bridge**
  - Visual Type: Waterfall
  - X-Axis: Drivers
  - Y-Axis: P, V, M impact
  - Segment: Region/Channel
  - Default Filter: Current Q
  - Notes: Link to COM-002

- **GM % by Region/Channel**
  - Visual Type: Column
  - X-Axis: Region/Channel
  - Y-Axis: GM %
  - Segment: Product Tier
  - Default Filter: Current Q
  - Notes: Guardrails

- **Top/Bottom Segments**
  - Visual Type: Bar (rank)
  - X-Axis: Region/Channel/Segment
  - Y-Axis: Net Sales Gap
  - Segment: Product
  - Default Filter: Current Q
  - Notes: Focus list

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel  
- Product Category  
- Customer Segment (optional)

### 6.4 300-Second Layer (Diagnostics)

- PVM decomposition by Region/Channel/Product.
- Margin guardrail table (GM %, discount discipline).
- Top-N accounts/products with adverse price/mix effects.

---

## 7. Data Requirements Summary

```yaml
required_facts:

  - fact_sales
required_dimensions:

  - dim_date

  - dim_org

  - dim_product

  - security_user_org
required_grain: >
  invoice_line (aggregated to month for KPIs)
required_time_range: 24 months history with Plan and LY
required_slicers: >
  Date, Region/Channel, Product Category, Customer Segment (optional)
```

---

## 8. Dependencies, Assumptions & Constraints

- Plan and LY fields must be populated in fact_sales (Plan Sales Amount,
  Last Year Sales Amount).
- PVM requires Net Price Amount, Plan Sales Amount, Quantity and residual logic
  alignment with COM-002.
- Gross Margin uses COGS; returns/credit notes handled upstream.
- Conformed dims (Date, Org, Product, security_user_org) required.

---

## 9. Success Criteria

- Impact: Net Sales vs Plan/LY gaps reduced; GM % at or above target.
- Adoption: Used in monthly sales performance reviews; actions tracked via
  Action Codes.
- Quality: PVM residual within tolerance; reconciled to source totals;
  definitions consistent with COM-002/004.
- Decision Frequency: Monthly/Quarterly.

---

## 10. Risks & Wrong Interpretations (Short)

- Misstated Plan/LY leading to false gaps.
- PVM residual too high due to inconsistent plan price or quantity.
- Over-reacting on price without GM guardrails can erode margin.

---
