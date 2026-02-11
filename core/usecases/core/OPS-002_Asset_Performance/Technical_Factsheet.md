---
id: OPS-002
factsheet_type: technical
---

# OPS-002 - Asset Performance  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Operations
- **Technical Owner:** Maintenance / Reliability BI Lead
- **Model ID:** ops_asset_performance
- **Source Systems:** MES/SCADA, CMMS/EAM, ERP (maintenance), DWH
- **Business Factsheet:** core/usecases/core/OPS-002_Asset_Performance/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** core/core/core/data_contracts/domains/operations.yaml
- **Source Data Contract:** core/core/core/data_contracts/sources/operations.yaml (if present)
- **Semantic Model Definition:** core/core/core/semantic_models/core_action_ready/model_definition.yaml
- **KPI Catalog:** core/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** core/core/core/semantic_models/domains/Operations/Measure_Dictionary_Operations.md
- **Action Codes:** core/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: ops.availability.pct
    kpi_name: Availability %
    measure_name: [Availability %]
    format: 0.0%
    folder: 05_Ops

  - kpi_id: ops.mtbf.hours
    kpi_name: MTBF (hours)
    measure_name: [MTBF (hours)]
    format: #,0.0
    folder: 05_Ops

  - kpi_id: ops.mttr.hours
    kpi_name: MTTR (hours)
    measure_name: [MTTR (hours)]
    format: #,0.0
    folder: 05_Ops

  - kpi_id: ops.downtime.unplanned.pct
    kpi_name: Unplanned Downtime %
    measure_name: [Unplanned Downtime %]
    format: 0.0%
    folder: 05_Ops

  - kpi_id: ops.spare_parts.stockout.pct
    kpi_name: Spare Parts Stockout %
    measure_name: [Spare Parts Stockout %]
    format: 0.0%
    folder: 06_Maintenance

  - kpi_id: ops.pm_compliance.pct
    kpi_name: PM Compliance %
    measure_name: [PM Compliance %]
    format: 0.0%
    folder: 06_Maintenance
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
      - {name: Plant, type: text}
      - {name: Line, type: text}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}

  - name: dim_asset
    columns:
      - {name: AssetKey, type: int, role: key}
      - {name: AssetCode, type: text}
      - {name: AssetName, type: text}
      - {name: AssetClass, type: text}
      - {name: Criticality, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}

fact:
  - name: fact_ops
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: AssetKey, type: int, ref: dim_asset}
      - {name: Planned Time Minutes, type: decimal, agg: sum}
      - {name: Run Time Minutes, type: decimal, agg: sum}
      - {name: Unplanned Downtime Minutes, type: decimal, agg: sum}
      - {name: Planned Downtime Minutes, type: decimal, agg: sum, nullable: true}
      - {name: Output Units, type: decimal, agg: sum, nullable: true}

  - name: fact_ops_failures
    columns:
      - {name: AssetKey, type: int, ref: dim_asset}
      - {name: Failure Start DateTime, type: datetime}
      - {name: Failure End DateTime, type: datetime}
      - {name: Repair Duration Hours, type: decimal}
      - {name: Downtime Minutes, type: decimal}
      - {name: Cause Code, type: text, nullable: true}

  - name: fact_maintenance
    columns:
      - {name: AssetKey, type: int, ref: dim_asset}
      - {name: DateKey, type: int, ref: dim_date}
      - {name: Order Type, type: text}            # PM / CM
      - {name: Order Status, type: text}
      - {name: On Time Flag, type: boolean, nullable: true}
      - {name: Delayed Reason, type: text, nullable: true}
      - {name: Parts Stockout Flag, type: boolean, nullable: true}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_ops  
- fact_ops_failures  
- fact_maintenance  
- dim_date  
- dim_org  
- dim_asset  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> fact_ops on DateKey; dim_date (1) -> fact_maintenance on DateKey; dim_date (1) -> fact_ops_failures on DateKey  
- dim_org (1) -> fact_ops on OrgKey  
- dim_asset (1) -> fact_ops / fact_ops_failures / fact_maintenance on AssetKey  
- security_user_org filters dim_org -> cascades via dim_asset to facts (ensure asset has OrgKey)  
- Single direction; no ambiguous paths; avoid bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month -> Week  
- Org: Plant -> Line  
- Asset: AssetClass -> AssetName (or by criticality)

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- AssetName -> AssetCode

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; display folders per dictionary.  
- Surrogate keys mandatory; avoid M2M; handle time intelligence with date dimension.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Availability % | ops.availability.pct | Uptime | 05_Ops | 0.0% | KPI |
| MTBF (hours) | ops.mtbf.hours | Reliability | 05_Ops | #,0.0 | KPI |
| MTTR (hours) | ops.mttr.hours | Maintainability | 05_Ops | #,0.0 | KPI |
| Unplanned Downtime % | ops.downtime.unplanned.pct | Unplanned loss | 05_Ops | 0.0% | KPI |
| Spare Parts Stockout % | ops.spare_parts.stockout.pct | Parts readiness | 06_Maintenance | 0.0% | KPI |
| PM Compliance % | ops.pm_compliance.pct | PM discipline | 06_Maintenance | 0.0% | KPI |
| Run Time Minutes | Supporting | Base time | 05_Ops | #,0 | Supporting |
| Unplanned Downtime Minutes | Supporting | Loss time | 05_Ops | #,0 | Supporting |
| Failure Count | Supporting | MTBF/MTTR calc | 05_Ops | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Time
Planned Time :=
    SUM ( fact_ops[Planned Time Minutes] )

/// Supporting - Run Time
Run Time :=
    SUM ( fact_ops[Run Time Minutes] )

/// Supporting - Unplanned Downtime Minutes
Unplanned Downtime Minutes :=
    SUM ( fact_ops[Unplanned Downtime Minutes] )

/// Supporting - Failure Count
Failure Count :=
    DISTINCTCOUNT ( fact_ops_failures[Failure Start DateTime] )

/// ops.availability.pct - Uptime
Availability % :=
    DIVIDE ( [Run Time], [Planned Time] )

/// ops.downtime.unplanned.pct - Unplanned downtime share
Unplanned Downtime % :=
    DIVIDE ( [Unplanned Downtime Minutes], [Planned Time] )

/// ops.mtbf.hours - Reliability (hours between failures)
MTBF (hours) :=
    VAR TotalRunHours = DIVIDE ( [Run Time], 60 )
    RETURN DIVIDE ( TotalRunHours, [Failure Count] )

/// ops.mttr.hours - Maintainability
MTTR (hours) :=
    AVERAGEX ( fact_ops_failures, fact_ops_failures[Repair Duration Hours] )

/// ops.spare_parts.stockout.pct - Parts readiness
Spare Parts Stockout % :=
    DIVIDE (
        CALCULATE ( COUNTROWS ( fact_maintenance ), fact_maintenance[Parts Stockout Flag] = TRUE ),
        COUNTROWS ( fact_maintenance )
    )

/// ops.pm_compliance.pct - PM discipline
PM Compliance % :=
    DIVIDE (
        CALCULATE ( COUNTROWS ( fact_maintenance ), fact_maintenance[Order Type] = "PM", fact_maintenance[On Time Flag] = TRUE ),
        CALCULATE ( COUNTROWS ( fact_maintenance ), fact_maintenance[Order Type] = "PM" )
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
    - Plant
    - Line
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

- None required; parts cost could be masked if added (TODO per client).

---

## 7. Technical Assumptions

- Failure events timestamped; repair duration provided; planned vs unplanned flagged.
- PM plan exists and on-time flags populated; parts stockout flags available.
- Data latency <=24h; timezone consistent.
- OneLake canonical dims used (dim_date, dim_org, dim_asset, security_user_org).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import depending on MES/CMMS connectors; prefer DirectLake if stable.  
- Incremental refresh: yes, partition by DateKey (e.g., last 12-24 months).  
- Aggregations: optional for high-frequency events.  
- Workspace/naming: `ARF - Operations` dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Asset keys non-null in facts | 100% | Y | Data Engineering |
| Time Balancing | Run Time + Unplanned + Planned <= Planned Time | 100% | Y | BI |
| MTBF/MTTR Validity | No zero/negative durations | 0 exceptions | Y | BI |
| PM Compliance | PM denominator/flags present | 100% PM orders | Y | Maintenance |
| Stockout Flagging | Stockout flag coverage on maintenance orders | 100% | Y | Maintenance |
| RLS Coverage | Users see only authorised plants/lines/assets | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md



