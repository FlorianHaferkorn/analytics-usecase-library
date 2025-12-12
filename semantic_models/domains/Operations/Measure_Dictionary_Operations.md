# Measure Dictionary - Operations

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "OEE %"
  is_kpi_measure: true
  kpi_id_ref: "ops.oee.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "01_Ops"
  category: "KPI"
  expression:
    dax: "/* TODO: implement OEE % (Availability * Performance * Quality) */"
    formatString: "0.0%"
  documentation:
    description: "Overall equipment effectiveness combining availability, performance, and quality."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Run Time], fact_ops[Planned Time], fact_ops[Output], fact_quality[Good Units], fact_quality[Total Units].
      QA: Ensure consistent time base; flags for downtime types; DIVIDE guards.
  dependencies:
    columns:
      - "fact_ops[Run Time]"
      - "fact_ops[Planned Time]"
      - "fact_ops[Output]"
      - "fact_quality[Good Units]"
      - "fact_quality[Total Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Availability %"
  is_kpi_measure: true
  kpi_id_ref: "ops.availability.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "01_Ops"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Availability % */"
    formatString: "0.0%"
  documentation:
    description: "Uptime control: Run Time / Planned Production Time."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Run Time], fact_ops[Planned Time].
      QA: Planned Time > 0; consistent shift definitions.
  dependencies:
    columns:
      - "fact_ops[Run Time]"
      - "fact_ops[Planned Time]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Performance %"
  is_kpi_measure: true
  kpi_id_ref: "ops.performance.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "01_Ops"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Performance % */"
    formatString: "0.0%"
  documentation:
    description: "Speed vs standard: Actual Output / Theoretical Output."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Output], standards.
      QA: Standards maintained; guard against zero standard.
  dependencies:
    columns:
      - "fact_ops[Output]"
    measures:
      - "[Standard Output]"   # placeholder if modeled as measure
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Quality %"
  is_kpi_measure: true
  kpi_id_ref: "ops.quality.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "01_Ops"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Quality % */"
    formatString: "0.0%"
  documentation:
    description: "First pass yield: Good Units / Total Units."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_quality[Good Units], fact_quality[Total Units].
      QA: Total Units > 0; align with scrap/rework capture.
  dependencies:
    columns:
      - "fact_quality[Good Units]"
      - "fact_quality[Total Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Throughput Units"
  is_kpi_measure: true
  kpi_id_ref: "ops.throughput.units"
  semantic_model: "Operations_SemanticModel"
  display_folder: "02_Throughput"
  category: "KPI"
  expression:
    dax: "SUM(fact_ops[Produced Units])"
    formatString: "#,0"
  documentation:
    description: "Volume output over time."
    notes: |
      Grain: line_day. Unit: qty.
      Lineage: fact_ops[Produced Units].
      QA: Units consistent with quality measures.
  dependencies:
    columns:
      - "fact_ops[Produced Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Downtime %"
  is_kpi_measure: true
  kpi_id_ref: "ops.downtime.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Downtime % */"
    formatString: "0.0%"
  documentation:
    description: "Loss share: Downtime / Planned Production Time."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Downtime], fact_ops[Planned Time].
      QA: Distinguish planned vs unplanned; Planned Time > 0.
  dependencies:
    columns:
      - "fact_ops[Downtime]"
      - "fact_ops[Planned Time]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "MTBF (hours)"
  is_kpi_measure: true
  kpi_id_ref: "ops.mtbf.hours"
  semantic_model: "Operations_SemanticModel"
  display_folder: "04_Reliability"
  category: "KPI"
  expression:
    dax: "/* TODO: implement MTBF */"
    formatString: "0.0"
  documentation:
    description: "Mean time between failures."
    notes: |
      Grain: asset. Unit: hours.
      Lineage: fact_ops_failures[Failure Start/End].
      QA: Accurate failure timestamps; exclude planned stops.
  dependencies:
    columns:
      - "fact_ops_failures[Failure Start]"
      - "fact_ops_failures[Failure End]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "MTTR (hours)"
  is_kpi_measure: true
  kpi_id_ref: "ops.mttr.hours"
  semantic_model: "Operations_SemanticModel"
  display_folder: "04_Reliability"
  category: "KPI"
  expression:
    dax: "/* TODO: implement MTTR */"
    formatString: "0.0"
  documentation:
    description: "Mean time to repair."
    notes: |
      Grain: asset. Unit: hours.
      Lineage: fact_ops_failures[Repair Duration].
      QA: Repair duration capture consistent; exclude waiting times if needed.
  dependencies:
    columns:
      - "fact_ops_failures[Repair Duration]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Unplanned Downtime %"
  is_kpi_measure: true
  kpi_id_ref: "ops.downtime.unplanned.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Unplanned Downtime % */"
    formatString: "0.0%"
  documentation:
    description: "Unplanned downtime share of planned time."
    notes: |
      Grain: asset_day. Unit: %.
      Lineage: fact_ops[Unplanned Downtime], fact_ops[Planned Time].
      QA: Correct tagging of unplanned events; Planned Time > 0.
  dependencies:
    columns:
      - "fact_ops[Unplanned Downtime]"
      - "fact_ops[Planned Time]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Spare Parts Stockout %"
  is_kpi_measure: true
  kpi_id_ref: "ops.spare_parts.stockout.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "05_Maintenance"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Spare Parts Stockout % */"
    formatString: "0.0%"
  documentation:
    description: "Maintenance readiness via stockout rate for parts."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_maintenance[Parts Stockout Flag], fact_maintenance[Orders].
      QA: Orders denominator > 0; flag accuracy.
  dependencies:
    columns:
      - "fact_maintenance[Parts Stockout Flag]"
      - "fact_maintenance[Orders]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "PM Compliance %"
  is_kpi_measure: true
  kpi_id_ref: "ops.pm_compliance.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "05_Maintenance"
  category: "KPI"
  expression:
    dax: "/* TODO: implement PM Compliance % */"
    formatString: "0.0%"
  documentation:
    description: "Preventive maintenance discipline: on-time PM orders / planned PM orders."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_maintenance[PM On Time], fact_maintenance[PM Planned].
      QA: PM Planned > 0; on-time flag logic consistent.
  dependencies:
    columns:
      - "fact_maintenance[PM On Time]"
      - "fact_maintenance[PM Planned]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "First Pass Yield %"
  is_kpi_measure: true
  kpi_id_ref: "quality.fpy.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "KPI"
  expression:
    dax: "/* TODO: implement First Pass Yield % */"
    formatString: "0.0%"
  documentation:
    description: "Good units / total units at first pass."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_quality[Good Units], fact_quality[Total Units].
      QA: Total Units > 0; align with scrap/rework metrics.
  dependencies:
    columns:
      - "fact_quality[Good Units]"
      - "fact_quality[Total Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Scrap Rate %"
  is_kpi_measure: true
  kpi_id_ref: "quality.scrap.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Scrap Rate % */"
    formatString: "0.0%"
  documentation:
    description: "Scrap units / total units."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_quality[Scrap Units], fact_quality[Total Units].
      QA: Total Units > 0; scrap capture consistent.
  dependencies:
    columns:
      - "fact_quality[Scrap Units]"
      - "fact_quality[Total Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Rework Rate %"
  is_kpi_measure: true
  kpi_id_ref: "quality.rework.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Rework Rate % */"
    formatString: "0.0%"
  documentation:
    description: "Reworked units / total units."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_quality[Rework Units], fact_quality[Total Units].
      QA: Total Units > 0; rework capture consistent.
  dependencies:
    columns:
      - "fact_quality[Rework Units]"
      - "fact_quality[Total Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Cost of Poor Quality"
  is_kpi_measure: true
  kpi_id_ref: "quality.copq.amount"
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Cost of Poor Quality */"
    formatString: "EUR #,0.00"
  documentation:
    description: "Financial impact from scrap, rework, and warranty/complaint costs."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_quality_costs[COPQ], fact_quality.
      QA: Components of COPQ documented; no double-counting.
  dependencies:
    columns:
      - "fact_quality_costs[COPQ]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Complaint Rate %"
  is_kpi_measure: true
  kpi_id_ref: "quality.complaint.pct"
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Complaint Rate % */"
    formatString: "0.0%"
  documentation:
    description: "Complaints / units shipped."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_complaints[Complaints], fact_shipments[Units].
      QA: Units shipped > 0; complaint capture complete.
  dependencies:
    columns:
      - "fact_complaints[Complaints]"
      - "fact_shipments[Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Defect Density"
  is_kpi_measure: true
  kpi_id_ref: "quality.defect_density"
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Defect Density */"
    formatString: "0.0"
  documentation:
    description: "Defects per 1k units."
    notes: |
      Grain: line_day. Unit: defects per 1k units.
      Lineage: fact_quality[Defect Count], fact_quality[Units].
      QA: Units > 0; consistent counting rules.
  dependencies:
    columns:
      - "fact_quality[Defect Count]"
      - "fact_quality[Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
