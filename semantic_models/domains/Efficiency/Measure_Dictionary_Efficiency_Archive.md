# Measure Dictionary Archive - Efficiency

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Planned Hours
  is_kpi_measure: true
  kpi_id_ref: ops.planned.hours
  semantic_model: Efficiency_SemanticModel
  category: KPI
  expression:
    dax: "DIVIDE ( SUM ( fact_ops[Planned Time Minutes] ), 60 )"
    formatString: '0.00'
  documentation:
    description: Sum of planned production hours
    notes: ''
  governance:
    owner: Supply Chain BI
    status: active
    version: v1.0
    last_review: 04.11.2025
```

