# Measure Dictionary - Innovation & People

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "New Product Share %"
  is_kpi_measure: true
  kpi_id_ref: "people.new_product_share"
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

- measure_name: "Product Contribution Margin %"
  is_kpi_measure: true
  kpi_id_ref: "prod.contribution_margin.pct"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "03_Product"
  category: "KPI"
  expression:
    dax: |
      VAR Revenue = SUM ( fact_sales[Net Sales Amount] )
      VAR Cogs    = SUM ( fact_sales[Cost of Goods Sold Amount] )
      RETURN DIVIDE ( Revenue - Cogs, Revenue )
    formatString: "0.0%"
  documentation:
    description: "Contribution margin by product."
    notes: |
      Grain: product_month. Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].
      QA: Product mapping; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
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
  kpi_id_ref: "people.gross_margin_per_fte"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: |
      VAR GM  = SUM ( fact_sales[Net Sales Amount] ) - SUM ( fact_sales[Cost of Goods Sold Amount] )
      VAR FTE = SUM ( fact_hr[FTE] )
      RETURN DIVIDE ( GM, FTE )
    formatString: "EUR #,0.00"
  documentation:
    description: "Gross margin per FTE."
    notes: |
      Grain: month. Unit: EUR per FTE.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], fact_hr[FTE].
      QA: FTE > 0; currency alignment.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "fact_hr[FTE]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Personnel Cost Ratio %"
  is_kpi_measure: true
  kpi_id_ref: "people.personnel_cost_ratio"
  semantic_model: "InnovationPeople_SemanticModel"
  display_folder: "04_People"
  category: "KPI"
  expression:
    dax: |
      VAR Cost  = SUM ( fact_hr[Personnel Cost] )
      VAR Rev   = SUM ( fact_finance[Revenue] )
      RETURN DIVIDE ( Cost, Rev )
    formatString: "0.0%"
  documentation:
    description: "Personnel cost / revenue."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_hr[Personnel Cost], fact_finance[Revenue].
      QA: Revenue > 0; cost completeness.
  dependencies:
    columns:
      - "fact_hr[Personnel Cost]"
      - "fact_finance[Revenue]"
  governance:
    owner: "Innovation Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
