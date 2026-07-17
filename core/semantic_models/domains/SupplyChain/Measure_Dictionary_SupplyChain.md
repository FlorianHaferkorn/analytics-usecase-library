# Measure Dictionary - SupplyChain

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

## Aggregation Method Conventions

All measures must declare an `aggregation_method` in their `expression` block. Conventions:

| Method | Use for |
|--------|---------|
| `sum` | Additive facts (units, costs, penalties, expedite costs) |
| `average` | Average inventory, coverage days — dimension-sensitive |
| `last_value` | Inventory balance at a point in time — not additive across time |
| `ratio` | Rate measures (OTIF %, Forecast Accuracy %, Stockout Rate %) — recompute from components |
| `count` | Order counts, shipment counts — additive |

**Rule:** DIO, Inventory Turnover, OTIF %, Forecast Accuracy %, and MAPE must never be averaged across periods. Always recompute from summed inventory/COGS/order components.

## Logical Expression Convention

`expression.logical` contains tool-agnostic business-logic pseudocode. Tool-specific DAX/SQL lives in `products/fabric/`.

Format: `MEASURE_NAME = <pseudocode using column references from supply_chain data contract>`

```yaml
- measure_name: Days in Inventory
  is_kpi_measure: true
  kpi_id_ref: inv.dio.days
  semantic_model: SupplyChain_SemanticModel
  display_folder: 01_Inventory
  category: KPI
  expression:
    aggregation_method: ratio
    logical: DIO = SUM(fact_inventory[Average Inventory Amount]) / (SUM(fact_cogs[COGS Amount]) / 365)
  documentation:
    description: Working capital efficiency via inventory days.
    notes: 'Grain: location_sku_month. Unit: days.

      Lineage: fact_inventory[Avg Inventory], fact_cogs[COGS].

      QA: COGS aligned to same period; DIVIDE guard for zero COGS/day.

      '
  dependencies:
    columns:
    - fact_inventory[Average Inventory Amount]
    - fact_cogs[COGS Amount]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Inventory Turnover
  is_kpi_measure: true
  kpi_id_ref: inv.turnover
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
    owner: Supply Chain Analytics
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31
  semantic_model: SupplyChain_SemanticModel
  display_folder: 01_Inventory
  documentation:
    description: 'Velocity of inventory: COGS / Avg Inventory.'
    notes: 'Grain: location_sku_month. Unit: x.

      Lineage: fact_inventory[Avg Inventory], fact_cogs[COGS].

      QA: Avg Inventory > 0; COGS completeness.

      '

- measure_name: Stockout Rate %
  is_kpi_measure: true
  kpi_id_ref: inv.stockout.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    logical: Stockout Rate % = Stockout Events / Total Demand Events.
    aggregation_method: ratio
  documentation:
    description: Service risk from stockout occurrences.
    notes: 'Grain: location_sku_day. Unit: %.

      Lineage: fact_stockout[Stockout Flag], demand events.

      QA: Demand denominator > 0; flag accuracy.

      '
  dependencies:
    columns:
    - fact_stockout[Stockout Flag]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: OTIF %
  is_kpi_measure: true
  kpi_id_ref: supply.otif.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    aggregation_method: ratio
    logical: OTIF = DIVIDE ( CALCULATE ( COUNTROWS ( fact_fulfillment ), fact_fulfillment[OTIF Flag] = TRUE ), COUNTROWS ( fact_fulfillment ) )
  documentation:
    description: On-Time In-Full orders share.
    notes: 'Grain: order. Unit: %.

      Lineage: fact_fulfillment[OTIF Flag].

      QA: One row per order; flag consistency.

      '
  dependencies:
    columns:
    - fact_fulfillment[OTIF Flag]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Obsolete Inventory %
  is_kpi_measure: true
  kpi_id_ref: inv.obsolete.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 01_Inventory
  category: KPI
  expression:
    logical: Obsolete Inventory % = Obsolete Inventory Value / Total Inventory Value.
    aggregation_method: ratio
  documentation:
    description: Share of obsolete stock vs total stock.
    notes: 'Grain: location_sku_month. Unit: %.

      Lineage: fact_inventory[Obsolete Stock], fact_inventory[Total Stock].

      QA: Total Stock > 0; valuation rules consistent.

      '
  dependencies:
    columns:
    - fact_inventory[Obsolete Stock]
    - fact_inventory[Total Stock]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Forecast Accuracy %
  is_kpi_measure: true
  kpi_id_ref: plan.forecast.accuracy.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    aggregation_method: ratio
    logical: Forecast Accuracy = 1 - SUM(ABS(fact_forecast[Forecast Units] - fact_sales[Actual Units])) / SUM(fact_sales[Actual Units])
  documentation:
    description: 'Planning quality: 1 - |Forecast - Actual| / Actual.'
    notes: 'Grain: sku_month. Unit: %.

      Lineage: fact_forecast[Forecast], fact_sales[Actual].

      QA: Actual > 0; consistent calendars; cap at [0;1] if needed.

      '
  dependencies:
    columns:
    - fact_forecast[Forecast]
    - fact_sales[Actual]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: MAPE %
  is_kpi_measure: true
  kpi_id_ref: plan.forecast.mape.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: MAPE % = Mean(|Forecast - Actual| / Actual).
    aggregation_method: ratio
  documentation:
    description: Mean absolute percentage error.
    notes: 'Grain: sku_month. Unit: %.

      Lineage: fact_forecast vs fact_sales.

      QA: Actual > 0; outlier handling documented.

      '
  dependencies:
    measures:
    - '[Absolute Error]'
    - '[Forecast Units]'
    - '[Actual Units]'
    columns:
    - fact_forecast[Forecast Units]
    - fact_sales[Actual Units]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Forecast Bias %
  is_kpi_measure: true
  kpi_id_ref: plan.forecast.bias.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: Forecast Bias % = (Forecast - Actual) / Actual.
    aggregation_method: ratio
  documentation:
    description: Alias for Bias % (TMDL display name). Forecast error direction (Forecast - Actual) / Actual.
    notes: Same as Bias %.
  dependencies:
    measures: []
    columns: []
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Forecast MAPE %
  is_kpi_measure: true
  kpi_id_ref: plan.forecast.mape.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: Forecast MAPE % = Mean(|Forecast - Actual| / Actual).
    aggregation_method: ratio
  documentation:
    description: Alias for MAPE % (TMDL display name).
    notes: Same as MAPE %.
  dependencies:
    measures: []
    columns: []
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Bias %
  is_kpi_measure: true
  kpi_id_ref: plan.forecast.bias.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: Bias % = (Forecast - Actual) / Actual.
    aggregation_method: ratio
  documentation:
    description: Forecast error direction (Forecast - Actual) / Actual.
    notes: 'Grain: sku_month. Unit: %.

      Lineage: fact_forecast vs fact_sales.

      QA: Bias band defined; Actual > 0; DIVIDE guard.

      '
  dependencies:
    columns:
    - fact_forecast[Forecast]
    - fact_sales[Actual]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Service Impact %
  is_kpi_measure: true
  kpi_id_ref: plan.forecast.service_impact.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: Service Impact % = Service Impact % = Stockout Impact % x (Under-Forecast Lost Demand / Total Lost Demand). Under-forecast is defined as a negative forecast error below a configurable threshold; all inputs are unit-based (qty), not revenue.
    aggregation_method: ratio
  documentation:
    description: Portion of service misses attributable to forecast error.
    notes: 'Grain: sku_month. Unit: %.

      Lineage: forecast error, OTIF/stockout links.

      QA: Align with OTIF and stockout measures; guard divide-by-zero.

      '
  dependencies:
    measures:
    - '[Forecast Units]'
    - '[Actual Units]'
    - '[Lost Demand Units]'
    - '[Demand Units]'
    columns:
    - fact_forecast[Forecast Units]
    - fact_sales[Actual Units]
    - fact_stockout[Lost Demand Units]
    - fact_stockout[Demand Units]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Re-Plan Count
  is_kpi_measure: true
  kpi_id_ref: plan.replan.count
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: Re-Plan Count = Total replan events logged in planning system.
    aggregation_method: count
  documentation:
    description: Number of re-plans within period.
    notes: 'Grain: month. Unit: count.

      Lineage: planning system logs.

      QA: Consistent definition of re-plan event.

      '
  dependencies:
    columns:
    - fact_planning[Replan Count]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: On-Time %
  is_kpi_measure: true
  kpi_id_ref: supply.on_time.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    logical: On-Time % = On-Time Deliveries / Total Deliveries.
    aggregation_method: ratio
  documentation:
    description: On-time deliveries share.
    notes: 'Grain: shipment. Unit: %.

      Lineage: fact_fulfillment[On-Time Flag].

      QA: One row per shipment; flag consistency.

      '
  dependencies:
    columns:
    - fact_fulfillment[On-Time Flag]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: In-Full %
  is_kpi_measure: true
  kpi_id_ref: supply.in_full.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    logical: In-Full % = In-Full Deliveries / Total Deliveries.
    aggregation_method: ratio
  documentation:
    description: In-full deliveries share.
    notes: 'Grain: shipment. Unit: %.

      Lineage: fact_fulfillment[In-Full Flag].

      QA: One row per shipment; flag consistency.

      '
  dependencies:
    columns:
    - fact_fulfillment[In-Full Flag]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Stockout Impact %
  is_kpi_measure: true
  kpi_id_ref: supply.stockout_impact.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    logical: Stockout Impact % = Lost Demand Qty / Total Demand Qty.
    aggregation_method: ratio
  documentation:
    description: Lost demand share due to stockout.
    notes: 'Grain: location_sku_day. Unit: %.

      Lineage: fact_stockout[Lost Demand], fact_stockout[Demand].

      QA: Demand > 0; align with service metrics.

      '
  dependencies:
    columns:
    - fact_stockout[Lost Demand]
    - fact_stockout[Demand]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Penalty Amount
  is_kpi_measure: true
  kpi_id_ref: supply.penalty.amount
  semantic_model: SupplyChain_SemanticModel
  display_folder: 04_Cost
  category: KPI
  expression:
    logical: Penalty Amount = Sum of penalty charges incurred in the period.
    aggregation_method: sum
  documentation:
    description: Penalties incurred for service misses.
    notes: 'Grain: order. Unit: EUR.

      Lineage: fact_fulfillment[Penalty Amount].

      QA: One row per order; completeness of penalty capture.

      '
  dependencies:
    columns:
    - fact_fulfillment[Penalty Amount]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Expedite Cost Amount
  is_kpi_measure: true
  kpi_id_ref: supply.expedite.amount
  semantic_model: SupplyChain_SemanticModel
  display_folder: 04_Cost
  category: KPI
  expression:
    logical: Expedite Cost Amount = Sum of expedite fees and premium freight charges.
    aggregation_method: sum
  documentation:
    description: Additional cost for expedited shipping.
    notes: 'Grain: shipment. Unit: EUR.

      Lineage: fact_fulfillment[Expedite Cost].

      QA: Ensure capture of incremental costs only.

      '
  dependencies:
    columns:
    - fact_fulfillment[Expedite Cost]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Avg Inventory Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 01_Inventory
  category: Base
  expression:
    logical: Avg Inventory Amount = SUM(fact_inventory[Average Inventory Amount])
    aggregation_method: sum
  documentation:
    description: Average inventory value used as base for DIO and turnover.
    notes: 'Source: fact_inventory[Average Inventory Amount].'
  dependencies:
    columns:
    - fact_inventory[Average Inventory Amount]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: COGS Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 01_Inventory
  category: Base
  expression:
    logical: COGS Amount = SUM(fact_cogs[COGS Amount])
    aggregation_method: sum
  documentation:
    description: COGS base for inventory turnover and DIO.
    notes: 'Source: fact_cogs[COGS Amount].'
  dependencies:
    columns:
    - fact_cogs[COGS Amount]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: On-Time In-Full Orders
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: On-Time In-Full Orders = SUM(fact_fulfillment[OTIF Flag])
    aggregation_method: sum
  documentation:
    description: OTIF order quantity used as numerator for OTIF %.
    notes: 'Source: fact_fulfillment[OTIF Flag], [Order Qty].'
  dependencies:
    columns:
    - fact_fulfillment[OTIF Flag]
    - fact_fulfillment[Order Qty]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: OTIF Orders
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: OTIF Orders = SUM(fact_fulfillment[OTIF Flag])
    aggregation_method: sum
  documentation:
    description: OTIF order quantity used for OTIF %.
    notes: Same base as On-Time In-Full Orders.
  dependencies:
    columns:
    - fact_fulfillment[OTIF Flag]
    - fact_fulfillment[Order Qty]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Total Orders
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: Total Orders = SUM(fact_fulfillment[Order Qty])
    aggregation_method: sum
  documentation:
    description: Total order quantity used as denominator for OTIF, on-time, and in-full.
    notes: 'Source: fact_fulfillment[Order Qty].'
  dependencies:
    columns:
    - fact_fulfillment[Order Qty]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: On-Time Deliveries
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: On-Time Deliveries = SUM(fact_fulfillment[On-Time Flag])
    aggregation_method: sum
  documentation:
    description: On-time delivery quantity used as numerator for On-Time %.
    notes: 'Source: fact_fulfillment[On-Time Flag], [Order Qty].'
  dependencies:
    columns:
    - fact_fulfillment[On-Time Flag]
    - fact_fulfillment[Order Qty]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: In-Full Deliveries
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: In-Full Deliveries = SUM(fact_fulfillment[In-Full Flag])
    aggregation_method: sum
  documentation:
    description: In-full delivery quantity used as numerator for In-Full %.
    notes: 'Source: fact_fulfillment[In-Full Flag], [Order Qty].'
  dependencies:
    columns:
    - fact_fulfillment[In-Full Flag]
    - fact_fulfillment[Order Qty]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Demand Occurrences
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: Demand Occurrences = SUM(fact_stockout[Demand Occurrences])
    aggregation_method: sum
  documentation:
    description: Demand occurrences used as denominator for stockout rate.
    notes: 'Source: fact_stockout[Demand Occurrences].'
  dependencies:
    columns:
    - fact_stockout[Demand Occurrences]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Stockout Count
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: Stockout Count = SUM(fact_stockout[Stockout Flag])
    aggregation_method: count
  documentation:
    description: Stockout occurrences used as numerator for stockout rate.
    notes: 'Source: fact_stockout[Stockout Flag], [Demand Occurrences].'
  dependencies:
    columns:
    - fact_stockout[Stockout Flag]
    - fact_stockout[Demand Occurrences]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Lost Demand Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: Lost Demand Units = SUM(fact_stockout[Lost Demand Units])
    aggregation_method: sum
  documentation:
    description: Lost demand units used for stockout impact.
    notes: 'Source: fact_stockout[Lost Demand Units].'
  dependencies:
    columns:
    - fact_stockout[Lost Demand Units]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Demand Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: Base
  expression:
    logical: Demand Units = SUM(fact_stockout[Demand Units])
    aggregation_method: sum
  documentation:
    description: Demand units used as denominator for stockout impact.
    notes: 'Source: fact_stockout[Demand Units].'
  dependencies:
    columns:
    - fact_stockout[Demand Units]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Forecast Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: Base
  expression:
    logical: Forecast Units = SUM(fact_forecast[Forecast Units])
    aggregation_method: sum
  documentation:
    description: Forecast quantity base for planning KPIs.
    notes: 'Source: fact_forecast[Forecast Units].'
  dependencies:
    columns:
    - fact_forecast[Forecast Units]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Actual Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: Base
  expression:
    logical: Actual Units = SUM(fact_sales[Actual Units])
    aggregation_method: sum
  documentation:
    description: Actual quantity base for planning KPIs.
    notes: 'Source: fact_sales[Actual Units].'
  dependencies:
    columns:
    - fact_sales[Actual Units]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Absolute Error
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: Base
  expression:
    logical: Absolute Error = ABS ( [Forecast Units] - [Actual Units] )
    aggregation_method: sum
  documentation:
    description: Absolute forecast error used for accuracy and MAPE.
    notes: Derived from Forecast Units and Actual Units.
  dependencies:
    measures:
    - '[Forecast Units]'
    - '[Actual Units]'
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Forecast Error Qty
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: Base
  expression:
    logical: Forecast Error Qty = [Forecast Units] - [Actual Units]
    aggregation_method: sum
  documentation:
    description: Forecast units minus actual units.
    notes: Derived from Forecast Units and Actual Units.
  dependencies:
    measures:
    - '[Forecast Units]'
    - '[Actual Units]'
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Under-Forecast Lost Demand Qty
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: Base
  expression:
    logical: Under-Forecast Lost Demand Qty = SUM(fact_stockout[Lost Demand Units])
    aggregation_method: sum
  documentation:
    description: Lost demand units attributable to under-forecasting beyond threshold.
    notes: Requires Lost Demand Units and forecast error logic.
  dependencies:
    columns:
    - fact_stockout[Lost Demand Units]
    measures:
    - '[Forecast Error Qty]'
    - '[Actual Units]'
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Under-Forecast Lost Demand Share %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: Base
  expression:
    logical: Under-Forecast Lost Demand Share % = [[Under-Forecast Lost Demand Qty]] / [[Stockout Lost Demand Qty]]
    aggregation_method: ratio
  documentation:
    description: Share of stockout lost demand attributable to under-forecasting.
    notes: Derived from Under-Forecast Lost Demand Qty and Stockout Lost Demand Qty.
  dependencies:
    measures:
    - '[Under-Forecast Lost Demand Qty]'
    - '[Stockout Lost Demand Qty]'
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Order Lines Count
  is_kpi_measure: true
  kpi_id_ref: order.lines
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    logical: Order Lines Count = Count of order line items.
    aggregation_method: count
  documentation:
    description: Count of order line items.
    notes: 'Grain: order_line. Unit: count.

      Lineage: fact_order_lines[Order Line ID].

      QA: De-duplicate merged or split lines.

      '
  dependencies:
    columns:
    - fact_order_lines[Order Line ID]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Plans Count
  is_kpi_measure: true
  kpi_id_ref: plans.count
  semantic_model: SupplyChain_SemanticModel
  display_folder: 03_Forecast
  category: KPI
  expression:
    logical: Plans Count = Count of plan records or plan versions.
    aggregation_method: count
  documentation:
    description: Count of plan records or plan versions.
    notes: 'Grain: plan_version. Unit: count.

      Lineage: fact_plan[Plan ID].

      QA: Distinguish baseline vs scenario plans.

      '
  dependencies:
    columns:
    - fact_plan[Plan ID]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Shipments Count
  is_kpi_measure: true
  kpi_id_ref: shipments.count
  semantic_model: SupplyChain_SemanticModel
  display_folder: 02_Service
  category: KPI
  expression:
    logical: Shipments Count = Count of shipment records.
    aggregation_method: count
  documentation:
    description: Count of shipments executed.
    notes: 'Grain: shipment. Unit: count.

      Lineage: fact_shipment[Shipment ID].

      QA: Exclude canceled shipments.

      '
  dependencies:
    columns:
    - fact_shipment[Shipment ID]
  governance:
    owner: Supply Chain Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: OTIF % (XD)
  is_kpi_measure: true
  kpi_id_ref: supply.otif.pct
  semantic_model: SupplyChain_SemanticModel
  display_folder: 01_Service_Level
  category: KPI
  expression:
    logical: OTIF % (XD) = VAR OTIFFulfillments = CALCULATE ( COUNTROWS ( fact_fulfillment ), fact_fulfillment[OTIF Flag] = TRUE() ) VAR TotalFulfillments = COUNTROWS ( fact_fulfillment ) RETURN DIVIDE ( OTIFFulfillments, TotalFulfillments )
    aggregation_method: custom
  documentation:
    description: Measures share of orders delivered on time and in full — Supply Chain cross-domain view.
    notes: 'Grain: order_day. Unit: %. Lineage: fact_fulfillment[OTIF Flag].'
  dependencies:
    columns:
    - fact_fulfillment[OTIF Flag]
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Actions Executed Count (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.actions_executed.count
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Actions Executed Count (XD) = COUNTROWS ( FILTER ( fact_action_outcome, NOT ISBLANK ( fact_action_outcome[outcome_status] ) ) )
    aggregation_method: count
  documentation:
    notes: 'Grain: month. Unit: count. Lineage: fact_action_outcome[outcome_status].'
    description: Number of action codes with a recorded outcome — Supply Chain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Supply Chain BI
  semantic_model: SupplyChain_SemanticModel

- measure_name: Action Outcome Rate % (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_outcome_rate.pct
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Outcome Rate % (XD) = DIVIDE ( CALCULATE ( COUNTROWS ( fact_action_outcome ), fact_action_outcome[outcome_status] = "achieved" ), COUNTROWS ( fact_action_outcome ) )
    aggregation_method: custom
  documentation:
    notes: 'Grain: month. Unit: %. Lineage: fact_action_outcome[outcome_status].'
    description: Percentage of executed actions with confirmed achieved outcome — Supply Chain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Supply Chain BI
  semantic_model: SupplyChain_SemanticModel

- measure_name: Avg Time-to-Outcome Days (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.avg_time_to_outcome.days
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Avg Time-to-Outcome Days (XD) = AVERAGEX ( fact_action_outcome, fact_action_outcome[days_to_outcome] )
    aggregation_method: average
  documentation:
    notes: 'Grain: month. Unit: days. Lineage: fact_action_outcome[days_to_outcome].'
    description: Average days between action execution and outcome confirmation — Supply Chain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[days_to_outcome]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Supply Chain BI
  semantic_model: SupplyChain_SemanticModel

- measure_name: Action ROI % (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_roi.pct
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action ROI % (XD) = DIVIDE ( SUMX ( fact_action_outcome, fact_action_outcome[impact_value] ), SUMX ( fact_action_outcome, fact_action_outcome[cost_to_execute] ) ) - 1
    aggregation_method: custom
  documentation:
    notes: 'Grain: month. Unit: %. Lineage: fact_action_outcome[impact_value], fact_action_outcome[cost_to_execute].'
    description: Average ROI of executed actions — Supply Chain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[cost_to_execute]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Supply Chain BI
  semantic_model: SupplyChain_SemanticModel

- measure_name: Action Effectiveness Delta (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_effectiveness_delta.amount
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Effectiveness Delta (XD) = AVERAGEX ( FILTER ( fact_action_outcome, fact_action_outcome[outcome_status] = "achieved" ), fact_action_outcome[impact_value] )
    aggregation_method: average
  documentation:
    notes: 'Grain: month. Unit: EUR. Lineage: fact_action_outcome[impact_value], fact_action_outcome[outcome_status].'
    description: Average EUR impact per achieved action execution — Supply Chain cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Supply Chain BI
  semantic_model: SupplyChain_SemanticModel
```

