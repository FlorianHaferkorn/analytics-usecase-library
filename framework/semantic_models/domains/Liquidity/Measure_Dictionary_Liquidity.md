# Measure Dictionary - Liquidity

Schema: see `framework/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Operating Cash Flow Amount
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: Liquidity_SemanticModel
  category: Base
  expression:
    dax: "SUM ( fact_cashflow[Operating Cash Flow Amount] )"
    formatString: 'EUR #,0.00'
  documentation:
    description: Operating cash flow amount from the cash flow statement.
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
  dependencies:
    columns:
    - fact_cashflow[Operating Cash Flow Amount]

- measure_name: Operating Cash Flow
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.operating_cash_flow
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: '[Operating Cash Flow Amount]'
    formatString: 'EUR #,0.00'
  documentation:
    description: Cash generated from operations
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
    dax: 'SUM ( fact_inventory[Inventory Value] )'
    formatString: 'EUR #,0.00'
  documentation:
    description: Inventory value at period end
    notes: 'Used for working capital and liquidity calculations'
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 27.01.2026

- measure_name: Payables Amount
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.payables.amount
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: 'SUM ( fact_payables[Payables Balance] )'
    formatString: 'EUR #,0.00'
  documentation:
    description: Accounts payable balance at period end
    notes: 'Used for DPO and working capital analysis'
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 27.01.2026
```


