# Measure Dictionary - People / HR

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ALUCA Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Digital Adoption %
  is_kpi_measure: true
  kpi_id_ref: people.digital_adoption.pct
  category: KPI
  expression:
    logical: Digital Adoption % = DIVIDE ( SUM ( fact_it[Digital Users] ), SUM ( fact_hr[Headcount] ) )
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
    status: active
    version: v1.2
    last_review: TBD
    owner: People Analytics
  semantic_model: People_SemanticModel
  display_folder: 03_Digital
```

