# Measure Dictionary - Efficiency

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: OEE %
  is_kpi_measure: true
  kpi_id_ref: ops.oee.pct
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
    - fact_mes.Availability
    - fact_mes.Performance
    - fact_mes.Quality
- measure_name: Process Cost per Unit
  is_kpi_measure: true
  kpi_id_ref: ops.process.cost_per_unit.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Total Process Cost Amount],[Produced Units Qty])
    formatString: 'EUR #,0.00'
  documentation:
    description: Average process cost per produced unit.
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - ops.total_process_cost.amount
    - ops.produced_units.qty
    columns:
    - fact_costs.TotalProcessCost
    - fact_production.ProducedUnits
- measure_name: Inventory Days
  is_kpi_measure: true
  kpi_id_ref: ops.inventory.days
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Average Inventory divided by Daily COGS (Days of Inventory Outstanding).
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Capacity Utilization %
  is_kpi_measure: true
  kpi_id_ref: ops.capacity.utilization.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Capacity utilization percentage based on planned load and available hours.
    notes: ''
  governance:
    owner: Operations BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 02_Capacity
  dependencies:
    columns:
    - fact_capacity.AvailableHours
    - fact_capacity.PlannedLoadHours
- measure_name: Total Demand Qty
  is_kpi_measure: true
  kpi_id_ref: ops.demand.total.qty
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Total requested units (orders + forecast)
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Unfulfilled Demand Qty
  is_kpi_measure: true
  kpi_id_ref: ops.demand.unfulfilled.qty
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Requested units not delivered
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Availability %
  is_kpi_measure: true
  kpi_id_ref: ops.availability.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
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
  is_kpi_measure: true
  kpi_id_ref: ops.performance.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
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
  is_kpi_measure: true
  kpi_id_ref: ops.quality.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Good units / Total units
    notes: ''
  governance:
    owner: Manufacturing BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Downtime Hours
  is_kpi_measure: true
  kpi_id_ref: ops.downtime.hours
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0.00'
  documentation:
    description: Sum of downtime hours
    notes: ''
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Planned Hours
  is_kpi_measure: true
  kpi_id_ref: ops.planned.hours
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0.00'
  documentation:
    description: Sum of planned production hours
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Stock-Out Rate %
  is_kpi_measure: true
  kpi_id_ref: ops.stockout.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Unfulfilled Demand / Total Demand
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    measures:
    - Unfulfilled Demand Qty
    - Total Demand Qty
- measure_name: Inventory Turnover
  is_kpi_measure: true
  kpi_id_ref: ops.inventory.turnover
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
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
    dax: '// TODO: add expression'
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
- measure_name: PPV %
  is_kpi_measure: true
  kpi_id_ref: ops.ppv.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: (Actual Price - Contract Price) / Contract Price
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    measures:
    - Actual Purchase Price Amount
    - Contract Purchase Price Amount
- measure_name: PPV Amount
  is_kpi_measure: true
  kpi_id_ref: ops.ppv.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0.00'
  documentation:
    description: (Actual Price - Contract Price) x Quantity
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    measures:
    - Actual Purchase Price Amount
    - Contract Purchase Price Amount
    - Purchase Quantity
- measure_name: Contract Compliance %
  is_kpi_measure: true
  kpi_id_ref: ops.contract.compliance.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Purchases at agreed price / Total purchases
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Replenishment Adherence %
  is_kpi_measure: true
  kpi_id_ref: ops.replenishment.adherence.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Actual Orders / Target Orders (on time/quantity)
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Order Accuracy %
  is_kpi_measure: true
  kpi_id_ref: ops.order_accuracy.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Orders fulfilled correctly / Total Orders
    notes: ''
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    measures:
    - Correct Orders Count
    - Total Orders Count
- measure_name: Machine Downtime %
  is_kpi_measure: true
  kpi_id_ref: ops.machine_downtime.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Downtime Hours],[Planned Hours])
    formatString: 0.0 %
  documentation:
    description: Downtime hours divided by planned production hours for the selected slice.
    notes: ''
  governance:
    owner: Operations Data Team
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Downtime Hours
    - Planned Hours
    columns:
    - fact_production.DowntimeHours
    - fact_production.PlannedHours
- measure_name: DSO (Days)
  is_kpi_measure: true
  kpi_id_ref: ops.working_capital.dso.days
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Average AR Amount],[Net Sales Amount]) * [Days in Period]
    formatString: '0'
  documentation:
    description: Days Sales Outstanding derived from AR balance and revenue.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  display_folder: 02_WorkingCapital
- measure_name: DIO (Days)
  is_kpi_measure: true
  kpi_id_ref: ops.working_capital.dio.days
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Average Inventory Amount],[COGS Amount]) * [Days in Period]
    formatString: '0'
  documentation:
    description: Days Inventory Outstanding derived from inventory balance and COGS.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  display_folder: 02_WorkingCapital
- measure_name: DPO (Days)
  is_kpi_measure: true
  kpi_id_ref: ops.working_capital.dpo.days
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Average AP Amount],[COGS Amount]) * [Days in Period]
    formatString: '0'
  documentation:
    description: Days Payables Outstanding derived from AP balances and cost of goods sold.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  display_folder: 02_WorkingCapital
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
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 02_WorkingCapital
- measure_name: Delta CCC (Days)
  is_kpi_measure: true
  kpi_id_ref: ops.working_capital.ccc.delta_days
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Variance of CCC in days versus a baseline.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.1
    last_review: 11.11.2025
  display_folder: 02_WorkingCapital
- measure_name: Total Orders Count
  is_kpi_measure: true
  kpi_id_ref: ops.orders.total.count
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Total number of orders in period
    notes: ''
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Correct Orders Count
  is_kpi_measure: true
  kpi_id_ref: ops.orders.correct.count
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Orders fulfilled correctly
    notes: ''
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Total Deliveries Count
  is_kpi_measure: true
  kpi_id_ref: ops.deliveries.total.count
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Total deliveries in period
    notes: ''
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: OTIF Deliveries Count
  is_kpi_measure: true
  kpi_id_ref: ops.deliveries.otif.count
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Deliveries on-time and in-full
    notes: ''
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Purchases at Contract Amount
  is_kpi_measure: true
  kpi_id_ref: ops.purchases.at_contract.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Purchases at contracted price
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Total Purchases Amount
  is_kpi_measure: true
  kpi_id_ref: ops.purchases.total.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Total purchase spend
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Actual Purchase Price Amount
  is_kpi_measure: true
  kpi_id_ref: ops.purchase.price.actual.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.0000'
  documentation:
    description: Actual paid unit price
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Contract Purchase Price Amount
  is_kpi_measure: true
  kpi_id_ref: ops.purchase.price.contract.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.0000'
  documentation:
    description: Contracted unit price
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Purchase Quantity
  is_kpi_measure: true
  kpi_id_ref: ops.purchase.units.qty
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Purchased units
    notes: ''
  governance:
    owner: Procurement BI
    status: active
    version: v1.0
    last_review: 21.11.2025
- measure_name: Logistics Cost Ratio %
  is_kpi_measure: true
  kpi_id_ref: ops.logistics.cost_ratio.pct
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Logistics cost as % of Net Sales or shipped value.
    notes: ''
  governance:
    owner: Operations BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 05_Logistics
  dependencies:
    columns:
    - fact_logistics.CostAmount
    - fact_sales.Net Sales Amount
- measure_name: Logistics Cost per Unit
  is_kpi_measure: true
  kpi_id_ref: ops.logistics.cost_per_unit.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.000'
  documentation:
    description: Average logistics cost per shipped unit.
    notes: ''
  governance:
    owner: Operations BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 05_Logistics
  dependencies:
    columns:
    - fact_logistics.CostAmount
    - fact_logistics.UnitsQty
- measure_name: Warehouse Lines per Hour
  is_kpi_measure: true
  kpi_id_ref: ops.warehouse.lines_per_hour
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0.0'
  documentation:
    description: Average number of order lines processed per productive hour.
    notes: ''
  governance:
    owner: Operations BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 06_Warehouse
  dependencies:
    columns:
    - fact_warehouse.OrderLinesProcessed
    - fact_warehouse.ProductiveHours
- measure_name: Picks per Hour
  is_kpi_measure: true
  kpi_id_ref: ops.warehouse.picks_per_hour
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0.0'
  documentation:
    description: Average number of picks carried out per productive hour.
    notes: ''
  governance:
    owner: Operations BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 06_Warehouse
  dependencies:
    columns:
    - fact_warehouse.PicksCount
    - fact_warehouse.PickingHours
- measure_name: Warehouse Cost per Line
  is_kpi_measure: true
  kpi_id_ref: ops.warehouse.cost_per_line.amount
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.000'
  documentation:
    description: Average warehouse operating cost per processed order line.
    notes: ''
  governance:
    owner: Operations BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 06_Warehouse
  dependencies:
    columns:
    - fact_warehouse.CostAmount
    - fact_warehouse.OrderLinesProcessed
```
