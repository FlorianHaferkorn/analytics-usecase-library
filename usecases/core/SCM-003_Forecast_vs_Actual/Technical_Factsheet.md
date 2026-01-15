---
id: SCM-003
factsheet_type: technical
---

# SCM-003 - Forecast vs Actual  

## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Domain:** Supply Chain / Planning
- **Technical Owner:** Planning / S&OP BI Lead
- **Model ID:** scm_forecast_vs_actual
- **Source Systems:** Forecasting system, ERP (actuals), OMS/WMS (service), DWH
- **Business Factsheet:** usecases/core/SCM-003_Forecast_vs_Actual/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** data_contracts/domains/supply_chain.yaml
- **Source Data Contract:** data_contracts/sources/supply_chain.yaml (if present)
- **Semantic Model Definition:** semantic_models/domains/scm/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** semantic_models/domains/SupplyChain/Measure_Dictionary_SupplyChain.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: plan.forecast.accuracy.pct
    kpi_name: Forecast Accuracy %
    measure_name: [Forecast Accuracy %]
    format: 0.0%
    folder: 09_Planning

  - kpi_id: plan.forecast.mape.pct
    kpi_name: MAPE %
    measure_name: [MAPE %]
    format: 0.0%
    folder: 09_Planning

  - kpi_id: plan.forecast.bias.pct
    kpi_name: Bias %
    measure_name: [Bias %]
    format: 0.0%
    folder: 09_Planning

  - kpi_id: plan.forecast.service_impact.pct
    kpi_name: Service Impact %
    measure_name: [Service Impact %]
    format: 0.0%
    folder: 08_SCM_Service

  - kpi_id: plan.replan.count
    kpi_name: Re-Plan Count
    measure_name: [Re-Plan Count]
    format: #,0
    folder: 09_Planning
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
      - {name: Region, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}
      - {name: Location, type: text, nullable: true}

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
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_forecast
    grain: sku_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Forecast Units, type: decimal, agg: sum}
      - {name: Forecast Version, type: text, nullable: true}

  - name: fact_sales
    grain: sku_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Actual Units, type: decimal, agg: sum}

  - name: fact_fulfillment   # for service impact linkage
    grain: order
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: ProductKey, type: int, ref: dim_product, nullable: true}
      - {name: OTIF Flag, type: boolean, nullable: true}

  - name: fact_stockout      # for service impact linkage
    grain: location_sku_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Stockout Flag, type: boolean}
      - {name: Lost Demand Units, type: decimal, agg: sum, nullable: true}
      - {name: Demand Units, type: decimal, agg: sum}

  - name: fact_replan   # if available
    grain: month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: Re-Plan Count, type: int, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_forecast  
- fact_sales  
- fact_fulfillment  
- fact_stockout  
- fact_replan (if present)  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> fact_forecast/fact_sales/fact_fulfillment/fact_stockout on OrgKey  
- dim_product (1) -> fact_forecast/fact_sales/fact_fulfillment/fact_stockout on ProductKey  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month  
- Org: Region -> Channel -> Location  
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
| Forecast Accuracy % | plan.forecast.accuracy.pct | Planning quality | 09_Planning | 0.0% | KPI |
| MAPE % | plan.forecast.mape.pct | Error magnitude | 09_Planning | 0.0% | KPI |
| Bias % | plan.forecast.bias.pct | Error direction | 09_Planning | 0.0% | KPI |
| Service Impact % | plan.forecast.service_impact.pct | Service linkage | 08_SCM_Service | 0.0% | KPI |
| Re-Plan Count | plan.replan.count | Stability | 09_Planning | #,0 | KPI |
| Forecast Units | Supporting | Forecast base | 09_Planning | #,0 | Supporting |
| Actual Units | Supporting | Actual base | 09_Planning | #,0 | Supporting |
| Absolute Error | Supporting | Error magnitude | 09_Planning | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Units-based bases
Forecast Units :=
    SUM ( fact_forecast[Forecast Units] )

/// Supporting - Actual Units
Actual Units :=
    SUM ( fact_sales[Actual Units] )

/// Supporting - Absolute Error
Absolute Error :=
    ABS ( [Forecast Units] - [Actual Units] )

/// plan.forecast.accuracy.pct - Accuracy (units-based)
Forecast Accuracy % :=
    VAR AbsErr = [Absolute Error]
    VAR Actual = [Actual Units]
    RETURN 1 - DIVIDE ( AbsErr, Actual )

/// plan.forecast.mape.pct - MAPE (units-based)
MAPE % :=
    DIVIDE ( [Absolute Error], [Actual Units] )

/// plan.forecast.bias.pct - Bias (units-based)
Bias % :=
    DIVIDE ( [Forecast Units] - [Actual Units], [Actual Units] )

/// plan.forecast.service_impact.pct - Service impact (units-based, placeholder linkage)
Service Impact % :=
    // TODO: requires linkage from forecast error to OTIF/stockout impact
    BLANK ()

/// plan.replan.count - Re-plans
Re-Plan Count :=
    SUM ( fact_replan[Re-Plan Count] )
```

```DAX
// Forecast Error Qty
/// Supporting - Forecast Error Qty
Forecast Error Qty =
[Forecast Qty] - [Actual Demand Qty]


// Under-Forecast Lost Demand Qty
/// Supporting - Under-Forecast Lost Demand Qty
Under-Forecast Lost Demand Qty =
VAR ThresholdPct = 0.05   // configurable threshold
RETURN
SUMX (
    FILTER (
        fact_stockout,
        fact_stockout[Stockout Flag] = TRUE()
            && [Forecast Error Qty] < - ThresholdPct * [Actual Demand Qty]
    ),
    fact_stockout[Lost Demand Qty]
)


// Under-Forecast Lost Demand Share %
/// Supporting - Under-Forecast Lost Demand Share %
Under-Forecast Lost Demand Share % =
DIVIDE ( [Under-Forecast Lost Demand Qty], [Stockout Lost Demand Qty] )


// Service Impact %
/// Supporting - Service Impact %
Service Impact % =
[Stockout Impact %] * [Under-Forecast Lost Demand Share %]
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

- None required; mask cost fields if added (TODO if client requires).

---

## 7. Technical Assumptions

- Forecast and actual data aligned by SKU/location/time; versions managed.
- Service impact linkage requires OTIF/stockout mapping to forecast error (TODO).
- Data latency <=24h; currency not needed unless financial metrics added.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, partition by Month (e.g., last 24 months).  
- Aggregations: optional for large order/stockout linkage tables.  
- Workspace/naming: `ARF - Supply Chain` dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in facts | 100% | Y | Data Engineering |
| Accuracy/Bias Validity | No divide-by-zero on actuals; bias within plausible range | 0 errors | Y | BI |
| Forecast Versioning | Correct version used for comparison window | 100% in scope | Y | Planning |
| Service Impact Coverage | Linkage to OTIF/stockout populated if used | TODO coverage target | N (if manual) | BI/Planning |
| RLS Coverage | Users see only authorised locations/channels | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md


