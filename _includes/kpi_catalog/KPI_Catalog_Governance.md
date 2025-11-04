# KPI Catalog – Governance & Compliance

---

## Catalog Schema
```yaml
# Fields for each KPI entry
kpi_id: "namespace.identifier"           # ASCII, namespaced, unique
kpi_key: "Readable KPI Name"             # Human-readable title
kpi_type: "strategic|diagnostic|supporting"
domain_tag: ["…"]                         # One or more domains
impact_dimension: "Growth|Profitability|Liquidity|Efficiency|Customer|ESG|Governance"
use_case_ref: ["COM-001"]               # Optional UC references
calc_type: "amount|rate|ratio|count"
technical:
  dax_name: "Measure Name"
  dax_expression: "...optional..."
  formatString: "..."
  displayFolder: "...optional..."
  description: "Short purpose/definition"
aliases: ["Optional alternative names"]
verified: false
```

## KPIs - Strategic
```yaml
- kpi_key: "Data Quality %"
  kpi_type: "strategic"
  strategic_ref: "Data Quality %"
  impact_dimension: "Governance"
  domain_tag: ["Data Governance"]
  use_case_ref: ["GOV-001"]
  depends_on: ["Valid Records Count","Total Records Count"]
  calc_type: ratio
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
```

```yaml
- kpi_key: "Compliance Breach Count"
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

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_key: "Open Audit Findings Count"
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
    dax_expression: "COUNTROWS(FILTER(fact_audit,[Status]="Open"))"
    lineage: ["fact_audit.AuditFindingID"]
    source_grain: "audit_record"
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
- kpi_key: "Valid Records Count"
  kpi_type: "base"
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

## 4. Governance Summary
| Metric | Value |
|--------|--------|
| **Total KPIs (Governance)** | 31 |
| **Completeness Score (avg)** | 0.97 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Monthly |
| **Business Owner** | Chief Data Officer |
| **Data Owner** | Data Governance Team |
| **Steward** | Data Steward |
| **Validation Process** | Automated |

---

_Last updated: 12.10.2025_
 
## 2. Project Portfolio KPIs (added)
```yaml
- kpi_id: "corp.project.roi.pct"
  kpi_key: "Project ROI %"
  kpi_type: "strategic"
  domain_tag: ["Corporate & Strategy"]
  calc_type: rate
  technical:
    dax_name: "Project ROI %"
    description: "(Realized Benefits - Total Cost) / Total Cost"
    formatString: "0.0 %"
```

```yaml
- kpi_id: "corp.benefit.realization.pct"
  kpi_key: "Benefit Realization %"
  kpi_type: "diagnostic"
  domain_tag: ["Corporate & Strategy"]
  calc_type: rate
  technical:
    dax_name: "Benefit Realization %"
    description: "Realized Benefits / Planned Benefits"
    formatString: "0.0 %"
```

```yaml
- kpi_id: "corp.budget.adherence.pct"
  kpi_key: "Budget Adherence %"
  kpi_type: "diagnostic"
  domain_tag: ["Corporate & Strategy"]
  calc_type: rate
  technical:
    dax_name: "Budget Adherence %"
    description: "Actual Cost / Planned Cost"
    formatString: "0.0 %"
```

```yaml
- kpi_id: "corp.schedule.adherence.pct"
  kpi_key: "Schedule Adherence %"
  kpi_type: "diagnostic"
  domain_tag: ["Corporate & Strategy"]
  calc_type: rate
  technical:
    dax_name: "Schedule Adherence %"
    description: "Actual Progress / Planned Progress"
    formatString: "0.0 %"
```

```yaml
- kpi_id: "corp.payback.months"
  kpi_key: "Payback Period (Months)"
  kpi_type: "diagnostic"
  domain_tag: ["Corporate & Strategy"]
  calc_type: amount
  technical:
    dax_name: "Payback Period (Months)"
    description: "Time until cumulative benefits = total cost"
    formatString: "0"
```
