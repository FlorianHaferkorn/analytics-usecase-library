# KPI Catalog Schema

Purpose: Single source of truth for KPI entry structure and ID conventions across all domain catalogs.

Fields (YAML block per KPI)
```yaml
- kpi_id: "namespace.identifier"            # Required; stable ASCII ID (dot-separated)
  kpi_key: "Readable KPI Name"              # Required; human-readable name (with symbols OK)
  kpi_type: "strategic|diagnostic|supporting"  # Required; one of the enum values
  strategic_ref: "Optional strategic parent name"  # Optional; human ref only
  impact_dimension: "Growth|Profitability|Liquidity|Efficiency|Customer|ESG|Governance"  # Required
  domain_tag: ["Commercial"]                # Required; one or more domain tags
  use_case_ref: ["COM-001"]                # Optional; related Use Case IDs
  depends_on: ["Other KPI Key(s)"]         # Optional; human-readable dependencies
  calc_type: "amount|rate|ratio|count"     # Required; calculation type
  refresh: daily|weekly|monthly|quarterly  # Optional; data refresh cadence
  status: Active|Draft|Deprecated          # Optional; lifecycle

  business:                                 # Required; business semantics
    purpose: "What decision this KPI informs"  # Required
    definition: "Precise business definition"  # Required
    grain_scope: "Source grain + aggregation level"  # Required
    unit_format: "Display units (e.g., EUR, %, pcs)" # Required
    interpretation: "How to read the KPI"          # Required

  technical:                                # Required; technical mapping
    dax_name: "Measure Name"                # Required if implemented
    dax_expression: "...optional..."        # Optional; expression if available
    formatString: "..."                     # Required for numeric KPIs
    displayFolder: "...optional..."         # Optional; model folder hint
    description: "Short purpose/definition" # Required summary
    lineage: ["table.column or measure"]    # Optional; lineage hints
    source_grain: "table-level grain"       # Optional
    source_column_ref: ["table.column"]     # Optional
    source_system: "ERP|CRM|..."            # Optional
    verified: false                          # Required; mark true when validated

  governance:                               # Required; ownership & QA
    business_owner: "Role/Team"             # Required
    data_owner: "Team"                      # Required
    steward: "Role"                         # Optional
    review_cycle: "monthly|quarterly|..."   # Optional
    validation_process: "automated|manual|dual control"  # Optional
    qa_rules:
      - "Rule 1"                            # Optional list of checks
    version: "vX.Y"                         # Optional version tag
    last_review: "DD.MM.YYYY"               # Optional review date

  metadata_quality:                         # Optional; metadata KPIs
    completeness_score: 0.00                # Optional 0..1
    lineage_verified: false                 # Optional
    copilot_ready: false                    # Optional

  aliases: ["Optional alternative names"]  # Optional; human variants
```

Authoring checklist
- Provide one YAML list item per KPI starting with `- kpi_id:`.
- Use ASCII-only for `kpi_id`; use readable symbols in `kpi_key` if helpful (e.g., Δ, ±, €).
- Fill the business and technical blocks; leave technical expression blank only if unknown.
- Prefer one canonical definition per KPI across catalogs; avoid duplicates.

---

## Field Semantics (what to write)

- kpi_id
  - What: Stable, ASCII, dot-separated identifier that conveys domain.topic.metric.variant.
  - Do: `margin.gm.amount`, `sales.net_sales.delta_pct.ly`, `fin.liquidity.cash_conversion_cycle.days`.
  - Don’t: include spaces, uppercase, or symbols; don’t reuse for different semantics.

- kpi_key
  - What: Human-readable KPI name as seen by users (symbols allowed).
  - Do: "Gross Margin %", "Δ Net Sales Amount", "Free Cash Flow".
  - Don’t: encode technical table/column names here.

- kpi_type
  - strategic: directly reflects strategic objectives or board metrics.
  - diagnostic: explains variance or drivers of a strategic KPI.
  - supporting: base or helper KPI needed to compute/interpret others.

- strategic_ref
  - What: Human name of the parent strategic KPI this KPI supports (if applicable).
  - Use when a diagnostic/supporting KPI ladders to a strategic KPI.

- impact_dimension
  - One of: Growth, Profitability, Liquidity, Efficiency, Customer, ESG, Governance.
  - Choose the primary impact lens for decision-making.

- domain_tag
  - What: One or more business domains; e.g., Commercial, Operational Efficiency, Customer & Market, Corporate & Strategy, ESG, Governance.
  - Use the domain most responsible for the KPI.

- use_case_ref
  - What: List of Use Case IDs this KPI is used in (e.g., ["COM-001"]).
  - Helps traceability from KPI ↔ Use Case.

- depends_on
  - What: Human-readable KPI keys this KPI conceptually depends on (not lineage).
  - Example: for "Δ% Net Sales" → ["Δ Net Sales Amount", "Net Sales Amount LY"].

- calc_type
  - amount (currency/absolute), rate (calculated rate like %), ratio (unitless ratio), count (integer count).
  - Choose based on unit and formatting behavior.

- refresh / status
  - refresh: expected data cadence (daily/weekly/monthly/quarterly).
  - status: Active/Draft/Deprecated to signal lifecycle.

- business block
  - purpose: Why this KPI exists and the decision it informs (1–2 sentences).
  - definition: Business definition; include baseline or filter logic if relevant.
  - grain_scope: Data grain and aggregation scope (e.g., invoice_line aggregated monthly by Org/Product/Date).
  - unit_format: Display unit guidance (e.g., "% (1 decimal)", "€ (2 decimals)", "days").
  - interpretation: How to read changes and what good/bad looks like.

- technical block
  - dax_name: The exact measure name in the model.
  - dax_expression: DAX (or semantic formula) when available; keep consistent with definition.
  - formatString: Valid Power BI format string (e.g., "€ #,0.00", "0.0 %", "0").
  - displayFolder: Optional model folder path for organization.
  - description: Short, structured sentence combining purpose/definition/unit.
  - lineage/source_*: Tables/columns and source systems involved; clarify model vs source grain.
  - verified: true once the measure compiles and passes basic QA.

- governance block
  - business_owner: Accountable business role/team.
  - data_owner: Technical/data team owning the pipeline/model.
  - steward: Optional caretaker role for metadata quality.
  - review_cycle: cadence for KPI stewardship (e.g., quarterly).
  - validation_process: "automated", "manual", or "dual control"; aligns to QA rigor.
  - qa_rules: Concrete checks with thresholds (e.g., "Variance reconciliation within ±0.1 pp").
  - version / last_review: Use to track governance changes and last validation.

- metadata_quality
  - completeness_score: 0..1 subjective coverage score of filled fields.
  - lineage_verified: true when lineage has been confirmed from source to model.
  - copilot_ready: true when naming/formatting/descriptions are sufficient for automated tooling.

- aliases
  - Alternative human names (e.g., legacy labels or symbol-free variants) to aid searchability.

---

## Mini Examples

Amount (currency)
```yaml
- kpi_id: "margin.gm.amount"
  kpi_key: "Gross Margin Amount"
  kpi_type: "supporting"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  calc_type: amount
  business:
    purpose: "Shows absolute gross margin before OpEx."
    definition: "Net Sales Amount - COGS Amount"
    grain_scope: "Invoice line aggregated monthly by Org/Product/Date"
    unit_format: "€ (2 decimals)"
    interpretation: "Higher is better; use with GM % for quality."
  technical:
    dax_name: "Gross Margin Amount"
    dax_expression: "[Net Sales Amount] - [COGS Amount]"
    formatString: "€ #,0.00"
    description: "Absolute GM; NS - COGS; € #,0.00; monthly"
    verified: true
  governance:
    business_owner: "Head of Controlling"
    data_owner: "BI Engineering"
    review_cycle: "quarterly"
    qa_rules: ["Reconcile with P&L GM within ±0.5 %"]
```

Rate (percentage)
```yaml
- kpi_id: "sales.revenue.growth_pct"
  kpi_key: "Revenue Growth %"
  kpi_type: "strategic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  calc_type: rate
  business:
    purpose: "Top-line expansion vs baseline"
    definition: "(Net Sales - Net Sales LY) / Net Sales LY"
    grain_scope: "Aggregated monthly by Org"
    unit_format: "% (1 decimal)"
    interpretation: ">0% indicates growth vs LY"
  technical:
    dax_name: "Revenue Growth %"
    dax_expression: "DIVIDE([Net Sales Amount]-[Net Sales Amount LY],[Net Sales Amount LY])"
    formatString: "0.0 %"
    verified: true
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
- Reference the schema in each catalog's header; do not embed schema copies.
- Prefer adding aliases for legacy names with symbols (e.g., “Δ”, “Δ%”) to support readability.

Last updated: 04.11.2025


