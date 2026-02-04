# Measure Dictionary - Risk

Schema: see `framework/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
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

