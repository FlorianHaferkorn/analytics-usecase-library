---
id: OPS-001
factsheet_type: business
---

# OPS-001 - Operations Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-001
- **Domain:** Operations
- **Business Owner:** COO / Plant Manager / Ops Excellence Lead
- **KPI Owner:** Operations Controlling / OEE Lead
- **Decision Owner:** Operations Leadership Team
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic
- **Related Data Contract:** core/data_contracts/domains/operations.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Operations.SemanticModel (domain model for OPS-*).

---

## 1. Business Summary

**Purpose:** Improve overall equipment effectiveness and throughput by addressing availability, performance, and quality losses.  
**Business Value:** Higher OEE, more stable throughput, reduced downtime, and better cost efficiency without additional CAPEX.  
**Out of Scope:** Predictive maintenance specifics (OPS-013); logistics/warehouse performance (OPS-011); detailed cost modeling (OPS-008).

---

## 2. Core Business Questions

- What is OEE and its components (availability, performance, quality) by line/plant?
- Where are the largest downtime and speed losses, and what are the top causes?
- How does throughput vary by shift, line, and product mix?
- Which targeted actions will lift OEE fastest with minimal risk?

**Example Query Patterns (optional):**

- "Which lines have availability < target in the last 4 weeks and what are the top 3 downtime reasons?"
- "Where is performance loss >5% vs standard for top products?"

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| ops.oee.pct | Strategic |
| ops.availability.pct | Influencing |
| ops.performance.pct | Influencing |
| ops.quality.pct | Influencing |
| ops.throughput.units | Supporting |
| ops.downtime.pct | Supporting |
| ops.planned_output.units | Supporting |

**Action Codes:** O-O1.1, O-O1.2, O-O1.3, O-O1.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- OEE %  
- Availability %  
- Performance %  
- Quality %  
- Downtime %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| OEE vs Target by Line | Column | dim_org[Line] | [OEE %], [Target] | Plant | Current month | Core ranking |
| Downtime by Cause | Bar (horizontal) | fact_ops[Cause] | [Downtime Minutes] | Line/Plant | Last 4 weeks | Pareto |
| Performance Loss vs Standard | Column | dim_org[Line] | [Performance %] | Shift | Last 4 weeks | Speed losses |
| Quality Trend | Line | dim_date[Week] | [Quality %] | Line/Plant | L12W | Stability view |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Category (if applicable)  

---

### 5.4 300-Second Layer (Diagnostics)

- OEE gap decomposition by line, shift, and cause category with absolute downtime minutes and relative contribution to the plant-level OEE shortfall vs target.
- Loss-type guardrail table linking availability loss, speed loss, and quality loss to the specific line/shift combinations that trigger O-O1.1 (performance recovery), O-O1.2 (availability recovery), O-O1.3 (changeover reduction), or O-O1.4 (quality containment).
- Top-N lines and assets with the largest OEE gaps, including the last 4 weekly observations to separate one-off disruptions from persistent structural losses.

---

## 6. Data Requirements Summary

- Required facts: fact_ops as the production-event backbone for runtime, downtime, output, good units, and scrap.
- Required dimensions: dim_date, dim_org, optional dim_product, and security_user_org.
- Required grain: line_day, with shift retained where available for operational execution.
- Required time range: 12-24 months history.
- Required slicers: Date, Plant/Line/Shift, Product/Category.

---

## 7. Dependencies, Assumptions & Constraints

- Standard cycle times and planned production time defined; changeovers classified.
- Downtime coded with cause categories; trial runs flagged.
- OneLake canonical dims used (dim_date, dim_org, security_user_org; dim_product optional).
- Data latency =24h; plan vs actual for throughput if used.

---

## 8. Success Criteria

- Impact: OEE uplift toward target; reduced downtime minutes; improved throughput vs plan.  
- Adoption: Used in weekly ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; KPI definitions consistent across ops UCs.  
- Decision Frequency: Weekly ops and daily tiered meetings.

---

## 9. Risks & Wrong Interpretations (Short)

- Misclassified planned vs unplanned downtime distorts availability.
- Ignoring product mix/standard rate differences when reading performance %.
- Quality issues masked if rework/scrap not fully captured.

---

## 10. Typical Decision Scenarios

### Scenario A: OEE Drop Below Target — Availability as Dominant Cause

**Situation:** Line 3 OEE has dropped from 78% to 67% over 3 weeks. The OEE bridge shows: Availability −8pp (dominant), Performance −2pp, Quality −1pp. Availability loss is concentrated in 2 failure events on the same asset.

**Decision question:** Is this an asset-specific reliability issue (MTBF deteriorating) or a maintenance compliance issue (PM overdue)?

**Who decides:** Operations Controlling / OEE Lead + Maintenance Manager.

**Consequence of inaction:** At €2,000/hour production value, 11pp OEE drop on a 16h/day line = ~€28,000 daily lost output. The DEC-SPINE-OPS-ASSET spine escalates to RequiredIntervention after 3 shifts.

**Action Code triggered:** O-A2.1 (Asset Reliability Recovery) — activates asset inspection schedule and MTBF root cause analysis.

### Scenario B: Performance Loss Without Downtime Events

**Situation:** OEE is 72%, but Availability is at 94% and Quality at 97%. The Performance component is 79% — significantly below the 92% standard. Operators report no downtime events but acknowledge running at reduced speed due to "product quality concerns."

**Decision question:** Is the speed reduction an official decision (quality qualification run per `when_not_to_act`) or an unauthorized operator adjustment?

**Who decides:** Operations Controlling / OEE Lead + Shift Lead + Quality Manager.

**Consequence of inaction:** Systematic speed reduction of 13pp is not captured in downtime and will not trigger maintenance or quality corrective actions. The loss becomes invisible.

**Action Code triggered:** O-O1.1 (Performance Recovery) — activates standard rate review and speed authorization audit.

### Scenario C: Quality % Drop Triggering Scrap Cost Alert

**Situation:** First Pass Yield has dropped from 97.2% to 94.1% on Product Line A over 5 consecutive shifts. Scrap rate is up 3pp. COPQ for the month is on track to exceed budget by 18%.

**Decision question:** Is the yield drop caused by a raw material issue (batch-specific), a process parameter drift, or an equipment degradation?

**Who decides:** Quality Manager + Operations BI Lead.

**Consequence of inaction:** 3pp scrap rate on 200,000 units/day = 6,000 scrapped units/day. At €4/unit COGS = €24,000 daily COPQ. DEC-SPINE-OPS-QUALITY escalates to RequiredIntervention within 1 shift if pattern persists.

**Action Code triggered:** O-Q3.1 (Quality Root Cause) — activates defect pareto analysis and containment review.

---





