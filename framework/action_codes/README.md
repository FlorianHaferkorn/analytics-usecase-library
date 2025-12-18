# Action Codes

This README explains **what Action Codes are**, **why they exist**, and **how they are used** in the Analytics Use Case Library.

Action Codes are a core building block of the framework, but they are intentionally **lightweight, stable, and reusable**.

They answer one question only:

> **What should be done when a certain business situation becomes relevant?**

---

## What Action Codes Are (and Are Not)

### Action Codes ARE
- Prescriptive decision constructs
- Reusable across use cases, KPIs, and reports
- Evaluated by **business outcome**
- Independent of specific KPI thresholds or targets

### Action Codes ARE NOT
- Task or workflow definitions
- Jira tickets or execution checklists
- KPI definitions
- Customer- or tool-specific configurations

This separation is intentional and critical for scalability and low maintenance.

---

## Design Principles (Non-Negotiable)

Action Codes in this framework are intentionally constrained.

They must be:

- **Trigger-compatible**  
  Designed to be activated by KPI-based signals via trigger mappings.

- **Prescriptive**  
  Clearly define what to *do, stop, or change* — not what to review or monitor.

- **Decision-focused**  
  Executable at decision level, without embedding task workflows.

- **Economically meaningful**  
  Impact expressed as ranges and directional effects, not fake precision.

- **Risk-aware**  
  Trade-offs and side effects are explicitly stated.

- **Reusable**  
  Applicable across multiple use cases and domains.

Action Codes that merely explain KPIs are **not allowed**.

---

## Core Artifacts (Single Source of Truth)

The Action Code concept is defined by **exactly two normative artifacts**:

```
framework/templates/action_codes/
  ActionCode_Canonical_Template.md
  ActionCode_KPI_Trigger_Map.yaml
```

- **ActionCode_Canonical_Template**  
  Defines *what* an Action Code is, including situation, action, outcome, risks, and evaluation.

- **ActionCode_KPI_Trigger_Map**  
  Defines *when* an Action Code becomes decision-relevant, based on KPIs, targets, and signal patterns.

There is deliberately **no separate Action Code portfolio document**.
This avoids duplication and ongoing maintenance effort.

---

## Decision Coverage (Orientation Only)

The framework supports prescriptive actions across common business situations, for example:

- Price or margin erosion without demand decline
- Cost overruns and efficiency losses
- Cash and working-capital pressure
- Service-level or operational performance degradation
- Strategic KPI deviations requiring escalation

This list is **illustrative**, not exhaustive.
Concrete actions are defined via Action Codes and Trigger Mappings.

---

## How Action Codes Fit into the Framework

```
KPI Catalog
   ↓
ActionCode_KPI_Trigger_Map   (when relevant)
   ↓
Action Codes                (what to do)
   ↓
T4 – Prescriptive Pages     (decision & communication)
```

- KPIs remain descriptive and neutral
- Trigger mappings define relevance
- Action Codes define decisions
- T4 pages surface and contextualize actions

---

## Tracking and Learning

The framework distinguishes between three levels:

1. **Action Code**  
   Stable definition of the recommended intervention and expected outcome.

2. **Action Execution (optional)**  
   Records that a decision was taken and acted upon in a specific context.

3. **Outcome Evaluation (mandatory)**  
   Measures whether the action had the intended business effect.

This enables learning without introducing workflow complexity.

---

## Governance Principles

- Action Codes are few by design
- IDs are immutable
- New Action Codes are added only if:
  - the situation is recurring and economically meaningful
  - no existing Action Code covers it
- KPI thresholds and targets must never be embedded in Action Codes

---

## Why There Is No Action Code Portfolio

Every additional document creates long-term maintenance effort.

A separate portfolio:
- would duplicate existing information
- would not be required for configuration or execution
- would add governance overhead

Therefore, orientation is handled **here**, and all normative logic lives in the two core artifacts.

---

## Key Takeaway

> Action Codes turn analytics into decisions,  
> without turning the framework into a workflow system.

**Location:**  
`framework/action_codes/README.md`
