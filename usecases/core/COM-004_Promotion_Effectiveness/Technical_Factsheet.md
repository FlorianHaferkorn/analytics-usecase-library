# COM-004 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: COM-004)

---

## 1. Data Contract (YAML – COM-004 Scope)

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

---

## 2. Semantic Model Requirements

### Model Name
`promotion_effectiveness`

### Tables
- fact_promo_performance  
- dim_date  
- dim_org  
- dim_product  
- dim_promo  

### Relationships
- fact_promo_performance[DateKey] → dim_date[DateKey] (1:* | single)
- fact_promo_performance[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_promo_performance[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_promo_performance[PromoKey] → dim_promo[PromoKey] (1:* | single)

### Hierarchies
- Org: Region → Country → Channel
- Product: Category → Subcategory → SKU
- Date: Year → Quarter → Month
- Promo: PromoType → PromoName

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name            | kpi_id                       | Type        | Folder         | Format   |
|-------------------------|------------------------------|-------------|----------------|----------|
| Promo ROI %             | sales.promo.roi.pct          | KPI         | 01_Promo       | 0.0 %    |
| Incremental Sales %     | sales.promo.incremental.pct  | KPI         | 01_Promo       | 0.0 %    |
| Gross Margin %          | margin.promo.gm.pct          | KPI         | 02_Margin      | 0.0 %    |
| Price Realization %     | sales.price.realization_pct  | Supporting  | 03_Price       | 0.0 %    |
| Cannibalization %       | sales.promo.cannibalization.pct | KPI      | 04_Risk        | 0.0 %    |

---

## 4. Measures (DAX)

```DAX
Promo Qty =
    SUM ( fact_promo_performance[Promo Qty] )
```

```DAX
Baseline Qty =
    SUM ( fact_promo_performance[Baseline Qty] )
```

```DAX
Promo Uplift Qty =
    [Promo Qty] - [Baseline Qty]
```

```DAX
Promo Sales Amount =
    SUM ( fact_promo_performance[Promo Sales Amount] )
```

```DAX
Baseline Sales Amount =
    SUM ( fact_promo_performance[Baseline Sales Amount] )
```

```DAX
Incremental Sales Amount =
    [Promo Sales Amount] - [Baseline Sales Amount]
```

```DAX
Incremental Sales % =
    DIVIDE ( [Incremental Sales Amount], [Baseline Sales Amount] )
```

```DAX
Promo GM % =
    DIVIDE (
        [Promo Sales Amount] - SUM ( fact_promo_performance[COGS Amount] ),
        [Promo Sales Amount]
    )
```

```DAX
Promo ROI % =
    DIVIDE (
        [Incremental Sales Amount] - SUM ( fact_promo_performance[Promo Spend Amount] ),
        SUM ( fact_promo_performance[Promo Spend Amount] )
    )
```

```DAX
Cannibalization % =
    DIVIDE ( SUM ( fact_promo_performance[Cannibalization Amount] ),
             [Incremental Sales Amount] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder |
|---------------|----------|---------------|----------------|
| Amounts       | €#,0.00  | Sum           | Promo/Margin   |
| Percentages   | 0.0 %    | None          | KPI folders    |
| Quantities    | #,0      | Sum           | Promo          |

---

## 6. RLS / OLS

- Region/Country/Channel-based RLS via dim_org.  
- Optional OLS to hide promo spend for external parties; expose uplift KPIs only.

Example RLS:
```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

---

## 7. Performance & Refresh

- Storage: Import; incremental by month (12–24 months).  
- Pre-aggregate promotions weekly if daily is too granular.  
- No calculated columns; hide technical fields.

---

## 8. QA & Validation

| Check Type              | Object                       | Rule                                    | Tolerance |
|-------------------------|------------------------------|-----------------------------------------|-----------|
| Referential Integrity   | fact → dims                  | ≥ 99.9 % matched keys                   | 0.1 %     |
| ROI Calculation         | GM incremental vs spend      | ROI formula consistent                  | ±0.5 pp   |
| Baseline Accuracy       | Baseline Sales/Qty           | Matches agreed baseline method          | manual    |
| Cannibalization Capture | Cannibalization Amount       | Captured for affected SKUs              | coverage  |
