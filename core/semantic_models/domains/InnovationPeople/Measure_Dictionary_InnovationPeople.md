# Measure Dictionary - Innovation & People

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

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
  kpi_id_ref: people.digital_adoption.pct
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

- measure_name: Gross Margin per FTE Amount
  is_kpi_measure: true
  kpi_id_ref: people.gm_per_fte.amount
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Gross Margin per FTE Amount = DIVIDE ( [Gross Margin Amount], SUM ( fact_hr[FTE] ) )
    aggregation_method: ratio
  documentation:
    description: Gross margin per FTE.
    notes: 'Grain: month. Unit: EUR per FTE.

      Lineage: fact_financials[GrossMarginAmount], fact_hr_headcount[FTEFactor].

      QA: FTE > 0; currency alignment.

      '
  dependencies:
    columns:
    - fact_hr[FTE]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Personnel Cost Ratio %
  is_kpi_measure: true
  kpi_id_ref: people.personnel_cost.pct
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Personnel Cost Ratio % = DIVIDE ( SUM ( fact_hr[Personnel Cost] ), SUM ( fact_sales[Net Sales Amount] ) )
    aggregation_method: ratio
  documentation:
    description: Personnel cost / revenue.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_hr_cost[PersonnelCost], fact_financials[RevenueAmount].

      QA: Revenue > 0; cost completeness.

      '
  dependencies:
    columns:
    - fact_hr[Personnel Cost]
    - fact_sales[Net Sales Amount]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Revenue per FTE
  is_kpi_measure: true
  kpi_id_ref: people.revenue_per_fte.amount
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Revenue per FTE = DIVIDE ( SUM ( fact_sales[Net Sales Amount] ), SUM ( fact_hr[FTE] ) )
    aggregation_method: ratio
  formatString: 'EUR #,0'
  documentation:
    description: Total revenue divided by average FTE.
    notes: 'Grain: month. Unit: EUR per FTE.

      QA: FTE > 0; revenue reconciles to finance totals.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_hr[FTE]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Attrition Risk %
  is_kpi_measure: true
  kpi_id_ref: people.attrition_risk.pct
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

- measure_name: Turnover Rate %
  is_kpi_measure: true
  kpi_id_ref: people.turnover.pct
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Turnover Rate % = DIVIDE ( SUM ( fact_hr[Leavers] ), AVERAGE ( fact_hr[Headcount] ) )
    aggregation_method: ratio
  documentation:
    description: Employee exits divided by average headcount.
    notes: 'Grain: month. Unit: %.

      QA: Headcount > 0; exits non-negative.

      '
  dependencies:
    columns:
    - fact_hr[Leavers]
    - fact_hr[Headcount]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Absenteeism %
  is_kpi_measure: true
  kpi_id_ref: people.absenteeism.pct
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: Absenteeism % = DIVIDE ( SUM ( fact_hr[Absent Hours] ), SUM ( fact_hr[Scheduled Hours] ) )
    aggregation_method: ratio
  documentation:
    description: Absent hours divided by scheduled hours.
    notes: 'Grain: month. Unit: %.

      QA: Scheduled hours > 0; absenteeism bounded 0-100%.

      '
  dependencies:
    columns:
    - fact_hr[Absent Hours]
    - fact_hr[Scheduled Hours]
  governance:
    owner: Innovation Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Gross Margin Amount
  is_kpi_measure: true
  kpi_id_ref: margin.gm.amount
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

