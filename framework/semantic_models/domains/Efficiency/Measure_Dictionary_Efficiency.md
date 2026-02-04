# Measure Dictionary - Efficiency

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: OEE %
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '[Availability %] * [Performance %] * [Quality %]'
    formatString: 0.0 %
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
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: Base
  expression:
    dax: SUM ( fact_cost[COGS Amount] )
    formatString: 'EUR #,0.00'
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
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: Base
  expression:
    dax: SUM ( fact_output[Output Units] )
    formatString: '#,0'
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
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: Base
  expression:
    dax: "SUM ( fact_finance[Net Sales Amount] )"
    formatString: 'EUR #,0.00'
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
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "DIVIDE ( SUM ( fact_ops[Planned Time Minutes] ) - SUM ( fact_ops[Downtime Minutes] ), SUM ( fact_ops[Planned Time Minutes] ) )"
    formatString: 0.0 %
  documentation:
    description: Available time / Planned time
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025

- measure_name: Performance %
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "DIVIDE ( SUM ( fact_ops[Output Units] ), SUM ( fact_ops[Run Time Minutes] ) * AVERAGE ( fact_ops[Standard Rate Units Per Minute] ) )"
    formatString: 0.0 %
  documentation:
    description: Actual output / Theoretical maximum
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v1.0
    last_review: 04.11.2025

- measure_name: Quality %
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "DIVIDE ( SUM ( fact_ops[Good Units] ), SUM ( fact_ops[Output Units] ) )"
    formatString: 0.0 %
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
  kpi_id_ref: ops.inventory.turnover
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "DIVIDE ( SUM ( fact_cogs[COGS Amount] ), SUM ( fact_inventory[Average Inventory Amount] ) )"
    formatString: '0.00'
  documentation:
    description: COGS / Average Inventory
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025

- measure_name: OTIF %
  is_kpi_measure: true
  kpi_id_ref: ops.otif.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "DIVIDE ( SUM ( fact_fulfillment[OTIF Flag] ), COUNTROWS ( fact_fulfillment ) )"
    formatString: 0.0 %
  documentation:
    description: On-Time In-Full deliveries / Total Deliveries
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    measures:
    - OTIF Deliveries Count
    - Total Deliveries Count

- measure_name: Cash Conversion Cycle (Days)
  is_kpi_measure: true
  kpi_id_ref: ops.working_capital.ccc.days
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '[DSO (Days)] + [DIO (Days)] - [DPO (Days)]'
    formatString: '0'
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
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: Supporting
  expression:
    dax: "SUM ( fact_forecast[Forecast Units] ) - SUM ( fact_sales[Sales Units] )"
    formatString: '0'
  documentation:
    description: Forecast Error Qty = Forecast Qty - Actual Demand Qty.
    notes: Calculated at location_sku_day or sku_week; aggregated to sku_month.
  governance:
    owner: Supply Chain BI
    status: draft
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    columns:
    - fact_forecast.Forecast Units
    - fact_sales.Sales Units

- measure_name: Under-Forecast Lost Demand Qty
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: Supporting
  expression:
    dax: "VAR Forecast = SUM ( fact_forecast[Forecast Units] ); VAR Actual = SUM ( fact_sales[Sales Units] ); VAR Lost = SUM ( fact_stockout[Lost Demand Units] ); RETURN IF ( Forecast < Actual, MIN ( Lost, Actual - Forecast ), 0 )"
    formatString: '0'
  documentation:
    description: Lost demand attributable to forecast under-coverage below threshold.
    notes: Aggregated to sku_month.
  governance:
    owner: Supply Chain BI
    status: draft
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    measures:
    - Forecast Error Qty
    columns:
    - fact_stockout.Lost Demand Units

- measure_name: Under-Forecast Lost Demand Share %
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: Supporting
  expression:
    dax: "DIVIDE ( [Under-Forecast Lost Demand Qty], SUM ( fact_stockout[Lost Demand Units] ) )"
    formatString: 0.0 %
  documentation:
    description: Under-Forecast Lost Demand Qty / Stockout Lost Demand Qty.
    notes: sku_month aggregated by Date, Org, Product.
  governance:
    owner: Supply Chain BI
    status: draft
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    measures:
    - Under-Forecast Lost Demand Qty
    columns:
    - fact_stockout.Lost Demand Units

- measure_name: Service Impact %
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "[Stockout Impact %] * [Under-Forecast Lost Demand Share %]"
    formatString: 0.0 %
  documentation:
    description: Service Impact % = Stockout Impact % x Under-Forecast Lost Demand Share %.
    notes: sku_month aggregated by Date, Org, Product.
  governance:
    owner: Supply Chain BI
    status: draft
    version: v0.1
  display_folder: 08_SCM_Service
  dependencies:
    measures:
    - Under-Forecast Lost Demand Share %
    - Stockout Impact %
```


