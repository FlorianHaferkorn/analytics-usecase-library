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
  use_case_ref:
    - "COM-001"
    - "COM-002"
  depends_on:
    - "Δ Net Sales Amount"
    - "Net Sales Amount LY"
  depends_on_ids:
    - "sales.net_sales.delta_amount.ly"
    - "sales.net_sales.amount.ly"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measures top-line expansion versus Plan and Last Year."
    definition:
      "((Net Sales Amount - Net Sales Amount LY) / Net Sales Amount LY)"
    grain_scope:
      "Aggregated at month and org level."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Shows revenue momentum and market success."
  technical:
    dax_name:
      "Revenue Growth %"
    dax_expression:
      "DIVIDE([Δ Net Sales Amount],[Net Sales Amount LY])"
    formatString:
      "0.0 %"
    description:
      "Growth rate vs last year revenue."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.Net Sales Amount LY"
    source_grain:
      "invoice_line"
    source_column_ref:
      "fact_sales.net_sales_amt"
    source_system:
      "ERP"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Sales"
    data_owner:
      "BI Engineering"
    steward:
      "Sales Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "dual control"
    qa_rules:
      "Variance within ±0.1 pp of plan reconciliation"
    version:
      "v2.0"
    last_review:
      "03.11.2025"
  metadata_quality:
    completeness_score:
      "0.96"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
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
  depends_on:
    - "Net Sales Amount (source)"
  depends_on_ids:
    - "sales.net_sales.amount"
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

    description: "Growth rate vs last year revenue."
    formatString: "0.0 %"
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

    description: "Growth rate vs last year revenue."
    formatString: "0.0 %"
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
  aliases: ["Delta Net Sales Amount","Δ Net Sales Amount"]
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

    description: "Growth rate vs last year revenue."
    formatString: "0.0 %"
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


- kpi_id: "sales.promo.uplift_pct"
  kpi_key: "Promo Uplift %"
  kpi_type: "diagnostic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  calc_type: rate
  refresh: weekly
  status: Active
  business:
    purpose: "Measures incremental sales generated during a promotion versus the baseline."
    definition: "(Promo Sales Amount - Baseline Sales Amount) / Baseline Sales Amount."
    grain_scope: "Promo period / product / channel."
    unit_format: "% (1 decimal)"
    interpretation: "Shows effectiveness of promo mechanics and depth."
  technical:
    dax_name: "Promo Uplift %"
    dax_expression: "DIVIDE([Promo Sales Amount]-[Baseline Sales Amount],[Baseline Sales Amount])"
    formatString: "0.0 %"
    displayFolder: "03_Price_Promo"
    description: "Relative uplift of promo sales versus baseline volume."
    lineage: ["fact_sales.Promo Sales Amount","fact_sales.Baseline Sales Amount"]
    source_grain: "invoice_line"
    source_system: "Trade Marketing"
    verified: false
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "BI Engineering"
    steward: "Trade Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Baseline method documented"
      - "Exclude promos with <5 transactions"
    version: "v1.1"
    last_review: "11.11.2025"

- kpi_id: "sales.net_sales.delta_pct.ly"
  kpi_key: "Δ% Net Sales"
  aliases: ["Delta% Net Sales","Δ% Net Sales"]
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

    description: "Growth rate vs last year revenue."
    formatString: "0.0 %"
    formatString: "0.0 %"
    displayFolder: "01_Sales"
    description: "Δ Net Sales / LY. Grain & Scope: period-level. Unit/Format: 0.0 %."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true

  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "Commercial BI"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to Net Sales and LY revenue within +/- 0.1 pp"
    version: "v1.0"
    last_review: "2025-11-04"

- kpi_id: "sales.price.realization_pct"
  kpi_key: "Price Realization %"
  kpi_type: "diagnostic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-002","COM-003"]
  calc_type: rate
  refresh: weekly
  status: Active
  business:
    purpose: "Shows how much of list price is realized after discounts."
    definition: "Net Sales Amount / List Price Amount."
    grain_scope: "Invoice line aggregated to reporting period."
    unit_format: "% (1 decimal)"
    interpretation: "Values below 100% indicate discounting; values above 100% indicate uplift vs list price."
  technical:
    dax_name: "Price Realization %"
    dax_expression: "DIVIDE([Net Sales Amount],[List Price Amount])"
    formatString: "0.0 %"
    displayFolder: "03_Price_Promo"
    description: "Net price versus list price to monitor discount discipline."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.List Price Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "Pricing Team"
    steward: "Pricing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Bounds [0%; 150%]"
      - "List price source reconciled to price books"
    version: "v1.1"
    last_review: "11.11.2025"
- kpi_id: "sales.list_price.amount"
  kpi_key: "List Price Amount"
  kpi_type: "supporting"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  calc_type: "amount"
  business:
    purpose:
      "Provide the list price value of invoiced units as reference for price realization and discount analysis."
    definition:
      "Sum of list price per unit multiplied by quantity for the selected period and slice."
    grain_scope:
      "Invoice line; aggregated to reporting period and segment."
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Used as denominator or reference for price realization; interpret mainly via derived ratios such as Price Realization %."
  technical:
    dax_name:
      "List Price Amount"
    formatString:
      "€ #,0.00"
    description:
      "List price value for invoiced units in the selected context."
    lineage:
      - "fact_sales.List Price Amount"
    source_grain:
      "invoice_line"
    source_column_ref:
      - "fact_sales.ListPriceAmount"
    source_system:
      "ERP"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Pricing"
    data_owner:
      "Commercial BI"
    steward:
      "Pricing Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "reconciled against price books and invoice data"
    qa_rules:
      - "List price amounts reconcile to price master within tolerance"
    version:
      "v1.0"
    last_review:
      "2025-11-06"
- kpi_id: "sales.promo.uplift_pct"
  kpi_key: "Promo Uplift %"
  kpi_type: "diagnostic"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  calc_type: rate
  technical:
    dax_name: "Promo Uplift %"
    dax_expression: "DIVIDE([Promo Sales Amount]-[Baseline Sales Amount],[Baseline Sales Amount])"
    description: "Growth rate vs last year revenue."
    formatString: "0.0 %"   
    displayFolder: "01_Sales"
    verified: false
  business:
    purpose: "Measure incremental sales impact of promotions versus baseline demand."
    definition: "(Promo Sales Amount - Baseline Sales Amount) / Baseline Sales Amount"
    grain_scope: "SKU/channel/period at promo vs baseline windows; aggregated to reporting level."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "Commercial BI"
    steward: "Promotion Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Bounds [ -100%; +500% ]; reconcile promo uplift with campaign post-analysis within +/- 1 pp"
    version: "v1.0"
    last_review: "2025-11-04"

- kpi_id: "sales.pvm.price_effect.amount"
  kpi_key: "Price Effect Amount"
  kpi_type: "diagnostic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Quantifies the pure price impact in the PVM bridge."
    definition: "(Actual Price - Plan Price) x Actual Quantity."
    grain_scope: "Aggregated to reporting period / segment."
    unit_format: "EUR (2 decimals)"
    interpretation: "Positive values indicate price gains; negative values represent price pressure."
  technical:
    dax_name: "Price Effect Amount"
    dax_expression: "([Actual Unit Price]-[Plan Unit Price]) * [Actual Units Qty]"
    formatString: "EUR #,0.00"
    displayFolder: "04_PVM"
    description: "Isolates the price component of variance using plan vs actual unit price."
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Plan price locked before period"
      - "Exclude items without plan price"
    version: "v1.1"
    last_review: "11.11.2025"

- kpi_id: "sales.pvm.volume_effect.amount"
  kpi_key: "Volume Effect Amount"
  kpi_type: "diagnostic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Measures the variance caused purely by quantity changes at plan price."
    definition: "(Actual Quantity - Plan Quantity) x Plan Price."
    grain_scope: "Aggregated to reporting period / segment."
    unit_format: "EUR (2 decimals)"
    interpretation: "Positive values indicate higher volume than plan; negative values indicate volume shortfalls."
  technical:
    dax_name: "Volume Effect Amount"
    dax_expression: "([Actual Units Qty]-[Plan Units Qty]) * [Plan Unit Price]"
    formatString: "EUR #,0.00"
    displayFolder: "04_PVM"
    description: "Pure volume contribution within the PVM variance bridge."
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Plan quantity frozen"
      - "Exclude negative plan quantities"
    version: "v1.1"
    last_review: "11.11.2025"

- kpi_id: "sales.pvm.mix_effect.amount"
  kpi_key: "Mix Effect Amount"
  kpi_type: "diagnostic"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Captures the residual effect from changes in product, channel, or region mix."
    definition: "Total variance - Price Effect - Volume Effect."
    grain_scope: "Aggregated to reporting period / segment."
    unit_format: "EUR (2 decimals)"
    interpretation: "Explains whether composition shifts drive positive or negative outcomes."
  technical:
    dax_name: "Mix Effect Amount"
    dax_expression: "[Δ Net Sales Amount] - [Price Effect Amount] - [Volume Effect Amount]"
    formatString: "EUR #,0.00"
    displayFolder: "04_PVM"
    description: "Residual mix contribution in the PVM bridge."
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Price + Volume + Mix reconcile to total variance"
    version: "v1.1"
    last_review: "11.11.2025"

- kpi_id: "sales.promo.amount"
  kpi_key: "Promo Sales Amount"
  kpi_type: "supporting"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  calc_type: amount
  technical:
    dax_name: "Promo Sales Amount"
    description: "Revenue during promotional period"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "Sales value attributed to promotions for uplift analysis."
    definition: "Sum of invoice line amount during promo flag/period"
    grain_scope: "Invoice line"
    unit_format: "EUR (2 decimals)"
  governance:
    business_owner: "Trade Marketing Lead"
    data_owner: "Commercial BI"
    steward: "Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Promo flag/period source reconciles within +/- 0.1 %"

- kpi_id: "sales.baseline.amount"
  kpi_key: "Baseline Sales Amount"
  kpi_type: "supporting"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  calc_type: "amount"
  business:
    purpose: "Baseline reference for calculating promotional uplift."
    definition: "Modeled or historical average sales excluding promo effect."
    grain_scope: "Invoice line aggregated to period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Used as baseline for promo uplift and ROI calculations; interpret together with Promo Sales Amount."
  technical:
    dax_name: "Baseline Sales Amount"
    dax_expression: ""
    formatString: "EUR #,0.00"
    description: "Expected sales without promotion, used as baseline for promo uplift."
    verified: false
  governance:
    business_owner: "Trade Marketing Lead"
    data_owner: "Commercial BI"
    steward: "Data Scientist"
    review_cycle: "quarterly"
    validation_process: "model validation"
    qa_rules:
      - "Baseline method documented; drift monitored"

- kpi_id: "sales.net_sales.amount.forecast"
  kpi_key: "Net Sales Amount (Forecast)"
  kpi_type: "supporting"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-008"
  depends_on:
    - "Net Sales Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Provide forecasted net sales for planning and forecast accuracy analysis."
    definition: "Forecasted Net Sales Amount for a given period, channel, and product scope."
    grain_scope: "Forecast line aggregated to reporting period by Org/Channel/Product."
    unit_format: "EUR (2 decimals)"
    interpretation: "Used as baseline for forecast accuracy KPIs; compare with actual Net Sales Amount."
  technical:
    dax_name: "Net Sales Amount (Forecast)"
    dax_expression: ""
    formatString: "EUR #,0.00"
    displayFolder: "02_Forecast"
    description: "Forecasted Net Sales Amount used for forecast accuracy and bias calculations."
    lineage:
      - "fact_forecast.Net Sales Amount"
    source_grain: "forecast_line"
    source_column_ref:
      - "fact_forecast.net_sales_amt_fcst"
    source_system: "Planning"
    verified: false
  governance:
    business_owner: "Head of Sales Planning"
    data_owner: "Commercial BI"
    steward: "Sales Planning Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Forecast version frozen before month start"
    version: "v0.1"
    last_review: "19.11.2025"
  metadata_quality:
    completeness_score: 0.85
    lineage_verified: false
    copilot_ready: true

- kpi_id: "sales.forecast.mape_pct"
  kpi_key: "Forecast Accuracy (MAPE %)"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-008"
  depends_on:
    - "Net Sales Amount"
    - "Net Sales Amount (Forecast)"
  depends_on_ids:
    - "sales.net_sales.amount"
    - "sales.net_sales.amount.forecast"
  calc_type: "rate"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Quantify average absolute forecast error of net sales versus actuals."
    definition: "Mean Absolute Percentage Error between Net Sales Amount and Net Sales Amount (Forecast) for all periods in scope."
    grain_scope: "Org/Channel/Product aggregated to month or week."
    unit_format: "% (1 decimal)"
    interpretation: "Lower MAPE % indicates better forecast quality; values above 20–30 % typically require forecast model review."
  technical:
    dax_name: "Forecast Accuracy (MAPE %)"
    dax_expression: ""
    formatString: "0.0 %"
    displayFolder: "02_Forecast"
    description: "Mean absolute percentage error of Net Sales Forecast versus actual Net Sales."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_forecast.Net Sales Amount"
    source_grain: "invoice_line and forecast_line"
    source_column_ref:
      - "fact_sales.net_sales_amt"
      - "fact_forecast.net_sales_amt_fcst"
    source_system: "ERP; Planning"
    verified: false
  governance:
    business_owner: "Head of Sales Planning"
    data_owner: "Commercial BI"
    steward: "Sales Planning Analyst"
    review_cycle: "monthly"
    validation_process: "automated"
    qa_rules:
      - "Exclude periods with Net Sales Amount = 0 from MAPE calculation"
    version: "v0.1"
    last_review: "19.11.2025"
  metadata_quality:
    completeness_score: 0.85
    lineage_verified: false
    copilot_ready: true

- kpi_id: "sales.forecast.bias_pct"
  kpi_key: "Forecast Bias %"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-008"
  depends_on:
    - "Net Sales Amount"
    - "Net Sales Amount (Forecast)"
  depends_on_ids:
    - "sales.net_sales.amount"
    - "sales.net_sales.amount.forecast"
  calc_type: "rate"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Indicate systematic over- or under-forecasting of net sales."
    definition: "(Net Sales Amount (Forecast) - Net Sales Amount) / Net Sales Amount."
    grain_scope: "Org/Channel/Product aggregated to month or week."
    unit_format: "% (1 decimal)"
    interpretation: "Positive values indicate over-forecasting; negative values indicate under-forecasting; values close to 0 % indicate unbiased forecasts."
  technical:
    dax_name: "Forecast Bias %"
    dax_expression: ""
    formatString: "0.0 %"
    displayFolder: "02_Forecast"
    description: "Systematic forecast bias of Net Sales, as percentage of actual Net Sales."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_forecast.Net Sales Amount"
    source_grain: "invoice_line and forecast_line"
    source_column_ref:
      - "fact_sales.net_sales_amt"
      - "fact_forecast.net_sales_amt_fcst"
    source_system: "ERP; Planning"
    verified: false
  governance:
    business_owner: "Head of Sales Planning"
    data_owner: "Commercial BI"
    steward: "Sales Planning Analyst"
    review_cycle: "monthly"
    validation_process: "automated"
    qa_rules:
      - "Bias monitored at least at total company and main channel level"
    version: "v0.1"
    last_review: "19.11.2025"
  metadata_quality:
    completeness_score: 0.85
    lineage_verified: false
    copilot_ready: true

- kpi_id: "sales.net_sales.channel_share.pct"
  kpi_key: "Channel Net Sales Share %"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-009"
  depends_on:
    - "Net Sales Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
  calc_type: "rate"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Show the share of total net sales generated by each channel."
    definition: "Net Sales Amount of a given channel divided by total Net Sales Amount across all channels."
    grain_scope: "Channel / Org / Product aggregated to month or quarter."
    unit_format: "% (1 decimal)"
    interpretation: "Highlights relative channel importance and enables channel mix optimization."
  technical:
    dax_name: "Channel Net Sales Share %"
    dax_expression: ""
    formatString: "0.0 %"
    displayFolder: "01_Sales"
    description: "Share of total Net Sales attributable to a given channel."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "dim_channel.Channel"
    source_grain: "invoice_line"
    source_column_ref:
      - "fact_sales.net_sales_amt"
      - "dim_channel.channel"
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Channel Management"
    data_owner: "Commercial BI"
    steward: "Channel Performance Analyst"
    review_cycle: "monthly"
    validation_process: "automated"
    qa_rules:
      - "Channel shares sum to 100 % per scope"
    version: "v0.1"
    last_review: "19.11.2025"
  metadata_quality:
    completeness_score: 0.85
    lineage_verified: false
    copilot_ready: true

- kpi_id: "margin.gm.channel_contribution.amount"
  kpi_key: "Channel Gross Margin Contribution Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-009"
  depends_on:
    - "Gross Margin Amount"
  depends_on_ids:
    - "margin.gm.amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Measure the absolute gross margin contribution of each channel to total profitability."
    definition: "Gross Margin Amount aggregated by channel and period."
    grain_scope: "Channel / Org / Product aggregated to month or quarter."
    unit_format: "EUR (2 decimals)"
    interpretation: "Higher contribution indicates more profitable channels; interpret together with Channel Net Sales Share %."
  technical:
    dax_name: "Channel Gross Margin Contribution Amount"
    dax_expression: ""
    formatString: "EUR #,0.00"
    displayFolder: "02_Margin"
    description: "Gross Margin Amount by channel for profitability contribution analysis."
    lineage:
      - "fact_sales.Gross Margin Amount"
      - "dim_channel.Channel"
    source_grain: "invoice_line"
    source_column_ref:
      - "fact_sales.gross_margin_amt"
      - "dim_channel.channel"
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "Commercial BI"
    steward: "Channel Performance Analyst"
    review_cycle: "monthly"
    validation_process: "automated"
    qa_rules:
      - "Channel GM reconciles with total GM within ±0.5 %"
    version: "v0.1"
    last_review: "19.11.2025"
  metadata_quality:
    completeness_score: 0.85
    lineage_verified: false
    copilot_ready: true
```


