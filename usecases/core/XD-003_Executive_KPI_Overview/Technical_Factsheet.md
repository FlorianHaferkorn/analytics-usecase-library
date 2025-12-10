# XD-003 — Executive KPI Overview  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Executive / Cross-Functional
- **Technical Owner:** Enterprise BI Lead
- **Model ID:** executive_kpi_overview
- **Source Systems:** Finance, Commercial, Supply Chain, HR, DWH
- **Business Factsheet:** usecases/core/XD-003_Executive_KPI_Overview/Business_Factsheet.md

---

## 1. Model References
- **Domain Data Contract:** data_contracts/domains/executive.yaml
- **Source Data Contracts:** data_contracts/domains/finance.yaml; supply_chain.yaml; hr.yaml; commercial_sales.yaml
- **Semantic Model Definition:** semantic_models/domains/executive/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** framework/kpi_catalog/domain_measure_dictionary.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs → Measure Mapping (Mandatory)
```yaml
kpi_to_measure_mapping:
  - kpi_id: sales.revenue.growth_pct
    kpi_name: Revenue Growth %
    measure_name: [Revenue Growth %]
    format: 0.0%
    folder: 01_Growth
  - kpi_id: margin.gm.pct
    kpi_name: Gross Margin %
    measure_name: [Gross Margin %]
    format: 0.0%
    folder: 02_Margin
  - kpi_id: profit.ebitda_margin
    kpi_name: EBITDA Margin
    measure_name: [EBITDA Margin]
    format: 0.0%
    folder: 02_Margin
  - kpi_id: ops.working_capital.ccc.days
    kpi_name: Cash Conversion Cycle (days)
    measure_name: [CCC Days]
    format: #,0.0
    folder: 03_Liquidity
  - kpi_id: supply.otif.pct
    kpi_name: OTIF %
    measure_name: [OTIF %]
    format: 0.0%
    folder: 04_Service
  - kpi_id: hr.turnover.pct
    kpi_name: Employee Turnover %
    measure_name: [Employee Turnover %]
    format: 0.0%
    folder: 05_People
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
      - {name: Entity, type: text}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: Segment, type: text, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}

fact:
  - name: fact_finance
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Gross Margin Amount, type: currency, agg: sum}
      - {name: EBITDA Amount, type: currency, agg: sum}

  - name: fact_wc   # derived or from finance/supply chain
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: DSO Days, type: decimal}
      - {name: DIO Days, type: decimal}
      - {name: DPO Days, type: decimal}

  - name: fact_fulfillment
    grain: order
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: OTIF Flag, type: boolean}
      - {name: Order Qty, type: decimal, agg: sum}

  - name: fact_hr
    grain: month_entity
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Leavers, type: int, agg: sum}
      - {name: Headcount, type: int, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables
- fact_finance  
- fact_wc  
- fact_fulfillment  
- fact_hr  
- dim_date  
- dim_org  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)
- dim_date (1) → all facts on DateKey  
- dim_org (1) → all facts on OrgKey  
- security_user_org filters dim_org → cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies
- Date: Year → Quarter → Month  
- Org: Region → Entity → Segment

### 4.4 Sort-by Columns
- Month → MonthNumber  
- Entity → OrgKey

### 4.5 Modeling Constraints
- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; avoid M2M.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory
| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Revenue Growth % | sales.revenue.growth_pct | Growth | 01_Growth | 0.0% | KPI |
| Gross Margin % | margin.gm.pct | Profitability | 02_Margin | 0.0% | KPI |
| EBITDA Margin | profit.ebitda_margin | Profitability | 02_Margin | 0.0% | KPI |
| CCC Days | ops.working_capital.ccc.days | Liquidity | 03_Liquidity | #,0.0 | KPI |
| OTIF % | supply.otif.pct | Service | 04_Service | 0.0% | KPI |
| Employee Turnover % | hr.turnover.pct | People | 05_People | 0.0% | KPI |
| Net Sales Amount | Supporting | Revenue base | 01_Growth | €#,0 | Supporting |
| Gross Margin Amount | Supporting | Profitability | 02_Margin | €#,0 | Supporting |
| EBITDA Amount | Supporting | Profitability | 02_Margin | €#,0 | Supporting |
| DSO Days | Supporting | CCC component | 03_Liquidity | #,0.0 | Supporting |
| DIO Days | Supporting | CCC component | 03_Liquidity | #,0.0 | Supporting |
| DPO Days | Supporting | CCC component | 03_Liquidity | #,0.0 | Supporting |
| OTIF Orders | Supporting | OTIF numerator | 04_Service | #,0 | Supporting |
| Total Orders | Supporting | OTIF denominator | 04_Service | #,0 | Supporting |
| Leavers | Supporting | Turnover numerator | 05_People | #,0 | Supporting |
| Headcount | Supporting | Turnover denominator | 05_People | #,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// Supporting — Finance bases
Net Sales Amount :=
    SUM ( fact_finance[Net Sales Amount] )

Gross Margin Amount :=
    SUM ( fact_finance[Gross Margin Amount] )

EBITDA Amount :=
    SUM ( fact_finance[EBITDA Amount] )

/// sales.revenue.growth_pct — Growth vs prior period
Revenue Growth % :=
    VAR Current = [Net Sales Amount]
    VAR Prior =
        CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, MONTH ) )
    RETURN DIVIDE ( Current - Prior, Prior )

/// margin.gm.pct — GM%
Gross Margin % :=
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )

/// profit.ebitda_margin — EBITDA %
EBITDA Margin :=
    DIVIDE ( [EBITDA Amount], [Net Sales Amount] )

/// CCC components
DSO Days :=
    AVERAGE ( fact_wc[DSO Days] )

DIO Days :=
    AVERAGE ( fact_wc[DIO Days] )

DPO Days :=
    AVERAGE ( fact_wc[DPO Days] )

CCC Days :=
    [DSO Days] + [DIO Days] - [DPO Days]

/// supply.otif.pct — OTIF
OTIF Orders :=
    SUMX ( fact_fulfillment, IF ( fact_fulfillment[OTIF Flag], fact_fulfillment[Order Qty], 0 ) )

Total Orders :=
    SUM ( fact_fulfillment[Order Qty] )

OTIF % :=
    DIVIDE ( [OTIF Orders], [Total Orders] )

/// hr.turnover.pct — Turnover
Leavers :=
    SUM ( fact_hr[Leavers] )

Headcount :=
    SUM ( fact_hr[Headcount] )

Employee Turnover % :=
    DIVIDE ( [Leavers], [Headcount] )
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
- None required; consider masking EBITDA if client policy demands (TODO).

---

## 7. Technical Assumptions
- Finance, supply chain, and HR data aligned by entity/region and month; plan/targets available.
- CCC components derived upstream (preferred) to avoid duplication; OTIF at order level; turnover at entity level.
- Data latency ≤24h; currency EUR.
- OneLake canonical dims used (dim_date, dim_org, security_user_org).

---

## 8. Deployment Requirements
- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, partition by Month.  
- Aggregations: optional; monthly aggregates sufficient.  
- Workspace/naming: `ARF – Executive` dataset/model per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org keys non-null in facts | 100% | Y | Data Engineering |
| Revenue Growth Calc | Prior-period reference available | 100% | Y | BI |
| GM/EBITDA Validity | No div-by-zero; margins within plausible bands | 0 errors | Y | Finance |
| CCC Consistency | CCC recomputes from DSO/DIO/DPO | Exact | Y | Finance |
| OTIF Coverage | OTIF flag coverage on orders | 100% | Y | Supply |
| Turnover Coverage | Leavers and headcount populated | 100% | Y | HR |
| RLS Coverage | Users see only authorised entities | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |
