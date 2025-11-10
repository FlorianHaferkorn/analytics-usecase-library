# Instructions for Authoring and Maintaining Use Cases

## 1. Purpose
This document defines how business analytics use cases are to be created, formatted, named, and maintained.  
It ensures consistency, traceability, and quality across all documentation within the **Analytics Use Case Library**.

---

## 2. File and Folder Structure
```
/analytics-usecase-library/
â”‚
â”œâ”€â”€ /docs/
â”‚   â”œâ”€â”€ Reporting_Strategy.md     â† defines reporting levels & architecture
â”‚   â”œâ”€â”€ Methodology.md            â† describes modeling & design principles
â”‚   â”œâ”€â”€ Instructions.md           â† authoring and governance rules
â”‚   â”œâ”€â”€ Changelog.md              â† version control and audit log
â”‚
â”œâ”€â”€ /usecases/
â”‚   â”œâ”€â”€ /01_Commercial/
â”‚   â”‚     â”œâ”€â”€ COM-001_Sales_Performance.md
â”‚   â”‚     â”œâ”€â”€ COM-002_Gross_Margin.md
â”‚   â”‚     â””â”€â”€ ...
â”‚   â”œâ”€â”€ /02_Operational_Efficiency/
â”‚   â”œâ”€â”€ /03_Customer_and_Market/
â”‚   â”œâ”€â”€ /04_Corporate_and_Strategy/
â”‚   â””â”€â”€ UC-000_Template.md
â”‚
â”œâ”€â”€ /_includes/
â”‚     â”œâ”€â”€ Glossary.md
â”‚     â”œâ”€â”€ ActionCodes.md
â”‚     â”œâ”€â”€ Strategic_KPIs.md
â”‚     â””â”€â”€ /kpi_catalog/
â”‚           â”œâ”€â”€ KPI_Catalog_README.md
â”‚           â”œâ”€â”€ KPI_Catalog_Growth.md
â”‚           â”œâ”€â”€ KPI_Catalog_Profitability.md
â”‚           â”œâ”€â”€ KPI_Catalog_Liquidity.md
â”‚           â”œâ”€â”€ KPI_Catalog_Efficiency.md
â”‚           â”œâ”€â”€ KPI_Catalog_CustomerValue.md
â”‚           â”œâ”€â”€ KPI_Catalog_ESG.md
â”‚           â”œâ”€â”€ KPI_Catalog_Governance.md
â”‚           â””â”€â”€ KPI_Catalog_InnovationPeople.md
â”‚
â””â”€â”€ README.md
```
Each Use Case lives in its own folder with a `FactSheet.md` and is grouped by business cluster (Variant A).  
All files follow the defined structure and metadata fields (see Section 4).

---

## 3. Naming Conventions

### 3.1 File Names
- Format: `{PREFIX}-###_Short_Title.md` (e.g., `COM-001_Sales_Performance.md`)
- `{PREFIX}` corresponds to the cluster code: COM, OPS, CST, COR.
- Use Title Case, no spaces or special characters.
- Keep titles concise and descriptive.

### 3.2 Use Case IDs
- Sequential numeric ID within the cluster (`COM-001`, `OPS-002`, …)
- Once assigned, IDs are never reused.

### 3.3 Field Naming (within text)
- **Δ** prefix = absolute variance (e.g., Δ Net Sales Amount)
- **Δ%** prefix = relative variance (e.g., Δ% Gross Margin)
- **%** suffix = percentage metric (e.g., Gross Margin %)
- Amount = currency (0–2 decimals), Qty/Count = integer, % = 1–2 decimals.

---

## 4. Standard Layout for Each Use Case

Every Use Case follows the same Markdown template (`UC-000_Template.md`):

```markdown
---
id: COM-001
title: Sales Performance vs Plan & Last Year
domain: Commercial
cluster: Sales & Revenue
reporting_level: Tactical
analytics_stage: Descriptive
owner: Head of Sales
impact: High
status: Active
last_update: DD.MM.YYYY
---

## Business Goal
Explain the strategic purpose of the analysis and why it matters for decision-making.

## Business Context
Summarize the background, challenges, and intended decisions supported by this analysis.

## Key Questions
- Main analytical question(s)
- Supporting drill-down questions

## Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Net Sales Amount | Revenue excluding returns | € | 0–2 decimals |
| Δ Net Sales Amount | Absolute variance vs Plan | € | 0–2 decimals |
| Δ% Net Sales | Percentage variance vs Plan | % | 1 decimal |

## Typical Actions
- Describe concrete levers or actions derived from the analysis.
- Include both what to do and expected impact.

## Expected Business Impact
Summarize the expected improvement (e.g., “+2–5 pp Δ% Net Sales, +0.5 pp Gross Margin %”).

## Related Processes
List linked operational or planning processes (e.g., Sales Planning, Promotion Management).

## Insights & Learnings
Document key takeaways, interpretation notes, or connections to other use cases.
```

---

## 5. Formatting and Style Guidelines

| Element | Rule |
|----------|------|
| Headings | Use `##` for section titles; no decorative symbols. |
| Lists | Use hyphens or numbers, consistent indentation. |
| Tables | Use Markdown syntax, no HTML. |
| Units | Always specify (€, %, days, pcs). |
| Dates | Format as `DD.MM.YYYY`. |
| Text | Keep concise, avoid marketing tone; focus on analytical meaning. |
| Line breaks | Use one blank line between sections. |
| No emojis | Maintain professional, machine-readable text. |

---

## 6. Review and Approval Workflow

1. **Create a new branch**: `feature/{PREFIX}-###_Short_Title`  
   Example: `feature/COM-003_Price_Realization`
2. **Copy the template** from `usecases/UC-000_Template.md`
3. **Fill in** all required sections following this guide.
4. **Submit a Pull Request** with a short description of the business goal.
5. **Review requirements**:
   - One business reviewer (domain expert)
   - One technical reviewer (data model owner)
6. **Merge** only after both approvals.
7. (removed) No changelog required.

---

## 7. Governance and Versioning

| Element | Guideline |
|----------|------------|
| **Versioning** | Minor = textual update; Major = KPI or logic change. |
| **Status** | `Draft`, `In Review`, `Active`, `Deprecated`. |
| **Changelog** | Not required (govern via PR history). |
| **Archiving** | Deprecated Use Cases remain stored with final version tag. |
| **Cross-References** | Use `[COM-002 Gross Margin %](../01_Commercial/COM-002_Gross_Margin.md)` for linking. |

---

## 8. Supporting Documents

| File | Purpose |
|------|----------|
| [`/docs/Reporting_Strategy.md`](./Reporting_Strategy.md) | Defines reporting levels, analytics stages, and governance layers. |
| [`/docs/Methodology.md`](./Methodology.md) | Explains modeling, visualization, and standardization principles. |
| [`/docs/Changelog.md`](./Changelog.md) | Tracks all changes and approvals. |
| [`/_includes/Glossary.md`](../_includes/Glossary.md) | Contains all abbreviations and analytical term definitions. |
| `/_includes/kpi_catalog/KPI_Catalog_README.md` | Einstieg in alle KPI-Kataloge (Dimensionen, Schema, Links). |
| [`/_includes/ActionCodes.md`](../_includes/ActionCodes.md) | Lists standardized action codes (P2, D1, etc.) and meanings. |

---

## 9. Quality Criteria (Definition of Done)

A Use Case is considered **complete** when:

- All mandatory fields are filled (Business Goal, Context, KPIs, Actions, Impact).  
- Naming follows the conventions (`Δ`, `Δ%`, `%`).  
- Cross-references and glossary links are valid.  
- Reviewed and approved by both business and data reviewers.  


---

_Last updated: 03.11.2025_



