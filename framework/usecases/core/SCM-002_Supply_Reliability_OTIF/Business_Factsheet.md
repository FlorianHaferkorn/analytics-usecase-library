---
id: SCM-002
factsheet_type: business
---

# SCM-002 - Supply Reliability & OTIF  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-002
- **Domain:** Supply Chain
- **Business Owner:** Head of Supply Chain / Logistics
- **KPI Owner:** Supply Chain Controlling / Logistics Performance
- **Decision Owner:** Supply Chain Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** framework/framework/framework/data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** framework/framework/framework/semantic_models/core_action_ready/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Improve supply reliability by raising On-Time In-Full (OTIF),
reducing stockout impact, and lowering penalties/expedites.  
**Business Value:** Higher service level, fewer penalties/expedites, better
customer satisfaction, and more stable inventory.  
**Out of Scope:** Inventory optimization specifics (SCM-001); forecast accuracy
deep dive (SCM-003); promo effects (COM-004).

---

## 2. Core Business Questions

- Where is OTIF below target by lane/DC/channel/product?
- What are the main drivers of late or incomplete deliveries?
- How much do stockouts, penalties, and expedites cost?
- Which corrective actions improve OTIF fastest without excessive cost?

**Example Query Patterns (optional):**

- "Which lanes have OTIF <97% in the last 8 weeks and what are the top delay reasons?"
- "What is the stockout impact and penalty cost by channel?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: supply.otif.pct
    kpi_catalog_id: Efficiency
    name: OTIF %
    purpose: Service level delivered
    agg: avg

  - id: supply.on_time.pct
    name: On-Time %
    purpose: Timeliness
    agg: avg

  - id: supply.in_full.pct
    name: In-Full %
    purpose: Completeness
    agg: avg

  - id: supply.stockout_impact.pct
    name: Stockout Impact %
    purpose: Service loss
    agg: avg

  - id: supply.penalty.amount
    name: Penalty Amount
    purpose: Financial impact of service failures
    agg: sum

  - id: supply.expedite.amount
    name: Expedite Cost Amount
    purpose: Cost to recover service
    agg: sum

  - id: order.lines
    name: Order Lines Count
    purpose: Volume context
    agg: sum

  - id: shipments.count
    name: Shipments Count
    purpose: Execution volume
    agg: sum
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: S-R2.1
    name: OTIF Orchestration
    purpose: Coordinate OTIF Improvement Levers Without Masking Root Causes
    status: active
    owner: Head of Supply Chain
    trigger_kpis: [supply.otif.pct, supply.expedite.amount]
    guardrail_kpis: [inv.dio.days]
    outcome_kpis: [supply.otif.pct]
    impact_range: supply.otif.pct: 1.0-4.0 pp
    levels: L1-L3

  - id: S-R2.2
    name: Fulfillment & Transport Stabilisation
    purpose: Stabilise On-Time Delivery Performance
    status: active
    owner: Logistics Manager
    trigger_kpis: [supply.on_time.pct]
    guardrail_kpis: [supply.expedite.amount]
    outcome_kpis: [supply.on_time.pct, supply.otif.pct]
    impact_range: supply.on_time.pct: 2.0-5.0 pp
    levels: L1-L3

  - id: S-R2.3
    name: In-Full & Stockout Impact Reduction
    purpose: Prevent Partial Deliveries and Lost Demand
    status: active
    owner: Supply Planner
    trigger_kpis: [supply.stockout_impact.pct]
    guardrail_kpis: [inv.dio.days]
    outcome_kpis: [supply.stockout_impact.pct, supply.in_full.pct]
    impact_range: supply.stockout_impact.pct: -1.0--4.0 pp
    levels: L1-L3

  - id: S-R2.4
    name: Penalty & Expedite Cost Control
    purpose: Reduce Avoidable Penalties and Expedite Spend Without Masking OTIF Issues
    status: active
    owner: Logistics Cost Manager
    trigger_kpis: [supply.penalty.amount, supply.expedite.amount]
    guardrail_kpis: [supply.otif.pct]
    outcome_kpis: [supply.penalty.amount, supply.expedite.amount]
    impact_range: supply.penalty.amount: -10.0--30.0 %
    levels: L1-L3

  - id: S-R2.5
    name: Planning & Execution Alignment
    purpose: Align Short-Term Plans with Operational Execution to Protect OTIF
    status: active
    owner: S&OP Lead
    trigger_kpis: [supply.otif.pct, supply.expedite.amount]
    guardrail_kpis: [inv.dio.days]
    outcome_kpis: [supply.otif.pct]
    impact_range: supply.otif.pct: 1.0-3.0 pp
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- OTIF %  
- On-Time %  
- In-Full %  
- Stockout Impact %  
- Penalty Amount / Expedite Cost  

### 5.2 30-Second Layer (Main Visuals)

- **OTIF vs Target by Lane/DC**
  - Visual Type: Column
  - X-Axis: dim_lane[Lane/DC]
  - Y-Axis: [OTIF %], [Target]
  - Segment: Channel
  - Default Filter: Current quarter
  - Notes: Core ranking

- **On-Time vs In-Full Components**
  - Visual Type: Column clustered
  - X-Axis: dim_lane[Lane/DC]
  - Y-Axis: [On-Time %], [In-Full %]
  - Segment: Channel
  - Default Filter: Current quarter
  - Notes: Component view

- **Penalty & Expedite Cost by Customer/Channel**
  - Visual Type: Bar (horizontal)
  - X-Axis: dim_org[Customer/Channel]
  - Y-Axis: [Penalty Amount], [Expedite Cost]
  - Segment: Region
  - Default Filter: Current quarter
  - Notes: Cost impact

- **Stockout Impact Trend**
  - Visual Type: Line
  - X-Axis: dim_date[Week]
  - Y-Axis: [Stockout Impact %]
  - Segment: Location/Channel
  - Default Filter: L12W
  - Notes: Service stability

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Lane / DC / Channel  
- Customer / Region  
- Product / Category (if relevant)  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_fulfillment (OTIF, penalties, expedites)

  - fact_stockout (stockout impact)

  - fact_forecast (variance drivers, if used)
required_dimensions:

  - dim_date

  - dim_org (customer/channel/DC)

  - dim_product (if needed)

  - dim_lane (if modeled for transport lanes)

  - security_user_org
required_grain: >
  order for OTIF/penalties; location_sku_day for stockouts
required_time_range: 12-24 months history
required_slicers: >
  Date, Lane/DC/Channel, Customer/Region, Product/Category (optional)
```

---

## 7. Dependencies, Assumptions & Constraints

- OTIF flags consistent; on-time and in-full flags available;
  penalties/expedites captured.
- Stockout impact measured; lane/DC structure available.
- Forecast/plan variance may be needed to explain service misses.
- OneLake canonical dims used (dim_date, dim_org, dim_product,
  security_user_org); dim_lane optional if defined.

---

## 8. Success Criteria

- Impact: OTIF raised to target; penalties/expedites reduced; stockout impact
  reduced.  
- Adoption: Used in weekly supply/logistics reviews; action codes triggered with
  <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source
  totals.  
- Decision Frequency: Weekly supply/logistics review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misapplied force majeure exclusions inflating OTIF.  
- Missing penalty/expedite capture understates cost.  
- Stockout impact misread if demand not captured consistently.  



