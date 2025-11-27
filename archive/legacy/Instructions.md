Status: Archive
Note: This file was moved to /archive because it does not fit the current target structure. Review and delete or migrate if still needed.

# Instructions for Authoring and Maintaining Use Cases

## 1. Purpose
This document defines how business analytics use cases are to be created, formatted, named, and maintained.  
It ensures consistency, traceability, and quality across all documentation within the **Analytics Use Case Library**.

---

## 2. File and Folder Structure (vereinfachte Ãœbersicht)

```text
/analytics-usecase-library/
  /docs/
    Concept_and_Conventions.md
    Business_Playbook.md
    Quickstart_1-Pager.md
    Instructions.md

  /usecases/
    /01_Commercial/
      COM-001_Sales_Performance/
        Business_Factsheet.md   # front-matter + business narrative
        Technical_Factsheet.md  # data contract, model + KPI binding
        FactSheet.md            # legacy stub pointing to the two files
      COM-002_Gross_Margin_Analysis/
        Business_Factsheet.md
        Technical_Factsheet.md
        FactSheet.md
      ...
    /02_Operational_Efficiency/
    /03_Customer_and_Market/
    /04_Corporate_and_Strategy/
    /05_ESG/
    /06_Governance/
    /07_Innovation_and_People/
    UC-000_Template.md

  /_includes/
    Glossary.md
    ActionCodes.md
    Strategic_KPIs.md
    Strategic_Alignment_Map.md
    UseCase_Inventory.md
    /kpi_catalog/
      SCHEMA.md
      KPI_Catalog_Growth.md
      KPI_Catalog_Profitability.md
      KPI_Catalog_Liquidity.md
      KPI_Catalog_Efficiency.md
      KPI_Catalog_CustomerValue.md
      KPI_Catalog_ESG.md
      KPI_Catalog_Governance.md
      KPI_Catalog_InnovationPeople.md

  /dist/
    <UC-ID>/<SemanticModel>/
      definition/model.tmdl
      definition/tables/_Measures.tmdl

  /tools/
    run_all_checks.ps1
    new_usecase.ps1
    /generate/
      generate_tmdl_measures.ps1
      generate_all_measures.ps1
```

Each Use Case lives in its own folder with a `Business_Factsheet.md` and `Technical_Factsheet.md`.  
`FactSheet.md` remains as a stub for legacy links and redirects tooling to the Business file. All files follow the defined structure and metadata fields (see Section 4).

---

## 3. Naming Conventions

### 3.1 File Names
- Format: `{PREFIX}-###_Short_Title/Business_Factsheet.md` and `/Technical_Factsheet.md` (e.g., `COM-001_Sales_Performance/Business_Factsheet.md`)
- A minimal `FactSheet.md` stub stays in the folder for backward compatibility.
- `{PREFIX}` corresponds to the cluster code: COM, OPS, CST, COR, ESG, GOV, INN, HR.
- Use Title Case for folder titles, keine Leerzeichen oder Sonderzeichen.
- Keep titles concise and descriptive.

### 3.2 Use Case IDs
- Sequential numeric ID within the cluster (`COM-001`, `OPS-002`, â€¦)
- Once assigned, IDs are never reused.

### 3.3 KPI/Measure Naming (im Text)
- **Î”** prefix = absolute variance (e.g., `Î” Net Sales Amount`)
- **Î”%** prefix = relative variance (e.g., `Î”% Gross Margin`)
- **%** suffix = percentage metric (e.g., `Gross Margin %`)
- Amount = currency (0â€“2 decimals), Qty/Count = integer, % = 1 decimal.

---

## 4. Standard Layout for Each Use Case

Every Use Case follows the same Markdown template (`UC-000_Template.md`). The **front-matter now lives in `Business_Factsheet.md`** and is reused by automation through the `FactSheet.md` stub. Business narrative and technical deep-dive sit in their respective files.

```markdown
---
id: "COM-001"
title: "Sales Performance vs Plan & Last Year"
domain: "Commercial"
owner: "Head of Sales"
impact: "High"
status: "Active"
last_update: "DD.MM.YYYY"
supports_strategic_kpi_ids: ["sales.revenue.growth_pct","margin.gm.pct"]
action_codes: ["P2","D1"]
expected_impact: "+2â€“5 pp Î”% Net Sales; +0.5â€“1.5 pp Gross Margin %"
dataset_model: "COM-001.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Org.Region>Area>Store","Product.Category>Subcategory>SKU","Channel","Time.Year>Month>Week>Day"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK","DeltaPct_OnlyWhenPlanPositive"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.delta_amount.ly",
  "sales.net_sales.delta_pct.ly",
  "sales.price.realization_pct",
  "margin.gm.pct",
  "margin.gm.amount"
]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.delta_amount.ly: "Î” Net Sales Amount"
  sales.net_sales.delta_pct.ly: "Î”% Net Sales"
  margin.gm.pct: "Gross Margin %"
  margin.gm.amount: "Gross Margin Amount"
---

## Business Goal
Explain the strategic purpose of the analysis and why it matters for decision-making.

## Business Context
Summarize the background, challenges, and intended decisions supported by this analysis.

## Key Questions
- Main analytical question(s)
- Supporting drill-down questions

## Key KPIs
| KPI                | Definition                           | Unit | Format     |
|--------------------|--------------------------------------|------|-----------|
| Net Sales Amount   | Revenue excluding returns            | â‚¬    | â‚¬ #,0.00  |
| Î” Net Sales Amount | Absolute variance vs Last Year       | â‚¬    | â‚¬ #,0.00  |
| Î”% Net Sales       | Percentage variance vs Last Year     | %    | 0.0 %     |

## Typical Actions
- Describe concrete levers or actions derived from the analysis.
- Include both what to do and expected impact.

## Expected Business Impact
Summarize the expected improvement (e.g., "+2â€“5 pp Î”% Net Sales, +0.5 pp Gross Margin %").

## Related Processes
List linked operational or planning processes (e.g., Sales Planning, Promotion Management).

## Insights & Learnings
Document key takeaways, interpretation notes, or connections to other use cases.
```

---

## 5. Formatting and Style Guidelines

| Element | Rule |
|--------|------|
| Headings | Use `##` for section titles; no decorative symbols. |
| Lists | Use hyphens or numbers, consistent indentation. |
| Tables | Use Markdown syntax, no HTML. |
| Units | Always specify (â‚¬, %, days, pcs). |
| Dates | Format as `DD.MM.YYYY`. |
| Text | Keep concise, avoid marketing tone; focus on analytical meaning. |
| Line breaks | Use one blank line between sections. |
| No emojis | Maintain professional, machine-readable text. |

---

## 6. Review and Approval Workflow

1. Create a branch (optional, wenn Git-Workflow genutzt wird).  
2. Copy the template from `usecases/UC-000_Template.md`.  
3. Fill in all required sections following this guide.  
4. Run `.\tools\run_all_checks.ps1` und behebe Fehler/Warnungen.  
5. Review durch einen fachlichen und einen technischen Verantwortlichen.  

---

## 7. Governance and Versioning

| Element | Guideline |
|--------|-----------|
| Versioning | Minor = textual update; Major = KPI or logic change. |
| Status | `Draft`, `In Review`, `Active`, `Deprecated`. |
| Archiving | Deprecated Use Cases remain stored with final version tag. |
| Cross-References | Use relative Markdown links zwischen Use Cases und Dokus. |

---

## 8. Supporting Documents

| File | Purpose |
|------|---------|
| `docs/Reporting_Strategy.md` | Defines reporting levels, analytics stages, and governance layers. |
| `docs/Methodology.md` | Explains modeling, visualization, and standardization principles. |
| `docs/Concept_and_Conventions.md` | Single source of truth for naming and measure conventions. |
| `/_includes/Glossary.md` | Contains all abbreviations and analytical term definitions. |
| `/_includes/kpi_catalog/SCHEMA.md` | Schema and authoring rules for KPI catalogs. |

---

## 9. Quality Criteria (Definition of Done)

Ein Use Case ist **fertig**, wenn:

- Alle Pflichtfelder im Frontmatter und in den Kapiteln befÃ¼llt sind.  
- `required_kpi_ids` in den KPI-Katalogen existieren.  
- `run_all_checks.ps1` ohne Fehler durchlÃ¤uft (nur bekannte Warnungen).  
- Naming folgt den Konventionen (`Î”`, `Î”%`, `%`, `â‚¬`).  
- Die fachliche und technische Sicht den Use Case freigeben.  

---

_Last updated: 19.11.2025_

