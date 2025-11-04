# KPI Catalog Schema

Purpose: Single source of truth for KPI entry structure and ID conventions across all domain catalogs.

Fields (YAML block per KPI)
```yaml
kpi_id: "namespace.identifier"           # ASCII, namespaced, unique across repo
kpi_key: "Readable KPI Name"             # Human-readable title
kpi_type: "strategic|diagnostic|supporting"
domain_tag: ["Commercial"]               # One or more domains (Commercial, Operational Efficiency, Customer & Market, Corporate & Strategy, ESG, Governance)
impact_dimension: "Growth|Profitability|Liquidity|Efficiency|Customer|ESG|Governance"
use_case_ref: ["COM-001"]               # Optional Use Case IDs this KPI supports
calc_type: "amount|rate|ratio|count"    # Calculation type
technical:
  dax_name: "Measure Name"               # DAX or semantic name
  dax_expression: "...optional..."       # Expression if available
  formatString: "..."                    # Formatting string
  displayFolder: "...optional..."        # Optional folder hint
  description: "Short purpose/definition"
aliases: ["Optional alternative names"] # Human-readable variants
verified: false                           # true when validated in a model
```

ID Conventions
- ASCII only; lowercase; words separated by dots: `area.topic.metric.variant`
- Examples:
  - `sales.net_sales.delta_pct.ly`, `margin.gm.pct`, `cost.cogs.amount`
  - `ops.working_capital.ccc.days`, `crm.retention.pct`, `esg.co2.total.tco2e`
- Stable across catalogs; no reuse for different semantics.

Validation (optional CI)
- Enforce unique `kpi_id` across all catalogs.
- Restrict `kpi_type` to {strategic, diagnostic, supporting}.
- Check `calc_type` in {amount, rate, ratio, count}.
- Lint `kpi_id` by regex: `^[a-z0-9]+(\.[a-z0-9_]+)*$`.

Authoring Rules
- Define each KPI once in the most relevant domain catalog.
- Reference the schema in each catalog’s header; do not embed schema copies.
- Prefer adding aliases for legacy names with symbols (e.g., Δ) to support readability.

Last updated: 03.11.2025

