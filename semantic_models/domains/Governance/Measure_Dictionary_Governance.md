# Measure Dictionary - Governance

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Data Quality %
  is_kpi_measure: true
  kpi_id_ref: gov.data_quality.pct
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Valid Records Count],[Total Records Count])
    formatString: 0.0 %
  documentation:
    description: Share of valid records over total processed records.
    notes: ''
  governance:
    owner: Data Governance Team
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Valid Records Count
    - Total Records Count
    columns:
    - fact_dq.ValidRecords
    - fact_dq.TotalRecords
- measure_name: Compliance Breach Count
  is_kpi_measure: true
  kpi_id_ref: gov.compliance.breach.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: COUNTROWS(fact_compliance)
    formatString: ''
  documentation:
    description: Count of recorded confirmed compliance incidents.
    notes: ''
  governance:
    owner: Compliance BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Breach Incidents
    columns:
    - fact_compliance.IncidentID
- measure_name: Project ROI %
  is_kpi_measure: true
  kpi_id_ref: corp.project.roi.pct
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Realized Benefit Amount]-[Total Project Cost Amount],[Total Project Cost Amount])
    formatString: 0.0 %
  documentation:
    description: ROI evaluation using realized financial benefits.
    notes: ''
  governance:
    owner: PMO / Finance
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 01_Strategy
  dependencies:
    measures:
    - Realized Benefit Amount
    - Total Project Cost Amount
    columns:
    - fact_projects.RealizedBenefit
    - fact_projects.TotalCost
- measure_name: Benefit Realization %
  is_kpi_measure: true
  kpi_id_ref: corp.benefit.realization.pct
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Realized Benefit Amount],[Planned Benefit Amount])
    formatString: 0.0 %
  documentation:
    description: Tracks benefit execution per project.
    notes: ''
  governance:
    owner: PMO / Finance
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 01_Strategy
  dependencies:
    measures:
    - Realized Benefit Amount
    - Planned Benefit Amount
    columns:
    - fact_projects.RealizedBenefit
    - fact_projects.PlannedBenefit
- measure_name: Budget Adherence %
  is_kpi_measure: true
  kpi_id_ref: corp.budget.adherence.pct
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: 1 - DIVIDE(ABS([Actual Project Cost Amount]-[Approved Budget Amount]),[Approved Budget Amount])
    formatString: 0.0 %
  documentation:
    description: Normalizes budget variance into an adherence percentage.
    notes: ''
  governance:
    owner: PMO / Finance
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 01_Strategy
  dependencies:
    measures:
    - Actual Project Cost Amount
    - Approved Budget Amount
    columns:
    - fact_projects.ActualCost
    - fact_projects.BudgetCost
- measure_name: Schedule Adherence %
  is_kpi_measure: true
  kpi_id_ref: corp.schedule.adherence.pct
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([On-Time Milestones],[Total Milestones])
    formatString: 0.0 %
  documentation:
    description: Share of milestones delivered on or before committed date.
    notes: ''
  governance:
    owner: PMO
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 01_Strategy
  dependencies:
    measures:
    - On-Time Milestones
    - Total Milestones
    columns:
    - fact_projects.MilestoneStatus
- measure_name: Payback Period (Months)
  is_kpi_measure: true
  kpi_id_ref: corp.payback.months
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: VAR _cost = [Total Project Cost Amount] RETURN CALCULATE(MIN('Calendar'[MonthNumber]), [Cumulative Benefit Amount]
      >= _cost)
    formatString: '0'
  documentation:
    description: Approximated payback derived from cumulative benefits.
    notes: ''
  governance:
    owner: PMO / Finance
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 01_Strategy
  dependencies:
    measures:
    - Cumulative Benefit Amount
    - Total Project Cost Amount
    columns:
    - fact_projects.RealizedBenefit
    - fact_projects.TotalCost
    - dim_date.MonthNumber
- measure_name: Compliance Incidents Count
  is_kpi_measure: true
  kpi_id_ref: gov.compliance.incidents.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: COUNTROWS(fact_compliance)
    formatString: '0'
  documentation:
    description: Simple incident volume measure aligned with COR-003 use case.
    notes: ''
  governance:
    owner: Compliance BI
    status: active
    version: v1.0
    last_review: 11.11.2025
  dependencies:
    measures:
    - Compliance Incidents
    columns:
    - fact_compliance.IncidentID
- measure_name: Open Audit Findings Count
  is_kpi_measure: true
  kpi_id_ref: gov.audit.findings.open.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: ''
  documentation:
    description: Count of findings with status = open.
    notes: ''
  governance:
    owner: Audit BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Audit Findings
- measure_name: Audit Findings
  is_kpi_measure: true
  kpi_id_ref: gov.audit.findings.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Total count of audit findings in period
    notes: ''
  governance:
    owner: Audit & Risk Analytics
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Total Records Count
  is_kpi_measure: true
  kpi_id_ref: gov.records.total.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: Total rows processed in governed dataset
    notes: ''
  governance:
    owner: Data Governance Team
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Valid Records Count
  is_kpi_measure: true
  kpi_id_ref: gov.valid_records.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: SUM(fact_dq_checks[ValidRecords])
    formatString: '#,0'
  documentation:
    description: Number of records flagged as valid by the data quality pipeline for the selected dataset and period.
    notes: ''
  governance:
    owner: Data Governance Team
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    columns:
    - fact_dq.ValidRecords
- measure_name: Security Incidents Count
  is_kpi_measure: true
  kpi_id_ref: sec.incident.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0'
  documentation:
    description: Number of logged security incidents for the selected slice.
    notes: ''
  governance:
    owner: Security Operations
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 01_Security
  dependencies:
    columns:
    - fact_sec_incident.IncidentID
- measure_name: Critical Security Incidents Count
  is_kpi_measure: true
  kpi_id_ref: sec.incident.critical.count
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0'
  documentation:
    description: Number of security incidents classified as high or critical severity.
    notes: ''
  governance:
    owner: Security Operations
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 01_Security
  dependencies:
    columns:
    - fact_sec_incident.IncidentID
    - fact_sec_incident.Severity
- measure_name: Security Incident MTTR (Hours)
  is_kpi_measure: true
  kpi_id_ref: sec.incident.mttr.hours
  semantic_model: Governance_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0.0'
  documentation:
    description: Average time in hours between detection and resolution of security incidents.
    notes: ''
  governance:
    owner: Security Operations
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 01_Security
  dependencies:
    columns:
    - fact_sec_incident.DetectedAt
    - fact_sec_incident.ResolvedAt
```
