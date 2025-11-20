# Business Playbook – Analytics Use Case Framework

Purpose: Explain in plain language how to work with the Analytics Use Case Framework – who provides what, how the process flows, and what the scripts/Agent deliver.

---

## Who This Is For
- Business owners and domain experts who define goals and KPIs
- Analysts and product owners who shape Use Cases
- Data/BI teams who operationalize semantic models and reports

---

## What You Can Achieve
- Turn business goals into standardized Use Cases that can be turned into working reports.
- Reuse a shared KPI Catalog with stable IDs to ensure consistency across teams.
- Automate measure creation and quality checks to speed up delivery while improving governance.

---

## Roles & Responsibilities (Who provides what)

- **Business Owner (domain)**:
  - Defines the business goal, key questions, and expected impact.
  - Selects required KPIs (by name) together with the Analyst.

- **Analyst / Product Owner**:
  - Fills the Use Case FactSheet (IDs for KPIs, segments, default filters).
  - Describes Data Requirements in business terms (facts, dims, relationships).
  - Links the Use Case to strategy (strategic KPIs) and action codes.

- **Data / BI Team**:
  - Maps canonical labels to model fields (`model_mapping`).
  - Validates data availability against Data Requirements.
  - Curates KPI Catalog entries and approves new KPIs/IDs.

- **Automation (Scripts / Agent)**:
  - Resolves `required_kpi_ids` in catalogs, generiert/aktualisiert Measures (`_Measures.tmdl`).
  - Wendet Formatstrings, DisplayFolder und Beschreibungen aus dem Katalog an.
  - Führt Coverage- und Konsistenz-Checks aus (`run_all_checks.ps1`).

---

## Golden Path (How it works)

1. Define Reporting Strategy and Strategic KPIs (business).  
2. Identify influencing KPIs and cluster them into Use Cases (business + analyst).  
3. Author the Use Case FactSheet (analyst):
   - `required_kpi_ids` (from KPI Catalog)
   - `segments` and `filters_default`
   - `data_requirements` and `model_mapping` (business-level; no code)
4. Automate measures (scripts/Agent):
   - Look up KPIs by ID in the catalogs.
   - Create or patch measures in the semantic model via  
     `.\tools\generate\generate_tmdl_measures.ps1 -UseCase <ID> -OverwriteExisting`  
     oder für alle Use Cases: `.\tools\generate_all_measures.ps1 -StubOnly`.
   - Run coverage and consistency checks: `.\tools\run_all_checks.ps1`.

---

## What You Provide vs What the Automation Provides

- **You provide**
  - Use Case FactSheet content: goals, questions, `required_kpi_ids`, `segments`, `filters_default`.
  - Data Requirements (facts/dims/relationships) and `model_mapping` labels.
  - Strategic links (`supports_strategic_kpi_ids`), Action Codes.

- **Automation provides**
  - Measure creation (from KPI Catalog technical blocks and safe templates).
  - Measure-Regeneration, wenn sich KPI-Katalog oder Use Case ändern.
  - Diagnostics: best-practice linting (Katalog/Factsheets) und KPI-Coverage.

---

## Authoring a Use Case (non-technical)

Fill `usecases/<cluster>/<UC-ID>_<Title>/FactSheet.md` front-matter:
- `id`, `title`, `domain`, `owner`, `impact`, `status`, `last_update`
- `supports_strategic_kpi_ids`, `action_codes`, `expected_impact`
- `required_kpi_ids` (IDs) and `required_kpis` (human names)
- `segments` (e.g., `Org.Region>Area>Store`) and `filters_default` (e.g., `Time: Last 12M`)
- `data_requirements` (facts/dims/relationships) and `model_mapping` (labels → model fields)

Tips:
- Choose only the KPIs needed to answer the key questions.
- Keep segments and defaults minimal; avoid mutually exclusive filters.
- Use existing KPIs before proposing new ones; if needed, add to catalogs with a new `kpi_id`.

---

## KPI Catalog, IDs & Measure Naming (why they matter)

- KPI Catalogs live in `/_includes/kpi_catalog/`.
- Each KPI has a stable ASCII `kpi_id` (e.g., `margin.gm.pct`, `fin.liquidity.free_cash_flow`).
- Use these IDs in Use Cases; names with symbols (z.B. `Δ`, `%`, `€`) bleiben in `kpi_key` und Measure-Namen.
- The automation uses IDs to generate the right measures regardless of encoding or language.
- Naming and formatting conventions for measures in `_Measures.tmdl`:
  - Use the **Delta symbol `Δ`** in measure names for variances (e.g., `Δ Net Sales Amount`, `Δ% Net Sales`, `Δ Gross Margin %`).
  - Use the **Euro symbol `€`** in `formatString` for currency formats (e.g., `"€ #,0.00"`, `"€ #,0"`).
  - Use `DIVIDE()` in DAX for ratios instead of `/`, and `SAMEPERIODLASTYEAR('Date'[Date])` for simple LY comparisons.

---

## Data Requirements (business language)

- **facts**: business tables with a grain (e.g., `invoice_line`) and required columns.
- **dims**: lookup tables (date, org, product), keys and important attributes.
- **relationships**: how facts join to dims (direction, RI expectations).
- **model_mapping**: link canonical labels (e.g., "Net Sales Amount") to the actual model fields.

Outcome: The automation can validate data readiness or scaffold a model if one doesn't exist yet.

---

## Quality & Validation (what happens automatically)

- Coverage:
  - Every `required_kpi_id` must exist in the catalogs (`check_factsheet_vs_kpi.ps1`).
- Measures vs Catalog:
  - Every KPI referenced in `_Measures.tmdl` must have a `kpi_id` in the catalogs (`check_measures_vs_kpi.ps1`).
- Additional best practices (optional, später ausbaubar):
  - DAX patterns (DIVIDE statt `/`, LY mit `SAMEPERIODLASTYEAR`).
  - Formatstrings, DisplayFolder, Beschreibungen auf Measures.

---

## FAQ

- **Can I add a new KPI?**  
  Ja. Propose an ID and add an entry in the relevant KPI catalog using the schema in `SCHEMA.md`. Keep IDs ASCII and descriptive.

- **What if I don't know DAX?**  
  The scripts use catalog technical blocks and safe templates (Δ, Δ%, LY). Provide business definitions; the measures werden generiert.

- **Do I need a finished data model?**  
  No. Use the Data Requirements block. Die Automation kann Datenverfügbarkeit prüfen und bei Bedarf ein Modellgerüst erzeugen.

---

Start here: Use COM-001 in `usecases/01_Commercial/COM-001_Sales_Performance/FactSheet.md` as the working example.

For a one-screen summary, see: `./Quickstart_1-Pager.md`.

Last updated: 19.11.2025


