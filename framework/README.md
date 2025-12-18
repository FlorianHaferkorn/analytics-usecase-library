# Framework (WITH WHAT)

## Purpose

This folder contains the **reusable, governed building blocks** of the Analytics Use Case Library.

It defines *what* is used to build analytics solutions — independent of a specific customer, project, or dataset.

The framework is intentionally **opinionated, minimal, and scalable**. Every artifact exists to reduce ambiguity, accelerate delivery, and enable automation.

---

## What the Framework Is

The framework provides:

* Standardized **templates** for reports, pages, measures, and data contracts
* A governed **KPI catalog** with clear business meaning and actionability
* A prescriptive **Action Code system** to move from insight to decision
* Shared **glossaries** to align business and technical language
* Platform-specific **implementation guides** (optional, non-binding)

All assets are designed to be:

* Human-readable and machine-readable
* Reusable across domains and use cases
* Suitable for manual delivery *and* agent-based automation

---

## What the Framework Is Not

The framework deliberately does **not** include:

* Customer-specific implementations
* Project delivery plans or timelines
* Operational processes or roles
* Tool configuration beyond reusable patterns

These topics belong to:

* `docs/company/` (WHY)
* `docs/operating_model/` (HOW)

---

## Folder Structure

```
framework/
  templates/               Reusable build artifacts (SSOT)
  action_codes/            Prescriptive Action Codes portfolio
  kpi_catalog/             Domain KPI catalogs (Markdown + embedded YAML)
  glossary/                Business and technical terminology
  implementation_guides/   Optional platform-specific guidance
```

### templates/

Single Source of Truth for all **build-time artifacts**.

Includes:

* Page templates (T1–T4) and governance
* Measure templates and naming conventions
* Data contract templates (dimensions, facts)
* Reusable components (e.g. Action Panel spec)

Templates define *structure and rules*, not customer content.

### action_codes/

The **prescriptive layer** of the framework.

Action Codes define:

* When an action should be triggered
* Who owns the decision
* What the recommended next step is

They are mandatory for prescriptive analytics (T4) and optional elsewhere.

### kpi_catalog/

The **business meaning layer**.

Each domain has its own KPI catalog:

* Markdown document with embedded YAML (single source of truth)
* Clear ownership, impact dimension, and actionability
* Designed for reuse across use cases

There are no duplicate YAML files.

### glossary/

Shared language for consistency:

* Business glossary (terms, definitions)
* Technical glossary (analytics, data, BI terms)

Glossaries reduce misinterpretation and onboarding effort.

### implementation_guides/

Optional, **non-normative** guidance for specific platforms (e.g. Fabric / Power BI).

They explain *how* the framework can be implemented — not *what* must be done.

---

## How the Framework Is Used

### For Customers

* Understand what is standardized vs. flexible
* Reuse proven patterns instead of starting from scratch
* Know what must be maintained when extending analytics

### For Delivery Teams

* Always start from framework templates
* Treat KPI catalogs and Action Codes as governed assets
* Avoid project-specific reinvention

### For Automation / Agents

* Deterministic structure
* Clear Single Sources of Truth
* No redundant or ambiguous artifacts

---

## Design Principles

* **Ease of use over theoretical purity**
* **Single Source of Truth over convenience copies**
* **Prescriptive over descriptive where meaningful**
* **Minimal surface area for customers**

If an artifact increases maintenance effort without clear benefit, it does not belong in the framework.

---

## Relation to Other Layers

* **WHY** → `docs/company/`
* **HOW** → `docs/operating_model/`
* **WITH WHAT** → `framework/`

Framework assets are consumed by:

* `usecases/`
* `semantic_models/`
* `data_contracts/`
