# Measure Dictionary - Innovation & People

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

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

      QA: Headcount > 0; identity consistency.

      '
  dependencies:
    columns:
    - fact_it[Digital Users]
    - fact_hr[Headcount]
  governance:
    status: active
    version: v1.2
    last_review: TBD
    owner: Innovation Analytics
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 02_Digital

- measure_name: Digital Adoption Rate %
  is_kpi_measure: true
  kpi_id_ref: KPI-SVC-002
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 02_Digital
  category: KPI
  expression:
    logical: Digital Adoption Rate % = Alias for Digital Adoption % (TMDL display name).
    aggregation_method: ratio
  documentation:
    description: Alias for Digital Adoption % (TMDL display name).
    notes: Same as Digital Adoption %.
  dependencies:
    columns: []
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Attrition Risk %
  is_kpi_measure: true
  kpi_id_ref: KPI-SVC-003
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Attrition Risk % = Probability of attrition for the selected population in the period.
    aggregation_method: ratio
  documentation:
    description: Average attrition risk for the selected population.
    notes: 'Grain: month. Unit: %.

      QA: Bounded between 0% and 100%.

      '
  dependencies:
    columns:
    - fact_hr[Attrition Risk %]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Gross Margin Amount
  is_kpi_measure: true
  kpi_id_ref: KPI-COM-019
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Gross Margin Amount = [Net Sales Amount] - [Cost of Goods Sold Amount]
    aggregation_method: sum
  documentation:
    description: Gross margin amount for the selected period.
    notes: 'Grain: month. Unit: EUR.

      QA: Reconciles to Finance gross margin.

      '
  dependencies:
    columns:
    - fact_financials[GrossMarginAmount]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD
```

