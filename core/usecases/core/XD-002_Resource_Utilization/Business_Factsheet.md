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
- **Related Data Contract:** core/core/core/data_contracts/domains/experience.yaml
- **Related Semantic Model:** core/core/core/semantic_models/core_action_ready/model_definition.yaml

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

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


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

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_wfm (work/idle/wrap/overtime/shrinkage)

  - fact_cases (SLA, backlog)
required_dimensions:

  - dim_date

  - dim_org (region/channel/queue)

  - dim_queue (if separate)

  - security_user_org
required_grain: >
  agent_day or queue_day; week/month for trends
required_time_range: 12-24 months history
required_slicers: >
  Date, Region/Channel/Queue, Agent Group/Skill (if available)
```

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


