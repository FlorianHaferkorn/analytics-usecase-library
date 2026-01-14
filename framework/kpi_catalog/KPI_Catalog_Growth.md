# KPI Catalog - Growth

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: sales.revenue.growth_pct
  kpi_key: Revenue Growth %
  kpi_type: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  calc_type: rate
  business:
    purpose: Measures top-line expansion versus last year.
    definition: ((Net Sales Amount - Net Sales Amount LY) / Net Sales Amount LY)
    grain_scope: Aggregated at month and org level.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate growth; negative values indicate contraction.
  technical:
    dax_name: Revenue Growth %
    depends_on_measures:
    - Net Sales Amount
    - Net Sales Amount LY
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Net Sales Amount LY
  governance:
    business_owner: Head of Sales
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconciles to Net Sales and LY within +/- 0.1 pp
    version: v2.0
  metadata_quality:
    completeness_score: 0.96
    last_review: 03.11.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: sales.net_sales.amount
  kpi_key: Net Sales Amount
  kpi_type: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: amount
  business:
    purpose: Total invoiced revenue net of discounts and returns.
    definition: Sum of all invoice line amounts net of VAT and returns.
    grain_scope: Invoice line.
    unit_format: EUR (2 decimals)
    interpretation: Represents total top-line sales.
  technical:
    dax_name: Net Sales Amount
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules: []
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 03.11.2025

- kpi_id: sales.net_sales.amount.ly
  kpi_key: Net Sales Amount LY
  kpi_type: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: amount
  business:
    purpose: Last year's net sales for period-over-period comparison.
    definition: Net Sales Amount shifted by one year (same period last year).
    grain_scope: Aggregated from invoice line to period granularity.
    unit_format: EUR (2 decimals)
    interpretation: Baseline reference for growth and variance.
  technical:
    dax_name: Net Sales Amount LY
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - dim_date.Date
  governance:
    business_owner: Head of Sales
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules: []
    version: v2.0
  metadata_quality:
    completeness_score: 0.96
    last_review: 03.11.2025

- kpi_id: sales.net_sales.delta_amount.ly
  kpi_key: Delta Net Sales Amount
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Absolute variance of Net Sales vs Last Year.
    definition: Net Sales Amount - Net Sales Amount LY
    grain_scope: Aggregated to reporting period.
    unit_format: EUR (2 decimals)
    interpretation: Explains magnitude of change in revenue.
  technical:
    dax_name: Delta Net Sales Amount
    depends_on_measures:
    - Net Sales Amount
    - Net Sales Amount LY
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules: []
    version: v2.0
  metadata_quality:
    completeness_score: 0.96
    last_review: 03.11.2025
  aliases:
  - Delta Net Sales Amount

- kpi_id: sales.promo.uplift_pct
  kpi_key: Promo Uplift %
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-003
  calc_type: rate
  business:
    purpose: Measures incremental sales generated during a promotion versus the baseline.
    definition: (Promo Sales Amount - Baseline Sales Amount) / Baseline Sales Amount.
    grain_scope: Promo period / product / channel.
    unit_format: '% (1 decimal)'
    interpretation: Shows effectiveness of promo mechanics and depth.
  technical:
    dax_name: Promo Uplift %
    depends_on_measures: []
    lineage:
    - fact_sales.Promo Sales Amount
    - fact_sales.Baseline Sales Amount
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Baseline method documented
    - Exclude promos with <5 transactions
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.net_sales.delta_pct.ly
  kpi_key: Delta% Net Sales
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: rate
  business:
    purpose: Relative variance of Net Sales vs Last Year.
    definition: (Net Sales - LY) / LY
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Shows growth rate vs prior year.
  technical:
    dax_name: Delta% Net Sales
    depends_on_measures:
    - Net Sales Amount
    - Net Sales Amount LY
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to Net Sales and LY revenue within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
  aliases:
  - Delta% Net Sales

- kpi_id: sales.net_sales.delta_pct.plan
  kpi_key: Net Sales % vs Plan
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: rate
  business:
    purpose: Relative variance of Net Sales vs Plan.
    definition: (Net Sales Amount - Plan Sales Amount) / Plan Sales Amount
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate outperformance vs plan; negative values indicate shortfall.
  technical:
    dax_name: Net Sales % vs Plan
    depends_on_measures:
    - Net Sales Amount
    - Plan Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Plan Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to Net Sales and Plan revenue within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: sales.price.realization_pct
  kpi_key: Price Realization %
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  calc_type: rate
  business:
    purpose: Shows how much of list price is realized after discounts.
    definition: Net Price Amount / List Price Amount.
    grain_scope: Invoice line aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Values below 100% indicate discounting; values above 100% indicate uplift vs list price.
  technical:
    dax_name: Price Realization %
    depends_on_measures:
    - Net Price Amount
    - List Price Amount
    lineage:
    - fact_sales.Net Price Amount
    - fact_sales.List Price Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Pricing Team
    steward: Pricing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounds [0%; 150%]
    - List price source reconciled to price books
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.list_price.amount
  kpi_key: List Price Amount
  kpi_type: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Provide the list price value of invoiced units as reference for price realization and discount analysis.
    definition: Sum of list price per unit multiplied by quantity for the selected period and slice.
    grain_scope: Invoice line; aggregated to reporting period and segment.
    unit_format: EUR (2 decimals)
    interpretation: Used as denominator or reference for price realization; interpret mainly via derived ratios such as Price
      Realization %.
  technical:
    dax_name: List Price Amount
    depends_on_measures: []
    lineage:
    - fact_sales.List Price Amount
  governance:
    business_owner: Head of Pricing
    data_owner: Commercial BI
    steward: Pricing Analyst
    review_cycle: quarterly
    validation_process: reconciled against price books and invoice data
    qa_rules:
    - List price amounts reconcile to price master within tolerance
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 06.11.2025

- kpi_id: sales.pvm.price_effect.amount
  kpi_key: Price Effect Amount
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Quantifies the pure price impact in the PVM bridge.
    definition: (Actual Price - Plan Price) x Actual Quantity.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Positive values indicate price gains; negative values represent price pressure.
  technical:
    dax_name: Price Effect Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan price locked before period
    - Exclude items without plan price
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.pvm.volume_effect.amount
  kpi_key: Volume Effect Amount
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Measures the variance caused purely by quantity changes at plan price.
    definition: (Actual Quantity - Plan Quantity) x Plan Price.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Positive values indicate higher volume than plan; negative values indicate volume shortfalls.
  technical:
    dax_name: Volume Effect Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan quantity frozen
    - Exclude negative plan quantities
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.pvm.mix_effect.amount
  kpi_key: Mix Effect Amount
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Captures the residual effect from changes in product, channel, or region mix.
    definition: Total variance - Price Effect - Volume Effect.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Explains whether composition shifts drive positive or negative outcomes.
  technical:
    dax_name: Mix Effect Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Price + Volume + Mix reconcile to total variance
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.promo.amount
  kpi_key: Promo Sales Amount
  kpi_type: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Sales value attributed to promotions for uplift analysis.
    definition: Sum of invoice line amount during promo flag/period
    grain_scope: Invoice line
    unit_format: EUR (2 decimals)
    interpretation: Higher values indicate stronger promo-driven sales; interpret together with baseline and ROI.
  technical:
    dax_name: Promo Sales Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Trade Marketing Lead
    data_owner: Commercial BI
    steward: Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Promo flag/period source reconciles within +/- 0.1 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025

- kpi_id: sales.baseline.amount
  kpi_key: Baseline Sales Amount
  kpi_type: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Baseline reference for calculating promotional uplift.
    definition: Modeled or historical average sales excluding promo effect.
    grain_scope: Invoice line aggregated to period.
    unit_format: EUR (2 decimals)
    interpretation: Used as baseline for promo uplift and ROI calculations; interpret together with Promo Sales Amount.
  technical:
    dax_name: Baseline Sales Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Trade Marketing Lead
    data_owner: Commercial BI
    steward: Data Scientist
    review_cycle: quarterly
    validation_process: model validation
    qa_rules:
    - Baseline method documented; drift monitored
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025

- kpi_id: sales.forecast.mape_pct
  kpi_key: Forecast Accuracy (MAPE %)
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-008
  calc_type: rate
  business:
    purpose: Quantify average absolute forecast error of revenue (Net Sales Amount) versus actuals.
    definition: Mean Absolute Percentage Error between Net Sales Amount and Net Sales Amount (Forecast) for all periods in
      scope (revenue-based, not units).
    grain_scope: Org/Channel/Product aggregated to month or week.
    unit_format: '% (1 decimal)'
    interpretation: Lower MAPE % indicates better forecast quality; values above 2030 % typically require forecast model
      review.
  technical:
    dax_name: Forecast Accuracy (MAPE %)
    depends_on_measures:
    - Net Sales Amount
    - Net Sales Amount (Forecast)
    lineage:
    - fact_sales.Net Sales Amount
    - fact_forecast.Net Sales Amount
  governance:
    business_owner: Head of Sales Planning
    data_owner: Commercial BI
    steward: Sales Planning Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Exclude periods with Net Sales Amount = 0 from MAPE calculation
    version: v0.1
  metadata_quality:
    completeness_score: 0.85
    last_review: 19.11.2025

- kpi_id: sales.forecast.bias_pct
  kpi_key: Forecast Bias %
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-008
  calc_type: rate
  business:
    purpose: Indicate systematic over- or under-forecasting of revenue (Net Sales Amount).
    definition: (Net Sales Amount (Forecast) - Net Sales Amount) / Net Sales Amount (revenue-based, not units).
    grain_scope: Org/Channel/Product aggregated to month or week.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate over-forecasting; negative values indicate under-forecasting; values close to
      0 % indicate unbiased forecasts.
  technical:
    dax_name: Forecast Bias %
    depends_on_measures:
    - Net Sales Amount
    - Net Sales Amount (Forecast)
    lineage:
    - fact_sales.Net Sales Amount
    - fact_forecast.Net Sales Amount
  governance:
    business_owner: Head of Sales Planning
    data_owner: Commercial BI
    steward: Sales Planning Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Bias monitored at least at total company and main channel level
    version: v0.1
  metadata_quality:
    completeness_score: 0.85
    last_review: 19.11.2025

- kpi_id: sales.net_sales.channel_share.pct
  kpi_key: Channel Net Sales Share %
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-009
  calc_type: rate
  business:
    purpose: Show the share of total net sales generated by each channel.
    definition: Net Sales Amount of a given channel divided by total Net Sales Amount across all channels.
    grain_scope: Channel / Org / Product aggregated to month or quarter.
    unit_format: '% (1 decimal)'
    interpretation: Highlights relative channel importance and enables channel mix optimization.
  technical:
    dax_name: Channel Net Sales Share %
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - dim_channel.Channel
  governance:
    business_owner: Head of Channel Management
    data_owner: Commercial BI
    steward: Channel Performance Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Channel shares sum to 100 % per scope
    version: v0.1
  metadata_quality:
    completeness_score: 0.85
    last_review: 19.11.2025

- kpi_id: margin.gm.channel_contribution.amount
  kpi_key: Channel Gross Margin Contribution Amount
  kpi_type: diagnostic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-009
  calc_type: amount
  business:
    purpose: Measure the absolute gross margin contribution of each channel to total profitability.
    definition: Gross Margin Amount aggregated by channel and period.
    grain_scope: Channel / Org / Product aggregated to month or quarter.
    unit_format: EUR (2 decimals)
    interpretation: Higher contribution indicates more profitable channels; interpret together with Channel Net Sales Share
      %.
  technical:
    dax_name: Channel Gross Margin Contribution Amount
    depends_on_measures:
    - Gross Margin Amount
    lineage:
    - fact_sales.Gross Margin Amount
    - dim_channel.Channel
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: Commercial BI
    steward: Channel Performance Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Channel GM reconciles with total GM within +/- 0.5 %
    version: v0.1
  metadata_quality:
    completeness_score: 0.85
    last_review: 19.11.2025
```
