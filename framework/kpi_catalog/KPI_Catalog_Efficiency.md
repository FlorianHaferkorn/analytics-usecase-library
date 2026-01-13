# KPI Catalog - Efficiency

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: ops.oee.pct
  kpi_key: Overall Equipment Effectiveness (OEE) %
  kpi_type: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  calc_type: ratio
  business:
    purpose: Measures manufacturing performance combining availability, performance, and quality.
    definition: Availability % * Performance % * Quality %
    grain_scope: Production line; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher OEE indicates better utilization; capped at 100 %.
  technical:
    dax_name: OEE %
    depends_on_measures:
    - Availability %
    - Performance %
    - Quality %
    lineage:
    - fact_mes.Availability
    - fact_mes.Performance
    - fact_mes.Quality
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: MES Analyst
    review_cycle: quarterly
    validation_process: automated + manual spot checks
    qa_rules:
    - Subcomponents validated against MES feed; OEE = 100 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 12.10.2025
- kpi_id: ops.process.cost_per_unit.amount
  kpi_key: Process Cost per Unit
  kpi_type: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: ratio
  business:
    purpose: Measures average process cost per produced unit.
    definition: Total Process Cost / Produced Units Qty
    grain_scope: Production site, monthly.
    unit_format: EUR (2 decimals)
    interpretation: Key indicator for cost efficiency and process optimization.
  technical:
    dax_name: Process Cost per Unit
    depends_on_measures:
    - Total Process Cost Amount
    - Produced Units Qty
    lineage:
    - fact_costs.TotalProcessCost
    - fact_production.ProducedUnits
  governance:
    business_owner: Head of Operations
    data_owner: Manufacturing BI
    steward: Operations Controller
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconcile with manufacturing ledger <= 1 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.97
    last_review: 12.10.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: ops.inventory.days
  kpi_key: Inventory Days
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Average number of days current inventory covers sales (on-hand duration).
    definition: (Average Inventory / Daily COGS)
    grain_scope: Company/segment; monthly closing based on inventory valuation and COGS.
    unit_format: days
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Inventory Days
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to inventory valuation and COGS within +/- 1 day; Inventory Days >= 0.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.inventory.obsolescence.pct
  kpi_key: Inventory Obsolescence %
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: rate
  business:
    purpose: Measures the share of inventory that is obsolete or slow moving.
    definition: Obsolete Inventory Value / Total Inventory Value
    grain_scope: SKU/Location; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher values signal excess or aged stock tying up working capital and increasing write-off risk.
  technical:
    dax_name: Inventory Obsolescence %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounded between 0% and 100%
    - Reconciles to aging/valuation reports within +/- 0.5 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 27.11.2025
- kpi_id: ops.capacity.utilization.pct
  kpi_key: Capacity Utilization %
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-005
  - COR-011
  calc_type: rate
  business:
    purpose: Measure how much of the available capacity is used to produce output.
    definition: Planned Load Hours / Available Hours for a given line, site or resource in the selected period.
    grain_scope: Line/Resource; aggregated to site/region and period.
    unit_format: '% (1 decimal)'
    interpretation: Higher utilization indicates better capacity usage; very high values may indicate risk of bottlenecks
      or service issues.
  technical:
    dax_name: Capacity Utilization %
    depends_on_measures: []
    lineage:
    - fact_capacity.AvailableHours
    - fact_capacity.PlannedLoadHours
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Capacity Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles with capacity planning reports within +/- 0.5 pp
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
- kpi_id: ops.demand.total.qty
  kpi_key: Total Demand Qty
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Total units requested by customers or planning in the period.
    definition: Sum of requested units across orders and/or forecast
    grain_scope: SKU/Location/Day; aggregated weekly/monthly.
    unit_format: qty
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Total Demand Qty
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to order/forecast system within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.demand.unfulfilled.qty
  kpi_key: Unfulfilled Demand Qty
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Units requested but not delivered due to stock constraints.
    definition: Total Demand Qty - Fulfilled Qty
    grain_scope: SKU/Location/Day; aggregated weekly/monthly.
    unit_format: qty
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Unfulfilled Demand Qty
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Consistent with stockout exceptions within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.availability.pct
  kpi_key: Availability %
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Uptime share relative to planned production time.
    definition: Available time / Planned time
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Availability %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Availability % bounded between 0 % and 100 %; reconciles to planned/available time from MES within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.performance.pct
  kpi_key: Performance %
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Throughput speed versus theoretical maximum.
    definition: Actual output / Theoretical maximum output
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Performance %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Production Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Performance % bounded between 0 % and 150 %; investigate values outside expected range by line.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.quality.pct
  kpi_key: Quality %
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Yield of conforming units relative to total units produced.
    definition: Good units / Total units
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Quality %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Quality Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Quality % bounded between 0 % and 100 %; reconcile to scrap/rework reporting within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.downtime.hours
  kpi_key: Downtime Hours
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Total duration of machine/line unavailability impacting production.
    definition: Sum of downtime hours
    grain_scope: Machine/line level; per shift/day, aggregated monthly.
    unit_format: hours
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Downtime Hours
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Order Management
    data_owner: Operations BI
    steward: Order Management Lead
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative; reconcile to MES downtime logs within +/- 0.1 h
    - Categorization (planned/unplanned) consistent with maintenance system
    - Non-negative; investigate values < 1 or unusually high
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.planned.hours
  kpi_key: Planned Hours
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Scheduled production time allocated for machines/lines.
    definition: Sum of planned production hours
    grain_scope: Machine/line level; per shift/day, aggregated monthly.
    unit_format: hours
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Planned Hours
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain Planning
    data_owner: Supply Chain BI
    steward: Demand Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative; reconcile to planning system within +/- 0.1 h
    - Planned vs actual variance monitored in OEE context
    - Reconciles to WMS/OMS order status within +/- 1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.stockout.pct
  kpi_key: Stock-Out Rate %
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Share of demand not fulfilled due to stock unavailability.
    definition: Unfulfilled Demand / Total Demand
    grain_scope: SKU/Location level; aggregated daily/weekly.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Stock-Out Rate %
    depends_on_measures:
    - Unfulfilled Demand Qty
    - Total Demand Qty
    lineage: []
  governance:
    business_owner: Head of Supply Chain Planning
    data_owner: Supply Chain BI
    steward: Demand Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounded between 0% and 100%
    - Cross-check with replenishment exceptions within +/- 1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.inventory.turnover
  kpi_key: Inventory Turnover
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: ratio
  business:
    purpose: Measures how often inventory is sold and replaced over a period to assess stock efficiency.
    definition: COGS / Average Inventory
    grain_scope: Company/segment; monthly or quarterly using average inventory over the period.
    unit_format: x (turns per period)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Inventory Turnover
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Finance
    data_owner: Supply Chain BI
    steward: Inventory Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative; reconciles to inventory and COGS reporting within +/- 0.5 turns.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.otif.pct
  kpi_key: OTIF %
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Delivery reliability measured by orders delivered on-time and in-full.
    definition: On-Time In-Full deliveries / Total Deliveries
    grain_scope: Order/shipment level; aggregated weekly/monthly.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: OTIF %
    depends_on_measures:
    - OTIF Deliveries Count
    - Total Deliveries Count
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Finance
    data_owner: Supply Chain BI
    steward: Inventory Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory days reconcile to inventory and COGS within +/- 1 day
    - 'Bounded: DSO/DIO/DPO derived days must be >= 0'
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.ppv.pct
  kpi_key: PPV %
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Relative variance between actual purchase price and contracted price.
    definition: (Actual Price - Contract Price) / Contract Price
    grain_scope: PO line level; aggregated monthly by supplier/category.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: PPV %
    depends_on_measures:
    - Actual Purchase Price Amount
    - Contract Purchase Price Amount
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - PPV bounded within reasonable range (e.g., [-100%; +200%])
    - Reconciles to contract price list and invoice data within +/- 0.5 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.ppv.amount
  kpi_key: PPV Amount
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Absolute variance between actual price paid and contracted price for purchased quantity.
    definition: (Actual Price - Contract Price) x Quantity
    grain_scope: PO line level; aggregated monthly by supplier/category.
    unit_format: EUR (2 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: PPV Amount
    depends_on_measures:
    - Actual Purchase Price Amount
    - Contract Purchase Price Amount
    - Purchase Quantity
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to invoice/PO data within +/- 1 %
    - Currency consistent with procurement ledger
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.contract.compliance.pct
  kpi_key: Contract Compliance %
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Share of purchases placed at contracted terms (price/conditions).
    definition: Purchases at agreed price / Total purchases
    grain_scope: PO line level; aggregated monthly by supplier/category.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Contract Compliance %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounded between 0% and 100%
    - Reconciles to contract master and invoice lines within +/- 1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.replenishment.adherence.pct
  kpi_key: Replenishment Adherence %
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Adherence of replenishment execution to plan (timing and quantity).
    definition: Actual Orders / Target Orders (on time/quantity)
    grain_scope: SKU/Location planning level; aggregated weekly/monthly.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Replenishment Adherence %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounded between 0% and 100%
    - Cross-check vs planning system exceptions within +/- 1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.order_accuracy.pct
  kpi_key: Order Accuracy %
  kpi_type: diagnostic
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Share of customer orders delivered exactly as ordered (quantity, items, conditions).
    definition: Orders fulfilled correctly / Total Orders
    grain_scope: Order level; aggregated daily/weekly/monthly by channel or region.
    unit_format: '% (1 decimal)'
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Order Accuracy %
    depends_on_measures:
    - Correct Orders Count
    - Total Orders Count
    lineage: []
  governance:
    business_owner: Head of Order Management
    data_owner: Operations BI
    steward: Order Management Lead
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Order Accuracy % bounded between 0 % and 100 %
    - Cross-check vs. returns/claims data for inconsistencies
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.machine_downtime.pct
  kpi_key: Machine Downtime %
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: ratio
  business:
    purpose: Measures proportion of time equipment is not running.
    definition: Downtime Hours / Planned Hours
    grain_scope: Machine level.
    unit_format: '% (1 decimal)'
    interpretation: High downtime reduces efficiency and throughput.
  technical:
    dax_name: Machine Downtime %
    depends_on_measures:
    - Downtime Hours
    - Planned Hours
    lineage:
    - fact_production.DowntimeHours
    - fact_production.PlannedHours
  governance:
    business_owner: Head of Maintenance
    data_owner: Operations Data Team
    steward: Maintenance Planner
    review_cycle: quarterly
    validation_process: automated
    qa_rules:
    - Downtime % <= 100 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 12.10.2025
- kpi_id: ops.working_capital.dso.days
  kpi_key: DSO (Days)
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - COR-004
  calc_type: amount
  business:
    purpose: Measures how long receivables remain outstanding before being converted into cash.
    definition: (Average Accounts Receivable / Net Sales) x Days in Period.
    grain_scope: Consolidated by legal entity, region, or company code.
    unit_format: days
    interpretation: Higher values signal slower collections and higher working capital.
  technical:
    dax_name: DSO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - DSO bounded between 0 and 180 days; reconciles to AR and revenue balances within +/- 1 day.
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.working_capital.dio.days
  kpi_key: DIO (Days)
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  calc_type: amount
  business:
    purpose: Shows how long inventory stays on hand before being sold.
    definition: (Average Inventory / COGS) x Days in Period.
    grain_scope: Warehouse / business unit.
    unit_format: days
    interpretation: Higher values indicate slow-moving stock binding capital.
  technical:
    dax_name: DIO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain
    data_owner: Finance BI
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    steward: Inventory Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - DIO bounded between 0 and 365 days; reconciles to inventory and COGS balances within +/- 1 day.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.working_capital.dpo.days
  kpi_key: DPO (Days)
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  calc_type: amount
  business:
    purpose: Indicates how long the company takes to pay suppliers.
    definition: (Accounts Payable / COGS) x Days in Period.
    grain_scope: Supplier group / legal entity.
    unit_format: days
    interpretation: Higher values reflect longer payment terms and better cash preservation.
  technical:
    dax_name: DPO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement Controlling
    data_owner: Finance BI
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - DPO bounded between 0 and 180 days; reconciles to AP and COGS balances within +/- 1 day.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: ops.working_capital.ccc.days
  kpi_key: Cash Conversion Cycle (Days)
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - COR-004
  calc_type: amount
  business:
    purpose: Combines receivables, inventory, and payables days to show cash efficiency.
    definition: DSO + DIO - DPO.
    grain_scope: Company / region level.
    unit_format: days
    interpretation: Lower CCC means faster cash conversion and lower working capital.
  technical:
    dax_name: Cash Conversion Cycle (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    note: Cross-domain view. Canonical definition in KPI_Catalog_Liquidity.
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Input metrics reconciled before aggregation
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025
- kpi_id: ops.working_capital.ccc.delta_days
  kpi_key: Delta CCC (Days)
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Explains the variance of the cash conversion cycle versus plan or last year.
    definition: Cash Conversion Cycle (Days) - Baseline CCC (Plan or LY).
    grain_scope: Company / region level.
    unit_format: days
    interpretation: Positive values indicate slower cash conversion than the reference; negative values indicate improvement.
  technical:
    dax_name: Delta CCC (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Baseline CCC defined and frozen before comparison
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025
- kpi_id: ops.orders.total.count
  kpi_key: Total Orders Count
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Denominator for order accuracy and fulfillment KPIs.
    definition: Count of orders
    grain_scope: Order level; aggregated weekly/monthly.
    unit_format: count
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Total Orders Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Order Management
    data_owner: Operations BI
    steward: Order Specialist
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to OMS within +/- 1 count
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.orders.correct.count
  kpi_key: Correct Orders Count
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Numerator for order accuracy KPI.
    definition: Count of orders fulfilled without errors
    grain_scope: Order level; aggregated weekly/monthly.
    unit_format: count
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Correct Orders Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Order Management
    data_owner: Operations BI
    steward: Order Specialist
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to OMS quality flags within +/- 1 count
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.deliveries.total.count
  kpi_key: Total Deliveries Count
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Denominator for OTIF KPI.
    definition: Count of deliveries
    grain_scope: Shipment/delivery level; aggregated weekly/monthly.
    unit_format: count
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Total Deliveries Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to WMS/TMS within +/- 1 count
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.deliveries.otif.count
  kpi_key: OTIF Deliveries Count
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Numerator for OTIF KPI.
    definition: Count of deliveries meeting OTIF criteria
    grain_scope: Shipment/delivery level; aggregated weekly/monthly.
    unit_format: count
    interpretation: TODO - add interpretation.
  technical:
    dax_name: OTIF Deliveries Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to WMS/TMS within +/- 1 count
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.purchases.at_contract.amount
  kpi_key: Purchases at Contract Amount
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Spend against contracted terms for compliance KPI.
    definition: Sum of purchase amounts at contract price
    grain_scope: PO line level; aggregated monthly.
    unit_format: EUR (2 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Purchases at Contract Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to PO/invoice data within +/- 1 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.purchases.total.amount
  kpi_key: Total Purchases Amount
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Denominator for contract compliance KPI.
    definition: Sum of all purchase amounts
    grain_scope: PO line level; aggregated monthly.
    unit_format: EUR (2 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Total Purchases Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to PO/invoice data within +/- 1 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.purchase.price.actual.amount
  kpi_key: Actual Purchase Price Amount
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Actual unit price input for PPV.
    definition: Average actual price per unit
    grain_scope: PO line level; aggregated monthly.
    unit_format: EUR (4 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Actual Purchase Price Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Currency and unit alignment with contract
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.purchase.price.contract.amount
  kpi_key: Contract Purchase Price Amount
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Contract price input for PPV.
    definition: Contract price per unit
    grain_scope: PO line level; aggregated monthly.
    unit_format: EUR (4 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Contract Purchase Price Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Currency and unit alignment with contract
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.purchase.units.qty
  kpi_key: Purchase Quantity
  kpi_type: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: count
  business:
    purpose: Quantity input for PPV amount.
    definition: Sum of purchased units
    grain_scope: PO line level; aggregated monthly.
    unit_format: qty
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Purchase Quantity
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Procurement BI
    steward: Procurement Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to PO goods receipt within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 21.11.2025
- kpi_id: ops.logistics.cost_ratio.pct
  kpi_key: Logistics Cost Ratio %
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-009
  calc_type: rate
  business:
    purpose: Measure logistics cost relative to net sales or shipped value.
    definition: Total logistics cost divided by Net Sales Amount (or shipped value) in the same scope.
    grain_scope: Org / region / route; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Lower ratio indicates more efficient logistics; extreme reductions may signal underinvestment or service
      risk.
  technical:
    dax_name: Logistics Cost Ratio %
    depends_on_measures: []
    lineage:
    - fact_logistics.CostAmount
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Logistics Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Cost base (transport, warehousing, handling) clearly defined
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
- kpi_id: ops.logistics.cost_per_unit.amount
  kpi_key: Logistics Cost per Unit
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-009
  calc_type: ratio
  business:
    purpose: Measure average logistics cost per shipped unit.
    definition: Total logistics cost divided by shipped units quantity.
    grain_scope: Shipment / lane / customer; aggregated to reporting period.
    unit_format: EUR per unit
    interpretation: Lower cost per unit indicates more efficient utilization; interpret together with service level.
  technical:
    dax_name: Logistics Cost per Unit
    depends_on_measures: []
    lineage:
    - fact_logistics.CostAmount
    - fact_logistics.UnitsQty
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Logistics Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Units and cost base reconciled to operational reports
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
- kpi_id: ops.warehouse.lines_per_hour
  kpi_key: Warehouse Lines per Hour
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-011
  calc_type: ratio
  business:
    purpose: Measure warehouse productivity in terms of processed order lines per working hour.
    definition: Total processed order lines divided by total productive hours in the warehouse.
    grain_scope: Warehouse / shift / day.
    unit_format: lines per hour
    interpretation: Higher values indicate better productivity; interpret with error rates and service level.
  technical:
    dax_name: Warehouse Lines per Hour
    depends_on_measures: []
    lineage:
    - fact_warehouse.OrderLinesProcessed
    - fact_warehouse.ProductiveHours
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Warehouse Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Productive hours definition includes only active picking/packing time
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
- kpi_id: ops.warehouse.picks_per_hour
  kpi_key: Picks per Hour
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-011
  calc_type: ratio
  business:
    purpose: Measure picking productivity per hour in the warehouse.
    definition: Total picks (pick operations) divided by productive picking hours.
    grain_scope: Warehouse / zone / shift / day.
    unit_format: picks per hour
    interpretation: Higher picks per hour indicate more efficient picking; interpret with error rates and health/safety constraints.
  technical:
    dax_name: Picks per Hour
    depends_on_measures: []
    lineage:
    - fact_warehouse.PicksCount
    - fact_warehouse.PickingHours
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Warehouse Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Picks and hours reconciled to WMS and time tracking
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
- kpi_id: ops.warehouse.cost_per_line.amount
  kpi_key: Warehouse Cost per Line
  kpi_type: diagnostic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-011
  calc_type: ratio
  business:
    purpose: Measure warehouse operating cost per processed order line.
    definition: Total warehouse operating cost divided by number of processed order lines.
    grain_scope: Warehouse / period (month or quarter).
    unit_format: EUR per line
    interpretation: Lower cost per line indicates higher efficiency; significant changes require analysis of volume, wage,
      and productivity drivers.
  technical:
    dax_name: Warehouse Cost per Line
    depends_on_measures: []
    lineage:
    - fact_warehouse.CostAmount
    - fact_warehouse.OrderLinesProcessed
  governance:
    business_owner: Head of Logistics
    data_owner: Operations BI
    steward: Warehouse Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Cost allocation model and order line definition documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
- kpi_id: plan.forecast.service_impact.pct
  kpi_key: Service Impact %
  kpi_type: percentage
  impact_dimension: Efficiency
  domain_tag:
    - Forecast Planning
  use_case_ref:
    - SCM-003
    - SCM-002
    - SCM-001
  business:
    purpose: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage.
    definition: Service Impact % = Stockout Impact % x (Under-Forecast Lost Demand / Total Lost Demand). Under-forecast is defined as a negative forecast error below a configurable threshold.
    grain_scope: Calculated at location_sku_day or sku_week; reported at sku_month aggregated by Date, Org, Product.
    unit_format: "%"
    qa:
      - KPI only valid when Total Demand Qty > 0.
      - Service Impact % must be <= Stockout Impact %.
      - Under-Forecast Lost Demand Share must be between 0 % and 100 %.
  technical:
    required_columns:
      - fact_forecast[Forecast Qty]
      - fact_demand[Actual Demand Qty]
      - fact_stockout[Lost Demand Qty]
      - fact_stockout[Demand Qty]
      - fact_stockout[Stockout Flag] or fact_otif[OTIF Flag]
    lineage: fact_forecast, fact_demand or sales, fact_stockout/fact_fulfillment.
    formatString: "0.0 %"
  governance:
    owner: Supply Chain Planning
    certified: false
    last_review: TBD
```
