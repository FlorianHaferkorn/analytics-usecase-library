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
**Out of Scope:** Sales pipeline (planned: COM-010); marketing journey analytics; field service parts/ops (scoped separately).

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
| KPI-SVC-004 | Strategic |
| KPI-SVC-005 | Influencing |
| KPI-SVC-006 | Influencing |
| KPI-SVC-007 | Influencing |
| KPI-SVC-008 | Influencing |
| KPI-SVC-013 | Influencing |
| KPI-SVC-014 | Influencing |
| KPI-CUS-003 | Supporting |

**Action Codes:** X-S1.1, X-S1.2, X-S1.3, X-S1.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **SLA Attainment %** (`KPI-SVC-004`) → **ISO/IEC 20000-1 8.3.3** (partial): ISO/IEC 20000-1:2018 clause 8.3.3 (Service level management) requires documented SLAs and monitoring of performance against agreed service-level targets.
- **Backlog Count** (`KPI-SVC-007`) → **ISO/IEC 20000-1 8.6.1** (partial): Open-case backlog is an operational measure of the ISO/IEC 20000-1 resolution & fulfilment processes (8.6.1 incident / 8.6.2 service request).
- **First Contact Resolution %** (`KPI-SVC-005`) → **ITIL 4** (partial): First Contact Resolution is a de-facto ITIL 4 service-desk / incident-management practice metric (and COPC CX Standard), not formally defined by ISO/IEC 20000.
- **Average Handling Time (minutes)** (`KPI-SVC-006`) → **ITIL 4** (partial): AHT is a contact-centre / ITIL service-desk practice metric (also COPC CX Standard); not ISO/IEC 20000-defined.
- **Escalation %** (`KPI-SVC-008`) → **ISO/IEC 20000-1 8.6.1** (partial): Escalation ratio relates to ISO/IEC 20000-1 incident-management escalation (8.6.1, functional/hierarchical) and ITIL practice.
- **Tickets Created Count** (`KPI-SVC-013`) → **ISO/IEC 20000-1 8.6.1** (none): Raw created-ticket count is an incident/service-request volume element (ISO/IEC 20000-1 8.6.1/8.6.2), not a named ISO KPI.
- **Tickets Closed Count** (`KPI-SVC-014`) → **ISO/IEC 20000-1 8.6.1** (none): Raw closed-ticket count is a throughput element feeding backlog and closure-rate.
- **NPS Index** (`KPI-CUS-003`) → **Bain NPS (proprietary)** (none): NPS is a proprietary Bain & Company methodology, not an open standard; the governed NPS is the Customer-domain `KPI-CUS-003` (consolidated from the former `svc.nps.index`).

---

## 4. Action Codes (Summary)

**X-S1.1 — Service Level Orchestration**
Fires when SLA attainment falls persistently below target for two or more consecutive periods and backlog or escalation data confirms the deterioration is structural rather than a one-off incident. Owned by the Head of Service Operations. Diagnoses the dominant service constraint (capacity, quality, or handling efficiency), activates the corresponding execution Action Code, and reviews SLA recovery daily. Expected to improve SLA attainment by 3–8 pp within 1–3 periods. Not triggered for queues under planned transformation programs, for incident-driven demand surges with executive override, or for low-volume specialist queues with insufficient ticket volume.

**X-S1.2 — Capacity & Backlog Stabilisation**
Fires when ticket backlog grows persistently above baseline for two or more consecutive periods and the growth exceeds the arrival rate trend, indicating that available capacity is structurally below demand. Owned by the Service Operations Manager. Identifies queues with sustained backlog growth, reallocates capacity or extends operating windows, executes backlog reduction waves, and monitors SLA and quality daily. Expected to reduce backlog count by 15–35% within 1–4 periods. Not triggered for quality-driven backlog increases (X-S1.3 takes precedence), for incident-driven spikes under executive override, or for low-volume specialist queues.

**X-S1.3 — Quality & First-Contact Resolution Uplift**
Fires when FCR falls persistently below target for two or more consecutive periods and repeat contacts are confirmed as a backlog driver, indicating that resolution quality — not capacity — is the primary bottleneck. Owned by the Quality and Training Lead. Identifies cases with low FCR by queue and agent group, diagnoses top repeat-contact drivers, deploys targeted coaching, scripts, or knowledge updates, and reviews FCR and escalations bi-weekly. Expected to improve FCR by 5–12 pp within 2–6 periods. Not triggered if the FCR gap is driven by authority or empowerment limits (not a coaching problem), during active capacity stabilisation actions, or for regulatory-mandated escalations.

**X-S1.4 — Handling Time & Flow Efficiency**
Fires when average handling time rises persistently above baseline for two or more consecutive periods and the increase is not driven by quality improvements or contact complexity, indicating process inefficiency. Owned by the Service Operations Manager. Identifies queues with rising AHT, analyses top handling-time drivers, removes or streamlines non-value-adding process steps, and monitors AHT and FCR weekly. Expected to reduce AHT by 5–15% within 2–6 periods. Not triggered if the AHT increase is quality-driven or from training and onboarding, during active capacity stabilisation actions, or for regulatory-mandated handling steps.

> Full machine-readable trigger conditions, thresholds, and routing in `UseCase_Bracket.yaml` (SSOT).


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

_Filter Interaction: Queue/Channel slicer cascades to all backlog, FCR, and AHT visuals. Issue Type slicer is independent and applies to the 30-second case volume distribution only._

---

### 5.4 300-Second Layer (Diagnostics)

- Queue- and severity-level case table with SLA flag, backlog flag, escalation flag, and handle-time context.
- Aging and backlog decomposition by queue, issue type, and region.
- Action panel routing for SLA recovery, backlog stabilisation, quality uplift, or handling-time optimisation.

## 6. Data Requirements Summary

- Required facts: support-case events for SLA, FCR, handle time, escalation, backlog, and ticket flow plus NPS survey results.
- Required dimensions: date, organization, queue, issue type/severity.
- Required grain: case for operations metrics, with monthly aggregation for NPS comparison.
- Required time range: 12 to 24 months history.
- Required slicers: Date, Region/Channel/Queue, Issue Type, Severity.
- **Data latency SLA:** Case status and SLA flag updated in real time with maximum 15-minute lag for open cases; closed case metrics finalized within 4 hours of case closure; backlog count used in weekly capacity decisions must be current as of morning of review; any SLA data >4 hours stale triggers a dashboard staleness warning.

---

## 7. Dependencies, Assumptions & Constraints

- SLA/FCR/AHT definitions stable; backlog and escalation flags available.
- NPS survey data linked by channel/period; queue/channel structures consistent.
- OneLake canonical dims used (dim_date, dim_org, security_user_org; dim_queue optional).
- Data latency: 24h.

### 7.4 Data Protection & Privacy (DSGVO / GDPR)

This use case processes service ticket data that may include personal identifiers (customer name, contact details, case description) and is subject to DSGVO obligations. The following controls are mandatory before go-live:

**Legal basis:** Service operations analytics relies on legitimate interest (Art. 6(1)(f) DSGVO) for internal performance monitoring. SLA attainment, FCR, and AHT are aggregated at queue and channel level for reporting — individual ticket-level data including customer identifiers is not surfaced in the dashboard. If ticket-level customer data is required for drill-through, a separate legal basis review is required.

**Data minimisation:** The semantic model exposes only ticket ID, status flags, timestamps, queue, channel, and agent group. Customer name, contact information, and case description text are excluded from the analytical layer. Ticket IDs are internal system identifiers without direct customer identification capability in the reporting context.

**Retention:** Service ticket operational data follows the retention schedule in the experience domain data contract (core/data_contracts/domains/experience.yaml). Aggregated reporting data is retained for a maximum of 36 months. Tickets containing special category data (e.g. health-related complaints) require separate review of the applicable retention period.

**Data subject rights:** Customer right-of-erasure requests require removal of any ticket records associated with the identified customer from the analytical layer within 30 days. The Service BI Lead coordinates with the DPO on erasure execution. Agent performance data (AHT, FCR by agent) is classified as employee personal data; access is restricted to direct management roles.

**Access restriction:** Agent-level performance data (AHT, FCR attributed to an individual agent) is accessible only to direct line managers and above. Team-aggregated and queue-aggregated metrics are available to the full Service Operations team. Enforcement via RLS on the security_user_org canonical dimension.

**DSGVO owner:** Data Protection Officer. Review cycle: annual DPIA review for the service operations domain.

---

## 8. Success Criteria

- **Impact:** SLA attainment at or above 92% in ≥9 of 12 months across all service queues; backlog below 100 open cases at week-end in ≥85% of weeks; FCR at or above 80% within 2 quarters of go-live.
- **Adoption:** Dashboard used in daily team leader standup and weekly Service Operations Review (Service Ops Lead + Queue Managers); ≥90% of SLA breaches below 85% result in a documented X-S1.1–X-S1.4 action within 24 hours.
- **Quality:** SLA flag logic validated against service agreement definitions quarterly; FCR flag reconciled against customer satisfaction follow-up sample (5% of cases) monthly; any FCR variance >2pp escalated to Service Ops BI Lead.
- **Decision Frequency:** Daily (team leader standup); weekly (Service Operations Review); monthly (SLA performance review with CX Director); Action Code closures tracked by Service Ops Lead within 14 days.

---

## 9. Risks & Wrong Interpretations (Short)

- **Risk:** SLA clock misconfigured for specific queue types (e.g., weekend exclusions not applied), causing SLA % to understate performance and triggering unnecessary X-S1.1.
  **Owner:** Service Ops BI Lead.
  **Detection:** SLA attainment variance >3pp between dashboard and service desk reporting in weekly comparison.
  **Mitigation:** SLA clock configuration reviewed and validated quarterly against service agreement definitions; any queue-type exception documented in configuration log.
  **Escalation:** If misconfiguration confirmed, BI Lead suspends X-S1.1 eligibility for affected queue until configuration is corrected; correction implemented within 5 business days.

- **Risk:** Backlog count spike driven by system migration or batch import creates a false demand signal, triggering X-S1.2 capacity reallocation when staffing is adequate.
  **Owner:** Service Ops Lead.
  **Detection:** Backlog count increases >100 cases within a single day without corresponding increase in inbound volume.
  **Mitigation:** System migrations and batch imports registered in the exception log with expected backlog impact and duration; X-S1.2 gating rule excludes batch-import events.
  **Escalation:** If X-S1.2 fires during a registered event, Service Ops Lead confirms exclusion with WFM Lead within 4 hours.

- **Risk:** FCR calculation based on reopened case count is distorted by customers contacting different channels for the same issue, understating true FCR and potentially delaying X-S1.3.
  **Owner:** Service Ops BI Lead.
  **Detection:** FCR variance >5pp between single-channel and cross-channel measurement in quarterly audit.
  **Mitigation:** Cross-channel case linkage validated quarterly using customer ID matching; FCR shown as both single-channel and cross-channel estimates in the 300-layer diagnostic.
  **Escalation:** If cross-channel linkage not available, FCR is labeled as single-channel estimate in dashboard until cross-channel data is integrated.




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

**Action Code triggered:** X-S1.3 (Quality & First-Contact Resolution Uplift) — activates resolution satisfaction analysis and escalation root-cause breakdown.

### Scenario C: SLA Drop During Planned System Outage or Migration

**Situation:** SLA attainment drops from 90% to 74% over two weeks. Backlog grows 38%. X-S1.1 fires. However, the IT and service teams confirm that the company is mid-migration of the ticketing platform — the performance degradation is fully explained by the planned transition window documented in the project register.

**Decision question:** Is the SLA drop an operational failure requiring corrective action, or the expected performance impact of an approved system migration?

**Who decides:** Head of Service Operations + IT Project Lead.

**When NOT to act:** X-S1.1's `scope.exclusions` covers "Queues under planned transformation." If SLA deterioration is fully attributable to an approved system migration within its documented window, X-S1.1 and X-S1.2 must not fire. The correct outcome is a time-boxed exception flag in the performance register acknowledging the approved deviation. Monitor daily to ensure the SLA trajectory recovers as the migration stabilises — if recovery does not happen within the projected timeline, escalate with context.

**Action Code triggered:** None during the approved migration window. After go-live stabilisation, re-evaluate SLA attainment and trigger X-S1.1 if recovery does not occur within the agreed post-migration grace period.

---
