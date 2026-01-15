# Archived KPIs - KPI_Catalog_Profitability

```yaml
- kpi_id: profit.ebitda_margin
  kpi_key: EBITDA Margin %
  kpi_type: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-002
  calc_type: ratio
  business:
    purpose: Shows earnings before interest, taxes, depreciation, and amortization as a share of revenue.
    definition: EBITDA Amount / Net Sales Amount
    grain_scope: Monthly close data, company level.
    unit_format: '% (1 decimal)'
    interpretation: Represents operational profitability before financial effects.
  technical:
    dax_name: EBITDA Margin %
    depends_on_measures:
    - EBITDA Amount
    - Net Sales Amount
    lineage:
    - fact_finance.EBITDA Amount
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Financial Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - EBITDA reconciles with P&L within +/-0.2 pp
    version: v2.0
  metadata_quality:
    completeness_score: 0.95
    last_review: 12.10.2025

- kpi_id: cost.cogs.amount
  kpi_key: COGS Amount
  kpi_type: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-003
  calc_type: amount
  business:
    purpose: Represents cost of goods sold directly linked to sales.
    definition: Sum of all product cost components for sold units.
    grain_scope: Invoice line.
    unit_format: EUR (2 decimals)
    interpretation: Input for gross margin calculation.
  technical:
    dax_name: COGS Amount
    depends_on_measures:
    - Invoice Cost Amount
    lineage:
    - fact_sales.COGS Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - COGS must reconcile with P&L COGS +/-0.5 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.99
    last_review: 12.10.2025


- kpi_id: margin.gm.delta_amount
  kpi_key: '? Gross Margin Amount'
  kpi_type: diagnostic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-004
  calc_type: amount
  business:
    purpose: Explains absolute change in gross margin vs Plan or Last Year.
    definition: Gross Margin Amount - Baseline GM Amount (Plan/LY).
    grain_scope: Aggregated to reporting period.
    unit_format: EUR (2 decimals)
    interpretation: Quantifies bridge contribution of gross margin variance.
  technical:
    dax_name: '? Gross Margin Amount'
    depends_on_measures:
    - Gross Margin Amount
    - Plan Gross Margin Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - fact_plan_sales.Plan Gross Margin Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Variance reconciles to financial bridge within +/-0.5%
    version: v1.0
  metadata_quality:
    completeness_score: 0.85
    last_review: 11.11.2025


- kpi_id: margin.gm.delta_pct
  kpi_key: Gross Margin % Delta%
  kpi_type: diagnostic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  calc_type: rate
  business:
    purpose: Relative change in Gross Margin % vs Last Year.
    definition: ([Gross Margin %] - CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date]))) / CALCULATE([Gross Margin
      %], SAMEPERIODLASTYEAR('Date'[Date]))
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Shows relative profitability improvement vs LY.
  technical:
    dax_name: Gross Margin % Delta%
    depends_on_measures:
    - Gross Margin %
    lineage: []
  governance:
    business_owner: Controlling
    data_owner: BI Engineering
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Cross-check against GM% and LY base
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 06.11.2025



- kpi_id: fin.ebitda.amount
  kpi_key: EBITDA Amount
  kpi_type: supporting
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Provide EBITDA as key profitability indicator before financing and non-cash charges.
    definition: Earnings before interest, taxes, depreciation and amortization for the period.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Higher EBITDA indicates stronger operating profitability; compare to margin and cash flow trends.
  technical:
    dax_name: EBITDA Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of FP&A
    data_owner: Finance BI
    steward: Financial Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - EBITDA reconciles to management P&L within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025


- kpi_id: margin.gm.plan.amount
  kpi_key: Plan Gross Margin Amount
  kpi_type: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Store planned gross margin to compare actual profitability against budget.
    definition: Gross margin amount from approved plan or budget for the period.
    grain_scope: Company/segment/product; aligned with planning hierarchy and calendar.
    unit_format: EUR (2 decimals)
    interpretation: Baseline for variance analysis; deviations highlight pricing, mix, or cost changes versus plan.
  technical:
    dax_name: Plan Gross Margin Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Margin Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Plan GM reconciles to approved budget/plan version; single source of truth for comparisons.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025


- kpi_id: margin.customer.amount
  kpi_key: Customer Margin Amount
  kpi_type: diagnostic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-006
  calc_type: amount
  business:
    purpose: Measure gross margin generated by a specific customer or customer segment.
    definition: Net Sales Amount - COGS Amount aggregated by customer.
    grain_scope: Customer / customer group / region / period.
    unit_format: EUR (2 decimals)
    interpretation: Shows absolute profitability contribution of a customer or segment.
  technical:
    dax_name: Customer Margin Amount
    depends_on_measures:
    - Net Sales Amount
    - COGS Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - dim_customer.CustomerID
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review and reconciliation vs margin bridge
    qa_rules:
    - Aggregated margin by customer reconciles to P&L gross margin within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.85
    last_review: 19.11.2025


- kpi_id: margin.customer.pct
  kpi_key: Customer Margin %
  kpi_type: diagnostic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-006
  calc_type: rate
  business:
    purpose: Show gross margin rate for a customer or segment.
    definition: Customer Margin Amount / Net Sales Amount.
    grain_scope: Customer / customer group / region / period.
    unit_format: '% (1 decimal)'
    interpretation: Values below target indicate unprofitable or weakly priced relationships.
  technical:
    dax_name: Customer Margin %
    depends_on_measures:
    - Customer Margin Amount
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.COGS Amount
    - dim_customer.CustomerID
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review and comparison vs overall GM %
    qa_rules:
    - Weighted average customer margin % reconciles to overall GM % within +/- 0.2 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.85
    last_review: 19.11.2025


```
