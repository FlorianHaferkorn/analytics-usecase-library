# Measure Dictionary - Growth

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

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
    dax: |
      SUM ( fact_sales[Net Sales Amount] )
        - SUM ( fact_sales[Cost of Goods Sold Amount] )
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
    dax: |
      VAR NetPrice  = SUM ( fact_sales[Net Price Amount] )
      VAR ListPrice = SUM ( fact_sales[List Price Amount] )
      RETURN DIVIDE ( NetPrice, ListPrice )
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
  is_kpi_measure: true
  kpi_id_ref: "sales.baseline.amount"
  semantic_model: "Growth_SemanticModel"
  display_folder: "04_Promo"
  category: "KPI"
  expression:
    dax: "SUM ( fact_sales[Baseline Sales Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Baseline sales amount for promo comparison."
    notes: |
      Grain: promotion. Unit: EUR.
      Lineage: fact_sales[Baseline Sales Amount].
      QA: Baseline definition consistent; promo scoping applied.
  dependencies:
    columns:
      - "fact_sales[Baseline Sales Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Net Sales Amount LY"
  is_kpi_measure: true
  kpi_id_ref: "sales.net_sales.amount.ly"
  semantic_model: "Growth_SemanticModel"
  display_folder: "01_Growth"
  category: "KPI"
  expression:
    dax: "SUM ( fact_sales[Net Sales Amount LY] )"
    formatString: "EUR #,0"
  documentation:
    description: "Net sales for the same period last year."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_sales[Net Sales Amount LY].
      QA: LY mapping aligned to fiscal calendar.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount LY]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "List Price Amount"
  is_kpi_measure: true
  kpi_id_ref: "sales.list_price.amount"
  semantic_model: "Growth_SemanticModel"
  display_folder: "03_Pricing"
  category: "KPI"
  expression:
    dax: "SUM ( fact_sales[List Price Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "List price value before discounts."
    notes: |
      Grain: invoice_line / month. Unit: EUR.
      Lineage: fact_sales[List Price Amount].
      QA: Excludes taxes; list price versioning documented.
  dependencies:
    columns:
      - "fact_sales[List Price Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Promo Amount"
  is_kpi_measure: true
  kpi_id_ref: "sales.promo.amount"
  semantic_model: "Growth_SemanticModel"
  display_folder: "04_Promo"
  category: "KPI"
  expression:
    dax: "SUM ( fact_promo[Promo Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Total promotional spend or discount amount."
    notes: |
      Grain: promotion / period. Unit: EUR.
      Lineage: fact_promo[Promo Amount].
      QA: Promo scoping and attribution documented.
  dependencies:
    columns:
      - "fact_promo[Promo Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Promo Uplift %"
  is_kpi_measure: true
  kpi_id_ref: "sales.promo.uplift_pct"
  semantic_model: "Growth_SemanticModel"
  display_folder: "04_Promo"
  category: "KPI"
  expression:
    dax: |
      VAR PromoSales = SUM ( fact_sales[Promo Sales Amount] )
      VAR Baseline   = [Baseline Sales Amount]
      RETURN DIVIDE ( PromoSales - Baseline, Baseline )
    formatString: "0.0%"
  documentation:
    description: "Relative uplift of promo sales vs baseline."
    notes: |
      Grain: promotion / period. Unit: %.
      QA: Baseline definition consistent; DIVIDE guard.
  dependencies:
    measures:
      - "Baseline Sales Amount"
    columns:
      - "fact_sales[Promo Sales Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast Net Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Growth_SemanticModel"
  display_folder: "05_Forecast"
  category: "Base"
  expression:
    dax: "SUM ( fact_forecast[Net Sales Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Forecasted net sales amount."
    notes: |
      Grain: sku_month or org_month. Unit: EUR.
      Lineage: fact_forecast[Net Sales Amount].
      QA: Versioned forecast; calendar alignment.
  dependencies:
    columns:
      - "fact_forecast[Net Sales Amount]"
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
    dax: |
      VAR Forecast = [Forecast Net Sales Amount]
      VAR Actual   = [Net Sales Amount]
      RETURN DIVIDE ( ABS ( Forecast - Actual ), Actual )
    formatString: "0.0%"
  documentation:
    description: "Mean absolute percentage error for sales forecast."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Actual > 0; outlier handling; DIVIDE guard.
  dependencies:
    measures:
      - "Forecast Net Sales Amount"
      - "Net Sales Amount"
    columns:
      - "fact_forecast[Net Sales Amount]"
      - "fact_sales[Net Sales Amount]"
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
    dax: |
      VAR Forecast = [Forecast Net Sales Amount]
      VAR Actual   = [Net Sales Amount]
      RETURN DIVIDE ( Forecast - Actual, Actual )
    formatString: "0.0%"
  documentation:
    description: "Bias of sales forecast: (Forecast - Actual) / Actual."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Actual > 0; bias band defined.
  dependencies:
    measures:
      - "Forecast Net Sales Amount"
      - "Net Sales Amount"
    columns:
      - "fact_forecast[Net Sales Amount]"
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
