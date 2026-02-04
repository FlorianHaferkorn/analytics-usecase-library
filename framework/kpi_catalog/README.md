# KPI Catalog

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
- KPI -> Domain -> Use Case -> Action Code mapping (see framework/usecases/UseCase_ActionCode_Map.yaml and framework/usecases/UseCase_ActionCode_Rationale.yaml)
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

## Relations

- **WHY ?** Strategic KPIs from the Company Layer define what belongs here.  
- **HOW ?** Semantic Layer & Measure System govern design, naming, and logic.  
- **WITH WHAT ->** Action Codes and Templates use this catalog as input.
- **TEMPLATES ->** Factsheet templates reference KPIs directly.

---

**Location:**  
`framework/kpi_catalog/README.md`

