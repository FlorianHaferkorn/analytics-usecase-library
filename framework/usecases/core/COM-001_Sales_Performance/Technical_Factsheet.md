---
id: COM-001
factsheet_type: technical
---

# COM-001 - Sales Performance vs Plan & LY  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Commercial
- **Technical Owner:** Sales BI Lead
- **Model ID:** commercial_sales_performance
- **Source Systems:** ERP (sales), DWH
- **Business Factsheet:** ./Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** framework/framework/framework/data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** framework/framework/framework/data_contracts/sources/commercial.yaml
- **Semantic Model Definition:** framework/framework/framework/semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** framework/framework/framework/semantic_models/domains/Commercial/Measure_Dictionary_Commercial.md
- **Action Codes:** framework/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: sales.net_sales.amount
    kpi_name: Net Sales Amount
    measure_name: Net Sales Amount
    format: "EUR #,0"
    folder: 01_Revenue

  - kpi_id: sales.net_sales.delta_pct.plan
    kpi_name: Net Sales % vs Plan
    measure_name: Net Sales % vs Plan
    format: "0.0%"
    folder: 01_Revenue

  - kpi_id: sales.net_sales.delta_pct.ly
    kpi_name: Net Sales % vs LY
    measure_name: Net Sales % vs LY
    format: "0.0%"
    folder: 01_Revenue

  - kpi_id: margin.gm.pct
    kpi_name: Gross Margin %
    measure_name: Gross Margin %
    format: "0.0%"
    folder: 02_Margin

  - kpi_id: sales.pvm.price_effect.amount
    kpi_name: Price Effect Amount
    measure_name: Price Effect Amount
    format: "EUR #,0"
    folder: 03_PVM

  - kpi_id: sales.pvm.volume_effect.amount
    kpi_name: Volume Effect Amount
    measure_name: Volume Effect Amount
    format: "EUR #,0"
    folder: 03_PVM

  - kpi_id: sales.pvm.mix_effect.amount
    kpi_name: Mix Effect Amount
    measure_name: Mix Effect Amount
    format: "EUR #,0"
    folder: 03_PVM
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
      - {name: Plan Quantity, type: decimal, agg: sum, nullable: true}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Discount Amount, type: currency, agg: sum, nullable: true}
      - {name: Plan Sales Amount, type: currency, agg: sum, nullable: true}
      - {name: Last Year Sales Amount, type: currency, agg: sum, nullable: true}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- dim_date, dim_org, dim_product, security_user_org, dim_customer (nullable on fact), dim_promo (optional)
- fact_sales (with plan/LY and pricing fields)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> fact_sales on DateKey  
- dim_org (1) -> fact_sales on OrgKey  
- dim_product (1) -> fact_sales on ProductKey  
- dim_promo (1) -> fact_sales on PromoKey (if used)  
- dim_customer (1) -> fact_sales on CustomerKey (nullable)  
- security_user_org filters dim_org -> cascades to fact_sales  
- Single direction; no ambiguous paths; no bi-directional except RLS bridge if required.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month  
- Org: Region -> Country -> Channel -> OrgName  
- Product: Category -> Subcategory -> ProductName  

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- ProductName -> ProductCode  

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; display folders per dictionary.  
- Surrogate keys mandatory; avoid M2M; plan/LY fields required for KPI deltas.  

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Net Sales Amount | sales.net_sales.amount | Revenue base | 01_Revenue | EUR #,0 | KPI |
| Net Sales % vs Plan | sales.net_sales.delta_pct.plan | Gap to plan | 01_Revenue | 0.0% | KPI |
| Net Sales % vs LY | sales.net_sales.delta_pct.ly | Gap to LY | 01_Revenue | 0.0% | KPI |
| Gross Margin % | margin.gm.pct | Profitability quality | 02_Margin | 0.0% | KPI |
| Price Effect Amount | sales.pvm.price_effect.amount | P driver | 03_PVM | EUR #,0 | KPI/Supporting |
| Volume Effect Amount | sales.pvm.volume_effect.amount | V driver | 03_PVM | EUR #,0 | KPI/Supporting |
| Mix Effect Amount | sales.pvm.mix_effect.amount | M driver | 03_PVM | EUR #,0 | KPI/Supporting |
| Plan Sales Amount | Supporting | Plan base | 01_Revenue | EUR #,0 | Supporting |
| Last Year Sales Amount | Supporting | LY base | 01_Revenue | EUR #,0 | Supporting |
| Net Price Amount | Supporting | Price input | 03_PVM | EUR #,0 | Supporting |
| List Price Amount | Supporting | Price input | 03_PVM | EUR #,0 | Supporting |
| Plan Quantity | Supporting | Volume input | 03_PVM | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// sales.net_sales.amount - Revenue base
Net Sales Amount =
SUM ( fact_sales[Net Sales Amount] )

/// sales.net_sales.delta_pct.plan - Gap to plan
Net Sales % vs Plan =
VAR Actual = [Net Sales Amount]
VAR Plan   = SUM ( fact_sales[Plan Sales Amount] )
RETURN DIVIDE ( Actual - Plan, Plan )

/// sales.net_sales.delta_pct.ly - Gap to LY
Net Sales % vs LY =
VAR Actual = [Net Sales Amount]
VAR LY     = SUM ( fact_sales[Last Year Sales Amount] )
RETURN DIVIDE ( Actual - LY, LY )

/// margin.gm.pct - Profitability quality
Gross Margin % =
DIVIDE ( [Net Sales Amount] - SUM ( fact_sales[Cost of Goods Sold Amount] ), [Net Sales Amount] )

/// sales.pvm.price_effect.amount - Price impact vs Plan
Price Effect Amount =
SUMX (
    fact_sales,
    VAR ActualPrice = DIVIDE ( fact_sales[Net Sales Amount], fact_sales[Quantity] )
    VAR PlanPrice   = DIVIDE ( fact_sales[Plan Sales Amount], fact_sales[Plan Quantity] )
    RETURN ( ActualPrice - PlanPrice ) * fact_sales[Quantity]
)

/// sales.pvm.volume_effect.amount - Volume impact vs Plan
Volume Effect Amount =
SUMX (
    fact_sales,
    VAR ActualQty = fact_sales[Quantity]
    VAR PlanQty   = fact_sales[Plan Quantity]
    VAR PlanPrice = DIVIDE ( fact_sales[Plan Sales Amount], PlanQty )
    RETURN ( ActualQty - PlanQty ) * PlanPrice
)

/// sales.pvm.mix_effect.amount - Mix residual
Mix Effect Amount =
[Net Sales Amount] - SUM ( fact_sales[Plan Sales Amount] ) - [Price Effect Amount] - [Volume Effect Amount]
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

- Plan and LY fields populated in fact_sales; PVM relies on Plan Sales Amount and Plan Quantity.
- Returns/credit notes handled upstream; Net Sales already net of discounts.
- Currency EUR; no FX conversion in model.
- PVM logic aligned with COM-002; shared calc layer if reused.

---

## 8. Deployment Requirements

- Mode: DirectLake or Import; prefer DirectLake if available.
- Incremental refresh: partition by Month for last 24 months.
- Aggregations optional for large volumes; avoid grain distortion.
- Workspace/naming per governance; display folders per dictionary.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in fact_sales | 100% | Y | Data Engineering |
| Balancing | Net Sales Amount matches source totals per month | �0.1% | Y | Controlling |
| PVM Integrity | Price + Volume + Mix = Net Sales gap vs Plan | Residual < 0.5% of Net Sales | Y | BI |
| GM Consistency | GM % recomputes from GM Amount/Net Sales | Exact | Y | BI |
| RLS Coverage | Users only see authorised regions/channels | 0 leaks in test | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

---

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md



