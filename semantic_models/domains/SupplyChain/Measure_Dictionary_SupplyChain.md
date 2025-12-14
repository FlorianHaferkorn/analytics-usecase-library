# Measure Dictionary - SupplyChain

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Days in Inventory (DIO)"
  is_kpi_measure: true
  kpi_id_ref: "inv.dio.days"
  semantic_model: "SupplyChain_SemanticModel"
  display_folder: "01_Inventory"
  category: "KPI"
  expression:
    dax: |
      VAR AvgInv = SUM ( fact_inventory[Avg Inventory] )
      VAR CogsPerDay =
          DIVIDE (
              SUM ( fact_cogs[COGS] ),
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
      - "fact_inventory[Avg Inventory]"
      - "fact_cogs[COGS]"
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
      VAR AvgInv = SUM ( fact_inventory[Avg Inventory] )
      VAR Cogs   = SUM ( fact_cogs[COGS] )
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
      - "fact_inventory[Avg Inventory]"
      - "fact_cogs[COGS]"
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
    dax: "/* TODO: implement MAPE % */"
    formatString: "0.0%"
  documentation:
    description: "Mean absolute percentage error."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: fact_forecast vs fact_sales.
      QA: Actual > 0; outlier handling documented.
  dependencies:
    columns:
      - "fact_forecast[Forecast]"
      - "fact_sales[Actual]"
  governance:
    owner: "Supply Chain Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Forecast Bias %"
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
    dax: "/* TODO: implement Service Impact % */"
    formatString: "0.0%"
  documentation:
    description: "Portion of service misses attributable to forecast error."
    notes: |
      Grain: sku_month. Unit: %.
      Lineage: forecast error, OTIF/stockout links.
      QA: Align with OTIF and stockout measures; guard divide-by-zero.
  dependencies:
    columns:
      - "fact_forecast[Forecast]"
      - "fact_sales[Actual]"
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
```
