---
id: SCM-001
factsheet_type: technical
---

# SCM-001 - Inventory Performance  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Supply Chain
- **Technical Owner:** Supply Chain BI Lead
- **Model ID:** scm_inventory_performance
- **Source Systems:** ERP/WMS, OMS, Forecasting, DWH
- **Business Factsheet:** core/usecases/core/SCM-001_Inventory_Performance/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** core/core/core/data_contracts/domains/supply_chain.yaml
- **Source Data Contract:** core/core/core/data_contracts/sources/supply_chain.yaml (if present)
- **Semantic Model Definition:** core/core/core/semantic_models/core_action_ready/model_definition.yaml
- **KPI Catalog:** core/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** core/core/core/semantic_models/domains/SupplyChain/Measure_Dictionary_SupplyChain.md
- **Action Codes:** core/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)


> Machine-readable KPI-to-Measure mapping is governed by `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on technical context and modeling guidance.


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
      - {name: Week, type: text, nullable: true}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: Location, type: text}
      - {name: Region, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text, nullable: true}
      - {name: ABC_Class, type: text, nullable: true}
      - {name: XYZ_Class, type: text, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_inventory
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Average Inventory Amount, type: currency, agg: sum}
      - {name: Average Inventory Units, type: decimal, agg: sum}
      - {name: Obsolete Inventory Amount, type: currency, agg: sum, nullable: true}
      - {name: Obsolete Inventory Units, type: decimal, agg: sum, nullable: true}

  - name: fact_cogs
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: COGS Amount, type: currency, agg: sum}

  - name: fact_fulfillment
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: OTIF Flag, type: boolean}
      - {name: Order Qty, type: decimal, agg: sum}

  - name: fact_stockout
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Stockout Flag, type: boolean}
      - {name: Demand Occurrences, type: int, agg: sum}

  - name: fact_forecast
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Forecast Units, type: decimal, agg: sum}

  - name: fact_sales
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Sales Units, type: decimal, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_inventory  
- fact_cogs  
- fact_fulfillment  
- fact_stockout  
- fact_forecast  
- fact_sales  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> fact_inventory/fact_cogs/fact_fulfillment/fact_stockout on OrgKey  
- dim_product (1) -> all product-bearing facts on ProductKey  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month -> Week  
- Org: Region -> Location -> Channel  
- Product: Category -> Subcategory -> ProductName

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- ProductName -> ProductCode

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; avoid M2M.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Days in Inventory | inv.dio.days | Working capital | 08_SCM_Inventory | #,0.0 | KPI |
| Inventory Turnover | inv.turnover | Velocity | 08_SCM_Inventory | #,0.0 | KPI |
| Stockout Rate % | inv.stockout.pct | Service risk | 08_SCM_Service | 0.0% | KPI |
| OTIF % | supply.otif.pct | Service level | 08_SCM_Service | 0.0% | KPI |
| Obsolete Inventory % | inv.obsolete.pct | Obsolescence | 08_SCM_Inventory | 0.0% | KPI |
| Forecast Accuracy % | plan.forecast.accuracy.pct | Planning quality | 09_Planning | 0.0% | KPI |
| Avg Inventory Amount | Supporting | DIO base | 08_SCM_Inventory | EUR#,0 | Supporting |
| COGS Amount | Supporting | DIO/turnover base | 08_SCM_Inventory | EUR#,0 | Supporting |
| On-Time In-Full Orders | Supporting | OTIF numerator | 08_SCM_Service | #,0 | Supporting |
| Total Orders | Supporting | OTIF denominator | 08_SCM_Service | #,0 | Supporting |
| Demand Occurrences | Supporting | Stockout denominator | 08_SCM_Service | #,0 | Supporting |
| Stockout Count | Supporting | Stockout numerator | 08_SCM_Service | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Inventory bases
Avg Inventory Amount :=
    SUM ( fact_inventory[Average Inventory Amount] )

/// Supporting - COGS Amount
COGS Amount :=
    SUM ( fact_cogs[COGS Amount] )

/// inv.dio.days - Days in Inventory
Days in Inventory :=
    VAR Days = 30  // adjust to period if needed
    RETURN DIVIDE ( [Avg Inventory Amount], [COGS Amount] ) * Days

/// inv.turnover - Inventory Turnover
Inventory Turnover :=
    DIVIDE ( [COGS Amount], [Avg Inventory Amount] )

/// inv.obsolete.pct - Obsolete %
Obsolete Inventory % :=
    DIVIDE ( SUM ( fact_inventory[Obsolete Inventory Amount] ), [Avg Inventory Amount] )

/// supply.otif.pct - OTIF
On-Time In-Full Orders :=
    SUMX ( fact_fulfillment, IF ( fact_fulfillment[OTIF Flag], fact_fulfillment[Order Qty], 0 ) )

/// Supporting - Total Orders
Total Orders :=
    SUM ( fact_fulfillment[Order Qty] )

/// Supporting - OTIF %
OTIF % :=
    DIVIDE ( [On-Time In-Full Orders], [Total Orders] )

/// inv.stockout.pct - Stockout rate
Stockout Count :=
    SUMX ( fact_stockout, IF ( fact_stockout[Stockout Flag], fact_stockout[Demand Occurrences], 0 ) )

/// Supporting - Demand Occurrences
Demand Occurrences :=
    SUM ( fact_stockout[Demand Occurrences] )

/// Supporting - Stockout Rate %
Stockout Rate % :=
    DIVIDE ( [Stockout Count], [Demand Occurrences] )

/// plan.forecast.accuracy.pct - Forecast accuracy (units-based)
Forecast Accuracy % :=
    VAR Forecast = SUM ( fact_forecast[Forecast Units] )
    VAR Actual   = SUM ( fact_sales[Sales Units] )
    VAR AbsErr   = ABS ( Forecast - Actual )
    RETURN 1 - DIVIDE ( AbsErr, Actual )
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

- None required; inventory values can be sensitive EUR mask if client requests (TODO).

---

## 7. Technical Assumptions

- Inventory snapshots consistent; COGS aligned to same SKU/location/time as inventory.
- Stockout events captured; OTIF flag present; forecast/actual aligned to SKU and month.
- Data latency <=24h; currency EUR.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import (prefer DirectLake if Fabric); ensure incremental refresh on month partitions.  
- Aggregations: optional for large order/stockout tables (weekly/monthly).  
- Workspace/naming: ARF - Supply Chain dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in facts | 100% | Y | Data Engineering |
| DIO/Turnover Integrity | Inventory and COGS alignment; no div-by-zero | 0 errors | Y | BI |
| OTIF Coverage | OTIF flag coverage on orders | 100% orders | Y | Ops |
| Stockout Coverage | Stockout flag coverage on demand occurrences | 100% | Y | Ops |
| Forecast Accuracy | Forecast vs actual available for target SKUs | 100% target scope | Y | Planning |
| RLS Coverage | Users see only authorised locations/channels | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in facts | 100% | Y | Data Engineering |
| DIO/Turnover Integrity | Inventory and COGS alignment; no div-by-zero | 0 errors | Y | BI |
| OTIF Coverage | OTIF flag coverage on orders | 100% orders | Y | Ops |
| Stockout Coverage | Stockout flag coverage on demand occurrences | 100% | Y | Ops |
| Forecast Accuracy | Forecast vs actual available for target SKUs | 100% target scope | Y | Planning |
| RLS Coverage | Users see only authorised locations/channels | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md




