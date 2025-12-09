# COM-002 – Technical Factsheet

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Pricing / BI Lead
- **Data Product / Model ID:** `commercial_margin_performance`
- **Source Systems:** ERP (sales, pricing), DWH
- **Use Case Business Factsheet:** `usecases/core/COM-002_Margin_Price_Performance/Business_Factsheet.md`

---

## 1. Model References
- **Data Contract (Domain):** `data_contracts/domains/commercial_sales.yaml`
- **Data Contract (Sources):** `data_contracts/sources/commercial.yaml` (if available)
- **Semantic Model Definition:** `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`

---

## 2. Data Contract Scope (YAML – COM-002)

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
      - {name: UoM, type: text}

  - name: security_user_org   # RLS
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

fact:
  - name: fact_margin
    grain: invoice_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Discount Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Plan GM Amount, type: currency, agg: sum}
      - {name: Plan GM %, type: number, agg: avg}
      - {name: GM Target %, type: number, agg: avg}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_margin → `lh_commercial_sales.fact_margin`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`
- security_user_org → `lh_security.security_user_org`

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_margin  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 3.2 Relationships
- fact_margin[DateKey] → dim_date[DateKey] (1:* | single)
- fact_margin[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_margin[ProductKey] → dim_product[ProductKey] (1:* | single)

### 3.3 Hierarchies
- Org: Region → Country → Channel → OrgName
- Product: Category → Subcategory → Brand → ProductName
- Date: Year → Quarter → Month → Date

### 3.4 Sort-by Columns
- Month → MonthNumber
- OrgName → OrgCode
- ProductName → ProductCode

### 3.5 Modeling Rules
- No calculated columns; keep logic in measures/ETL.
- Default summarization set; technical fields hidden.
- Display folders: 01_Margin, 02_Price, 03_Cost, 04_Plan.

---

## 4. Measure Inventory

| Measure Name          | KPI ID / Supporting          | Purpose                  | Display Folder | Format  | Type |
|-----------------------|------------------------------|--------------------------|----------------|---------|------|
| Gross Margin %        | margin.gm.pct                | Margin quality           | 01_Margin      | 0.0 %   | KPI  |
| Gross Margin Amount   | margin.gm.amount             | Margin value             | 01_Margin      | €#,0.00 | KPI  |
| Price Realization %   | sales.price.realization_pct  | Discount discipline      | 02_Price       | 0.0 %   | KPI  |
| Discount %            | sales.discount.pct           | Discount rate            | 02_Price       | 0.0 %   | Supporting |
| Mix Effect Amount     | sales.mix_effect.amount      | Portfolio quality        | 01_Margin      | €#,0.00 | KPI  |
| COGS per Unit         | cost.cogs_per_unit.amount    | Cost efficiency          | 03_Cost        | €#,0.000| KPI  |
| GM vs Plan %          | margin.gm.vs_plan.pct        | Target attainment        | 04_Plan        | 0.0 %   | KPI  |

---

## 5. Measures (DAX)

```DAX
/// margin.gm.amount – Margin value
Gross Margin Amount =
    [Net Sales Amount] - [COGS Amount]
```

```DAX
/// margin.gm.pct – Margin quality
Gross Margin % =
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )
```

```DAX
/// sales.price.realization_pct – Discount discipline
Price Realization % =
    DIVIDE ( [Net Price Amount], [List Price Amount] )
```

```DAX
/// sales.discount.pct – Discount rate
Discount % =
    1 - [Price Realization %]
```

```DAX
/// cost.cogs_per_unit.amount – Unit cost
COGS per Unit =
    DIVIDE ( [COGS Amount], [Quantity Qty] )
```

```DAX
/// margin.gm.vs_plan.pct – Gap to plan
GM vs Plan % =
    DIVIDE ( [Gross Margin Amount] - SUM ( fact_margin[Plan GM Amount] ),
             SUM ( fact_margin[Plan GM Amount] ) )
```

```DAX
/// sales.mix_effect.amount – Mix impact (via PVM template)
Mix Effect Amount =
    CALCULATE ( [Gross Margin Amount] ) - [Price Effect Amount] - [Volume Effect Amount]
```

> Price/Volume/Mix implementation per `framework/templates/measure_templates/pevm_sales_delta.md`.

---

## 6. Defaults & Formatting
- Currency: `€#,0.00` | Percent: `0.0 %` | Qty: `#,0` | Unit Cost: `€#,0.000`
- Summarization: Amounts = Sum; Percent = None; Unit Cost = None; Qty = Sum.
- Display folders: 01_Margin, 02_Price, 03_Cost, 04_Plan.

---

## 7. Visual Requirements

| Visual Name          | Type      | X-Axis / Category        | Y-Axis / Value                              | Segment / Legend | Filters / Defaults |
|----------------------|-----------|--------------------------|---------------------------------------------|------------------|--------------------|
| GM Trend vs Plan     | Line      | dim_date[Month]          | [Gross Margin %], [GM vs Plan %], Plan      | Region/Channel   | Last 12–24M        |
| GM by Product/Ch     | Bar       | dim_product[Category] / dim_org[Channel] | [Gross Margin %], [Price Realization %] | Region           | Top/Bottom N       |
| Margin Variance Bridge | Waterfall | Drivers (Price, Volume, Mix, Cost) | Δ GM vs Plan/LY                         | n/a              | Period selector    |
| Detail Matrix        | Matrix    | Region → Channel → Product | GM %, Price Realization %, COGS/Unit, Mix Effect | Region/Channel | Export enabled    |

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
- Hide cost fields (COGS, GM) for non-finance roles; keep price/volume visible.

---

## 9. Performance & Refresh
- Storage Mode: Import.
- Partitioning: monthly; history 24–36 months.
- No calculated columns; technical fields hidden; optional aggregations for large invoice volumes.

---

## 10. QA & Validation Rules

| Check Name            | Object               | Rule                                    | Threshold | Automated | Owner          |
|-----------------------|----------------------|-----------------------------------------|-----------|-----------|----------------|
| RI Check              | fact_margin → dims   | ≥ 99.9 % matched keys                   | 99.9 %    | Y         | Data Engineer  |
| Margin Reconciliation | Gross Margin Amount  | vs source within tolerance              | ±0.5 %    | Y         | Controller     |
| Plan Reconciliation   | Plan GM vs planning  | Matches planning system                 | ±0.5 %    | Y         | Controller     |
| PVM Consistency       | Price+Volume+Mix     | ≈ Δ GM within rounding                  | ±1.0 %    | Y         | BI Dev         |
| Price Realization     | Net/List consistency | Net ≤ List unless surcharge; flag breaks | rule-based| Y         | BI Dev         |
