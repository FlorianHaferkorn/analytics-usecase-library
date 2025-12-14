# Measure Dictionary - Growth

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Revenue Growth %"
  is_kpi_measure: true
  kpi_id_ref: "sales.revenue.growth_pct"
  semantic_model: "Growth_SemanticModel"
  display_folder: "01_Growth"
  category: "KPI"
  expression:
    dax: |
      VAR Curr = SUM ( fact_sales[Net Sales Amount] )
      VAR Ly   = SUM ( fact_sales[Net Sales Amount LY] )
      RETURN DIVIDE ( Curr - Ly, Ly )
    formatString: "0.0%"
  documentation:
    description: "Top-line momentum vs last year."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY].
      QA: LY mapping consistent; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Net Sales Amount LY]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Net Sales Amount"
  is_kpi_measure: true
  kpi_id_ref: "sales.net_sales.amount"
  semantic_model: "Growth_SemanticModel"
  display_folder: "01_Growth"
  category: "KPI"
  expression:
    dax: "SUM(fact_sales[Net Sales Amount])"
    formatString: "EUR #,0"
  documentation:
    description: "Sum of net sales after discounts."
    notes: |
      Grain: invoice_line / month. Unit: EUR.
      Lineage: fact_sales[Net Sales Amount].
      QA: Excludes VAT/returns; currency conversion upstream.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Net Sales Delta % vs LY"
  is_kpi_measure: true
  kpi_id_ref: "sales.net_sales.delta_pct.ly"
  semantic_model: "Growth_SemanticModel"
  display_folder: "01_Growth"
  category: "KPI"
  expression:
    dax: |
      VAR Curr = SUM ( fact_sales[Net Sales Amount] )
      VAR Ly   = SUM ( fact_sales[Net Sales Amount LY] )
      RETURN DIVIDE ( Curr - Ly, Ly )
    formatString: "0.0%"
  documentation:
    description: "Relative growth vs last year."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY].
      QA: DIVIDE guard; LY alignment.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Net Sales Amount LY]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Net Sales Delta Amount vs LY"
  is_kpi_measure: true
  kpi_id_ref: "sales.net_sales.delta_amount.ly"
  semantic_model: "Growth_SemanticModel"
  display_folder: "01_Growth"
  category: "KPI"
  expression:
    dax: |
      VAR Curr = SUM ( fact_sales[Net Sales Amount] )
      VAR Ly   = SUM ( fact_sales[Net Sales Amount LY] )
      RETURN Curr - Ly
    formatString: "EUR #,0"
  documentation:
    description: "Absolute growth vs last year."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY].
      QA: LY alignment; currency conversion upstream.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Net Sales Amount LY]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Channel Revenue Share %"
  is_kpi_measure: true
  kpi_id_ref: "sales.net_sales.channel_share.pct"
  semantic_model: "Growth_SemanticModel"
  display_folder: "02_Mix"
  category: "KPI"
  expression:
    dax: |
      VAR ChannelSales = SUM ( fact_sales[Net Sales Amount] )
      VAR TotalSales   =
          CALCULATE ( SUM ( fact_sales[Net Sales Amount] ), ALL ( dim_org[Channel] ) )
      RETURN DIVIDE ( ChannelSales, TotalSales )
    formatString: "0.0%"
  documentation:
    description: "Channel revenue / total revenue."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_sales[Net Sales Amount], dim_org[Channel].
      QA: Channel mapping complete; total revenue > 0.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "dim_org[Channel]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Channel Gross Margin Contribution"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.channel_contribution.amount"
  semantic_model: "Growth_SemanticModel"
  display_folder: "02_Mix"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Channel GM Contribution */"
    formatString: "EUR #,0"
  documentation:
    description: "Gross margin by channel."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], dim_org[Channel].
      QA: Channel mapping; COGS alignment.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "dim_org[Channel]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Price Realization %"
  is_kpi_measure: true
  kpi_id_ref: "sales.price.realization_pct"
  semantic_model: "Growth_SemanticModel"
  display_folder: "03_Pricing"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Price Realization % */"
    formatString: "0.0%"
  documentation:
    description: "Net Price / List Price."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_sales[Net Price Amount], fact_sales[List Price Amount].
      QA: List price excludes taxes; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Price Amount]"
      - "fact_sales[List Price Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Baseline Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Growth_SemanticModel"
  display_folder: "04_Promo"
  category: "Base"
  expression:
    dax: "/* TODO: implement Baseline Sales Amount */"
    formatString: "EUR #,0"
  documentation:
    description: "Baseline sales amount for promo comparison."
    notes: |
      Grain: promotion. Unit: EUR.
      Lineage: fact_promo[Baseline Sales Amount].
      QA: Baseline definition consistent; promo scoping applied.
  dependencies:
    columns:
      - "fact_promo[Baseline Sales Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast Net Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: "sales.net_sales.amount.forecast"
  semantic_model: "Growth_SemanticModel"
  display_folder: "05_Forecast"
  category: "Base"
  expression:
    dax: "/* TODO: implement Forecast Net Sales Amount */"
    formatString: "EUR #,0"
  documentation:
    description: "Forecasted net sales amount."
    notes: |
      Grain: sku_month or org_month. Unit: EUR.
      Lineage: fact_forecast[Forecast Net Sales Amount].
      QA: Versioned forecast; calendar alignment.
  dependencies:
    columns:
      - "fact_forecast[Forecast Net Sales Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast MAPE %"
  is_kpi_measure: true
  kpi_id_ref: "sales.forecast.mape_pct"
  semantic_model: "Growth_SemanticModel"
  display_folder: "05_Forecast"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Forecast MAPE % */"
    formatString: "0.0%"
  documentation:
    description: "Mean absolute percentage error for sales forecast."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Actual > 0; outlier handling; DIVIDE guard.
  dependencies:
    columns:
      - "fact_forecast[Forecast]"
      - "fact_sales[Actual]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast Bias %"
  is_kpi_measure: true
  kpi_id_ref: "sales.forecast.bias_pct"
  semantic_model: "Growth_SemanticModel"
  display_folder: "05_Forecast"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Forecast Bias % */"
    formatString: "0.0%"
  documentation:
    description: "Bias of sales forecast: (Forecast - Actual) / Actual."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Actual > 0; bias band defined.
  dependencies:
    columns:
      - "fact_forecast[Forecast]"
      - "fact_sales[Actual]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
