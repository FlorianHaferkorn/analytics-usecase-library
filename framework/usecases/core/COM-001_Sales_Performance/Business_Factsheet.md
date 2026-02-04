---
id: COM-001
factsheet_type: business
---
# COM-001 - Sales Performance vs Plan & LY  

## Business Factsheet

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
    kpi_catalog_id: Growth
    name: Net Sales Amount
    purpose: Core revenue control
    agg: sum

  - id: sales.net_sales.delta_pct.plan
    name: Net Sales % vs Plan
    purpose: Execution vs Plan
    agg: avg

  - id: sales.net_sales.delta_pct.ly
    name: Net Sales % vs LY
    purpose: Growth vs LY
    agg: avg

  - id: margin.gm.pct
    name: Gross Margin %
    purpose: Profitability quality
    agg: avg

  - id: sales.pvm.price_effect.amount
    name: Price Effect Amount
    purpose: Driver analysis
    agg: sum

  - id: sales.pvm.volume_effect.amount
    name: Volume Effect Amount
    purpose: Driver analysis
    agg: sum

  - id: sales.pvm.mix_effect.amount
    name: Mix Effect Amount
    purpose: Driver analysis
    agg: sum
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: C-M2.1
    name: Price Realization Guardrails
    purpose: Stop Discount Leakage
    status: active
    owner: Pricing Lead
    trigger_kpis: [sales.price.realization_pct]
    guardrail_kpis: [margin.gm.pct]
    outcome_kpis: [sales.price.realization_pct, margin.gm.pct]
    impact_range: sales.price.realization_pct: 1.0-3.0 pp
    levels: L1-L3

  - id: C-S1.1
    name: Price Discipline Enforcement
    purpose: Protect Gross Margin
    status: active
    owner: Pricing Manager
    trigger_kpis: [margin.gm.pct, sales.pvm.price_effect.amount]
    guardrail_kpis: [sales.net_sales.delta_pct.plan]
    outcome_kpis: [margin.gm.pct]
    impact_range: margin.gm.pct: 0.5-1.5 pp
    levels: L1-L3

  - id: C-S1.2
    name: Sales Gap Recovery via Price & Pack Adjustment
    purpose: Close Plan Gaps Without Margin Erosion
    status: active
    owner: Sales Director
    trigger_kpis: [sales.net_sales.delta_pct.plan]
    guardrail_kpis: [margin.gm.pct]
    outcome_kpis: [sales.net_sales.amount]
    impact_range: sales.net_sales.amount: 1.0-3.0 %
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Net Sales Amount  
- Net Sales % vs Plan  
- Net Sales % vs LY  
- Gross Margin %  
- Price/Volume/Mix Effects (cards or mini-tiles)  

### 5.2 30-Second Layer (Main Visuals)

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

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel  
- Product Category  
- Customer Segment (optional)

### 5.4 300-Second Layer (Diagnostics)

- PVM decomposition by Region/Channel/Product.
- Margin guardrail table (GM %, discount discipline).
- Top-N accounts/products with adverse price/mix effects.

---

## 6. Data Requirements Summary

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

## 7. Dependencies, Assumptions & Constraints

- Plan and LY fields must be populated in fact_sales (Plan Sales Amount,
  Last Year Sales Amount).
- PVM requires Net Price Amount, Plan Sales Amount, Quantity and residual logic
  alignment with COM-002.
- Gross Margin uses COGS; returns/credit notes handled upstream.
- Conformed dims (Date, Org, Product, security_user_org) required.

---

## 8. Success Criteria

- Impact: Net Sales vs Plan/LY gaps reduced; GM % at or above target.
- Adoption: Used in monthly sales performance reviews; actions tracked via
  Action Codes.
- Quality: PVM residual within tolerance; reconciled to source totals;
  definitions consistent with COM-002/004.
- Decision Frequency: Monthly/Quarterly.

---

## 9. Risks & Wrong Interpretations (Short)

- Misstated Plan/LY leading to false gaps.
- PVM residual too high due to inconsistent plan price or quantity.
- Over-reacting on price without GM guardrails can erode margin.

---



