# Measure Dictionary - Operations

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

## Aggregation Method Conventions

All measures must declare an `aggregation_method` in their `expression` block. Conventions:

| Method | Use for |
|--------|---------|
| `sum` | Additive facts (units, minutes, costs) — safe to aggregate across all dimensions |
| `average` | Per-unit or per-asset averages (MTBF, MTTR, cycle time) — dimension-sensitive |
| `last_value` | Not applicable in operations domain (no balance measures) |
| `ratio` | Rate measures (%, OEE, FPY) — must be recomputed from components when filter changes |
| `count` | Event counts (failures, orders) — additive |

**Rule:** OEE, FPY, Scrap Rate, and all percentage measures must never be averaged. Always re-derive from summed time/unit components.

## Logical Expression Convention

`expression.logical` contains tool-agnostic business-logic pseudocode. Tool-specific DAX/SQL lives in `products/fabric/`.

Format: `MEASURE_NAME = <pseudocode using column references from operations data contract>`

```yaml
- measure_name: OEE %
  is_kpi_measure: true
  kpi_id_ref: ops.oee.pct
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    aggregation_method: ratio
    logical: OEE = Availability % * Performance % * Quality % = (SUM(Run Time) / SUM(Planned Time)) * (SUM(Output Units) / (SUM(Planned Time) * Standard Rate)) * (SUM(Good Units) / SUM(Output Units))
  documentation:
    description: Overall equipment effectiveness combining availability, performance, and quality.
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_ops[Run Time Minutes], fact_ops[Planned Time Minutes], fact_ops[Output Units], fact_ops[Good Units].

      QA: Ensure consistent time base; flags for downtime types; DIVIDE guards; replace Perf divisor with theoretical output when available.

      '
  dependencies:
    columns:
    - fact_ops[Run Time Minutes]
    - fact_ops[Planned Time Minutes]
    - fact_ops[Output Units]
    - fact_ops[Good Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Availability %
  is_kpi_measure: true
  kpi_id_ref: ops.availability.pct
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    aggregation_method: ratio
    logical: Availability = SUM(fact_ops[Run Time Minutes]) / SUM(fact_ops[Planned Time Minutes])
  documentation:
    description: 'Uptime control: Run Time / Planned Production Time.'
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_ops[Run Time Minutes], fact_ops[Planned Time Minutes].

      QA: Planned Time > 0; consistent shift definitions.

      '
  dependencies:
    columns:
    - fact_ops[Run Time Minutes]
    - fact_ops[Planned Time Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Performance %
  is_kpi_measure: true
  kpi_id_ref: ops.performance.pct
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    logical: Performance % = Actual output / Theoretical maximum output
    aggregation_method: ratio
  documentation:
    description: 'Speed vs standard: Actual Output / Theoretical Output.'
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_ops[Output Units], standards.

      QA: Standards maintained; guard against zero standard.

      '
  dependencies:
    columns:
    - fact_ops[Output Units]
    measures:
    - '[Standard Output]'
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Planned Hours
  is_kpi_measure: true
  kpi_id_ref: ops.planned.hours
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    logical: Planned Hours = Sum of planned production hours
    aggregation_method: ratio
  documentation:
    description: Scheduled production time allocated for machines/lines.
    notes: 'Grain: machine/line level per shift/day.

      Unit: hours.

      Lineage: fact_ops[Planned Hours].

      QA: Non-negative; reconcile to planning system within +/- 0.1 h.

      '
  dependencies:
    columns:
    - fact_ops[Planned Hours]
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 27.01.2026

- measure_name: Quality %
  is_kpi_measure: true
  kpi_id_ref: ops.quality.pct
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    logical: Quality % = Good units / Total units
    aggregation_method: ratio
  documentation:
    description: 'First pass yield: Good Units / Total Units.'
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_ops[Good Units], fact_ops[Output Units].

      QA: Total Units > 0; align with scrap/rework capture.

      '
  dependencies:
    columns:
    - fact_ops[Good Units]
    - fact_ops[Output Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Throughput Units
  is_kpi_measure: true
  kpi_id_ref: ops.throughput.units
  semantic_model: Operations_SemanticModel
  display_folder: 02_Throughput
  category: KPI
  expression:
    logical: Throughput Units = Sum of produced units in the period.
    aggregation_method: sum
  documentation:
    description: Volume output over time.
    notes: 'Grain: line_day. Unit: qty.

      Lineage: fact_ops[Output Units].

      QA: Units consistent with quality measures.

      '
  dependencies:
    columns:
    - fact_ops[Output Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Downtime %
  is_kpi_measure: true
  kpi_id_ref: ops.downtime.pct
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: KPI
  expression:
    logical: Downtime % = Downtime Minutes / Planned Time Minutes.
    aggregation_method: ratio
  documentation:
    description: 'Loss share: Downtime / Planned Production Time.'
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_ops[Downtime Minutes], fact_ops[Planned Time Minutes].

      QA: Distinguish planned vs unplanned; Planned Time > 0.

      '
  dependencies:
    columns:
    - fact_ops[Downtime Minutes]
    - fact_ops[Planned Time Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Run Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: Base
  expression:
    logical: Run Time Minutes = SUM(fact_ops[Run Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total run time in minutes.
    notes: 'Source: fact_ops[Run Time Minutes].'
  dependencies:
    columns:
    - fact_ops[Run Time Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Downtime Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: Base
  expression:
    logical: Downtime Minutes = SUM(fact_ops[Downtime Minutes])
    aggregation_method: sum
  documentation:
    description: Total downtime minutes (planned + unplanned if not split).
    notes: 'Source: fact_ops[Downtime Minutes].'
  dependencies:
    columns:
    - fact_ops[Downtime Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Unplanned Downtime Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: Base
  expression:
    logical: Unplanned Downtime Minutes = SUM(fact_ops[Unplanned Downtime Minutes])
    aggregation_method: sum
  documentation:
    description: Minutes of production time lost to unscheduled breakdowns and equipment failures.
    notes: 'Source: fact_ops[Unplanned Downtime].'
  dependencies:
    columns:
    - fact_ops[Unplanned Downtime Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Standard Output Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 02_Throughput
  category: Base
  expression:
    logical: Standard Output Units = SUMX ( fact_ops, fact_ops[Planned Time Minutes] * fact_ops[Standard Rate Units Per Minute] )
    aggregation_method: sum
  documentation:
    description: Theoretical output based on planned time and standard rate.
    notes: 'Source: fact_ops planned time and standard rate.'
  dependencies:
    columns:
    - fact_ops[Planned Time Minutes]
    - fact_ops[Standard Rate Units Per Minute]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Failure Count
  is_kpi_measure: true
  kpi_id_ref: ops.failure.count
  semantic_model: Operations_SemanticModel
  display_folder: 04_Reliability
  category: KPI
  expression:
    logical: Failure Count = COUNT ( fact_ops_failures[Failure Start DateTime] )
    aggregation_method: count
  documentation:
    description: Count of recorded equipment or process failure events.
    notes: 'Grain: failure_event. Unit: count. Source: fact_ops_failures (one row per failure event), matching the ops.failure.count lineage. Feeds MTBF/MTTR reliability measures. QA: de-duplicate failure events; confirm consistent failure taxonomy.'
  dependencies:
    columns:
    - fact_ops_failures[Failure Start DateTime]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: MTBF (hours)
  is_kpi_measure: true
  kpi_id_ref: ops.mtbf.hours
  semantic_model: Operations_SemanticModel
  display_folder: 04_Reliability
  category: KPI
  expression:
    logical: MTBF (hours) = Operating Time Hours / Number of Failures.
    aggregation_method: ratio
  documentation:
    description: Mean time between failures.
    notes: 'Grain: asset. Unit: hours.

      Lineage: fact_ops_failures[Failure Start/End].

      QA: Accurate failure timestamps; exclude planned stops.

      '
  dependencies:
    columns:
    - fact_ops_failures[Failure Start]
    - fact_ops_failures[Failure End]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: MTTR (hours)
  is_kpi_measure: true
  kpi_id_ref: ops.mttr.hours
  semantic_model: Operations_SemanticModel
  display_folder: 04_Reliability
  category: KPI
  expression:
    logical: MTTR (hours) = Total Repair Time Hours / Number of Failures.
    aggregation_method: ratio
  documentation:
    description: Mean time to repair.
    notes: 'Grain: asset. Unit: hours.

      Lineage: fact_ops_failures[Repair Duration].

      QA: Repair duration capture consistent; exclude waiting times if needed.

      '
  dependencies:
    columns:
    - fact_ops_failures[Repair Duration]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Unplanned Downtime %
  is_kpi_measure: true
  kpi_id_ref: ops.downtime.unplanned.pct
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: KPI
  expression:
    logical: Unplanned Downtime % = Unplanned Downtime Minutes / Planned Time Minutes.
    aggregation_method: ratio
  documentation:
    description: Unplanned downtime share of planned time.
    notes: 'Grain: asset_day. Unit: %.

      Lineage: fact_ops[Unplanned Downtime Minutes], fact_ops[Planned Time Minutes].

      QA: Correct tagging of unplanned events; Planned Time > 0.

      '
  dependencies:
    columns:
    - fact_ops[Unplanned Downtime Minutes]
    - fact_ops[Planned Time Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Spare Parts Stockout %
  is_kpi_measure: true
  kpi_id_ref: ops.spare_parts.stockout.pct
  semantic_model: Operations_SemanticModel
  display_folder: 05_Maintenance
  category: KPI
  expression:
    logical: Spare Parts Stockout % = Stockout Events / Total Parts Requests.
    aggregation_method: ratio
  documentation:
    description: Maintenance readiness via stockout rate for parts.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_maintenance[Parts Stockout Flag], fact_maintenance[Orders].

      QA: Orders denominator > 0; flag accuracy.

      '
  dependencies:
    columns:
    - fact_maintenance[Parts Stockout Flag]
    - fact_maintenance[Orders]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: PM Compliance %
  is_kpi_measure: true
  kpi_id_ref: ops.pm_compliance.pct
  semantic_model: Operations_SemanticModel
  display_folder: 05_Maintenance
  category: KPI
  expression:
    logical: PM Compliance % = Completed PM Orders / Planned PM Orders.
    aggregation_method: ratio
  documentation:
    description: 'Preventive maintenance discipline: on-time PM orders / planned PM orders.'
    notes: 'Grain: month. Unit: %.

      Lineage: fact_maintenance[PM On Time], fact_maintenance[PM Planned].

      QA: PM Planned > 0; on-time flag logic consistent.

      '
  dependencies:
    columns:
    - fact_maintenance[PM On Time]
    - fact_maintenance[PM Planned]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: First Pass Yield %
  is_kpi_measure: true
  kpi_id_ref: quality.fpy.pct
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: KPI
  expression:
    aggregation_method: ratio
    logical: FPY = SUM(fact_quality[Good Units]) / SUM(fact_quality[Total Units])
  documentation:
    description: Good units / total units at first pass.
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_quality[Good Units], fact_quality[Total Units].

      QA: Total Units > 0; align with scrap/rework metrics.

      '
  dependencies:
    columns:
    - fact_quality[Good Units]
    - fact_quality[Total Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Scrap Rate %
  is_kpi_measure: true
  kpi_id_ref: quality.scrap.pct
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: KPI
  expression:
    logical: Scrap Rate % = Scrap Units / Total Units.
    aggregation_method: ratio
  documentation:
    description: Scrap units / total units.
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_quality[Scrap Units], fact_quality[Total Units].

      QA: Total Units > 0; scrap capture consistent.

      '
  dependencies:
    columns:
    - fact_quality[Scrap Units]
    - fact_quality[Total Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Rework Rate %
  is_kpi_measure: true
  kpi_id_ref: quality.rework.pct
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: KPI
  expression:
    logical: Rework Rate % = Reworked Units / Total Units.
    aggregation_method: ratio
  documentation:
    description: Reworked units / total units.
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_quality[Rework Units], fact_quality[Total Units].

      QA: Total Units > 0; rework capture consistent.

      '
  dependencies:
    columns:
    - fact_quality[Rework Units]
    - fact_quality[Total Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Total Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: Base
  expression:
    logical: Total Units = SUM(fact_quality[Total Units])
    aggregation_method: sum
  documentation:
    description: Total produced units in the selected context.
    notes: 'Source: fact_quality[Total Units].'
  dependencies:
    columns:
    - fact_quality[Total Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Good Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: Base
  expression:
    logical: Good Units = SUM(fact_quality[Good Units])
    aggregation_method: sum
  documentation:
    description: Conforming units produced.
    notes: 'Source: fact_quality[Good Units].'
  dependencies:
    columns:
    - fact_quality[Good Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Scrap Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: Base
  expression:
    logical: Scrap Units = SUM(fact_quality[Scrap Units])
    aggregation_method: sum
  documentation:
    description: Scrapped units in the selected context.
    notes: 'Source: fact_quality[Scrap Units].'
  dependencies:
    columns:
    - fact_quality[Scrap Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Rework Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: Base
  expression:
    logical: Rework Units = SUM(fact_quality[Rework Units])
    aggregation_method: sum
  documentation:
    description: Reworked units in the selected context.
    notes: 'Source: fact_quality[Rework Units].'
  dependencies:
    columns:
    - fact_quality[Rework Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Cost of Poor Quality
  is_kpi_measure: true
  kpi_id_ref: quality.copq.amount
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: KPI
  expression:
    logical: Cost of Poor Quality = Sum of cost impacts for quality failures in period.
    aggregation_method: sum
  documentation:
    description: Financial impact from scrap, rework, and warranty/complaint costs.
    notes: 'Grain: month. Unit: EUR.

      Lineage: fact_quality_costs[COPQ], fact_quality.

      QA: Components of COPQ documented; no double-counting.

      '
  dependencies:
    columns:
    - fact_quality_costs[COPQ]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Complaint Rate %
  is_kpi_measure: true
  kpi_id_ref: quality.complaint.pct
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: KPI
  expression:
    logical: Complaint Rate % = Complaint Count / Units Shipped.
    aggregation_method: ratio
  documentation:
    description: Complaints / units shipped.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_complaints[Complaints], fact_shipments[Units].

      QA: Units shipped > 0; complaint capture complete.

      '
  dependencies:
    columns:
    - fact_complaints[Complaints]
    - fact_shipments[Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Complaint Count
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: Base
  expression:
    logical: Complaint Count = COUNTROWS ( fact_experience )
    aggregation_method: count
  documentation:
    description: Number of complaints in the selected context.
    notes: 'Source: fact_complaints[Complaint Count].'
  dependencies:
    columns:
    - fact_complaints[Complaint Count]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Shipped Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: Base
  expression:
    logical: Shipped Units = SUM(fact_shipments[Shipped Units])
    aggregation_method: sum
  documentation:
    description: Units shipped used as denominator for complaint rate.
    notes: 'Source: fact_shipments[Shipped Units].'
  dependencies:
    columns:
    - fact_shipments[Shipped Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Defect Density
  is_kpi_measure: true
  kpi_id_ref: quality.defect_density
  semantic_model: Operations_SemanticModel
  display_folder: 06_Quality
  category: KPI
  expression:
    logical: Defect Density = (Defect Count / Total Units) * 1,000.
    aggregation_method: sum
  documentation:
    description: Defects per 1k units.
    notes: 'Grain: line_day. Unit: defects per 1k units.

      Lineage: fact_quality[Defect Count], fact_quality[Units].

      QA: Units > 0; consistent counting rules.

      '
  dependencies:
    columns:
    - fact_quality[Defect Count]
    - fact_quality[Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Planned Time
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: Base
  expression:
    logical: Planned Time = SUM(fact_ops[Planned Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total planned production time in minutes.
    notes: 'Source: fact_ops[Planned Time Minutes].'
  dependencies:
    columns:
    - fact_ops[Planned Time Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Run Time
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 03_Downtime
  category: Base
  expression:
    logical: Run Time = SUM(fact_ops[Run Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total run time in minutes.
    notes: 'Source: fact_ops[Run Time Minutes].'
  dependencies:
    columns:
    - fact_ops[Run Time Minutes]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Output Units
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: Base
  expression:
    logical: Output Units = SUM(fact_ops[Output Units])
    aggregation_method: sum
  documentation:
    description: Total good units produced in the period.
    notes: 'Source: fact_ops[Output Units].'
  dependencies:
    columns:
    - fact_ops[Output Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Defect Count
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 04_Quality
  category: Base
  expression:
    logical: Defect Count = SUM(fact_quality[Defect Count])
    aggregation_method: count
  documentation:
    description: Number of defective units detected during quality inspection.
    notes: 'Source: fact_quality[Defect Count].'
  dependencies:
    columns:
    - fact_quality[Defect Count]
  governance:
    owner: Operations Analytics
    status: active
    version: v1.2
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Planned Output Units
  is_kpi_measure: true
  kpi_id_ref: ops.planned_output.units
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    logical: Planned Output Units = Sum of planned output units for the period.
    aggregation_method: sum
  documentation:
    description: Scheduled target output for the period at standard run rate.
    notes: 'Grain: line_day. Unit: units.

      Lineage: fact_ops[Planned Output Units].

      QA: Align planning calendar with actuals.

      '
  dependencies:
    columns:
    - fact_ops[Planned Output Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Preventive Maintenance Task Count
  is_kpi_measure: true
  kpi_id_ref: ops.pm.task.count
  semantic_model: Operations_SemanticModel
  display_folder: 01_Ops
  category: KPI
  expression:
    logical: Preventive Maintenance Task Count = Count of PM tasks in the period.
    aggregation_method: count
  documentation:
    description: Count of preventive maintenance tasks.
    notes: 'Grain: asset_day. Unit: count.

      Lineage: fact_maintenance[PM Task Count].

      QA: Distinguish completed vs scheduled if needed.

      '
  dependencies:
    columns:
    - fact_maintenance[PM Task Count]
  governance:
    owner: Operations Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Quality Defect Rate %
  is_kpi_measure: true
  kpi_id_ref: ops.quality.defect_rate.pct
  semantic_model: Operations_SemanticModel
  display_folder: 04_Quality
  category: KPI
  expression:
    logical: Quality Defect Rate % = Defective Units / Total Produced Units.
    aggregation_method: ratio
  documentation:
    description: Defect count divided by total output units.
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_quality[Defect Count], fact_ops[Output Units].

      QA: Output Units > 0; ensure defect definition consistent.

      '
  dependencies:
    columns:
    - fact_quality[Defect Count]
    - fact_ops[Output Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Safety Incident Count
  is_kpi_measure: true
  kpi_id_ref: ops.safety.incident.count
  category: KPI
  expression:
    logical: Safety Incident Count = Count of recorded safety incidents in the selected period.
    aggregation_method: count
  dependencies:
    columns:
    - fact_safety[Incident ID]
  governance:
    status: active
    version: v0.1
    owner: Operations Analytics
    last_review: 2026-03-27
    review_due: 2027-03-31
  semantic_model: Operations_SemanticModel
  display_folder: 05_Safety
  documentation:
    description: Count of safety incidents in the period.
    notes: 'Grain: site_day. Unit: count.

      Lineage: fact_safety[Incident Count].

      QA: Harmonize incident classification and severity.

      '

- measure_name: Yield %
  is_kpi_measure: true
  kpi_id_ref: ops.yield.pct
  semantic_model: Operations_SemanticModel
  display_folder: 04_Quality
  category: KPI
  expression:
    logical: Yield % = Good Units / Total Units Produced.
    aggregation_method: ratio
  documentation:
    description: Good units divided by total output.
    notes: 'Grain: line_day. Unit: %.

      Lineage: fact_ops[Good Units], fact_ops[Output Units].

      QA: Output Units > 0; align good vs total unit definitions.

      '
  dependencies:
    columns:
    - fact_ops[Good Units]
    - fact_ops[Output Units]
  governance:
    owner: Operations Analytics
    status: active
    version: v0.1
    last_review: 2026-03-27
    review_due: 2027-03-31

- measure_name: Overall Equipment Effectiveness (OEE) %
  is_kpi_measure: true
  kpi_id_ref: ops.oee.pct
  semantic_model: Operations_SemanticModel
  display_folder: 01_Manufacturing
  category: KPI
  expression:
    logical: Overall Equipment Effectiveness (OEE) % = [OEE %]
    aggregation_method: custom
  documentation:
    description: Display alias for OEE %. Composite measure combining availability, performance, and quality in manufacturing.
    notes: 'Grain: line_day. Unit: %. Lineage: [OEE %]. QA: Composite of Availability %, Performance %, Quality %.'
  dependencies:
    measures:
    - '[OEE %]'
  governance:
    owner: Operations BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Sales Units (OPS)
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Operations_SemanticModel
  display_folder: 03_Quality
  category: Base
  expression:
    logical: Sales Units (OPS) = SUM ( fact_ops[Output Units] )
    aggregation_method: sum
  documentation:
    description: Output units volume from operations — Operations domain view.
    notes: 'Grain: line_day. Unit: units. Lineage: fact_ops[Output Units].'
  dependencies:
    columns:
    - fact_ops[Output Units]
  governance:
    owner: Operations BI
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
    description: Number of action codes with a recorded outcome — Operations cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Operations BI
  semantic_model: Operations_SemanticModel

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
    description: Percentage of executed actions with a confirmed achieved outcome — Operations cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Operations BI
  semantic_model: Operations_SemanticModel

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
    description: Average days between action execution and outcome confirmation — Operations cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[days_to_outcome]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Operations BI
  semantic_model: Operations_SemanticModel

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
    description: Average ROI of executed actions — Operations cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[cost_to_execute]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Operations BI
  semantic_model: Operations_SemanticModel

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
    description: Average EUR impact per achieved action execution — Operations cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Operations BI
  semantic_model: Operations_SemanticModel
```

