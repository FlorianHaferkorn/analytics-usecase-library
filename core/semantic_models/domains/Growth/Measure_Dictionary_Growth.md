# Measure Dictionary - Growth

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Growth_SemanticModel
  display_folder: 01_Growth
  category: KPI
  expression:
    logical: Net Sales Amount = Sum of all invoice line amounts net of VAT and returns.
    aggregation_method: sum
  documentation:
    description: Sum of net sales after discounts.
    notes: 'Grain: invoice_line / month. Unit: EUR.

      Lineage: fact_sales[Net Sales Amount].

      QA: Excludes VAT/returns; currency conversion upstream.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: Growth Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Net Sales Delta % vs LY
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.delta_pct.ly
  semantic_model: Growth_SemanticModel
  display_folder: 01_Growth
  category: KPI
  expression:
    logical: Net Sales Delta % vs LY = (Net Sales - LY) / LY
    aggregation_method: ratio
  documentation:
    description: Relative growth vs last year.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Net Sales Amount LY].

      QA: DIVIDE guard; LY alignment.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Net Sales Amount LY]
  governance:
    owner: Growth Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Price Realization %
  is_kpi_measure: true
  kpi_id_ref: sales.price.realization_pct
  semantic_model: Growth_SemanticModel
  display_folder: 03_Pricing
  category: KPI
  expression:
    logical: Price Realization % = Net Price Amount / List Price Amount.
    aggregation_method: ratio
  documentation:
    description: Net Price / List Price.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_sales[Net Price Amount], fact_sales[List Price Amount].

      QA: List price excludes taxes; DIVIDE guard.

      '
  dependencies:
    columns:
    - fact_sales[Net Price Amount]
    - fact_sales[List Price Amount]
  governance:
    owner: Growth Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Forecast Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Growth_SemanticModel
  display_folder: 05_Forecast
  category: Base
  expression:
    logical: Forecast Net Sales Amount = SUM(fact_forecast[Net Sales Amount])
    aggregation_method: sum
  documentation:
    description: Forecasted net sales amount.
    notes: 'Grain: sku_month or org_month. Unit: EUR.

      Lineage: fact_forecast[Net Sales Amount].

      QA: Versioned forecast; calendar alignment.

      '
  dependencies:
    columns:
    - fact_forecast[Net Sales Amount]
  governance:
    owner: Growth Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Sales Units
  is_kpi_measure: true
  kpi_id_ref: sales.units
  semantic_model: Growth_SemanticModel
  display_folder: 01_Growth
  category: KPI
  expression:
    logical: Sales Units = Sum of sold units across transactions.
    aggregation_method: sum
  documentation:
    description: Total units sold in the period.
    notes: 'Grain: invoice_line. Unit: units.

      Lineage: fact_sales[Sales Units].

      QA: Exclude returns when needed; units aligned to product master.

      '
  dependencies:
    columns:
    - fact_sales[Sales Units]
  governance:
    owner: Growth Analytics
    status: active
    version: v0.1
    last_review: TBD
```

