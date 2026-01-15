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
    dax: |
      AVERAGEX ( VALUES ( fact_credit_risk[Exposure ID] ), fact_credit_risk[PD] )
    formatString: "0.0%"
  documentation:
    description: "Default probability over a defined horizon."
    notes: |
      Grain: exposure/month. Unit: %.
      Lineage: fact_credit_risk[PD].
      QA: PD within 0-100%; model version documented; horizon (e.g., 12M) documented.
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
    dax: |
      AVERAGEX ( VALUES ( fact_credit_risk[Exposure ID] ), fact_credit_risk[LGD] )
    formatString: "0.0%"
  documentation:
    description: "Loss severity on default."
    notes: |
      Grain: exposure/month. Unit: %.
      Lineage: fact_credit_risk[LGD].
      QA: LGD within 0-100%; assumptions documented; scenario/version tracked.
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
      QA: Currency alignment; EAD definition consistent; conversion factors applied.
  dependencies:
    columns:
      - "fact_credit_risk[EAD]"
  governance:
    owner: "Risk Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
- measure_name: "Enterprise Value-at-Risk Index"
  is_kpi_measure: true
  kpi_id_ref: "enterprise.value_at_risk.index"
  semantic_model: "Risk_SemanticModel"
  display_folder: "02_Enterprise"
  category: "KPI"
  expression:
    dax: "AVERAGE ( fact_risk[Value at Risk Index] )"
    formatString: "0.0"
  documentation:
    description: "Composite enterprise risk index based on domain signals."
    notes: |
      Grain: entity_month. Unit: index.
      Lineage: fact_risk[Value at Risk Index].
      QA: Weighting logic documented in upstream model.
  dependencies:
    columns:
      - "fact_risk[Value at Risk Index]"
  governance:
    owner: "Risk Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"

- measure_name: "Supplier Risk Score"
  is_kpi_measure: true
  kpi_id_ref: "scm.supplier_risk.score"
  semantic_model: "Risk_SemanticModel"
  display_folder: "03_Supply"
  category: "KPI"
  expression:
    dax: "AVERAGE ( fact_supplier_risk[Risk Score] )"
    formatString: "0.0"
  documentation:
    description: "Average supplier risk score across the selected scope."
    notes: |
      Grain: supplier_month. Unit: score.
      Lineage: fact_supplier_risk[Risk Score].
      QA: Supplier score normalization documented.
  dependencies:
    columns:
      - "fact_supplier_risk[Risk Score]"
  governance:
    owner: "Risk Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"
```
