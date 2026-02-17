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
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** core/semantic_models/core_action_ready/model_definition.yaml

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


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


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



