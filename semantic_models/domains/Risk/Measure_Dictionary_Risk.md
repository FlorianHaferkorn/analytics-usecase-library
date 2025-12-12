# Measure Dictionary - Risk

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: PD %
  is_kpi_measure: true
  kpi_id_ref: fin.risk.pd.pct
  semantic_model: Risk_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Probability of Default per exposure or segment; used in expected loss and capital calculations.
    notes: ''
  governance:
    owner: Risk Analytics
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 06_Risk\Credit Risk
  dependencies:
    columns:
    - fact_credit_risk.PD
- measure_name: LGD %
  is_kpi_measure: true
  kpi_id_ref: fin.risk.lgd.pct
  semantic_model: Risk_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: Loss Given Default percentage per exposure or segment.
    notes: ''
  governance:
    owner: Risk Analytics
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 06_Risk\Credit Risk
  dependencies:
    columns:
    - fact_credit_risk.LGD
- measure_name: EAD Amount
  is_kpi_measure: true
  kpi_id_ref: fin.risk.ead.amount
  semantic_model: Risk_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Exposure at Default amount per facility or segment.
    notes: ''
  governance:
    owner: Risk Analytics
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 06_Risk\Credit Risk
  dependencies:
    columns:
    - fact_credit_risk.EAD
```
