# Measure Dictionary - Growth

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Revenue Growth %
  is_kpi_measure: true
  kpi_id_ref: sales.revenue.growth_pct
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Delta Net Sales Amount],[Net Sales Amount LY])
    formatString: 0.0 %
  documentation:
    description: Growth rate vs last year revenue.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 03.11.2025
  dependencies:
    measures:
    - Î” Net Sales Amount
    - Net Sales Amount LY
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.Net Sales Amount LY
- measure_name: Net Sales Amount
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: SUM(fact_sales[Net Sales Amount])
    formatString: '#,0.00'
  documentation:
    description: 'Purpose: total invoiced sales excluding returns and taxes. Definition: sum of invoice line amounts net of
      VAT/returns. Grain & Scope: invoice_line aggregated to reporting period by Date/Org/Product. Unit/Format: EUR #,0.00.
      Lineage: fact_sales[Net Sales Amount]. QA: reconciles with P&L revenue within 0.1%.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 03.11.2025
  display_folder: 01_Sales
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - fact_sales.Net Sales Amount
- measure_name: Net Sales Amount LY
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.amount.ly
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: CALCULATE([Net Sales Amount], SAMEPERIODLASTYEAR('Date'[Date]))
    formatString: '#,0.00'
  documentation:
    description: 'Purpose: prior year reference for revenue comparison. Definition: [Net Sales Amount] shifted by SAMEPERIODLASTYEAR.
      Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: fact_sales[Net Sales Amount], dim_date[Date]. QA: reconciles
      to prior year totals within 0.1%.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 03.11.2025
  display_folder: 01_Sales
  dependencies:
    measures:
    - Î” Net Sales Amount
    columns:
    - fact_sales.Net Sales Amount
    - dim_date.Date
- measure_name: Delta Net Sales Amount
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.delta_amount.ly
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '[Net Sales Amount] - [Net Sales Amount LY]'
    formatString: '#,0.00'
  documentation:
    description: 'Purpose: absolute variance of revenue vs LY. Definition: [Net Sales Amount]-[Net Sales Amount LY]. Grain
      & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: measures above. QA: variance reconciliation within 0.1 pp.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 03.11.2025
  display_folder: 01_Sales
  dependencies:
    measures:
    - Î” Net Sales Amount
    - Net Sales Amount LY
    columns:
    - fact_sales.Net Sales Amount
- measure_name: Promo Uplift %
  is_kpi_measure: true
  kpi_id_ref: sales.promo.uplift_pct
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Promo Sales Amount]-[Baseline Sales Amount],[Baseline Sales Amount])
    formatString: 0.0 %
  documentation:
    description: Relative uplift of promo sales versus baseline volume.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 03_Price_Promo
  dependencies:
    columns:
    - fact_sales.Promo Sales Amount
    - fact_sales.Baseline Sales Amount
- measure_name: Delta% Net Sales
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.delta_pct.ly
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Delta Net Sales Amount],[Net Sales Amount LY])
    formatString: 0.0 %
  documentation:
    description: 'Delta Net Sales / LY. Grain & Scope: period-level. Unit/Format: 0.0 %.'
    notes: ''
  governance:
    owner: Commercial BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  display_folder: 01_Sales
  dependencies:
    measures:
    - Î” Net Sales Amount
    - Net Sales Amount LY
    columns:
    - fact_sales.Net Sales Amount
- measure_name: Price Realization %
  is_kpi_measure: true
  kpi_id_ref: sales.price.realization_pct
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Net Sales Amount],[List Price Amount])
    formatString: 0.0 %
  documentation:
    description: Net price versus list price to monitor discount discipline.
    notes: ''
  governance:
    owner: Pricing Team
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 03_Price_Promo
  dependencies:
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.List Price Amount
- measure_name: List Price Amount
  is_kpi_measure: true
  kpi_id_ref: sales.list_price.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0.00'
  documentation:
    description: List price value for invoiced units in the selected context.
    notes: ''
  governance:
    owner: Commercial BI
    status: active
    version: v1.0
    last_review: 06.11.2025
  dependencies:
    columns:
    - fact_sales.List Price Amount
- measure_name: Price Effect Amount
  is_kpi_measure: true
  kpi_id_ref: sales.pvm.price_effect.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: ([Actual Unit Price]-[Plan Unit Price]) * [Actual Units Qty]
    formatString: 'EUR #,0.00'
  documentation:
    description: Isolates the price component of variance using plan vs actual unit price.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 04_PVM
- measure_name: Volume Effect Amount
  is_kpi_measure: true
  kpi_id_ref: sales.pvm.volume_effect.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: ([Actual Units Qty]-[Plan Units Qty]) * [Plan Unit Price]
    formatString: 'EUR #,0.00'
  documentation:
    description: Pure volume contribution within the PVM variance bridge.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 04_PVM
- measure_name: Mix Effect Amount
  is_kpi_measure: true
  kpi_id_ref: sales.pvm.mix_effect.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '[Delta Net Sales Amount] - [Price Effect Amount] - [Volume Effect Amount]'
    formatString: 'EUR #,0.00'
  documentation:
    description: Residual mix contribution in the PVM bridge.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 04_PVM
- measure_name: Promo Sales Amount
  is_kpi_measure: true
  kpi_id_ref: sales.promo.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Revenue during promotional period
    notes: ''
  governance:
    owner: Commercial BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Baseline Sales Amount
  is_kpi_measure: true
  kpi_id_ref: sales.baseline.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Expected sales without promotion, used as baseline for promo uplift.
    notes: ''
  governance:
    owner: Commercial BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Net Sales Amount (Forecast)
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.amount.forecast
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Forecasted Net Sales Amount used for forecast accuracy and bias calculations.
    notes: ''
  governance:
    owner: Commercial BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 02_Forecast
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - fact_forecast.Net Sales Amount
- measure_name: Forecast Accuracy (MAPE %)
  is_kpi_measure: true
  kpi_id_ref: sales.forecast.mape_pct
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Mean absolute percentage error of Net Sales Forecast versus actual Net Sales.
    notes: ''
  governance:
    owner: Commercial BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 02_Forecast
  dependencies:
    measures:
    - Net Sales Amount
    - Net Sales Amount (Forecast)
    columns:
    - fact_sales.Net Sales Amount
    - fact_forecast.Net Sales Amount
- measure_name: Forecast Bias %
  is_kpi_measure: true
  kpi_id_ref: sales.forecast.bias_pct
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Systematic forecast bias of Net Sales, as percentage of actual Net Sales.
    notes: ''
  governance:
    owner: Commercial BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 02_Forecast
  dependencies:
    measures:
    - Net Sales Amount
    - Net Sales Amount (Forecast)
    columns:
    - fact_sales.Net Sales Amount
    - fact_forecast.Net Sales Amount
- measure_name: Channel Net Sales Share %
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.channel_share.pct
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Share of total Net Sales attributable to a given channel.
    notes: ''
  governance:
    owner: Commercial BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 01_Sales
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - fact_sales.Net Sales Amount
    - dim_channel.Channel
- measure_name: Channel Gross Margin Contribution Amount
  is_kpi_measure: true
  kpi_id_ref: margin.gm.channel_contribution.amount
  semantic_model: Growth_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Gross Margin Amount by channel for profitability contribution analysis.
    notes: ''
  governance:
    owner: Commercial BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Gross Margin Amount
    columns:
    - fact_sales.Gross Margin Amount
    - dim_channel.Channel
```
