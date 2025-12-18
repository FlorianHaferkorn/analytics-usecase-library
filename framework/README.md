# Action Codes

## Purpose

Action Codes define **standardised, reusable decision and steering logic** that translates KPI deviations into concrete management actions.

They are **not reports**, **not dashboards**, and **not Use Cases**.
Action Codes represent the **execution and governance layer** between insight and action.

Their primary goal is to ensure that analytics consistently leads to **decisions, accountability, and measurable outcomes**.

---

## Core Principle (Non-Negotiable)

> **Use Cases consume Action Codes. Action Codes never belong to Use Cases.**

This separation is mandatory to ensure:

* Reusability across multiple Use Cases
* Clear ownership and governance
* Long-term scalability of the Analytics Framework

---

## Conceptual Separation

### Use Case

A Use Case defines:

* *Why* a business question matters
* *Which KPIs* are relevant
* *Which decisions* must be enabled

A Use Case **never** contains execution logic.

Example:

> `COM-002 — Margin & Price Performance`

### Action Code

An Action Code defines:

* *What to do* when KPIs deviate
* *When to act* (trigger logic L1–L3)
* *Which guardrails apply*
* *How outcomes are evaluated*

Action Codes can be referenced by **multiple Use Cases** and remain stable over time.

Example:

> `C-M2.3 — Price Leakage Containment`

---

## Architecture & Ownership

Action Codes are **standalone, domain- or governance-owned assets**.

They are deliberately **decoupled from Use Cases** to avoid:

* Duplication
* Conflicting ownership
* Tight coupling between analytics and execution

Ownership principles:

* **Domain Action Codes** are owned by the respective business domain
* **Enterprise Action Codes** are owned by executive governance functions
* A Use Case may reference an Action Code, but never owns it

This design enables:

* Cross-use-case reuse
* Executive orchestration across domains
* Stable governance even as new Use Cases are added

---

## Folder Structure (Source of Truth)

Action Codes are organised by **domain or governance layer**, never by Use Case.

```
framework/action_codes/
├─ Commercial/
├─ Finance/
├─ Operations/
├─ People/
├─ Service/
├─ SupplyChain/
└─ Enterprise/
```

### Domain folders

Contain **execution-level Action Codes** owned by a business domain.

Examples:

* Commercial → pricing, margin, customer actions
* SupplyChain → inventory, OTIF, forecast actions
* Service → SLA, backlog, quality actions

### Enterprise folder

Contains **meta-level governance Action Codes** that:

* Orchestrate
* Prioritise
* Route
* Govern outcomes

Enterprise Action Codes **never execute domain logic themselves**.

Examples:

* `X-E3.1 — Executive Performance Orchestration`
* `X-E3.2 — Cross-Domain Risk Prioritisation`
* `X-E3.3 — Action Follow-up & Outcome Governance`

---

## Binding Action Codes to Use Cases

The **only allowed coupling** between Use Cases and Action Codes is via:

```
usecases/core/<USECASE_ID>/actioncodes_map.yaml
```

Example:

```yaml
use_case: XD-003
action_codes:
  - X-E3.1
  - X-E3.2
  - X-E3.3
```

Rules:

* No Action Code may exist outside `framework/action_codes/`
* No Action Code may be duplicated per Use Case
* All mappings must be explicit and auditable

---

## Reuse & Scalability Guarantee

Because Action Codes are **decoupled from Use Cases**:

* New Use Cases can reuse existing Action Codes without refactoring
* Executive Use Cases can orchestrate across multiple domains
* Governance and ownership remain stable as the framework grows

Example:
A future Use Case `ESG-001 — Supplier Risk` may reuse:

* `S-S2.3 — Supply Risk Containment`
* `X-E3.2 — Cross-Domain Risk Prioritisation`

No duplication. No rework. No ambiguity.

---

## Anti-Patterns (Explicitly Forbidden)

The following patterns are **not allowed**:

* Storing Action Codes under `/usecases/`
* Creating "Executive versions" of existing domain Action Codes
* Duplicating Action Codes for different Use Cases
* Embedding execution logic directly into dashboards

---

## Definition of Done for Action Codes

An Action Code is considered **valid** only if:

* It is stored in the correct domain or Enterprise folder
* It follows the canonical ActionCode template
* It is referenced by at least one `actioncodes_map.yaml`
* Ownership, trigger logic, guardrails, and outcomes are explicit

---

## Key Takeaway

> **Action Codes are reusable, domain-owned steering assets.**
> **Use Cases reference them to turn insight into action — never the other way around.**
