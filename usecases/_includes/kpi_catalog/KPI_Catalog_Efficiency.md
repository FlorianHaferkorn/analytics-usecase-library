# KPI Catalog – Efficiency

---

## 1. Strategic KPIs
```yaml
- kpi_key: "Overall Equipment Effectiveness (OEE) %"
  kpi_type: "strategic"
  strategic_ref: "Overall Equipment Effectiveness (OEE) %"
  impact_dimension: "Efficiency"
  domain_tag: ["Operations"]
  use_case_ref: ["OPS-001"]
  depends_on: ["Availability %","Performance %","Quality %"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures manufacturing performance combining availability, performance, and quality."
    definition: "Availability % × Performance % × Quality %"
    grain_scope: "Production line; aggregated monthly."
    unit_format: "% (1 decimal)"
    interpretation: "Higher OEE indicates more efficient equipment utilization."
  technical:
    dax_name: "OEE %"
    dax_expression: "[Availability %]*[Performance %]*[Quality %]"
    lineage: ["fact_production.Availability","fact_production.Performance","fact_production.Quality"]
    source_grain: "production_line"
    source_column_ref: ["fact_production.availability_pct","fact_production.performance_pct","fact_production.quality_pct"]
    source_system: "MES"
    verified: true
  governance:
    business_owner: "Head of Operations"
    data_owner: "Manufacturing BI"
    steward: "Operations Analyst"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "OEE ≤ 100 %"
      - "All subcomponents validated from MES feed"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Process Cost per Unit"
  kpi_type: "strategic"
  strategic_ref: "Process Cost per Unit"
  impact_dimension: "Efficiency"
  domain_tag: ["Operations"]
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
      - "Reconcile with manufacturing ledger ±1 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
```

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_key: "Machine Downtime %"
  kpi_type: "supporting"
  strategic_ref: "OEE %"
  impact_dimension: "Efficiency"
  domain_tag: ["Operations"]
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
      - "Downtime % ≤ 100 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_key: "Produced Units Qty"
  kpi_type: "base"
  strategic_ref: "Process Cost per Unit"
  impact_dimension: "Efficiency"
  domain_tag: ["Operations"]
  use_case_ref: ["OPS-002"]
  depends_on: []
  calc_type: qty
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
      - "Produced Units ≥ 0"
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

_Last updated: 12.10.2025_
