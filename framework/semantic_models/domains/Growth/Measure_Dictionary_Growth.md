# Measure Dictionary - Growth

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
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


- measure_name: "Sales Units"
  is_kpi_measure: true
  kpi_id_ref: "sales.units"
  semantic_model: "Growth_SemanticModel"
  display_folder: "01_Growth"
  category: "KPI"
  expression:
    dax: "SUM ( fact_sales[Sales Units] )"
    formatString: "#,0"
  documentation:
    description: "Total units sold in the period."
    notes: |
      Grain: invoice_line. Unit: units.
      Lineage: fact_sales[Sales Units].
      QA: Exclude returns when needed; units aligned to product master.
  dependencies:
    columns:
      - "fact_sales[Sales Units]"
  governance:
    owner: "Growth Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"
```

