# Measure Dictionary - Liquidity

Schema: see `/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Working Capital %
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.working_capital
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Receivables Amount]+[Inventory Amount]-[Payables Amount],[Net Sales Amount])
    formatString: 0.0 %
  documentation:
    description: Share of (AR + Inventory - AP) relative to Net Sales.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Inventory Amount
    - Payables Amount
    - Net Sales Amount
    columns:
    - fact_balance.Receivables
    - fact_balance.Inventory
    - fact_balance.Payables
    - fact_sales.Net Sales Amount
- measure_name: Free Cash Flow
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.free_cash_flow
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '[Operating Cash Flow]-[CapEx Amount]'
    formatString: 'EUR #,0.00'
  documentation:
    description: Net cash generated after capital expenditures.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Operating Cash Flow
    - CapEx Amount
    columns:
    - fact_cashflow.OperatingCashFlow
    - fact_cashflow.CapEx
- measure_name: DSO (Days)
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.dso_days_sales_outstanding
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: (Accounts Receivable / Net Sales) x Days in Period
    notes: Canonical Working Capital metric; cross-domain views should reference this definition.
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Operating Cash Flow
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.operating_cash_flow
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Cash generated from operations
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: DIO (Days)
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.dio_days_inventory_outstanding
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: (Inventory / COGS) x Days in Period
    notes: Canonical Working Capital metric; cross-domain views should reference this definition.
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: DPO (Days)
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.dpo_days_payables_outstanding
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: (Accounts Payable / COGS) x Days in Period
    notes: Canonical Working Capital metric; cross-domain views should reference this definition.
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: CCC (Days)
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.cash_conversion_cycle_days
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: DSO + DIO - DPO
    notes: Canonical Working Capital metric; cross-domain views should reference this definition.
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Delta CCC (Days)
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.cash_conversion_cycle.delta_days
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '0'
  documentation:
    description: CCC (Days) - Baseline (Plan or LY)
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: CapEx Amount
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.capex.amount
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Capital expenditures
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Inventory Amount
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.inventory.amount
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Inventory value at period end
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Payables Amount
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.payables.amount
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 'EUR #,0.00'
  documentation:
    description: Accounts payable at period end
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: CapEx to Net Sales Ratio %
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.capex_ratio.pct
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: 0.0 %
  documentation:
    description: CapEx as a percentage of Net Sales.
    notes: ''
  governance:
    owner: Finance BI
    status: draft
    version: v0.1
    last_review: 19.11.2025
  display_folder: 02_Investments
  dependencies:
    measures:
    - CapEx Amount
    - Net Sales Amount
    columns:
    - fact_cashflow.CapEx
    - fact_sales.Net Sales Amount
```
