# COM-004 – Technical Factsheet

## 0. Model References
- **Data Contract:** commercial_sales domain
- **Semantic Model:** core_action_ready/commercial_sales
- **KPI Catalog:** domain_kpi_catalog
- **Measure Dictionary:** domain_measure_dictionary
- **Use Case Inventory:** COM-003

---

## 1. Data Contract Scope

```yaml
dimension:
  - name: dim_promo
    columns:
      - {name: PromoID, type: text, role: key}
      - {name: PromoName, type: text}
      - {name: Mechanic, type: text}
      - {name: Retailer, type: text}
      - {name: PromoStartDate, type: date}
      - {name: PromoEndDate, type: date}

fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: PromoID, type: text, ref: dim_promo}
      - {name: Promo Cost Amount, type: currency, agg: sum}
      - {name: Baseline Qty, type: number, agg: avg}
      - {name: Baseline Sales Amount, type: currency, agg: avg}
```

---

## 2. Semantic Model Requirements
+ dim_promo added, with relationships:
- fact_sales[PromoID] → dim_promo[PromoID]

Promo hierarchy:
- Retailer → Mechanic → PromoName

---

## 3. Measure Inventory

| Measure Name           | Folder     | Type |
|------------------------|------------|------|
| Promo Qty              | 01_Promo   | Supporting |
| Baseline Qty           | 01_Promo   | Supporting |
| Promo Uplift Qty       | 01_Promo   | KPI |
| Promo Sales Amount     | 01_Promo   | Supporting |
| Baseline Sales Amount  | 01_Promo   | Supporting |
| Promo Uplift Amount    | 01_Promo   | KPI |
| Promo GM %             | 02_Margin  | KPI |
| Promo ROI              | 01_Promo   | KPI |
| Promo Leakage Amount   | 02_Margin  | KPI |

---

## 4. Measures (DAX)

```DAX
Promo Qty =
    SUM ( fact_sales[Quantity Qty] )
```

```DAX
Baseline Qty =
    AVERAGE ( fact_sales[Baseline Qty] )
```

```DAX
Promo Uplift Qty =
    [Promo Qty] - [Baseline Qty]
```

```DAX
Promo Sales Amount =
    SUM ( fact_sales[Net Sales Amount] )
```

```DAX
Baseline Sales Amount =
    AVERAGE ( fact_sales[Baseline Sales Amount] )
```

```DAX
Promo Uplift Amount =
    [Promo Sales Amount] - [Baseline Sales Amount]
```

```DAX
Promo GM % =
    DIVIDE (
        [Promo Sales Amount] - SUM ( fact_sales[COGS Amount] ),
        [Promo Sales Amount]
    )
```

```DAX
Promo ROI =
    DIVIDE (
        [Promo Uplift Amount] - SUM ( fact_sales[Promo Cost Amount] ),
        SUM ( fact_sales[Promo Cost Amount] )
    )
```

```DAX
Promo Leakage Amount =
    ([Baseline Sales Amount] * <Baseline GM %>)
        - ([Promo Sales Amount] * [Promo GM %])
```

---

## 5. Formatting
- Uplift Qty: `#,0`
- Amounts: `€#,0.00`
- Percentages: `0.0 %`

---

## 6. RLS
Same pattern as COM-001/002.

---

## 7. QA Rules

| Check                   | Threshold |
|-------------------------|-----------|
| Baseline stability      | manual    |
| Uplift reconciliation   | ±1 %      |
| ROI consistency         | ±1 %      |
| Leakage calculation     | ±1 %      |
