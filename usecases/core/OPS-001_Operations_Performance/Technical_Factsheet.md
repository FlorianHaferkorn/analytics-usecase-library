---
id: OPS-001
factsheet_type: technical
---

# OPS-001 - Operations Performance  

## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Domain:** Operations
- **Technical Owner:** Ops BI Lead / Plant Analytics
- **Model ID:** ops_performance
- **Source Systems:** MES/SCADA, ERP (production orders), DWH
- **Business Factsheet:** usecases/core/OPS-001_Operations_Performance/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** data_contracts/domains/operations.yaml
- **Source Data Contract:** data_contracts/sources/operations.yaml (if present)
- **Semantic Model Definition:** semantic_models/domains/scm/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** semantic_models/domains/Operations/Measure_Dictionary_Operations.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: ops.oee.pct
    kpi_name: OEE %
    measure_name: [OEE %]
    format: 0.0%
    folder: 05_Ops

  - kpi_id: ops.availability.pct
    kpi_name: Availability %
    measure_name: [Availability %]
    format: 0.0%
    folder: 05_Ops

  - kpi_id: ops.performance.pct
    kpi_name: Performance %
    measure_name: [Performance %]
    format: 0.0%
    folder: 05_Ops

  - kpi_id: ops.quality.pct
    kpi_name: Quality %
    measure_name: [Quality %]
    format: 0.0%
    folder: 05_Ops

  - kpi_id: ops.throughput.units
    kpi_name: Throughput Units
    measure_name: [Throughput Units]
    format: #,0
    folder: 01_Output

  - kpi_id: ops.downtime.pct
    kpi_name: Downtime %
    measure_name: [Downtime %]
    format: 0.0%
    folder: 05_Ops
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
      - {name: Shift, type: text, nullable: true}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}

  - name: dim_product   # optional if needed
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}

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
  - name: fact_ops
    grain: line_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Planned Time Minutes, type: decimal, agg: sum}
      - {name: Run Time Minutes, type: decimal, agg: sum}
      - {name: Downtime Minutes, type: decimal, agg: sum}
      - {name: Output Units, type: decimal, agg: sum}
      - {name: Good Units, type: decimal, agg: sum}
      - {name: Scrap Units, type: decimal, agg: sum}
      - {name: Standard Rate Units Per Minute, type: decimal}
      - {name: Cause Code, type: text, nullable: true}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_ops  
- dim_date  
- dim_org  
- dim_product (optional)  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> fact_ops on DateKey  
- dim_org (1) -> fact_ops on OrgKey  
- dim_product (1) -> fact_ops on ProductKey (if modeled)  
- security_user_org filters dim_org -> cascades to fact_ops  
- Single direction; no ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month -> Week  
- Org: Plant -> Line -> Shift
- Product (if used): Category -> ProductName

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- Week -> DateKey  

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; avoid M2M.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| OEE % | ops.oee.pct | Overall effectiveness | 05_Ops | 0.0% | KPI |
| Availability % | ops.availability.pct | Uptime | 05_Ops | 0.0% | KPI |
| Performance % | ops.performance.pct | Speed vs standard | 05_Ops | 0.0% | KPI |
| Quality % | ops.quality.pct | First pass yield | 05_Ops | 0.0% | KPI |
| Throughput Units | ops.throughput.units | Output volume | 01_Output | #,0 | KPI |
| Downtime % | ops.downtime.pct | Unplanned loss | 05_Ops | 0.0% | KPI |
| Downtime Minutes | Supporting | Loss quantification | 05_Ops | #,0 | Supporting |
| Standard Output Units | Supporting | Theoretical output | 05_Ops | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Base times
Planned Time :=
    SUM ( fact_ops[Planned Time Minutes] )

/// Supporting - Run Time
Run Time :=
    SUM ( fact_ops[Run Time Minutes] )

/// Supporting - Downtime Minutes
Downtime Minutes :=
    SUM ( fact_ops[Downtime Minutes] )

/// ops.availability.pct - Uptime
Availability % :=
    DIVIDE ( [Run Time], [Planned Time] )

/// Supporting - Output
Output Units :=
    SUM ( fact_ops[Output Units] )

/// Supporting - Good Units
Good Units :=
    SUM ( fact_ops[Good Units] )

/// Supporting - Scrap Units
Scrap Units :=
    SUM ( fact_ops[Scrap Units] )

/// Supporting - Standard Output Units
Standard Output Units :=
    SUMX ( fact_ops, fact_ops[Planned Time Minutes] * fact_ops[Standard Rate Units Per Minute] )

/// ops.performance.pct - Speed vs standard
Performance % :=
    DIVIDE ( [Output Units], [Standard Output Units] )

/// ops.quality.pct - First pass yield
Quality % :=
    DIVIDE ( [Good Units], [Output Units] )

/// ops.oee.pct - Overall effectiveness
OEE % :=
    [Availability %] * [Performance %] * [Quality %]

/// ops.throughput.units - Volume
Throughput Units :=
    [Output Units]

/// ops.downtime.pct - Downtime share
Downtime % :=
    DIVIDE ( [Downtime Minutes], [Planned Time] )
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

- None required; consider masking cost/scrap EUR if added.

---

## 7. Technical Assumptions

- Standard rates maintained; downtime causes coded; shift data available where used.
- Data latency <=24h; time zone consistent.
- OneLake canonical dims used (dim_date, dim_org, security_user_org; dim_product optional).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import depending on MES connectivity; prefer DirectLake if Fabric connectors stable.  
- Incremental refresh: yes, partition by DateKey (e.g., last 12-24 months).  
- Aggregations: optional for high-frequency data (use day-level aggregates for speed).  
- Workspace/naming: `ARF - Operations` dataset/model naming per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org keys non-null in fact_ops | 100% | Y | Data Engineering |
| Time Balancing | Run Time + Downtime <= Planned Time | 100% | Y | BI |
| OEE Consistency | OEE = AxPxQ recomputes | Exact | Y | BI |
| Performance Reasonability | Performance % within 0-1.2 range | Exceptions <0.5% | Y | BI |
| Quality Reasonability | Quality % within 0-1.0 range | Exceptions <0.5% | Y | Quality |
| RLS Coverage | Users see only authorised plants/lines | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md

