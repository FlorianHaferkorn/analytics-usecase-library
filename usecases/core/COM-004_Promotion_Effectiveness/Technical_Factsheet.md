# COM-004 – Technical Factsheet

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Trade Marketing / BI Lead
- **Data Product / Model ID:** `promotion_effectiveness`
- **Source Systems:** ERP (sales), Promo Mgmt, DWH
- **Use Case Business Factsheet:** `usecases/core/COM-004_Promotion_Effectiveness/Business_Factsheet.md`

---

## 1. Model References
- **Data Contract (Domain):** `data_contracts/domains/commercial_sales.yaml`
- **Data Contract (Sources):** `data_contracts/sources/commercial.yaml` (if available)
- **Semantic Model Definition:** `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`

---

## 2. Data Contract Scope (YAML – COM-004)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Channel, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: SKU, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: Brand, type: text}

  - name: dim_promo
    columns:
      - {name: PromoKey, type: int, role: key}
      - {name: PromoCode, type: text}
      - {name: PromoName, type: text}
      - {name: PromoType, type: text}
      - {name: StartDate, type: date}
      - {name: EndDate, type: date}
      - {name: Mechanic, type: text}
      - {name: Retailer, type: text}

  - name: security_user_org   # RLS
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

fact:
  - name: fact_promo_performance
    grain: promo_sku_channel_period
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: PromoKey, type: int, ref: dim_promo}
      - {name: Baseline Sales Amount, type: currency, agg: sum}
      - {name: Baseline Qty, type: number, agg: sum}
      - {name: Promo Sales Amount, type: currency, agg: sum}
      - {name: Promo Qty, type: number, agg: sum}
      - {name: Promo Spend Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Cannibalization Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_promo_performance → `lh_commercial_sales.fact_promo_performance`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`
- dim_promo → `lh_commercial_sales.dim_promo`
- security_user_org → `lh_security.security_user_org`

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_promo_performance  
- dim_date  
- dim_org  
- dim_product  
- dim_promo  
- security_user_org (RLS)

### 3.2 Relationships
- fact_promo_performance[DateKey] → dim_date[DateKey] (1:* | single)
- fact_promo_performance[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_promo_performance[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_promo_performance[PromoKey] → dim_promo[PromoKey] (1:* | single)

### 3.3 Hierarchies
- Org: Region → Country → Channel
- Product: Category → Subcategory → SKU
- Date: Year → Quarter → Month
- Promo: PromoType → PromoName

### 3.4 Sort-by Columns
- Month → MonthNumber
- ProductName → ProductCode
- PromoName → PromoCode

### 3.5 Modeling Rules
- No calculated columns; use measures/ETL.
- Default summarization set; technical fields hidden.
- Display folders: 01_Promo, 02_Margin, 03_Price, 04_Risk.

---

## 4. Measure Inventory

| Measure Name            | KPI ID / Supporting           | Purpose                      | Display Folder | Format   | Type |
|-------------------------|-------------------------------|------------------------------|----------------|----------|------|
| Promo ROI %             | sales.promo.roi.pct           | Promo profitability          | 01_Promo       | 0.0 %    | KPI  |
| Incremental Sales %     | sales.promo.incremental.pct   | Demand lift                  | 01_Promo       | 0.0 %    | KPI  |
| Gross Margin %          | margin.promo.gm.pct           | Margin quality during promo  | 02_Margin      | 0.0 %    | KPI  |
| Price Realization %     | sales.price.realization_pct   | Discount discipline          | 03_Price       | 0.0 %    | Supporting |
| Cannibalization %       | sales.promo.cannibalization.pct | Impact on related items    | 04_Risk        | 0.0 %    | KPI  |
| Incremental Sales Amount| Supporting                    | Value of uplift              | 01_Promo       | €#,0.00  | Supporting |
| Promo Uplift Qty        | Supporting                    | Volume uplift                | 01_Promo       | #,0      | Supporting |

---

## 5. Measures (DAX)

```DAX
/// sales.promo.incremental.pct – Demand lift
Incremental Sales Amount =
    [Promo Sales Amount] - [Baseline Sales Amount]

Incremental Sales % =
    DIVIDE ( [Incremental Sales Amount], [Baseline Sales Amount] )
```

```DAX
/// margin.promo.gm.pct – Margin quality during promo
Promo GM % =
    DIVIDE (
        [Promo Sales Amount] - SUM ( fact_promo_performance[COGS Amount] ),
        [Promo Sales Amount]
    )
```

```DAX
/// sales.promo.roi.pct – Promo profitability
Promo ROI % =
    DIVIDE (
        [Incremental Sales Amount] - SUM ( fact_promo_performance[Promo Spend Amount] ),
        SUM ( fact_promo_performance[Promo Spend Amount] )
    )
```

```DAX
/// sales.promo.cannibalization.pct – Cannibalization
Cannibalization % =
    DIVIDE ( SUM ( fact_promo_performance[Cannibalization Amount] ),
             [Incremental Sales Amount] )
```

> Baseline method (pre/post or modeled) must be consistent across Promos.

---

## 6. Defaults & Formatting
- Currency: `€#,0.00` | Percent: `0.0 %` | Qty: `#,0`
- Summarization: Amounts = Sum; Percent = None; Qty = Sum.
- Display folders: 01_Promo, 02_Margin, 03_Price, 04_Risk.

---

## 7. Visual Requirements

| Visual Name          | Type      | X-Axis / Category | Y-Axis / Value                           | Segment / Legend | Filters / Defaults |
|----------------------|-----------|-------------------|------------------------------------------|------------------|--------------------|
| Promo ROI & GM Trend | Line      | dim_date[Month]   | [Promo ROI %], [Promo GM %], [Uplift %]  | Channel/Region   | Last 12–24M        |
| ROI by Promo/Ch/Prod | Bar       | Promo / Channel / Category | [Promo ROI %], [Incremental Sales %]    | Region           | Top/Bottom N       |
| Promo Variance Bridge| Waterfall | Drivers (Price, Volume, Mix, Spend)  | Δ Promo GM vs Baseline                    | n/a              | Period selector    |
| Detail Matrix        | Matrix    | Promo → Product/Channel | ROI %, Uplift %, GM %, Cannibalization % | Channel/Region   | Export enabled     |

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
- Hide spend or GM for external roles; show uplift metrics only.

---

## 9. Performance & Refresh
- Storage Mode: Import.
- Partitioning: monthly; history 12–24 months.
- No calculated columns; technical fields hidden; consider weekly aggregation for high volume.

---

## 10. QA & Validation Rules

| Check Name              | Object                       | Rule                                    | Threshold | Automated | Owner          |
|-------------------------|------------------------------|-----------------------------------------|-----------|-----------|----------------|
| RI Check                | fact → dims                  | ≥ 99.9 % matched keys                   | 99.9 %    | Y         | Data Engineer  |
| ROI Calculation         | ROI vs source                | ROI formula consistent                  | ±0.5 pp   | Y         | BI Dev         |
| Baseline Accuracy       | Baseline Sales/Qty           | Matches agreed baseline method          | manual    | N/Y*      | BI Dev         |
| Cannibalization Capture | Cannibalization Amount       | Captured for affected SKUs              | coverage  | Y         | BI Dev         |
| Price Realization Check | Net/List consistency         | Net ≤ List unless surcharge             | rule-based| Y         | BI Dev         |
