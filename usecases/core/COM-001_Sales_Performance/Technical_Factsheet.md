# COM-001 — Sales Performance vs Plan & LY  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Sales BI Lead
- **Model ID:** commercial_sales_performance
- **Source Systems:** ERP (sales), DWH
- **Business Factsheet:** usecases/core/COM-001_Sales_Performance/Business_Factsheet.md

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
  - kpi_id: sales.net_sales.amount
    kpi_name: Net Sales Amount
    measure_name: [Net Sales Amount]
    format: €#,0
    folder: 01_Revenue
    notes: KPI
  - kpi_id: sales.net_sales.delta_pct.plan
    kpi_name: Net Sales % vs Plan
    measure_name: [Net Sales % vs Plan]
    format: 0.0%
    folder: 01_Revenue
    notes: KPI
  - kpi_id: sales.net_sales.delta_pct.ly
    kpi_name: Net Sales % vs LY
    measure_name: [Net Sales % vs LY]
    format: 0.0%
    folder: 01_Revenue
    notes: KPI
  - kpi_id: margin.gm.pct
    kpi_name: Gross Margin %
    measure_name: [Gross Margin %]
    format: 0.0%
    folder: 02_Margin
    notes: KPI
  - kpi_id: sales.pvm.price_effect.amount
    kpi_name: Price Effect Amount
    measure_name: [Price Effect Amount]
    format: €#,0
    folder: 03_PVM
    notes: Supporting/KPI driver
  - kpi_id: sales.pvm.volume_effect.amount
    kpi_name: Volume Effect Amount
    measure_name: [Volume Effect Amount]
    format: €#,0
    folder: 03_PVM
    notes: Supporting/KPI driver
  - kpi_id: sales.pvm.mix_effect.amount
    kpi_name: Mix Effect Amount
    measure_name: [Mix Effect Amount]
    format: €#,0
    folder: 03_PVM
    notes: Supporting/KPI driver
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
      - {name: Discount Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Plan Sales Amount, type: currency, agg: sum}
      - {name: Last Year Sales Amount, type: currency, agg: sum}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}

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
- OrgName → OrgCode (if needed)  
- ProductName → ProductCode

### 4.5 Modeling Constraints
- No calculated columns; no implicit measures.  
- Default summarization set explicitly.  
- Technical columns hidden; display folders per dictionary.  
- Surrogate keys mandatory; no M2M relationships.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory
| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Net Sales Amount | sales.net_sales.amount | Core revenue | 01_Revenue | €#,0 | KPI |
| Net Sales % vs Plan | sales.net_sales.delta_pct.plan | Plan comparison | 01_Revenue | 0.0% | KPI |
| Net Sales % vs LY | sales.net_sales.delta_pct.ly | Growth vs LY | 01_Revenue | 0.0% | KPI |
| Gross Margin % | margin.gm.pct | Profitability | 02_Margin | 0.0% | KPI |
| Price Effect Amount | sales.pvm.price_effect.amount | PVM driver | 03_PVM | €#,0 | Supporting |
| Volume Effect Amount | sales.pvm.volume_effect.amount | PVM driver | 03_PVM | €#,0 | Supporting |
| Mix Effect Amount | sales.pvm.mix_effect.amount | PVM driver | 03_PVM | €#,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// sales.net_sales.amount — Core revenue
Net Sales Amount :=
    SUM ( fact_sales[Net Sales Amount] )

/// Supporting — Plan
Plan Sales Amount :=
    SUM ( fact_sales[Plan Sales Amount] )

/// Supporting — LY
Last Year Sales Amount :=
    SUM ( fact_sales[Last Year Sales Amount] )

/// Supporting — Gross Margin Amount
Gross Margin Amount :=
    SUM ( fact_sales[Net Sales Amount] ) - SUM ( fact_sales[Cost of Goods Sold Amount] )

/// margin.gm.pct — Profitability
Gross Margin % :=
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )

/// sales.net_sales.delta_pct.plan — Plan comparison
Net Sales % vs Plan :=
    DIVIDE ( [Net Sales Amount] - [Plan Sales Amount], [Plan Sales Amount] )

/// sales.net_sales.delta_pct.ly — Growth vs LY
Net Sales % vs LY :=
    DIVIDE ( [Net Sales Amount] - [Last Year Sales Amount], [Last Year Sales Amount] )

/// sales.pvm.price_effect.amount — Price impact vs Plan
Price Effect Amount :=
    SUMX (
        fact_sales,
        VAR ActualQty = fact_sales[Quantity]
        VAR PlanQty   = fact_sales[Plan Quantity]
        VAR ActualPrice = DIVIDE ( fact_sales[Net Price Amount], ActualQty )
        VAR PlanPrice   = DIVIDE ( fact_sales[Plan Sales Amount], PlanQty )
        RETURN ( ActualPrice - PlanPrice ) * ActualQty
    )

/// sales.pvm.volume_effect.amount — Volume impact vs Plan
Volume Effect Amount :=
    SUMX (
        fact_sales,
        VAR ActualQty = fact_sales[Quantity]
        VAR PlanQty   = fact_sales[Plan Quantity]
        VAR PlanPrice = DIVIDE ( fact_sales[Plan Sales Amount], PlanQty )
        RETURN ( ActualQty - PlanQty ) * PlanPrice
    )

/// sales.pvm.mix_effect.amount — Mix residual
Mix Effect Amount :=
    [Net Sales Amount] - [Plan Sales Amount] - [Price Effect Amount] - [Volume Effect Amount]
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
- None required for this use case; monetary columns visible to authorised users.

---

## 7. Technical Assumptions
- Data latency ≤24h; monthly plan/LY snapshots stored at same grain as actuals.
- Currency in EUR; no FX conversion needed in model.
- PVM logic aligned with COM-002 margin/price performance; shared calc layer.
- Returns/credit notes handled in source; if material, flagged separately.

---

## 8. Deployment Requirements
- Mode: DirectLake or Import depending on Fabric availability; prefer DirectLake.  
- Incremental refresh: yes, partition by Month for last 24 months.  
- Aggregations: optional for >24M rows; consider monthly aggregates for trend visuals.  
- Workspace/naming: `ARF – Commercial` dataset/model naming per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | All Date/Org/Product keys non-null in fact_sales | 100% | Y | Data Engineering |
| Balancing | Net Sales Amount matches source totals per month | ±0.1% | Y | Controlling |
| PVM Integrity | Price + Volume + Mix = Net Sales Δ vs Plan | Residual < 0.5% of Net Sales | Y | BI |
| GM Consistency | GM % recomputes from GM Amount/Net Sales | Exact | Y | BI |
| RLS Coverage | Users only see authorised regions/channels | 0 leaks in test | Y | Security |
| Performance | Main visuals render < 2s on 24M row sample | <2s | Y | BI |
