# Data Contract Templates

## Purpose

These templates define the **standard structure for Data Contracts** used in
ALUCA (Analytics Library of Use Cases).

Data Contracts specify **what data must look like** to support KPIs, Use Cases,
and Action Codes — not how data is ingested or transformed.

---

## What these templates are

- Canonical schemas for:
  - Dimensions (`dim_template.yaml`)
  - Facts (`fact_template.yaml`)
- A governed interface between source systems and the semantic layer
- The foundation for:
  - consistent semantic models
  - reusable KPIs
  - scalable use cases

---

## What these templates are NOT

- Not ETL or pipeline definitions
- Not physical storage designs
- Not customer-specific schemas
- Not optional documentation

---

## Usage Rules (Mandatory)

- One Data Contract per **domain**
- Grain must be explicitly defined
- Ownership (business & data) is required
- Fields without KPI or Use Case relevance are not allowed
- Changes to contracts may impact multiple domains and must be reviewed

---

## Relations

- **WHY:** Derived from domains and KPIs
- **HOW:** Enforced by the Semantic Layer
- **WITH WHAT:** Used by semantic models and measures
- **WHAT:** Required by all Core Use Cases

---

**Location:**  
`core/templates/data_contract_templates/`
