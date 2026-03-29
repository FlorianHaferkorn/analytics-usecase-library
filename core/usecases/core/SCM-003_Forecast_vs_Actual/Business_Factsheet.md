---
id: SCM-003
factsheet_type: business
---

# SCM-003 - Forecast vs Actual  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-003
- **Domain:** Supply Chain / Planning
- **Business Owner:** Head of Demand Planning / S&OP Lead
- **KPI Owner:** Planning Excellence / Controlling
- **Decision Owner:** S&OP Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/SupplyChain.SemanticModel (domain model for SCM-*).

---

## 1. Business Summary

**Purpose:** Improve forecast accuracy and bias to stabilize supply, service level, and inventory.  
**Business Value:** Fewer re-plans, better OTIF/stockout performance, lower working capital driven by better forecast quality.  
**Out of Scope:** Promotion-specific uplift models (COM-004); portfolio mix strategy (COM-009); detailed inventory optimization (SCM-001).

---

## 2. Core Business Questions

- Where is forecast accuracy and bias below target by channel/category/location?
- Which products drive the largest forecast errors and service impact?
- How often are re-plans triggered and why?
- Which actions (process, data, parameters) improve forecast quality fastest?

**Example Query Patterns (optional):**

- "Which top 20 SKUs by revenue have forecast accuracy < target and negative bias?"
- "Where did low accuracy drive OTIF misses or stockouts?"

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| plan.forecast.accuracy.pct | Strategic |
| plan.forecast.mape.pct | Influencing |
| plan.forecast.bias.pct | Influencing |
| plan.forecast.service_impact.pct | Influencing |
| plan.replan.count | Influencing |
| order.lines | Influencing |
| plans.count | Influencing |
| sales.units | Influencing |

**Action Codes:** S-F3.1, S-F3.2, S-F3.3, S-F3.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Forecast Accuracy %  
- MAPE %  
- Bias %  
- Service Impact %  
- Re-Plan Count  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Accuracy vs Target by Category/Location | Column | dim_product[Category] | [Forecast Accuracy %] | Location/Channel | Current quarter | Core ranking |
| Bias Distribution | Column | dim_product[Category] | [Bias %] | Location | Current quarter | Highlight over/under |
| Service Impact Trend | Line | dim_date[Month] | [Service Impact %] | Channel | L12M | Service linkage |
| Re-Plan Count by Month | Column | dim_date[Month] | [Re-Plan Count] | Region | L12M | Stability |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel / Location  
- Category / Product  
- ABC/XYZ (if available)

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_forecast

  - fact_sales (actuals)

  - fact_fulfillment (for service impact linkage)

  - fact_stockout (for service impact linkage)

  - fact_replan (if available)
required_dimensions:

  - dim_date

  - dim_org (location/channel/region)

  - dim_product

  - security_user_org
required_grain: sku_month for accuracy/bias; order/day for service impact; month for replans
required_time_range: 12-24 months history
required_slicers: Date, Region/Channel/Location, Category/Product, ABC/XYZ
```

---

## 7. Dependencies, Assumptions & Constraints

- Forecast/actual aligned by SKU/location/time; promotions/launches flagged to avoid misinterpretation.
- Re-plan events captured; service impact link to OTIF/stockout available.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).
- Data latency =24h; plan versions stored.

---

## 8. Success Criteria

- Impact: Accuracy improves to target; bias within bands; reduced service impact; fewer re-plans.  
- Adoption: Used in monthly S&OP/planning reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source totals.  
- Decision Frequency: Monthly S&OP and weekly planning reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misinterpreting bias/accuracy on launch or promo items.  
- Service impact overstated if OTIF/stockout not properly linked.  
- Re-plan counts misleading if process changes not tracked.  







## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: Persistent Forecast Bias Driving Excess Inventory

**Situation:** Forecast accuracy is 72% (target 85%), but the issue is directional — forecast bias is consistently +15%, meaning systematic over-forecasting. Inventory days on hand have increased 8 days as a result.

**Decision question:** Is the bias driven by optimistic sales input, outdated baseline models, or promotional volume that didn't materialize?

**Who decides:** Demand Planning Lead + Sales Operations.

**Consequence of inaction:** Excess inventory ties up €4M in working capital; obsolescence risk increases for perishable/seasonal items.

**Action Code triggered:** S-F3.2 (Forecast Bias Correction) — activates bias decomposition by product family and input source.

### Scenario B: High MAPE Concentrated in New Product Launches

**Situation:** Overall MAPE is 28%, but segmentation reveals that new products (launched <6 months) account for 60% of forecast error. Mature products forecast at 88% accuracy.

**Decision question:** Should new product forecasting use a different method (analogous, bottom-up from pre-orders) rather than the statistical baseline?

**Who decides:** Demand Planning Lead + Product Launch Manager.

**Consequence of inaction:** New product launches consistently over- or under-stocked; service impact on key launches damages market entry.

**Action Code triggered:** S-F3.3 (Forecast Method Review) — activates accuracy segmentation and method-level benchmarking.
