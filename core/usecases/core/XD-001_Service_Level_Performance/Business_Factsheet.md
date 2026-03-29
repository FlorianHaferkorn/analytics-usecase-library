---
id: XD-001
factsheet_type: business
---

# XD-001 - Service Level Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** XD-001
- **Domain:** Experience / Service
- **Business Owner:** Head of Customer Service / CX Lead
- **KPI Owner:** Service Operations / CX Analytics
- **Decision Owner:** CX/Service Leadership
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/experience.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Experience.SemanticModel (domain model for XD-*).

---

## 1. Business Summary

**Purpose:** Improve service level by monitoring SLA attainment, first contact
resolution, handling time, backlog, and escalation.  
**Business Value:** Higher customer satisfaction, lower cost-to-serve, reduced
escalations and backlog.  
**Out of Scope:** Sales pipeline (COM-010); marketing journey analytics; field
service parts/ops (scoped separately).

---

## 2. Core Business Questions

- Where is SLA attainment below target by channel/region/queue?
- How do FCR and AHT trend, and how do they affect SLA and NPS?
- Which queues/regions drive backlog and escalations?
- Which actions improve service level fastest without quality loss?

**Example Query Patterns (optional):**

- "Which queues have SLA < target in the last 4 weeks and rising backlog?"
- "How does FCR vs AHT impact NPS across channels?"

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| svc.sla.attainment.pct | Strategic |
| svc.fcr.pct | Influencing |
| svc.aht.minutes | Influencing |
| svc.backlog.count | Influencing |
| svc.nps.index | Influencing |
| svc.escalation.pct | Influencing |
| svc.tickets.created.count | Influencing |
| svc.tickets.closed.count | Influencing |

**Action Codes:** X-S1.1, X-S1.2, X-S1.3, X-S1.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- SLA Attainment %  
- FCR %  
- AHT (minutes)  
- Backlog Count  
- Escalation % / NPS Index  

### 5.2 30-Second Layer (Main Visuals)

- **SLA vs Target by Queue**
  - Visual Type: Column
  - X-Axis: dim_queue[Queue]
  - Y-Axis: [SLA %], [Target]
  - Segment: Channel/Region
  - Default Filter: Current month
  - Notes: Core ranking

- **FCR vs AHT**
  - Visual Type: Scatter
  - X-Axis: [AHT]
  - Y-Axis: [FCR %]
  - Segment: Queue/Channel
  - Default Filter: Current quarter
  - Notes: Efficiency-quality tradeoff

- **Backlog & Escalation Trend**
  - Visual Type: Line
  - X-Axis: dim_date[Week]
  - Y-Axis: [Backlog], [Escalation %]
  - Segment: Region/Channel
  - Default Filter: L12W
  - Notes: Risk indicator

- **NPS vs SLA**
  - Visual Type: Scatter
  - X-Axis: [SLA %]
  - Y-Axis: [NPS Index]
  - Segment: Channel
  - Default Filter: Current quarter
  - Notes: Experience linkage

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Region / Channel / Queue  
- Issue Type / Severity  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_cases (SLA, FCR, AHT, backlog, escalation)

  - fact_nps (NPS scores)
required_dimensions:

  - dim_date

  - dim_org (region/channel/queue)

  - dim_queue (if separate)

  - dim_issue (if modeled)

  - security_user_org
required_grain: >
  day_queue for ops metrics; month for NPS
required_time_range: 12-24 months history
required_slicers: >
  Date, Region/Channel/Queue, Issue Type/Severity
```

---

## 7. Dependencies, Assumptions & Constraints

- SLA/FCR/AHT definitions stable; backlog and escalation flags available.
- NPS survey data linked by channel/period; queue/channel structures consistent.
- OneLake canonical dims used (dim_date, dim_org, security_user_org;
  dim_queue optional).
- Data latency =24h.

---

## 8. Success Criteria

- Impact: SLA attainment to target; backlog/escalations reduced; FCR up; NPS
  improved.  
- Adoption: Used in weekly service ops reviews; action codes triggered with <5%
  false positives.  
- Quality: KPI definitions consistent across service channels; reconciled to
  source totals.  
- Decision Frequency: Weekly and daily service reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misclassified SLA breaches (force majeure vs controllable).  
- FCR misread on complex/regulatory cases.  
- NPS shifts not directly attributable without considering channel mix.  




## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: SLA Attainment Drop Driven by Backlog Surge

**Situation:** SLA attainment dropped from 91% to 78% over 4 weeks. First contact resolution is stable at 68%, but ticket backlog has grown 40%. Average handling time increased 15%.

**Decision question:** Is the backlog driven by volume spike (seasonal, campaign), staffing gap, or complexity increase in incoming tickets?

**Who decides:** Service Operations Lead + Workforce Manager.

**Consequence of inaction:** SLA penalties activate at <80%; customer churn risk increases with each week below threshold.

**Action Code triggered:** X-S1.1 (SLA Recovery) — activates backlog decomposition by category and aging analysis.

### Scenario B: NPS Decline Despite SLA on Target

**Situation:** SLA attainment is 92% (above target), yet NPS has dropped 8 points over the quarter. Escalation rate increased from 5% to 11%.

**Decision question:** Is the NPS gap driven by resolution quality (cases resolved but not to satisfaction), channel friction, or a specific product/service issue?

**Who decides:** Service Operations Lead + Customer Experience Manager.

**Consequence of inaction:** SLA compliance masks service quality erosion; NPS decline signals future churn.

**Action Code triggered:** X-S1.3 (Service Quality Review) — activates resolution satisfaction analysis and escalation root-cause breakdown.
