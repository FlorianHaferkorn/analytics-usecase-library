# KPI Catalog - Profitability

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: margin.gm.pct
  kpi_key: Gross Margin % (Operational)
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  - XD-003
  action_code_ref:
  - C-M2.1
  - C-M2.2
  - C-S1.1
  calc_type: ratio
  business:
    purpose: Provide the Gross Margin % used in commercial and management reporting at the same granularity as Net Sales.
    definition: (Net Sales Amount - COGS Amount) / Net Sales Amount
    grain_scope: Invoice line aggregated to reporting period, org, customer or product segments.
    unit_format: '% (1 decimal)'
    interpretation: Values above 0 % indicate positive gross profit; trend over time shows structural profitability changes.
  technical:
    dax_name: Gross Margin %
    depends_on_measures:
    - Net Sales Amount
    - COGS Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to strategic Gross Margin % within +/- 0.1 pp for the same slice
    version: v1.0
  metadata_quality:
    completeness_score: 0.9
    last_review: 19.11.2025

- kpi_id: sales.promo.roi.pct
  kpi_key: Promo ROI %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: ratio
  business:
    purpose: Measures profitability of promotions relative to spend.
    definition: (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount
    grain_scope: Promo campaign / product / period.
    unit_format: '% (1 decimal)'
    interpretation: Values > 0 indicate promotions adding value.
  technical:
    dax_name: Promo ROI %
    depends_on_measures:
    - Incremental GM Amount
    - Promo Cost Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_sales.Promo Cost Amount
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Promo cost > 0 required
    - Variance vs finance ROI < 2 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.82
    last_review: 11.11.2025

- kpi_id: margin.promo.gm.pct
  kpi_key: GM % During Promo
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: ratio
  business:
    purpose: Gross margin rate during promo periods.
    definition: (Promo NS - Promo COGS) / Promo NS
    grain_scope: Promo period/product
    unit_format: '% (1 decimal)'
    interpretation: Profitability of promotions.
  technical:
    dax_name: GM % During Promo
    depends_on_measures:
    - Promo Sales Amount
    - Promo COGS Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_sales.Promo Flag
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Promo mapping consistent with finance
    version: v2.0
  metadata_quality:
    completeness_score: 0.9
    last_review: 12.10.2025

- kpi_id: cost.cogs_per_unit.amount
  kpi_key: COGS per Unit
  kpi_type: rate
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Shows unit cost level relative to sold volume.
    definition: COGS Amount / Units Sold.
    grain_scope: Product / period.
    unit_format: EUR per unit
    interpretation: Lower is better; rising unit cost erodes margin.
  technical:
    dax_name: COGS per Unit
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Units Sold > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: sales.promo.cannibalization.pct
  kpi_key: Cannibalization %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-004
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of promo uplift offset by decline in non-promoted sales.
    definition: Cannibalized Sales / Promo Uplift Sales.
    grain_scope: Promo campaign / product / period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high cannibalization reduces net gain.
  technical:
    dax_name: Cannibalization %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Promo uplift > 0 for ratio
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: cost.material.pct
  kpi_key: Material Cost %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.2
  calc_type: rate
  business:
    purpose: Shows material cost share of net sales.
    definition: Material Cost Amount / Net Sales Amount.
    grain_scope: Company/segment; monthly close.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; increases indicate supplier or price pressure.
  technical:
    dax_name: Material Cost %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: cost.opex.vs_plan.pct
  kpi_key: OpEx vs Plan %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.4
  calc_type: rate
  business:
    purpose: Measures OpEx variance versus plan.
    definition: (OpEx Amount - OpEx Plan Amount) / OpEx Plan Amount.
    grain_scope: Company/segment; monthly close.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate overspend; negative values indicate savings.
  technical:
    dax_name: OpEx vs Plan %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan Amount > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: cost.unit.amount
  kpi_key: Unit Cost Amount
  kpi_type: rate
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.1
  - F-K2.2
  - F-K2.3
  - F-K2.4
  calc_type: ratio
  business:
    purpose: Measures total cost per unit produced or sold.
    definition: Total Cost Amount / Units Produced or Sold.
    grain_scope: Product / period.
    unit_format: EUR per unit
    interpretation: Lower is better; used to track cost efficiency.
  technical:
    dax_name: Unit Cost Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Units > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: profit.gross_margin
  kpi_key: Gross Margin %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Measures gross margin relative to net sales.
    definition: (Net Sales Amount - COGS Amount) / Net Sales Amount
    grain_scope: Invoice line aggregated to Org, Product, Date.
    unit_format: '% (1 decimal)'
    interpretation: Core profitability metric showing sales efficiency vs cost.
  technical:
    dax_name: Gross Margin %
    depends_on_measures:
    - Net Sales Amount
    - COGS Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Value in [-100%; 100%]
    - Reconcile with P&L Gross Margin +/-0.5 pp
    version: v2.0
  metadata_quality:
    completeness_score: 0.97
    last_review: 12.10.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: margin.gm.amount
  kpi_key: Gross Margin Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-M2.1
  - C-M2.2
  calc_type: amount
  business:
    purpose: Absolute gross margin in currency.
    definition: Net Sales Amount - COGS Amount
    grain_scope: Aggregated from invoice_line to reporting period.
    unit_format: EUR (2 decimals)
    interpretation: Explains profitability magnitude before OpEx.
  technical:
    dax_name: Gross Margin Amount
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconcile with P&L GM within +/-0.5%
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 12.10.2025
  aliases:
  - hr.gm.amount

- kpi_id: sales.promo.incremental.amount
  kpi_key: Incremental Sales Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: amount
  business:
    purpose: Additional sales due to promotion.
    definition: Promo Sales Amount - Baseline Sales Amount
    grain_scope: Promo period/product
    unit_format: EUR (2 decimals)
    interpretation: Input to promo ROI.
  technical:
    dax_name: Incremental Sales Amount
    depends_on_measures:
    - Promo Sales Amount
    - Baseline Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Promo Flag
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Baseline method documented; overlap handling
    version: v2.0
  metadata_quality:
    completeness_score: 0.9
    last_review: 12.10.2025

- kpi_id: margin.cogs.pct
  kpi_key: COGS % of Sales
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.1
  calc_type: rate
  business:
    purpose: Shows cost share relative to net sales.
    definition: COGS Amount / Net Sales Amount.
    grain_scope: Invoice line aggregated to period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; complements gross margin %.
  technical:
    dax_name: COGS % of Sales
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: margin.gm.vs_plan.pct
  kpi_key: Gross Margin % vs Plan
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures gross margin rate variance versus plan.
    definition: (Gross Margin % - Plan Gross Margin %) / Plan Gross Margin %.
    grain_scope: Company/segment; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate better-than-plan margin.
  technical:
    dax_name: Gross Margin % vs Plan
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Plan GM % available for reported period
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: cost.base_volume.amount
  kpi_key: Cost Base Volume Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.1
  - F-K2.2
  calc_type: amount
  business:
    purpose: Baseline cost volume used for variance analysis.
    definition: Baseline amount of cost volume for the selected period.
    grain_scope: Cost center or product; aggregated by period.
    unit_format: EUR (2 decimals)
    interpretation: Provides a stable base for cost variance comparisons.
  technical:
    dax_name: Cost Base Volume Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Cost Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: cost.opex.base.amount
  kpi_key: Opex Base Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.4
  calc_type: amount
  business:
    purpose: Baseline operating expense amount for variance tracking.
    definition: Baseline operating expense amount for the selected period.
    grain_scope: Cost center; aggregated by period.
    unit_format: EUR (2 decimals)
    interpretation: Used to compare actual Opex against the base.
  technical:
    dax_name: Opex Base Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Cost Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD
```
