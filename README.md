# Analytics Use Case Library

## Purpose
The **Analytics Use Case Library** is part of the company-wide **Reporting Framework**.  
It translates strategic, tactical, and operational information needs into standardized, reusable analytical use cases organized by functional clusters.

Each use case links **business goals** with **data structures**, **KPIs**, and **actions**, ensuring clarity, comparability, and governance across all analytics initiatives.

> **Goal:** Enable consistent, goal-driven, and AI-ready reporting instead of tool-driven dashboards.

---

## Objectives
- Establish a unified structure for documenting business analytics scenarios.  
- Align reporting across all functional clusters to the **Reporting Strategy**.  
- Enable a shared language between business, data, and analytics teams.  
- Create a foundation for standardized KPIs, actions, and insights.  
- Support Copilot readiness through structured metadata and traceability.  
- Ensure governance and version control through changelog discipline.

---

## Reporting Framework Integration
The Library operationalizes the **Reporting Framework** defined in [`/docs/Reporting_Strategy.md`](./docs/Reporting_Strategy.md).

| Element | Role | Example |
|----------|------|----------|
| **Reporting Strategy** | Defines reporting levels (Strategic, Tactical, Operational) and analytics maturity (Descriptive → Prescriptive) | `/docs/Reporting_Strategy.md` |
| **Cluster (Domain)** | Groups related business topics (Commercial, Operational Efficiency, Customer & Market, Corporate & Strategy) | `/usecases/01_Commercial/` |
| **Use Case** | Describes one analytical question with KPIs and actions | `/usecases/01_Commercial/COM-001_Sales_Performance.md` |
| **KPI Catalog & Action Codes** | Provide shared semantics and operational levers | `/_includes/KPI_Catalog.md` / `/_includes/ActionCodes.md` |

Each Use Case is classified by:
- `reporting_level:` **Strategic / Tactical / Operational**  
- `analytics_stage:` **Descriptive / Diagnostic / Predictive / Prescriptive**  
- `domain:` **Cluster affiliation (e.g., Commercial, Operational Efficiency)**  

This structure ensures traceability from **business goals → KPIs → data → actions**.

---

## Repository Structure
```
/analytics-usecase-library/
│
├── /docs/
│   ├── Reporting_Strategy.md     ← defines reporting levels & architecture
│   ├── Methodology.md            ← describes modeling & design principles
│   ├── Instructions.md           ← authoring and governance rules
│   ├── Changelog.md              ← version control and audit log
│
├── /usecases/
│   ├── /01_Commercial/
│   │     ├── COM-001_Sales_Performance.md
│   │     ├── COM-002_Gross_Margin.md
│   │     └── ...
│   ├── /02_Operational_Efficiency/
│   ├── /03_Customer_and_Market/
│   ├── /04_Corporate_and_Strategy/
│   └── UC-000_Template.md
│
├── /_includes/
│     ├── Glossary.md
│     ├── ActionCodes.md
│     ├── Strategic_KPIs.md
│     └── /kpi_catalog/
│           ├── KPI_Catalog_README.md
│           ├── KPI_Catalog_Growth.md
│           ├── KPI_Catalog_Profitability.md
│           ├── KPI_Catalog_Liquidity.md
│           ├── KPI_Catalog_Efficiency.md
│           ├── KPI_Catalog_CustomerValue.md
│           ├── KPI_Catalog_ESG.md
│           ├── KPI_Catalog_Governance.md
│           └── KPI_Catalog_InnovationPeople.md
│
└── README.md
```

---

## Use Case Layout

Each file follows a uniform Markdown layout (see `UC-000_Template.md`):

```yaml
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
last_update: 12.10.2025
---
```

### Standard Sections
1. **Business Goal** – Purpose of the analysis and its link to business outcomes.  
2. **Business Context** – Background, relevance, and decisions supported.  
3. **Key Questions** – Core analytical questions (What, Where, Why, What Next).  
4. **Key KPIs** – Reference to standardized KPIs in `/_includes/KPI_Catalog.md`.  
5. **Required Attributes** – Business-level fields needed for mapping.  
6. **Segmentation & Hierarchies** – Time, Org, Product, Customer structures.  
7. **Scope & Assumptions** – Analytical boundaries and definitions.  
8. **Typical Actions** – Derived operational levers (linked via Action Codes).  
9. **Expected Business Impact** – Quantified value of improvements.  
10. **Related Processes / Learnings** – Context and cross-references.  
11. **Review Information** – Reviewers, version, and notes.

---

## Cluster Logic

| Cluster | Purpose | Example Use Cases |
|----------|----------|------------------|
| **Commercial** | Revenue, pricing, margin, sales efficiency | Sales Performance, Gross Margin %, Price Realization |
| **Operational Efficiency** | Cost, productivity, supply chain | Inventory Turnover, COGS Control, Logistics Cost Ratio |
| **Customer & Market** | Customer value and demand | Retention Rate, Customer Lifetime Value, Market Share |
| **Corporate & Strategy** | Financials, ESG, governance | Working Capital, Headcount Efficiency, Sustainability KPIs |

Each cluster aggregates Use Cases that share a **business objective** and **data domain**, aligned with the Reporting Framework.

---

## Contribution Workflow

1. **Create a new branch**:  
   `feature/{CLUSTER}-###_Short_Title`  
   Example: `feature/COM-003_Price_Realization`
2. **Duplicate the template**:  
   `usecases/UC-000_Template.md`
3. **Fill all required sections** following `docs/Instructions.md`.
4. **Add metadata** (`reporting_level`, `analytics_stage`, `domain`).
5. **Submit Pull Request** → reviewed by:
   - One **Business Reviewer** (domain expert)  
   - One **Technical Reviewer** (data model owner)
6. **Update** `docs/Changelog.md` with ID, version, author, date, and summary.

---

## Governance & Quality Criteria

| Element | Rule |
|----------|------|
| **Review Workflow** | Mandatory business + technical approval |
| **Versioning** | Major = new KPIs/actions; Minor = text update |
| **Status** | Draft → In Review → Active → Deprecated |
| **Changelog Discipline** | Required for every change |
| **Naming** | `Δ` = absolute variance, `Δ%` = relative variance, `%` = percentage |
| **Data Quality** | Referential Integrity ≥ 99.9 % across Date/Org/Product |
| **Copilot Readiness** | All sections and lineage metadata filled |
| **No Emojis** | Maintain professional and machine-readable format |

---

## Supporting Documents

| File | Purpose |
|------|----------|
| [`/docs/Reporting_Strategy.md`](./docs/Reporting_Strategy.md) | Defines reporting levels, analytics stages, and governance layers. |
| [`/docs/Methodology.md`](./docs/Methodology.md) | Explains modeling, 3-30-300 design, and visualization standards. |
| [`/docs/Instructions.md`](./docs/Instructions.md) | Details authoring and maintenance process. |
| [`/_includes/KPI_Catalog.md`](./_includes/KPI_Catalog.md) | Canonical KPI definitions with formulas and QA rules. |
| [`/_includes/ActionCodes.md`](./_includes/ActionCodes.md) | Standardized operational actions (P2, D1, etc.). |
| [`/_includes/Glossary.md`](./_includes/Glossary.md) | Glossary of business and analytical terms. |

---

## License and Use
Internal documentation for enterprise analytics governance.  
Not intended for external publication without prior approval.

_Last updated: 12.10.2025_
3. Update existing Use Cases with the new metadata fields.  
4. Validate consistency across clusters via the KPI Catalog.
