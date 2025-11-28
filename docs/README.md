# ActionReady Analytics Framework – Documentation

## Purpose
This documentation provides the strategic and conceptual foundation of the **ActionReady Analytics Framework**.  
It explains *why* the framework exists, *how* it is structured, and *how* customers and delivery teams should navigate the repository.

This is the primary entry point for all readers.

---

## How to Use This Documentation
If you are new to the framework, read the sections in this order:

1. **Company Layer (WHY)**  
   Understand business strategy, domains, KPIs and key questions.  
   → `docs/company/`

2. **Analytics Operating Model (HOW)**  
   Learn how data, semantics, UX, KPIs and AI-readiness form a unified system.  
   → `docs/operating_model/`

3. **Framework Standards & Templates (WITH WHAT)**  
   See the building blocks: Action Codes, KPI Catalog, Measures, Page Templates.  
   → `framework/`

4. **Use Case Library (WHAT)**  
   Explore core, extended and industry use cases.  
   → `usecases/`

5. **Technical Backbone**  
   Data Contracts + Semantic Models  
   → `data_contracts/`  
   → `semantic_models/`

6. **Aurora Group Showcase**  
   Full example implementation (end-to-end).  
   → `showcases/aurora_group/`

---

## The 4-Layer Model
The ActionReady Analytics Framework is organized into four conceptual layers:

```
WHY        → Company Strategy & KPI Alignment
HOW        → Analytics Operating Model (UX, Semantics, Governance)
WITH WHAT  → Standards, Templates, Action Codes, KPI Catalog
TEMPLATES  → Use Case Blueprints, Page Templates, Data Contracts
```

---

## Repository Navigation (ASCII Map)

```
docs/
  company/             → WHY: Strategy, KPIs, Domains, Questions
  operating_model/     → HOW: Semantics, UX, Ops, AI-Readiness

framework/
  implementation_guides/ → Platform-specific HOW (Power BI, Databricks...)
  templates/             → TEMPLATES: Pages, Measures, Contracts
  action_codes/          → Action Codes Portfolio
  kpi_catalog/           → KPI Structures & Measure Dictionaries
  glossary/              → Business & Technical Terminology

usecases/
  core/                → Core Use Cases every company needs
  extended/            → Extended Use Cases
  industry/            → Industry-specific variants

semantic_models/
  domains/             → Domain measure dictionaries
  core_action_ready/   → ActionReady reference semantic model

data_contracts/
  domains/             → Domain-level data contracts
  sources/             → Sample/synthetic sources (if applicable)

showcases/
  aurora_group/        → Full end-to-end demo implementation

_internal/
  tools/               → Linting, generation, QA automation (internal only)
  archive/             → Legacy, drafts, experimental files
```

---

## How Customers Should Use This Repository

- **To establish a unified reporting & analytics strategy**  
  → Start with the Company Layer.

- **To build a scalable analytics foundation**  
  → Follow the Operating Model (Semantics, UX, Ops).

- **To build high-quality reports quickly**  
  → Use the Templates (Pages, Measures, Data Contracts).

- **To deploy Action Codes and measure impact**  
  → Leverage the Action Codes Portfolio.

- **To validate implementation quality**  
  → Use Semantic Models, KPI Catalog and Data Contracts.

- **To see how everything works together**  
  → Review the Aurora Group Showcase.

---

## How Delivery Teams Should Use This Repository

- Mirror the folder structure when onboarding new clients.
- Reuse templates to ensure consistent quality.
- Extend semantic models only through measure dictionaries.
- Keep customer-specific implementations inside their own project repos.
- Reference Aurora Showcase for guidance and best practices.

---

## Next Steps
To get started, review:

1. `docs/company/`  
2. `docs/operating_model/`  
3. `framework/templates/`  
4. `showcases/aurora_group/`

This gives you a complete understanding of the ActionReady Analytics Framework.

---

**Location to place this file:**  
`docs/README.md`
