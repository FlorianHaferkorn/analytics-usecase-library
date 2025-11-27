Status: Archive
Note: This file was moved to /archive because it does not fit the current target structure. Review and delete or migrate if still needed.

# Analytics Use Case Framework â€“ Quickstart (1-Pager)

Audience: Business owners, analysts, product owners. Goal: Turn a Use Case into a working report (theme/layout optional) with minimal friction.

---

## Outcome (What you get)
- A standardized Business + Technical factsheet pair that the scripts/Agent convert into:
  - Validated data requirements (facts/dims/relationships)
  - Measures generated from the KPI Catalog (by `kpi_id`)
  - A consistent `_Measures.tmdl` per Use Case
  - Best-practice checks and a short build log (`run_all_checks.ps1`)

---

## Your 5 Steps (Business/Analyst)
1. Define the business goal and key questions.  
2. Pick the KPIs from the Catalog (use `kpi_id`s).  
3. Fill the Business factsheet front-matter:
   - `required_kpi_ids` (IDs) + `required_kpis` (readable names)
   - `segments` (e.g., `Org.Region>Area>Store`) & `filters_default` (e.g., `Time: Last 12M`)
   - `data_requirements` (facts/dims/relationships) & `model_mapping` (labels â†’ model fields)
4. Link to strategy (`supports_strategic_kpi_ids`) and add `action_codes`.  
5. Run the tooling from the repo root:
   - `.\tools\generate\generate_tmdl_measures.ps1 -UseCase COM-001 -OverwriteExisting`
   - `.\tools\run_all_checks.ps1`

---

## What the Automation Does
- Resolves KPI IDs in catalogs â†’ generates/patches measures (`_Measures.tmdl`) based on the KPI catalogs.
- Applies format strings, display folders, and descriptions from the Catalog.
- Ensures coverage:
  - `required_kpi_ids` â†” KPI Catalog (`check_factsheet_vs_kpi.ps1`)
  - KPI references in `_Measures.tmdl` â†” KPI Catalog (`check_measures_vs_kpi.ps1`)

---

## Inputs per Use Case (Front-Matter)

- `id`, `title`, `domain`, `owner`, `impact`, `status`, `last_update`
- `supports_strategic_kpi_ids`, `action_codes`, `expected_impact`
- `required_kpi_ids`, `required_kpis`
- `segments`, `filters_default`, `qa_asserts`
- `data_requirements` (facts/dims/relationships)
- `model_mapping` (canonical labels â†’ model fields)

Template: `usecases/UC-000_Template.md`

---

## Where to Find KPIs & IDs

- KPI Catalogs: `/_includes/kpi_catalog/` (IDs are ASCII, stable)
- Schema & authoring rules: `/_includes/kpi_catalog/SCHEMA.md`
- Strategic overview: `/_includes/Strategic_KPIs.md`

---

## Data Readiness (Business language)

- **facts**: name, grain (e.g., `invoice_line`), primary key, required columns with types/roles
- **dims**: date/org/product keys & attributes
- **relationships**: joins + referential integrity expectation
- **model_mapping**: link labels (e.g., "Net Sales Amount") to actual fields (e.g., `fact_sales[Net Sales Amount]`)

---

## Example (Start here)

- `usecases/01_Commercial/COM-001_Sales_Performance/Business_Factsheet.md`
- Business Playbook (non-technical guide): `./Business_Playbook.md`

---

## VS Code & CI â€“ How to use it fast

- **Tasks** (VS Code â†’ â€žRun Taskâ€¦â€œ):
  - `Generate measures for Use Case` â†’ Measures fÃ¼r eine UC-ID erzeugen/aktualisieren.
  - `Generate all measures` â†’ alle `_Measures.tmdl` aus KPI-Katalogen generieren.
  - `Generate all & run all checks` â†’ Generierung + kompletter QualitÃ¤tslauf in einem Schritt.
- **Snippets**:  
  - Tippe `uc-business` â†’ Tab, um Frontmatter + Business-Outline einzufÃ¼gen.  
  - Tippe `uc-technical` â†’ Tab, um die Technical-Outline einzufÃ¼gen.
- **CI** (GitHub):  
  - Workflow `.github/workflows/run-all-checks.yml` fÃ¼hrt `tools/run_all_checks.ps1` bei Push/PR aus und blockt PRs bei Fehlern.

Last updated: 27.11.2025

