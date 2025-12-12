# Measure Dictionary - Governance

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Data Quality %"
  is_kpi_measure: true
  kpi_id_ref: "gov.data_quality.pct"
  semantic_model: "Governance_SemanticModel"
  display_folder: "01_Data"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Data Quality % */"
    formatString: "0.0%"
  documentation:
    description: "Valid records divided by total records."
    notes: |
      Grain: dataset/month. Unit: %.
      Lineage: fact_dq[Valid Records], fact_dq[Total Records].
      QA: Total > 0; certification rules applied.
  dependencies:
    columns:
      - "fact_dq[Valid Records]"
      - "fact_dq[Total Records]"
  governance:
    owner: "Data Governance"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Records Total Count"
  is_kpi_measure: true
  kpi_id_ref: "gov.records.total.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "01_Data"
  category: "KPI"
  expression:
    dax: "SUM(fact_dq[Total Records])"
    formatString: "#,0"
  documentation:
    description: "Total records processed."
    notes: |
      Grain: dataset/month. Unit: count.
      Lineage: fact_dq[Total Records].
      QA: One row per dataset/month; avoid duplicates.
  dependencies:
    columns:
      - "fact_dq[Total Records]"
  governance:
    owner: "Data Governance"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Valid Records Count"
  is_kpi_measure: true
  kpi_id_ref: "gov.valid_records.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "01_Data"
  category: "KPI"
  expression:
    dax: "SUM(fact_dq[Valid Records])"
    formatString: "#,0"
  documentation:
    description: "Count of valid records."
    notes: |
      Grain: dataset/month. Unit: count.
      Lineage: fact_dq[Valid Records].
      QA: Validation rules documented; no double counting.
  dependencies:
    columns:
      - "fact_dq[Valid Records]"
  governance:
    owner: "Data Governance"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Compliance Incidents Count"
  is_kpi_measure: true
  kpi_id_ref: "gov.compliance.incidents.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "02_Compliance"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Compliance Incidents Count */"
    formatString: "#,0"
  documentation:
    description: "Number of compliance incidents."
    notes: |
      Grain: month. Unit: count.
      Lineage: fact_compliance[Incidents].
      QA: Clear incident definition; avoid duplicates.
  dependencies:
    columns:
      - "fact_compliance[Incidents]"
  governance:
    owner: "Compliance"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Compliance Breach Count"
  is_kpi_measure: true
  kpi_id_ref: "gov.compliance.breach.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "02_Compliance"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Compliance Breach Count */"
    formatString: "#,0"
  documentation:
    description: "Number of compliance breaches."
    notes: |
      Grain: month. Unit: count.
      Lineage: fact_compliance[Breaches].
      QA: Zero tolerance tracking; consistent severity rules.
  dependencies:
    columns:
      - "fact_compliance[Breaches]"
  governance:
    owner: "Compliance"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Audit Findings Count"
  is_kpi_measure: true
  kpi_id_ref: "gov.audit.findings.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "03_Audit"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Audit Findings Count */"
    formatString: "#,0"
  documentation:
    description: "Total audit findings."
    notes: |
      Grain: audit. Unit: count.
      Lineage: fact_audit[Findings].
      QA: One row per finding; status codes consistent.
  dependencies:
    columns:
      - "fact_audit[Findings]"
  governance:
    owner: "Internal Audit"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Open Audit Findings Count"
  is_kpi_measure: true
  kpi_id_ref: "gov.audit.findings.open.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "03_Audit"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Open Audit Findings Count */"
    formatString: "#,0"
  documentation:
    description: "Open audit findings."
    notes: |
      Grain: audit. Unit: count.
      Lineage: fact_audit[Open Findings].
      QA: Status transitions tracked; avoid stale items.
  dependencies:
    columns:
      - "fact_audit[Open Findings]"
  governance:
    owner: "Internal Audit"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Project ROI %"
  is_kpi_measure: true
  kpi_id_ref: "corp.project.roi.pct"
  semantic_model: "Governance_SemanticModel"
  display_folder: "04_Portfolio"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Project ROI % */"
    formatString: "0.0%"
  documentation:
    description: "Project ROI."
    notes: |
      Grain: project. Unit: %.
      Lineage: fact_projects[Benefit], fact_projects[Cost].
      QA: Benefit/cost definitions; currency alignment.
  dependencies:
    columns:
      - "fact_projects[Benefit]"
      - "fact_projects[Cost]"
  governance:
    owner: "Portfolio Management"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Benefit Realization %"
  is_kpi_measure: true
  kpi_id_ref: "corp.benefit.realization.pct"
  semantic_model: "Governance_SemanticModel"
  display_folder: "04_Portfolio"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Benefit Realization % */"
    formatString: "0.0%"
  documentation:
    description: "Realized benefit / planned benefit."
    notes: |
      Grain: project. Unit: %.
      Lineage: fact_projects[Benefit], fact_projects[Planned Benefit].
      QA: Plan available; avoid double counting benefits.
  dependencies:
    columns:
      - "fact_projects[Benefit]"
      - "fact_projects[Planned Benefit]"
  governance:
    owner: "Portfolio Management"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Budget Adherence %"
  is_kpi_measure: true
  kpi_id_ref: "corp.budget.adherence.pct"
  semantic_model: "Governance_SemanticModel"
  display_folder: "04_Portfolio"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Budget Adherence % */"
    formatString: "0.0%"
  documentation:
    description: "Actual vs budget for projects."
    notes: |
      Grain: project. Unit: %.
      Lineage: fact_projects[Actual Cost], fact_projects[Budget].
      QA: Budget versioning; DIVIDE guard.
  dependencies:
    columns:
      - "fact_projects[Actual Cost]"
      - "fact_projects[Budget]"
  governance:
    owner: "Portfolio Management"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Schedule Adherence %"
  is_kpi_measure: true
  kpi_id_ref: "corp.schedule.adherence.pct"
  semantic_model: "Governance_SemanticModel"
  display_folder: "04_Portfolio"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Schedule Adherence % */"
    formatString: "0.0%"
  documentation:
    description: "On-time milestones / total milestones."
    notes: |
      Grain: project. Unit: %.
      Lineage: fact_projects[Milestone On Time], fact_projects[Milestone Total].
      QA: Milestone tracking completeness; DIVIDE guard.
  dependencies:
    columns:
      - "fact_projects[Milestone On Time]"
      - "fact_projects[Milestone Total]"
  governance:
    owner: "Portfolio Management"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Payback Period (months)"
  is_kpi_measure: true
  kpi_id_ref: "corp.payback.months"
  semantic_model: "Governance_SemanticModel"
  display_folder: "04_Portfolio"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Payback Period (months) */"
    formatString: "0"
  documentation:
    description: "Months to recover investment."
    notes: |
      Grain: project. Unit: months.
      Lineage: fact_projects[Cashflows].
      QA: Cashflow assumptions documented; discounting handled upstream if applicable.
  dependencies:
    columns:
      - "fact_projects[Cashflows]"
  governance:
    owner: "Portfolio Management"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Security Incidents Count"
  is_kpi_measure: true
  kpi_id_ref: "sec.incident.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "05_Security"
  category: "KPI"
  expression:
    dax: "SUM(fact_security[Incidents])"
    formatString: "#,0"
  documentation:
    description: "Number of security incidents."
    notes: |
      Grain: month. Unit: count.
      Lineage: fact_security[Incidents].
      QA: Severity tagging; avoid duplicates.
  dependencies:
    columns:
      - "fact_security[Incidents]"
  governance:
    owner: "Security"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Critical Security Incidents Count"
  is_kpi_measure: true
  kpi_id_ref: "sec.incident.critical.count"
  semantic_model: "Governance_SemanticModel"
  display_folder: "05_Security"
  category: "KPI"
  expression:
    dax: "SUM(fact_security[Critical Incidents])"
    formatString: "#,0"
  documentation:
    description: "Number of critical security incidents."
    notes: |
      Grain: month. Unit: count.
      Lineage: fact_security[Critical Incidents].
      QA: Criticality criteria documented.
  dependencies:
    columns:
      - "fact_security[Critical Incidents]"
  governance:
    owner: "Security"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Security MTTR (hours)"
  is_kpi_measure: true
  kpi_id_ref: "sec.incident.mttr.hours"
  semantic_model: "Governance_SemanticModel"
  display_folder: "05_Security"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Security MTTR */"
    formatString: "0.0"
  documentation:
    description: "Mean time to recover security incidents."
    notes: |
      Grain: month. Unit: hours.
      Lineage: fact_security[MTTR].
      QA: Time capture consistent; excludes pending cases as needed.
  dependencies:
    columns:
      - "fact_security[MTTR]"
  governance:
    owner: "Security"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
