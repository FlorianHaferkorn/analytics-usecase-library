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
    dax: |
      VAR Avail =
          DIVIDE ( SUM ( fact_ops[Run Time Minutes] ), SUM ( fact_ops[Planned Time Minutes] ) )
      VAR Perf =
          /* If standard output available, replace divisor accordingly */
          DIVIDE ( SUM ( fact_ops[Output Units] ), SUM ( fact_ops[Output Units] ) )
      VAR Qual =
          DIVIDE ( SUM ( fact_ops[Good Units] ), SUM ( fact_ops[Output Units] ) )
      RETURN Avail * Perf * Qual
    formatString: "0.0%"
  documentation:
    description: "Overall equipment effectiveness combining availability, performance, and quality."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Run Time Minutes], fact_ops[Planned Time Minutes], fact_ops[Output Units], fact_ops[Good Units].
      QA: Ensure consistent time base; flags for downtime types; DIVIDE guards; replace Perf divisor with theoretical output when available.
  dependencies:
    columns:
      - "fact_ops[Run Time Minutes]"
      - "fact_ops[Planned Time Minutes]"
      - "fact_ops[Output Units]"
      - "fact_ops[Good Units]"
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
    dax: |
      DIVIDE ( SUM ( fact_ops[Run Time Minutes] ), SUM ( fact_ops[Planned Time Minutes] ) )
    formatString: "0.0%"
  documentation:
    description: "Uptime control: Run Time / Planned Production Time."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Run Time Minutes], fact_ops[Planned Time Minutes].
      QA: Planned Time > 0; consistent shift definitions.
  dependencies:
    columns:
      - "fact_ops[Run Time Minutes]"
      - "fact_ops[Planned Time Minutes]"
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
    dax: |
      /* Replace Standard Output with actual standard if available */
      DIVIDE ( SUM ( fact_ops[Output Units] ), SUM ( fact_ops[Output Units] ) )
    formatString: "0.0%"
  documentation:
    description: "Speed vs standard: Actual Output / Theoretical Output."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Output Units], standards.
      QA: Standards maintained; guard against zero standard.
  dependencies:
    columns:
      - "fact_ops[Output Units]"
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
    dax: |
      DIVIDE ( SUM ( fact_ops[Good Units] ), SUM ( fact_ops[Output Units] ) )
    formatString: "0.0%"
  documentation:
    description: "First pass yield: Good Units / Total Units."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Good Units], fact_ops[Output Units].
      QA: Total Units > 0; align with scrap/rework capture.
  dependencies:
    columns:
      - "fact_ops[Good Units]"
      - "fact_ops[Output Units]"
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
    dax: "SUM(fact_ops[Output Units])"
    formatString: "#,0"
  documentation:
    description: "Volume output over time."
    notes: |
      Grain: line_day. Unit: qty.
      Lineage: fact_ops[Output Units].
      QA: Units consistent with quality measures.
  dependencies:
    columns:
      - "fact_ops[Output Units]"
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
    dax: |
      DIVIDE ( SUM ( fact_ops[Downtime Minutes] ), SUM ( fact_ops[Planned Time Minutes] ) )
    formatString: "0.0%"
  documentation:
    description: "Loss share: Downtime / Planned Production Time."
    notes: |
      Grain: line_day. Unit: %.
      Lineage: fact_ops[Downtime Minutes], fact_ops[Planned Time Minutes].
      QA: Distinguish planned vs unplanned; Planned Time > 0.
  dependencies:
    columns:
      - "fact_ops[Downtime Minutes]"
      - "fact_ops[Planned Time Minutes]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Run Time Minutes"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "Base"
  expression:
    dax: "SUM ( fact_ops[Run Time Minutes] )"
    formatString: "#,0"
  documentation:
    description: "Total run time in minutes."
    notes: "Source: fact_ops[Run Time Minutes]."
  dependencies:
    columns:
      - "fact_ops[Run Time Minutes]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Downtime Minutes"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "Base"
  expression:
    dax: "SUM ( fact_ops[Downtime Minutes] )"
    formatString: "#,0"
  documentation:
    description: "Total downtime minutes (planned + unplanned if not split)."
    notes: "Source: fact_ops[Downtime Minutes]."
  dependencies:
    columns:
      - "fact_ops[Downtime Minutes]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Unplanned Downtime Minutes"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "Base"
  expression:
    dax: "SUM ( fact_ops[Unplanned Downtime Minutes] )"
    formatString: "#,0"
  documentation:
    description: "Unplanned downtime minutes."
    notes: "Source: fact_ops[Unplanned Downtime]."
  dependencies:
    columns:
      - "fact_ops[Unplanned Downtime Minutes]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Standard Output Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "02_Throughput"
  category: "Base"
  expression:
    dax: "SUMX ( fact_ops, fact_ops[Planned Time Minutes] * fact_ops[Standard Rate Units Per Minute] )"
    formatString: "#,0"
  documentation:
    description: "Theoretical output based on planned time and standard rate."
    notes: "Source: fact_ops planned time and standard rate."
  dependencies:
    columns:
      - "fact_ops[Planned Time Minutes]"
      - "fact_ops[Standard Rate Units Per Minute]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Failure Count"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "04_Reliability"
  category: "Base"
  expression:
    dax: "DISTINCTCOUNT ( fact_ops_failures[Failure Start DateTime] )"
    formatString: "#,0"
  documentation:
    description: "Count of failure events."
    notes: "Source: fact_ops_failures[Failure Start]."
  dependencies:
    columns:
      - "fact_ops_failures[Failure Start DateTime]"
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
    dax: |
      VAR TotalHours = DIVIDE ( SUM ( fact_ops[Run Time Minutes] ), 60 )
      VAR Failures   = DISTINCTCOUNT ( fact_ops_failures[Failure Start DateTime] )
      RETURN DIVIDE ( TotalHours, Failures )
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
    dax: |
      AVERAGEX ( fact_ops_failures, fact_ops_failures[Repair Duration] )
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
    dax: |
      DIVIDE ( SUM ( fact_ops[Unplanned Downtime Minutes] ), SUM ( fact_ops[Planned Time Minutes] ) )
    formatString: "0.0%"
  documentation:
    description: "Unplanned downtime share of planned time."
    notes: |
      Grain: asset_day. Unit: %.
      Lineage: fact_ops[Unplanned Downtime Minutes], fact_ops[Planned Time Minutes].
      QA: Correct tagging of unplanned events; Planned Time > 0.
  dependencies:
    columns:
      - "fact_ops[Unplanned Downtime Minutes]"
      - "fact_ops[Planned Time Minutes]"
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
    dax: |
      VAR Stockout = SUM ( fact_maintenance[Parts Stockout Flag] )
      VAR Orders   = SUM ( fact_maintenance[Orders] )
      RETURN DIVIDE ( Stockout, Orders )
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
    dax: |
      DIVIDE ( SUM ( fact_maintenance[PM On Time] ), SUM ( fact_maintenance[PM Planned] ) )
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
    dax: |
      DIVIDE ( SUM ( fact_quality[Good Units] ), SUM ( fact_quality[Total Units] ) )
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
    dax: |
      DIVIDE ( SUM ( fact_quality[Scrap Units] ), SUM ( fact_quality[Total Units] ) )
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
    dax: |
      DIVIDE ( SUM ( fact_quality[Rework Units] ), SUM ( fact_quality[Total Units] ) )
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

- measure_name: "Total Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_quality[Total Units] )"
    formatString: "#,0"
  documentation:
    description: "Total produced units in the selected context."
    notes: "Source: fact_quality[Total Units]."
  dependencies:
    columns:
      - "fact_quality[Total Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Good Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_quality[Good Units] )"
    formatString: "#,0"
  documentation:
    description: "Conforming units produced."
    notes: "Source: fact_quality[Good Units]."
  dependencies:
    columns:
      - "fact_quality[Good Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Scrap Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_quality[Scrap Units] )"
    formatString: "#,0"
  documentation:
    description: "Scrapped units in the selected context."
    notes: "Source: fact_quality[Scrap Units]."
  dependencies:
    columns:
      - "fact_quality[Scrap Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Rework Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_quality[Rework Units] )"
    formatString: "#,0"
  documentation:
    description: "Reworked units in the selected context."
    notes: "Source: fact_quality[Rework Units]."
  dependencies:
    columns:
      - "fact_quality[Rework Units]"
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
    dax: "SUM(fact_quality_costs[COPQ])"
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
    dax: |
      VAR Complaints = SUM ( fact_complaints[Complaints] )
      VAR Units      = SUM ( fact_shipments[Units] )
      RETURN DIVIDE ( Complaints, Units )
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

- measure_name: "Complaint Count"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_complaints[Complaint Count] )"
    formatString: "#,0"
  documentation:
    description: "Number of complaints in the selected context."
    notes: "Source: fact_complaints[Complaint Count]."
  dependencies:
    columns:
      - "fact_complaints[Complaint Count]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Shipped Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "06_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_shipments[Shipped Units] )"
    formatString: "#,0"
  documentation:
    description: "Units shipped used as denominator for complaint rate."
    notes: "Source: fact_shipments[Shipped Units]."
  dependencies:
    columns:
      - "fact_shipments[Shipped Units]"
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
    dax: |
      VAR Defects = SUM ( fact_quality[Defect Count] )
      VAR Units   = SUM ( fact_quality[Units] )
      RETURN DIVIDE ( Defects, Units ) * 1000
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
- measure_name: "Planned Time"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "Base"
  expression:
    dax: "SUM ( fact_ops[Planned Time Minutes] )"
    formatString: "#,0"
  documentation:
    description: "Total planned production time in minutes."
    notes: "Source: fact_ops[Planned Time Minutes]."
  dependencies:
    columns:
      - "fact_ops[Planned Time Minutes]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Run Time"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "03_Downtime"
  category: "Base"
  expression:
    dax: "SUM ( fact_ops[Run Time Minutes] )"
    formatString: "#,0"
  documentation:
    description: "Total run time in minutes."
    notes: "Source: fact_ops[Run Time Minutes]."
  dependencies:
    columns:
      - "fact_ops[Run Time Minutes]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Output Units"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "01_Ops"
  category: "Base"
  expression:
    dax: "SUM ( fact_ops[Output Units] )"
    formatString: "#,0"
  documentation:
    description: "Total output units."
    notes: "Source: fact_ops[Output Units]."
  dependencies:
    columns:
      - "fact_ops[Output Units]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Defect Count"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Operations_SemanticModel"
  display_folder: "04_Quality"
  category: "Base"
  expression:
    dax: "SUM ( fact_quality[Defect Count] )"
    formatString: "#,0"
  documentation:
    description: "Total defect count."
    notes: "Source: fact_quality[Defect Count]."
  dependencies:
    columns:
      - "fact_quality[Defect Count]"
  governance:
    owner: "Operations Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```

