# COM-002 – Technical Factsheet

## 0. Model References
- **Data Contract:** `data_contracts/domains/commercial_sales.yaml`
- **Semantic Model:** `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** COM-002

---

## 1. Data Contract Scope

(identical dims as COM-001, plus pricing & margin fields)

```yaml
fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: GM Plan %, type: number, agg: avg}
      - {name: GM Target %, type: number, agg: avg}
```

---

## 2. Semantic Model Requirements
Same tables/relationships/hierarchies as COM-001.

---

## 3. Measure Inventory

| Measure Name           | Folder        | Purpose |
|------------------------|---------------|----------|
| Gross Margin Amount    | 02_Margin     | KPI base |
| Gross Margin %         | 02_Margin     | KPI      |
| Price Realization %    | 03_Pricing    | KPI      |
| Discount %             | 03_Pricing    | KPI      |
| Margin vs Plan %       | 02_Margin     | KPI      |
| Margin Leakage Amount  | 02_Margin     | KPI      |

---

## 4. Measures (DAX)

```DAX
Gross Margin Amount =
    [Net Sales Amount] - [COGS Amount]
```

```DAX
Gross Margin % =
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )
```

```DAX
Price Realization % =
    DIVIDE (
        SUM ( fact_sales[Net Price Amount] ),
        SUM ( fact_sales[List Price Amount] )
    )
```

```DAX
Discount % =
    1 - [Price Realization %]
```

```DAX
Margin vs Plan % =
    DIVIDE ( [Gross Margin %] - AVERAGE ( fact_sales[GM Plan %] ),
             AVERAGE ( fact_sales[GM Plan %] ) )
```

```DAX
Margin Leakage Amount =
    ([GM Target %] - [Gross Margin %]) * [Net Sales Amount]
```

---

## 5. Formatting
All % = `0.0 %`  
All amounts = `€#,0.00`

---

## 6. RLS
Identical to COM-001.

---

## 7. QA Rules

| Check                 | Tolerance |
|-----------------------|-----------|
| GM % plausibility     | manual    |
| Margin vs Plan        | ±0.5 %    |
| Leakage consistency   | ±1 %      |

