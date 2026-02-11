---
id: COM-004
factsheet_type: technical
---

# COM-004 - Promotion Effectiveness  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Commercial
- **Technical Owner:** Trade Marketing / Commercial BI Lead
- **Model ID:** commercial_promo_effectiveness
- **Source Systems:** ERP (sales), Promo systems, DWH
- **Business Factsheet:** ./Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** core/core/core/data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** core/core/core/data_contracts/sources/commercial.yaml
- **Semantic Model Definition:** core/core/core/semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** core/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** core/core/core/semantic_models/domains/Commercial/Measure_Dictionary_Commercial.md
- **Action Codes:** core/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: sales.promo.roi.pct
    kpi_name: Promotion ROI %
    measure_name: Promotion ROI %
    format: "0.0%"
    folder: 03_Promo

  - kpi_id: sales.promo.incremental.amount
    kpi_name: Incremental Sales Amount
    measure_name: Incremental Sales Amount
    format: "EUR #,0"
    folder: 03_Promo

  - kpi_id: margin.promo.gm.pct
    kpi_name: Promo Gross Margin %
    measure_name: Promo Gross Margin %
    format: "0.0%"
    folder: 03_Promo

  - kpi_id: sales.price.realization_pct
    kpi_name: Price Realization %
    measure_name: Price Realization %
    format: "0.0%"
    folder: 03_Pricing

  - kpi_id: sales.promo.cannibalization.pct
    kpi_name: Cannibalization %
    measure_name: Cannibalization %
    format: "0.0%"
    folder: 03_Promo
```

---

## 3. Data Contract Scope (Subset YAML)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Quarter, type: text}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

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

  - name: dim_promo
    columns:
      - {name: PromoKey, type: int, role: key}
      - {name: Promotion, type: text}
      - {name: PromoType, type: text, nullable: true}
      - {name: Mechanic, type: text, nullable: true}
      - {name: StartDateKey, type: int, ref: dim_date, nullable: true}
      - {name: EndDateKey, type: int, ref: dim_date, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_sales
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: CustomerKey, type: int, ref: dim_customer, nullable: true}
      - {name: PromoKey, type: int, ref: dim_promo, nullable: true}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity, type: decimal, agg: sum}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}

  - name: fact_promo
    columns:
      - {name: PromoKey, type: int, ref: dim_promo}
      - {name: Promo Cost, type: currency, agg: sum}
      - {name: Funding Amount, type: currency, agg: sum, nullable: true}
      - {name: Baseline Sales Amount, type: currency, agg: sum, nullable: true}
      - {name: Baseline Quantity, type: decimal, agg: sum, nullable: true}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- dim_date, dim_org, dim_product, dim_promo, security_user_org, dim_customer (nullable on fact)
- fact_sales (with promo linkage, price components), fact_promo (cost, baseline)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> fact_sales on DateKey; dim_date -> dim_promo (start/end optional)
- dim_org (1) -> fact_sales on OrgKey
- dim_product (1) -> fact_sales on ProductKey
- dim_promo (1) -> fact_sales on PromoKey; fact_promo on PromoKey
- dim_customer (optional) (1) -> fact_sales on CustomerKey (nullable)
- security_user_org filters dim_org -> cascades to facts
- Single direction; avoid ambiguous paths; no bi-directional except RLS bridge if required.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month
- Org: Region -> Country -> Channel -> OrgName
- Product: Category -> Subcategory -> ProductName
- Promo: Type -> Mechanic (optional)

### 4.4 Sort-by Columns

- Month -> MonthNumber
- ProductName -> ProductCode
- Promotion -> PromoKey

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.
- Default summarization set; technical columns hidden; display folders per dictionary.
- Surrogate keys mandatory; avoid M2M; baseline fields used for incremental calcs.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Promotion ROI % | sales.promo.roi.pct | Promo profitability | 03_Promo | 0.0% | KPI |
| Incremental Sales Amount | sales.promo.incremental.amount | Uplift sizing | 03_Promo | EUR #,0 | KPI |
| Promo Gross Margin % | margin.promo.gm.pct | Profit quality | 03_Promo | 0.0% | KPI |
| Price Realization % | sales.price.realization_pct | Discount discipline | 03_Pricing | 0.0% | KPI |
| Cannibalization % | sales.promo.cannibalization.pct | Net effect on portfolio | 03_Promo | 0.0% | KPI |
| Net Sales Amount | Supporting | Revenue base | 01_Revenue | EUR #,0 | Supporting |
| Cost of Goods Sold Amount | Supporting | Cost base | 02_Margin | EUR #,0 | Supporting |
| Net Price Amount | Supporting | Price input | 03_Pricing | EUR #,0 | Supporting |
| List Price Amount | Supporting | Price input | 03_Pricing | EUR #,0 | Supporting |
| Promo Cost | Supporting | Promo spend | 03_Promo | EUR #,0 | Supporting |
| Baseline Sales Amount | Supporting | Baseline reference | 03_Promo | EUR #,0 | Supporting |
| Baseline Quantity | Supporting | Baseline reference | 03_Promo | #,0 | Supporting |
| Funding Amount | Supporting | Trade funding | 03_Promo | EUR #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// sales.promo.roi.pct - Promo profitability
Promotion ROI % =
DIVIDE ( [Incremental Gross Margin Amount], [Promo Cost] )

/// sales.promo.incremental.amount - Uplift sizing
Incremental Sales Amount =
[Net Sales Amount] - [Baseline Sales Amount]

/// margin.promo.gm.pct - Profit quality during promo
Promo Gross Margin % =
DIVIDE ( [Net Sales Amount] - [Cost of Goods Sold Amount], [Net Sales Amount] )

/// sales.price.realization_pct - Discount discipline
Price Realization % =
DIVIDE ( [Net Price Amount], [List Price Amount] )

/// sales.promo.cannibalization.pct - Net effect on portfolio
Cannibalization % =
DIVIDE ( [Cannibalized Sales Amount], [Incremental Sales Amount] )
```

---

## 6. RLS / OLS Requirements

### 6.1 Security Table Pattern

```yaml
security_table:
  name: security_user_org
  keys:
    - UserPrincipalName
    - Region
    - Country
    - OrgKey
    - Channel
  mapping_target: dim_org[OrgKey]
  fallback_behavior: deny_all_if_no_match
```

### 6.2 RLS Rule (Fabric / Power BI)

```DAX
dim_org[OrgKey] IN
    CALCULATETABLE (
        VALUES ( security_user_org[OrgKey] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
    )
```

### 6.3 OLS (optional)

- None required; monetary columns visible to authorised users.

---

## 7. Technical Assumptions

- Baseline model available for incremental sales/quantity; cannibalization logic defined against related items.
- Promo cost/funding captured in fact_promo; price components available in fact_sales.
- Cannibalized Sales Amount measure depends on related SKU mapping (not included here; requires data prep).
- Currency EUR; returns/credit notes handled upstream.

---

## 8. Deployment Requirements

- Mode: DirectLake or Import; prefer DirectLake if available.
- Incremental refresh: by Month for last 12-24 months.
- Aggregations optional; avoid grain distortion.
- Workspace/naming per governance; display folders per dictionary.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product/Promo keys non-null in fact_sales/fact_promo | 100% | Y | Data Engineering |
| ROI Calculation | Incremental GM and Promo Cost populated | 100% where ROI reported | Y | Controlling |
| Baseline Quality | Baseline Sales/Qty present for promoted items | 100% where promos exist | Y | BI |
| Price Realization | Net/List price populated for promo lines | 100% | Y | Pricing |
| Cannibalization | Inputs for cannibalization logic available | As defined by model | Y | BI |
| RLS Coverage | Users only see authorised regions/channels | 0 leaks | Y | Security |

---

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md



