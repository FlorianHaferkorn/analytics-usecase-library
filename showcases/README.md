# Showcases

## Purpose

The **Showcases** folder contains fully realized, end-to-end examples demonstrating how the **ActionReady Analytics Framework** works in practice.  
These examples allow customers and delivery teams to see the entire methodology — strategy, semantics, UX, use cases, and operations — applied to a real company scenario.

The primary goal is to turn abstract framework concepts into tangible, high-quality reference implementations.

## Scope

Included:

- Company profile, operating model, and synthetic gold data (Aurora Group)
- Archived PBIP example for structural reference (sample_pbip_report)

Not included:

- Semantic models and reports — these are in `products/fabric/powerbi/dist/`
- Customer-specific implementations (kept in separate project repositories)
- Internal drafts, prototypes, or experiments
- Tool-specific implementation guides (see `products/fabric/powerbi/docs/`)

## Structure

```yaml
showcases/
  aurora_group/        → Company profile, operating model, and synthetic gold data
    company/           → Business profile, value chain, org model
    data/              → Synthetic gold layer (fact_*, dim_*) + generation scripts
    usecases/          → Aurora demo scope (pointers to core/usecases/core)
  sample_pbip_report/  → ARCHIVED — structural reference only; do not use for new work
```

> **Semantic models and reports are NOT stored here.**
> Generated artefacts live in `products/fabric/powerbi/dist/`.

### aurora_group/

This is the active showcase. It provides company context (Aurora Group is the synthetic demo company used across all framework examples).  
It demonstrates:

- Company-layer alignment (strategy to KPIs)
- Operating model principles
- Synthetic gold data aligned to data contracts (`core/data_contracts/`)
- Demo use case scope aligned to `core/usecases/core/`

## Usage

### For Customers

- Understand what a modern analytics framework *looks like when done right*.  
- Use Aurora as a benchmark for their own future-state vision.  
- Explore complete examples of KPIs, data products, and report design.  
- Validate that the methodology is practical, realistic, and scalable.

### For Delivery Teams

- Use Aurora as the **gold standard** for new client implementations.  
- Copy patterns for:
  - Data contracts  
  - Semantic models  
  - Measure dictionaries  
  - Use case structures  
  - UX/page layouts  
- Ensure consistent, high-quality delivery across all engagements.

### For Internal Framework Evolution

- Use Aurora to experiment with improvements before rolling them into the framework.  
- Maintain Aurora as the “single source of truth” for best practices in action.

## Relations

- **WHY (Company Layer)**  
  Showcases demonstrate how strategy, KPIs, and domains translate into real use cases.

- **HOW (Operating Model)**  
  All operating-model components (semantics, UX, governance, operations, AI readiness) are *visible in action*.

- **WITH WHAT (Framework Standards)**  
  Templates, Action Codes, KPI Catalog — all applied consistently.

- **TEMPLATES (Pattern Library)**  
  Showcases provide real-world examples built entirely from these templates.

## Next Step

Start with the flagship example:

`showcases/aurora_group/README.md`

It provides a complete, guided walkthrough of how the ActionReady Analytics Framework is applied end-to-end.
