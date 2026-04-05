---
id: XD-004
factsheet_type: business
---

# XD-004 - Executive Action Governance

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** XD-004
- **Domain:** Executive / Governance
- **Business Owner:** Chief of Staff / Executive PMO
- **KPI Owner:** Executive Office / PMO Analytics
- **Decision Owner:** Executive Committee
- **Reporting Level:** Strategic / Prescriptive
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/governance.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Governance domain model for executive action lifecycle transparency.

---

## 1. Business Summary

**Purpose:** Provide executive transparency on whether routed strategic actions are being completed on time and producing the intended outcome.

**Business Value:** Reduces governance drag, improves follow-through on executive interventions, and makes ownership gaps visible before they turn into repeated enterprise performance issues.

**Out of Scope:** Domain-level remediation logic; root-cause analysis of underlying commercial, finance, operations, or people KPIs; executive performance roll-up itself (covered by XD-003).

---

## 2. Core Business Questions

- Which executive-routed actions are overdue, stalled, or ineffective?
- Which domains or entities accumulate the most unresolved action backlog?
- Where is routed action volume increasing without a corresponding improvement in action outcome rate?
- Which ownership patterns repeatedly correlate with delayed closure or poor outcome realization?

---

## 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| enterprise.action_outcome_rate.pct | Strategic |
| enterprise.action_routed.count | Influencing |

**Action Codes:** X-E3.3

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

This use case subscribes to a single executive governance action that escalates delayed or ineffective action instances once lifecycle and outcome evidence is available.

> Machine-readable config in `UseCase_Bracket.yaml` (SSOT).

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Action Outcome Rate %
- Actions Routed Count
- Overdue Executive Actions

### 5.2 30-Second Layer (Main Visuals)

- **Action Governance Trend**
  - Visual Type: Line
  - X-Axis: Date[Month]
  - Y-Axis: Action Outcome Rate %, Actions Routed Count
  - Segment: Domain / Entity
  - Default Filter: Last 12 months
  - Notes: Shows whether governance quality improves while action volume changes.

- **Owner and Domain Heatmap**
  - Visual Type: Matrix / Heatmap
  - X-Axis: Owner Role
  - Y-Axis: Domain / Entity
  - Segment: Status Bucket
  - Default Filter: Current quarter
  - Notes: Highlights clusters of stalled or ineffective action instances.

### 5.3 Required Slicers (Mandatory)

- Date (Month / Quarter)
- Domain
- Entity / Region
- Owner Role
- Action Status

### 5.4 300-Second Layer (Diagnostics)

- Action-instance table with owner, due date, status, elapsed days, and outcome evidence.
- Escalation queue for overdue or ineffective actions.
- Domain action-code view to distinguish governance failure from domain execution complexity.

---

## 6. Data Requirements Summary

- Required facts: action governance lifecycle records with routed date, due date, completion date, and outcome success flag.
- Required dimensions: date, organization/entity, action code, owner role.
- Required grain: action_instance.
- Required time range: at least 12 months of lifecycle history.
- Required slicers: Date, Domain, Entity, Owner Role, Status.

---

## 7. Dependencies, Assumptions & Constraints

- Routed actions must have a stable action instance identifier and linked domain action code.
- Outcome success criteria must be defined per action family before evaluation.
- Informational actions must be excluded to avoid governance noise.
- Executive governance evaluates follow-through; it does not replace domain action ownership.

---

## 8. Success Criteria

- **Impact:** Action outcome rate improves quarter over quarter while overdue backlog decreases.
- **Adoption:** Used in executive governance cadence and PMO follow-up reviews.
- **Quality:** 100% of routed executive actions have owner, due date, status, and evaluable outcome flag.
- **Decision Frequency:** Monthly governance review and ad-hoc escalation when critical backlog appears.

---

## 9. Risks & Wrong Interpretations (Short)

- High routed action count is not positive if outcome rate deteriorates.
- Late actions should not be treated as ineffective without checking the agreed evaluation window.
- Governance metrics must not be used to second-guess domain remediation logic without domain context.

---

## 10. Typical Decision Scenarios

### Scenario A: Routed Actions Grow but Closure Stalls

**Situation:** Routed action volume rises 40% after an executive steering cycle, but completion status remains flat and overdue actions accumulate in two entities.

**Decision question:** Is leadership over-routing actions without enough execution capacity, or are specific owners failing to close assigned actions?

**Who decides:** Chief of Staff + Executive Committee.

**Consequence of inaction:** Executive decisions create visible activity but no delivered outcome; unresolved actions roll over and erode trust in governance.

**Action Code triggered:** X-E3.3 (Executive Action Governance) — escalates overdue action instances and surfaces ownership concentration.

### Scenario B: Actions Close but Outcomes Do Not Improve

**Situation:** Closure rate appears healthy, but action outcome rate drops because many completed actions do not generate the expected KPI improvement.

**Decision question:** Are actions being closed administratively without real impact, or are outcome criteria and review windows incorrectly defined?

**Who decides:** Chief of Staff + Domain Executive Sponsors.

**Consequence of inaction:** Teams optimize for closure rather than effect; executive governance appears active while enterprise performance does not improve.

**Action Code triggered:** X-E3.3 (Executive Action Governance) — forces outcome-based follow-up instead of status-only closure.
