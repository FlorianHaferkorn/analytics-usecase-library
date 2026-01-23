# KPI Catalog - InnovationPeople

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: people.digital_adoption.pct

  kpi_key: Digital Adoption Rate %

  kpi_type: percentage

  kpi_role: strategic

  impact_dimension: Innovation & People

  domain_tag:

  - Corporate & Strategy

  use_case_ref:

  - INN-002

  calc_type: ratio

  business:

    purpose: Measure how much of all eligible process transactions are executed via digital tools instead of manual channels.

    definition: Digital Transactions Count / Total Transactions Count for eligible processes.

    grain_scope: Process area / org; aggregated monthly or quarterly.

    unit_format: '% (1 decimal)'

    interpretation: Higher values indicate greater adoption of digital processes; low values show manual work and automation

      potential.

  technical:

    dax_name: Digital Adoption Rate %

    depends_on_measures:

    - Digital Transactions Count

    - Total Transactions Count

    lineage:

    - fact_digital_usage.TransactionsCount

  governance:

    business_owner: Head of Digital Transformation

    data_owner: Corporate BI

    steward: Digital Adoption Analyst

    review_cycle: quarterly

    validation_process: comparison with process mining and application telemetry

    qa_rules:

    - Eligible processes flagged correctly; adoption bounded between 0 % and 100 %

    version: v1.0

  metadata_quality:

    completeness_score: 0.85

    last_review: 19.11.2025



- kpi_id: people.attrition_risk.pct
  kpi_key: Attrition Risk %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: governance
  domain_tag:
  - Human Resources
  use_case_ref:
  - XD-003
  calc_type: rate
  business:
    purpose: Monitor risk of employee attrition across key roles and segments.
    definition: Probability of attrition for the selected population in the period.
    grain_scope: Org/role/segment; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher values signal retention risk and require targeted actions.
  technical:
    dax_name: Attrition Risk %
    depends_on_measures: []
    lineage:
    - fact_hr.Attrition Risk %
    - fact_hr.Headcount
    - fact_hr.Leavers
  governance:
    business_owner: Head of HR
    data_owner: People Analytics
    steward: HR Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Attrition risk bounded between 0 % and 100 %
    - Headcount > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
```
