# XD-001 – Service Level Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** XD-001
- **Domain:** Customer Experience / Service
- **Owner (Business):** Head of Customer Service / Operations
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/experience.yaml
- **Related Semantic Model:** semantic_models/domains/experience/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve service level performance to reduce churn risk, protect revenue, and cut service cost.  
**Business Value:** Higher SLA attainment, lower backlog/handling time, improved NPS/CSAT, fewer penalties.  
**Out of Scope:** Product feature roadmap decisions; long-term channel mix strategy.

---

## 2. Core Questions
- Where do we miss SLAs (channel, region, product, customer segment)?
- What drives SLA misses: backlog, staffing, process adherence, or channel mix?
- How do SLA misses affect churn, NPS/CSAT, and compensation/penalties?
- Which actions (staffing, routing, deflection, process fixes) lift SLA fastest?

**Example Queries:**
- “Which queues missed SLA >5% last week and why?”
- “How does First Contact Resolution vary by channel and segment?”

---

## 3. KPI Set (Business View)

| KPI Name                    | KPI ID (mandatory)          | Purpose                       | Definition (short)                                | Unit / Format | Target / Threshold    | Interpretation                     |
|-----------------------------|-----------------------------|-------------------------------|---------------------------------------------------|---------------|-----------------------|------------------------------------|
| SLA Attainment %            | svc.sla.attainment.pct      | Core service reliability      | % interactions meeting SLA (response/resolution)  | %             | ≥ 95%                | Reliability of service delivery    |
| First Contact Resolution %  | svc.fcr.pct                 | Quality and efficiency        | % resolved in first contact                       | %             | ≥ 80%                | Process effectiveness              |
| Average Handle Time (AHT)   | svc.aht.minutes             | Efficiency                    | Avg time to resolve                               | minutes       | ≤ target by channel   | Process/staffing pressure          |
| Backlog Volume              | svc.backlog.count           | Workload pressure             | Open tickets/cases                                | count         | Trend ↓               | Pending work                       |
| NPS/CSAT                    | svc.nps.index               | Experience outcome            | Net Promoter / CSAT index                         | index         | ↑ vs prior            | Customer sentiment                 |
| Escalation Rate %           | svc.escalation.pct          | Quality risk                  | Escalated cases / total                           | %             | ≤ 5%                 | Process stability                  |

> Use KPI IDs from catalog; targets differ by channel/segment.

---

## 4. Business Logic & Thresholds
- SLA Attainment % < 95% for 2 periods → staffing/routing or process action.
- FCR % < 80% OR Escalation % > 5% → quality/process fix.
- AHT above target with rising backlog → staffing/automation needed.
- NPS/CSAT decline linked to SLA misses → prioritise impacted queues/segments.

**Trigger Logic (formal, for automation):**
```
WHEN svc.sla.attainment.pct < 95
OR   svc.fcr.pct < 80
OR   svc.escalation.pct > 5
OR   svc.aht.minutes > target_channel
THEN propose L2 (staffing/routing), PC4 (process fix), D1 (demand management), O2 (quality improvement)
```

---

## 5. Action Codes

| Code | Name                          | Trigger (formal, KPIs)                       | Description (business action)                   | Expected KPI Impact            |
|------|-------------------------------|----------------------------------------------|-------------------------------------------------|--------------------------------|
| L2   | Staffing / Routing Optimise   | sla.attainment.pct < 95 OR backlog rising    | Rebalance FTE, skills-based routing             | Higher SLA, lower AHT/backlog  |
| O2   | Process / Quality Fix         | fcr.pct < 80 OR escalation.pct > 5           | SOP/knowledge fixes, QA coaching                | Higher FCR, lower escalations  |
| D1   | Demand Signal Management      | surge in volume driving SLA misses           | Deflection, self-service, proactive comms       | Lower backlog, higher SLA      |
| PC4  | Root-Cause Elimination        | repeated misses by queue/channel             | Fix systemic issues (tools, integrations)       | Sustained SLA improvement      |

> Use ActionCodes_Portfolio; triggers must reference KPIs.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- SLA Attainment %, FCR %, AHT, Backlog, NPS/CSAT, Escalation %.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name                 | Type   | X-Axis / Category        | Y-Axis / Value                          | Segment / Legend | Filters / Defaults |
|-----------------------------|--------|--------------------------|-----------------------------------------|------------------|--------------------|
| SLA vs Target Trend         | Line   | dim_date[Week/Month]     | [SLA Attainment %], Target              | Channel/Queue    | Last 12–24 months  |
| FCR and Escalation by Queue | Column | dim_queue[Queue]         | [FCR %], [Escalation %]                 | Region/Segment   | Current period     |
| AHT vs Volume               | Scatter| [AHT]                    | [Volume]                                | Channel          | Last 30–90 days    |
| Backlog by Priority         | Column | dim_case[Priority]       | [Backlog Count]                         | Queue            | Current period     |
| Experience Trend            | Line   | dim_date[Month]          | [NPS/CSAT]                              | Channel          | Last 12 months     |
| Detail Matrix               | Matrix | Region > Channel > Queue | SLA %, FCR %, AHT, Backlog, NPS/CSAT    | Region           | Export enabled     |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Channel → Queue → Priority → Agent; link to knowledge article usage and escalation reasons.
- Export: action list with owner/due date; backlog by age and priority.

---

## 7. Dependencies, Assumptions & Constraints
- Data: ticket/case interactions with open/close timestamps, SLA targets, queue/channel/priority, agent, backlog flag, escalation flag, NPS/CSAT; routing and staffing attributes.
- Assumptions: Targets by channel/queue are maintained; SLA definitions consistent; NPS/CSAT survey mapping to interactions.
- Constraints: Missing SLA target mapping or inconsistent timestamps reduce reliability; incomplete escalation coding weakens diagnostics.

---

## 8. Success Criteria
- Leading: >80% usage in weekly service reviews; action log maintained; SLA target table maintained.
- Lagging: SLA ≥ targets; FCR ↑; AHT at/below target; backlog stable; NPS/CSAT improving; escalations ≤ threshold.
- Cadence/Quality: Weekly review; consistent KPI definitions across regions/channels; target coverage ≥95%.
