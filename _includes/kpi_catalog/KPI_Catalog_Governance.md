# KPI Catalog - Governance & Compliance

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "gov.data_quality.pct"
  kpi_key: "Data Quality %"
  kpi_type: "strategic"
  strategic_ref: "Data Quality %"
  impact_dimension: "Governance"
  domain_tag: ["Data Governance"]
  use_case_ref:
    - "GOV-001"
  depends_on:
    - "Valid Records Count"
    - "Total Records Count"
  depends_on_ids:
    - "gov.valid_records.count"
    - "gov.records.total.count"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measures data accuracy and completeness in governed systems."
    definition:
      "(Valid Records / Total Records) × 100"
    grain_scope:
      "Dataset level; aggregated monthly."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Indicates trustworthiness of analytical data assets."
  technical:
    dax_name:
      "Data Quality %"
    dax_expression:
      "DIVIDE([Valid Records Count],[Total Records Count])"
    formatString:
      "0.0 %"
    description:
      "Share of valid records over total processed records."
    lineage:
      - "fact_dq.ValidRecords"
      - "fact_dq.TotalRecords"
    source_grain:
      "dataset"
    source_column_ref:
      - "fact_dq.valid_records"
      - "fact_dq.total_records"
    source_system:
      "Data Quality Platform"
    verified:
      "true"
  governance:
    business_owner:
      "Chief Data Officer"
    data_owner:
      "Data Governance Team"
    steward:
      "Data Steward"
    review_cycle:
      "monthly"
    validation_process:
      "automated"
    qa_rules:
      "DQ % ≥ 98 % for certified datasets"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.99"
    lineage_verified:
      "true"
    copilot_ready:
      "true"

- kpi_id: "gov.compliance.breach.count"
  kpi_key: "Compliance Breach Count"
  kpi_type: "strategic"
  strategic_ref: "Compliance Breach Count"
  impact_dimension: "Governance"
  domain_tag: ["Compliance"]
  use_case_ref:
    - "GOV-003"
  depends_on:
    - "Breach Incidents"
  calc_type: "count"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Tracks number of confirmed compliance or regulatory breaches."
    definition:
      "Count of recorded confirmed compliance incidents."
    grain_scope:
      "Organization level; per reporting period."
    unit_format:
      "count"
    interpretation:
      "High numbers indicate weak compliance culture."
  technical:
    dax_name:
      "Compliance Breach Count"
    dax_expression:
      "COUNTROWS(fact_compliance)"
    lineage:
      "fact_compliance.IncidentID"
    source_grain:
      "incident_record"
    source_column_ref:
      "fact_compliance.incident_id"
    source_system:
      "Compliance Management"
    verified:
      "true"
  governance:
    business_owner:
      "Chief Compliance Officer"
    data_owner:
      "Compliance BI"
    steward:
      "Compliance Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "All incidents classified before quarter-end"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.96"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
```


```yaml
- kpi_id: "corp.project.roi.pct"
  kpi_key: "Project ROI %"
  kpi_type: "strategic"
  strategic_ref: "Project ROI %"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-001"
    - "COR-004"
  depends_on:
    - "Realized Benefit Amount"
    - "Total Project Cost Amount"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measures realized return of strategic initiatives."
    definition:
      "(Realized Benefits - Total Costs) / Total Costs"
    grain_scope:
      "Project portfolio."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Indicates whether investments deliver expected value."
  technical:
    dax_name:
      "Project ROI %"
    dax_expression:
      "DIVIDE([Realized Benefit Amount]-[Total Project Cost Amount],[Total Project Cost Amount])"
    displayFolder:
      "01_Strategy"
    formatString:
      "0.0 %"
    description:
      "ROI evaluation using realized financial benefits."
    lineage:
      - "fact_projects.RealizedBenefit"
      - "fact_projects.TotalCost"
    source_grain:
      "project"
    source_system:
      "Project Portfolio Management"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Strategy"
    data_owner:
      "PMO / Finance"
    steward:
      "Portfolio Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      - "Benefits reconciled with finance actuals"
      - "Costs include CapEx + OpEx"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.85"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


```yaml
- kpi_id: "corp.benefit.realization.pct"
  kpi_key: "Benefit Realization %"
  kpi_type: "strategic"
  strategic_ref: "Benefit Realization %"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-001"
  depends_on:
    - "Realized Benefit Amount"
    - "Planned Benefit Amount"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Shows how much of the approved business case has been achieved."
    definition:
      "Realized Benefit Amount / Planned Benefit Amount"
    grain_scope:
      "Project or portfolio."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Values below 100 % indicate realization gaps."
  technical:
    dax_name:
      "Benefit Realization %"
    dax_expression:
      "DIVIDE([Realized Benefit Amount],[Planned Benefit Amount])"
    displayFolder:
      "01_Strategy"
    formatString:
      "0.0 %"
    description:
      "Tracks benefit execution per project."
    lineage:
      - "fact_projects.RealizedBenefit"
      - "fact_projects.PlannedBenefit"
    source_grain:
      "project"
    source_system:
      "Project Portfolio Management"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Strategy"
    data_owner:
      "PMO / Finance"
    steward:
      "Portfolio Analyst"
    review_cycle:
      "monthly"
    validation_process:
      "manual review"
    qa_rules:
      "Currency harmonized with finance actuals"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.82"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


```yaml
- kpi_id: "corp.budget.adherence.pct"
  kpi_key: "Budget Adherence %"
  kpi_type: "supporting"
  strategic_ref: "Project ROI %"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-001"
  depends_on:
    - "Actual Project Cost Amount"
    - "Approved Budget Amount"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measures how close spending is to approved budget."
    definition:
      "1 - ABS(Actual Cost - Budget) / Budget"
    grain_scope:
      "Project / program."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Near 100 % indicates strong spending discipline."
  technical:
    dax_name:
      "Budget Adherence %"
    dax_expression:
      "1 - DIVIDE(ABS([Actual Project Cost Amount]-[Approved Budget Amount]),[Approved Budget Amount])"
    displayFolder:
      "01_Strategy"
    formatString:
      "0.0 %"
    description:
      "Normalizes budget variance into an adherence percentage."
    lineage:
      - "fact_projects.ActualCost"
      - "fact_projects.BudgetCost"
    source_grain:
      "project"
    source_system:
      "Project Portfolio Management"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Finance Controlling"
    data_owner:
      "PMO / Finance"
    steward:
      "Project Controller"
    review_cycle:
      "monthly"
    validation_process:
      "manual review"
    qa_rules:
      "Budget > 0 required"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.8"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


```yaml
- kpi_id: "corp.schedule.adherence.pct"
  kpi_key: "Schedule Adherence %"
  kpi_type: "supporting"
  strategic_ref: "Project ROI %"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-001"
  depends_on:
    - "On-Time Milestones"
    - "Total Milestones"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Indicates delivery reliability against planned milestones."
    definition:
      "On-Time Milestones / Total Milestones"
    grain_scope:
      "Project / program."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Low adherence highlights execution risk."
  technical:
    dax_name:
      "Schedule Adherence %"
    dax_expression:
      "DIVIDE([On-Time Milestones],[Total Milestones])"
    displayFolder:
      "01_Strategy"
    formatString:
      "0.0 %"
    description:
      "Share of milestones delivered on or before committed date."
    lineage:
      "fact_projects.MilestoneStatus"
    source_grain:
      "milestone"
    source_system:
      "Project Portfolio Management"
    verified:
      "false"
  governance:
    business_owner:
      "Head of PMO"
    data_owner:
      "PMO"
    steward:
      "Project Manager"
    review_cycle:
      "monthly"
    validation_process:
      "manual review"
    qa_rules:
      "Milestones reconciled with PMO register"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.78"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


```yaml
- kpi_id: "corp.payback.months"
  kpi_key: "Payback Period (Months)"
  kpi_type: "supporting"
  strategic_ref: "Project ROI %"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-001"
  depends_on:
    - "Cumulative Benefit Amount"
    - "Total Project Cost Amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Shows months required until cumulative benefits exceed total cost."
    definition:
      "Months until cumulative benefits >= total costs."
    grain_scope:
      "Project."
    unit_format:
      "months"
    interpretation:
      "Lower payback indicates faster value capture."
  technical:
    dax_name:
      "Payback Period (Months)"
    dax_expression:
      "VAR _cost = [Total Project Cost Amount] RETURN CALCULATE(MIN('Calendar'[MonthNumber]), [Cumulative Benefit Amount] >= _cost)"
    displayFolder:
      "01_Strategy"
    formatString:
      "0"
    description:
      "Approximated payback derived from cumulative benefits."
    lineage:
      - "fact_projects.RealizedBenefit"
      - "fact_projects.TotalCost"
      - "dim_date.MonthNumber"
    source_grain:
      "project"
    source_system:
      "Project Portfolio Management"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Strategy"
    data_owner:
      "PMO / Finance"
    steward:
      "Portfolio Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Cumulative benefit curve documented"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.75"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "gov.compliance.incidents.count"
  kpi_key: "Compliance Incidents Count"
  kpi_type: "supporting"
  strategic_ref: "Compliance Breach Count"
  impact_dimension: "Governance"
  domain_tag: ["Compliance"]
  use_case_ref:
    - "COR-003"
  depends_on:
    - "Compliance Incidents"
  calc_type: "count"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Counts all reported compliance incidents (open + closed)."
    definition:
      "Number of incidents recorded in the compliance case management system."
    grain_scope:
      "Organization level."
    unit_format:
      "count"
    interpretation:
      "Trend indicator for compliance exposure."
  technical:
    dax_name:
      "Compliance Incidents Count"
    dax_expression:
      "COUNTROWS(fact_compliance)"
    formatString:
      "0"
    description:
      "Simple incident volume measure aligned with COR-003 use case."
    lineage:
      "fact_compliance.IncidentID"
    source_grain:
      "incident_record"
    source_system:
      "Compliance Management"
    verified:
      "false"
  governance:
    business_owner:
      "Chief Compliance Officer"
    data_owner:
      "Compliance BI"
    steward:
      "Compliance Analyst"
    review_cycle:
      "monthly"
    validation_process:
      "manual review"
    qa_rules:
      "Incident status validated before month-end"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.85"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


```yaml
- kpi_id: "gov.audit.findings.open.count"
  kpi_key: "Open Audit Findings Count"
  kpi_type: "supporting"
  strategic_ref: "Audit Finding Severity %"
  impact_dimension: "Governance"
  domain_tag: ["Audit"]
  use_case_ref:
    - "GOV-004"
  depends_on:
    - "Audit Findings"
  depends_on_ids:
    - "gov.audit.findings.count"
  calc_type: "count"
  refresh: "quarterly"
  status: "Active"
  business:
    purpose:
      "Number of unresolved audit findings still open."
    definition:
      "Count of findings with status = open."
    grain_scope:
      "Audit report level."
    unit_format:
      "count"
    interpretation:
      "Shows audit remediation backlog."
    technical:
      dax_name:
        "Open Audit Findings Count"
      dax_expression:
        "COUNTROWS(fact_audit_findings)"
      formatString:
        "#,0"
      description:
        "Number of audit findings with status open for the selected slice."
    lineage:
      "fact_audit.finding_id"
    source_grain:
      "audit_report"
    source_column_ref:
      "fact_audit.finding_id"
    source_system:
      "Audit System"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Internal Audit"
    data_owner:
      "Audit BI"
    steward:
      "Audit Coordinator"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      - "All closed findings verified by audit committee"
      - "Open findings reconcile to audit tracking system within +/- 1 count"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.97"
    lineage_verified:
      "true"
  copilot_ready: "true"
```


```yaml
- kpi_id: "gov.audit.findings.count"
  kpi_key: "Audit Findings"
  kpi_type: "supporting"
  impact_dimension: "Governance"
  domain_tag: ["Audit"]
  calc_type: count
  technical:
    dax_name: "Audit Findings"
    description: "Total count of audit findings in period"
    formatString: "0"
    verified: false
  business:
        purpose: "Number of audit findings identified in the reporting period."   
        definition: "Count of audit findings meeting reporting criteria (e.g., severity threshold)."   
        grain_scope: "Audit report/engagement level; consolidated quarterly."   
        unit_format: "count"
  governance:
    business_owner: "Head of Internal Audit"
    data_owner: "Audit & Risk Analytics"
    steward: "Audit Manager"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
        - "All closed findings verified by audit committee"     
        - "Open findings reconciled to audit tracking system (+/- 1 count)"   
    version: "v1.0"
    last_review: "2025-11-04"
```


```yaml
- kpi_id: "gov.records.total.count"
  kpi_key: "Total Records Count"
  kpi_type: "supporting"
  impact_dimension: "Governance"
  domain_tag: ["Data Governance"]
  calc_type: count
  technical:
    dax_name: "Total Records Count"
    description: "Total rows processed in governed dataset"
    formatString: "0"
    verified: false
  business:
        purpose: "Total number of processed records in a governed dataset."   
        definition: "Row count after ingestion/quality processing for the period."   
        grain_scope: "Dataset/table level; partitioned by load period."   
        unit_format: "count"
  governance:
    business_owner: "Chief Data Officer"
    data_owner: "Data Governance Team"
    steward: "Data Steward"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
            - "Row count reconciles to source landing within +/- 0.1 %"     
            - "Non-negative and integer only"   
    version: "v1.0"
    last_review: "2025-11-04"
```


## 3. Base Measures
```yaml
- kpi_id: "gov.valid_records.count"
  kpi_key: "Valid Records Count"
  kpi_type: "supporting"
  strategic_ref: "Data Quality %"
  impact_dimension: "Governance"
  domain_tag: ["Data Governance"]
  use_case_ref: ["GOV-001"]
  depends_on: []
  depends_on_ids: []
  calc_type: count
  refresh: daily
  status: Active
  business:
    purpose: "Number of records passing all data quality checks."
    definition: "Count of rows flagged as valid in data quality pipeline."
    grain_scope: "Dataset level."
    unit_format: "count"
    interpretation: "Foundation metric for DQ ratio calculations."
  technical:
    dax_name: "Valid Records Count"
    dax_expression: "SUM(fact_dq_checks[ValidRecords])"
    formatString: "#,0"
    description: "Number of records flagged as valid by the data quality pipeline for the selected dataset and period."
    lineage: ["fact_dq.ValidRecords"]
    source_grain: "dataset"
    source_column_ref: ["fact_dq.valid_records"]
    source_system: "Data Quality Platform"
    verified: true
  governance:
    business_owner: "Chief Data Officer"
    data_owner: "Data Governance Team"
    steward: "Data Steward"
    review_cycle: "monthly"
    validation_process: "automated"
    qa_rules:
            - "Non-negative integer"     
            - "Reconciles against total count minus invalid/error rows"   
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 1.00
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_id: "sec.incident.count"
  kpi_key: "Security Incidents Count"
  kpi_type: "diagnostic"
  strategic_ref: "Cybersecurity Posture"
  impact_dimension: "Governance"
  domain_tag: ["Governance"]
  use_case_ref: ["COR-008"]
  calc_type: "count"
  refresh: "daily"
  status: "Draft"
  business:
    purpose: "Measure the number of detected cybersecurity or information security incidents."
    definition: "Count of security incidents logged in the incident management system for the selected period and scope."
    grain_scope: "Incident; aggregated to org / system / period."
    unit_format: "count"
    interpretation: "Higher counts can signal increased threat activity or detection quality; interpret together with severity and MTTR."
  technical:
    dax_name: "Security Incidents Count"
    dax_expression: ""
    formatString: "#,0"
    displayFolder: "01_Security"
    description: "Number of logged security incidents for the selected slice."
    lineage:
      - "fact_sec_incident.IncidentID"
    source_grain: "incident"
    source_column_ref:
      - "fact_sec_incident.incident_id"
    source_system: "SIEM / ITSM"
    verified: false
  governance:
    business_owner: "CISO"
    data_owner: "Security Operations"
    steward: "Security Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Incident classification and deduplication rules documented"
    version: "v0.1"
    last_review: "19.11.2025"

- kpi_id: "sec.incident.critical.count"
  kpi_key: "Critical Security Incidents Count"
  kpi_type: "diagnostic"
  strategic_ref: "Cybersecurity Posture"
  impact_dimension: "Governance"
  domain_tag: ["Governance"]
  use_case_ref: ["COR-008"]
  calc_type: "count"
  refresh: "daily"
  status: "Draft"
  business:
    purpose: "Highlight the number of high or critical severity security incidents."
    definition: "Count of incidents classified as high or critical severity in the incident management system."
    grain_scope: "Incident; aggregated to org / system / period."
    unit_format: "count"
    interpretation: "High numbers indicate material security risk; reduction over time is typically a key objective."
  technical:
    dax_name: "Critical Security Incidents Count"
    dax_expression: ""
    formatString: "#,0"
    displayFolder: "01_Security"
    description: "Number of security incidents classified as high or critical severity."
    lineage:
      - "fact_sec_incident.IncidentID"
      - "fact_sec_incident.Severity"
    source_grain: "incident"
    source_column_ref:
      - "fact_sec_incident.incident_id"
      - "fact_sec_incident.severity"
    source_system: "SIEM / ITSM"
    verified: false
  governance:
    business_owner: "CISO"
    data_owner: "Security Operations"
    steward: "Security Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Severity classification scheme documented and consistently applied"
    version: "v0.1"
    last_review: "19.11.2025"

- kpi_id: "sec.incident.mttr.hours"
  kpi_key: "Security Incident MTTR (Hours)"
  kpi_type: "diagnostic"
  strategic_ref: "Cybersecurity Posture"
  impact_dimension: "Governance"
  domain_tag: ["Governance"]
  use_case_ref: ["COR-008"]
  calc_type: "ratio"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Measure average time to resolve security incidents."
    definition: "Average duration in hours between incident detection and resolution/closure."
    grain_scope: "Incident; aggregated by org / system / severity and period."
    unit_format: "hours (1 decimal)"
    interpretation: "Lower MTTR indicates faster response and containment; very low values must still be checked against data quality."
  technical:
    dax_name: "Security Incident MTTR (Hours)"
    dax_expression: ""
    formatString: "0.0"
    displayFolder: "01_Security"
    description: "Average time in hours between detection and resolution of security incidents."
    lineage:
      - "fact_sec_incident.DetectedAt"
      - "fact_sec_incident.ResolvedAt"
    source_grain: "incident"
    source_column_ref:
      - "fact_sec_incident.detected_at"
      - "fact_sec_incident.resolved_at"
    source_system: "SIEM / ITSM"
    verified: false
  governance:
    business_owner: "CISO"
    data_owner: "Security Operations"
    steward: "Security Analyst"
    review_cycle: "monthly"
    validation_process: "manual review"
    qa_rules:
      - "Durations validated; negative or extreme outliers investigated"
    version: "v0.1"
    last_review: "19.11.2025"
```

---

Last updated: 19.11.2025
