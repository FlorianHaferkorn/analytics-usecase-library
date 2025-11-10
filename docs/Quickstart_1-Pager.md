# Analytics Use Case Framework — Quickstart (1-Pager)

Audience: Business owners, analysts, product owners. Goal: Turn a Use Case into a working report (theme/layout optional) with the Agent/MCP.

---

## Outcome (What you get)
- A standardized Use Case FactSheet that the Agent converts into:
  - Validated data requirements (facts/dims/relationships)
  - Measures generated from the KPI Catalog (by ID)
  - A scaffolded report page (template later), slicers from segments, default filters applied
  - Best-practice checks and a short build log

---

## Your 5 Steps (Business/Analyst)
1) Define the business goal and key questions
2) Pick the KPIs from the Catalog (use IDs)
3) Fill the FactSheet front-matter:
   - required_kpi_ids (IDs) + required_kpis (readable names)
   - segments (e.g., Org.Region>Area>Store) & filters_default (e.g., Time: Last 12M)
   - data_requirements (facts/dims/relationships) & model_mapping (labels → model fields)
4) Link to strategy (supports_strategic_kpi_ids) and add action_codes
5) Hand the Use Case folder to the Agent — it builds and validates

---

## What the Agent/MCP Does (Automation)
- Resolves KPI IDs in catalogs → generates/patches measures (DAX/templates)
- Applies format strings, display folders, and descriptions from the Catalog
- Builds a report page (template later), wires visuals to measures, adds slicers
- Runs best-practice checks (semantic model/report) and KPI coverage

---

## Inputs per Use Case (Front-Matter)
- id, title, domain, owner, impact, status, last_update
- supports_strategic_kpi_ids, action_codes, expected_impact
- required_kpi_ids, required_kpis
- segments, filters_default, qa_asserts
- data_requirements (facts/dims/relationships)
- model_mapping (canonical labels → model fields)

Template: `usecases/UC-000_Template.md`

---

## Where to Find KPIs & IDs
- KPI Catalogs: `/_includes/kpi_catalog/` (IDs are ASCII, stable)
- Schema & authoring rules: `/_includes/kpi_catalog/SCHEMA.md`
- Strategic overview: `/_includes/Strategic_KPIs.md`

---

## Data Readiness (Business language)
- facts: name, grain (e.g., invoice_line), primary key, required columns with types/roles
- dims: date/org/product keys & attributes
- relationships: joins + referential integrity expectation
- model_mapping: link labels (e.g., "Net Sales Amount") to actual fields (e.g., `fact_sales[Net Sales Amount]`)

---

## Example (Start here)
- `usecases/01_Commercial/COM-001_Sales_Performance/FactSheet.md`
- Business Playbook (non-technical guide): `./Business_Playbook.md`

Last updated: 04.11.2025


