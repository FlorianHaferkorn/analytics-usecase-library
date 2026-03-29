# Measure Dictionary - People / HR

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Digital Adoption %
  is_kpi_measure: true
  kpi_id_ref: people.digital_adoption.pct
  semantic_model: People_SemanticModel
  display_folder: 03_Digital
  category: KPI
  expression:
    logical: Digital Adoption % = Digital Transactions Count / Total Transactions Count for eligible processes.
    aggregation_method: ratio
  documentation:
    description: Digital tool users divided by total employees.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_it[Digital Users], fact_hr[Headcount].

      QA: Headcount > 0; user identity consistent.

      '
  dependencies:
    columns:
    - fact_it[Digital Users]
    - fact_hr[Headcount]
  governance:
    owner: People Analytics
    status: active
    version: v1.2
    last_review: TBD
```

