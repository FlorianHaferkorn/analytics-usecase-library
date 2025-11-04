# KPI Catalog - Growth
---

## KPIs - Strategic
```yaml
- kpi_id: "sales.revenue.growth_pct"
  kpi_key: "Revenue Growth %"
  kpi_type: "strategic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001", "COM-002"]
  depends_on: ["Δ Net Sales Amount", "Net Sales Amount LY"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Measures top-line expansion versus Plan and Last Year."
    definition: "((Net Sales Amount - Net Sales Amount LY) / Net Sales Amount LY)"
    grain_scope: "Aggregated at month and org level."
    unit_format: "% (1 decimal)"
    interpretation: "Shows revenue momentum and market success."
  technical:
    dax_name: "Revenue Growth %"
    dax_expression: "DIVIDE([Δ Net Sales Amount],[Net Sales Amount LY])"
    lineage: ["fact_sales.Net Sales Amount","fact_sales.Net Sales Amount LY"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.net_sales_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Variance within ±0.1 pp of plan reconciliation"
    version: "v2.0"
    last_review: "03.11.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "sales.net_sales.amount"
  kpi_key: "Net Sales Amount"
  kpi_type: "supporting"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: ["Invoice Line Amount"]
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Total invoiced revenue net of discounts and returns."
    definition: "Sum of all invoice line amounts net of VAT and returns."
    grain_scope: "Invoice line."
    unit_format: "EUR (2 decimals)"
    interpretation: "Represents total top-line sales."
  technical:
    dax_name: "Net Sales Amount"
    dax_expression: "SUM(fact_sales[Net Sales Amount])"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: total invoiced sales excluding returns and taxes. Definition: sum of invoice line amounts net of VAT/returns. Grain & Scope: invoice_line aggregated to reporting period by Date/Org/Product. Unit/Format: EUR #,0.00. Lineage: fact_sales[Net Sales Amount]. QA: reconciles with P&L revenue within ±0.1%."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.net_sales_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    version: "v2.0"
    last_review: "03.11.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
  copilot_ready: true

- kpi_id: "sales.net_sales.amount.ly"
  kpi_key: "Net Sales Amount LY"
  kpi_type: "supporting"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: ["Δ Net Sales Amount"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Last year's net sales for period-over-period comparison."
    definition: "Net Sales Amount shifted by one year (same period last year)."
    grain_scope: "Aggregated from invoice line to period granularity."
    unit_format: "EUR (2 decimals)"
    interpretation: "Baseline reference for growth and variance."
  technical:
    dax_name: "Net Sales Amount LY"
    dax_expression: "CALCULATE([Net Sales Amount], SAMEPERIODLASTYEAR('Date'[Date]))"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: prior year reference for revenue comparison. Definition: [Net Sales Amount] shifted by SAMEPERIODLASTYEAR. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: fact_sales[Net Sales Amount], dim_date[Date]. QA: reconciles to prior year totals within ±0.1%."
    lineage: ["fact_sales.Net Sales Amount","dim_date.Date"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.net_sales_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    version: "v2.0"
    last_review: "03.11.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true

- kpi_id: "sales.net_sales.delta_amount.ly"
  kpi_key: "Δ Net Sales Amount"
  aliases: ["Delta Net Sales Amount", "? Net Sales Amount"]
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  depends_on: ["Δ Net Sales Amount","Net Sales Amount LY"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Absolute variance of Net Sales vs Last Year."
    definition: "Net Sales Amount - Net Sales Amount LY"
    grain_scope: "Aggregated to reporting period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Explains magnitude of change in revenue."
  technical:
    dax_name: "Δ Net Sales Amount"
    dax_expression: "[Net Sales Amount] - [Net Sales Amount LY]"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: absolute variance of revenue vs LY. Definition: [Net Sales Amount]-[Net Sales Amount LY]. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: measures above. QA: variance reconciliation within ±0.1 pp."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    version: "v2.0"
    last_review: "03.11.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true

- kpi_id: "sales.net_sales.delta_pct.ly"
  kpi_key: "Δ% Net Sales"
  aliases: ["Delta% Net Sales", "?% Net Sales"]
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: ["Δ Net Sales Amount","Net Sales Amount LY"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Relative variance of Net Sales vs Last Year."
    definition: "(Net Sales - LY) / LY"
    grain_scope: "Aggregated to reporting period."
    unit_format: "% (1 decimal)"
    interpretation: "Shows growth rate vs prior year."
  technical:
    dax_name: "Δ% Net Sales"
    dax_expression: "DIVIDE([Δ Net Sales Amount],[Net Sales Amount LY])"
    formatString: "0.0 %"
    displayFolder: "01_Sales"
    description: "Δ Net Sales / LY. Grain & Scope: period-level. Unit/Format: 0.0 %."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true

- kpi_id: "sales.price.realization_pct"
  kpi_key: "Price Realization %"
  kpi_type: "diagnostic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-002","COM-003"]
  calc_type: rate
  technical:
    dax_name: "Price Realization %"
    dax_expression: "DIVIDE([Net Sales Amount],[List Price Amount])"
    displayFolder: "01_Sales"
    formatString: "0.0 %"
    verified: false

- kpi_id: "sales.promo.uplift_pct"
  kpi_key: "Promo Uplift %"
  kpi_type: "diagnostic"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  calc_type: rate
  technical:
    dax_name: "Promo Uplift %"
    dax_expression: "DIVIDE([Promo Sales Amount]-[Baseline Sales Amount],[Baseline Sales Amount])"
    displayFolder: "01_Sales"
    formatString: "0.0 %"
    verified: false

- kpi_id: "sales.pvm.price_effect.amount"
  kpi_key: "Price Effect Amount"
  kpi_type: "diagnostic"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  calc_type: amount
  technical:
    dax_name: "Price Effect Amount"
    dax_expression: "([Actual Unit Price]-[Plan Unit Price]) * [Actual Units Qty]"
    displayFolder: "01_Sales"
    formatString: "€ #,0.00"
    verified: false

- kpi_id: "sales.pvm.volume_effect.amount"
  kpi_key: "Volume Effect Amount"
  kpi_type: "diagnostic"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  calc_type: amount
  technical:
    dax_name: "Volume Effect Amount"
    dax_expression: "([Actual Units Qty]-[Plan Units Qty]) * [Plan Unit Price]"
    displayFolder: "01_Sales"
    formatString: "€ #,0.00"
    verified: false

- kpi_id: "sales.pvm.mix_effect.amount"
  kpi_key: "Mix Effect Amount"
  kpi_type: "diagnostic"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  depends_on: ["Δ Net Sales Amount","Price Effect Amount","Volume Effect Amount"]
  calc_type: amount
  technical:
    dax_name: "Mix Effect Amount"
    dax_expression: "[Δ Net Sales Amount] - [Price Effect Amount] - [Volume Effect Amount]"
    displayFolder: "01_Sales"
    formatString: "€ #,0.00"
    verified: false
```

Last updated: 04.11.2025



