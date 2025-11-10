# KPI Catalog - Efficiency

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "ops.oee.pct"
  kpi_key: "Overall Equipment Effectiveness (OEE) %"
  kpi_type: "strategic"
  strategic_ref: "Overall Equipment Effectiveness (OEE) %"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  use_case_ref: ["OPS-001"]
  depends_on: ["Availability %","Performance %","Quality %"]
  depends_on_ids: ["ops.availability.pct","ops.performance.pct","ops.quality.pct"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures manufacturing performance combining availability, performance, and quality."
    definition: "Availability % * Performance % * Quality %"
    grain_scope: "Production line; aggregated monthly."
    unit_format: "% (1 decimal)"
    interpretation: "Higher OEE indicates better utilization; capped at 100 %."
  technical:
    dax_name: "OEE %"
    dax_expression: "[Availability %] * [Performance %] * [Quality %]"
    description: "Composite efficiency: Availability x Performance x Quality."
    lineage: ["fact_mes.Availability","fact_mes.Performance","fact_mes.Quality"]
    source_grain: "production_line"
    source_column_ref: ["fact_mes.availability_pct","fact_mes.performance_pct","fact_mes.quality_pct"]
    source_system: "MES"
    formatString: "0.0 %"
    verified: true
  governance:
    business_owner: "Head of Manufacturing"
    data_owner: "Manufacturing BI"
    steward: "MES Analyst"
    review_cycle: "quarterly"
    validation_process: "automated + manual spot checks"
    qa_rules:
      - "Subcomponents validated against MES feed; OEE ≤ 100 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_id: "ops.process.cost_per_unit.amount"
  kpi_key: "Process Cost per Unit"
  kpi_type: "strategic"
  strategic_ref: "Process Cost per Unit"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  use_case_ref: ["OPS-002"]
  depends_on: ["Total Process Cost Amount","Produced Units Qty"]
  depends_on_ids: ["ops.total_process_cost.amount","ops.produced_units.qty"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures average process cost per produced unit."
    definition: "Total Process Cost / Produced Units Qty"
    grain_scope: "Production site, monthly."
    unit_format: "€ (2 decimals)"
    interpretation: "Key indicator for cost efficiency and process optimization."
  technical:
    dax_name: "Process Cost per Unit"
    dax_expression: "DIVIDE([Total Process Cost Amount],[Produced Units Qty])"
    lineage: ["fact_costs.TotalProcessCost","fact_production.ProducedUnits"]
    source_grain: "production_line"
    source_column_ref: ["fact_costs.total_process_cost_amt"]
    source_system: "ERP"
    description: "Average process cost per produced unit."
    formatString: "EUR #,0.00"
    verified: true
  governance:
    business_owner: "Head of Operations"
    data_owner: "Manufacturing BI"
    steward: "Operations Controller"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Reconcile with manufacturing ledger <= 1 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
```

## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "ops.inventory.days"
  kpi_key: "Inventory Days"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Inventory Days"
    description: "Average Inventory / Daily COGS"
    formatString: "0"
  verified: false
  business:
    purpose: "Average number of days current inventory covers sales (on-hand duration)."
    definition: "(Average Inventory / Daily COGS)"
    grain_scope: "Company/segment; monthly closing based on inventory valuation and COGS."
    unit_format: "days"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.demand.total.qty"
  kpi_key: "Total Demand Qty"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "Total Demand Qty"
    description: "Total requested units (orders + forecast)"
    formatString: "0"
    verified: false
  business:
    purpose: "Total units requested by customers or planning in the period."
    definition: "Sum of requested units across orders and/or forecast"
    grain_scope: "SKU/Location/Day; aggregated weekly/monthly."
    unit_format: "qty"
  governance:
    business_owner: "Supply Planning Lead"
    data_owner: "Supply Chain BI"
    steward: "Planner"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to order/forecast system within +/- 0.5 %"
    version: "v1.0"
    last_review: "2025-11-04"
```

```yaml
- kpi_id: "ops.demand.unfulfilled.qty"
  kpi_key: "Unfulfilled Demand Qty"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "Unfulfilled Demand Qty"
    description: "Requested units not delivered"
    formatString: "0"
    verified: false
  business:
    purpose: "Units requested but not delivered due to stock constraints."
    definition: "Total Demand Qty - Fulfilled Qty"
    grain_scope: "SKU/Location/Day; aggregated weekly/monthly."
    unit_format: "qty"
  governance:
    business_owner: "Supply Planning Lead"
    data_owner: "Supply Chain BI"
    steward: "Planner"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Consistent with stockout exceptions within +/- 0.5 %"
    version: "v1.0"
    last_review: "2025-11-04"
```

```yaml
- kpi_id: "ops.availability.pct"
  kpi_key: "Availability %"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Availability %"
    description: "Available time / Planned time"
    formatString: "0.0 %"
    verified: false
  business:
    purpose: "Uptime share relative to planned production time."
    definition: "Available time / Planned time"
    grain_scope: "Machine/line level; per shift or day, aggregated monthly."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.performance.pct"
  kpi_key: "Performance %"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Performance %"
    description: "Actual output / Theoretical maximum"
    formatString: "0.0 %"
    verified: false
  business:
    purpose: "Throughput speed versus theoretical maximum."
    definition: "Actual output / Theoretical maximum output"
    grain_scope: "Machine/line level; per shift or day, aggregated monthly."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.quality.pct"
  kpi_key: "Quality %"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Quality %"
    description: "Good units / Total units"
    formatString: "0.0 %"
    verified: false
  business:
    purpose: "Yield of conforming units relative to total units produced."
    definition: "Good units / Total units"
    grain_scope: "Machine/line level; per shift or day, aggregated monthly."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.downtime.hours"
  kpi_key: "Downtime Hours"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Downtime Hours"
    description: "Sum of downtime hours"
    formatString: "0.00"
    verified: false
  business:
        purpose: "Total duration of machine/line unavailability impacting production."`n    definition: "Sum of downtime hours"`n    grain_scope: "Machine/line level; per shift/day, aggregated monthly."`n    unit_format: "hours"`n
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Non-negative; reconcile to MES downtime logs within +/- 0.1 h"`n      - "Categorization (planned/unplanned) consistent with maintenance system"`n      - "Non-negative; investigate values < 1 or unusually high"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.planned.hours"
  kpi_key: "Planned Hours"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Planned Hours"
    description: "Sum of planned production hours"
    formatString: "0.00"
    verified: false
  business:
        purpose: "Scheduled production time allocated for machines/lines."`n    definition: "Sum of planned production hours"`n    grain_scope: "Machine/line level; per shift/day, aggregated monthly."`n    unit_format: "hours"`n
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Non-negative; reconcile to planning system within +/- 0.1 h"`n      - "Planned vs actual variance monitored in OEE context"`n      - "Reconciles to WMS/OMS order status within +/- 1 pp"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.total_process_cost.amount"
  kpi_key: "Total Process Cost Amount"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Total Process Cost Amount"
    description: "Total manufacturing process cost"
    formatString: "€ #,0.00"
    verified: false
  business:
        purpose: "Total cost incurred for production processes."`n    definition: "Sum of all process-related manufacturing cost components."`n    grain_scope: "Site/line level; monthly closing."`n    unit_format: "EUR (2 decimals)"`n
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Reconciles to cost ledger within +/- 0.5 %"`n      - "Currency consistent with finance system"`n    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.stockout.pct"
  kpi_key: "Stock-Out Rate %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Stock-Out Rate %"
    description: "Unfulfilled Demand / Total Demand"
    formatString: "0.0 %"
    verified: false`n  depends_on: ["Unfulfilled Demand Qty","Total Demand Qty"]`n  depends_on_ids: ["ops.demand.unfulfilled.qty","ops.demand.total.qty"]
  business:
    purpose: "Share of demand not fulfilled due to stock unavailability."
    definition: "Unfulfilled Demand / Total Demand"
    grain_scope: "SKU/Location level; aggregated daily/weekly."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Bounded between 0% and 100%"
      - "Cross-check with replenishment exceptions within +/- 1 pp"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.inventory.turnover"
  kpi_key: "Inventory Turnover"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: ratio
  technical:
    dax_name: "Inventory Turnover"
    description: "COGS / Average Inventory"
    formatString: "0.00"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.inventory.obsolescence.pct"
  kpi_key: "Obsolescence %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Obsolescence %"
    description: "Aged or blocked stock / Total Inventory"
    formatString: "0.0 %"
    verified: false
  business:
        purpose: "Share of inventory considered obsolete or blocked."`n    definition: "Aged or blocked stock / Total Inventory"`n    grain_scope: "SKU/Location; monthly."`n    unit_format: "% (1 decimal)"`n
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Bounded between 0% and 100%"`n      - "Cross-check against aging report within +/- 1 pp"`n    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.otif.pct"
  kpi_key: "OTIF %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "OTIF %"
    description: "On-Time In-Full deliveries / Total Deliveries"
    formatString: "0.0 %"
    verified: false`n  depends_on: ["OTIF Deliveries Count","Total Deliveries Count"]`n  depends_on_ids: ["ops.deliveries.otif.count","ops.deliveries.total.count"]
  business:
    purpose: "Delivery reliability measured by orders delivered on-time and in-full."
    definition: "On-Time In-Full deliveries / Total Deliveries"
    grain_scope: "Order/shipment level; aggregated weekly/monthly."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Inventory days reconcile to inventory and COGS within +/- 1 day"
      - "Bounded: DSO/DIO/DPO derived days must be >= 0"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.ppv.pct"
  kpi_key: "PPV %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "PPV %"
    description: "(Actual Price - Contract Price) / Contract Price"
    formatString: "0.0 %"
    verified: false`n  depends_on: ["Actual Purchase Price Amount","Contract Purchase Price Amount"]`n  depends_on_ids: ["ops.purchase.price.actual.amount","ops.purchase.price.contract.amount"]
  business:
    purpose: "Relative variance between actual purchase price and contracted price."
    definition: "(Actual Price - Contract Price) / Contract Price"
    grain_scope: "PO line level; aggregated monthly by supplier/category."
    unit_format: "% (1 decimal)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "PPV bounded within reasonable range (e.g., [-100%; +200%])"
      - "Reconciles to contract price list and invoice data within +/- 0.5 pp"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.ppv.amount"
  kpi_key: "PPV Amount"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "PPV Amount"
    description: "(Actual Price - Contract Price) x Quantity"
    formatString: "€ #,0.00"
    verified: false`n  depends_on: ["Actual Purchase Price Amount","Contract Purchase Price Amount","Purchase Quantity"]`n  depends_on_ids: ["ops.purchase.price.actual.amount","ops.purchase.price.contract.amount","ops.purchase.units.qty"]
  business:
    purpose: "Absolute variance between actual price paid and contracted price for purchased quantity."
    definition: "(Actual Price - Contract Price) x Quantity"
    grain_scope: "PO line level; aggregated monthly by supplier/category."
    unit_format: "EUR (2 decimals)"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to invoice/PO data within +/- 1 %"
      - "Currency consistent with procurement ledger"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.contract.compliance.pct"
  kpi_key: "Contract Compliance %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Contract Compliance %"
    description: "Purchases at agreed price / Total purchases"
    formatString: "0.0 %"
    verified: false
  business:
        purpose: "Share of purchases placed at contracted terms (price/conditions)."`n    definition: "Purchases at agreed price / Total purchases"`n    grain_scope: "PO line level; aggregated monthly by supplier/category."`n    unit_format: "% (1 decimal)"`n
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Bounded between 0% and 100%"`n      - "Reconciles to contract master and invoice lines within +/- 1 pp"`n    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.replenishment.adherence.pct"
  kpi_key: "Replenishment Adherence %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Replenishment Adherence %"
    description: "Actual Orders / Target Orders (on time/quantity)"
    formatString: "0.0 %"
    verified: false
  business:
        purpose: "Adherence of replenishment execution to plan (timing and quantity)."`n    definition: "Actual Orders / Target Orders (on time/quantity)"`n    grain_scope: "SKU/Location planning level; aggregated weekly/monthly."`n    unit_format: "% (1 decimal)"`n
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Bounded between 0% and 100%"`n      - "Cross-check vs planning system exceptions within +/- 1 pp"`n    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.order_accuracy.pct"
  kpi_key: "Order Accuracy %"
  kpi_type: "diagnostic"
  domain_tag: ["Operational Efficiency"]
  calc_type: rate
  technical:
    dax_name: "Order Accuracy %"
    description: "Orders fulfilled correctly / Total Orders"
    formatString: "0.0 %"
    verified: false`n  depends_on: ["Correct Orders Count","Total Orders Count"]`n  depends_on_ids: ["ops.orders.correct.count","ops.orders.total.count"]
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```
```yaml
- kpi_id: "ops.machine_downtime.pct"
  kpi_key: "Machine Downtime %"
  kpi_type: "supporting"
  strategic_ref: "OEE %"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  use_case_ref: ["OPS-003"]
  depends_on: ["Downtime Hours","Planned Hours"]
  depends_on_ids: ["ops.downtime.hours","ops.planned.hours"]
  calc_type: ratio
  refresh: daily
  status: Active
  business:
    purpose: "Measures proportion of time equipment is not running."
    definition: "Downtime Hours / Planned Hours"
    grain_scope: "Machine level."
    unit_format: "% (1 decimal)"
    interpretation: "High downtime reduces efficiency and throughput."
  technical:
    dax_name: "Machine Downtime %"
    dax_expression: "DIVIDE([Downtime Hours],[Planned Hours])"
    lineage: ["fact_production.DowntimeHours","fact_production.PlannedHours"]
    source_grain: "machine_log"
    source_column_ref: ["fact_production.downtime_hrs","fact_production.planned_hrs"]
    source_system: "MES"
    verified: true
  governance:
    business_owner: "Head of Maintenance"
    data_owner: "Operations Data Team"
    steward: "Maintenance Planner"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "Downtime % <= 100 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_id: "ops.produced_units.qty"
  kpi_key: "Produced Units Qty"
  kpi_type: "supporting"
  strategic_ref: "Process Cost per Unit"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  use_case_ref: ["OPS-002"]
  depends_on: []
  calc_type: count
  refresh: daily
  status: Active
  business:
    purpose: "Number of finished goods units produced."
    definition: "Sum of all finished units confirmed by production system."
    grain_scope: "Machine and shift level."
    unit_format: "pcs"
    interpretation: "Primary production volume metric."
  technical:
    dax_name: "Produced Units Qty"
    dax_expression: "SUM(fact_production[Produced Units Qty])"
  depends_on_ids: []
    lineage: ["fact_production.ProducedUnits"]
    source_grain: "production_line"
    source_column_ref: ["fact_production.produced_qty"]
    source_system: "MES"
    verified: true
  governance:
    business_owner: "Head of Production"
    data_owner: "Manufacturing BI"
    steward: "Production Planner"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Produced Units >= 0"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 1.00
    lineage_verified: true
    copilot_ready: true
```

---

## 4. Governance Summary
| Metric | Value |
|--------|--------|
| **Total KPIs (Efficiency)** | 31 |
| **Completeness Score (avg)** | 0.97 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Quarterly |
| **Business Owner** | Head of Operations |
| **Data Owner** | Manufacturing BI |
| **Steward** | Operations Analyst |
| **Validation Process** | Automated |

---

Last updated: 04.11.2025



```yaml
- kpi_id: "ops.working_capital.dso.days"
  kpi_key: "DSO (Days)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "DSO (Days)"
    description: "(Accounts Receivable / Net Sales) x Days in Period"
    formatString: "0"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.working_capital.dio.days"
  kpi_key: "DIO (Days)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "DIO (Days)"
    description: "(Inventory / COGS) x Days in Period"
    formatString: "0"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.working_capital.dpo.days"
  kpi_key: "DPO (Days)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "DPO (Days)"
    description: "(Accounts Payable / COGS) x Days in Period"
    formatString: "0"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "ops.working_capital.ccc.delta_days"
  kpi_key: "Δ CCC (Days)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Δ CCC (Days)"
    description: "CCC (Days) - Baseline (Plan or LY)"
    formatString: "0"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```





```yaml
- kpi_id: "ops.orders.total.count"
  kpi_key: "Total Orders Count"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "Total Orders Count"
    description: "Total number of orders in period"
    formatString: "0"
    verified: false
  business:
    purpose: "Denominator for order accuracy and fulfillment KPIs."
    definition: "Count of orders"
    grain_scope: "Order level; aggregated weekly/monthly."
    unit_format: "count"
  governance:
    business_owner: "Head of Order Management"
    data_owner: "Operations BI"
    steward: "Order Specialist"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to OMS within +/- 1 count"
```
```yaml
- kpi_id: "ops.orders.correct.count"
  kpi_key: "Correct Orders Count"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "Correct Orders Count"
    description: "Orders fulfilled correctly"
    formatString: "0"
    verified: false
  business:
    purpose: "Numerator for order accuracy KPI."
    definition: "Count of orders fulfilled without errors"
    grain_scope: "Order level; aggregated weekly/monthly."
    unit_format: "count"
  governance:
    business_owner: "Head of Order Management"
    data_owner: "Operations BI"
    steward: "Order Specialist"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to OMS quality flags within +/- 1 count"
```
```yaml
- kpi_id: "ops.deliveries.total.count"
  kpi_key: "Total Deliveries Count"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "Total Deliveries Count"
    description: "Total deliveries in period"
    formatString: "0"
    verified: false
  business:
    purpose: "Denominator for OTIF KPI."
    definition: "Count of deliveries"
    grain_scope: "Shipment/delivery level; aggregated weekly/monthly."
    unit_format: "count"
  governance:
    business_owner: "Head of Logistics"
    data_owner: "Operations BI"
    steward: "Logistics Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to WMS/TMS within +/- 1 count"
```
```yaml
- kpi_id: "ops.deliveries.otif.count"
  kpi_key: "OTIF Deliveries Count"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "OTIF Deliveries Count"
    description: "Deliveries on-time and in-full"
    formatString: "0"
    verified: false
  business:
    purpose: "Numerator for OTIF KPI."
    definition: "Count of deliveries meeting OTIF criteria"
    grain_scope: "Shipment/delivery level; aggregated weekly/monthly."
    unit_format: "count"
  governance:
    business_owner: "Head of Logistics"
    data_owner: "Operations BI"
    steward: "Logistics Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to WMS/TMS within +/- 1 count"
```
```yaml
- kpi_id: "ops.purchases.at_contract.amount"
  kpi_key: "Purchases at Contract Amount"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Purchases at Contract Amount"
    description: "Purchases at contracted price"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "Spend against contracted terms for compliance KPI."
    definition: "Sum of purchase amounts at contract price"
    grain_scope: "PO line level; aggregated monthly."
    unit_format: "EUR (2 decimals)"
  governance:
    business_owner: "Head of Procurement"
    data_owner: "Procurement BI"
    steward: "Procurement Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to PO/invoice data within +/- 1 %"
```
```yaml
- kpi_id: "ops.purchases.total.amount"
  kpi_key: "Total Purchases Amount"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Total Purchases Amount"
    description: "Total purchase spend"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "Denominator for contract compliance KPI."
    definition: "Sum of all purchase amounts"
    grain_scope: "PO line level; aggregated monthly."
    unit_format: "EUR (2 decimals)"
  governance:
    business_owner: "Head of Procurement"
    data_owner: "Procurement BI"
    steward: "Procurement Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to PO/invoice data within +/- 1 %"
```
```yaml
- kpi_id: "ops.purchase.price.actual.amount"
  kpi_key: "Actual Purchase Price Amount"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Actual Purchase Price Amount"
    description: "Actual paid unit price"
    formatString: "EUR #,0.0000"
    verified: false
  business:
    purpose: "Actual unit price input for PPV."
    definition: "Average actual price per unit"
    grain_scope: "PO line level; aggregated monthly."
    unit_format: "EUR (4 decimals)"
  governance:
    business_owner: "Head of Procurement"
    data_owner: "Procurement BI"
    steward: "Procurement Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Currency and unit alignment with contract"
```
```yaml
- kpi_id: "ops.purchase.price.contract.amount"
  kpi_key: "Contract Purchase Price Amount"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Contract Purchase Price Amount"
    description: "Contracted unit price"
    formatString: "EUR #,0.0000"
    verified: false
  business:
    purpose: "Contract price input for PPV."
    definition: "Contract price per unit"
    grain_scope: "PO line level; aggregated monthly."
    unit_format: "EUR (4 decimals)"
  governance:
    business_owner: "Head of Procurement"
    data_owner: "Procurement BI"
    steward: "Procurement Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Currency and unit alignment with contract"
```
```yaml
- kpi_id: "ops.purchase.units.qty"
  kpi_key: "Purchase Quantity"
  kpi_type: "supporting"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  calc_type: count
  technical:
    dax_name: "Purchase Quantity"
    description: "Purchased units"
    formatString: "0"
    verified: false
  business:
    purpose: "Quantity input for PPV amount."
    definition: "Sum of purchased units"
    grain_scope: "PO line level; aggregated monthly."
    unit_format: "qty"
  governance:
    business_owner: "Head of Procurement"
    data_owner: "Procurement BI"
    steward: "Procurement Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Reconciles to PO goods receipt within +/- 0.5 %"
```
