# Glossary

## Purpose

This glossary defines the shared business and technical vocabulary used across the ActionReady Analytics Platform.

It exists to:

- avoid misunderstandings between business and analytics teams,
- provide stable semantic grounding for AI/Copilot,
- ensure consistent interpretation across domains and products.

## Business terms

### Impact Dimension

A strategic lens used to classify KPIs and use cases by the business outcome they influence (for example Growth, Profitability, Liquidity, Efficiency).

### Use Case

A standardized, decision-oriented business question answered with analytics. A use case must result in a decision or action, not only insight.

### KPI (Key Performance Indicator)

A quantitative measure used to track performance against a defined business objective. KPIs are governed, documented, and reused across reports and use cases.

### Strategic KPI

A top-level KPI directly linked to company strategy and executive decisions.

### Tactical KPI

A KPI used to steer departments or functions toward strategic targets.

### Operational KPI

A KPI used to control and optimize day-to-day operations.

### Reporting Level

Classification of a use case by decision horizon:

- Strategic
- Tactical
- Operational

### Analytics Stage

Classification of analytical maturity:

- Descriptive
- Diagnostic
- Predictive
- Prescriptive

### Prescriptive Analytics

An analytics stage focused on recommending concrete actions, not only explaining results.

### Business Owner

Accountable for the business meaning and interpretation of a KPI or use case.

### Data Owner

Responsible for data quality, lineage, and availability of underlying data.

### Report Owner

Responsible for report usability, clarity, and decision support quality.

### Definition of Done (DoD)

A set of criteria confirming that a KPI or use case is complete, validated, and ready for implementation/use.

## Technical terms

### Semantic Model

A governed analytical layer defining relationships, measures, hierarchies, and metadata. It is the single analytical interface for reporting and decision-making.

### Fact Table

A table storing measurable data at a defined grain.

### Dimension Table

A table storing descriptive attributes used to analyze facts.

### Grain

The lowest level of detail at which data is stored and measures are evaluated.

### Star Schema

A data modeling pattern where fact tables are surrounded by conformed dimension tables.

### Conformed Dimension

A shared dimension reused consistently across multiple fact tables and domains.

### Measure

A reusable calculation returning one aggregated value. Measures implement business logic; calculated columns are minimized.

### KPI ID

A stable, unique KPI identifier using dot notation (for example `sales.net_sales.amount`), reused across catalog, use cases, semantic models, action codes, and automation.

### Data Contract

A governed specification for facts/dimensions, grain, keys, units, lineage, and quality expectations. It defines what data must look like, not how it is processed.

### Referential Integrity (RI)

The degree to which fact keys correctly match corresponding dimension keys.

### QA Rule

A validation rule ensuring data or measure correctness (for example allowed ranges or logical consistency).

### Row-Level Security (RLS)

A security mechanism restricting data access at row level based on user context.

### Object-Level Security (OLS)

A security mechanism controlling visibility of tables, columns, or measures.

## Action and control terms

### Action Code

A standardized, coded description of a prescriptive business action linked to KPI behavior.

### Trigger Level (L1-L3)

Classification of action activation:

- L1: early warning
- L2: intervention required
- L3: execution required

### Action Aggregate

A fact-like structure summarizing KPI deviations, triggers, or root causes used to activate action codes.

## Usage rules

- Definitions must be domain-independent.
- One term has one meaning.
- KPI-specific semantics belong in `core/kpi_catalog/`.
- Operating model rules belong in `core/strategy_operating_model/`.
- New terms are added only when reused across domains/products.

*(Archived from `core/glossary/glossary.md`. Not SSOT.)*
