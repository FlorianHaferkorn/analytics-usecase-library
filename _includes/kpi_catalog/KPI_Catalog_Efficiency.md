# KPI Catalog - Efficiency

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "ops.oee.pct"`n  kpi_key: "Overall Equipment Effectiveness (OEE) %"
  kpi_type: "strategic"
  strategic_ref: "Overall Equipment Effectiveness (OEE) %"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  use_case_ref: ["OPS-001"]
  depends_on: ["Availability %","Performance %","Quality %"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures manufacturing performance combining availability, performance, and quality."
    definition: "Availability % * Performance % * Quality %"
    grain_scope: "Production line; aggregated monthly."
    unit_format: "% (1 decimal)"
    interpretation: "Higher OEE <= 100 %"
      - "All subcomponents validated from MES feed"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_id: "ops.process.cost_per_unit.amount"`n  kpi_key: "Process Cost per Unit"
  kpi_type: "strategic"
  strategic_ref: "Process Cost per Unit"
  impact_dimension: "Efficiency"
  domain_tag: ["Operational Efficiency"]
  use_case_ref: ["OPS-002"]
  depends_on: ["Total Process Cost Amount","Produced Units Qty"]
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
    verified: false
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
    verified: false
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
    verified: false
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
    verified: false
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
    verified: false
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
```
