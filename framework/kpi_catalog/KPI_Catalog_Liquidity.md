# KPI Catalog - Liquidity

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: wc.dso.days
  kpi_key: DSO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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

- kpi_id: fin.liquidity.operating_cash_flow
  kpi_key: Operating Cash Flow
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref: []
  action_code_ref: []
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
- kpi_id: fin.cash.balance
  kpi_key: Cash Balance
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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
  aliases:
  - fin.liquidity.operating_cash_flow

- kpi_id: fin.cash.vs_plan.pct
  kpi_key: Cash vs Plan %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref: []
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
```
