---
id: COM-002
factsheet_type: technical
---

# COM-002 - Margin & Price Performance  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Commercial
- **Technical Owner:** Commercial BI / Pricing Analytics Lead
- **Model ID:** commercial_margin_price
- **Source Systems:** ERP (sales, cost), DWH
- **Business Factsheet:** ./Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** data_contracts/sources/commercial.yaml
- **Semantic Model Definition:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** semantic_models/domains/Commercial/Measure_Dictionary_Commercial.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: margin.gm.pct
    kpi_name: Gross Margin %
    measure_name: Gross Margin %
    format: "0.0%"
    folder: 02_Margin

  - kpi_id: profit.gross_margin
    kpi_name: Gross Margin % (Strategic)
    measure_name: Gross Margin %
    format: "0.0%"
    folder: 02_Margin

  - kpi_id: margin.gm.amount
    kpi_name: Gross Margin Amount
    measure_name: Gross Margin Amount
    format: "EUR #,0"
    folder: 02_Margin

  - kpi_id: sales.price.realization_pct
    kpi_name: Price Realization %
    measure_name: Price Realization %
    format: "0.0%"
    folder: 03_Pricing

  - kpi_id: sales.pvm.mix_effect.amount
    kpi_name: Mix Effect Amount
    measure_name: Mix Effect Amount
    format: "EUR #,0"
    folder: 03_PVM

  - kpi_id: cost.cogs_per_unit.amount
    kpi_name: COGS per Unit
    measure_name: COGS per Unit
    format: "EUR #,0.00"
    folder: 02_Margin

  - kpi_id: margin.gm.vs_plan.pct
    kpi_name: Gross Margin % vs Plan
    measure_name: Gross Margin % vs Plan
    format: "0.0 pp"
    folder: 02_Margin
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
      - {name: Rebate Amount, type: currency, agg: sum, nullable: true}
      - {name: Surcharge Amount, type: currency, agg: sum, nullable: true}
      - {name: Plan Sales Amount, type: currency, agg: sum, nullable: true}
      - {name: Last Year Sales Amount, type: currency, agg: sum, nullable: true}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}
      - {name: Plan COGS Amount, type: currency, agg: sum, nullable: true}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- dim_date, dim_org, dim_product, security_user_org, dim_customer (nullable on fact), dim_promo (optional)
- fact_sales (including plan/LY, price components, discounts/rebates/surcharges, COGS, plan COGS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> fact_sales on DateKey  
- dim_org (1) -> fact_sales on OrgKey  
- dim_product (1) -> fact_sales on ProductKey  
- dim_promo (1) -> fact_sales on PromoKey (if used)  
- dim_customer (1) -> fact_sales on CustomerKey (nullable)  
- security_user_org filters dim_org -> cascades to fact_sales  
- Single direction; avoid ambiguous paths; no bi-directional except RLS bridge if required.

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
- Surrogate keys mandatory; avoid M2M; plan price/quantity and plan COGS required for variance logic.  

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Gross Margin % | margin.gm.pct | Profitability quality | 02_Margin | 0.0% | KPI |
| Gross Margin Amount | margin.gm.amount | Profit pool | 02_Margin | EUR #,0 | KPI |
| Price Realization % | sales.price.realization_pct | Discount discipline | 03_Pricing | 0.0% | KPI |
| Mix Effect Amount | sales.pvm.mix_effect.amount | Mix driver | 03_PVM | EUR #,0 | KPI/Supporting |
| COGS per Unit | cost.cogs_per_unit.amount | Unit cost control | 02_Margin | EUR #,0.00 | KPI |
| Gross Margin % vs Plan | margin.gm.vs_plan.pct | Performance vs plan | 02_Margin | 0.0 pp | KPI |
| Net Sales Amount | Supporting | Revenue base | 01_Revenue | EUR #,0 | Supporting |
| Plan Sales Amount | Supporting | Plan base | 01_Revenue | EUR #,0 | Supporting |
| Last Year Sales Amount | Supporting | LY base | 01_Revenue | EUR #,0 | Supporting |
| Cost of Goods Sold Amount | Supporting | Cost base | 02_Margin | EUR #,0 | Supporting |
| Plan COGS Amount | Supporting | Cost plan | 02_Margin | EUR #,0 | Supporting |
| Net Price Amount | Supporting | Pricing input | 03_Pricing | EUR #,0 | Supporting |
| List Price Amount | Supporting | Pricing input | 03_Pricing | EUR #,0 | Supporting |
| Quantity | Supporting | Volume input | 03_PVM | #,0 | Supporting |
| Plan Quantity | Supporting | Volume plan | 03_PVM | #,0 | Supporting |
| Discount Amount | Supporting | Discount input | 03_Pricing | EUR #,0 | Supporting |
| Rebate Amount | Supporting | Rebate input | 03_Pricing | EUR #,0 | Supporting |
| Surcharge Amount | Supporting | Surcharge input | 03_Pricing | EUR #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// margin.gm.pct - Profitability quality
Gross Margin % =
DIVIDE ( [Net Sales Amount] - [Cost of Goods Sold Amount], [Net Sales Amount] )

/// margin.gm.amount - Profit pool
Gross Margin Amount =
[Net Sales Amount] - [Cost of Goods Sold Amount]

/// sales.price.realization_pct - Discount discipline
Price Realization % =
DIVIDE ( [Net Price Amount], [List Price Amount] )

/// sales.pvm.mix_effect.amount - Mix residual (PVM)
Mix Effect Amount =
[Net Sales Amount]
    - SUM ( fact_sales[Plan Sales Amount] )
    - [Price Effect Amount]
    - [Volume Effect Amount]

/// cost.cogs_per_unit.amount - Unit cost control
COGS per Unit =
DIVIDE ( [Cost of Goods Sold Amount], SUM ( fact_sales[Quantity] ) )

/// margin.gm.vs_plan.pct - Performance vs plan
Gross Margin % vs Plan =
VAR GMAct =
    DIVIDE ( [Net Sales Amount] - [Cost of Goods Sold Amount], [Net Sales Amount] )
VAR GMPlan =
    DIVIDE ( SUM ( fact_sales[Plan Sales Amount] ) - SUM ( fact_sales[Plan COGS Amount] ),
             SUM ( fact_sales[Plan Sales Amount] ) )
RETURN
    DIVIDE ( GMAct - GMPlan, GMPlan )

// Supporting PVM effects
/// Supporting - Net Sales Amount
Net Sales Amount =
SUM ( fact_sales[Net Sales Amount] )

/// Supporting - Price Effect Amount
Price Effect Amount =
SUMX (
    fact_sales,
    VAR ActualPrice = DIVIDE ( fact_sales[Net Sales Amount], fact_sales[Quantity] )
    VAR PlanPrice   = DIVIDE ( fact_sales[Plan Sales Amount], fact_sales[Plan Quantity] )
    RETURN ( ActualPrice - PlanPrice ) * fact_sales[Quantity]
)

/// Supporting - Volume Effect Amount
Volume Effect Amount =
SUMX (
    fact_sales,
    VAR ActualQty = fact_sales[Quantity]
    VAR PlanQty   = fact_sales[Plan Quantity]
    VAR PlanPrice = DIVIDE ( fact_sales[Plan Sales Amount], PlanQty )
    RETURN ( ActualQty - PlanQty ) * PlanPrice
)
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

- Plan/LY fields populated (Plan Sales/COGS, LY Sales) at the same grain as actuals.
- Discount/Net/List price, rebates, surcharges complete for price realization.
- PVM logic consistent with COM-001; shared calc layer recommended.
- Currency EUR; returns/credit notes handled upstream.

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
| GM Recompute | GM % recomputes from amounts | Exact | Y | BI |
| Plan Alignment | Plan Sales/COGS populated for plan periods | 100% for plan scope | Y | Controlling |
| PVM Residual | Price + Volume + Mix = Net Sales gap vs Plan | Residual < 0.5% of Net Sales | Y | BI |
| RLS Coverage | Users only see authorised regions/channels | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

---

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md



