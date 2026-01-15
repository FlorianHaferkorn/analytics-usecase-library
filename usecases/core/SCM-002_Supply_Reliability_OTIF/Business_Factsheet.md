---
id: SCM-002
factsheet_type: business
---

# SCM-002 - Supply Reliability & OTIF  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-002
- **Domain:** Supply Chain
- **Business Owner:** Head of Supply Chain / Logistics
- **KPI Owner:** Supply Chain Controlling / Logistics Performance
- **Decision Owner:** Supply Chain Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Improve supply reliability by raising On-Time In-Full (OTIF), reducing stockout impact, and lowering penalties/expedites.  
**Business Value:** Higher service level, fewer penalties/expedites, better customer satisfaction, and more stable inventory.  
**Out of Scope:** Inventory optimization specifics (SCM-001); forecast accuracy deep dive (SCM-003); promo effects (COM-004).

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
    name: OTIF %
    purpose: Service level delivered
    definition_short: On-Time In-Full orders / total orders
    unit: %
    grain: order
    agg: avg
    target: = 97-99%
    interpretation: Low OTIF signals service failure
    lineage: fact_fulfillment[OTIF Flag]

  - id: supply.on_time.pct
    name: On-Time %
    purpose: Timeliness
    definition_short: On-time deliveries / total deliveries
    unit: %
    grain: shipment
    agg: avg
    target: = 97-99%
    interpretation: Low on-time signals delay issues
    lineage: fact_fulfillment[On-Time Flag]

  - id: supply.in_full.pct
    name: In-Full %
    purpose: Completeness
    definition_short: In-full deliveries / total deliveries
    unit: %
    grain: shipment
    agg: avg
    target: = 97-99%
    interpretation: Low in-full signals quantity issues
    lineage: fact_fulfillment[In-Full Flag]

  - id: supply.stockout_impact.pct
    name: Stockout Impact %
    purpose: Service loss
    definition_short: Lost demand due to stockout / total demand
    unit: %
    grain: location_sku_day
    agg: avg
    target: = target
    interpretation: High impact shows service gaps
    lineage: fact_stockout[Lost Demand], fact_stockout[Demand]

  - id: supply.penalty.amount
    name: Penalty Amount
    purpose: Financial impact of service failures
    definition_short: Penalties incurred for service misses
    unit: EUR
    grain: order
    agg: sum
    target: Reduce to target
    interpretation: High penalties indicate systemic issues
    lineage: fact_fulfillment[Penalty Amount]

  - id: supply.expedite.amount
    name: Expedite Cost Amount
    purpose: Cost to recover service
    definition_short: Additional cost for expedited shipping
    unit: EUR
    grain: shipment
    agg: sum
    target: Reduce to target
    interpretation: High expedites show plan/fulfillment gaps
    lineage: fact_fulfillment[Expedite Cost]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag lanes/products with OTIF below target for 2 consecutive periods.
- Flag high stockout impact % by channel/location.
- Flag penalties/expedites above materiality thresholds.
- Identify on-time or in-full components failing most.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: supply.otif.pct
    condition: <
    threshold: otif_target
    scope: lane_dc_channel
    exclusion: force_majeure
    action_code: O2

  - kpi: supply.stockout_impact.pct
    condition: >
    threshold: stockout_target
    scope: location_channel
    exclusion: planned_outages
    action_code: I2

  - kpi: supply.penalty.amount
    condition: >
    threshold: penalty_materiality
    scope: customer_channel
    exclusion: negotiated_penalties
    action_code: D1

  - kpi: supply.expedite.amount
    condition: >
    threshold: expedite_materiality
    scope: lane_dc_channel
    exclusion: crisis
    action_code: O2
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| O2 | Operations Stabilisation | supply.otif.pct < target OR expedite/penalty high | Fix root causes (supplier, transport, DC process), re-sequence orders | Improve OTIF %, reduce expedites/penalties | L2 | Supply/Logistics |
| I2 | Stockout Prevention | supply.stockout_impact.pct > target | Improve safety stock/replenishment, expedite critical items | Reduce stockout impact, improve OTIF | L2 | Supply Planning |
| D1 | Cost Take-Out | Penalties/expedites above materiality | Reduce penalties/expedites via SLA adherence and planning fixes | Lower costs, improve service stability | L2 | Procurement / Logistics |
| O2 (Planning variant) | Forecast/process stabilisation | plan/actual variance causing service misses | Improve plan, align supply with demand | Improve OTIF, reduce expedites | L2 | S&OP |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- OTIF %  
- On-Time %  
- In-Full %  
- Stockout Impact %  
- Penalty Amount / Expedite Cost  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| OTIF vs Target by Lane/DC | Column | dim_lane[Lane/DC] | [OTIF %], [Target] | Channel | Current quarter | Core ranking |
| On-Time vs In-Full Components | Column clustered | dim_lane[Lane/DC] | [On-Time %], [In-Full %] | Channel | Current quarter | Component view |
| Penalty & Expedite Cost by Customer/Channel | Bar (horizontal) | dim_org[Customer/Channel] | [Penalty Amount], [Expedite Cost] | Region | Current quarter | Cost impact |
| Stockout Impact Trend | Line | dim_date[Week] | [Stockout Impact %] | Location/Channel | L12W | Service stability |

### 6.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Lane / DC / Channel  
- Customer / Region  
- Product / Category (if relevant)  

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

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
required_grain: order for OTIF/penalties; location_sku_day for stockouts
required_time_range: 12-24 months history
required_slicers: Date, Lane/DC/Channel, Customer/Region, Product/Category (optional)
```

---

## 8. Dependencies, Assumptions & Constraints

- OTIF flags consistent; on-time and in-full flags available; penalties/expedites captured.
- Stockout impact measured; lane/DC structure available.
- Forecast/plan variance may be needed to explain service misses.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org); dim_lane optional if defined.

---

## 9. Success Criteria

- Impact: OTIF raised to target; penalties/expedites reduced; stockout impact reduced.  
- Adoption: Used in weekly supply/logistics reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source totals.  
- Decision Frequency: Weekly supply/logistics review.

---

## 10. Risks & Wrong Interpretations (Short)

- Misapplied force majeure exclusions inflating OTIF.  
- Missing penalty/expedite capture understates cost.  
- Stockout impact misread if demand not captured consistently.  


