# Framework (WITH WHAT)

## Purpose
The **Framework** folder contains all reusable building blocks of the *ActionReady Analytics Framework*.  
These components define **how analytics is designed, standardized, and delivered**, independent of any specific customer or technology platform.

If the Company Layer explains the WHY, and the Operating Model explains the HOW,  
**the Framework folder provides the WITH WHAT**.

It is the productized toolkit that enables scalable, repeatable, high‑quality analytics delivery.

---

## Scope

Included:
- Implementation guides for different platforms (Fabric, Databricks, Snowflake, Looker…)
- Templates for pages, measures, data contracts
- Action Codes (portfolio, usage rules, trigger logic)
- KPI Catalog & Domain Measure Dictionary
- Business & technical glossaries

Not included:
- Customer-specific implementations  
- Data contracts, semantic models, or use cases for specific clients  
- Operational processes (see `docs/operating_model/`)

---

## Structure

```
framework/
  implementation_guides/   → Platform-specific translation of the Operating Model
  templates/               → Page, measure, and data contract templates
  action_codes/            → Action Codes portfolio (Single Source of Truth)
  kpi_catalog/             → KPI structures & domain measure dictionaries
  glossary/                → Business & technical terminology
```

### implementation_guides/
Provides tool-specific mappings of the Operating Model principles:
- Microsoft Fabric / Power BI  
- Databricks  
- Snowflake + Tableau  
- Looker  

These guides translate the conceptual operating model into platform reality.

### templates/
Reusable building blocks:
- Page templates (3-30-300 aligned)  
- Measure templates (naming, documentation structure, foldering)  
- Data contract templates (fact/dim blueprints)  

These ensure consistent report design, measure structure, and data modeling across all projects.

### action_codes/
The *ActionReady engine*.
- Full Action Code portfolio (L1–L3)  
- Trigger rules  
- Impact definitions  
- Usage guidelines  
- Legacy versions (optional)

This drives business actionability and impact measurement.

### kpi_catalog/
Contains:
- Domain KPI overview  
- Domain measure dictionaries  
- Links to semantic model implementations  

Ensures KPI governance, consistency, and Copilot-readiness across domains.

### glossary/
Defines:
- Business terminology  
- Technical terminology  
- Model terminology (facts, dims, grains, hierarchical definitions)

Critical for metadata quality, governance, and AI/Copilot scenarios.

---

## Usage

### For Customers
- Use this folder to understand the standard components applied in every project.  
- Reuse page templates and measure templates to accelerate report development.  
- Validate KPI governance and Action Code structures.

### For Delivery Teams
- Always start from templates — never rebuild patterns manually.  
- Keep all changes platform-independent unless explicitly necessary.  
- Treat Action Codes and KPI Catalog as **immutable, governed assets**.

### For Framework Evolution
- Extend templates and catalogs carefully and version them cleanly.  
- Add new implementation guides only when tested in real projects.

---

## Relations

- **WHY →** Company Layer sets the business context for all templates and catalogs.  
- **HOW →** Operating Model defines the rules and principles that all templates must follow.  
- **WITH WHAT →** This folder *is* the toolkit of reusable assets used to implement the model.  
- **TEMPLATES →** Framework templates flow directly into use case pages, semantic models, and data contracts.

---

## Next Step
Start with:

1. `templates/page_templates/`  
2. `action_codes/ActionCodes_Portfolio.md`  
3. `kpi_catalog/domain_kpi_catalog.md`

This will give you the fastest understanding of how to build compliant, high-quality analytics products.

---

**Location to place this file:**  
`framework/README.md`
