# Service & Experience KPIs — ITIL 4 / ISO/IEC 20000 alignment & drift audit

> **Standards:** [ISO/IEC 20000-1:2018](https://www.iso.org/standard/70636.html) — *Information
> technology — Service management — Part 1: Service management system requirements*, the
> international standard for IT/service management (service level management, incident & service
> request management, performance evaluation) — and **[ITIL 4](https://www.axelos.com/certifications/itil-service-management)**
> as the practice framework where ISO/IEC 20000 sets the requirement but not the specific metric
> (FCR, AHT). **Method:** each governed `svc.*` KPI is mapped to its nearest clause/practice with an
> explicit `alignment` (exact / partial / none) + drift note, recorded per-KPI in `standard_ref`.
> Fourth run of the per-domain program after SCM→SCOR, [Finance→IFRS](FIN_IFRS_alignment.md),
> [Operations→ISO 22400](OPS_ISO22400_alignment.md).

## Scope note

This run covers the **service-desk `svc.*` family**. Two adjacent families are deliberately out of
this run:
- **`res.*` workforce metrics** (occupancy, shrinkage, utilization, overtime) already carry refs from
  the [Operations run](OPS_ISO22400_alignment.md) with a COPC CX Standard pointer — they are
  contact-centre workforce management, not service-desk process metrics.
- **`crm.*` Customer & Market KPIs** (CLV, retention, churn, NPS) are a **separate Customer-domain
  run** — that domain has no single dominant standard (NPS is proprietary; CLV/retention are
  marketing-analytics conventions), which is itself the finding to record there.

## Standards fit — an honest read

Service management is a *requirements* standard, not a *metric-definition* standard like SCOR or
ISO 22400. ISO/IEC 20000-1 tells you that you **must** run service level management, incident and
request management, and measure customer satisfaction — it does **not** hand you a formula for FCR
or AHT. So the strongest alignment here is **partial**: our KPIs are the right practice metrics for
the right clauses, but the standard governs the *process*, not the *arithmetic*. That is the correct
story to tell a client — "ISO/IEC 20000-conformant service management, measured with the ITIL-standard
service-desk KPIs" — rather than over-claiming an exact standard definition.

## Headline findings

1. **SLA attainment is the one clause-anchored KPI.** `KPI-SVC-004` maps to ISO/IEC
   20000-1 clause 8.3.3 (Service level management), which mandates SLAs and monitoring against
   targets. Pin the agreed target set and it is conformance evidence, not just a dashboard number.
2. **FCR and AHT are ITIL/COPC practice, not ISO-defined.** They are genuinely standard *in
   practice*, but no ISO clause defines their arithmetic — label them as ITIL 4 / COPC metrics and
   pin the contact grain and handle-time components so they compare across teams and vendors.
3. **Ticket counts are elements, not KPIs.** Created/closed counts are inputs to arrival-rate,
   throughput and backlog — map them as 8.6.1 incident/request elements, not standalone KPIs.
4. **NPS is proprietary, and duplicated.** `svc.nps.index` uses Bain's NPS (not an open standard) and
   duplicates `KPI-CUS-003`. ISO/IEC 20000 requires customer-satisfaction monitoring (8.3.2 / 9.1)
   but not NPS specifically — consolidate to one governed NPS and treat it as a CX index.

## Mapping table

| KPI | Standard | Alignment | Drift note / recommendation |
|---|---|---|---|
| `KPI-SVC-006` | `ITIL 4` Average Handling Time | **partial** | AHT is a contact-centre / ITIL service-desk practice metric (also COPC CX Standard); not ISO/IEC 20000-defined. Align the handle-time components (talk + hold + wrap) so the average is comparable across teams. |
| `KPI-SVC-007` | `ISO/IEC 20000-1 8.6.1` Incident & service-request management — open backlog | **partial** | Open-case backlog is an operational measure of the ISO/IEC 20000-1 resolution & fulfilment processes (8.6.1 incident / 8.6.2 service request); a count element rather than a named ISO KPI. |
| `KPI-SVC-008` | `ISO/IEC 20000-1 8.6.1` Incident escalation ratio | **partial** | Escalation ratio relates to ISO/IEC 20000-1 incident-management escalation (8.6.1, functional/hierarchical) and ITIL practice; the % is a practice metric, not an ISO-defined formula. |
| `KPI-SVC-005` | `ITIL 4` Service desk — First Contact Resolution | **partial** | First Contact Resolution is a de-facto ITIL 4 service-desk / incident-management practice metric (and COPC CX Standard), not formally defined by ISO/IEC 20000. Widely standard in service management; pin the 'contact' grain (call vs case, single vs multi-channel) to compare externally. |
| `KPI-SVC-004` | `ISO/IEC 20000-1 8.3.3` Service level management — SLA attainment | **partial** | ISO/IEC 20000-1:2018 clause 8.3.3 (Service level management) requires documented SLAs and monitoring of performance against agreed service-level targets. SLA attainment % is the practice metric for that clause — ISO mandates the SLA and its monitoring, not this specific formula. Pin the target set so attainment is comparable. |
| `svc.nps.index` | `ISO/IEC 20000-1 9.1` Customer satisfaction (Net Promoter Score) | **none** | NPS is a proprietary Bain & Company methodology, not an open standard. ISO/IEC 20000-1 requires customer-satisfaction monitoring (8.3.2 / performance evaluation 9.1) but does not prescribe NPS. Treat as a CX index; duplicate of KPI-CUS-003 — consolidate to one governed NPS. |
| `KPI-SVC-014` | `ISO/IEC 20000-1 8.6.1` Incident/request throughput (element) | **none** | Raw closed-ticket count is a throughput element feeding backlog and closure-rate; not a named ISO/IEC 20000 KPI on its own. |
| `KPI-SVC-013` | `ISO/IEC 20000-1 8.6.1` Incident/request volume (element) | **none** | Raw created-ticket count is an incident/service-request volume element (ISO/IEC 20000-1 8.6.1/8.6.2), not a named ISO KPI — it is an input to arrival-rate/backlog measures. |

**Alignment legend:** `exact` = same definition as the standard's KPI · `partial` = the standard
governs the process/requirement (right clause, right practice metric) but not the exact formula ·
`none` = no standard definition (proprietary methodology or a raw count element; note points to the
practice owner).

_Sources: ISO/IEC 20000-1:2018 (iso.org/standard/70636.html) — clause structure 8.3.3 Service level
management, 8.6.1 Incident management, 8.6.2 Service request management, 9.1 Performance evaluation;
ITIL 4 service-management practices (AXELOS) for the service-desk practice metrics (FCR, AHT). NPS is
a proprietary Bain & Company methodology, cited as such rather than as a standard._
