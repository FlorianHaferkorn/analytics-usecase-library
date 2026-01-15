# Measure Dictionary - Profitability

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Gross Margin %"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: |
      VAR NetSales = SUM ( fact_sales[Net Sales Amount] )
      VAR Cogs     = SUM ( fact_sales[Cost of Goods Sold Amount] )
      RETURN DIVIDE ( NetSales - Cogs, NetSales )
    formatString: "0.0%"
  documentation:
    description: "Gross margin divided by net sales."
    notes: |
      Grain: month (aggregated from invoice_line). Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].
      QA: Net Sales > 0; currency alignment; exclusions (returns) consistent.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin %"
  is_kpi_measure: true
  kpi_id_ref: "profit.gross_margin"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: |
      VAR NetSales = SUM ( fact_sales[Net Sales Amount] )
      VAR Cogs     = SUM ( fact_sales[Cost of Goods Sold Amount] )
      RETURN DIVIDE ( NetSales - Cogs, NetSales )
    formatString: "0.0%"
  documentation:
    description: "Strategic gross margin KPI; same DAX as operational GM %."
    notes: |
      Grain: month (aggregated from invoice_line). Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].
      QA: Net Sales > 0; currency alignment; exclusions (returns) consistent.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin Amount"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: "[Net Sales Amount] - [Cost of Goods Sold Amount]"
    formatString: "EUR #,0"
  documentation:
    description: "Profit pool: net sales minus COGS."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].
      QA: Currency alignment; COGS completeness.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin Delta Amount"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.delta_amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: |
      VAR GM = [Gross Margin Amount]
      VAR GM_Base =
          COALESCE ( [Plan Gross Margin Amount], [Gross Margin Amount LY] )
      RETURN GM - GM_Base
    formatString: "EUR #,0"
  documentation:
    description: "Absolute change in gross margin vs baseline."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: gross margin vs baseline GM.
      QA: Baseline definition documented.
  dependencies:
    measures:
      - "[Gross Margin Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin Delta %"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.delta_pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: |
      VAR GM_Pct = [Gross Margin %]
      VAR GM_Pct_Base =
          COALESCE ( [Plan Gross Margin %], [Gross Margin % LY] )
      RETURN DIVIDE ( GM_Pct - GM_Pct_Base, GM_Pct_Base )
    formatString: "0.0%"
  documentation:
    description: "Relative change in gross margin rate vs baseline."
    notes: |
      Grain: month. Unit: %.
      Lineage: Gross Margin %, baseline GM %.
      QA: Baseline defined; DIVIDE guard.
  dependencies:
    measures:
      - "[Gross Margin %]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin % vs Plan"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.vs_plan.pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: |
      VAR GM_Pct = [Gross Margin %]
      VAR GM_Pct_Plan = [Plan Gross Margin %]
      RETURN DIVIDE ( GM_Pct - GM_Pct_Plan, GM_Pct_Plan )
    formatString: "0.0 percentage-point"
  documentation:
    description: "Relative variance of GM% versus plan."
    notes: |
      Grain: month. Unit: percentage-point.
      Lineage: GM %, Plan GM %.
      QA: Plan sales/COGS complete; DIVIDE guard.
  dependencies:
    measures:
      - "[Gross Margin %]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "EBITDA Margin"
  is_kpi_measure: true
  kpi_id_ref: "profit.ebitda_margin"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "02_Profit"
  category: "KPI"
  expression:
    dax: |
      DIVIDE ( [EBITDA Amount], [Net Sales Amount] )
    formatString: "0.0%"
  documentation:
    description: "EBITDA divided by net sales."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_finance[EBITDA Amount], fact_sales[Net Sales Amount].
      QA: Net Sales > 0; EBITDA definition aligned to P&L.
  dependencies:
    measures:
      - "[EBITDA Amount]"
      - "[Net Sales Amount]"
    columns:
      - "fact_finance[EBITDA Amount]"
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "COGS Amount"
  is_kpi_measure: true
  kpi_id_ref: "cost.cogs.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "03_Cost"
  category: "KPI"
  expression:
    dax: "SUM(fact_sales[Cost of Goods Sold Amount])"
    formatString: "EUR #,0"
  documentation:
    description: "Total cost of goods sold."
    notes: |
      Grain: invoice_line / month. Unit: EUR.
      Lineage: fact_sales[Cost of Goods Sold Amount].
      QA: Currency alignment; completeness of COGS.
  dependencies:
    columns:
      - "fact_sales[Cost of Goods Sold Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Promotion ROI %"
  is_kpi_measure: true
  kpi_id_ref: "sales.promo.roi.pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "04_Promo"
  category: "KPI"
  expression:
    dax: |
      VAR IncrementalGM = [Incremental GM Amount]
      VAR PromoCost     = [Promo Cost Amount]
      RETURN DIVIDE ( IncrementalGM, PromoCost )
    formatString: "0.0%"
  documentation:
    description: "Incremental GM divided by promo cost."
    notes: |
      Grain: promotion. Unit: %.
      Lineage: Incremental GM Amount, Promo Cost Amount.
      QA: Promo cost completeness; incremental GM logic aligned.
  dependencies:
    measures:
      - "[Incremental GM Amount]"
      - "[Promo Cost Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

# Supporting / Diagnostic Measures

- measure_name: "Net Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "00_Sales"
  category: "Supporting"
  expression:
    dax: "SUM ( fact_sales[Net Sales Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Total net sales after discounts."
    notes: |
      Grain: invoice_line / month. Unit: EUR.
      QA: Align with finance net revenue; currency alignment.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin Amount LY"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "Supporting"
  expression:
    dax: |
      CALCULATE ( [Gross Margin Amount], DATEADD ( dim_date[Date], -1, YEAR ) )
    formatString: "EUR #,0"
  documentation:
    description: "Last year gross margin for variance bridges."
    notes: |
      Grain: month. Unit: EUR.
      QA: Calendar alignment; identical filters except date shift.
  dependencies:
    measures:
      - "[Gross Margin Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Gross Margin % LY"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "Supporting"
  expression:
    dax: |
      CALCULATE ( [Gross Margin %], DATEADD ( dim_date[Date], -1, YEAR ) )
    formatString: "0.0%"
  documentation:
    description: "Last year gross margin rate for variance analysis."
    notes: |
      Grain: month. Unit: %.
      QA: Calendar alignment; filters identical except date shift.
  dependencies:
    measures:
      - "[Gross Margin %]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Plan Gross Margin Amount"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.plan.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: "SUM ( fact_plan_sales[Plan Gross Margin Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Planned gross margin for variance vs plan."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: plan fact (e.g., fact_plan_sales[Plan Gross Margin Amount]).
      QA: Plan versioning and currency alignment required.
  dependencies:
    columns:
      - "fact_plan_sales[Plan Gross Margin Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "EBITDA Amount"
  is_kpi_measure: true
  kpi_id_ref: "fin.ebitda.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "02_Profit"
  category: "KPI"
  expression:
    dax: "SUM ( fact_finance[EBITDA Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "EBITDA for the reporting period."
    notes: |
      Grain: month. Unit: EUR.
      Lineage: fact_finance[EBITDA Amount].
      QA: Reconcile to P&L; currency alignment.
  dependencies:
    columns:
      - "fact_finance[EBITDA Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Customer Margin Amount"
  is_kpi_measure: true
  kpi_id_ref: "margin.customer.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: "[Net Sales Amount] - [COGS Amount]"
    formatString: "EUR #,0"
  documentation:
    description: "Gross margin amount by customer."
    notes: |
      Grain: customer / period. Unit: EUR.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].
      QA: Customer mapping consistent with sales and COGS.
  dependencies:
    measures:
      - "[Net Sales Amount]"
      - "[COGS Amount]"
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "dim_customer[CustomerID]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Customer Margin %"
  is_kpi_measure: true
  kpi_id_ref: "margin.customer.pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: "DIVIDE ( [Customer Margin Amount], [Net Sales Amount] )"
    formatString: "0.0%"
  documentation:
    description: "Gross margin rate by customer."
    notes: |
      Grain: customer / period. Unit: %.
      QA: Net Sales > 0; customer filters aligned.
  dependencies:
    measures:
      - "[Customer Margin Amount]"
      - "[Net Sales Amount]"
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "dim_customer[CustomerID]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Plan Gross Margin %"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "Supporting"
  expression:
    dax: |
      DIVIDE (
        SUM ( fact_plan_sales[Plan Gross Margin Amount] ),
        SUM ( fact_plan_sales[Plan Net Sales Amount] )
      )
    formatString: "0.0%"
  documentation:
    description: "Planned gross margin rate for variance vs plan."
    notes: |
      Grain: month. Unit: %.
      QA: Plan net sales > 0; versioning documented.
  dependencies:
    columns:
      - "fact_plan_sales[Plan Gross Margin Amount]"
      - "fact_plan_sales[Plan Net Sales Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Promo Cost Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "04_Promo"
  category: "Supporting"
  expression:
    dax: "SUM ( fact_sales[Promo Cost Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Total promo spend for a promotion."
    notes: |
      Grain: promotion / product. Unit: EUR.
      QA: Align with marketing accruals; promo flag logic consistent.
  dependencies:
    columns:
      - "fact_sales[Promo Cost Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Promo COGS Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "04_Promo"
  category: "Supporting"
  expression:
    dax: |
      CALCULATE ( SUM ( fact_sales[Cost of Goods Sold Amount] ), fact_sales[Promo Flag] = TRUE () )
    formatString: "EUR #,0"
  documentation:
    description: "COGS limited to promo periods/products."
    notes: |
      Grain: promotion / product. Unit: EUR.
      QA: Promo flag accurate; currency alignment.
  dependencies:
    columns:
      - "fact_sales[Cost of Goods Sold Amount]"
      - "fact_sales[Promo Flag]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Incremental Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "04_Promo"
  category: "Supporting"
  expression:
    dax: |
      VAR PromoSales = CALCULATE ( SUM ( fact_sales[Net Sales Amount] ), fact_sales[Promo Flag] = TRUE () )
      VAR Baseline   = CALCULATE ( SUM ( fact_sales[Baseline Non-Promo Sales Amount] ), fact_sales[Promo Flag] = TRUE () )
      RETURN PromoSales - Baseline
    formatString: "EUR #,0"
  documentation:
    description: "Additional sales due to promotion vs baseline."
    notes: |
      Grain: promotion / product. Unit: EUR.
      QA: Baseline logic documented; avoid double counting overlaps.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Baseline Non-Promo Sales Amount]"
      - "fact_sales[Promo Flag]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Incremental GM Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Profitability_SemanticModel"
  display_folder: "04_Promo"
  category: "Supporting"
  expression:
    dax: |
      VAR PromoGM =
          CALCULATE ( [Gross Margin Amount], fact_sales[Promo Flag] = TRUE () )
      VAR BaselineGM =
          CALCULATE ( [Gross Margin Amount], fact_sales[Promo Flag] = FALSE () )
      RETURN PromoGM - BaselineGM
    formatString: "EUR #,0"
  documentation:
    description: "Incremental gross margin during promotion vs non-promo baseline."
    notes: |
      Grain: promotion / product. Unit: EUR.
      QA: Baseline window defined; check for mix shifts.
  dependencies:
    measures:
      - "[Gross Margin Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Promo Gross Margin %"
  is_kpi_measure: true
  kpi_id_ref: "margin.promo.gm.pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "04_Promo"
  category: "KPI"
  expression:
    dax: |
      VAR PromoSales =
          CALCULATE ( SUM ( fact_sales[Net Sales Amount] ), fact_sales[Promo Flag] = TRUE () )
      VAR PromoCogs =
          CALCULATE ( SUM ( fact_sales[Cost of Goods Sold Amount] ), fact_sales[Promo Flag] = TRUE () )
      RETURN DIVIDE ( PromoSales - PromoCogs, PromoSales )
    formatString: "0.0%"
  documentation:
    description: "GM rate during promotions."
    notes: |
      Grain: promotion. Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], promo flag.
      QA: Promo filter context; DIVIDE guard.
  dependencies:
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[Cost of Goods Sold Amount]"
      - "fact_sales[Promo Flag]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
- measure_name: "Cost Base Volume Amount"
  is_kpi_measure: true
  kpi_id_ref: "cost.base_volume.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "02_Cost"
  category: "KPI"
  expression:
    dax: "SUM ( fact_cost[Base Volume Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Baseline cost volume amount for variance analysis."
    notes: |
      Grain: cost_center_month. Unit: EUR.
      Lineage: fact_cost[Base Volume Amount].
      QA: Baseline aligned with planning cycle.
  dependencies:
    columns:
      - "fact_cost[Base Volume Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"

- measure_name: "Opex Base Amount"
  is_kpi_measure: true
  kpi_id_ref: "cost.opex.base.amount"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "02_Cost"
  category: "KPI"
  expression:
    dax: "SUM ( fact_opex[Opex Base Amount] )"
    formatString: "EUR #,0"
  documentation:
    description: "Baseline operating expense amount."
    notes: |
      Grain: cost_center_month. Unit: EUR.
      Lineage: fact_opex[Opex Base Amount].
      QA: Baseline aligned with plan version.
  dependencies:
    columns:
      - "fact_opex[Opex Base Amount]"
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v0.1"
    last_review: "TBD"
```
