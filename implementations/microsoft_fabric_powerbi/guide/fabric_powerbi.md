# Microsoft Fabric & Power BI Implementation Guide

## Purpose

Translate the **ActionReady Operating Model** into a precise, repeatable, and scalable implementation within **Microsoft Fabric** and **Power BI**.  
This guide defines *how* semantics, measure governance, data contracts, Action Codes, and distribution patterns are realized in the Fabric ecosystem.

## Scope

Included:

- Mapping of Operating Model → Fabric components  
- Lakehouse & Dataflows Gen2 ingestion patterns  
- PBIP semantic modeling standards  
- Measure System enforcement (`_Measures.tmdl`)  
- RLS/OLS patterns  
- Distribution & navigation rules  
- AI/Copilot readiness  
- Recommended workspace, folder, and project structure  
- **Report themes and Power BI Theme Generator** — standardized report themes aligned with framework conventions; Theme Generator lives in `implementations/microsoft_fabric_powerbi/tools/theme_generator/` and is part of Fabric/Power BI development; working, to be refined.

Not included:

- Customer-specific provisioning  
- ETL pipelines beyond standard patterns  
- Framework-agnostic architecture (see framework/strategy_operating_model/operating_model)

### Where this fits in the repo

- **Use case factsheets:** `framework/usecases/core/` (e.g. `COM-001_Sales_Performance/` Business and Technical Factsheets).
- **KPI catalog:** `framework/kpi_catalog/` — source for measure definitions and KPI mapping; used by TMDL generation.
- **Validation:** `_internal/tools/validation/run_stage1_checks.ps1` (docs/structure); `run_all_checks.ps1` (Stage 1 + Fabric checks).
- **Fabric checks:** `implementations/microsoft_fabric_powerbi/tools/run_fabric_checks.ps1` — measures vs KPI, TMDL vs measure dictionary, DAX best practices.
- **TMDL generation:** `_internal/tools/generation/generate_tmdl_measures.ps1` — generates `_Measures.tmdl` from KPI catalog; output to `implementations/microsoft_fabric_powerbi/dist` or a showcase path.

---

# 1. Operating Model → Fabric Mapping

| Operating Model Element | Fabric / Power BI Implementation |
|-------------------------|----------------------------------|
| Data Contracts          | Lakehouse tables / Dataflows Gen2 |
| Semantic Layer          | PBIP Dataset + TMDL |
| Measure System          | `_Measures.tmdl` (SSOT) |
| Action Codes            | Action Aggregates + Execution Layer |
| Distribution            | Apps + Navigation Map |
| Governance              | Workspaces + Git PBIP |
| AI Readiness            | Descriptions + Metadata + Glossary |

---

# 2. Data Ingestion Blueprint

## 2.1 Lakehouse (preferred)

- Use **Bronze → Silver → Gold** pattern for high-quality ingestion.  
- Map upstream systems to domain data contracts.  
- Use **Delta tables** with schema enforcement.  
- Partition Date-heavy facts by `DateKey`.

## 2.2 Dataflows Gen2 (when Lakehouse not possible)

- Use Data Contract templates as schema target.  
- Never merge heavy tables inside Dataflows.  
- Use only lightweight transformations and load into Lakehouse.

## 2.3 Naming & Foldering

- Domain-driven folder structure in Lakehouse Files:  

```yaml
/Sales
/Finance
/SCM
/ESG
/Shared
```

- All tables must follow the naming rule:  
`fact_<name>` or `dim_<name>`.

### 2.4 Descriptive table names (best-practice nomenclature)

Table names should be **descriptive** while staying within the `dim_` / `fact_` convention: avoid opaque abbreviations; use clear, domain-understandable terms.

| Short / legacy name | Preferred descriptive name | Domain / meaning |
|---------------------|----------------------------|------------------|
| `dim_queue` | `dim_case_queue` or `dim_support_queue` | Case/support queue dimension |
| `dim_issue` | `dim_issue_type` | Issue type / severity dimension |
| `fact_cases` | `fact_support_cases` or `fact_customer_cases` | Support case facts |
| `fact_wfm` | `fact_workforce_management` | Workforce management facts |
| `fact_ap` | `fact_accounts_payable` | Accounts payable facts |
| `fact_ar` | `fact_accounts_receivable` | Accounts receivable facts |
| `fact_cash` | `fact_cash_position` | Cash position / balance facts |
| `fact_cashflow` | `fact_cash_flow` | Cash flow facts (OCF, CapEx, etc.) |

- **Gold data folders** should match the table name (e.g. `facts/fact_accounts_payable` if the table is `fact_accounts_payable`).
- **New models and generators** should use the preferred names; existing Aurora CoreActionReady model may keep short names for backward compatibility until a coordinated rename (relationships, measures, and all references must be updated together).

---

# 3. Semantic Layer Implementation (PBIP)

## 3.1 PBIP Folder Structure

```yaml
<dataset>/
  definition/
    model.bim
    tables/
      <table>.tmdl
      _Measures.tmdl
    relationships/
  report/ (optional)
```

## 3.2 Semantic Modeling Rules

- **Star Schema only**.  
- **Dimensions conformed** across domains.  
- **Role-playing dates** explicitly defined (Date, Posting Date, Invoice Date, …).  
- **NO calculated columns**, except SortBy or static mapping columns.  
- All additive logic implemented as Measures.

## 3.3 Relationships

- Single direction  
- Many-to-one  
- Active only when required  
- Avoid bi-directional relationships

---

# 4. Measure System Enforcement

## 4.1 `_Measures.tmdl` as Single Source of Truth

- All measures must be defined in `_Measures.tmdl`.  
- No measures inside table-level TMDLs unless absolutely mandatory.

## 4.2 Supporting vs KPI Measures

- KPI Measures must map to a `kpi_id` from the KPI Catalog.  
- Supporting measures must be **hidden**, reusable, and placed in Folder `10_Tech`.

## 4.3 Naming & Formatting Enforcement

- Follows `measure_system.md`.  
- Currency formatting via FormatString `"€ #,0.00"` – not in the name.  
- Percent formatting `"0.0 %"`.

## 4.4 Folder Structure

```yaml
00_KPIs
01_Sales
02_Finance
03_SCM
10_Tech
```

---

# 5. Action Codes in Power BI

## 5.1 Action Aggregates

Modeled as separate fact tables:

- `agg_price_leakage`
- `agg_downtime_rootcause`
- Domain-specific Action Fact tables.

## 5.2 Execution Layer

Fact table: `fact_action_execution`

- Captures trigger levels (L1/L2/L3)
- Pre/Post KPI values  
- Execution metadata  
- Notes & tracking

## 5.3 Trigger Logic

Implemented as Measures:

- `Trigger L1 Flag`
- `Trigger L2 Flag`
- `Trigger L3 Flag`

---

# 6. RLS & OLS Patterns

## 6.1 RLS (Dimension-Based)

- Always implemented on **dimensions**, never facts.  
- Recommended patterns:
  - Org-based RLS  
  - Region/BU filters  
  - User → Org mapping table

## 6.2 OLS (Sensitive Columns)

Use when hiding sensitive data:

- HR metrics  
- Margin-cost-level metrics  
- Use `objectLevelSecurity` in PBIP TMDL.

## 6.3 Least Privilege Pattern

Roles:

- Viewer  
- Analyst  
- Admin  
- Data Steward (optional)

---

# 7. Distribution & Navigation

## 7.1 App Structure

- One app per domain OR one app per persona (depending on org size).  
- Always include:
  - Landing Page  
  - Domain Overview → Insights → Explorer  
  - Glossary & KPI Page  

## 7.2 Navigation Pattern

3-30-300 UI enforced via:

- Top-level KPIs (3-sec)  
- Trends/Rankings (30-sec)  
- Explorer Table (300-sec)  

## 7.3 Deployment Pipeline

- Workspace separation:

```yaml
DEV
TEST
PROD
```

- Use deployment pipelines + rules.

---

# 8. AI & Copilot Readiness

## 8.1 Descriptions

Every measure must have:

- Purpose  
- Definition  
- Grain  
- Unit  
- Lineage  
- QA  

## 8.2 Metadata

- Table descriptions  
- Column descriptions  
- Folder descriptions  
- KPI → Glossary mapping  

## 8.3 Semantic Exposure

- Ensure Copilot sees context via KPI Catalog + Glossary.  
- No ambiguous names across domains.

---

# 9. Recommended Workspace Structure

## 9.1 Data Engineering

```yaml
DE_Lakehouse
DE_Dataflows
DE_Sources
```

## 9.2 Data Models

```yaml
DM_Core
DM_Domains
DM_ActionReady
```

## 9.3 Reporting

```yaml
BI_Apps
BI_Reports
BI_Experiments
```

## 9.4 Report Themes and Power BI Theme Generator

- Report themes (JSON) define visual consistency across reports (colors, fonts, layout defaults).
- The framework uses **BaseThemes** (e.g. `Base_Theme_Template_V1.json`) and derived themes (e.g. per brand or app) under `StaticResources/SharedResources/BaseThemes/` in PBIP report projects.
- **Power BI Theme Generator** — lives in `implementations/microsoft_fabric_powerbi/tools/theme_generator/` and generates Power BI themes (JSON) plus documentation (Markdown) from a single color prompt (Light/Dark, multiple concepts). It is part of the Fabric/Power BI development stack. Minimal usage (Windows): `cd implementations/microsoft_fabric_powerbi/tools/theme_generator`, `py -m pip install -r tools/theme-agent/requirements.txt`, then `./theme.ps1 -Action all -Color '#118DFF' -Concept Monochromatic -Mode Both -Brand 'Generic'`. More: `theme_generator/README.md`, `theme_generator/USAGE_Agent.md`.

**Base vs custom theme:** The base theme is fixed (e.g. in `StaticResources/SharedResources/BaseThemes/`); do not change it. The standardized look is applied via a **custom theme** in `StaticResources/RegisteredResources/`, referenced in report.json as `themeCollection.customTheme` and in `resourcePackages` as type `CustomTheme`. Use **apply_report_theme** to copy a theme into a report and wire base + custom in `definition/report.json` (PBIP definition format only).

**Theme schema (official):** The report theme JSON schema is published by Microsoft in [powerbi-desktop-samples](https://github.com/microsoft/powerbi-desktop-samples) (Report Theme JSON Schema). A pinned version is kept in `theme_generator/themes.config.json` (`reportThemeSchemaVersion`). Run **fetch_latest_theme_schema.py** with `--update-pin` to fetch the latest schema and update the pin; validation and theme generator use the pinned schema. Run from repo root: `py implementations/microsoft_fabric_powerbi/tools/theme_generator/tools/theme-agent/fetch_latest_theme_schema.py --update-pin`.

**Customer rollout:** When rolling the framework out to customers, keep report look consistent: (1) Default theme can come from `theme_generator/themes/` (e.g. Generic or a branded theme). (2) One-time optional: run `fetch_latest_theme_schema.py --update-pin` so validation uses the latest schema. (3) For every new report, use the page scaffold generator with `--theme <name>` so the theme is applied in one step, or run `apply_report_theme` so all reports share the same base + custom theme.

## 9.5 Shared Assets

```yaml
Shared_Datasets
Shared_Parameters
Shared_Tools
```

---

# 10. Pitfalls & Anti-Patterns

- Blending Dataflows + Lakehouse incorrectly  
- Calculated Columns for logic  
- Bi-directional relationships  
- Wildly inconsistent DisplayFolders  
- More than 7 KPIs on Overview pages  
- Overuse of bookmarks  
- Using DAX for row-by-row logic  
- No descriptions → breaks Copilot

---

# 11. Fabric & Power BI best practices and validation

- **TMDL:** Follow `tmdl_best_practices.md` (this guide folder) — tabs only, `///` comments, `displayFolder`/`formatString`, no `description` property, `let...in` for M.
- **DAX:** Measures are checked against DAX best-practice rules (e.g. avoid `ISERROR`/`IFERROR`, prefer `VAR` over `EARLIER`, no shortened `CALCULATE` syntax, use `DIVIDE(..., BLANK())` for safe division). Rules: `_internal/tools/linters/powerbi/bpa-rules-dax.json`; runner: `implementations/microsoft_fabric_powerbi/validation/check_dax_best_practices.ps1`.
- **TMDL syntax:** Run `check_tmdl_syntax.ps1` (tabs-only indentation, no `description:` property) as part of `run_fabric_checks.ps1`.
- **Run Fabric checks:** After changing measures or TMDL, run `implementations/microsoft_fabric_powerbi/tools/run_fabric_checks.ps1` (TMDL syntax, measures vs KPI catalog, TMDL vs measure dictionaries, DAX rules). Fix any failures before commit.

## 11.1 Semantic model and table best practices (Microsoft Learn)

**Star schema:** Use star schema only. Classify tables as dimension (filtering/grouping) or fact (summarization). Table type is determined by relationships: the “one” side is dimension, the “many” side is fact. Avoid mixing both in a single table. Use the right number of tables and relationships; keep fact tables at a consistent grain.

**Explicit measures:** Create explicit DAX measures for business metrics. Avoid relying on implicit measures for KPIs; set correct default summarization on numeric columns. Use explicit measures when report authors use MDX (e.g. Analyze in Excel, paginated reports).

**Naming:** Use clear, business-friendly names for tables, columns, and measures (e.g. “Total Revenue”, “Sales Region”). Avoid codes like `TR_AMT`, `DIM_GEO_01` unless descriptions/synonyms clarify them. Non-descriptive names reduce Copilot/data agent accuracy.

**Descriptions:** Add `///` comments above tables, columns, and measures (TMDL does not support a `description` property). Descriptions improve tooltips and Prep for AI / Copilot interpretation.

**Prep for AI:** Configure AI data schema (subset of tables/columns/measures), verified answers, and AI instructions in Power BI (Desktop or service). Semantic-model-specific guidance belongs in Prep for AI, not in data agent–level instructions.

**Direct Lake:** For Direct Lake semantic models, use tables (not views) from the SQL analytics endpoint; views cause fallback to DirectQuery and slower performance.

**Pitfalls to avoid:** Flat/denormalized or pivoted tables (DAX is optimized for star schema); verified answers that reference hidden columns (they will not work); including unnecessary or duplicate measures in the AI schema; implicit measures for key metrics; ambiguous date fields without AI instructions or verified answers; conflicting AI instructions.

---

# 12. Minimal Example

```yaml
dataset/
  definition/
    _Measures.tmdl
    tables/
      fact_sales.tmdl
      dim_product.tmdl
      dim_date.tmdl
```

Example KPI Measure snippet:

```yaml
/// sales.net_sales.amount – Net Sales Amount
measure Net Sales Amount =
    SUM ( fact_sales[Net Sales Amount] )
```

---

**Sources (Microsoft Learn):** [Semantic model best practices for data agent](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices), [Star schema and Power BI](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema), [Develop Direct Lake semantic models](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-develop).

**Location:**  
`implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md`
