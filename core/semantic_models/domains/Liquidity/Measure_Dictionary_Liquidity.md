# Measure Dictionary - Liquidity

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Operating Cash Flow Amount
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Liquidity_SemanticModel
  display_folder: 01_CashFlow
  category: Base
  expression:
    aggregation_method: sum
    logical: Operating Cash Flow Amount = SUM(fact_cashflow[Operating Cash Flow Amount])
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
  kpi_id_ref: fin.cash.ocf
  semantic_model: Liquidity_SemanticModel
  display_folder: 01_CashFlow
  category: KPI
  expression:
    aggregation_method: sum
    logical: Operating Cash Flow = SUM(fact_cashflow[Operating Cash Flow Amount]) for the reporting period
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
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: last_value
    logical: Inventory Amount = SUM(fact_inventory[Average Inventory Amount]) at latest DateKey in filter context
  documentation:
    description: Inventory value at period end
    notes: Used for working capital and liquidity calculations
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 27.01.2026

- measure_name: Payables Amount
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.payables.amount
  semantic_model: Liquidity_SemanticModel
  display_folder: 02_WorkingCapital
  category: KPI
  expression:
    aggregation_method: last_value
    logical: Payables Amount = SUM(fact_ap[AP Amount]) at latest DateKey in filter context
  documentation:
    description: Accounts payable balance at period end
    notes: Used for DPO and working capital analysis
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 27.01.2026
```


