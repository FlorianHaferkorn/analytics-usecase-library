# KPI Catalog - Growth

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: sales.price.realization_pct
  kpi_key: Price Realization %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  calc_type: rate
  business:
    purpose: Shows how much of list price is realized after discounts.
    definition: Net Price Amount / List Price Amount.
    grain_scope: Invoice line aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Values below 100% indicate discounting; values above 100% indicate uplift vs list price.
  technical:
    dax_name: Price Realization %
    depends_on_measures:
    - Net Price Amount
    - List Price Amount
    lineage:
    - fact_sales.Net Price Amount
    - fact_sales.List Price Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Pricing Team
    steward: Pricing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounds [0%; 150%]
    - List price source reconciled to price books
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.pvm.mix_effect.amount
  kpi_key: Mix Effect Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Captures the residual effect from changes in product, channel, or region mix.
    definition: Total variance - Price Effect - Volume Effect.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Explains whether composition shifts drive positive or negative outcomes.
  technical:
    dax_name: Mix Effect Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Price + Volume + Mix reconcile to total variance
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: sales.net_sales.amount
  kpi_key: Net Sales Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: amount
  business:
    purpose: Total invoiced revenue net of discounts and returns.
    definition: Sum of all invoice line amounts net of VAT and returns.
    grain_scope: Invoice line.
    unit_format: EUR (2 decimals)
    interpretation: Represents total top-line sales.
  technical:
    dax_name: Net Sales Amount
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules: []
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 03.11.2025

- kpi_id: sales.net_sales.delta_pct.ly
  kpi_key: Delta% Net Sales
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: rate
  business:
    purpose: Relative variance of Net Sales vs Last Year.
    definition: (Net Sales - LY) / LY
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Shows growth rate vs prior year.
  technical:
    dax_name: Delta% Net Sales
    depends_on_measures:
    - Net Sales Amount
    - Net Sales Amount LY
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to Net Sales and LY revenue within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
  aliases:
  - Delta% Net Sales

- kpi_id: sales.net_sales.delta_pct.plan
  kpi_key: Net Sales % vs Plan
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  calc_type: rate
  business:
    purpose: Relative variance of Net Sales vs Plan.
    definition: (Net Sales Amount - Plan Sales Amount) / Plan Sales Amount
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate outperformance vs plan; negative values indicate shortfall.
  technical:
    dax_name: Net Sales % vs Plan
    depends_on_measures:
    - Net Sales Amount
    - Plan Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Plan Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to Net Sales and Plan revenue within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: sales.pvm.price_effect.amount
  kpi_key: Price Effect Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Quantifies the pure price impact in the PVM bridge.
    definition: (Actual Price - Plan Price) x Actual Quantity.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Positive values indicate price gains; negative values represent price pressure.
  technical:
    dax_name: Price Effect Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan price locked before period
    - Exclude items without plan price
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.pvm.volume_effect.amount
  kpi_key: Volume Effect Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  calc_type: amount
  business:
    purpose: Measures the variance caused purely by quantity changes at plan price.
    definition: (Actual Quantity - Plan Quantity) x Plan Price.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Positive values indicate higher volume than plan; negative values indicate volume shortfalls.
  technical:
    dax_name: Volume Effect Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan quantity frozen
    - Exclude negative plan quantities
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025

- kpi_id: sales.units
  kpi_key: Sales Units
  kpi_type: quantity
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - OPS-003
  - SCM-001
  - SCM-002
  - SCM-003
  calc_type: count
  business:
    purpose: Measures sold units volume in the period.
    definition: Sum of sold units across transactions.
    grain_scope: Transaction line; aggregated by period and segment.
    unit_format: units
    interpretation: Higher values indicate higher volume sold.
  technical:
    dax_name: Sales Units
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD
```
