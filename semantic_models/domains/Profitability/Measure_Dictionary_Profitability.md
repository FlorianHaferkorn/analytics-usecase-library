# Measure Dictionary - Profitability

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Gross Margin %"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.pct"
  semantic_model: "Profitability_SemanticModel"
  display_folder: "01_Margin"
  category: "KPI"
  expression:
    dax: "/* TODO: implement Gross Margin % */"
    formatString: "0.0%"
  documentation:
    description: "Gross margin divided by net sales."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].
      QA: Net Sales > 0; currency alignment.
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
    dax: "/* TODO: implement Gross Margin Delta Amount */"
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
    dax: "/* TODO: implement Gross Margin Delta % */"
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
    dax: "/* TODO: implement Gross Margin % vs Plan */"
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
    dax: "/* TODO: implement EBITDA Margin */"
    formatString: "0.0%"
  documentation:
    description: "EBITDA divided by net sales."
    notes: |
      Grain: month. Unit: %.
      Lineage: fact_finance[EBITDA], fact_finance[Net Sales].
      QA: Net Sales > 0; EBITDA definition aligned to P&L.
  dependencies:
    columns:
      - "fact_finance[EBITDA]"
      - "fact_finance[Net Sales]"
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
    dax: "/* TODO: implement Promotion ROI % */"
    formatString: "0.0%"
  documentation:
    description: "Incremental GM divided by promo cost."
    notes: |
      Grain: promotion. Unit: %.
      Lineage: fact_sales[Incremental GM], fact_promo[Promo Cost].
      QA: Promo cost completeness; incremental GM logic aligned.
  dependencies:
    columns:
      - "fact_sales[Incremental GM]"
      - "fact_promo[Promo Cost]"
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
    dax: "/* TODO: implement Promo Gross Margin % */"
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
  governance:
    owner: "Profitability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
