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
- **Related Data Contract:** data_contracts/domains/experience.yaml
- **Related Semantic Model:** semantic_models/domains/experience/model_definition.yaml

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

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: svc.sla.attainment.pct
    name: SLA Attainment %
    purpose: Service level compliance
    definition_short: Cases meeting SLA / total cases
    unit: %
    grain: day_queue
    agg: avg
    target: = target
    interpretation: Low attainment signals service failure
    lineage: fact_cases[SLA Met Flag]

  - id: svc.fcr.pct
    name: First Contact Resolution %
    purpose: Quality/efficiency
    definition_short: Cases resolved on first contact / total cases
    unit: %
    grain: day_queue
    agg: avg
    target: = target
    interpretation: Low FCR drives repeat contacts/backlog
    lineage: fact_cases[FCR Flag]

  - id: svc.aht.minutes
    name: Average Handling Time (minutes)
    purpose: Efficiency
    definition_short: Avg handle time per case/contact
    unit: minutes
    grain: day_queue
    agg: avg
    target: = target band
    interpretation: High AHT slows throughput
    lineage: fact_cases[Handle Time]

  - id: svc.backlog.count
    name: Backlog Count
    purpose: Workload risk
    definition_short: Open cases not resolved
    unit: count
    grain: day_queue
    agg: sum
    target: Reduce vs target
    interpretation: Rising backlog risks SLA failure
    lineage: fact_cases[Backlog Flag/Open Cases]

  - id: svc.nps.index
    name: NPS Index
    purpose: Customer satisfaction
    definition_short: NPS score from surveys
    unit: index
    grain: month
    agg: avg
    target: = target
    interpretation: Lower NPS signals experience issues
    lineage: fact_nps[NPS Score]

  - id: svc.escalation.pct
    name: Escalation %
    purpose: Quality/risk
    definition_short: Escalated cases / total cases
    unit: %
    grain: day_queue
    agg: avg
    target: = target
    interpretation: High escalation signals quality/process issues
    lineage: fact_cases[Escalation Flag]

  - id: svc.tickets.created.count
    name: Tickets Created Count
    purpose: Demand volume
    definition_short: Count of newly created service tickets
    unit: count
    grain: day_queue
    agg: sum
    target: Monitor trend
    interpretation: Higher volume drives workload and SLA risk
    lineage: fact_ticket[Ticket ID]

  - id: svc.tickets.closed.count
    name: Tickets Closed Count
    purpose: Throughput volume
    definition_short: Count of closed service tickets
    unit: count
    grain: day_queue
    agg: sum
    target: Keep pace with inflow
    interpretation: Lower closures vs created leads to backlog growth
    lineage: fact_ticket[Tickets Closed Count]
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: X-S1.1
    name: Service Level Orchestration
    purpose: Coordinate Service Levers Without Degrading Quality or Cost-to-Serve
    status: active
    owner: Head of Service Operations
    trigger_kpis: [svc.sla.attainment.pct, svc.backlog.count]
    guardrail_kpis: [svc.fcr.pct]
    outcome_kpis: [svc.sla.attainment.pct]
    impact_range: svc.sla.attainment.pct: 3.0-8.0 pp
    levels: L1-L3
    definition: framework\action_codes\Service\XS-S.1.1.yaml

  - id: X-S1.2
    name: Capacity & Backlog Stabilisation
    purpose: Stabilise Backlog to Protect SLA Attainment
    status: active
    owner: Service Operations Manager
    trigger_kpis: [svc.backlog.count]
    guardrail_kpis: [svc.fcr.pct]
    outcome_kpis: [svc.backlog.count, svc.sla.attainment.pct]
    impact_range: svc.backlog.count: -15.0--35.0 %
    levels: L1-L3
    definition: framework\action_codes\Service\XS-S.1.2.yaml

  - id: X-S1.3
    name: Quality & First-Contact Resolution Uplift
    purpose: Increase Resolution Quality to Reduce Repeat Contacts and Escalations
    status: active
    owner: Quality & Training Lead
    trigger_kpis: [svc.fcr.pct, svc.escalation.pct]
    guardrail_kpis: [svc.aht.minutes]
    outcome_kpis: [svc.fcr.pct, svc.escalation.pct]
    impact_range: svc.fcr.pct: 5.0-12.0 pp
    levels: L1-L3
    definition: framework\action_codes\Service\XS-S.1.3.yaml

  - id: X-S1.4
    name: Handling Time & Flow Efficiency
    purpose: Reduce Handling Time Without Degrading Resolution Quality
    status: active
    owner: Service Operations Manager
    trigger_kpis: [svc.aht.minutes]
    guardrail_kpis: [svc.fcr.pct]
    outcome_kpis: [svc.aht.minutes, svc.sla.attainment.pct]
    impact_range: svc.aht.minutes: -5.0--15.0 %
    levels: L1-L3
    definition: framework\action_codes\Service\XS-S.1.4.yaml
```

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

