# Measure Dictionary - People / HR

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Employee Turnover %"
  is_kpi_measure: true
  kpi_id_ref: "hr.turnover.pct"
  semantic_model: "People_SemanticModel"
  display_folder: "01_People"
  category: "KPI"
  expression:
    dax: |
      VAR Leavers = SUM ( fact_hr[Leavers] )
      VAR AvgHC   = AVERAGEX ( VALUES ( dim_date[MonthKey] ), SUM ( fact_hr[Headcount] ) )
      RETURN DIVIDE ( Leavers, AvgHC )
    formatString: "0.0%"
  documentation:
    description: "Leavers divided by average headcount."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_hr[Leavers], fact_hr[Headcount].
      QA: Headcount > 0; consistent leaver definition.
  dependencies:
    columns:
      - "fact_hr[Leavers]"
      - "fact_hr[Headcount]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Absenteeism %"
  is_kpi_measure: true
  kpi_id_ref: "hr.absenteeism.pct"
  semantic_model: "People_SemanticModel"
  display_folder: "01_People"
  category: "KPI"
  expression:
    dax: |
      VAR Absent   = SUM ( fact_hr[Absent Hours] )
      VAR Scheduled = SUM ( fact_hr[Scheduled Hours] )
      RETURN DIVIDE ( Absent, Scheduled )
    formatString: "0.0%"
  documentation:
    description: "Absent hours divided by scheduled hours."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_hr[Absent Hours], fact_hr[Scheduled Hours].
      QA: Scheduled Hours > 0; time capture consistent.
  dependencies:
    columns:
      - "fact_hr[Absent Hours]"
      - "fact_hr[Scheduled Hours]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "GM per FTE Amount"
  is_kpi_measure: true
  kpi_id_ref: "hr.gm_per_fte.amount"
  semantic_model: "People_SemanticModel"
  display_folder: "02_Productivity"
  category: "KPI"
  expression:
    dax: |
      VAR GM  = SUM ( fact_sales[Net Sales Amount] ) - SUM ( fact_sales[Cost of Goods Sold Amount] )
      VAR FTE = SUM ( fact_hr[FTE] )
      RETURN DIVIDE ( GM, FTE )
    formatString: "EUR #,0.00"
  documentation:
    description: "Gross margin divided by FTE."
    notes: |
      Grain: month. Unit: EUR per FTE.
      Lineage: fact_sales[Net Sales Amount], fact_sales[COGS], fact_hr[FTE].
      QA: FTE > 0; currency alignment.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "fact_hr[FTE]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Personnel Cost Ratio %"
  is_kpi_measure: true
  kpi_id_ref: "hr.personnel_cost_ratio.pct"
  semantic_model: "People_SemanticModel"
  display_folder: "02_Productivity"
  category: "KPI"
  expression:
    dax: |
      VAR Cost = SUM ( fact_hr[Personnel Cost] )
      VAR Rev  = SUM ( fact_finance[Revenue] )
      RETURN DIVIDE ( Cost, Rev )
    formatString: "0.0%"
  documentation:
    description: "Personnel cost divided by revenue."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_hr[Personnel Cost], fact_finance[Revenue].
      QA: Revenue > 0; cost completeness.
  dependencies:
    columns:
      - "fact_hr[Personnel Cost]"
      - "fact_finance[Revenue]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Revenue per FTE Amount"
  is_kpi_measure: true
  kpi_id_ref: "hr.revenue_per_fte.amount"
  semantic_model: "People_SemanticModel"
  display_folder: "02_Productivity"
  category: "KPI"
  expression:
    dax: |
      VAR Rev = SUM ( fact_sales[Net Sales Amount] )
      VAR FTE = SUM ( fact_hr[FTE] )
      RETURN DIVIDE ( Rev, FTE )
    formatString: "EUR #,0.00"
  documentation:
    description: "Revenue divided by FTE."
    notes: |
      Grain: month. Unit: EUR per FTE.
      Lineage: fact_sales[Net Sales Amount], fact_hr[FTE].
      QA: FTE > 0; currency alignment.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_hr[FTE]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Digital Adoption %"
  is_kpi_measure: true
  kpi_id_ref: "people.digital_adoption.pct"
  semantic_model: "People_SemanticModel"
  display_folder: "03_Digital"
  category: "KPI"
  expression:
    dax: |
      VAR Users = SUM ( fact_it[Digital Users] )
      VAR Heads = SUM ( fact_hr[Headcount] )
      RETURN DIVIDE ( Users, Heads )
    formatString: "0.0%"
  documentation:
    description: "Digital tool users divided by total employees."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_it[Digital Users], fact_hr[Headcount].
      QA: Headcount > 0; user identity consistent.
  dependencies:
    columns:
      - "fact_it[Digital Users]"
      - "fact_hr[Headcount]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Employee Engagement %"
  is_kpi_measure: true
  kpi_id_ref: "people.employee_engagement.pct"
  semantic_model: "People_SemanticModel"
  display_folder: "04_Engagement"
  category: "KPI"
  expression:
    dax: "DIVIDE ( SUM ( fact_survey[Engaged Responses] ), SUM ( fact_survey[Total Responses] ) )"
    formatString: "0.0%"
  documentation:
    description: "Share of engaged employees per survey."
    notes: |
      Grain: survey/month. Unit: %.
      Lineage: fact_survey[Engaged Responses], fact_survey[Total Responses].
      QA: Responses > 0; survey scoring consistent.
  dependencies:
    columns:
      - "fact_survey[Engaged Responses]"
      - "fact_survey[Total Responses]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Training Hours Amount"
  is_kpi_measure: true
  kpi_id_ref: "people.training_hours.amount"
  semantic_model: "People_SemanticModel"
  display_folder: "04_Engagement"
  category: "KPI"
  expression:
    dax: "SUM(fact_survey[Training Hours])"
    formatString: "#,0"
  documentation:
    description: "Total training hours."
    notes: |
      Grain: month. Unit: hours.
      Lineage: fact_survey[Training Hours].
      QA: Hours capture accurate; avoid double counting.
  dependencies:
    columns:
      - "fact_survey[Training Hours]"
  governance:
    owner: "People Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
