# KPI Catalog - Liquidity

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: fin.liquidity.working_capital
  kpi_key: Working Capital %
  kpi_type: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-001
  calc_type: ratio
  business:
    purpose: Share of capital tied up in operations relative to sales.
    definition: (Receivables + Inventory  Payables) / Net Sales Amount
    grain_scope: Monthly close level, companywide.
    unit_format: '% (1 decimal)'
    interpretation: Indicates liquidity efficiency and cash tied up in operations.
  technical:
    dax_name: Working Capital %
    depends_on_measures:
    - Inventory Amount
    - Payables Amount
    - Net Sales Amount
    lineage:
    - fact_balance.Receivables
    - fact_balance.Inventory
    - fact_balance.Payables
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Treasury Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconcile with balance sheet +/-1 %
    - Inventory coverage ratio cross-checked monthly
    version: v2.0
  metadata_quality:
    completeness_score: 0.97
    last_review: 12.10.2025
- kpi_id: fin.liquidity.free_cash_flow
  kpi_key: Free Cash Flow
  kpi_type: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-004
  calc_type: amount
  business:
    purpose: Net cash generated after capital expenditures.
    definition: Operating Cash Flow  CapEx Amount
    grain_scope: Monthly companywide.
    unit_format: (2 decimals)
    interpretation: Indicates cash generation capability after investment.
  technical:
    dax_name: Free Cash Flow
    depends_on_measures:
    - Operating Cash Flow
    - CapEx Amount
    lineage:
    - fact_cashflow.OperatingCashFlow
    - fact_cashflow.CapEx
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cashflow Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconcile with cashflow statement +/-1 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.96
    last_review: 12.10.2025
- kpi_id: fin.liquidity.operating_cash_flow
  kpi_key: Operating Cash Flow
  kpi_type: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Measure cash generated from core operations as basis for liquidity steering.
    definition: Net cash inflows from operating activities over the period.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Positive values improve liquidity; negative values may occur during growth or working-capital buildup.
  technical:
    dax_name: Operating Cash Flow
    depends_on_measures:
    - Operating Cash Flow Amount
    lineage:
    - fact_cashflow.OperatingCashFlow
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Flow Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Operating cash flow reconciles to cash flow statement within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: fin.liquidity.dso_days_sales_outstanding
  kpi_key: DSO (Days Sales Outstanding)
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Operational Efficiency
  - Working Capital
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Average number of days to collect receivables.
    definition: (Accounts Receivable / Net Sales) x Days in Period
    grain_scope: Company/segment; monthly closing.
    unit_format: days
    interpretation: TODO - add interpretation.
  technical:
    dax_name: DSO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
      qa_rules:
      - DSO bounded between 0 and 180 days; reconciles to AR and revenue balances within +/- 1 day.
      canonical: true
      note: Canonical Working Capital KPI; cross-domain views in other domains must reference this definition.
      version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.dio_days_inventory_outstanding
  kpi_key: DIO (Days Inventory Outstanding)
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Operational Efficiency
  - Working Capital
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Average number of days inventory is held.
    definition: (Inventory / COGS) x Days in Period
    grain_scope: Company/segment; monthly closing.
    unit_format: days
    interpretation: TODO - add interpretation.
  technical:
    dax_name: DIO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
      qa_rules:
      - DIO bounded between 0 and 365 days; reconciles to inventory and COGS balances within +/- 1 day.
      canonical: true
      note: Canonical Working Capital KPI; cross-domain views in other domains must reference this definition.
      version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.dpo_days_payables_outstanding
  kpi_key: DPO (Days Payables Outstanding)
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Operational Efficiency
  - Working Capital
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Average number of days to pay suppliers.
    definition: (Accounts Payable / COGS) x Days in Period
    grain_scope: Company/segment; monthly closing.
    unit_format: days
    interpretation: TODO - add interpretation.
  technical:
    dax_name: DPO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
      qa_rules:
      - DPO bounded between 0 and 180 days; reconciles to AP and COGS balances within +/- 1 day.
      canonical: true
      note: Canonical Working Capital KPI; cross-domain views in other domains must reference this definition.
      version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.cash_conversion_cycle_days
  kpi_key: Cash Conversion Cycle (Days)
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Operational Efficiency
  - Working Capital
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Combine receivables, inventory and payables days to show overall cash efficiency.
    definition: DSO + DIO - DPO.
    grain_scope: Company/segment; monthly closing.
    unit_format: days
    interpretation: TODO - add interpretation.
  technical:
    dax_name: CCC (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
      qa_rules:
      - CCC bounded within plausible range; reconciles to constituent DSO/DIO/DPO values.
      canonical: true
      note: Canonical Working Capital KPI; cross-domain views in other domains must reference this definition.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.cash_conversion_cycle.delta_days
  kpi_key: Delta Cash Conversion Cycle (Days)
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Show change in Cash Conversion Cycle versus baseline (Plan or Last Year).
    definition: CCC (Days) - baseline CCC (Plan or LY).
    grain_scope: Company/segment; monthly closing.
    unit_format: days
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Delta CCC (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Delta CCC reconciles to difference between current and baseline CCC within +/- 1 day.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
  aliases:
  - Delta CCC (Days)
- kpi_id: fin.liquidity.capex.amount
  kpi_key: CapEx Amount
  kpi_type: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Track capital expenditures as part of liquidity and investment planning.
    definition: Total capital expenditure amount for the selected org/time slice.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: CapEx Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury / Finance
    data_owner: Finance BI
    steward: CapEx Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - CapEx reconciles to fixed-asset and CapEx ledgers within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.inventory.amount
  kpi_key: Inventory Amount
  kpi_type: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Provide closing inventory value for working capital and liquidity metrics.
    definition: Inventory value at period end at reporting valuation (e.g., standard or average cost).
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Inventory Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury / Supply Chain Finance
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory value reconciles to balance sheet inventory accounts within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.payables.amount
  kpi_key: Payables Amount
  kpi_type: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Track accounts payable balances used in DPO and working capital analysis.
    definition: Accounts payable balance at period end.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: TODO - add interpretation.
  technical:
    dax_name: Payables Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury / Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Payables reconcile to AP ledgers within +/- 0.5 %; non-negative values.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: fin.liquidity.capex_ratio.pct
  kpi_key: CapEx to Net Sales Ratio %
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-009
  calc_type: rate
  business:
    purpose: Measure investment intensity relative to company size.
    definition: CapEx Amount divided by Net Sales Amount for the same period.
    grain_scope: Company / segment; quarterly or annually.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate stronger investment intensity; must be evaluated versus strategy, industry benchmarks,
      and Free Cash Flow.
  technical:
    dax_name: CapEx to Net Sales Ratio %
    depends_on_measures:
    - CapEx Amount
    - Net Sales Amount
    lineage:
    - fact_cashflow.CapEx
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Investment Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - CapEx and Net Sales reconciled to financial statements
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
```
