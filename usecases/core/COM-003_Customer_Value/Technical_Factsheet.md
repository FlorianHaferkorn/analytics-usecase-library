# COM-003 – Technical Factsheet (Customer Value)

## 0. Model References
- **Data Contract:** `data_contracts/domains/commercial_customer.yaml`
- **Semantic Model:** `semantic_models/core_action_ready/commercial_customer/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** COM-003

---

## 1. Data Contract Scope

```yaml
dimension:
  - name: dim_customer
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: CustomerCode, type: text}
      - {name: CustomerName, type: text}
      - {name: Segment, type: text}
      - {name: Region, type: text}
      - {name: Channel, type: text}

  - name: dim_date
    columns:
      - {name: DateKey, role: key, type: int}
      - {name: Date, type: date}
      - {name: MonthNumber, type: int}
      - {name: Month, type: text}
      - {name: Year, type: int}

  - name: security_user_org
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Channel, type: text}
      - {name: Region, type: text}

fact:
  - name: fact_customer_sales
    grain: customer_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: Visits Count, type: int, agg: sum}
      - {name: Tickets Count, type: int, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 2. Semantic Model Requirements

### Tables
- fact_customer_sales  
- dim_customer  
- dim_date  
- security_user_org (hidden)

### Relationships
- fact → customer  
- fact → date  

### Hierarchies
- Customer: Region → Channel → CustomerName  
- Date: Year → Month → Date  

### Sort-by
- Month → MonthNumber  

---

## 3. Measure Inventory

| Measure Name          | kpi_id                       | Type        | Folder           | Format   |
|-----------------------|-------------------------------|-------------|------------------|----------|
| Net Sales Amount      | customer.sales.amount        | Supporting  | 01_Value         | €#,0.00  |
| COGS Amount           | customer.cogs.amount         | Supporting  | 01_Value         | €#,0.00  |
| Gross Margin %        | customer.gm.pct              | KPI         | 02_Margin        | 0.0 %    |
| Revenue Growth %      | customer.growth.pct          | KPI         | 01_Value         | 0.0 %    |
| CLV Amount            | customer.clv.amount          | KPI         | 01_Value         | €#,0.00  |
| Churn Risk Score      | customer.churn.score         | KPI         | 03_Risk          | 0.00     |
| Customer Value Score  | customer.value.score         | KPI index   | 01_Value         | 0.00     |

---

## 4. Measures (DAX)

```DAX
Net Sales Amount =
    SUM ( fact_customer_sales[Net Sales Amount] )
```

```DAX
COGS Amount =
    SUM ( fact_customer_sales[COGS Amount] )
```

```DAX
Gross Margin % =
    DIVIDE ( [Net Sales Amount] - [COGS Amount], [Net Sales Amount] )
```

```DAX
Revenue Growth % =
    DIVIDE (
        [Net Sales Amount] - CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR )),
        CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR ))
    )
```

### CLV (simple version, replaceable with advanced model)

```DAX
CLV Amount =
    CALCULATE (
        SUMX (
            VALUES ( dim_date[Year] ),
            [Net Sales Amount] * 0.15    // margin proxy
        ),
        ALL ( dim_date )
    )
```

### Customer Value Score

```DAX
Customer Value Score =
    VAR _gm = [Gross Margin %]
    VAR _growth = [Revenue Growth %]
    VAR _clv = [CLV Amount]
    RETURN
        0.4 * _clv + 0.3 * _gm + 0.3 * _growth
```

### Churn Risk Score (early-warning proxy)

```DAX
Churn Risk Score =
    VAR sales_3m = CALCULATE ( [Net Sales Amount], DATESINPERIOD ( dim_date[Date], MAX(dim_date[Date]), -3, MONTH ) )
    VAR sales_prev = CALCULATE ( [Net Sales Amount], DATESINPERIOD ( dim_date[Date], MAX(dim_date[Date]) - 90, -3, MONTH ) )
    RETURN DIVIDE ( sales_prev - sales_3m, sales_prev )
```

---

## 5. Formatting
- Amounts: `€#,0.00`
- Percentages: `0.0 %`
- Scores: `0.00`

---

## 6. RLS

```DAX
dim_customer[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

---

## 7. QA Rules

| Check                       | Threshold |
|-----------------------------|-----------|
| RI customer/date            | ≥ 99.9 %  |
| GM % plausibility           | manual    |
| CLV logic consistency       | manual    |
| Churn score stability       | manual    |

