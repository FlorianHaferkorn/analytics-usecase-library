# Measure Dictionary - Profitability

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Gross Margin %
  is_kpi_measure: true
  kpi_id_ref: margin.gm.pct
  semantic_model: Profitability_SemanticModel
  display_folder: 01_Margin
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Gross margin divided by net sales.
    notes: 'Grain: month (aggregated from invoice_line). Unit: %.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].

      QA: Net Sales > 0; currency alignment; exclusions (returns) consistent.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Gross Margin Amount
  is_kpi_measure: true
  kpi_id_ref: margin.gm.amount
  semantic_model: Profitability_SemanticModel
  display_folder: 01_Margin
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: 'Profit pool: net sales minus COGS.'
    notes: 'Grain: month. Unit: EUR.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].

      QA: Currency alignment; COGS completeness.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Gross Margin % vs Plan
  is_kpi_measure: true
  kpi_id_ref: margin.gm.vs_plan.pct
  semantic_model: Profitability_SemanticModel
  display_folder: 01_Margin
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Relative variance of GM% versus plan.
    notes: 'Grain: month. Unit: percentage-point.

      Lineage: GM %, Plan GM %.

      QA: Plan sales/COGS complete; DIVIDE guard.

      '
  dependencies:
    measures:
    - '[Gross Margin %]'
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Promotion ROI %
  is_kpi_measure: true
  kpi_id_ref: sales.promo.roi.pct
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Incremental GM divided by promo cost.
    notes: 'Grain: promotion. Unit: %.

      Lineage: Incremental GM Amount, Promo Cost Amount.

      QA: Promo cost completeness; incremental GM logic aligned.

      '
  dependencies:
    measures:
    - '[Incremental GM Amount]'
    - '[Promo Cost Amount]'
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Promo ROI %
  is_kpi_measure: true
  kpi_id_ref: sales.promo.roi.pct
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Alias for Promotion ROI % (TMDL display name).
    notes: Same as Promotion ROI %.
  dependencies:
    measures: []
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 00_Sales
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total net sales after discounts.
    notes: 'Grain: invoice_line / month. Unit: EUR.

      QA: Align with finance net revenue; currency alignment.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Gross Margin Amount LY
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 01_Margin
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Last year gross margin for variance bridges.
    notes: 'Grain: month. Unit: EUR.

      QA: Calendar alignment; identical filters except date shift.

      '
  dependencies:
    measures:
    - '[Gross Margin Amount]'
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Gross Margin % LY
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 01_Margin
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Last year gross margin rate for variance analysis.
    notes: 'Grain: month. Unit: %.

      QA: Calendar alignment; filters identical except date shift.

      '
  dependencies:
    measures:
    - '[Gross Margin %]'
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Plan Gross Margin %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 01_Margin
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Planned gross margin rate for variance vs plan.
    notes: 'Grain: month. Unit: %.

      QA: Plan net sales > 0; versioning documented.

      '
  dependencies:
    columns:
    - fact_plan_sales[Plan Gross Margin Amount]
    - fact_plan_sales[Plan Net Sales Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Promo Cost Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total promo spend for a promotion.
    notes: 'Grain: promotion / product. Unit: EUR.

      QA: Align with marketing accruals; promo flag logic consistent.

      '
  dependencies:
    columns:
    - fact_sales[Promo Cost Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Promo COGS Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: COGS limited to promo periods/products.
    notes: 'Grain: promotion / product. Unit: EUR.

      QA: Promo flag accurate; currency alignment.

      '
  dependencies:
    columns:
    - fact_sales[Cost of Goods Sold Amount]
    - fact_sales[Promo Flag]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Incremental Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Additional sales due to promotion vs baseline.
    notes: 'Grain: promotion / product. Unit: EUR.

      QA: Baseline logic documented; avoid double counting overlaps.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Baseline Non-Promo Sales Amount]
    - fact_sales[Promo Flag]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Incremental GM Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Incremental gross margin during promotion vs non-promo baseline.
    notes: 'Grain: promotion / product. Unit: EUR.

      QA: Baseline window defined; check for mix shifts.

      '
  dependencies:
    measures:
    - '[Gross Margin Amount]'
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Promo Gross Margin %
  is_kpi_measure: true
  kpi_id_ref: margin.promo.gm.pct
  semantic_model: Profitability_SemanticModel
  display_folder: 04_Promo
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: GM rate during promotions.
    notes: 'Grain: promotion. Unit: %.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount],
      promo flag.

      QA: Promo filter context; DIVIDE guard.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Cost of Goods Sold Amount]
    - fact_sales[Promo Flag]
  governance:
    owner: Profitability Analytics
    status: active
    version: v1.2
    last_review: TBD
- measure_name: Cost Base Volume Amount
  is_kpi_measure: true
  kpi_id_ref: cost.base_volume.amount
  semantic_model: Profitability_SemanticModel
  display_folder: 02_Cost
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Baseline cost volume amount for variance analysis.
    notes: 'Grain: cost_center_month. Unit: EUR.

      Lineage: fact_cost[Base Volume Amount].

      QA: Baseline aligned with planning cycle.

      '
  dependencies:
    columns:
    - fact_cost[Base Volume Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v0.1
    last_review: TBD
- measure_name: Opex Base Amount
  is_kpi_measure: true
  kpi_id_ref: cost.opex.base.amount
  semantic_model: Profitability_SemanticModel
  display_folder: 02_Cost
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Baseline operating expense amount.
    notes: 'Grain: cost_center_month. Unit: EUR.

      Lineage: fact_opex[Opex Base Amount].

      QA: Baseline aligned with plan version.

      '
  dependencies:
    columns:
    - fact_opex[Opex Base Amount]
  governance:
    owner: Profitability Analytics
    status: active
    version: v0.1
    last_review: TBD
```

