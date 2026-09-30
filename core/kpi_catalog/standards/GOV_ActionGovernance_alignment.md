# Enterprise & Governance KPIs — standards alignment & drift audit

> **Standards:** The ActionReady framework's own action-governance layer — no external standard; ISO 9001 continual improvement / Balanced Scorecard as conceptual backdrop; the value-at-risk composite references the SCM & Operations runs. **Method:** each governed KPI is mapped with an explicit `alignment`
> (exact / partial / none) + drift note in `standard_ref`, naming the discipline where there is no
> governing standard. Part of the per-domain standards program (SCM→SCOR, Finance→IFRS,
> Operations→ISO 22400, Service→ITIL/ISO 20000, Commercial→IFRS 15/convention).

## Read

Enterprise governance KPIs are the **framework's own construct** — action outcome rate, effectiveness delta, routed count. No external standard defines 'action outcome rate'; ISO 9001 continual improvement (PDCA) and the Balanced Scorecard are the conceptual backdrop, cited honestly as backdrop not conformance. The **value-at-risk index is a composite** of already-governed KPIs (SCOR reliability + ISO 22400 quality) — its inputs are standardised even though the composite itself is proprietary; document the weighting for reproducibility.

## Mapping table

| KPI | Standard / discipline | Alignment | Drift note / recommendation |
|---|---|---|---|
| `KPI-GOV-002` | `Internal — ActionReady governance` Action effectiveness delta | **none** | Average realised impact across achieved actions — the framework's own effectiveness measure. No external standard; PDCA/Balanced-Scorecard is the conceptual backdrop. |
| `KPI-GOV-001` | `Internal — ActionReady governance` Action outcome rate | **none** | Action outcome rate (achieved / total action outcomes) is the ActionReady framework's own action-governance construct — no external standard defines it. Conceptual backdrop: ISO 9001 continual improvement (Plan-Do-Check-Act) and Balanced Scorecard, but the metric is proprietary to the framework. |
| `KPI-GOV-003` | `Internal — ActionReady governance` Actions routed (element) | **none** | Routed-action count is an operational element of the action-governance loop, not a named external KPI. |
| `KPI-GOV-004` | `Internal — ActionReady governance` Enterprise value-at-risk (composite) | **none** | A composite index built from already-governed KPIs — SCOR reliability (OTIF, in-full → RL) and ISO 22400 quality (first-pass yield → QR) weighted into a 0-100 risk score. No external standard defines the composite; its inputs are governed by the SCM and Operations runs. Document the weighting so the index is reproducible. |

**Alignment legend:** `exact` = same definition as the standard · `partial` = anchored to a real
standard with a documented difference · `none` = no governing standard (a named discipline convention
or the framework's own construct; the `standard` field says which).

_Sources: ISO 10002:2018 (complaints handling); ISO 30414:2018 (human capital reporting); IFRS 15
(revenue base); ISO 9001:2015 continual improvement as conceptual backdrop for the action-governance
layer. NPS cited as a proprietary Bain & Company methodology; CLV/RFM/retention cited as marketing-
analytics conventions rather than standards._
