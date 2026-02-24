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
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Commercial.SemanticModel (domain model for COM-*).

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

- Promo-level GM bridge (uplift vs cost vs leakage).
- Cannibalization root-cause table (related SKUs, categories).
- Mechanic depth/timing analysis by channel/category.

---

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_sales

  - fact_promo
required_dimensions:

  - dim_date

  - dim_org

  - dim_product

  - dim_promo

  - security_user_org
required_grain: promotion (with invoice_line base for uplift/realization)
required_time_range: 12-24 months of promo history with baseline
required_slicers: Date/Promo period, Region/Channel, Product Category/Subcategory, Mechanic
```

---

## 7. Dependencies, Assumptions & Constraints

- Baseline model for incremental sales defined and stable; uplift calculations align with COM-001/002.
- Discount components (net/list, rebates, surcharges) available to compute price realization during promos.
- Cannibalization logic depends on related items/product hierarchy.
- Conformed dims (Date, Org, Product, Promo, security_user_org) required; promo calendar/timing accurate.

---

## 8. Success Criteria

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




