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
  use_case_ref: ["GOV-001"]
  depends_on: ["Valid Records Count","Total Records Count"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Measures data accuracy and completeness in governed systems."
    definition: "(Valid Records / Total Records) × 100"
    grain_scope: "Dataset level; aggregated monthly."
    unit_format: "% (1 decimal)"
    interpretation: "Indicates trustworthiness of analytical data assets."
  technical:
    dax_name: "Data Quality %"
    dax_expression: "DIVIDE([Valid Records Count],[Total Records Count])"
    lineage: ["fact_dq.ValidRecords","fact_dq.TotalRecords"]
    source_grain: "dataset"
    source_column_ref: ["fact_dq.valid_records","fact_dq.total_records"]
    source_system: "Data Quality Platform"
    verified: true
  governance:
    business_owner: "Chief Data Officer"
    data_owner: "Data Governance Team"
    steward: "Data Steward"
    review_cycle: "monthly"
    validation_process: "automated"
    qa_rules:
      - "DQ % ≥ 98 % for certified datasets"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.99
    lineage_verified: true
    copilot_ready: true

- kpi_id: "gov.compliance.breach.count"
  kpi_key: "Compliance Breach Count"
  kpi_type: "strategic"
  strategic_ref: "Compliance Breach Count"
  impact_dimension: "Governance"
  domain_tag: ["Compliance"]
  use_case_ref: ["GOV-003"]
  depends_on: ["Breach Incidents"]
  calc_type: count
  refresh: monthly
  status: Active
  business:
    purpose: "Tracks number of confirmed compliance or regulatory breaches."
    definition: "Count of recorded confirmed compliance incidents."
    grain_scope: "Organization level; per reporting period."
    unit_format: "count"
    interpretation: "High numbers indicate weak compliance culture."
  technical:
    dax_name: "Compliance Breach Count"
    dax_expression: "COUNTROWS(fact_compliance)"
    lineage: ["fact_compliance.IncidentID"]
    source_grain: "incident_record"
    source_column_ref: ["fact_compliance.incident_id"]
    source_system: "Compliance Management"
    verified: true
  governance:
    business_owner: "Chief Compliance Officer"
    data_owner: "Compliance BI"
    steward: "Compliance Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "All incidents classified before quarter-end"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "gov.audit.findings.open.count"
  kpi_key: "Open Audit Findings Count"
  kpi_type: "supporting"
  strategic_ref: "Audit Finding Severity %"
  impact_dimension: "Governance"
  domain_tag: ["Audit"]
  use_case_ref: ["GOV-004"]
  depends_on: ["Audit Findings"]
  calc_type: count
  refresh: quarterly
  status: Active
  business:
    purpose: "Number of unresolved audit findings still open."
    definition: "Count of findings with status = open."
    grain_scope: "Audit report level."
    unit_format: "count"
    interpretation: "Shows audit remediation backlog."
  technical:
    dax_name: "Open Audit Findings Count"
    dax_expression: "COUNTROWS(fact_audit_findings)"
    lineage: ["fact_audit.finding_id"]
    source_grain: "audit_report"
    source_column_ref: ["fact_audit.finding_id"]
    source_system: "Audit System"
    verified: true
  governance:
    business_owner: "Head of Internal Audit"
    data_owner: "Audit BI"
    steward: "Audit Coordinator"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "All closed findings verified by audit committee"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
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
    dax_expression: "SUM(fact_dq[Valid Records Count])"
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
      - "Must be ≥ 0"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 1.00
    lineage_verified: true
    copilot_ready: true
```

---

Last updated: 04.11.2025

