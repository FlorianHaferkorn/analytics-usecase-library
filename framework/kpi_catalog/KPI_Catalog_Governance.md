# KPI Catalog - Governance

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: gov.data_quality.pct
  kpi_key: Data Quality %
  kpi_type: strategic
  impact_dimension: Governance
  domain_tag:
  - Data Governance
  use_case_ref:
  - GOV-001
  calc_type: rate
  business:
    purpose: Measures data accuracy and completeness in governed systems.
    definition: (Valid Records / Total Records) * 100
    grain_scope: Dataset level; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Indicates trustworthiness of analytical data assets.
  technical:
    dax_name: Data Quality %
    depends_on_measures:
    - Valid Records Count
    - Total Records Count
    lineage:
    - fact_dq.ValidRecords
    - fact_dq.TotalRecords
  governance:
    business_owner: Chief Data Officer
    data_owner: Data Governance Team
    steward: Data Steward
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - DQ % >= 98 % for certified datasets
    version: v2.0
  metadata_quality:
    completeness_score: 0.99
    last_review: 12.10.2025

- kpi_id: gov.compliance.breach.count
  kpi_key: Compliance Breach Count
  kpi_type: strategic
  impact_dimension: Governance
  domain_tag:
  - Compliance
  use_case_ref:
  - GOV-003
  calc_type: count
  business:
    purpose: Tracks number of confirmed compliance or regulatory breaches.
    definition: Count of recorded confirmed compliance incidents.
    grain_scope: Organization level; per reporting period.
    unit_format: count
    interpretation: High numbers indicate weak compliance culture.
  technical:
    dax_name: Compliance Breach Count
    depends_on_measures:
    - Breach Incidents
    lineage:
    - fact_compliance.IncidentID
  governance:
    business_owner: Chief Compliance Officer
    data_owner: Compliance BI
    steward: Compliance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - All incidents classified before quarter-end
    version: v2.0
  metadata_quality:
    completeness_score: 0.96
    last_review: 12.10.2025

- kpi_id: corp.project.roi.pct
  kpi_key: Project ROI %
  kpi_type: strategic
  impact_dimension: Governance
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-001
  - COR-004
  calc_type: rate
  business:
    purpose: Measures realized return of strategic initiatives.
    definition: (Realized Benefits - Total Costs) / Total Costs
    grain_scope: Project portfolio.
    unit_format: '% (1 decimal)'
    interpretation: Indicates whether investments deliver expected value.
  technical:
    dax_name: Project ROI %
    depends_on_measures:
    - Realized Benefit Amount
    - Total Project Cost Amount
    lineage:
    - fact_projects.RealizedBenefit
    - fact_projects.TotalCost
  governance:
    business_owner: Head of Strategy
    data_owner: PMO / Finance
    steward: Portfolio Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Benefits reconciled with finance actuals
    - Costs include CapEx + OpEx
    version: v1.0
  metadata_quality:
    completeness_score: 0.85
    last_review: 11.11.2025

- kpi_id: corp.benefit.realization.pct
  kpi_key: Benefit Realization %
  kpi_type: strategic
  impact_dimension: Governance
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-001
  calc_type: rate
  business:
    purpose: Shows how much of the approved business case has been achieved.
    definition: Realized Benefit Amount / Planned Benefit Amount
    grain_scope: Project or portfolio.
    unit_format: '% (1 decimal)'
    interpretation: Values below 100 % indicate realization gaps.
  technical:
    dax_name: Benefit Realization %
    depends_on_measures:
    - Realized Benefit Amount
    - Planned Benefit Amount
    lineage:
    - fact_projects.RealizedBenefit
    - fact_projects.PlannedBenefit
  governance:
    business_owner: Head of Strategy
    data_owner: PMO / Finance
    steward: Portfolio Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Currency harmonized with finance actuals
    version: v1.0
  metadata_quality:
    completeness_score: 0.82
    last_review: 11.11.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: corp.budget.adherence.pct
  kpi_key: Budget Adherence %
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-001
  calc_type: rate
  business:
    purpose: Measures how close spending is to approved budget.
    definition: 1 - ABS(Actual Cost - Budget) / Budget
    grain_scope: Project / program.
    unit_format: '% (1 decimal)'
    interpretation: Near 100 % indicates strong spending discipline.
  technical:
    dax_name: Budget Adherence %
    depends_on_measures:
    - Actual Project Cost Amount
    - Approved Budget Amount
    lineage:
    - fact_projects.ActualCost
    - fact_projects.BudgetCost
  governance:
    business_owner: Head of Finance Controlling
    data_owner: PMO / Finance
    steward: Project Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Budget > 0 required
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: corp.schedule.adherence.pct
  kpi_key: Schedule Adherence %
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-001
  calc_type: rate
  business:
    purpose: Indicates delivery reliability against planned milestones.
    definition: On-Time Milestones / Total Milestones
    grain_scope: Project / program.
    unit_format: '% (1 decimal)'
    interpretation: Low adherence highlights execution risk.
  technical:
    dax_name: Schedule Adherence %
    depends_on_measures:
    - On-Time Milestones
    - Total Milestones
    lineage:
    - fact_projects.MilestoneStatus
  governance:
    business_owner: Head of PMO
    data_owner: PMO
    steward: Project Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Milestones reconciled with PMO register
    version: v1.0
  metadata_quality:
    completeness_score: 0.78
    last_review: 11.11.2025

- kpi_id: corp.payback.months
  kpi_key: Payback Period (Months)
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-001
  calc_type: amount
  business:
    purpose: Shows months required until cumulative benefits exceed total cost.
    definition: Months until cumulative benefits >= total costs.
    grain_scope: Project.
    unit_format: months
    interpretation: Lower payback indicates faster value capture.
  technical:
    dax_name: Payback Period (Months)
    depends_on_measures:
    - Cumulative Benefit Amount
    - Total Project Cost Amount
    lineage:
    - fact_projects.RealizedBenefit
    - fact_projects.TotalCost
    - dim_date.MonthNumber
  governance:
    business_owner: Head of Strategy
    data_owner: PMO / Finance
    steward: Portfolio Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Cumulative benefit curve documented
    version: v1.0
  metadata_quality:
    completeness_score: 0.75
    last_review: 11.11.2025

- kpi_id: gov.compliance.incidents.count
  kpi_key: Compliance Incidents Count
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Compliance
  use_case_ref:
  - COR-003
  calc_type: count
  business:
    purpose: Counts all reported compliance incidents (open + closed).
    definition: Number of incidents recorded in the compliance case management system.
    grain_scope: Organization level.
    unit_format: count
    interpretation: Trend indicator for compliance exposure.
  technical:
    dax_name: Compliance Incidents Count
    depends_on_measures:
    - Compliance Incidents
    lineage:
    - fact_compliance.IncidentID
  governance:
    business_owner: Chief Compliance Officer
    data_owner: Compliance BI
    steward: Compliance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Incident status validated before month-end
    version: v1.0
  metadata_quality:
    completeness_score: 0.85
    last_review: 11.11.2025

- kpi_id: gov.audit.findings.open.count
  kpi_key: Open Audit Findings Count
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Audit
  use_case_ref:
  - GOV-004
  calc_type: count
  business:
    purpose: Number of unresolved audit findings still open.
    definition: Count of findings with status = open.
    grain_scope: Audit report level.
    unit_format: count
    interpretation: Shows audit remediation backlog.
  technical:
    dax_name: Open Audit Findings Count
    depends_on_measures:
    - Audit Findings
    lineage: []
  governance:
    business_owner: Head of Internal Audit
    data_owner: Audit BI
    steward: Audit Coordinator
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - All closed findings verified by audit committee
    - Open findings reconcile to audit tracking system within +/- 1 count
    version: v2.0
  metadata_quality:
    completeness_score: 0.97
    last_review: 12.10.2025

- kpi_id: gov.audit.findings.count
  kpi_key: Audit Findings
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Audit
  use_case_ref: []
  calc_type: count
  business:
    purpose: Number of audit findings identified in the reporting period.
    definition: Count of audit findings meeting reporting criteria (e.g., severity threshold).
    grain_scope: Audit report/engagement level; consolidated quarterly.
    unit_format: count
    interpretation: Higher counts indicate increased control gaps; trend and severity mix matter.
  technical:
    dax_name: Audit Findings
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Internal Audit
    data_owner: Audit & Risk Analytics
    steward: Audit Manager
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - All closed findings verified by audit committee
    - Open findings reconciled to audit tracking system (+/- 1 count)
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: gov.records.total.count
  kpi_key: Total Records Count
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Data Governance
  use_case_ref: []
  calc_type: count
  business:
    purpose: Total number of processed records in a governed dataset.
    definition: Row count after ingestion/quality processing for the period.
    grain_scope: Dataset/table level; partitioned by load period.
    unit_format: count
    interpretation: Baseline for data quality ratios; sudden drops/spikes indicate pipeline or source issues.
  technical:
    dax_name: Total Records Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Chief Data Officer
    data_owner: Data Governance Team
    steward: Data Steward
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Row count reconciles to source landing within +/- 0.1 %
    - Non-negative and integer only
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: gov.valid_records.count
  kpi_key: Valid Records Count
  kpi_type: supporting
  impact_dimension: Governance
  domain_tag:
  - Data Governance
  use_case_ref:
  - GOV-001
  calc_type: count
  business:
    purpose: Number of records passing all data quality checks.
    definition: Count of rows flagged as valid in data quality pipeline.
    grain_scope: Dataset level.
    unit_format: count
    interpretation: Foundation metric for DQ ratio calculations.
  technical:
    dax_name: Valid Records Count
    depends_on_measures: []
    lineage:
    - fact_dq.ValidRecords
  governance:
    business_owner: Chief Data Officer
    data_owner: Data Governance Team
    steward: Data Steward
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Non-negative integer
    - Reconciles against total count minus invalid/error rows
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 12.10.2025

- kpi_id: sec.incident.count
  kpi_key: Security Incidents Count
  kpi_type: diagnostic
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - COR-008
  calc_type: count
  business:
    purpose: Measure the number of detected cybersecurity or information security incidents.
    definition: Count of security incidents logged in the incident management system for the selected period and scope.
    grain_scope: Incident; aggregated to org / system / period.
    unit_format: count
    interpretation: Higher counts can signal increased threat activity or detection quality; interpret together with severity
      and MTTR.
  technical:
    dax_name: Security Incidents Count
    depends_on_measures: []
    lineage:
    - fact_sec_incident.IncidentID
  governance:
    business_owner: CISO
    data_owner: Security Operations
    steward: Security Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Incident classification and deduplication rules documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: sec.incident.critical.count
  kpi_key: Critical Security Incidents Count
  kpi_type: diagnostic
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - COR-008
  calc_type: count
  business:
    purpose: Highlight the number of high or critical severity security incidents.
    definition: Count of incidents classified as high or critical severity in the incident management system.
    grain_scope: Incident; aggregated to org / system / period.
    unit_format: count
    interpretation: High numbers indicate material security risk; reduction over time is typically a key objective.
  technical:
    dax_name: Critical Security Incidents Count
    depends_on_measures: []
    lineage:
    - fact_sec_incident.IncidentID
    - fact_sec_incident.Severity
  governance:
    business_owner: CISO
    data_owner: Security Operations
    steward: Security Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Severity classification scheme documented and consistently applied
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: sec.incident.mttr.hours
  kpi_key: Security Incident MTTR (Hours)
  kpi_type: diagnostic
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - COR-008
  calc_type: ratio
  business:
    purpose: Measure average time to resolve security incidents.
    definition: Average duration in hours between incident detection and resolution/closure.
    grain_scope: Incident; aggregated by org / system / severity and period.
    unit_format: hours (1 decimal)
    interpretation: Lower MTTR indicates faster response and containment; very low values must still be checked against data
      quality.
  technical:
    dax_name: Security Incident MTTR (Hours)
    depends_on_measures: []
    lineage:
    - fact_sec_incident.DetectedAt
    - fact_sec_incident.ResolvedAt
  governance:
    business_owner: CISO
    data_owner: Security Operations
    steward: Security Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Durations validated; negative or extreme outliers investigated
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
```

