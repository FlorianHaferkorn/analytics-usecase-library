# Measure Dictionary - SupplyChain

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Days in Inventory"
  is_kpi_measure: true
  kpi_id_ref: "inv.dio.days"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "KPI"
  expression:
    dax: |
      VAR AvgInv = [Avg Inventory Amount]
      VAR CogsPerDay =
          DIVIDE (
              [COGS Amount],
              365
          )
      RETURN DIVIDE ( AvgInv, CogsPerDay )
    formatString: "0 days"
  documentation:
    description: "Working capital efficiency via inventory days."
    notes: |
      Grain: location_sku_month. Unit: days.
      Lineage: fact_inventory[Avg Inventory], fact_cogs[COGS].
      QA: COGS aligned to same period; DIVIDE guard for zero COGS/day.
  dependencies:
    columns:
      - "fact_inventory[Average Inventory Amount]"
      - "fact_cogs[COGS Amount]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Inventory Turnover"
  is_kpi_measure: true
  kpi_id_ref: "inv.turnover"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "KPI"
  expression:
    dax: |
      VAR AvgInv = [Avg Inventory Amount]
      VAR Cogs   = [COGS Amount]
      RETURN DIVIDE ( Cogs, AvgInv )
    formatString: "0.0"
  documentation:
    description: "Velocity of inventory: COGS / Avg Inventory."
    notes: |
      Grain: location_sku_month. Unit: x.
      Lineage: fact_inventory[Avg Inventory], fact_cogs[COGS].
      QA: Avg Inventory > 0; COGS completeness.
  dependencies:
    columns:
      - "fact_inventory[Average Inventory Amount]"
      - "fact_cogs[COGS Amount]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Stockout Rate %"
  is_kpi_measure: true
  kpi_id_ref: "inv.stockout.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: |
      VAR StockoutEvents = SUM ( fact_stockout[Stockout Flag] )
      VAR DemandEvents   = COUNTROWS ( fact_stockout )
      RETURN DIVIDE ( StockoutEvents, DemandEvents )
    formatString: "0.0%"
  documentation:
    description: "Service risk from stockout occurrences."
    notes: |
      Grain: location_sku_day. Unit: %.
      Lineage: fact_stockout[Stockout Flag], demand events.
      QA: Demand denominator > 0; flag accuracy.
  dependencies:
    columns:
      - "fact_stockout[Stockout Flag]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "OTIF %"
  is_kpi_measure: true
  kpi_id_ref: "supply.otif.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Orders = COUNTROWS ( fact_fulfillment )
      VAR Otif   = SUM ( fact_fulfillment[OTIF Flag] )
      RETURN DIVIDE ( Otif, Orders )
    formatString: "0.0%"
  documentation:
    description: "On-Time In-Full orders share."
    notes: |
      Grain: order. Unit: %.
      Lineage: fact_fulfillment[OTIF Flag].
      QA: One row per order; flag consistency.
  dependencies:
    columns:
      - "fact_fulfillment[OTIF Flag]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Obsolete Inventory %"
  is_kpi_measure: true
  kpi_id_ref: "inv.obsolete.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "KPI"
  expression:
    dax: |
      DIVIDE (
        SUM ( fact_inventory[Obsolete Stock] ),
        SUM ( fact_inventory[Total Stock] )
      )
    formatString: "0.0%"
  documentation:
    description: "Share of obsolete stock vs total stock."
    notes: |
      Grain: location_sku_month. Unit: %.
      Lineage: fact_inventory[Obsolete Stock], fact_inventory[Total Stock].
      QA: Total Stock > 0; valuation rules consistent.
  dependencies:
    columns:
      - "fact_inventory[Obsolete Stock]"
      - "fact_inventory[Total Stock]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast Accuracy %"
  is_kpi_measure: true
  kpi_id_ref: "plan.forecast.accuracy.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "KPI"
  expression:
    dax: |
      VAR Forecast = SUM ( fact_forecast[Forecast] )
      VAR Actual   = SUM ( fact_sales[Actual] )
      VAR AbsErr   = ABS ( Forecast - Actual )
      RETURN 1 - DIVIDE ( AbsErr, Actual )
    formatString: "0.0%"
  documentation:
    description: "Planning quality: 1 - |Forecast - Actual| / Actual."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast[Forecast], fact_sales[Actual].
      QA: Actual > 0; consistent calendars; cap at [0;1] if needed.
  dependencies:
    columns:
      - "fact_forecast[Forecast]"
      - "fact_sales[Actual]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "MAPE %"
  is_kpi_measure: true
  kpi_id_ref: "plan.forecast.mape.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "KPI"
  expression:
    dax: |
      VAR Forecast = [Forecast Units]
      VAR Actual   = [Actual Units]
      RETURN DIVIDE ( [Absolute Error], Actual )
    formatString: "0.0%"
  documentation:
    description: "Mean absolute percentage error."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Actual > 0; outlier handling documented.
  dependencies:
    measures:
      - "[Absolute Error]"
      - "[Forecast Units]"
      - "[Actual Units]"
    columns:
      - "fact_forecast[Forecast Units]"
      - "fact_sales[Actual Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Bias %"
  is_kpi_measure: true
  kpi_id_ref: "plan.forecast.bias.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "KPI"
  expression:
    dax: |
      VAR Forecast = SUM ( fact_forecast[Forecast] )
      VAR Actual   = SUM ( fact_sales[Actual] )
      RETURN DIVIDE ( Forecast - Actual, Actual )
    formatString: "0.0%"
  documentation:
    description: "Forecast error direction (Forecast - Actual) / Actual."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Bias band defined; Actual > 0; DIVIDE guard.
  dependencies:
    columns:
      - "fact_forecast[Forecast]"
      - "fact_sales[Actual]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Service Impact %"
  is_kpi_measure: true
  kpi_id_ref: "plan.forecast.service_impact.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "KPI"
  expression:
    dax: |
      VAR Forecast = [Forecast Units]
      VAR Actual   = [Actual Units]
      VAR Lost     = [Lost Demand Units]
      VAR Demand   = [Demand Units]
      VAR UnderForecastLost =
          IF ( Forecast < Actual, MIN ( Lost, Actual - Forecast ), 0 )
      VAR LostShare =
          DIVIDE ( UnderForecastLost, Lost )
      VAR StockoutImpact =
          DIVIDE ( Lost, Demand )
      RETURN StockoutImpact * LostShare
    formatString: "0.0%"
  documentation:
    description: "Portion of service misses attributable to forecast error."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: forecast error, OTIF/stockout links.
      QA: Align with OTIF and stockout measures; guard divide-by-zero.
  dependencies:
    measures:
      - "[Forecast Units]"
      - "[Actual Units]"
      - "[Lost Demand Units]"
      - "[Demand Units]"
    columns:
      - "fact_forecast[Forecast Units]"
      - "fact_sales[Actual Units]"
      - "fact_stockout[Lost Demand Units]"
      - "fact_stockout[Demand Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Re-Plan Count"
  is_kpi_measure: true
  kpi_id_ref: "plan.replan.count"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "KPI"
  expression:
    dax: "SUM(fact_planning[Replan Count])"
    formatString: "#,0"
  documentation:
    description: "Number of re-plans within period."
    notes: |
      Grain: month. Unit: count.
      Lineage: planning system logs.
      QA: Consistent definition of re-plan event.
  dependencies:
    columns:
      - "fact_planning[Replan Count]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "On-Time %"
  is_kpi_measure: true
  kpi_id_ref: "supply.on_time.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Shipments = COUNTROWS ( fact_fulfillment )
      VAR OnTime    = SUM ( fact_fulfillment[On-Time Flag] )
      RETURN DIVIDE ( OnTime, Shipments )
    formatString: "0.0%"
  documentation:
    description: "On-time deliveries share."
    notes: |
      Grain: shipment. Unit: %.
      Lineage: fact_fulfillment[On-Time Flag].
      QA: One row per shipment; flag consistency.
  dependencies:
    columns:
      - "fact_fulfillment[On-Time Flag]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "In-Full %"
  is_kpi_measure: true
  kpi_id_ref: "supply.in_full.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Shipments = COUNTROWS ( fact_fulfillment )
      VAR InFull    = SUM ( fact_fulfillment[In-Full Flag] )
      RETURN DIVIDE ( InFull, Shipments )
    formatString: "0.0%"
  documentation:
    description: "In-full deliveries share."
    notes: |
      Grain: shipment. Unit: %.
      Lineage: fact_fulfillment[In-Full Flag].
      QA: One row per shipment; flag consistency.
  dependencies:
    columns:
      - "fact_fulfillment[In-Full Flag]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Stockout Impact %"
  is_kpi_measure: true
  kpi_id_ref: "supply.stockout_impact.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Lost    = SUM ( fact_stockout[Lost Demand] )
      VAR Demand  = SUM ( fact_stockout[Demand] )
      RETURN DIVIDE ( Lost, Demand )
    formatString: "0.0%"
  documentation:
    description: "Lost demand share due to stockout."
    notes: |
      Grain: location_sku_day. Unit: %.
      Lineage: fact_stockout[Lost Demand], fact_stockout[Demand].
      QA: Demand > 0; align with service metrics.
  dependencies:
    columns:
      - "fact_stockout[Lost Demand]"
      - "fact_stockout[Demand]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Penalty Amount"
  is_kpi_measure: true
  kpi_id_ref: "supply.penalty.amount"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "04_Cost"
  category: "KPI"
  expression:
    dax: "SUM(fact_fulfillment[Penalty Amount])"
    formatString: "EUR #,0.00"
  documentation:
    description: "Penalties incurred for service misses."
    notes: |
      Grain: order. Unit: EUR.
      Lineage: fact_fulfillment[Penalty Amount].
      QA: One row per order; completeness of penalty capture.
  dependencies:
    columns:
      - "fact_fulfillment[Penalty Amount]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Expedite Cost Amount"
  is_kpi_measure: true
  kpi_id_ref: "supply.expedite.amount"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "04_Cost"
  category: "KPI"
  expression:
    dax: "SUM(fact_fulfillment[Expedite Cost])"
    formatString: "EUR #,0.00"
  documentation:
    description: "Additional cost for expedited shipping."
    notes: |
      Grain: shipment. Unit: EUR.
      Lineage: fact_fulfillment[Expedite Cost].
      QA: Ensure capture of incremental costs only.
  dependencies:
    columns:
      - "fact_fulfillment[Expedite Cost]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Avg Inventory Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "Base"
  expression:
    dax: "SUM ( fact_inventory[Average Inventory Amount] )"
    formatString: "EUR #,0.00"
  documentation:
    description: "Average inventory value used as base for DIO and turnover."
    notes: "Source: fact_inventory[Average Inventory Amount]."
  dependencies:
    columns:
      - "fact_inventory[Average Inventory Amount]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "COGS Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "Base"
  expression:
    dax: "SUM ( fact_cogs[COGS Amount] )"
    formatString: "EUR #,0.00"
  documentation:
    description: "COGS base for inventory turnover and DIO."
    notes: "Source: fact_cogs[COGS Amount]."
  dependencies:
    columns:
      - "fact_cogs[COGS Amount]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "On-Time In-Full Orders"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUMX ( fact_fulfillment, IF ( fact_fulfillment[OTIF Flag], fact_fulfillment[Order Qty], 0 ) )"
    formatString: "#,0"
  documentation:
    description: "OTIF order quantity used as numerator for OTIF %."
    notes: "Source: fact_fulfillment[OTIF Flag], [Order Qty]."
  dependencies:
    columns:
      - "fact_fulfillment[OTIF Flag]"
      - "fact_fulfillment[Order Qty]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "OTIF Orders"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUMX ( fact_fulfillment, IF ( fact_fulfillment[OTIF Flag], fact_fulfillment[Order Qty], 0 ) )"
    formatString: "#,0"
  documentation:
    description: "OTIF order quantity used for OTIF %."
    notes: "Same base as On-Time In-Full Orders."
  dependencies:
    columns:
      - "fact_fulfillment[OTIF Flag]"
      - "fact_fulfillment[Order Qty]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Total Orders"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUM ( fact_fulfillment[Order Qty] )"
    formatString: "#,0"
  documentation:
    description: "Total order quantity used as denominator for OTIF, on-time, and in-full."
    notes: "Source: fact_fulfillment[Order Qty]."
  dependencies:
    columns:
      - "fact_fulfillment[Order Qty]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "On-Time Deliveries"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUMX ( fact_fulfillment, IF ( fact_fulfillment[On-Time Flag], fact_fulfillment[Order Qty], 0 ) )"
    formatString: "#,0"
  documentation:
    description: "On-time delivery quantity used as numerator for On-Time %."
    notes: "Source: fact_fulfillment[On-Time Flag], [Order Qty]."
  dependencies:
    columns:
      - "fact_fulfillment[On-Time Flag]"
      - "fact_fulfillment[Order Qty]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "In-Full Deliveries"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUMX ( fact_fulfillment, IF ( fact_fulfillment[In-Full Flag], fact_fulfillment[Order Qty], 0 ) )"
    formatString: "#,0"
  documentation:
    description: "In-full delivery quantity used as numerator for In-Full %."
    notes: "Source: fact_fulfillment[In-Full Flag], [Order Qty]."
  dependencies:
    columns:
      - "fact_fulfillment[In-Full Flag]"
      - "fact_fulfillment[Order Qty]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Demand Occurrences"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUM ( fact_stockout[Demand Occurrences] )"
    formatString: "#,0"
  documentation:
    description: "Demand occurrences used as denominator for stockout rate."
    notes: "Source: fact_stockout[Demand Occurrences]."
  dependencies:
    columns:
      - "fact_stockout[Demand Occurrences]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Stockout Count"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUMX ( fact_stockout, IF ( fact_stockout[Stockout Flag], fact_stockout[Demand Occurrences], 0 ) )"
    formatString: "#,0"
  documentation:
    description: "Stockout occurrences used as numerator for stockout rate."
    notes: "Source: fact_stockout[Stockout Flag], [Demand Occurrences]."
  dependencies:
    columns:
      - "fact_stockout[Stockout Flag]"
      - "fact_stockout[Demand Occurrences]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Lost Demand Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUM ( fact_stockout[Lost Demand Units] )"
    formatString: "#,0"
  documentation:
    description: "Lost demand units used for stockout impact."
    notes: "Source: fact_stockout[Lost Demand Units]."
  dependencies:
    columns:
      - "fact_stockout[Lost Demand Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Demand Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "Base"
  expression:
    dax: "SUM ( fact_stockout[Demand Units] )"
    formatString: "#,0"
  documentation:
    description: "Demand units used as denominator for stockout impact."
    notes: "Source: fact_stockout[Demand Units]."
  dependencies:
    columns:
      - "fact_stockout[Demand Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "Base"
  expression:
    dax: "SUM ( fact_forecast[Forecast Units] )"
    formatString: "#,0"
  documentation:
    description: "Forecast quantity base for planning KPIs."
    notes: "Source: fact_forecast[Forecast Units]."
  dependencies:
    columns:
      - "fact_forecast[Forecast Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Actual Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "Base"
  expression:
    dax: "SUM ( fact_sales[Actual Units] )"
    formatString: "#,0"
  documentation:
    description: "Actual quantity base for planning KPIs."
    notes: "Source: fact_sales[Actual Units]."
  dependencies:
    columns:
      - "fact_sales[Actual Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Absolute Error"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "Base"
  expression:
    dax: "ABS ( [Forecast Units] - [Actual Units] )"
    formatString: "#,0"
  documentation:
    description: "Absolute forecast error used for accuracy and MAPE."
    notes: "Derived from Forecast Units and Actual Units."
  dependencies:
    measures:
      - "[Forecast Units]"
      - "[Actual Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
- measure_name: "Forecast Error Qty"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "Base"
  expression:
    dax: "[Forecast Units] - [Actual Units]"
    formatString: "#,0"
  documentation:
    description: "Forecast units minus actual units."
    notes: "Derived from Forecast Units and Actual Units."
  dependencies:
    measures:
      - "[Forecast Units]"
      - "[Actual Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Under-Forecast Lost Demand Qty"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "Base"
  expression:
    dax: |
      VAR ThresholdPct = 0.05
      RETURN
      SUMX (
          FILTER (
              fact_stockout,
              [Forecast Error Qty] < - ThresholdPct * [Actual Units]
          ),
          fact_stockout[Lost Demand Units]
      )
    formatString: "#,0"
  documentation:
    description: "Lost demand units attributable to under-forecasting beyond threshold."
    notes: "Requires Lost Demand Units and forecast error logic."
  dependencies:
    columns:
      - "fact_stockout[Lost Demand Units]"
    measures:
      - "[Forecast Error Qty]"
      - "[Actual Units]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Under-Forecast Lost Demand Share %"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "Base"
  expression:
    dax: "DIVIDE ( [Under-Forecast Lost Demand Qty], [Stockout Lost Demand Qty] )"
    formatString: "0.0%"
  documentation:
    description: "Share of stockout lost demand attributable to under-forecasting."
    notes: "Derived from Under-Forecast Lost Demand Qty and Stockout Lost Demand Qty."
  dependencies:
    measures:
      - "[Under-Forecast Lost Demand Qty]"
      - "[Stockout Lost Demand Qty]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
- measure_name: "Inventory Value Amount"
  is_kpi_measure: true
  kpi_id_ref: "ops.inventory.value.amount"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "KPI"
  expression:
    dax: "SUM ( fact_inventory[Inventory Value Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Total inventory value in the selected scope."
    notes: |
      Grain: location_sku_day. Unit: EUR.
      Lineage: fact_inventory[Inventory Value Amount].
      QA: Valuation method consistent with finance policy.
  dependencies:
    columns:
      - "fact_inventory[Inventory Value Amount]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"

- measure_name: "Supply Chain Service Level %"
  is_kpi_measure: true
  kpi_id_ref: "scm.service_level.pct"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: |
      DIVIDE ( SUM ( fact_fulfillment[OTIF Flag] ), COUNTROWS ( fact_fulfillment ) )
    formatString: "0.0%"
  documentation:
    description: "On-time in-full rate for customer fulfillment."
    notes: |
      Grain: order_line_day. Unit: %.
      Lineage: fact_fulfillment[OTIF Flag].
      QA: OTIF definition aligned to customer policy.
  dependencies:
    columns:
      - "fact_fulfillment[OTIF Flag]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"

- measure_name: "Order Lines Count"
  is_kpi_measure: true
  kpi_id_ref: "order.lines"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: "COUNTROWS ( fact_order_lines )"
    formatString: "#,0"
  documentation:
    description: "Count of order line items."
    notes: |
      Grain: order_line. Unit: count.
      Lineage: fact_order_lines[Order Line ID].
      QA: De-duplicate merged or split lines.
  dependencies:
    columns:
      - "fact_order_lines[Order Line ID]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"

- measure_name: "Plans Count"
  is_kpi_measure: true
  kpi_id_ref: "plans.count"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "03_Forecast"
  category: "KPI"
  expression:
    dax: "COUNTROWS ( fact_plan )"
    formatString: "#,0"
  documentation:
    description: "Count of plan records or plan versions."
    notes: |
      Grain: plan_version. Unit: count.
      Lineage: fact_plan[Plan ID].
      QA: Distinguish baseline vs scenario plans.
  dependencies:
    columns:
      - "fact_plan[Plan ID]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"

- measure_name: "Shipments Count"
  is_kpi_measure: true
  kpi_id_ref: "shipments.count"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "02_Service"
  category: "KPI"
  expression:
    dax: "COUNTROWS ( fact_shipment )"
    formatString: "#,0"
  documentation:
    description: "Count of shipments executed."
    notes: |
      Grain: shipment. Unit: count.
      Lineage: fact_shipment[Shipment ID].
      QA: Exclude canceled shipments.
  dependencies:
    columns:
      - "fact_shipment[Shipment ID]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"
```

