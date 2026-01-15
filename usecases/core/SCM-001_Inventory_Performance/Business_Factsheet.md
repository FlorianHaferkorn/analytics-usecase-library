---
id: SCM-001
factsheet_type: business
---

# SCM-001 - Inventory Performance  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-001
- **Domain:** Supply Chain
- **Business Owner:** COO / Head of Supply Chain
- **KPI Owner:** Supply Chain Controlling / Inventory Mgmt Lead
- **Decision Owner:** Supply Chain Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Optimize inventory by balancing availability (service level) and working capital, reducing excess, stockouts, and obsolescence.  
**Business Value:** Lower working capital, fewer stockouts, higher OTIF, and reduced write-offs.  
**Out of Scope:** Detailed demand planning algorithm tuning (SCM-003); promotion-specific effects (COM-004); transport cost optimization (OPS-018).

---

## 2. Core Business Questions

- Where are inventory days and turnover off target by location/channel/category?
- Which items drive stockouts and OTIF misses?
- Where is excess/obsolete inventory accumulating?
- Which actions reduce inventory without hurting service level?
- How does forecast accuracy impact inventory KPIs?

**Example Query Patterns (optional):**

- "Which DCs have DIO above target and stockout > target in the last 8 weeks?"
- "Where is forecast accuracy low and driving excess or stockouts?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: inv.dio.days
    name: Days in Inventory (DIO)
    purpose: Working capital efficiency
    definition_short: (Avg Inventory / COGS) x Days
    unit: days
    grain: location_sku_month
    agg: avg
    target: = target (e.g., category/location specific)
    interpretation: High DIO indicates excess inventory
    lineage: fact_inventory[Avg Inventory], fact_cogs[COGS]

  - id: inv.turnover
    name: Inventory Turnover
    purpose: Velocity
    definition_short: COGS / Avg Inventory
    unit: x
    grain: location_sku_month
    agg: avg
    target: = target
    interpretation: Low turnover indicates slow-moving stock
    lineage: fact_inventory[Avg Inventory], fact_cogs[COGS]

  - id: inv.stockout.pct
    name: Stockout Rate %
    purpose: Service risk
    definition_short: Stockout occurrences / demand occurrences
    unit: %
    grain: location_sku_day
    agg: avg
    target: = target
    interpretation: High rate signals availability issues
    lineage: fact_inventory[Stockout Flag], demand events

  - id: supply.otif.pct
    name: OTIF %
    purpose: Service level fulfillment
    definition_short: On-Time In-Full orders / total orders
    unit: %
    grain: order
    agg: avg
    target: = 97-99% (context)
    interpretation: Low OTIF reflects fulfillment issues
    lineage: fact_fulfillment[OTIF Flag]

  - id: inv.obsolete.pct
    name: Obsolete Inventory %
    purpose: Write-off risk
    definition_short: Obsolete stock / total stock
    unit: %
    grain: location_sku_month
    agg: avg
    target: = target
    interpretation: High obsolete % indicates aging/excess
    lineage: fact_inventory[Obsolete Stock], fact_inventory[Total Stock]

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
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag locations/categories with DIO above target and OTIF/stockout below target.
- Highlight obsolete inventory % above threshold.
- Flag forecast accuracy below target for items with excess or stockouts.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: inv.dio.days
    condition: >
    threshold: dio_target
    scope: location_category
    exclusion: new_items
    action_code: I1

  - kpi: inv.stockout.pct
    condition: >
    threshold: stockout_target
    scope: location_category
    exclusion: force_majeure
    action_code: I2

  - kpi: inv.obsolete.pct
    condition: >
    threshold: obsolete_target
    scope: location_category
    exclusion: end_of_life_planned
    action_code: D1

  - kpi: plan.forecast.accuracy.pct
    condition: <
    threshold: forecast_target
    scope: top_variance_skus
    exclusion: launch_items
    action_code: O2
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| I1 | Inventory Rightsizing | inv.dio.days > target | Reduce safety stock/lot sizes; clearance for excess | Lower DIO, improve turnover | L2 | Supply Planning |
| I2 | Stockout Prevention | inv.stockout.pct > target OR OTIF < target | Fix replenishment parameters, expedite shipments | Reduce stockouts, improve OTIF | L2 | Supply & Logistics |
| D1 | Cost Take-Out / Obsolescence | inv.obsolete.pct > target | Liquidate obsolete stock, prevent rebuys | Reduce obsolete %, DIO | L2 | Inventory Mgmt / Finance |
| O2 | Operations Stabilisation (Forecast/Process) | plan.forecast.accuracy.pct < target | Improve forecast, align plan with supply | Reduce variance-driven excess/stockouts | L2 | Demand/S&OP |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- DIO (days)  
- Inventory Turnover (x)  
- Stockout Rate %  
- OTIF %  
- Obsolete Inventory %  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| DIO vs Target by Location/Category | Column | dim_org[Location] | [DIO], [Target] | Category | Current quarter | Core ranking |
| Stockout & OTIF Trend | Line | dim_date[Week] | [Stockout %], [OTIF %] | Location/Channel | L12W | Service stability |
| Obsolete Inventory by Category | Bar (horizontal) | dim_product[Category] | [Obsolete %] | Location | Current quarter | Excess risk |
| Forecast Accuracy vs DIO | Scatter | [Forecast Accuracy %] | [DIO] | Category | Current quarter | Planning impact |

### 6.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Location / DC / Channel  
- Category / Product  
- ABC/XYZ (if available)

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

```yaml
required_facts:
  - fact_inventory
  - fact_cogs (or fact_sales for COGS proxy)
  - fact_fulfillment (OTIF)
  - fact_forecast
  - fact_sales (actuals for accuracy)
required_dimensions:
  - dim_date
  - dim_org (location/DC/channel)
  - dim_product
  - security_user_org
required_grain: location_sku_month for inventory; order for OTIF; day for stockouts
required_time_range: 12-24 months history
required_slicers: Date, Location/DC/Channel, Category/Product, ABC/XYZ
```

---

## 8. Dependencies, Assumptions & Constraints

- COGS/actuals available to compute DIO/turnover; inventory snapshots consistent.
- Stockout and OTIF flags available; forecast and actual aligned by SKU/location/time.
- Obsolescence flagged; ABC/XYZ classification optional but recommended.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 9. Success Criteria

- Impact: Lower DIO/raise turnover to targets; reduce stockouts and OTIF misses; reduce obsolete %.  
- Adoption: Used in monthly S&OP/inventory reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source totals.  
- Decision Frequency: Monthly S&OP and weekly inventory reviews.

---

## 10. Risks & Wrong Interpretations (Short)

- Misstated DIO if COGS or inventory snapshots misaligned.  
- Stockout flags incomplete, underreporting availability risk.  
- Forecast accuracy misread without considering promotions or launches.  




