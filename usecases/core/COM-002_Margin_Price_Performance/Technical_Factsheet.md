# COM-002 — Margin & Price Performance  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Commercial BI / Pricing Analytics Lead
- **Model ID:** commercial_margin_price
- **Source Systems:** ERP (sales, cost), DWH
- **Business Factsheet:** usecases/core/COM-002_Margin_Price_Performance/Business_Factsheet.md

---

## 1. Model References
- **Domain Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** data_contracts/sources/commercial.yaml
- **Semantic Model Definition:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** framework/kpi_catalog/domain_measure_dictionary.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs → Measure Mapping (Mandatory)
```yaml
kpi_to_measure_mapping:
  - kpi_id: margin.gm.pct
    kpi_name: Gross Margin %
    measure_name: [Gross Margin %]
    format: 0.0%
    folder: 02_Margin
  - kpi_id: margin.gm.amount
    kpi_name: Gross Margin Amount
    measure_name: [Gross Margin Amount]
    format: €#,0
    folder: 02_Margin
  - kpi_id: sales.price.realization_pct
    kpi_name: Price Realization %
    measure_name: [Price Realization %]
    format: 0.0%
    folder: 03_Pricing
  - kpi_id: sales.pvm.mix_effect.amount
    kpi_name: Mix Effect Amount
    measure_name: [Mix Effect Amount]
    format: €#,0
    folder: 03_PVM
  - kpi_id: cost.cogs_per_unit.amount
    kpi_name: COGS per Unit
    measure_name: [COGS per Unit]
    format: €#,0.00
    folder: 02_Margin
  - kpi_id: margin.gm.vs_plan.pct
    kpi_name: Gross Margin % vs Plan
    measure_name: [Gross Margin % vs Plan]
    format: 0.0 pp
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
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity, type: decimal, agg: sum}
      - {name: Plan Quantity, type: decimal, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Discount Amount, type: currency, agg: sum}
      - {name: Rebate Amount, type: currency, agg: sum, nullable: true}
      - {name: Surcharge Amount, type: currency, agg: sum, nullable: true}
      - {name: Plan Sales Amount, type: currency, agg: sum}
      - {name: Last Year Sales Amount, type: currency, agg: sum}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}
      - {name: Plan COGS Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 4. Semantic Model Requirements

### 4.1 Tables
- fact_sales  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)
- dim_date (1) → fact_sales on DateKey  
- dim_org (1) → fact_sales on OrgKey  
- dim_product (1) → fact_sales on ProductKey  
- security_user_org filters dim_org (Region/Country/Channel/OrgKey) → cascades to fact_sales  
- Single direction; no bi-directional except RLS bridge; no ambiguous paths.

### 4.3 Hierarchies
- Date: Year → Quarter → Month  
- Org: Region → Country → Channel → OrgName  
- Product: Category → Subcategory → ProductName

### 4.4 Sort-by Columns
- Month → MonthNumber  
- OrgName → OrgCode  
- ProductName → ProductCode

### 4.5 Modeling Constraints
- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; display folders per dictionary.  
- Surrogate keys mandatory; no M2M relationships.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory
| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Gross Margin Amount | margin.gm.amount | Profit pool | 02_Margin | €#,0 | KPI |
| Gross Margin % | margin.gm.pct | Profitability | 02_Margin | 0.0% | KPI |
| Gross Margin % vs Plan | margin.gm.vs_plan.pct | Plan comparison | 02_Margin | 0.0 pp | KPI |
| Price Realization % | sales.price.realization_pct | Discount discipline | 03_Pricing | 0.0% | KPI |
| Mix Effect Amount | sales.pvm.mix_effect.amount | Mix driver | 03_PVM | €#,0 | Supporting |
| COGS per Unit | cost.cogs_per_unit.amount | Unit cost | 02_Margin | €#,0.00 | KPI |
| Net Sales Amount | Supporting | Revenue base | 01_Revenue | €#,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// Supporting — Revenue
Net Sales Amount :=
    SUM ( fact_sales[Net Sales Amount] )

/// Supporting — Plan revenue
Plan Sales Amount :=
    SUM ( fact_sales[Plan Sales Amount] )

/// Supporting — Cost
COGS Amount :=
    SUM ( fact_sales[Cost of Goods Sold Amount] )

/// margin.gm.amount — Profit pool
Gross Margin Amount :=
    [Net Sales Amount] - [COGS Amount]

/// margin.gm.pct — Profitability
Gross Margin % :=
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )

/// margin.gm.vs_plan.pct — Plan comparison (pp)
Gross Margin % vs Plan :=
    DIVIDE ( [Gross Margin %] - DIVIDE ( [Plan Sales Amount] - SUM ( fact_sales[Plan COGS Amount] ), [Plan Sales Amount] ), 1 )

/// sales.price.realization_pct — Discount discipline
Price Realization % :=
    DIVIDE ( SUM ( fact_sales[Net Price Amount] ), SUM ( fact_sales[List Price Amount] ) )

/// sales.pvm.mix_effect.amount — Mix driver (residual)
Mix Effect Amount :=
    VAR PVM_Total =
        [Net Sales Amount] - [Plan Sales Amount]
    VAR PriceEffect =
        SUMX (
            fact_sales,
            VAR ActualQty = fact_sales[Quantity]
            VAR PlanQty   = fact_sales[Plan Quantity]
            VAR ActualPrice = DIVIDE ( fact_sales[Net Price Amount], ActualQty )
            VAR PlanPrice   = DIVIDE ( fact_sales[Plan Sales Amount], PlanQty )
            RETURN ( ActualPrice - PlanPrice ) * ActualQty
        )
    VAR VolumeEffect =
        SUMX (
            fact_sales,
            VAR ActualQty = fact_sales[Quantity]
            VAR PlanQty   = fact_sales[Plan Quantity]
            VAR PlanPrice = DIVIDE ( fact_sales[Plan Sales Amount], PlanQty )
            RETURN ( ActualQty - PlanQty ) * PlanPrice
        )
    RETURN PVM_Total - PriceEffect - VolumeEffect

/// cost.cogs_per_unit.amount — Unit cost
COGS per Unit :=
    DIVIDE ( [COGS Amount], SUM ( fact_sales[Quantity] ) )
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
- None required; all measures visible to authorised users.

---

## 7. Technical Assumptions
- Data latency ≤24h; plan and LY snapshots stored monthly at invoice_line grain.
- Currency EUR; no FX conversion inside the model.
- Pricing elements (list, net, discounts, rebates, surcharges) populated from source.
- PVM logic harmonised with COM-001/004; shared calc layer to avoid divergence.

---

## 8. Deployment Requirements
- Mode: DirectLake or Import (prefer DirectLake where available).
- Incremental refresh: yes, monthly partitions for last 24 months.
- Aggregations: optional if >24M rows; consider monthly aggregates for GM trends.
- Workspace/naming: `ARF – Commercial` dataset/model naming per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in fact_sales | 100% | Y | Data Engineering |
| GM Reconciliation | GM Amount = Net Sales – COGS | Exact | Y | BI |
| PVM Integrity | Price + Volume + Mix = Net Sales Δ vs Plan | Residual < 0.5% | Y | BI |
| Price Realization | Net Price ≤ List Price within tolerance | ≤0.5% exceptions | Y | BI |
| COGS per Unit Stability | Variance vs Plan within ±2% except flagged SKUs | ±2% | Y | Controlling |
| RLS Coverage | Users only see authorised regions/channels | 0 leaks in test | Y | Security |
| Performance | Main visuals render < 2s on 24M row sample | <2s | Y | BI |
