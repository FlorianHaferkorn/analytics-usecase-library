# FIN-001 – Technical Factsheet

## 0. Model References
- **Data Contract:** `data_contracts/domains/finance_cash_liquidity.yaml`
- **Semantic Model:** `semantic_models/core_action_ready/finance_cash/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** FIN-001

---

## 1. Data Contract Scope

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: MonthNumber, type: int}
      - {name: Month, type: text}
      - {name: Year, type: int}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: OrgName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}

fact:
  - name: fact_ar
    grain: customer_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: CustomerKey, type: int}
      - {name: AR Amount, type: currency, agg: sum}
      - {name: AR Aging Bucket, type: text}

  - name: fact_ap
    grain: supplier_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: SupplierKey, type: int}
      - {name: AP Amount, type: currency, agg: sum}
      - {name: AP Aging Bucket, type: text}

  - name: fact_inventory
    grain: product_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int}
      - {name: Inventory Amount, type: currency, agg: sum}
      - {name: Inventory Qty, type: number, agg: sum}

  - name: fact_cash
    grain: org_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Cash Position Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 2. Semantic Model Requirements

### Tables
- fact_ar  
- fact_ap  
- fact_inventory  
- fact_cash  
- dim_date  
- dim_org  

### Relationships
- All fact tables link DateKey → dim_date  
- All fact tables link OrgKey → dim_org  

### Hierarchies
- Date: Year → Month → Date  
- Org: Region → Country → OrgName  

### Sort-by
- Month → MonthNumber  

---

## 3. Measure Inventory

| Measure Name            | kpi_id                           | Folder         | Type        | Format   |
|-------------------------|-----------------------------------|----------------|-------------|----------|
| AR Amount               | fin.ar.amount                    | 01_AR          | Supporting  | €#,0.00  |
| AP Amount               | fin.ap.amount                    | 02_AP          | Supporting  | €#,0.00  |
| Inventory Amount        | fin.inventory.amount             | 03_Inventory   | Supporting  | €#,0.00  |
| Cash Position Amount    | fin.cash.position.amount         | 04_Cash        | KPI         | €#,0.00  |
| Working Capital Amount  | fin.wc.amount                    | 05_WC          | KPI         | €#,0.00  |
| DSO                     | fin.wc.dso.days                  | 05_WC          | KPI         | #,0      |
| DPO                     | fin.wc.dpo.days                  | 05_WC          | KPI         | #,0      |
| DIO                     | fin.wc.dio.days                  | 05_WC          | KPI         | #,0      |
| Cash Conversion Cycle   | fin.wc.ccc.days                  | 05_WC          | KPI         | #,0      |

---

## 4. Measures (DAX)

### Core amounts

```DAX
AR Amount =
    SUM ( fact_ar[AR Amount] )
```

```DAX
AP Amount =
    SUM ( fact_ap[AP Amount] )
```

```DAX
Inventory Amount =
    SUM ( fact_inventory[Inventory Amount] )
```

```DAX
Cash Position Amount =
    SUM ( fact_cash[Cash Position Amount] )
```

### Working Capital

```DAX
Working Capital Amount =
    [AR Amount] + [Inventory Amount] - [AP Amount]
```

### DSO

```DAX
DSO =
    VAR daily_sales =
        DIVIDE ( [AR Amount], [Net Sales Amount LY Basis Placeholder] )
    RETURN daily_sales
```

*(You will replace the placeholder with your actual sales fact source.)*

### DPO

```DAX
DPO =
    VAR daily_cogs =
        DIVIDE ( [AP Amount], [COGS Amount LY Basis Placeholder] )
    RETURN daily_cogs
```

### DIO

```DAX
DIO =
    VAR daily_cogs =
        DIVIDE ( [Inventory Amount], [COGS Amount LY Basis Placeholder] )
    RETURN daily_cogs
```

### Cash Conversion Cycle

```DAX
Cash Conversion Cycle =
    [DSO] + [DIO] - [DPO]
```

---

## 5. Formatting
- € Amounts: `€#,0.00`
- Days: `#,0`

---

## 6. RLS

```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( dim_org[Region] ),
        dim_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

---

## 7. QA Rules

| Check                        | Threshold |
|------------------------------|-----------|
| AR/AP/Inventory RI           | ≥ 99.9 %  |
| WC = AR + Inventory – AP     | exact     |
| DSO/DPO/DIO plausibility     | manual    |
| Cash Position reconciliation | ±0.5 %    |
