# Company Layer (WHY)

Purpose:
Anchor the ActionReady Analytics Framework in business reality: strategy, domains, strategic KPIs, and the key questions analytics must answer.

Scope:
- Strategy and value creation logic
- Domain definitions and operating model context
- Strategic KPIs and their relevance
- Key questions that drive use cases
- Reporting/design principles tailored to the company
- Excludes technical semantics, data contracts, or page templates

Structure:
```
company/
  business_strategy.md          strategic direction, value chain, priorities
  domains.md                    domain catalog (Finance, Sales, SCM, ESG, etc.)
  strategic_kpis.md             top-level KPIs mapped to strategy
  key_questions.md              high-value questions that drive use cases
  reporting_design_principles.md company-specific design and reporting standards
```

Usage:
- Customers: validate goals, KPIs, and domain ownership; set reporting expectations early.
- Delivery teams: ground models, measures, and use cases in real business needs; derive prioritization and governance.
- Framework evolution: extend per customer without changing the core standards.

Relations:
- WHY: defines goals, questions, KPIs, decision paths.
- HOW: operating model (semantics, measure system, UX, ops) implements this strategy.
- WITH WHAT: KPI catalog, Action Codes, glossaries, templates derive from domains and strategic KPIs.
- PATTERNS: Business Factsheets and blueprints rely on the key questions and domains defined here.
