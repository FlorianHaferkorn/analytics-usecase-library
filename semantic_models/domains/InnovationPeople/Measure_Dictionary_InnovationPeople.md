# Measure Dictionary - Innovation & People

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Innovation Rate %"
  is_kpi_measure: true
  kpi_id_ref: "people.innovation_rate.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "01_Innovation"
  category: "KPI"
  expression:
    dax: |
      VAR NewCount =
          COUNTROWS ( FILTER ( dim_product, dim_product[Lifecycle Phase] = "New" ) )
      VAR TotalCount = COUNTROWS ( dim_product )
      RETURN DIVIDE ( NewCount, TotalCount )
    formatString: "0.0%"
  documentation:
    description: "New launches as a share of total portfolio."
    notes: |
      Grain: month. Unit: %.
      Lineage: dim_product[Launch Date], dim_product[Active].
      QA: Launch date maintained; active flag consistent.
  dependencies:
    columns:
      - "dim_product[Launch Date]"
      - "dim_product[Active]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Digital Adoption %"
  is_kpi_measure: true
  kpi_id_ref: "people.digital_adoption.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "02_Digital"
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
      QA: Headcount > 0; identity consistency.
  dependencies:
    columns:
      - "fact_it[Digital Users]"
      - "fact_hr[Headcount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Contribution Margin II %"
  is_kpi_measure: true
  kpi_id_ref: "prod.contribution_margin.incl_mkt.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "03_Product"
  category: "KPI"
  expression:
    dax: |
      VAR Revenue = SUM ( fact_sales[Net Sales Amount] )
      VAR Cogs    = SUM ( fact_sales[Cost of Goods Sold Amount] )
      VAR Promo   = SUM ( fact_sales[Promo Cost Amount] )
      VAR Mkt     = SUM ( fact_marketing[Marketing Cost Amount] )
      RETURN DIVIDE ( Revenue - Cogs - Promo - Mkt, Revenue )
    formatString: "0.0%"
  documentation:
    description: "Contribution margin including marketing cost."
    notes: |
      Grain: product_month. Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], fact_sales[Promo Cost Amount],
        fact_marketing[Marketing Cost Amount].
      QA: Product mapping; marketing allocation documented; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "fact_sales[Promo Cost Amount]"
      - "fact_marketing[Marketing Cost Amount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Product Lifecycle Age (months)"
  is_kpi_measure: true
  kpi_id_ref: "prod.lifecycle.age.months"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "03_Product"
  category: "KPI"
  expression:
    dax: |
      VAR LaunchDate = MIN ( dim_product[Launch Date] )
      VAR TodayDate  = MAX ( dim_date[Date] )
      RETURN DATEDIFF ( LaunchDate, TodayDate, MONTH )
    formatString: "0"
  documentation:
    description: "Age of product in months since launch."
    notes: |
      Grain: product_month. Unit: months.
      Lineage: dim_product[Launch Date], Date table.
      QA: Launch date maintained; calendar alignment.
  dependencies:
    columns:
      - "dim_product[Launch Date]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Product Lifecycle Phase Distribution %"
  is_kpi_measure: true
  kpi_id_ref: "prod.lifecycle.phase_distribution.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "03_Product"
  category: "KPI"
  expression:
    dax: |
      VAR PhaseCount = COUNTROWS ( dim_product )
      VAR TotalCount = CALCULATE ( COUNTROWS ( dim_product ), ALL ( dim_product ) )
      RETURN DIVIDE ( PhaseCount, TotalCount )
    formatString: "0.0%"
  documentation:
    description: "Share of products by lifecycle phase."
    notes: |
      Grain: month. Unit: %.
      Lineage: dim_product[Lifecycle Phase].
      QA: Phase assignment rules consistent.
  dependencies:
    columns:
      - "dim_product[Lifecycle Phase]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Product ROI %"
  is_kpi_measure: true
  kpi_id_ref: "prod.roi.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "03_Product"
  category: "KPI"
  expression:
    dax: |
      VAR Benefit = SUM ( fact_sales[Contribution Margin Amount] )
      VAR Cost    = SUM ( fact_sales[Product Investment Amount] )
      RETURN DIVIDE ( Benefit - Cost, Cost )
    formatString: "0.0%"
  documentation:
    description: "ROI per product."
    notes: |
      Grain: product. Unit: %.
      Lineage: product revenue and cost allocations.
      QA: Allocation rules documented; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin per FTE Amount"
  is_kpi_measure: true
  kpi_id_ref: "hr.gm_per_fte.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Gross Margin Amount], [Average FTE] )"
    formatString: "EUR #,0.00"
  documentation:
    description: "Gross margin per FTE."
    notes: |
      Grain: month. Unit: EUR per FTE.
      Lineage: fact_financials[GrossMarginAmount], fact_hr_headcount[FTEFactor].
      QA: FTE > 0; currency alignment.
  dependencies:
    measures:
      - "[Gross Margin Amount]"
      - "[Average FTE]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Personnel Cost Ratio %"
  is_kpi_measure: true
  kpi_id_ref: "hr.personnel_cost_ratio.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Personnel Cost Amount], [Revenue Amount] )"
    formatString: "0.0%"
  documentation:
    description: "Personnel cost / revenue."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_hr_cost[PersonnelCost], fact_financials[RevenueAmount].
      QA: Revenue > 0; cost completeness.
  dependencies:
    measures:
      - "[Personnel Cost Amount]"
      - "[Revenue Amount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "New Product Share %"
  is_kpi_measure: true
  kpi_id_ref: "prod.lifecycle.new_share.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "01_Innovation"
  category: "KPI"
  expression:
    dax: |
      VAR NewRev   = SUM ( fact_sales[New Product Revenue] )
      VAR TotalRev = SUM ( fact_sales[Net Sales Amount] )
      RETURN DIVIDE ( NewRev, TotalRev )
    formatString: "0.0%"
  documentation:
    description: "Revenue from recently launched products divided by total revenue."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_sales[New Product Revenue], fact_sales[Net Sales Amount].
      QA: Launch window defined; revenue > 0; correct tagging of new products.
  dependencies:
    columns:
      - "fact_sales[New Product Revenue]"
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Contribution Margin I %"
  is_kpi_measure: true
  kpi_id_ref: "prod.contribution_margin.excl_mkt.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "03_Product"
  category: "KPI"
  expression:
    dax: |
      VAR Revenue = SUM ( fact_sales[Net Sales Amount] )
      VAR Cogs    = SUM ( fact_sales[Cost of Goods Sold Amount] )
      VAR Promo   = SUM ( fact_sales[Promo Cost Amount] )
      RETURN DIVIDE ( Revenue - Cogs - Promo, Revenue )
    formatString: "0.0%"
  documentation:
    description: "Contribution margin excluding marketing cost."
    notes: |
      Grain: product_month. Unit: %.
      QA: Promo cost mapping aligned; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "fact_sales[Promo Cost Amount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Revenue per FTE"
  is_kpi_measure: true
  kpi_id_ref: "hr.revenue_per_fte.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Revenue Amount], [Average FTE] )"
  formatString: "EUR #,0"
  documentation:
    description: "Total revenue divided by average FTE."
    notes: |
      Grain: month. Unit: EUR per FTE.
      QA: FTE > 0; revenue reconciles to finance totals.
  dependencies:
    measures:
      - "[Revenue Amount]"
      - "[Average FTE]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Attrition Risk %"
  is_kpi_measure: true
  kpi_id_ref: "people.attrition_risk.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "AVERAGE ( fact_hr[Attrition Risk %] )"
    formatString: "0.0%"
  documentation:
    description: "Average attrition risk for the selected population."
    notes: |
      Grain: month. Unit: %.
      QA: Bounded between 0% and 100%.
  dependencies:
    columns:
      - "fact_hr[Attrition Risk %]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Turnover Rate %"
  is_kpi_measure: true
  kpi_id_ref: "hr.turnover.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Exits Count], [Average Headcount] )"
    formatString: "0.0%"
  documentation:
    description: "Employee exits divided by average headcount."
    notes: |
      Grain: month. Unit: %.
      QA: Headcount > 0; exits non-negative.
  dependencies:
    measures:
      - "[Exits Count]"
      - "[Average Headcount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Absenteeism %"
  is_kpi_measure: true
  kpi_id_ref: "hr.absenteeism.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Absent Hours], [Scheduled Hours] )"
    formatString: "0.0%"
  documentation:
    description: "Absent hours divided by scheduled hours."
    notes: |
      Grain: month. Unit: %.
      QA: Scheduled hours > 0; absenteeism bounded 0-100%.
  dependencies:
    measures:
      - "[Absent Hours]"
      - "[Scheduled Hours]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Engaged Employees"
  is_kpi_measure: true
  kpi_id_ref: "people.engaged_employees.count"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_hrsurvey[Engaged Employees] )"
    formatString: "#,0"
  documentation:
    description: "Count of engaged employees from surveys."
    notes: |
      Grain: survey_wave. Unit: count.
      QA: Engagement classification consistent.
  dependencies:
    columns:
      - "fact_hrsurvey[Engaged Employees]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Survey Respondents"
  is_kpi_measure: true
  kpi_id_ref: "people.survey_respondents.count"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_hrsurvey[Total Respondents] )"
    formatString: "#,0"
  documentation:
    description: "Number of survey respondents."
    notes: |
      Grain: survey_wave. Unit: count.
      QA: Respondent counts reconcile to survey exports.
  dependencies:
    columns:
      - "fact_hrsurvey[Total Respondents]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Revenue Amount"
  is_kpi_measure: true
  kpi_id_ref: "hr.revenue.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_financials[RevenueAmount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Revenue amount for the selected period."
    notes: |
      Grain: month. Unit: EUR.
      QA: Reconciles to Finance totals.
  dependencies:
    columns:
      - "fact_financials[RevenueAmount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin Amount"
  is_kpi_measure: true
  kpi_id_ref: "hr.gm.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_financials[GrossMarginAmount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Gross margin amount for the selected period."
    notes: |
      Grain: month. Unit: EUR.
      QA: Reconciles to Finance gross margin.
  dependencies:
    columns:
      - "fact_financials[GrossMarginAmount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Personnel Cost Amount"
  is_kpi_measure: true
  kpi_id_ref: "hr.personnel_cost.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_hr_cost[PersonnelCost] )"
    formatString: "EUR #,0"
  documentation:
    description: "Personnel cost for the selected period."
    notes: |
      Grain: month. Unit: EUR.
      QA: Reconciles to payroll and HR cost reports.
  dependencies:
    columns:
      - "fact_hr_cost[PersonnelCost]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Average FTE"
  is_kpi_measure: true
  kpi_id_ref: "hr.fte.avg"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "AVERAGE ( fact_hr_headcount[FTEFactor] )"
    formatString: "#,0.0"
  documentation:
    description: "Average FTE over the selected period."
    notes: |
      Grain: month. Unit: FTE.
      QA: FTE > 0 for reported slices.
  dependencies:
    columns:
      - "fact_hr_headcount[FTEFactor]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Average Headcount"
  is_kpi_measure: true
  kpi_id_ref: "hr.headcount.avg"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "AVERAGE ( fact_hr_headcount[Headcount] )"
    formatString: "#,0"
  documentation:
    description: "Average headcount over the selected period."
    notes: |
      Grain: month. Unit: heads.
      QA: Headcount > 0 for reported slices.
  dependencies:
    columns:
      - "fact_hr_headcount[Headcount]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Absent Hours"
  is_kpi_measure: true
  kpi_id_ref: "hr.absent_hours.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_hr_time[AbsentHours] )"
    formatString: "#,0.0"
  documentation:
    description: "Total absent hours."
    notes: |
      Grain: month. Unit: hours.
      QA: Absent hours non-negative.
  dependencies:
    columns:
      - "fact_hr_time[AbsentHours]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Scheduled Hours"
  is_kpi_measure: true
  kpi_id_ref: "hr.scheduled_hours.amount"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_hr_time[ScheduledHours] )"
    formatString: "#,0.0"
  documentation:
    description: "Total scheduled working hours."
    notes: |
      Grain: month. Unit: hours.
      QA: Scheduled hours > 0 for reported slices.
  dependencies:
    columns:
      - "fact_hr_time[ScheduledHours]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Exits Count"
  is_kpi_measure: true
  kpi_id_ref: "hr.exits.count"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: "SUM ( fact_hr_headcount[Exits] )"
    formatString: "#,0"
  documentation:
    description: "Number of employee exits."
    notes: |
      Grain: month. Unit: count.
      QA: Exits count non-negative.
  dependencies:
    columns:
      - "fact_hr_headcount[Exits]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
