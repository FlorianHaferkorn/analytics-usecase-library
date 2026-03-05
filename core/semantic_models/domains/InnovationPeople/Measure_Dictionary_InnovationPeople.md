# Measure Dictionary - Innovation & People

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Digital Adoption %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 02_Digital
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Digital Adoption Rate %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 02_Digital
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Alias for Digital Adoption % (TMDL display name).
    notes: Same as Digital Adoption %.
  dependencies:
    columns: []
  governance:
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Gross Margin per FTE Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Gross margin per FTE.
    notes: 'Grain: month. Unit: EUR per FTE.

      Lineage: fact_financials[GrossMarginAmount], fact_hr_headcount[FTEFactor].

      QA: FTE > 0; currency alignment.

      '
  dependencies:
    measures:
    - '[Gross Margin Amount]'
    - '[Average FTE]'
  governance:
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Personnel Cost Ratio %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Personnel cost / revenue.
    notes: 'Grain: month. Unit: %.

      Lineage: fact_hr_cost[PersonnelCost], fact_financials[RevenueAmount].

      QA: Revenue > 0; cost completeness.

      '
  dependencies:
    measures:
    - '[Personnel Cost Amount]'
    - '[Revenue Amount]'
  governance:
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Revenue per FTE
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  formatString: 'EUR #,0'
  documentation:
    description: Total revenue divided by average FTE.
    notes: 'Grain: month. Unit: EUR per FTE.

      QA: FTE > 0; revenue reconciles to finance totals.

      '
  dependencies:
    measures:
    - '[Revenue Amount]'
    - '[Average FTE]'
  governance:
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Attrition Risk %
  is_kpi_measure: true
  kpi_id_ref: people.attrition_risk.pct
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Turnover Rate %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Employee exits divided by average headcount.
    notes: 'Grain: month. Unit: %.

      QA: Headcount > 0; exits non-negative.

      '
  dependencies:
    measures:
    - '[Exits Count]'
    - '[Average Headcount]'
  governance:
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Absenteeism %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Absent hours divided by scheduled hours.
    notes: 'Grain: month. Unit: %.

      QA: Scheduled hours > 0; absenteeism bounded 0-100%.

      '
  dependencies:
    measures:
    - '[Absent Hours]'
    - '[Scheduled Hours]'
  governance:
    owner: Innovation Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Gross Margin Amount
  is_kpi_measure: true
  kpi_id_ref: hr.gm.amount
  semantic_model: InnovationPeople_SemanticModel
  display_folder: 04_People
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
```

