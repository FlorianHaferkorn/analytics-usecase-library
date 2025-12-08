# COM-001 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/commercial_sales.yaml`
- **Semantic Model Definition:**  
  `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: COM-001)

---

## 1. Data Contract Scope (COM-001)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}
      - {name: Quarter, type: text}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: OrgCode, type: text}
      - {name: OrgName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Channel, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}

  - name: security_user_org
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: CustomerKey, type: int}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: Plan Sales Amount, type: currency, agg: sum}
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Physical Layer
- `lh_commercial_sales.fact_sales`  
- shared dims under `lh_shared.*`  
- security table under `lh_security.*`

---

## 2. Semantic Model Requirements

### Tables
- fact_sales  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (hidden)

### Relationships
- fact_sales[DateKey] → dim_date[DateKey]  
- fact_sales[OrgKey] → dim_org[OrgKey]  
- fact_sales[ProductKey] → dim_product[ProductKey]  

### Hierarchies
- Org: Region → Country → OrgName  
- Product: Category → Subcategory → ProductName  
- Date: Year → Quarter → Month → Date  

### Sort By
- Month → MonthNumber  
- ProductName → ProductCode  
- OrgName → OrgCode  

---

## 3. Measure Inventory

| Measure Name        | kpi_id                     | Folder       | Type        |
|---------------------|-----------------------------|--------------|-------------|
| Net Sales Amount    | sales.net.amount           | 01_Sales     | Supporting  |
| COGS Amount         | margin.cogs.amount         | 02_Margin    | Supporting  |
| Revenue Growth %    | sales.growth.pct           | 01_Sales     | KPI         |
| Sales vs Plan %     | sales.vs_plan.pct          | 01_Sales     | KPI         |
| Price Effect Amount | sales.driver.price.amount  | 03_Drivers   | KPI         |
| Volume Effect Qty   | sales.driver.volume.qty    | 03_Drivers   | KPI         |
| Mix Effect Amount   | sales.driver.mix.amount    | 03_Drivers   | KPI         |

---

## 4. Measures (DAX)

```DAX
Net Sales Amount =
    SUM ( fact_sales[Net Sales Amount] )
```

```DAX
COGS Amount =
    SUM ( fact_sales[COGS Amount] )
```

```DAX
Revenue Growth % =
    DIVIDE (
        [Net Sales Amount] - CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR ) ),
        CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR ) )
    )
```

```DAX
Sales vs Plan % =
    DIVIDE (
        [Net Sales Amount] - SUM ( fact_sales[Plan Sales Amount] ),
        SUM ( fact_sales[Plan Sales Amount] )
    )
```

*Drivers (simplified template logic, depending on data availability):*

```DAX
Price Effect Amount =
    ([Net Sales Amount] / [Quantity Qty])
        - CALCULATE ([Net Sales Amount] / [Quantity Qty], DATEADD ( dim_date[Date], -1, YEAR ))
```

```DAX
Volume Effect Qty =
    [Quantity Qty]
        - CALCULATE ( [Quantity Qty], DATEADD ( dim_date[Date], -1, YEAR ) )
```

```DAX
Mix Effect Amount =
    [Net Sales Amount]
        - ([Price Effect Amount] + [Volume Effect Qty] * CALCULATE ([Net Sales Amount] / [Quantity Qty], DATEADD ( dim_date[Date], -1, YEAR )))
```

---

## 5. Formatting

| Measure              | Format    |
|----------------------|-----------|
| Net Sales Amount     | €#,0.00   |
| Revenue Growth %     | 0.0 %     |
| Sales vs Plan %      | 0.0 %     |
| Price Effect Amount  | €#,0.00   |
| Volume Effect Qty    | #,0       |
| Mix Effect Amount    | €#,0.00   |

---

## 6. RLS

```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

---

## 7. QA Rules

| Check                     | Threshold |
|---------------------------|-----------|
| RI dim_org/dim_product    | ≥ 99.9 %  |
| Net Sales reconciliation  | ±0.5 %    |
| Driver decomposition      | sum(price+vol+mix) ≈ ΔSales | ±1 % |

