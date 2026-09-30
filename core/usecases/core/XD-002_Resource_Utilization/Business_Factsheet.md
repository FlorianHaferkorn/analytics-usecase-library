---
id: XD-002
factsheet_type: business
---

# XD-002 - Resource Utilization  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** XD-002
- **Domain:** Experience / Service
- **Business Owner:** Head of Customer Service / Workforce Management
- **KPI Owner:** Service Operations / Workforce Planning
- **Decision Owner:** CX/Service Leadership
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/experience.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/Experience.SemanticModel (domain model for XD-*).

---

## 1. Business Summary

**Purpose:** Optimize resource utilization and occupancy while protecting SLA and
customer experience.  
**Business Value:** Better staffing efficiency, reduced overtime/shrinkage costs,
and controlled backlog without SLA degradation.  
**Out of Scope:** Detailed SLA performance drivers (XD-001); sales pipeline; field
service dispatching.

---

## 2. Core Business Questions

- What are utilization and occupancy by channel/queue/region vs targets?
- How do overtime and shrinkage affect SLA attainment and backlog?
- Where do staffing imbalances create SLA risk or idle capacity?
- Which actions improve utilization without harming quality?

**Example Query Patterns (optional):**

- "Which queues have utilization below target and SLA/backlog risk?"
- "Where is overtime rising while shrinkage is high?"

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| KPI-SVC-009 | Strategic |
| KPI-SVC-010 | Influencing |
| KPI-SVC-004 | Influencing |
| KPI-SVC-011 | Influencing |
| KPI-SVC-012 | Influencing |
| KPI-SVC-007 | Influencing |
| KPI-SVC-013 | Influencing |

**Action Codes:** X-R2.1, X-R2.2, X-R2.3, X-R2.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Utilization %** (`KPI-SVC-009`) → **ISO 22400-2 UE** (partial): Utilization (productive / paid time) parallels ISO 22400-2 Utilization efficiency UE, but this KPI is applied to a contact-centre workforce, not equipment.
- **Occupancy %** (`KPI-SVC-010`) → **ISO 22400-2** (none): Occupancy ((Talk+Wrap)/(Talk+Wrap+Idle)) is a contact-centre workforce metric governed by the COPC CX Standard / contact-centre WFM, not ISO 22400-2 manufacturing operations.
- **SLA Attainment %** (`KPI-SVC-004`) → **ISO/IEC 20000-1 8.3.3** (partial): ISO/IEC 20000-1:2018 clause 8.3.3 (Service level management) requires documented SLAs and monitoring of performance against agreed service-level targets.
- **Overtime %** (`KPI-SVC-011`) → **ISO 22400-2** (none): Overtime share is a workforce-management metric (COPC CX Standard / WFM), not an ISO 22400-2 operations KPI.
- **Shrinkage %** (`KPI-SVC-012`) → **ISO 22400-2** (none): Shrinkage (non-productive / paid time) is a contact-centre WFM metric (COPC CX Standard), not ISO 22400-2.
- **Backlog Count** (`KPI-SVC-007`) → **ISO/IEC 20000-1 8.6.1** (partial): Open-case backlog is an operational measure of the ISO/IEC 20000-1 resolution & fulfilment processes (8.6.1 incident / 8.6.2 service request).
- **Tickets Created Count** (`KPI-SVC-013`) → **ISO/IEC 20000-1 8.6.1** (none): Raw created-ticket count is an incident/service-request volume element (ISO/IEC 20000-1 8.6.1/8.6.2), not a named ISO KPI.

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Utilization %  
- Occupancy %  
- Overtime %  
- Shrinkage %  
- SLA % / Backlog Count  

### 5.2 30-Second Layer (Main Visuals)

- **Utilization vs Band by Queue**
  - Visual Type: Column
  - X-Axis: dim_org[Queue]
  - Y-Axis: [Utilization %], Band
  - Segment: Channel/Region
  - Default Filter: Current month
  - Notes: Core ranking

- **Occupancy vs Band**
  - Visual Type: Column
  - X-Axis: dim_org[Queue]
  - Y-Axis: [Occupancy %], Band
  - Segment: Channel/Region
  - Default Filter: Current month
  - Notes: Balance view

- **Overtime & Shrinkage Trend**
  - Visual Type: Line
  - X-Axis: dim_date[Week]
  - Y-Axis: [Overtime %], [Shrinkage %]
  - Segment: Region/Channel
  - Default Filter: L12W
  - Notes: Capacity health

- **SLA vs Backlog**
  - Visual Type: Scatter
  - X-Axis: [SLA %]
  - Y-Axis: [Backlog Count]
  - Segment: Queue/Region
  - Default Filter: Current quarter
  - Notes: Service risk

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Region / Channel / Queue  
- Agent Group / Skill (if available)  

---

### 5.4 300-Second Layer (Diagnostics)

- Queue- and agent-group-level workforce table with utilization, occupancy, overtime, shrinkage, and SLA context.
- Capacity imbalance view that separates demand surge from structural shrinkage or routing problems.
- Action panel routing for utilization orchestration, capacity reallocation, shrinkage control, or overtime containment.

## 6. Data Requirements Summary

- Required facts: workforce-management time records plus support-case volume and backlog context.
- Required dimensions: date, organization, queue, and agent-group attributes where available.
- Required grain: agent_day with queue/day roll-up for trend and balancing views.
- Required time range: 12 to 24 months history.
- Required slicers: Date, Region/Channel/Queue, Agent Group or Skill.

---

## 7. Dependencies, Assumptions & Constraints

- WFM data includes work/idle/wrap, overtime, shrinkage; SLA/backlog
  available from cases.
- Target bands defined for utilization/occupancy; exclusions for
  training/ramp-up.
- OneLake canonical dims used (dim_date, dim_org, security_user_org).
- Data latency =24h.

---

## 8. Success Criteria

- **Benchmark Targets (world-class reference):** Defend utilization/occupancy
  within a 75-85% sustainable band — above ~85% quality, SLA and agent
  sustainability degrade (burnout/attrition risk, SQM; Kingman queueing law);
  professional-services billable optimum ~75% (SPI Research); overtime < 8%
  (X-R2.4 L1) and structural shrinkage < 25% (X-R2.3 L1). Utilization is a band
  to defend, not a number to maximise.
- Impact: Utilization/occupancy within bands; overtime/shrinkage reduced; SLA
  stable/improved; backlog controlled.  
- Adoption: Used in weekly WFM/service ops reviews; action codes triggered with
  <5% false positives.  
- Quality: KPI definitions consistent across XD-001/002; reconciled to source
  totals.  
- Decision Frequency: Weekly and daily staffing reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Overdriving utilization causing quality decline.  
- Misclassifying shrinkage leading to wrong capacity view.  
- Ignoring seasonality causing false alarms on utilization/occupancy.  



## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: Low Utilization Despite High Demand

**Situation:** Resource utilization is 62% against a 78% target, yet ticket backlog is growing. Occupancy rate is 71% but shrinkage (training, meetings, system downtime) has increased to 22%.

**Decision question:** Is the utilization gap driven by excessive non-productive time, scheduling inefficiency, or skill mismatch (agents available but not qualified for queued work)?

**Who decides:** Workforce Planning Lead + Operations Manager.

**Consequence of inaction:** Understaffed queues grow while available agents sit in non-productive activities; overtime costs spike to compensate.

**Action Code triggered:** X-R2.1 (Utilization Recovery) — activates shrinkage decomposition and schedule adherence analysis.

### Scenario B: Overtime Spike with Stable Headcount

**Situation:** Overtime rate jumped to 18% (target <8%). Headcount is unchanged, but volume per agent increased 12% due to a product launch. SLA is at risk.

**Decision question:** Is this a temporary surge requiring short-term overtime, or does the volume step-change require permanent capacity adjustment?

**Who decides:** Workforce Planning Lead + Service Director.

**Consequence of inaction:** Sustained overtime degrades agent well-being, increases attrition, and costs 1.5x base rate.

**Action Code triggered:** X-R2.2 (Capacity Adjustment) — activates volume trend analysis and capacity model re-run.
