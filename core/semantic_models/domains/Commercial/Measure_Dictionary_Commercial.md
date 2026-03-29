# Measure Dictionary - Commercial

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Net Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: KPI
  expression:
    logical: Net Sales Amount = SUM ( fact_sales[Net Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Sum of net sales after discounts and rebates.
    notes: 'Grain: invoice_line, reported monthly. Unit: EUR.

      Lineage: fact_sales[Net Sales Amount].

      QA: Excludes VAT/returns; currency conversion handled upstream.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Net Sales % vs Plan
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.delta_pct.plan
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: KPI
  expression:
    logical: Net Sales % vs Plan = ([Net Sales Amount] - SUM ( fact_sales[Plan Sales Amount] )) / (SUM ( fact_sales[Plan Sales Amount] ))
    aggregation_method: ratio
  documentation:
    description: Variance of net sales versus plan as a percentage.
    notes: 'Grain: month. Unit: %.

      Lineage: [Net Sales Amount], fact_sales[Plan Sales Amount].

      QA: Plan Sales Amount must be populated for the same grain; DIVIDE protects divide-by-zero.

      '
  dependencies:
    measures:
    - '[Net Sales Amount]'
    - '[Plan Sales Amount]'
    columns:
    - fact_sales[Plan Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Net Sales % vs LY
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: KPI
  expression:
    logical: Net Sales % vs LY = ([Net Sales Amount] - [Last Year Sales Amount]) / [Last Year Sales Amount]
    aggregation_method: ratio
  documentation:
    description: Variance of net sales versus last year as a percentage.
    notes: 'Grain: month. Unit: %.

      Lineage: [Net Sales Amount], fact_sales[Last Year Sales Amount].

      QA: Requires aligned last-year calendar mapping; DIVIDE protects divide-by-zero.

      '
  dependencies:
    measures:
    - '[Net Sales Amount]'
    - '[Last Year Sales Amount]'
    columns:
    - fact_sales[Last Year Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Gross Margin Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: KPI
  expression:
    logical: Gross Margin Amount = [Net Sales Amount] - [Cost of Goods Sold Amount]
    aggregation_method: sum
  documentation:
    description: Profit pool calculated as net sales minus cost of goods sold.
    notes: 'Grain: invoice_line, reported monthly. Unit: EUR.

      Lineage: [Net Sales Amount], fact_sales[Cost of Goods Sold Amount].

      QA: COGS must align to sales grain; currency handled upstream.

      '
  dependencies:
    measures:
    - '[Net Sales Amount]'
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Gross Margin %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: KPI
  expression:
    logical: Gross Margin % = ([Net Sales Amount] - [Cost of Goods Sold Amount]) / ([Net Sales Amount])
    aggregation_method: ratio
  documentation:
    description: Gross margin rate as a share of net sales.
    notes: 'Grain: month. Unit: %.

      Lineage: [Gross Margin Amount], [Net Sales Amount].

      QA: DIVIDE protects divide-by-zero; ensure sales not zero for meaningful result.

      '
  dependencies:
    measures:
    - '[Gross Margin Amount]'
    - '[Net Sales Amount]'
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Gross Margin % vs Plan
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: KPI
  expression:
    logical: Gross Margin % vs Plan = (([Net Sales Amount] - [Cost of Goods Sold Amount]) / ([Net Sales Amount]) - (SUM ( fact_sales[Plan Sales Amount] ) - SUM ( fact_sales[Plan COGS Amount] )) / (SUM (
      fact_sales[Plan Sales Amount] ))) / ((SUM ( fact_sales[Plan Sales Amount] ) - SUM ( fact_sales[Plan COGS Amount] )) / (SUM ( fact_sales[Plan Sales Amount] )))
    aggregation_method: ratio
  documentation:
    description: Relative variance of gross margin rate versus plan.
    notes: 'Grain: month. Unit: percentage-point.

      Lineage: [Gross Margin Amount], [Net Sales Amount], [Plan Gross Margin Amount], [Plan Sales Amount].

      QA: Requires plan sales and plan COGS populated; DIVIDE protects divide-by-zero.

      '
  dependencies:
    measures:
    - '[Gross Margin Amount]'
    - '[Net Sales Amount]'
    - '[Plan Gross Margin Amount]'
    - '[Plan Sales Amount]'
    columns:
    - fact_sales[Plan COGS Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Price Effect Amount
  is_kpi_measure: true
  kpi_id_ref: sales.pvm.price_effect.amount
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_PVM
  category: Driver
  expression:
    logical: Price Effect Amount = ( (fact_sales[Net Sales Amount]) / (fact_sales[Quantity]) - (fact_sales[Plan Sales Amount]) / (fact_sales[Plan Quantity]) ) * fact_sales[Quantity] )
    aggregation_method: sum
  documentation:
    description: PVM driver quantifying the net sales impact from price change.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Plan Sales Amount], fact_sales[Quantity], fact_sales[Plan Quantity].

      QA: Plan quantities/prices must be available; watch for zero quantities.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Plan Sales Amount]
    - fact_sales[Quantity]
    - fact_sales[Plan Quantity]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Volume Effect Amount
  is_kpi_measure: true
  kpi_id_ref: sales.pvm.volume_effect.amount
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_PVM
  category: Driver
  expression:
    logical: Volume Effect Amount = ( fact_sales[Quantity] - fact_sales[Plan Quantity] ) * (fact_sales[Plan Sales Amount]) / (PlanQty) )
    aggregation_method: sum
  documentation:
    description: PVM driver quantifying the net sales impact from volume change.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Quantity], fact_sales[Plan Quantity], fact_sales[Plan Sales Amount].

      QA: Relies on plan quantities and plan prices at the same grain; watch for zero quantities.

      '
  dependencies:
    columns:
    - fact_sales[Quantity]
    - fact_sales[Plan Quantity]
    - fact_sales[Plan Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Mix Effect Amount
  is_kpi_measure: true
  kpi_id_ref: sales.pvm.mix_effect.amount
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_PVM
  category: Driver
  expression:
    logical: Mix Effect Amount = [Net Sales Amount] - SUM ( fact_sales[Plan Sales Amount] ) - [Price Effect Amount] - [Volume Effect Amount]
    aggregation_method: sum
  documentation:
    description: Residual PVM driver capturing mix impact after price and volume effects.
    notes: 'Grain: month. Unit: EUR.

      Lineage: [Net Sales Amount], [Price Effect Amount], [Volume Effect Amount], [Plan Sales Amount].

      QA: Uses plan sales as baseline; ensure consistent grain.

      '
  dependencies:
    measures:
    - '[Net Sales Amount]'
    - '[Price Effect Amount]'
    - '[Volume Effect Amount]'
    - '[Plan Sales Amount]'
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Price Realization %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_Pricing
  category: KPI
  expression:
    logical: Price Realization % = ([Net Price Amount]) / ([List Price Amount])
    aggregation_method: ratio
  documentation:
    description: Discount discipline metric comparing net price to list price.
    notes: 'Grain: month or promo. Unit: %.

      Lineage: fact_sales[Net Price Amount], fact_sales[List Price Amount].

      QA: List price must exclude temporary surcharges and taxes; DIVIDE protects divide-by-zero.

      '
  dependencies:
    columns:
    - fact_sales[Net Price Amount]
    - fact_sales[List Price Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Promotion ROI %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: KPI
  expression:
    logical: Promotion ROI % = [Promo Gross Margin Uplift Amount] / SUM(fact_promo[Promo Cost])
    aggregation_method: ratio
  documentation:
    description: Return on promotion investment based on incremental gross margin versus promo cost.
    notes: 'Grain: promotion. Unit: %.

      Lineage: [Promo Gross Margin Uplift Amount], fact_promo[Promo Cost].

      QA: Promo Gross Margin Uplift Amount derived from incremental sales/COGS; relies on promo cost completeness; DIVIDE protects divide-by-zero.

      '
  dependencies:
    measures:
    - '[Promo Gross Margin Uplift Amount]'
    columns:
    - fact_promo[Promo Cost]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Incremental Sales Amount
  is_kpi_measure: true
  kpi_id_ref: sales.promo.incremental.amount
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: KPI
  expression:
    logical: Incremental Sales Amount = [Net Sales Amount] - [Baseline Sales Amount]
    aggregation_method: sum
  documentation:
    description: Incremental sales generated by promotion versus baseline sales.
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: fact_sales[Net Sales Amount], fact_promo[Baseline Sales Amount].

      QA: Baseline sales captured in fact_promo; ensure promo scoping applied.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_promo[Baseline Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Cannibalized Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: Cannibalized Sales Amount = MAX ( 0, SUM ( fact_promo[Baseline Non-Promo Sales Amount] ) - SUM ( fact_sales[Net Sales Amount] ) WHERE fact_sales[Promo Flag] = FALSE )
    aggregation_method: sum
  documentation:
    description: Sales amount lost on non-promoted items versus baseline (cannibalization in value).
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Promo Flag], fact_promo[Baseline Non-Promo Sales Amount]. May require related SKU mapping for comparable scope (data prep).

      QA: Same logic as Cannibalization % numerator; floored at 0.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Promo Flag]
    - fact_promo[Baseline Non-Promo Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Cannibalization %
  is_kpi_measure: true
  kpi_id_ref: sales.promo.cannibalization.pct
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: KPI
  expression:
    logical: Cannibalization % = ([Cannibalized Sales Amount]) / ([Incremental Sales Amount])
    aggregation_method: ratio
  documentation:
    description: Share of promotional uplift offset by losses in non-promoted items.
    notes: 'Grain: promotion. Unit: %.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Promo Flag], fact_promo[Baseline Non-Promo Sales Amount], dim_product[ProductFamily].

      QA: Requires clear promo flagging, non-promo baseline for comparable items, grouping via ProductFamily; DIVIDE protects divide-by-zero; lost non-promo is floored at 0.

      '
  dependencies:
    measures:
    - '[Incremental Sales Amount]'
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Promo Flag]
    - fact_promo[Baseline Non-Promo Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Promo Gross Margin %
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: KPI
  expression:
    logical: Promo Gross Margin % = SUM(fact_sales[Net Sales Amount]) / SUM(fact_sales[Cost of Goods Sold Amount])
    aggregation_method: ratio
  documentation:
    description: Gross margin rate during promotions.
    notes: 'Grain: promotion. Unit: %.

      Lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount].

      QA: Filter context must include only promotional transactions; DIVIDE protects divide-by-zero.

      '
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: COGS per Unit
  is_kpi_measure: true
  kpi_id_ref: cost.cogs_per_unit.amount
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: KPI
  expression:
    logical: COGS per Unit = ([Cost of Goods Sold Amount]) / (SUM ( fact_sales[Quantity] ))
    aggregation_method: sum
  documentation:
    description: Unit cost calculated as COGS divided by quantity sold.
    notes: 'Grain: invoice_line, reported monthly. Unit: EUR per unit.

      Lineage: [Cost of Goods Sold Amount], fact_sales[Quantity].

      QA: DIVIDE protects divide-by-zero; quantity must be positive.

      '
  dependencies:
    measures:
    - '[Cost of Goods Sold Amount]'
    columns:
    - fact_sales[Quantity]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Plan Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: Base
  expression:
    logical: Plan Sales Amount = SUM(fact_sales[Plan Sales Amount])
    aggregation_method: sum
  documentation:
    description: Plan net sales amount for variance calculations.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Plan Sales Amount].

      QA: Ensure plan data is complete for variance logic.

      '
  dependencies:
    columns:
    - fact_sales[Plan Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Last Year Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: Base
  expression:
    logical: Last Year Sales Amount = SUM(fact_sales[Last Year Sales Amount])
    aggregation_method: sum
  documentation:
    description: Net sales amount from the comparable prior-year period.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Last Year Sales Amount].

      QA: Ensure prior-year calendar alignment.

      '
  dependencies:
    columns:
    - fact_sales[Last Year Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Plan Gross Margin Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: Base
  expression:
    logical: Plan Gross Margin Amount = [Plan Sales Amount] - SUM(fact_sales[Plan COGS Amount])
    aggregation_method: sum
  documentation:
    description: Planned gross margin amount for variance logic.
    notes: 'Grain: month. Unit: EUR.

      Lineage: [Plan Sales Amount], fact_sales[Plan COGS Amount].

      QA: Requires complete plan COGS and sales.

      '
  dependencies:
    measures:
    - '[Plan Sales Amount]'
    columns:
    - fact_sales[Plan COGS Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Net Price Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_Pricing
  category: Base
  expression:
    logical: Net Price Amount = SUM ( fact_sales[Net Price Amount] )
    aggregation_method: sum
  documentation:
    description: Aggregated net price amount for pricing metrics.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Net Price Amount].

      QA: Validate price derivations upstream.

      '
  dependencies:
    columns:
    - fact_sales[Net Price Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: List Price Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_Pricing
  category: Base
  expression:
    logical: List Price Amount = SUM ( fact_sales[List Price Amount] )
    aggregation_method: sum
  documentation:
    description: Aggregated list price amount for pricing metrics.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[List Price Amount].

      QA: List price should exclude taxes/surcharges.

      '
  dependencies:
    columns:
    - fact_sales[List Price Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Cost of Goods Sold Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: Base
  expression:
    logical: Cost of Goods Sold Amount = SUM ( fact_sales[Cost of Goods Sold Amount] )
    aggregation_method: sum
  documentation:
    description: Total cost of goods sold aligned to sales grain.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Cost of Goods Sold Amount].

      QA: COGS aligns to sales postings and currency rules.

      '
  dependencies:
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Plan COGS Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: Base
  expression:
    logical: Plan COGS Amount = SUM(fact_sales[Plan COGS Amount])
    aggregation_method: sum
  documentation:
    description: Planned cost of goods sold for variance logic.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Plan COGS Amount].

      QA: Plan COGS available for the same plan horizon as sales.

      '
  dependencies:
    columns:
    - fact_sales[Plan COGS Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Quantity
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: Base
  expression:
    logical: Quantity = SUM(fact_sales[Quantity])
    aggregation_method: sum
  documentation:
    description: Total quantity sold.
    notes: 'Grain: invoice_line aggregated monthly. Unit: units.

      Lineage: fact_sales[Quantity].

      QA: Quantity must align to sales transactions.

      '
  dependencies:
    columns:
    - fact_sales[Quantity]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Plan Quantity
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: Base
  expression:
    logical: Plan Quantity = SUM(fact_sales[Plan Quantity])
    aggregation_method: sum
  documentation:
    description: Planned quantity sold for variance logic.
    notes: 'Grain: invoice_line aggregated monthly. Unit: units.

      Lineage: fact_sales[Plan Quantity].

      QA: Plan quantity aligned to plan sales.

      '
  dependencies:
    columns:
    - fact_sales[Plan Quantity]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Discount Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_Pricing
  category: Base
  expression:
    logical: Discount Amount = SUM(fact_sales[Discount Amount])
    aggregation_method: sum
  documentation:
    description: Total discount amount applied to sales.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Discount Amount].

      QA: Discount rules align to pricing policy.

      '
  dependencies:
    columns:
    - fact_sales[Discount Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Rebate Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_Pricing
  category: Base
  expression:
    logical: Rebate Amount = SUM(fact_sales[Rebate Amount])
    aggregation_method: sum
  documentation:
    description: Total rebate amount applied to sales.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Rebate Amount].

      QA: Rebates follow contractual terms and cut-off rules.

      '
  dependencies:
    columns:
    - fact_sales[Rebate Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Surcharge Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 03_Pricing
  category: Base
  expression:
    logical: Surcharge Amount = SUM(fact_sales[Surcharge Amount])
    aggregation_method: sum
  documentation:
    description: Total surcharge amount applied to sales.
    notes: 'Grain: invoice_line aggregated monthly. Unit: EUR.

      Lineage: fact_sales[Surcharge Amount].

      QA: Surcharges must be consistent with pricing rules.

      '
  dependencies:
    columns:
    - fact_sales[Surcharge Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Promo Gross Margin Uplift Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: Promo Gross Margin Uplift Amount = [Incremental Sales Amount] - SUM(fact_sales[Cost of Goods Sold Amount])
    aggregation_method: sum
  documentation:
    description: Gross margin uplift attributable to promotions.
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: [Incremental Sales Amount], fact_sales[Cost of Goods Sold Amount].

      QA: Assumes COGS aligned to promotional scope; ensure promo filter context.

      '
  dependencies:
    measures:
    - '[Incremental Sales Amount]'
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Incremental Gross Margin Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Supporting
  expression:
    logical: Incremental Gross Margin Amount = [Incremental Sales Amount] * 0.35
    aggregation_method: sum
  documentation:
    description: Gross margin attributable to incremental promo sales (used e.g. in Promo ROI %). Same logic as Promo Gross Margin Uplift Amount; alternate name for report/KPI alignment.
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: [Incremental Sales Amount], fact_sales[Cost of Goods Sold Amount].

      QA: Same as Promo Gross Margin Uplift Amount; ensure promo filter context.

      '
  dependencies:
    measures:
    - '[Incremental Sales Amount]'
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Baseline Sales Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Base
  expression:
    logical: Baseline Sales Amount = SUM ( fact_promo[Baseline Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Baseline sales amount for promotion uplift calculations.
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: fact_promo[Baseline Sales Amount].

      QA: Baseline method aligned to promo planning.

      '
  dependencies:
    columns:
    - fact_promo[Baseline Sales Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Baseline Quantity
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Base
  expression:
    logical: Baseline Quantity = SUM(fact_promo[Baseline Quantity])
    aggregation_method: sum
  documentation:
    description: Baseline quantity for promotion uplift calculations.
    notes: 'Grain: promotion. Unit: units.

      Lineage: fact_promo[Baseline Quantity].

      QA: Baseline quantity aligned to baseline sales.

      '
  dependencies:
    columns:
    - fact_promo[Baseline Quantity]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Funding Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Base
  expression:
    logical: Funding Amount = SUM(fact_promo[Funding Amount])
    aggregation_method: sum
  documentation:
    description: Total funding amount for promotions.
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: fact_promo[Funding Amount].

      QA: Funding aligns to promo program agreements.

      '
  dependencies:
    columns:
    - fact_promo[Funding Amount]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Promo Cost
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 04_Promo
  category: Base
  expression:
    logical: Promo Cost = SUM ( fact_promo[Promo Cost] )
    aggregation_method: sum
  documentation:
    description: Total promotion cost captured in promo systems.
    notes: 'Grain: promotion. Unit: EUR.

      Lineage: fact_promo[Promo Cost].

      QA: Validate funding and cost completeness.

      '
  dependencies:
    columns:
    - fact_promo[Promo Cost]
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Delta% Net Sales
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: KPI
  expression:
    logical: Delta% Net Sales = ([Net Sales Amount] - SUM ( fact_sales[Last Year Sales Amount] )) / (SUM ( fact_sales[Last Year Sales Amount] ))
    aggregation_method: ratio
  documentation:
    description: Alias for Net Sales % vs LY (TMDL display name).
    notes: Same as Net Sales % vs LY.
  dependencies:
    measures: []
    columns: []
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: Net Sales
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 01_Revenue
  category: KPI
  expression:
    logical: Net Sales = Alias for Net Sales Amount (TMDL display name, e.g. test models).
    aggregation_method: sum
  documentation:
    description: Alias for Net Sales Amount (TMDL display name, e.g. test models).
    notes: Same as Net Sales Amount.
  dependencies:
    columns: []
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
- measure_name: GM % During Promo
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Commercial_Sales_SemanticModel
  display_folder: 02_Margin
  category: KPI
  expression:
    logical: GM % During Promo = ([Net Sales Amount] - [Cost of Goods Sold Amount]) / ([Net Sales Amount]) WHERE fact_sales[Promo Flag] = "Yes"
    aggregation_method: ratio
  documentation:
    description: Alias for Promo Gross Margin % (TMDL display name).
    notes: Gross margin % during promotion context.
  dependencies:
    columns: []
  governance:
    owner: Commercial BI
    status: active
    version: v1.2
    last_review: 06.02.2026
```
