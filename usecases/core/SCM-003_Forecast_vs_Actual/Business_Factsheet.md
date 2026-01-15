---
id: SCM-003
factsheet_type: business
---

# SCM-003 - Forecast vs Actual  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-003
- **Domain:** Supply Chain / Planning
- **Business Owner:** Head of Demand Planning / S&OP Lead
- **KPI Owner:** Planning Excellence / Controlling
- **Decision Owner:** S&OP Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

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
    name: Forecast Accuracy %
    purpose: Planning quality (units-based forecast)
    definition_short: 1 - |Forecast Units - Actual Units| / Actual Units
    unit: %
    grain: sku_month
    agg: avg
    target: % target
    interpretation: Low accuracy drives excess/stockouts; units-based (not revenue)
    lineage: fact_forecast[Forecast], fact_sales[Actual]

  - id: plan.forecast.mape.pct
    name: MAPE %
    purpose: Error magnitude (units-based forecast)
    definition_short: Mean absolute % error of Forecast Units vs Actual Units
    unit: %
    grain: sku_month
    agg: avg
    target: % target
    interpretation: High MAPE indicates poor forecast quality; units-based (not revenue)
    lineage: fact_forecast vs fact_sales

  - id: plan.forecast.bias.pct
    name: Forecast Bias %
    purpose: Direction of error (units-based forecast)
    definition_short: (Forecast Units - Actual Units) / Actual Units
    unit: %
    grain: sku_month
    agg: avg
    target: Near 0 (within bands)
    interpretation: Positive bias = over-forecast; negative = under-forecast; units-based (not revenue)
    lineage: fact_forecast vs fact_sales

  - id: plan.forecast.service_impact.pct
    name: Service Impact %
    purpose: Service effect of forecast error (units-based)
    definition_short: Portion of service misses attributable to forecast error (units-based)
    unit: %
    grain: sku_month
    agg: avg
    target: Minimize
    interpretation: High impact shows planning as root cause; units-based (not revenue)
    lineage: linkage between forecast error and OTIF/stockout

  - id: plan.replan.count
    name: Re-Plan Count
    purpose: Planning stability
    definition_short: Number of re-plans within period
    unit: count
    grain: month
    agg: sum
    target: Reduce vs baseline
    interpretation: Frequent re-plans indicate unstable process
    lineage: planning system logs

  - id: order.lines
    name: Order Lines Count
    purpose: Demand volume
    definition_short: Count of order line items
    unit: count
    grain: order_line
    agg: sum
    target: Meet plan
    interpretation: Volume context for forecast accuracy
    lineage: fact_order_lines[Order Line ID]

  - id: plans.count
    name: Plans Count
    purpose: Planning activity
    definition_short: Count of plan records or plan versions
    unit: count
    grain: month
    agg: sum
    target: Stable over time
    interpretation: Higher counts indicate more planning cycles
    lineage: fact_plan[Plan ID]

  - id: sales.units
    name: Sales Units
    purpose: Actuals baseline
    definition_short: Units sold in the period
    unit: units
    grain: sku_month
    agg: sum
    target: Meet plan
    interpretation: Actual volume for forecast comparison
    lineage: fact_sales[Sales Units]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action codes.

### 4.1 Logic Description

- Flag accuracy below target and bias outside bands for priority SKUs/locations.
- Flag high service impact from forecast error.
- Flag frequent re-plans beyond threshold.

### 4.2 Formal Action Code Rules (Machine-Readable)

```yaml
action_codes:

  - kpi: plan.forecast.accuracy.pct
    condition: <
    threshold: accuracy_target
    scope: sku_location
    exclusion: launch_items
    action_code: S-F3.1

  - kpi: plan.forecast.bias.pct
    condition: outside
    threshold: [-0.05, 0.05]
    scope: sku_location
    exclusion: launch_items
    action_code: S-F3.2

  - kpi: plan.forecast.service_impact.pct
    condition: >
    threshold: impact_target
    scope: sku_location
    exclusion: force_majeure
    action_code: S-F3.3

  - kpi: plan.replan.count
    condition: >
    threshold: replan_limit
    scope: month
    exclusion: major events
    action_code: S-F3.1
```

---

## 5. Action Codes (Mandatory)

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| S-F3.1 | Forecast Quality Orchestration | plan.forecast.accuracy.pct < accuracy_target; plan.replan.count > replan_limit | Select dominant forecast-quality lever per SKU/location (bias correction, containment, replan discipline); Sequence corrective actions to avoid parallel, conflicting planning fixes | plan.forecast.accuracy.pct +5.0-12.0 pp (2-5 periods) | L1 | S&OP Leadership |
| S-F3.2 | Forecast Bias & Accuracy Correction | plan.forecast.bias.pct outside | Correct systematic over-/under-forecasting; Reduce forecast error via disciplined overrides and data hygiene | plan.forecast.accuracy.pct +4.0-10.0 pp (2-5 periods) | L2 | Demand Planning |
| S-F3.3 | Service Impact Containment | plan.forecast.service_impact.pct > impact_target | Contain service loss while forecast quality is being corrected; Prioritise short-term planning adjustments to protect OTIF | Impact: High | L1 | Supply Planning |

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Forecast Accuracy %  
- MAPE %  
- Bias %  
- Service Impact %  
- Re-Plan Count  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Accuracy vs Target by Category/Location | Column | dim_product[Category] | [Forecast Accuracy %] | Location/Channel | Current quarter | Core ranking |
| Bias Distribution | Column | dim_product[Category] | [Bias %] | Location | Current quarter | Highlight over/under |
| Service Impact Trend | Line | dim_date[Month] | [Service Impact %] | Channel | L12M | Service linkage |
| Re-Plan Count by Month | Column | dim_date[Month] | [Re-Plan Count] | Region | L12M | Stability |

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel / Location  
- Category / Product  
- ABC/XYZ (if available)

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- Forecast/actual aligned by SKU/location/time; promotions/launches flagged to avoid misinterpretation.
- Re-plan events captured; service impact link to OTIF/stockout available.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).
- Data latency =24h; plan versions stored.

---

## 9. Success Criteria

- Impact: Accuracy improves to target; bias within bands; reduced service impact; fewer re-plans.  
- Adoption: Used in monthly S&OP/planning reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source totals.  
- Decision Frequency: Monthly S&OP and weekly planning reviews.

---

## 10. Risks & Wrong Interpretations (Short)

- Misinterpreting bias/accuracy on launch or promo items.  
- Service impact overstated if OTIF/stockout not properly linked.  
- Re-plan counts misleading if process changes not tracked.  



