# KPI Catalog - Risk

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml

```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: enterprise.value_at_risk.index
  kpi_key: Enterprise Value-at-Risk Index
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Risk
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - XD-003
  action_code_ref:
  - X-E3.2
  calc_type: ratio
  business:
    purpose: Aggregates downside risk across domains into a single index.
    definition: Weighted index of normalized domain risk signals.
    grain_scope: Entity or business unit; aggregated by period.
    unit_format: index
    interpretation: Higher index indicates higher enterprise risk exposure.
  technical:
    dax_name: Enterprise Value-at-Risk Index
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Chief Risk Officer
    data_owner: Enterprise Risk
    steward: Risk Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: scm.supplier_risk.score
  kpi_key: Supplier Risk Score
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Risk
  domain_tag:
  - Supply Chain
  use_case_ref:
  - FIN-001
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Rates suppliers based on risk indicators.
    definition: Composite risk score derived from supplier risk factors.
    grain_scope: Supplier; aggregated by period.
    unit_format: score
    interpretation: Higher scores indicate higher supplier risk.
  technical:
    dax_name: Supplier Risk Score
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Supply Chain BI
    steward: Supplier Risk Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD
```
