---
id: SCM-001
factsheet_type: business
---

# SCM-001 - Inventory Performance  

## Business Factsheet

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
    kpi_catalog_id: Efficiency
    name: Days in Inventory (DIO)
    purpose: Working capital efficiency
    agg: avg

  - id: inv.turnover
    name: Inventory Turnover
    purpose: Velocity
    agg: avg

  - id: inv.stockout.pct
    name: Stockout Rate %
    purpose: Service risk
    agg: avg

  - id: supply.otif.pct
    name: OTIF %
    purpose: Service level fulfillment
    agg: avg

  - id: inv.obsolete.pct
    name: Obsolete Inventory %
    purpose: Write-off risk
    agg: avg

  - id: plan.forecast.accuracy.pct
    name: Forecast Accuracy %
    purpose: Planning quality (units-based forecast)
    agg: avg

  - id: sales.units
    name: Sales Units
    purpose: Demand signal
    agg: sum
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: S-I1.1
    name: Inventory Orchestration
    purpose: Coordinate Inventory Levers Without Service Degradation
    status: active
    owner: Head of Supply Chain
    trigger_kpis: [inv.dio.days, inv.stockout.pct]
    guardrail_kpis: [supply.otif.pct]
    outcome_kpis: [inv.dio.days]
    impact_range: inv.dio.days: -5.0--15.0 days
    levels: L1-L3

  - id: S-I1.2
    name: Inventory Rightsizing
    purpose: Reduce Excess Inventory While Protecting Service
    status: active
    owner: Inventory Manager
    trigger_kpis: [inv.dio.days]
    guardrail_kpis: [inv.stockout.pct, supply.otif.pct]
    outcome_kpis: [inv.dio.days, inv.turnover]
    impact_range: inv.dio.days: -10.0--30.0 days
    levels: L1-L3

  - id: S-I1.3
    name: Stockout Prevention
    purpose: Prevent Stockouts and Protect OTIF
    status: active
    owner: Supply Planner
    trigger_kpis: [inv.stockout.pct]
    guardrail_kpis: [inv.dio.days]
    outcome_kpis: [inv.stockout.pct, supply.otif.pct]
    impact_range: inv.stockout.pct: -1.0--5.0 pp
    levels: L1-L3

  - id: S-I1.4
    name: Obsolescence & Excess Reduction
    purpose: Prevent and Reduce Obsolete and Excess Stock
    status: active
    owner: Inventory Controller
    trigger_kpis: [inv.obsolete.pct]
    guardrail_kpis: [inv.stockout.pct]
    outcome_kpis: [inv.obsolete.pct, inv.dio.days]
    impact_range: inv.obsolete.pct: -2.0--8.0 pp
    levels: L1-L3

  - id: S-I1.5
    name: Forecast & Planning Stabilisation
    purpose: Stabilise Planning Processes Driving Inventory Imbalance
    status: active
    owner: Head of Demand Planning
    trigger_kpis: [plan.forecast.accuracy.pct]
    guardrail_kpis: [inv.dio.days]
    outcome_kpis: [plan.forecast.accuracy.pct]
    impact_range: plan.forecast.accuracy.pct: 5.0-15.0 pp
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- DIO (days)  
- Inventory Turnover (x)  
- Stockout Rate %  
- OTIF %  
- Obsolete Inventory %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| DIO vs Target by Location/Category | Column | dim_org[Location] | [DIO], [Target] | Category | Current quarter | Core ranking |
| Stockout & OTIF Trend | Line | dim_date[Week] | [Stockout %], [OTIF %] | Location/Channel | L12W | Service stability |
| Obsolete Inventory by Category | Bar (horizontal) | dim_product[Category] | [Obsolete %] | Location | Current quarter | Excess risk |
| Forecast Accuracy vs DIO | Scatter | [Forecast Accuracy %] | [DIO] | Category | Current quarter | Planning impact |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Location / DC / Channel  
- Category / Product  
- ABC/XYZ (if available)

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

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

## 7. Dependencies, Assumptions & Constraints

- COGS/actuals available to compute DIO/turnover; inventory snapshots consistent.
- Stockout and OTIF flags available; forecast and actual aligned by SKU/location/time.
- Obsolescence flagged; ABC/XYZ classification optional but recommended.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Success Criteria

- Impact: Lower DIO/raise turnover to targets; reduce stockouts and OTIF misses; reduce obsolete %.  
- Adoption: Used in monthly S&OP/inventory reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source totals.  
- Decision Frequency: Monthly S&OP and weekly inventory reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misstated DIO if COGS or inventory snapshots misaligned.  
- Stockout flags incomplete, underreporting availability risk.  
- Forecast accuracy misread without considering promotions or launches.  







