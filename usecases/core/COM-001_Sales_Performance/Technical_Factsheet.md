# COM-001 – Technical Factsheet

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Sales BI Lead
- **Data Product / Model ID:** `commercial_sales_performance`
- **Source Systems:** ERP (sales), DWH
- **Use Case Business Factsheet:** `usecases/core/COM-001_Sales_Performance/Business_Factsheet.md`

---

## 1. Model References
- **Data Contract (Domain):** `data_contracts/domains/commercial_sales.yaml`
- **Data Contract (Sources):** `data_contracts/sources/commercial.yaml` (if available)
- **Semantic Model Definition:** `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`

---

## 2. Data Contract Scope (YAML – COM-001)

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

  - name: security_user_org   # RLS
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

### Source Mapping (Physical Layer)
- fact_sales → `lh_commercial_sales.fact_sales`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`
- security_user_org → `lh_security.security_user_org`

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_sales  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 3.2 Relationships
- fact_sales[DateKey] → dim_date[DateKey] (1:* | single)
- fact_sales[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_sales[ProductKey] → dim_product[ProductKey] (1:* | single)

### 3.3 Hierarchies
- Org: Region → Country → Channel → OrgName
- Product: Category → Subcategory → ProductName
- Date: Year → Quarter → Month → Date

### 3.4 Sort-by Columns
- Month → MonthNumber
- ProductName → ProductCode
- OrgName → OrgCode

### 3.5 Modeling Rules
- No calculated columns; business logic in measures/ETL.
- Default summarization set; technical fields hidden.
- Display folders: 01_Sales, 02_Margin, 03_PVM, 04_Plan.

---

## 4. Measure Inventory

| Measure Name           | KPI ID / Supporting            | Purpose               | Display Folder | Format   | Type |
|------------------------|--------------------------------|-----------------------|----------------|----------|------|
| Net Sales Amount       | sales.net.amount               | Sales base            | 01_Sales       | €#,0.00  | KPI  |
| Net Sales Amount LY    | sales.net.amount.ly            | Sales LY              | 01_Sales       | €#,0.00  | Supporting |
| Revenue Growth %       | growth.sales.yoy.pct           | YoY growth            | 01_Sales       | 0.0 %    | KPI  |
| Plan Sales Amount      | sales.net.plan.amount          | Plan                  | 04_Plan        | €#,0.00  | Supporting |
| Sales vs Plan %        | growth.sales.vs_plan.pct       | Plan attainment       | 04_Plan        | 0.0 %    | KPI  |
| COGS Amount            | margin.cogs.amount             | Cost base             | 02_Margin      | €#,0.00  | Supporting |
| Gross Margin %         | margin.gm.pct                  | Margin quality        | 02_Margin      | 0.0 %    | KPI  |
| Quantity Qty           | sales.qty.total                | Volume                | 01_Sales       | #,0      | Supporting |
| Price Effect Amount    | sales.price_effect.amount      | PVM                   | 03_PVM         | €#,0.00  | KPI  |
| Volume Effect Amount   | sales.volume_effect.amount     | PVM                   | 03_PVM         | €#,0.00  | KPI  |
| Mix Effect Amount      | sales.mix_effect.amount        | PVM                   | 03_PVM         | €#,0.00  | KPI  |

---

## 5. Measures (DAX)

```DAX
/// sales.net.amount – Sales base
Net Sales Amount =
    SUM ( fact_sales[Net Sales Amount] )
```

```DAX
/// sales.net.amount.ly – Sales LY
Net Sales Amount LY =
    CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR ) )
```

```DAX
/// growth.sales.yoy.pct – YoY growth
Revenue Growth % =
    DIVIDE ( [Net Sales Amount] - [Net Sales Amount LY], [Net Sales Amount LY] )
```

```DAX
/// sales.net.plan.amount – Plan
Plan Sales Amount =
    SUM ( fact_sales[Plan Sales Amount] )
```

```DAX
/// growth.sales.vs_plan.pct – Plan attainment
Sales vs Plan % =
    DIVIDE ( [Net Sales Amount] - [Plan Sales Amount], [Plan Sales Amount] )
```

```DAX
/// margin.gm.pct – Margin quality
Gross Margin % =
    DIVIDE ( [Net Sales Amount] - [COGS Amount], [Net Sales Amount] )
```

```DAX
/// PVM effects (template-based)
Price Effect Amount = <per PEVM template>
Volume Effect Amount = <per PEVM template>
Mix Effect Amount = <per PEVM template>
```

> PVM implementation per `framework/templates/measure_templates/pevm_sales_delta.md` (price + volume + mix ≈ Δ Net Sales, tolerance ±1 %).

---

## 6. Defaults & Formatting
- Currency: `€#,0.00` | Percent: `0.0 %` | Qty: `#,0`
- Summarization: Amounts = Sum; Percent = None; Qty = Sum.
- Display folders: 01_Sales, 02_Margin, 03_PVM, 04_Plan.

---

## 7. Visual Requirements

| Visual Name         | Type      | X-Axis / Category   | Y-Axis / Value                          | Segment / Legend | Filters          |
|---------------------|-----------|---------------------|-----------------------------------------|------------------|------------------|
| Sales Trend vs Plan | Line      | dim_date[Month]     | [Net Sales Amount], Plan, LY            | Region/Channel   | Last 12–24M      |
| PVM Waterfall       | Waterfall | Drivers (Price, Volume, Mix) | Δ Net Sales vs Plan/LY                | n/a              | Period selector  |
| Ranking (Top/Bottom)| Bar       | Region/Channel/Product | [Net Sales Amount], [Sales vs Plan %], [GM %] | Region/Channel | Top/Bottom N     |
| Detail Matrix       | Matrix    | Region → Country → Customer / Category → Product | NS, Growth, Plan %, GM %, PVM | Channel/Region | Export enabled   |

---

## 8. RLS / OLS Rules

### 8.1 RLS Pattern
Region/Channel-based RLS via security table:
```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

### 8.2 OLS (optional)
- Hide cost fields (COGS, GM) for non-finance roles; show sales only.

---

## 9. Performance & Refresh
- Storage Mode: Import.
- Partitioning: monthly; history 24–36 months.
- No calculated columns; technical fields hidden; optional aggregations for large volumes.

---

## 10. QA & Validation Rules

| Check Name              | Object                      | Rule                                      | Threshold | Automated | Owner          |
|-------------------------|-----------------------------|-------------------------------------------|-----------|-----------|----------------|
| RI Check                | fact → dims                 | ≥ 99.9 % matched keys                     | 99.9 %    | Y         | Data Engineer  |
| Sales Reconciliation    | Net Sales Amount            | Matches source                            | ±0.5 %    | Y         | Controller     |
| Plan Reconciliation     | Plan Sales Amount           | Matches planning system                   | ±0.5 %    | Y         | Controller     |
| PVM Consistency         | Price+Volume+Mix            | ≈ Δ Net Sales within tolerance            | ±1.0 %    | Y         | BI Dev         |
| Margin Plausibility     | Gross Margin %              | In expected range; flag outliers          | rule-based| Y         | BI Dev         |
