# Measure Templates

> **Canonical measure system:** [measure_system.md](../../strategy_operating_model/operating_model/measure_system.md).  
> These templates are scaffolds; naming and taxonomy are defined in the measure system.

## Purpose

This folder contains the **standard template for defining semantic model measures**
in the Analytics Use Case Library.

It ensures that measures are:

- reusable
- governed
- KPI-aligned
- AI / Copilot ready

---

## Core Principle

> **All business logic lives in measures.**

Measures are the **single execution layer** for KPIs, Action Codes, and reports.

---

## Usage Rules (Mandatory)

- Every KPI Measure must:
  - reference a `kpi_id` from the KPI Catalog
  - include a business description
  - define grain and lineage
- Supporting Measures must:
  - be reusable
  - be hidden by default
  - not duplicate KPI logic
- Calculated columns are avoided except for technical necessities

---

## What belongs here

- The canonical **Measure Template**
- Rules for measure documentation and structure

## What does NOT belong here

- KPI definitions (see KPI Catalog)
- Business interpretation (see Use Cases)
- Tool-specific implementation guides

---

## Relations

- **KPI Catalog:** Defines *what* is measured
- **Measure Template:** Defines *how* it is calculated
- **Semantic Model:** Implements the template
- **Action Codes:** Consume measure outputs

---

**Location:**  
`core/templates/measure_templates/`
