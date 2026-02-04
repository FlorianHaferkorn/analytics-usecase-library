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
- **Report themes and Power BI Theme Generator** — standardized report themes aligned with framework conventions; Theme Generator (dedicated folder, to be documented here once path is fixed) is part of Fabric/Power BI development; working, to be refined.

Not included:

- Customer-specific provisioning  
- ETL pipelines beyond standard patterns  
- Framework-agnostic architecture (see docs/operating_model)

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
- **Power BI Theme Generator** — a dedicated tool (folder/location to be documented in this guide) generates or standardizes report themes from framework conventions. It is part of the Fabric/Power BI development stack, already in use, and will be refined and documented alongside this implementation guide.

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

# 11. Minimal Example

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

**Location:**  
`framework/implementation_guides/fabric_powerbi.md`
