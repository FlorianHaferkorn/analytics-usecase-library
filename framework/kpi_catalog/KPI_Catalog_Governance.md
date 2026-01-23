# KPI Catalog - Governance

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: enterprise.action_outcome_rate.pct
  kpi_key: Action Outcome Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - XD-003
  action_code_ref:
  - X-E3.3
  calc_type: rate
  business:
    purpose: Measures share of actions that achieved the intended outcome.
    definition: Successful Actions / Routed Actions.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better execution effectiveness.
  technical:
    dax_name: Action Outcome Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: enterprise.action_routed.count
  kpi_key: Actions Routed Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: count
  business:
    purpose: Counts action codes routed for execution.
    definition: Count of routed action instances in the period.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: count
    interpretation: Higher counts indicate more routed actions.
  technical:
    dax_name: Actions Routed Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD
```
