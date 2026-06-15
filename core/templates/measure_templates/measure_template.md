# Measure Template

## Purpose

Standardized template for defining **semantic model measures** in ALUCA (Analytics Library of Use Cases).

This template ensures:

- consistent KPI implementation
- reuse across reports and use cases
- AI / Copilot readiness
- clear separation of business and technical logic

---

## Measure Definition

### Measure Name

`<Measure Name>`

### Measure Type

- KPI Measure
- Supporting Measure

---

## Business Description (Mandatory)

**Purpose**  
What business question does this measure answer?

**Definition**  
Clear, unambiguous description of the calculation logic  
(numerator / denominator, inclusions, exclusions).

**Business Grain**  
At which level the measure is meaningful  
(e.g. Invoice Line, Customer-Month, Store-Day).

---

## Technical Definition

**DAX Expression**

```DAX
<Insert DAX here>
```

**Dependencies**

- Tables:
  - `<fact_*>`
  - `<dim_*>`
- Supporting Measures:
  - `<Measure A>`
  - `<Measure B>`

---

## KPI Reference (if applicable)

- KPI ID: `<kpi_id from KPI Catalog>`
- Impact Dimension: `<Growth | Profitability | Liquidity | Efficiency | Customer Value | ESG | Governance | Risk>`

---

## Formatting & UX

- Format String: `<e.g. "€ #,0.00" | "0.0 %">`
- Display Folder: `<01_Revenue | 02_Margin | …>`
- Visible to End Users: `Yes / No`

---

## Quality & Validation

**Expected Range**

- `<min> – <max>` or `Not applicable`

**QA Rules**

- `<rule 1>`
- `<rule 2>`

---

## Lineage

- Source System(s): `<ERP, CRM, …>`
- Data Contract Reference: `<fact_xxx, dim_xxx>`

---

## Notes

Optional implementation or interpretation notes.

---

**Rule:**  
All KPI Measures must reference a KPI ID from the KPI Catalog.  
Supporting Measures must be reusable and hidden by default.
