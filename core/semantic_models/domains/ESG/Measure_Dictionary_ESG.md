# Measure Dictionary - ESG

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Safety Incident Count
  is_kpi_measure: true
  kpi_id_ref: KPI-OPS-015
  category: KPI
  expression:
    logical: Safety Incident Count = Count of recorded safety incidents in the selected period.
    aggregation_method: count
  dependencies:
    columns:
    - fact_safety[Incident ID]
  governance:
    status: active
    version: v0.1
    owner: EHS Manager
    last_review: 2026-04-03
  semantic_model: ESG_SemanticModel
  display_folder: 01_Safety
  documentation:
    description: Count of safety incidents used as the minimum governed ESG measure set.
    notes: 'Grain: site_month. Unit: count.

      Lineage: fact_safety[Incident ID].

      QA: Exclude duplicated incident records and keep reporting period aligned with EHS close.

      '
```

