# Framework (WITH WHAT)

Purpose:
Provide the reusable toolkit of the ActionReady Analytics Framework: templates, catalogs, Action Codes, glossaries, and platform guides.

Scope:
- Implementation guides (Fabric/Power BI, Databricks, Snowflake/Tableau, Looker)
- Templates for pages, measures, data contracts
- Action Codes portfolio and usage rules
- KPI catalog and domain measure dictionary
- Business and technical glossaries
- Excludes customer-specific builds and operational processes (see `docs/operating_model/`)

Structure:
```
framework/
  implementation_guides/   platform-specific HOW
  templates/               page, measure, data contract templates
  action_codes/            Action Codes portfolio (single source of truth)
  kpi_catalog/             KPI catalog + measure dictionary
  glossary/                business + technical terminology
```

Usage:
- Customers: understand the standard components applied in every project; reuse templates to accelerate build.
- Delivery teams: always start from templates; treat Action Codes and KPI catalog as governed assets.
- Framework evolution: extend carefully with clear versioning after real-world validation.

Relations:
- WHY: informed by strategy/domains in `docs/company/`.
- HOW: follows rules in `docs/operating_model/`.
- WHAT: feeds `usecases/`, `semantic_models/`, and `data_contracts/` with governed assets.
