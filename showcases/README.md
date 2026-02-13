# Showcases

## Purpose

The **Showcases** folder contains fully realized, end-to-end examples demonstrating how the **ActionReady Analytics Framework** works in practice.  
These examples allow customers and delivery teams to see the entire methodology — strategy, semantics, UX, use cases, and operations — applied to a real company scenario.

The primary goal is to turn abstract framework concepts into tangible, high-quality reference implementations.

## Scope

Included:

- Complete reference implementations (e.g., Aurora Group)
- Example data contracts and sample datasets
- Semantic models built according to ActionReady standards
- Fully structured use cases (business + technical)
- Report designs, screenshots, and navigation flows

Not included:

- Customer-specific implementations (kept in separate project repositories)
- Internal drafts, prototypes, or experiments
- Tool-specific implementation guides (see `products/fabric_powerbi/docs/`)

## Structure

```yaml
showcases/
  aurora_group/        → Full end-to-end reference implementation
    company/           → Business profile, value chain, org model
    data/              → Sample data contracts and synthetic data
    semantic_model/    → ActionReady semantic model applied to Aurora
    usecases/          → Core/Extended Aurora use cases (link to core/usecases/core)
    reporting/         → Screenshots, navigation map, page flows
```

### aurora_group/

This is the flagship showcase.  
It demonstrates the entire ActionReady stack:

- Company-layer alignment  
- Operating model principles  
- ActionReady semantic layer  
- Action Codes in action  
- KPIs, measures, and reporting design  
- Page templates (3-30-300) applied in real context  

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
