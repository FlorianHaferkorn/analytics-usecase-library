# KPI Catalog

> **Canonical definitions:** [KPI_Catalog.md](KPI_Catalog.md).  
> This README is for navigation and overview only; it must not redefine KPI semantics.

## Purpose

The **KPI Catalog** provides a governed, cross-domain inventory of all KPIs and measures used in the  
**ActionReady Analytics Framework**.  
It ensures consistency, clarity, and alignment between business, analytics, AI/Copilot, and reporting.

This catalog forms the foundation for semantic modeling, actionability, and long-term governance.

---

## Scope

Included:

- Strategic and operational KPIs per domain
- Measure dictionary references
- Calculation logic, naming rules, formats
- KPI → Domain → Use Case → Action Code mapping (action code subscriptions per use case in `UseCase_Bracket.yaml` `orchestration.action_code_ids`)
- Authoritative definitions required for AI/Copilot

Not included:

- Tool-specific implementation (covered in semantic models)
- Report/page design (see templates)
- Customer-specific KPIs (kept outside the framework)

---

## Usage

### For Customers

- Validate KPI consistency across business units  
- Ensure alignment between strategy and analytics  
- Use as onboarding reference for new teams or processes  
- Provide a single source of truth for AI/Copilot semantic grounding

### For Delivery Teams

- Implement KPIs consistently across projects  
- Reuse calculation logic and measure patterns  
- Synchronize KPI definitions with Action Codes and page templates  
- Ensure every measure has:  
  - Purpose  
  - Definition  
  - Grain  
  - Unit/Format  
  - Lineage  
  - QA check  

### For Framework Evolution

- Add new KPIs only if they provide cross-customer value  
- Version major changes through semantic model governance  
- Keep dictionaries clean, non-duplicated, and fully linked

---

## Supporting KPIs and data requirements

- **Supporting KPIs** (e.g. `sales.price.list.amount`, `sales.price.net.amount`) are defined in the catalog with `kpi_role: supporting`. They are referenced in `depends_on_measures` by strategic/diagnostic KPIs (e.g. `sales.price.realization_pct`) and must be listed in the use case’s `orchestration.influencing_kpi_ids` so the measure generator emits them.
- **Data requirement:** Each KPI’s `technical.lineage` lists the fact/dimension columns required for its measure (e.g. `fact_sales.List Price Amount`). The **semantic model** must provide these tables and columns; they are defined by the **domain data contracts** (`core/data_contracts/domains/`). The pipeline that builds the semantic model from the contract (e.g. Fabric table_ops) ensures the model satisfies this data need. When adding or changing KPIs, ensure the corresponding domain contract includes the required columns.

---

## Relations

- **WHY ?** Strategic KPIs from the Company Layer define what belongs here.  
- **HOW ?** Semantic Layer & Measure System govern design, naming, and logic.  
- **WITH WHAT ->** Action Codes and Templates use this catalog as input.
- **TEMPLATES ->** Factsheet templates reference KPIs directly.

---

**Location:**  
`core/kpi_catalog/README.md`

