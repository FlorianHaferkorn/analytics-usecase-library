# Action Code Template — Authoring & Governance Guide

This document defines the **non-negotiable rules** for authoring Action Codes
based on the canonical `ActionCode_TEMPLATE.md`.

The goal is absolute consistency, scalability, and automation readiness.

Action Codes are **prescriptive control mechanisms** that connect:
Strategic KPIs → Use Cases → Decisions → Execution → Measured Outcomes.

This guide applies to **all domains** and **all Core Use Cases**.

---

## 1. What an Action Code Is (and Is Not)

### Action Code IS
- A **prescriptive decision artifact**
- Triggered by **measurable KPI signals**
- Executable by **real roles in real organizations**
- Measurable in terms of **outcome and effectiveness**
- Reusable across **reports, domains, and time**

### Action Code IS NOT
- A KPI explanation
- A generic recommendation
- A “review / monitor / analyze” suggestion
- A one-off idea tied to demo data
- A consultant narrative

If it does not result in a **clear decision and action**, it is **not an Action Code**.

---

## 2. Canonical File Structure (Mandatory)

Each Action Code MUST be stored as:

framework/action_codes/<domain>/<ACTIONCODE_ID>_<slug>.md

Example:
framework/action_codes/commercial/C-P1.1_correct_price_leakage.md

### File rules
- Exactly **one YAML block**
- YAML block is the **single source of truth**
- Markdown outside YAML is optional and non-binding
- IDs are **immutable** once created

---

## 3. Canonical Template Usage

All Action Codes MUST conform to:

framework/templates/action_codes/ActionCode_TEMPLATE.md

Rules:
- No fields may be removed
- No fields may be renamed
- Optional fields may only be omitted if explicitly marked optional
- No free-text logic outside defined fields

---

## 4. Strategic KPI Anchoring (Critical)

Every Action Code MUST:
- Support **at least one Strategic KPI**
- Be triggered by **defined KPI signals**
- Contribute to **measurable KPI movement**

Action Codes do **not** define KPI targets.
Targets belong to KPI Catalogs and strategy documents.

---

## 5. Trigger Design Rules

Triggers must be deterministic, machine-readable, time-aware, and unambiguous.

### Trigger Levels
- **L1 — Early Signal**
- **L2 — Required Intervention**
- **L3 — Prescriptive Execution**

Free-text conditions like “if relevant” are not allowed.

---

## 6. KPI Roles (Strict Separation)

Each Action Code distinguishes:
- Trigger KPIs
- Guardrail KPIs
- Outcome KPIs

---

## 7. Impact Definition Rules

Impact must be expressed as ranges, never point estimates.
Confidence must be justified.

---

## 8. Operational Execution Requirements

Every Action Code must specify:
- Real roles
- Concrete steps
- Effort
- Risks

---

## 9. Tracking & Learning (Mandatory)

Action Codes support execution tracking and outcome evaluation
via customer-owned tables.

---

## 10. Relationship to Use Cases & Reports

Action Codes are derived from Core Use Cases.
Reports surface Action Codes but do not redefine them.

---

## 11. Quality Gate (10/10 Check)

An Action Code is final only if it:
- Conforms to the template
- Supports a Strategic KPI
- Is executable without consultants
- Is measurable
- Is reusable

---

## 12. Design Principles

- Fewer Action Codes, higher quality
- Precision over completeness
- Determinism over explanation
- Scalability over showcase value
- Customer operability over theoretical purity
