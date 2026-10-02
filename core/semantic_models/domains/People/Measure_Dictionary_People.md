# Measure Dictionary - People / HR

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Digital Adoption %
  is_kpi_measure: true
  kpi_id_ref: KPI-SVC-002
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

- measure_name: Attrition %
  is_kpi_measure: true
  kpi_id_ref: KPI-PPL-001
  semantic_model: People_SemanticModel
  display_folder: 01_Retention
  category: KPI
  expression:
    logical: Attrition % = DIVIDE ( SUM ( fact_workforce[Voluntary Leavers] ), SUM ( fact_workforce[Headcount FTE] ) ) * 12
    aggregation_method: ratio
  documentation:
    description: Voluntary leavers divided by headcount FTE, annualised from the monthly rate.
    notes: 'Grain: org/segment, monthly, annualised. Unit: %.

      Lineage: fact_workforce[Voluntary Leavers], fact_workforce[Headcount FTE].

      Expression synthesized from the governed catalog calculation (KPI-PPL-001, op ratio, scale 12) via tooling/superversion/targets/dax_synth.py; not yet measured against Aurora gold data.

      QA: Denominator > 0 for reported slices.

      '
  dependencies:
    columns:
    - fact_workforce[Voluntary Leavers]
    - fact_workforce[Headcount FTE]
  governance:
    owner: People Analytics
    status: experimental
    version: v0.1
    last_review: 02.10.2026
```

