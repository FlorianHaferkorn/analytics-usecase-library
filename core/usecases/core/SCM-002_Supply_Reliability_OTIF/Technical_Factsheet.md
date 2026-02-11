---
id: SCM-002
factsheet_type: technical
---

# SCM-002 - Supply Reliability & OTIF  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Supply Chain
- **Technical Owner:** Logistics / Supply Chain BI Lead
- **Model ID:** scm_supply_reliability
- **Source Systems:** ERP/WMS/TMS, OMS, DWH
- **Business Factsheet:** framework/usecases/core/SCM-002_Supply_Reliability_OTIF/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** framework/framework/framework/data_contracts/domains/supply_chain.yaml
- **Source Data Contract:** framework/framework/framework/data_contracts/sources/supply_chain.yaml (if present)
- **Semantic Model Definition:** framework/framework/framework/semantic_models/core_action_ready/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** framework/framework/framework/semantic_models/domains/SupplyChain/Measure_Dictionary_SupplyChain.md
- **Action Codes:** framework/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: supply.otif.pct
    kpi_name: OTIF %
    measure_name: [OTIF %]
    format: 0.0%
    folder: 08_SCM_Service

  - kpi_id: supply.on_time.pct
    kpi_name: On-Time %
    measure_name: [On-Time %]
    format: 0.0%
    folder: 08_SCM_Service

  - kpi_id: supply.in_full.pct
    kpi_name: In-Full %
    measure_name: [In-Full %]
    format: 0.0%
    folder: 08_SCM_Service

  - kpi_id: supply.stockout_impact.pct
    kpi_name: Stockout Impact %
    measure_name: [Stockout Impact %]
    format: 0.0%
    folder: 08_SCM_Service

  - kpi_id: supply.penalty.amount
    kpi_name: Penalty Amount
    measure_name: [Penalty Amount]
    format: EUR#,0
    folder: 08_SCM_Cost

  - kpi_id: supply.expedite.amount
    kpi_name: Expedite Cost Amount
    measure_name: [Expedite Cost Amount]
    format: EUR#,0
    folder: 08_SCM_Cost
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
      - {name: Week, type: text, nullable: true}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: Location, type: text}
      - {name: Region, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}
      - {name: Customer, type: text, nullable: true}

  - name: dim_product   # optional if needed
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text, nullable: true}

  - name: dim_lane      # optional for transport lanes
    columns:
      - {name: LaneKey, type: int, role: key}
      - {name: Origin, type: text}
      - {name: Destination, type: text}
      - {name: Mode, type: text, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_fulfillment
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product, nullable: true}
      - {name: LaneKey, type: int, ref: dim_lane, nullable: true}
      - {name: On-Time Flag, type: boolean}
      - {name: In-Full Flag, type: boolean}
      - {name: OTIF Flag, type: boolean}
      - {name: Order Qty, type: decimal, agg: sum}
      - {name: Penalty Amount, type: currency, agg: sum, nullable: true}
      - {name: Expedite Cost, type: currency, agg: sum, nullable: true}

  - name: fact_stockout
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Stockout Flag, type: boolean}
      - {name: Lost Demand Units, type: decimal, agg: sum, nullable: true}
      - {name: Demand Units, type: decimal, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_fulfillment  
- fact_stockout  
- dim_date  
- dim_org  
- dim_product (optional)  
- dim_lane (optional)  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> fact_fulfillment / fact_stockout on DateKey  
- dim_org (1) -> fact_fulfillment / fact_stockout on OrgKey  
- dim_product (1) -> fact_fulfillment / fact_stockout on ProductKey (if present)  
- dim_lane (1) -> fact_fulfillment on LaneKey (if used)  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month -> Week  
- Org: Region -> Location -> Channel -> Customer  
- Product (if used): Category -> ProductName  
- Lane: Origin -> Destination (optional)

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- Customer -> OrgKey (or CustomerCode)

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; avoid M2M.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| OTIF % | supply.otif.pct | Service level | 08_SCM_Service | 0.0% | KPI |
| On-Time % | supply.on_time.pct | Timeliness | 08_SCM_Service | 0.0% | KPI |
| In-Full % | supply.in_full.pct | Completeness | 08_SCM_Service | 0.0% | KPI |
| Stockout Impact % | supply.stockout_impact.pct | Service loss | 08_SCM_Service | 0.0% | KPI |
| Penalty Amount | supply.penalty.amount | Service failure cost | 08_SCM_Cost | EUR#,0 | KPI |
| Expedite Cost Amount | supply.expedite.amount | Recovery cost | 08_SCM_Cost | EUR#,0 | KPI |
| OTIF Orders | Supporting | OTIF numerator | 08_SCM_Service | #,0 | Supporting |
| Total Orders | Supporting | OTIF denominator | 08_SCM_Service | #,0 | Supporting |
| On-Time Deliveries | Supporting | On-time numerator | 08_SCM_Service | #,0 | Supporting |
| In-Full Deliveries | Supporting | In-full numerator | 08_SCM_Service | #,0 | Supporting |
| Lost Demand Units | Supporting | Stockout numerator | 08_SCM_Service | #,0 | Supporting |
| Demand Units | Supporting | Stockout denominator | 08_SCM_Service | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Fulfillment counts
OTIF Orders :=
    SUMX ( fact_fulfillment, IF ( fact_fulfillment[OTIF Flag], fact_fulfillment[Order Qty], 0 ) )

/// Supporting - Total Orders
Total Orders :=
    SUM ( fact_fulfillment[Order Qty] )

/// Supporting - On-Time Deliveries
On-Time Deliveries :=
    SUMX ( fact_fulfillment, IF ( fact_fulfillment[On-Time Flag], fact_fulfillment[Order Qty], 0 ) )

/// Supporting - In-Full Deliveries
In-Full Deliveries :=
    SUMX ( fact_fulfillment, IF ( fact_fulfillment[In-Full Flag], fact_fulfillment[Order Qty], 0 ) )

/// supply.otif.pct - OTIF %
OTIF % :=
    DIVIDE ( [OTIF Orders], [Total Orders] )

/// supply.on_time.pct - On-Time %
On-Time % :=
    DIVIDE ( [On-Time Deliveries], [Total Orders] )

/// supply.in_full.pct - In-Full %
In-Full % :=
    DIVIDE ( [In-Full Deliveries], [Total Orders] )

/// Supporting - Stockout
Lost Demand Units :=
    SUM ( fact_stockout[Lost Demand Units] )

/// Supporting - Demand Units
Demand Units :=
    SUM ( fact_stockout[Demand Units] )

/// supply.stockout_impact.pct - Stockout impact %
Stockout Impact % :=
    DIVIDE ( [Lost Demand Units], [Demand Units] )

/// supply.penalty.amount - Penalty
Penalty Amount :=
    SUM ( fact_fulfillment[Penalty Amount] )

/// supply.expedite.amount - Expedite cost
Expedite Cost Amount :=
    SUM ( fact_fulfillment[Expedite Cost] )
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

- None required; penalty/expedite cost could be masked if client requires (TODO if needed).

---

## 7. Technical Assumptions

- OTIF, on-time, in-full flags available and consistent; penalties/expedites captured at order/shipment level.
- Stockout impact measured via lost demand; demand captured consistently.
- Data latency <=24h; currency EUR.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org; dim_lane optional).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, partition by DateKey (e.g., last 12-24 months).  
- Aggregations: optional for large order lines; consider weekly aggregates for OTIF.  
- Workspace/naming: `ARF - Supply Chain` dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org keys non-null in facts | 100% | Y | Data Engineering |
| OTIF/On-Time/In-Full Integrity | OTIF <= On-Time and In-Full within tolerance | 100% | Y | BI |
| Stockout Coverage | Lost demand and demand populated where stockout flag true | 100% flagged scope | Y | Ops |
| Penalty/Expedite Coverage | Penalty/expedite captured for service failures | 100% expected scope | Y | Ops/Finance |
| RLS Coverage | Users see only authorised locations/channels | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md



