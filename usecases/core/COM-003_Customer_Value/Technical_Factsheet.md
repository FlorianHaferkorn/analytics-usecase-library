# COM-003 – Technical Factsheet

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Sales Ops / BI Lead
- **Data Product / Model ID:** `commercial_customer_value`
- **Source Systems:** ERP/CRM, DWH
- **Use Case Business Factsheet:** `usecases/core/COM-003_Customer_Value/Business_Factsheet.md`

---

## 1. Model References
- **Data Contract (Domain):** `data_contracts/domains/commercial_sales.yaml`
- **Data Contract (Sources):** `data_contracts/sources/commercial.yaml` (if available)
- **Semantic Model Definition:** `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`

---

## 2. Data Contract Scope (YAML – COM-003)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_customer
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: CustomerCode, type: text}
      - {name: CustomerName, type: text}
      - {name: Segment, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Channel, type: text}
      - {name: TenureStartDate, type: date}
      - {name: ChurnFlag, type: boolean}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: UoM, type: text}

  - name: security_user_org   # RLS (segment/region-based if needed)
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int}  # optional link if sales org used

fact:
  - name: fact_customer_margin
    grain: customer_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Discount Amount, type: currency, agg: sum}
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: Gross Margin Amount, type: currency, agg: sum}
      - {name: CLV Amount, type: currency, agg: sum}
      - {name: Churn Flag, type: boolean}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_customer_margin → `lh_commercial_sales.fact_customer_margin`
- dim_date → `lh_shared.dim_date`
- dim_customer → `lh_shared.dim_customer`
- dim_product → `lh_shared.dim_product`
- security_user_org → `lh_security.security_user_org`

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_customer_margin  
- dim_date  
- dim_customer  
- dim_product  
- security_user_org (optional RLS)

### 3.2 Relationships
- fact_customer_margin[DateKey] → dim_date[DateKey] (1:* | single)
- fact_customer_margin[CustomerKey] → dim_customer[CustomerKey] (1:* | single)
- fact_customer_margin[ProductKey] → dim_product[ProductKey] (1:* | single)

### 3.3 Hierarchies
- Customer: Region → Country → Channel → Segment → Customer
- Product: Category → Subcategory → ProductName
- Date: Year → Quarter → Month

### 3.4 Sort-by Columns
- Month → MonthNumber
- ProductName → ProductCode
- CustomerName → CustomerCode

### 3.5 Modeling Rules
- No calculated columns; logic in measures/ETL.
- Default summarization set; hide technical fields.
- Display folders: 01_Customer, 02_Margin, 03_Retention.

---

## 4. Measure Inventory

| Measure Name              | KPI ID / Supporting        | Purpose                          | Display Folder | Format | Type |
|---------------------------|----------------------------|----------------------------------|----------------|--------|------|
| Customer Lifetime Value   | crm.clv.amount             | Lifecycle profitability          | 01_Customer    | €#,0.00| KPI  |
| Gross Margin per Customer | margin.customer.amount     | Margin quality per customer      | 01_Customer    | €#,0.00| KPI  |
| Retention Rate %          | crm.retention.pct          | Loyalty/stickiness               | 03_Retention   | 0.0 %  | KPI  |
| Churn Rate %              | crm.churn.pct              | Loss indicator                   | 03_Retention   | 0.0 %  | KPI  |
| Revenue per Customer      | sales.customer.revenue.amount | Monetization level            | 01_Customer    | €#,0.00| Supporting |
| Churn Flag                | Supporting                 | Flag for churned customers       | 03_Retention   | Bool   | Supporting |
| GM Amount                 | margin.gm.amount           | Margin value                     | 02_Margin      | €#,0.00| Supporting |

---

## 5. Measures (DAX)

```DAX
/// crm.clv.amount – Lifecycle profitability
Customer Lifetime Value =
    SUM ( fact_customer_margin[CLV Amount] )
```

```DAX
/// margin.customer.amount – Margin per customer
Gross Margin per Customer =
    DIVIDE ( SUM ( fact_customer_margin[Gross Margin Amount] ),
             DISTINCTCOUNT ( dim_customer[CustomerKey] ) )
```

```DAX
/// crm.retention.pct – Loyalty/stickiness
Retention Rate % =
    1 - [Churn Rate %]
```

```DAX
/// crm.churn.pct – Loss indicator
Churn Rate % =
    DIVIDE (
        CALCULATE ( DISTINCTCOUNT ( fact_customer_margin[CustomerKey] ),
                    fact_customer_margin[Churn Flag] = TRUE() ),
        DISTINCTCOUNT ( fact_customer_margin[CustomerKey] )
    )
```

```DAX
/// sales.customer.revenue.amount – Monetization level
Revenue per Customer =
    DIVIDE ( SUM ( fact_customer_margin[Net Sales Amount] ),
             DISTINCTCOUNT ( fact_customer_margin[CustomerKey] ) )
```

---

## 6. Defaults & Formatting
- Currency: `€#,0.00` | Percent: `0.0 %` | Qty: `#,0` | Flags: Boolean
- Summarization: Amounts = Sum; Percent = None; Flags = None.
- Display folders: 01_Customer, 02_Margin, 03_Retention.

---

## 7. Visual Requirements

| Visual Name           | Type      | X-Axis / Category     | Y-Axis / Value                         | Segment / Legend | Filters / Defaults |
|-----------------------|-----------|-----------------------|----------------------------------------|------------------|--------------------|
| CLV & Retention Trend | Line      | dim_date[Month]       | [CLV], [Retention %], [Churn %]        | Segment/Region   | Last 12–24M        |
| Segment Ranking       | Bar       | dim_customer[Segment] | [CLV], [GM/Customer], [Retention %]    | Region/Channel   | Top/Bottom N       |
| CLV Driver Bridge     | Waterfall | Drivers               | Δ CLV vs Plan/LY                       | n/a              | Period selector    |
| Detail Matrix         | Matrix    | Segment → Customer    | CLV, GM/Customer, Churn flag, basket mix| Segment/Region  | Export enabled     |

---

## 8. RLS / OLS Rules

### 8.1 RLS Pattern
Region/Channel-based RLS via security table (if required):
```DAX
dim_customer[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

### 8.2 OLS (optional)
- Hide customer names for external roles; show segment/region only.

---

## 9. Performance & Refresh
- Storage Mode: Import.
- Partitioning: monthly; history 24–36 months.
- No calculated columns; technical fields hidden; optional aggregations for long history.

---

## 10. QA & Validation Rules

| Check Name              | Object                        | Rule                                     | Threshold | Automated | Owner         |
|-------------------------|-------------------------------|------------------------------------------|-----------|-----------|---------------|
| RI Check                | fact → dims                   | ≥ 99.9 % matched keys                    | 99.9 %    | Y         | Data Engineer |
| CLV Reconciliation      | CLV Amount                    | Matches source calculation               | ±0.5 %    | Y         | Controller    |
| Retention/Churn Capture | Churn flags                   | Coverage of churn flags ≥ 95 %           | 95 %      | Y         | BI Dev        |
| GM Reconciliation       | Gross Margin Amount           | Matches finance margin reporting         | ±0.5 %    | Y         | Controller    |
