# Measure Dictionary Archive - Liquidity

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Inventory Amount
  is_kpi_measure: true
  kpi_id_ref: fin.liquidity.inventory.amount
  semantic_model: Liquidity_SemanticModel
  category: KPI
  expression:
    dax: "SUM ( fact_inventory[Inventory Amount] )"
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
    dax: "SUM ( fact_ap[AP Amount] )"
    formatString: 'EUR #,0.00'
  documentation:
    description: Accounts payable at period end
    notes: ''
  governance:
    owner: Finance BI
    status: active
    version: v1.0
    last_review: 04.11.2025
```

