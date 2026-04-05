# Action Code Patterns

## 1. Purpose

Action Code **patterns** are recurring types of management response: they describe *what kind of action* is being taken (e.g. coordinate levers, enforce a control, rebalance capacity). Individual action codes in `core/action_codes/` implement these patterns with specific triggers, KPIs, and ownership.

Documenting patterns makes the closed loop easier to understand and extend: new action codes can be aligned to an existing pattern for consistent naming and behavior.

**Canonical mapping:** Use Case → Action Code subscriptions are declared in each use case's `UseCase_Bracket.yaml` (`orchestration.action_code_ids`). This document is descriptive.

---

## 2. Pattern Definitions

| Pattern | Description | Typical trigger | Example action code groups (from YAML category.group) |
|---------|-------------|-----------------|------------------------------------------------------|
| **Governance / Orchestration** | Coordinate multiple levers or stakeholders without executing a single control. Decide *which* sub-action to activate. | KPI deviation or imbalance across dimensions | Inventory Governance (S-I1.1), Service Governance (X-S1.1), Liquidity Steering (F-C1.1), Reliability Governance (O-A2.1), Quality Governance (O-Q3.1), Utilization Governance (X-R2.1), Forecast Governance (S-F3.1), Service Reliability Governance (S-R2.1), Cost Governance (F-K2.1), Pricing Governance (C-M2.1), Enterprise Risk Steering (X-E3.2) |
| **Control / Containment** | Enforce or correct a single lever: price, receivables, availability, defect, etc. | KPI breach (level L1–L3) | Price Realization Guardrails (C-M2.1), Receivables Control (F-C1.2), Payables Optimisation (F-C1.4), Inventory Rightsizing (S-I1.2), Availability Control (O-O1.1), Speed Loss Control (O-O1.2), Defect Control (O-Q3.2), Failure Control (O-A2.2), Delivery Execution Control (S-R2.2), Service Execution Control (X-S1.2) |
| **Allocate / Rebalance** | Shift resources (capacity, mix, budget) across dimensions. | Under/over utilization or misallocation | Portfolio & Mix Steering (C-M2.2), Capacity Allocation Control (X-R2.2) |
| **Escalate / Route** | Route issues to the right owner or prioritise cross-domain. | Cross-domain risk or executive attention | Enterprise Risk Steering (X-E3.2) |
| **Review and Decide** | Structured review with follow-up and outcome measurement. | Recurring cadence or after intervention | Domain governance action codes within the respective active use cases |

---

## 3. Pattern by Domain (Summary)

| Domain | Dominant patterns | Example themes |
|--------|-------------------|----------------|
| Commercial | Governance, Control, Allocate | Pricing Governance, Stop Discount Leakage, Portfolio & Mix Steering, Revenue Recovery |
| Finance | Governance, Control | Liquidity Steering, Receivables/Payables/Inventory Control, Cost Governance, Material/Labor/Overhead Control |
| Operations | Governance, Control | Availability, Speed Loss, Quality Loss, Throughput; Reliability, Failure Control, PM Control, Repair, Spare Parts; Quality Governance, Defect/Yield/COPQ/Complaint Control |
| Supply Chain | Governance, Control | Inventory Governance, Level/Service Availability/Aging/Planning; OTIF Governance, Delivery/Completeness/Service Cost/Plan–Execute; Forecast Governance, Error Control/Containment, Planning Governance |
| Service (XD) | Governance, Control, Allocate | Service Governance, Execution/Quality/Flow Control; Utilization Governance, Capacity Allocation, Utilization Quality, Workforce Sustainability |
| Enterprise | Escalate, Review and Decide | Enterprise Risk Steering, Executive Accountability |

---

## 4. Trigger Levels (L1–L3)

All action codes use a consistent severity ladder:

- **L1 — Early warning:** Monitor and prepare; no mandatory intervention.
- **L2 — Required intervention:** Action must be scheduled and executed within agreed SLA.
- **L3 — Prescriptive execution:** Immediate action; escalation if not executed.

Patterns do not change this; they describe the *type* of action (govern, control, allocate, escalate), not the trigger level.

---

## 5. Relationship to Other Artifacts

- **Action code YAML:** Each file has `category.group` and `category.theme`; these map to the patterns above.
- **UseCase_Bracket.yaml** (`orchestration.action_code_ids`): Canonical use case → action code subscriptions; do not duplicate here.
- **Decision taxonomy:** `operating_model/decision_taxonomy.md` — Intervene decision type aligns with all action codes; patterns refine how we intervene.
