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
- **Related Data Contract:** core/data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/SupplyChain.SemanticModel (domain model for SCM-*).

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

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| supply.otif.pct | Strategic |
| supply.on_time.pct | Influencing |
| supply.in_full.pct | Influencing |
| supply.stockout_impact.pct | Influencing |
| supply.penalty.amount | Influencing |
| supply.expedite.amount | Supporting |
| order.lines | Supporting |
| shipments.count | Supporting |

**Action Codes:** S-R2.1, S-R2.2, S-R2.3, S-R2.4, S-R2.5

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- OTIF %  
- On-Time %  
- In-Full %  
- Stockout Impact %  
- Penalty Amount / Expedite Cost  

### 5.2 30-Second Layer (Main Visuals)

- **OTIF vs Target by Route/Location**
  - Visual Type: Column
  - X-Axis: dim_lane[Origin]
  - Y-Axis: [OTIF %], [Target]
  - Segment: dim_lane[Destination]
  - Default Filter: Current quarter
  - Notes: Core ranking

- **On-Time vs In-Full Components**
  - Visual Type: Column clustered
  - X-Axis: dim_lane[Origin]
  - Y-Axis: [On-Time %], [In-Full %]
  - Segment: dim_lane[Destination]
  - Default Filter: Current quarter
  - Notes: Component view

- **Penalty & Expedite Cost by Customer/Channel**
  - Visual Type: Bar (horizontal)
  - X-Axis: dim_org[Customer]
  - Y-Axis: [Penalty Amount], [Expedite Cost]
  - Segment: dim_org[Channel]
  - Default Filter: Current quarter
  - Notes: Cost impact

- **Stockout Impact Trend**
  - Visual Type: Line
  - X-Axis: dim_date[Week]
  - Y-Axis: [Stockout Impact %]
  - Segment: dim_org[Location]
  - Default Filter: L12W
  - Notes: Service stability

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Origin / Destination / Location
- Customer / Channel / Region
- Product / Category (if relevant)  

---

### 5.4 300-Second Layer (Diagnostics)

- OTIF gap decomposition by supplier, lane, and customer with absolute shipment count and relative contribution to the on-time and in-full shortfall vs SLA target.
- Penalty and expedite guardrail table linking OTIF %, stockout impact %, and penalty/expedite cost to the specific supplier/lane clusters that trigger S-R2.1 (supplier escalation), S-R2.2 (route optimization), or S-R2.3 (buffer stock adjustment).
- Top-N suppliers and lanes with the worst OTIF and highest penalty costs, including the last 3 monthly observations to separate seasonal disruptions from systemic delivery failures.

---

## 6. Data Requirements Summary

- Required facts: fact_fulfillment and fact_stockout, with fact_forecast only where planning-driven service misses need explanation.
- Required dimensions: dim_date, dim_org, optional dim_product, dim_lane where route modeling exists, and security_user_org.
- Required grain: order for OTIF and service-cost signals, with location_sku_day for stockout impact analysis.
- Required time range: 12-24 months history.
- Required slicers: Date, Origin/Destination/Location, Customer/Channel/Region, Product/Category.

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

**Benchmark Targets (grounded):**

- **OTIF ≥ 95%** for best-in-class delivery reliability; **98%** for
  retail/contract OTIF compliance programs (e.g., Walmart OTIF). SCOR superior
  is ~96%, advantage 90%, median 85%.
- **On-Time ≥ 97%** (best-in-class delivery reliability, SCOR/CSCMP).
- **In-Full ≥ 98%** (SCOR Orders Delivered In Full, superior range).
- **Stockout impact < 2%** world-class (< 5% acceptable).

> **Grain note:** OTIF can be measured at **line grain** (each order line scored
> independently) or **order grain** (the whole order fails if any line is late or
> short). Order-level OTIF is almost always lower; the grain must be fixed and
> stated explicitly before comparing to a customer's program target.

---

## 9. Risks & Wrong Interpretations (Short)

- Misapplied force majeure exclusions inflating OTIF.
- Missing penalty/expedite capture understates cost.
- Stockout impact misread if demand not captured consistently.
- **OTIF is multiplicative: OTIF = On-Time × In-Full.** Reading aggregate OTIF
  without the component split hides whether the gap is a transport problem
  (On-Time) or an availability problem (In-Full) — e.g., 90% OTIF can be 97%
  On-Time × 93% In-Full or 93% On-Time × 97% In-Full, each demanding a different
  fix. Always read OTIF alongside its two components.
- **Expedite masking:** OTIF held at target while expedite cost rises is not
  reliability — it is structural unreliability hidden by premium freight at
  penalty/recovery cost. The recovered margin may be negative. Read OTIF
  alongside expedite and penalty cost, never in isolation.
- **Line-level vs order-level grain ambiguity:** A single short or late line
  breaks the whole order under order-level (and retailer PO-line) accounting, so
  order-level OTIF is almost always lower than line-level. Comparing a line-level
  internal figure against an order/PO-line program target understates exposure;
  the grain must be fixed and stated.

---

## 10. Typical Decision Scenarios

### Scenario A: OTIF Drop Driven by In-Full Failures on Key Customer

**Situation:** OTIF has dropped from 94.2% to 87.6% over 4 weeks. The OT/IF split shows: On-Time is 97.1% (stable), but In-Full has dropped to 90.3%. The concentration analysis shows 65% of In-Full failures come from a single large retail customer in the West region.

**Decision question:** Is the In-Full failure caused by short pick (warehouse capacity), by procurement shortfall (supplier late delivery), or by a demand spike not covered by safety stock?

**Who decides:** Supply Chain Controlling Lead + Warehouse Manager + Procurement.

**Consequence of inaction:** The customer's OTIF contract threshold is 92%. Below 90.3% for 2 consecutive weeks, penalties of €35K/week are triggered. Expedite costs are already +€18K vs budget.

**Action Code triggered:** S-R2.1 (OTIF Orchestration) — activates root cause split by OT vs IF failure type and customer exposure quantification.

### Scenario B: Penalty Amount Trend Requires Structural Fix

**Situation:** Penalty amounts have been rising for 3 consecutive months: €8K → €22K → €51K. The issue is persistent with 3 different customers across 2 major route-location combinations. The pattern does not suggest a single root cause.

**Decision question:** Is this a systemic route and site execution issue or a systemic planning and buffer issue that makes the company structurally exposed?

**Who decides:** Head of Supply Chain + Supply Chain Controlling (DEC-SPINE-SCM-OTIF, RequiredIntervention level).

**Consequence of inaction:** At the current penalty trajectory, full-year penalty exposure is €400K+. More critically: 3 customers are approaching the OTIF level that triggers contract review clauses.

**Action Code triggered:** S-R2.2 (Fulfillment & Transport Stabilisation) + S-R2.3 (In-Full & Stockout Impact Reduction).

### Scenario C: Expedite Cost Spike Following Demand Surge

**Situation:** A promotional event generated 35% more demand than forecast. The OTIF system flags 480 orders as at-risk of In-Full failure. The Operations team activates air freight to cover the shortfall. Expedite costs hit €95K in a single week.

**Decision question:** Was the demand surge foreseeable? Is the expedite cost justified by the margin of the orders rescued vs the penalty + lost sales alternative?

**Who decides:** Supply Chain + Commercial (cross-domain).

**Consequence of inaction:** Expedite spend can offset the promotional uplift margin. This scenario triggers the `when_not_to_act` review: if the demand surge was from an active promotion, DEC-SPINE-SCM-FORECAST requires S&OP review before structural forecast adjustment.

**Action Code triggered:** S-R2.4 (Penalty & Expedite Cost Control) — activates cost-benefit analysis and service-cost containment, with SCM-003 handoff if the root cause is forecast-driven.

---



