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
- **Related Data Contract:** core/core/core/data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** core/core/core/semantic_models/core_action_ready/model_definition.yaml

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

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: plan.forecast.accuracy.pct
    kpi_catalog_id: Efficiency
    name: Forecast Accuracy %
    purpose: Planning quality (units-based forecast)
    agg: avg

  - id: plan.forecast.mape.pct
    name: MAPE %
    purpose: Error magnitude (units-based forecast)
    agg: avg

  - id: plan.forecast.bias.pct
    name: Forecast Bias %
    purpose: Direction of error (units-based forecast)
    agg: avg

  - id: plan.forecast.service_impact.pct
    name: Service Impact %
    purpose: Service effect of forecast error (units-based)
    agg: avg

  - id: plan.replan.count
    name: Re-Plan Count
    purpose: Planning stability
    agg: sum

  - id: order.lines
    name: Order Lines Count
    purpose: Demand volume
    agg: sum

  - id: plans.count
    name: Plans Count
    purpose: Planning activity
    agg: sum

  - id: sales.units
    name: Sales Units
    purpose: Actuals baseline
    agg: sum
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: S-F3.1
    name: Forecast Quality Orchestration
    purpose: Coordinate Forecast Quality Levers Without Conflicting Fixes
    status: active
    owner: S&OP Lead
    trigger_kpis: [plan.forecast.accuracy.pct, plan.replan.count]
    guardrail_kpis: [plan.forecast.service_impact.pct]
    outcome_kpis: [plan.forecast.accuracy.pct]
    impact_range: plan.forecast.accuracy.pct: 5.0-12.0 pp
    levels: L1-L3

  - id: S-F3.2
    name: Forecast Bias & Accuracy Correction
    purpose: Correct Systematic Forecast Bias and Accuracy Gaps
    status: active
    owner: Demand Planning Manager
    trigger_kpis: [plan.forecast.bias.pct, plan.forecast.mape.pct]
    guardrail_kpis: [plan.replan.count]
    outcome_kpis: [plan.forecast.accuracy.pct, plan.forecast.bias.pct]
    impact_range: plan.forecast.accuracy.pct: 4.0-10.0 pp
    levels: L1-L3

  - id: S-F3.3
    name: Service Impact Containment
    purpose: Limit Downstream Service Damage Caused by Forecast Error
    status: active
    owner: Supply Planning Manager
    trigger_kpis: [plan.forecast.service_impact.pct]
    guardrail_kpis: [inv.dio.days]
    outcome_kpis: [plan.forecast.service_impact.pct, supply.otif.pct]
    impact_range: plan.forecast.service_impact.pct: -1.0--4.0 pp
    levels: L1-L3

  - id: S-F3.4
    name: Re-Plan Discipline & Stability
    purpose: Reduce Unnecessary Re-Plans and Planning Churn
    status: active
    owner: Planning Excellence Lead
    trigger_kpis: [plan.replan.count]
    guardrail_kpis: [supply.otif.pct]
    outcome_kpis: [plan.replan.count, plan.forecast.accuracy.pct]
    impact_range: plan.replan.count: -20.0--50.0 %
    levels: L1-L3
```

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






