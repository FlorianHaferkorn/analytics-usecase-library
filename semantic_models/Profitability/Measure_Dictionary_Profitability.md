# Measure Dictionary - Profitability

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Gross Margin %
  is_kpi_measure: true
  kpi_id_ref: profit.gross_margin
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Net Sales Amount]-[COGS Amount],[Net Sales Amount])
    formatString: 0.0 %
  documentation:
    description: 'Purpose: share of gross margin relative to net sales. Definition: ([Net Sales Amount]-[COGS Amount])/[Net
      Sales Amount]. Grain & Scope: aggregated from invoice_line by Date/Org/Product. Unit/Format: 0.0 %. Lineage: fact_sales
      Net Sales/COGS. QA: within [-100%;100%]; reconciles to P&L GM within +/-0.5 pp.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
- measure_name: EBITDA Margin %
  is_kpi_measure: true
  kpi_id_ref: profit.ebitda_margin
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([EBITDA Amount],[Net Sales Amount])
    formatString: 0.0 %
  documentation:
    description: 'Purpose: EBITDA share of revenue. Definition: [EBITDA Amount]/[Net Sales Amount]. Grain & Scope: monthly
      close, company level. Unit/Format: 0.0 %. Lineage: finance EBITDA, sales revenue. QA: reconciles within +/-0.2 pp.'
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - EBITDA Amount
    - Net Sales Amount
    columns:
    - fact_finance.EBITDA Amount
    - fact_sales.Net Sales Amount
- measure_name: COGS Amount
  is_kpi_measure: true
  kpi_id_ref: cost.cogs.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: SUM(fact_sales[COGS Amount])
    formatString: 'EUR #,0.00'
  documentation:
    description: 'Purpose: direct product cost for sold units. Definition: sum of product cost components for sold units.
      Grain & Scope: invoice_line aggregated. Unit/Format: EUR #,0.00. Lineage: fact_sales[COGS Amount]. QA: reconcile with
      P&L COGS within +/-0.5%.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Invoice Cost Amount
    columns:
    - fact_sales.COGS Amount
- measure_name: Gross Margin Amount
  is_kpi_measure: true
  kpi_id_ref: margin.gm.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: '[Net Sales Amount] - [COGS Amount]'
    formatString: 'EUR #,0.00'
  documentation:
    description: 'Purpose: currency value of gross margin. Definition: [Net Sales]-[COGS]. Grain & Scope: period-level. Unit/Format:
      EUR #,0.00. Lineage: revenue and COGS measures. QA: reconciles to P&L GM within tolerance.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
- measure_name: '? Gross Margin Amount'
  is_kpi_measure: true
  kpi_id_ref: margin.gm.delta_amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: '[Gross Margin Amount] - [Baseline GM Amount]'
    formatString: 'EUR #,0.00'
  documentation:
    description: Absolute gross margin variance to the selected baseline (Plan or Last Year).
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Gross Margin Amount
    - Plan Gross Margin Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_plan_sales.Plan Gross Margin Amount
- measure_name: Gross Margin % Delta%
  is_kpi_measure: true
  kpi_id_ref: margin.gm.delta_pct
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Gross Margin %] - CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date])), CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date])))
    formatString: 0.0 %
  documentation:
    description: Relative change vs LY of Gross Margin %.
    notes: ''
  governance:
    owner: BI Engineering
    status: draft
    version: v1.0
    last_review: 06.11.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Gross Margin %
- measure_name: Promo Cost Amount
  is_kpi_measure: true
  kpi_id_ref: sales.promo.cost.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: SUM(fact_sales[Promo Cost Amount])
    formatString: 'EUR #,0.00'
  documentation:
    description: Aggregated promotion spend captured in fact_sales[Promo Cost Amount].
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 03_Price_Promo
  dependencies:
    columns:
    - fact_sales.Promo Cost Amount
- measure_name: Promo COGS Amount
  is_kpi_measure: true
  kpi_id_ref: cost.cogs.promo.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: CALCULATE([COGS Amount], fact_sales[Promo Flag] = TRUE())
    formatString: 'EUR #,0.00'
  documentation:
    description: 'Purpose: cost of goods during promotion. Definition: CALCULATE([COGS Amount], Promo Flag). Grain & Scope:
      promo/product. Unit/Format: EUR #,0.00. Lineage: COGS with promo filter. QA: reconcile to campaign accounting.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - COGS Amount
    columns:
    - fact_sales.COGS Amount
    - fact_sales.Promo Flag
- measure_name: Incremental Sales Amount
  is_kpi_measure: true
  kpi_id_ref: sales.promo.incremental.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: '[Promo Sales Amount] - [Baseline Sales Amount]'
    formatString: 'EUR #,0.00'
  documentation:
    description: 'Purpose: incremental revenue vs baseline during promo. Definition: [Promo Sales]-[Baseline]. Grain & Scope:
      promo/product. Unit/Format: EUR #,0.00. Lineage: promo and baseline revenue measures. QA: exclude overlaps; align to
      calendar.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 01_Sales
  dependencies:
    measures:
    - Promo Sales Amount
    - Baseline Sales Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.Promo Flag
- measure_name: Incremental GM Amount
  is_kpi_measure: true
  kpi_id_ref: margin.promo.incremental.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: ([Promo Sales Amount]-[Promo COGS Amount]) - ([Baseline Sales Amount]-CALCULATE([COGS Amount], NOT fact_sales[Promo
      Flag]))
    formatString: 'EUR #,0.00'
  documentation:
    description: 'Purpose: incremental gross margin due to promo. Definition: (Promo NS-Promo COGS)-(Baseline NS-Baseline
      COGS). Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: promo/baseline revenue and costs. QA: allocation
      consistent.'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Promo Sales Amount
    - Baseline Sales Amount
    - COGS Amount
    - Promo COGS Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_sales.Promo Flag
- measure_name: Promo ROI %
  is_kpi_measure: true
  kpi_id_ref: sales.promo.roi.pct
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Incremental GM Amount] - [Promo Cost Amount],[Promo Cost Amount])
    formatString: 0.0 %
  documentation:
    description: Return on promotion investments using incremental gross margin uplift.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 03_Price_Promo
  dependencies:
    measures:
    - Incremental GM Amount
    - Promo Cost Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_sales.Promo Cost Amount
- measure_name: GM % During Promo
  is_kpi_measure: true
  kpi_id_ref: margin.promo.gm.pct
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: VAR _ns = [Promo Sales Amount] RETURN IF(_ns=0, BLANK(), DIVIDE([Promo Sales Amount]-[Promo COGS Amount], _ns))
    formatString: 0.0 %
  documentation:
    description: 'Purpose: margin rate during promotions. Definition: ([Promo Sales]-[Promo COGS])/[Promo Sales]. Grain &
      Scope: promo/product. Unit/Format: 0.0 %. Lineage: promo revenue and cost. QA: within [-100%;100%].'
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v2.0
    last_review: 12.10.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Promo Sales Amount
    - Promo COGS Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_sales.Promo Flag
- measure_name: EBITDA Amount
  is_kpi_measure: true
  kpi_id_ref: fin.ebitda.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Earnings before interest, taxes, depreciation, and amortization
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Plan Gross Margin Amount
  is_kpi_measure: true
  kpi_id_ref: margin.gm.plan.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Planned gross margin value for the period
    notes: ''
  governance:
    owner: Commercial BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Customer Margin Amount
  is_kpi_measure: true
  kpi_id_ref: margin.customer.amount
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: '[Net Sales Amount] - [COGS Amount]'
    formatString: '#,0.00'
  documentation:
    description: Gross margin amount per customer or customer segment (Net Sales - COGS).
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.0
    last_review: 19.11.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Net Sales Amount
    - COGS Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - dim_customer.CustomerID
- measure_name: Customer Margin %
  is_kpi_measure: true
  kpi_id_ref: margin.customer.pct
  semantic_model: Profitability_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Customer Margin Amount],[Net Sales Amount])
    formatString: 0.0 %
  documentation:
    description: Gross margin percentage per customer or segment.
    notes: ''
  governance:
    owner: BI Engineering
    status: active
    version: v1.0
    last_review: 19.11.2025
  display_folder: 02_Margin
  dependencies:
    measures:
    - Customer Margin Amount
    - Net Sales Amount
    columns:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - dim_customer.CustomerID
```
