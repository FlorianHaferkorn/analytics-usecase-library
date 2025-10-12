# Instructions for Authoring and Maintaining Use Cases

## 1. Purpose
This document defines how business analytics use cases are to be created, formatted, named, and maintained.  
It ensures consistency, traceability, and quality across all documentation within the **Analytics Use Case Library**.

---

## 2. File and Folder Structure
```
/analytics-usecase-library/
│
├── /docs/
│   ├── Instructions.md
│   ├── Methodology.md
│   ├── Changelog.md
│
├── /usecases/
│   ├── UC-001_Sales_Performance.md
│   ├── UC-002_Gross_Margin.md
│   ├── ...
│
├── /_includes/
│   ├── Glossary.md
│   ├── KPI_Catalog.md
│   ├── ActionCodes.md
│
└── README.md
```
Each Use Case is documented as an individual Markdown file in `/usecases/` and follows a defined layout (see Section 4).

---

## 3. Naming Conventions

### 3.1 Use Case Files
- Format: `UC-###_Short_Title.md`
- Example: `UC-001_Sales_Performance.md`
- Use Title Case, no spaces or special characters.
- Keep titles concise and descriptive.

### 3.2 Use Case IDs
- Sequential numeric ID (`UC-001`, `UC-002`, …)
- Once assigned, IDs are never reused.

### 3.3 Field Naming (within text)
- **Δ** prefix = absolute variance (e.g., Δ Net Sales Amount)
- **Δ%** prefix = relative variance (e.g., Δ% Gross Margin)
- **%** suffix = percentage metric (e.g., Gross Margin %)
- Amount = currency (0–2 decimals), Qty/Count = integer, % = 1–2 decimals.

---

## 4. Standard Layout for Each Use Case

Every Use Case follows the same Markdown template:

```markdown
---
id: UC-001
title: Sales Performance vs Plan & Last Year
domain: Sales & Revenue
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
| No emojis | Do not use emojis in any document. |

---

## 6. Review and Approval Workflow

1. **Create a new branch**: `feature/UC-###_Short_Title`
2. **Copy the template** from `usecases/UC-000_Template.md`
3. **Fill in** all required sections following this guide.
4. **Submit a Pull Request** with a short description of the business goal.
5. **Review requirements**:
   - One business reviewer (domain expert)
   - One technical reviewer (BI or data model owner)
6. **Merge** only after both approvals.
7. **Update** `/docs/Changelog.md` with:
   - ID, Title, Version, Author, Date, Change Summary

---

## 7. Governance and Versioning

| Element | Guideline |
|----------|------------|
| **Versioning** | Increment minor version for textual updates; major version for new KPIs or actions. |
| **Status** | `Draft`, `In Review`, `Active`, `Deprecated`. |
| **Changelog** | Required for every addition or modification. |
| **Archiving** | Deprecated Use Cases remain stored with final version tag. |
| **Cross-References** | Use `[UC-002 Gross Margin %](../usecases/UC-002_Gross_Margin.md)` for linking. |

---

## 8. Supporting Documents

| File | Purpose |
|------|----------|
| `/docs/Methodology.md` | Explains reasoning behind 3-30-300, semantic modeling, and standardization. |
| `/docs/Changelog.md` | Tracks all changes and approvals. |
| `/_includes/Glossary.md` | Contains all abbreviations, KPIs, and term definitions. |
| `/_includes/KPI_Catalog.md` | Defines metrics with formulas, units, and formats. |
| `/_includes/ActionCodes.md` | Lists standard action codes (P2, D1, etc.) with meaning. |

---

## 9. Quality Criteria (Definition of Done)
A Use Case is considered **complete** when:

- All mandatory fields are filled (Business Goal, Context, KPIs, Actions, Impact).  
- Naming follows the defined conventions (Δ, Δ%, %).  
- Cross-references and links are valid.  
- Document reviewed and approved by both business and data reviewer.  
- Changelog entry created and merged.  

---

_Last updated: 12.10.2025_
