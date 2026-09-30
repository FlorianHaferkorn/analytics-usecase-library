# Measure Dictionary - Efficiency

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: OEE %
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-011
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    logical: OEE % = [Availability %] * [Performance %] * [Quality %]
    aggregation_method: ratio
  documentation:
    description: 'Composite efficiency: Availability x Performance x Quality.'
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Availability %
    - Performance %
    - Quality %
    columns:
    - fact_ops.Planned Time Minutes
    - fact_ops.Run Time Minutes
    - fact_ops.Downtime Minutes
    - fact_ops.Output Units
    - fact_ops.Good Units
    - fact_ops.Standard Rate Units Per Minute

- measure_name: Total Process Cost Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Efficiency_SemanticModel
  category: Base
  expression:
    logical: Total Process Cost Amount = Total process cost in the selected context.
    aggregation_method: sum
  documentation:
    description: Total process cost in the selected context.
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    columns:
    - fact_cost.COGS Amount

- measure_name: Produced Units Qty
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Efficiency_SemanticModel
  category: Base
  expression:
    logical: Produced Units Qty = Total produced units in the selected context.
    aggregation_method: sum
  documentation:
    description: Total produced units in the selected context.
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    columns:
    - fact_output.Output Units

- measure_name: Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Efficiency_SemanticModel
  category: Base
  expression:
    logical: Net Sales Amount = SUM ( fact_sales[Net Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Net sales amount from finance for cross-domain ratios.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    columns:
    - fact_finance.Net Sales Amount

- measure_name: Availability %
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-016
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    logical: Availability % = (RunTime) / (PlannedTime)
    aggregation_method: ratio
  documentation:
    description: Available time / Planned time
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025

- measure_name: Performance %
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-002
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    logical: Performance % = (ActualOutput) / (TheoreticalOutput)
    aggregation_method: ratio
  documentation:
    description: Actual output / Theoretical maximum
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v1.0
    last_review: 04.11.2025

- measure_name: Quality %
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-003
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    logical: Quality % = (GoodUnits) / (TotalUnits)
    aggregation_method: ratio
  documentation:
    description: Good units / Total units
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v1.0
    last_review: 04.11.2025

- measure_name: Inventory Turnover
  is_kpi_measure: true
  kpi_id_ref: KPI-SCM-016
  category: KPI
  expression:
    logical: Inventory Turnover = COGS / Average Inventory
    aggregation_method: sum
  dependencies:
    columns:
    - fact_cogs[COGS Amount]
    - fact_inventory[Average Inventory Amount]
  governance:
    status: active
    owner: Supply Chain BI
    version: v1.0
    last_review: 04.11.2025
  semantic_model: Efficiency_SemanticModel
  documentation:
    description: COGS / Average Inventory
    notes: ''

- measure_name: Cash Conversion Cycle (Days)
  is_kpi_measure: true
  kpi_id_ref: KPI-FIN-006
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    logical: Cash Conversion Cycle (Days) = DSO + DIO - DPO.
    aggregation_method: ratio
  documentation:
    description: Aggregated cash conversion cycle derived from DSO, DIO, and DPO measures.
    notes: Cross-domain view; the canonical Working Capital definition is maintained in Measure_Dictionary_Liquidity.
  governance:
    owner: Finance BI
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 02_WorkingCapital

- measure_name: Forecast Error Qty
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Efficiency_SemanticModel
  category: Supporting
  expression:
    logical: Forecast Error Qty = Forecast Error Qty = Forecast Qty - Actual Demand Qty.
    aggregation_method: sum
  documentation:
    description: Forecast Error Qty = Forecast Qty - Actual Demand Qty.
    notes: Calculated at location_sku_day or sku_week; aggregated to sku_month.
  governance:
    owner: Supply Chain BI
    status: active
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    columns:
    - fact_forecast.Forecast Units
    - fact_sales.Sales Units

- measure_name: Under-Forecast Lost Demand Qty
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Efficiency_SemanticModel
  category: Supporting
  expression:
    logical: Under-Forecast Lost Demand Qty = [Forecast Error Qty]
    aggregation_method: sum
  documentation:
    description: Lost demand attributable to forecast under-coverage below threshold.
    notes: Aggregated to sku_month.
  governance:
    owner: Supply Chain BI
    status: active
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    measures:
    - Forecast Error Qty
    columns:
    - fact_stockout.Lost Demand Units

- measure_name: Under-Forecast Lost Demand Share %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Efficiency_SemanticModel
  category: Supporting
  expression:
    logical: Under-Forecast Lost Demand Share % = [Under-Forecast Lost Demand Qty]
    aggregation_method: ratio
  documentation:
    description: Under-Forecast Lost Demand Qty / Stockout Lost Demand Qty.
    notes: sku_month aggregated by Date, Org, Product.
  governance:
    owner: Supply Chain BI
    status: active
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    measures:
    - Under-Forecast Lost Demand Qty
    columns:
    - fact_stockout.Lost Demand Units

- measure_name: Service Impact %
  is_kpi_measure: true
  kpi_id_ref: KPI-SCM-012
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    logical: Service Impact % = [Under-Forecast Lost Demand Share %] / [Stockout Impact %]
    aggregation_method: ratio
  documentation:
    description: Service Impact % = Stockout Impact % x Under-Forecast Lost Demand Share %.
    notes: sku_month aggregated by Date, Org, Product.
  governance:
    owner: Supply Chain BI
    status: active
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    measures:
    - Under-Forecast Lost Demand Share %
    - Stockout Impact %
```


