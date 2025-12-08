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

## 1. Data Contract (YAML – COM-001 Scope)

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
      - {name: Brand, type: text}

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
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Plan Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### **Source Mapping (Physical Layer)**
- fact_sales → `lh_commercial_sales.fact_sales`  
- dim_date → `lh_shared.dim_date`  
- dim_org → `lh_shared.dim_org`  
- dim_product → `lh_shared.dim_product`  
- security_user_org → `lh_security.security_user_org`

---

## 2. Semantic Model Requirements

### **Model Name**
`commercial_sales_semantic`

### **Tables**
- fact_sales  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (hidden, RLS support)

### **Relationships**
- fact_sales[DateKey] → dim_date[DateKey] (1:* | single | to fact)
- fact_sales[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_sales[ProductKey] → dim_product[ProductKey] (1:* | single)

### **Hierarchies**
- Org: Region → Country → OrgName  
- Product: Category → Subcategory → ProductName  
- Date: Year → Quarter → Month → Date  

### **Sort-by Columns**
- Month → MonthNumber  
- ProductName → ProductCode  
- OrgName → OrgCode  

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name           | kpi_id                     | Type        | Folder               | Format     |
|------------------------|---------------------------|------------|----------------------|-----------|
| Net Sales Amount       | sales.net.amount          | KPI base   | 01_Sales             | €#,0.00   |
| Net Sales Amount LY    | sales.net.amount.ly       | Supporting | 01_Sales             | €#,0.00   |
| Revenue Growth %       | growth.sales.yoy.pct      | KPI        | 01_Sales             | 0.0 %     |
| Plan Sales Amount      | sales.net.plan.amount     | Supporting | 01_Sales             | €#,0.00   |
| Sales vs Plan %        | growth.sales.vs_plan.pct  | KPI        | 01_Sales             | 0.0 %     |
| COGS Amount            | margin.cogs.amount        | Supporting | 02_Margin            | €#,0.00   |
| Gross Margin %         | margin.gm.pct             | KPI        | 02_Margin            | 0.0 %     |
| Quantity Qty           | sales.qty.total           | Supporting | 01_Sales             | #,0       |
| Price Effect Amount    | sales.price_effect.amount | KPI        | 03_Price_Volume_Mix  | €#,0.00   |
| Volume Effect Amount   | sales.volume_effect.amount| KPI        | 03_Price_Volume_Mix  | €#,0.00   |
| Mix Effect Amount      | sales.mix_effect.amount   | KPI        | 03_Price_Volume_Mix  | €#,0.00   |

### **PEVM Implementation**
Die Price/Volume/Mix Measures werden gemäß Standard-Template gebaut:

```
framework/templates/measure_templates/pevm_sales_delta.md
```

→ QA: *Price + Volume + Mix ≈ Δ Net Sales (±1 %).*

---

## 4. Measures (DAX)

```DAX
Net Sales Amount =
    SUM ( fact_sales[Net Sales Amount] )
```

```DAX
Net Sales Amount LY =
    CALCULATE (
        [Net Sales Amount],
        DATEADD ( dim_date[Date], -1, YEAR )
    )
```

```DAX
Revenue Growth % =
    DIVIDE (
        [Net Sales Amount] - [Net Sales Amount LY],
        [Net Sales Amount LY]
    )
```

```DAX
Plan Sales Amount =
    SUM ( fact_sales[Plan Sales Amount] )
```

```DAX
Sales vs Plan % =
    DIVIDE (
        [Net Sales Amount] - [Plan Sales Amount],
        [Plan Sales Amount]
    )
```

```DAX
COGS Amount =
    SUM ( fact_sales[COGS Amount] )
```

```DAX
Gross Margin % =
    DIVIDE ( [Net Sales Amount] - [COGS Amount], [Net Sales Amount] )
```

*Hinweis:*  
PEVM Measures siehe Template.

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Folder               |
|---------------|----------|---------------|----------------------|
| Amounts       | €#,0.00  | Sum           | 01_Sales / 02_Margin |
| Percentages   | 0.0 %    | None          | KPI folders          |
| Quantities    | #,0      | Sum           | 01_Sales             |

---

## 6. Visual Requirements

### **KPI Cards**
- Net Sales Amount  
- Revenue Growth %  
- Sales vs Plan %  
- Gross Margin %  

### **Trend**
- Line Chart (12–24M)
- Axis: dim_date[Month]
- Values: Sales + Growth

### **Contribution**
- Price/Volume/Mix Waterfall

### **Ranking**
- Horizontal Bar (Region / Channel / Product)

### **Detail**
- Matrix mit Region → Country → Org  
- Category → Subcategory → Product  
- Export enabled

---

## 7. RLS / OLS

### **Simple Demo**
```DAX
dim_org[Region] = "Europe"
```

### **Enterprise Pattern (Recommended)**  
Uses `security_user_org` table.

```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

### **Optional OLS**
- Hide COGS Amount + GM% for non-Finance roles.

---

## 8. Performance & Refresh

- Storage Mode: Import (alternativ: Direct Lake)  
- Incremental Refresh:
  - monthly partitions via `DateKey`
  - ca. 36 Monate History  
- Page Load Target:
  - KPI Page < 2s  
  - Details < 3s  
- Technical fields hidden  
- No calculated columns  
- Aggregations optional für sehr große Datasets  

---

## 9. QA & Validation

| Check Type              | Object                      | Rule                                      | Tolerance |
|-------------------------|-----------------------------|-------------------------------------------|-----------|
| Referential Integrity   | fact_sales → dims           | ≥ 99.9 % match                             | 0.1 %     |
| Sales Reconciliation    | Net Sales Amount            | match source                               | ±0.5 %    |
| Plan Reconciliation     | Plan Sales Amount           | match planning system                       | ±0.5 %    |
| Variance Decomposition  | Price+Volume+Mix            | ≈ Δ Sales                                   | ±1.0 %    |
| Margin Plausibility     | Gross Margin %              | in expected range                           | manual    |
