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
    interpretation: Higher DSO indicates slower collections and weaker cash conversion; lower is better within credit policy bounds.
  technical:
    dax_name: DSO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review; canonical working capital KPI; cross-domain views must reference this definition.
    qa_rules:
    - DSO bounded between 0 and 180 days; reconciles to AR and revenue balances within +/- 1 day.
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
    interpretation: Higher DIO indicates slower inventory movement and more capital tied up; very low values may raise stockout risk.
  technical:
    dax_name: DIO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review; canonical working capital KPI; cross-domain views must reference this definition.
    qa_rules:
    - DIO bounded between 0 and 365 days; reconciles to inventory and COGS balances within +/- 1 day.
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
    interpretation: Higher DPO indicates longer payment terms and better cash preservation; too high may strain supplier relationships.
  technical:
    dax_name: DPO (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review; canonical working capital KPI; cross-domain views must reference this definition.
    qa_rules:
    - DPO bounded between 0 and 180 days; reconciles to AP and COGS balances within +/- 1 day.
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
    interpretation: Lower CCC indicates faster cash conversion; negative CCC implies customers fund operations.
  technical:
    dax_name: CCC (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review; canonical working capital KPI; cross-domain views must reference this definition.
    qa_rules:
    - CCC bounded within plausible range; reconciles to constituent DSO/DIO/DPO values.
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
    interpretation: Positive delta indicates worsening cash conversion; negative delta indicates improvement.
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
    interpretation: Higher values indicate stronger investment activity; compare to budget and cash generation.
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
    interpretation: Higher values increase working capital needs; validate against seasonality and service targets.
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
    interpretation: Higher balances increase working capital funding but can signal payment delays; compare to terms.
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

- kpi_id: fin.cash.balance
  kpi_key: Cash Balance
  kpi_type: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Tracks cash and cash equivalents at period end.
    definition: Cash and cash equivalents balance.
    grain_scope: Company/segment; monthly close.
    unit_format: EUR (2 decimals)
    interpretation: Higher balance improves liquidity buffer; consider seasonality and debt strategy.
  technical:
    dax_name: Cash Balance
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Management Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to balance sheet cash accounts within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: fin.cash.ocf
  kpi_key: Operating Cash Flow
  kpi_type: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Measures cash generated by operating activities.
    definition: Net cash flows from operations for the period.
    grain_scope: Company/segment; monthly close.
    unit_format: EUR (2 decimals)
    interpretation: Positive values improve liquidity; negative values require investigation.
  technical:
    dax_name: Operating Cash Flow
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Flow Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to cashflow statement within +/- 1 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: fin.cash.vs_plan.pct
  kpi_key: Cash vs Plan %
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: rate
  business:
    purpose: Measures deviation of cash balance versus plan.
    definition: (Cash Balance - Cash Plan) / Cash Plan.
    grain_scope: Company/segment; monthly close.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate higher cash than planned.
  technical:
    dax_name: Cash vs Plan %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Flow Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan Amount > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: fin.liquidity.receivables.amount
  kpi_key: Receivables Amount
  kpi_type: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Tracks accounts receivable balance at period end.
    definition: Accounts receivable balance.
    grain_scope: Company/segment; monthly close.
    unit_format: EUR (2 decimals)
    interpretation: Higher balances tie up cash; monitor against DSO targets.
  technical:
    dax_name: Receivables Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to AR ledger within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: wc.dso.days
  kpi_key: DSO Days
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Measures days sales outstanding for receivables.
    definition: Receivables / (Net Sales / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower is better; rising DSO indicates collection issues.
  technical:
    dax_name: DSO Days
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Net Sales > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: wc.dio.days
  kpi_key: DIO Days
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Measures days inventory outstanding.
    definition: Inventory / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower is better; high DIO increases cash tied up in stock.
  technical:
    dax_name: DIO Days
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury / Supply Chain Finance
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - COGS > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: wc.dpo.days
  kpi_key: DPO Days
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Measures days payables outstanding.
    definition: Payables / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Higher values improve cash but may impact supplier terms.
  technical:
    dax_name: DPO Days
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury / Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - COGS > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: wc.ccc.days
  kpi_key: CCC Days
  kpi_type: diagnostic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  calc_type: amount
  business:
    purpose: Measures cash conversion cycle length.
    definition: DSO + DIO - DPO.
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower values indicate faster cash recovery.
  technical:
    dax_name: CCC Days
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - DSO, DIO, DPO available for period
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
```
