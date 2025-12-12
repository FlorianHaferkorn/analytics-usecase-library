# Measure Dictionary - Risk

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Probability of Default (PD) %"
  is_kpi_measure: true
  kpi_id_ref: "fin.risk.pd.pct"
  semantic_model: "Risk_SemanticModel"
  display_folder: "01_CreditRisk"
  category: "KPI"
  expression:
    dax: "/* TODO: implement PD % */"
    formatString: "0.0%"
  documentation:
    description: "Default probability over a defined horizon."
    notes: |
      Grain: exposure/month. Unit: %.
      Lineage: fact_credit_risk[PD].
      QA: PD within 0-100%; model version documented.
  dependencies:
    columns:
      - "fact_credit_risk[PD]"
  governance:
    owner: "Risk Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Loss Given Default (LGD) %"
  is_kpi_measure: true
  kpi_id_ref: "fin.risk.lgd.pct"
  semantic_model: "Risk_SemanticModel"
  display_folder: "01_CreditRisk"
  category: "KPI"
  expression:
    dax: "/* TODO: implement LGD % */"
    formatString: "0.0%"
  documentation:
    description: "Loss severity on default."
    notes: |
      Grain: exposure/month. Unit: %.
      Lineage: fact_credit_risk[LGD].
      QA: LGD within 0-100%; assumptions documented.
  dependencies:
    columns:
      - "fact_credit_risk[LGD]"
  governance:
    owner: "Risk Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Exposure at Default Amount"
  is_kpi_measure: true
  kpi_id_ref: "fin.risk.ead.amount"
  semantic_model: "Risk_SemanticModel"
  display_folder: "01_CreditRisk"
  category: "KPI"
  expression:
    dax: "SUM(fact_credit_risk[EAD])"
    formatString: "EUR #,0"
  documentation:
    description: "Exposure amount at default."
    notes: |
      Grain: exposure/month. Unit: EUR.
      Lineage: fact_credit_risk[EAD].
      QA: Currency alignment; EAD definition consistent.
  dependencies:
    columns:
      - "fact_credit_risk[EAD]"
  governance:
    owner: "Risk Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
