# Business Playbook — Analytics Use Case Framework

Purpose: Explain in plain language how to work with the Analytics Use Case Framework — who provides what, how the process flows, and what the Agent/MCP delivers.

---

## Who This Is For
- Business owners and domain experts who define goals and KPIs
- Analysts and product owners who shape Use Cases
- Data/BI teams who operationalize semantic models and reports

---

## What You Can Achieve
- Turn business goals into standardized Use Cases that the Agent/MCP can transform into working reports (theme/layout can follow later).
- Reuse a shared KPI Catalog with stable IDs to ensure consistency across teams.
- Automate measure creation and quality checks to speed up delivery while improving governance.

---

## Roles & Responsibilities (Who provides what)
- Business Owner (domain):
  - Defines the business goal, key questions, and expected impact
  - Selects required KPIs (by name) with the Analyst
- Analyst / Product Owner:
  - Fills the Use Case FactSheet (IDs for KPIs, segments, default filters)
  - Describes Data Requirements in business terms (facts, dims, relationships)
  - Links the Use Case to strategy (strategic KPIs) and action codes
- Data / BI Team:
  - Maps canonical labels to model fields (model_mapping)
  - Validates data availability against Data Requirements
  - Curates KPI Catalog entries and approves new KPIs/IDs
- Agent/MCP:
  - Resolves required_kpi_ids in catalogs, generates/patches measures
  - Scaffolds a report page (based on `page_template` later)
  - Runs best‑practice checks and coverage; reports gaps

---

## Golden Path (How it works)
1) Define Reporting Strategy and Strategic KPIs (business)
2) Identify influencing KPIs and cluster them into Use Cases (business + analyst)
3) Author the Use Case FactSheet (analyst):
   - required_kpi_ids (from KPI Catalog)
   - segments and filters_default
   - data_requirements and model_mapping (business‑level; no code)
4) Agent/MCP (automation):
   - Look up KPIs by ID in the catalogs
   - Create/patch measures in the semantic model (DAX/templates)
   - Build a report page (template), wire visuals to measures
   - Apply best practices and coverage; produce a short build log

---

## What You Provide vs What the Agent Provides
- You provide
  - Use Case FactSheet content: goals, questions, required_kpi_ids, segments, filters_default
  - Data Requirements (facts/dims/relationships) and model_mapping labels
  - Strategic links (supports_strategic_kpi_ids), Action Codes
- Agent provides
  - Measure creation (from KPI Catalog technical blocks and safe templates)
  - Report scaffolding (page template, slicers from segments, default filters)
  - Diagnostics: best‑practice linting (semantic model/report) and KPI coverage

---

## Authoring a Use Case (non‑technical)
Fill `usecases/<cluster>/<UC-ID_Title>/FactSheet.md` front‑matter:
- id, title, domain, owner, impact, status, last_update
- supports_strategic_kpi_ids (ID list), action_codes, expected_impact
- required_kpi_ids (IDs) and required_kpis (human names)
- segments (e.g., Org.Region>Area>Store) and filters_default (e.g., Time: Last 12M)
- data_requirements (facts/dims/relationships) and model_mapping (labels → model fields)

Tips
- Choose only the KPIs needed to answer the key questions
- Keep segments and defaults minimal; avoid mutually exclusive filters
- Use existing KPIs before proposing new ones; if needed, add to catalogs with a new kpi_id

---

## KPI Catalog & IDs (why they matter)
- KPI Catalogs live in `/_includes/kpi_catalog/`
- Each KPI has a stable ASCII `kpi_id` (e.g., `margin.gm.pct`, `fin.liquidity.free_cash_flow`)
- Use these IDs in Use Cases; names with symbols (e.g., Δ, %) remain human‑friendly in `kpi_key`
- The Agent uses IDs to generate the right measures regardless of encoding or language

---

## Data Requirements (business language)
- facts: business tables with a grain (e.g., invoice_line) and required columns
- dims: lookup tables (date, org, product), keys and important attributes
- relationships: how facts join to dims (direction, RI expectations)
- model_mapping: link canonical labels (e.g., "Net Sales Amount") to the actual model fields

Outcome: The Agent can validate data readiness or scaffold a model if one doesn’t exist yet.

---

## Quality & Validation (what happens automatically)
- Coverage: Every `required_kpi_id` must exist in the catalogs
- Best Practices (semantic model/report):
  - DAX rules (e.g., DIVIDE instead of `/`, LY with SAMEPERIODLASTYEAR)
  - Format strings, display folders, and descriptions on measures
  - Report hygiene per `schemas/best_practices/`

---

## FAQ
- Can I add a new KPI?
  - Yes. Propose an ID and add an entry in the relevant KPI catalog using the schema in `SCHEMA.md`. Keep IDs ASCII and descriptive.
- What if I don’t know DAX?
  - The Agent uses catalog technical blocks and safe templates (Δ, Δ%, LY). Provide business definitions; we’ll generate DAX.
- Do I need a finished data model?
  - No. Use the Data Requirements block. The Agent can validate/scaffold based on it and your model_mapping.

---

Start here: Use COM‑001 in `usecases/01_Commercial/COM-001_Sales_Performance/FactSheet.md` as the working example.

For a one‑screen summary, see: `./Quickstart_1-Pager.md`.

Last updated: 04.11.2025
