---
id: XD-001
factsheet_type: business
---

# XD-001 - Service Level Performance  

## Business Factsheet (v1.2)

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

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag SLA attainment below target; correlate with backlog, AHT, FCR.
- Flag FCR below target or AHT above target bands.
- Flag high escalation % and rising backlog.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: svc.sla.attainment.pct
    condition: <
    threshold: sla_target
    scope: queue_region_channel
    exclusion: force_majeure
    action_code: O2

  - kpi: svc.fcr.pct
    condition: <
    threshold: fcr_target
    scope: queue_region_channel
    exclusion: complex_cases
    action_code: L2

  - kpi: svc.aht.minutes
    condition: >
    threshold: aht_target
    scope: queue_region_channel
    exclusion: complex_cases
    action_code: M2

  - kpi: svc.escalation.pct
    condition: >
    threshold: escalation_target
    scope: queue_region_channel
    exclusion: regulated_cases
    action_code: O2
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

- **O2 — Operations Stabilisation**
  - Trigger (formal): SLA below target; escalations/backlog rising
  - Description: Rebalance capacity, triage/backlog sweeps, fix process gaps
  - Expected KPI Impact: Improve SLA, reduce backlog/escalations
  - Level (L1/L2/L3): L2
  - Owner: Service Ops

- **L2 — Quality & Yield**
  - Trigger (formal): FCR below target
  - Description: Improve knowledge base, scripts, training
  - Expected KPI Impact: Improve FCR, reduce repeat contacts
  - Level (L1/L2/L3): L2
  - Owner: CX/Training

- **M2 — Performance Uplift**
  - Trigger (formal): AHT above target
  - Description: Streamline workflows, tools; deflect to self-service
  - Expected KPI Impact: Reduce AHT, improve SLA
  - Level (L1/L2/L3): L2
  - Owner: Service Ops

- **D1 — Cost Take-Out (if cost focus)**
  - Trigger (formal): Cost per contact high
  - Description: Optimize staffing/shift mix, automation
  - Expected KPI Impact: Reduce cost-to-serve
  - Level (L1/L2/L3): L2
  - Owner: Service Ops / Finance

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- SLA Attainment %  
- FCR %  
- AHT (minutes)  
- Backlog Count  
- Escalation % / NPS Index  

### 6.2 30-Second Layer (Main Visuals)

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

### 6.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Region / Channel / Queue  
- Issue Type / Severity  

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- SLA/FCR/AHT definitions stable; backlog and escalation flags available.
- NPS survey data linked by channel/period; queue/channel structures consistent.
- OneLake canonical dims used (dim_date, dim_org, security_user_org;
  dim_queue optional).
- Data latency =24h.

---

## 9. Success Criteria

- Impact: SLA attainment to target; backlog/escalations reduced; FCR up; NPS
  improved.  
- Adoption: Used in weekly service ops reviews; action codes triggered with <5%
  false positives.  
- Quality: KPI definitions consistent across service channels; reconciled to
  source totals.  
- Decision Frequency: Weekly and daily service reviews.

---

## 10. Risks & Wrong Interpretations (Short)

- Misclassified SLA breaches (force majeure vs controllable).  
- FCR misread on complex/regulatory cases.  
- NPS shifts not directly attributable without considering channel mix.  
