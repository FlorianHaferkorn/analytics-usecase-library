# XD-002 — Resource Utilization  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Experience / Service
- **Technical Owner:** Workforce Management / Service Ops BI Lead
- **Model ID:** experience_resource_utilization
- **Source Systems:** WFM/Telephony/CCaaS, CRM/Service Desk, DWH
- **Business Factsheet:** usecases/core/XD-002_Resource_Utilization/Business_Factsheet.md

---

## 1. Model References
- **Domain Data Contract:** data_contracts/domains/experience.yaml
- **Source Data Contract:** data_contracts/sources/experience.yaml (if present)
- **Semantic Model Definition:** semantic_models/domains/experience/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** framework/kpi_catalog/domain_measure_dictionary.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs → Measure Mapping (Mandatory)
```yaml
kpi_to_measure_mapping:
  - kpi_id: res.utilization.pct
    kpi_name: Utilization %
    measure_name: [Utilization %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: res.occupancy.pct
    kpi_name: Occupancy %
    measure_name: [Occupancy %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: svc.sla.attainment.pct
    kpi_name: SLA Attainment %
    measure_name: [SLA Attainment %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: res.overtime.pct
    kpi_name: Overtime %
    measure_name: [Overtime %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: res.shrinkage.pct
    kpi_name: Shrinkage %
    measure_name: [Shrinkage %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: svc.backlog.count
    kpi_name: Backlog Count
    measure_name: [Backlog Count]
    format: #,0
    folder: 11_Service
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
      - {name: Region, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}
      - {name: Queue, type: text, nullable: true}
      - {name: Agent Group, type: text, nullable: true}

  - name: dim_queue    # optional
    columns:
      - {name: QueueKey, type: int, role: key}
      - {name: QueueName, type: text}
      - {name: Channel, type: text, nullable: true}
      - {name: Region, type: text, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_wfm
    grain: agent_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: QueueKey, type: int, ref: dim_queue, nullable: true}
      - {name: Work Time Minutes, type: decimal, agg: sum}
      - {name: Paid Time Minutes, type: decimal, agg: sum}
      - {name: Talk Time Minutes, type: decimal, agg: sum}
      - {name: Wrap Time Minutes, type: decimal, agg: sum}
      - {name: Idle Time Minutes, type: decimal, agg: sum}
      - {name: Overtime Minutes, type: decimal, agg: sum, nullable: true}
      - {name: Shrinkage Minutes, type: decimal, agg: sum, nullable: true}

  - name: fact_cases
    grain: case
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: QueueKey, type: int, ref: dim_queue, nullable: true}
      - {name: SLA Met Flag, type: boolean}
      - {name: Backlog Flag, type: boolean}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables
- fact_wfm  
- fact_cases  
- dim_date  
- dim_org  
- dim_queue (optional)  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)
- dim_date (1) → fact_wfm/fact_cases on DateKey  
- dim_org (1) → fact_wfm/fact_cases on OrgKey  
- dim_queue (1) → fact_wfm/fact_cases on QueueKey (if used)  
- security_user_org filters dim_org → cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies
- Date: Year → Quarter → Month → Week  
- Org: Region → Channel → Queue → Agent Group

### 4.4 Sort-by Columns
- Month → MonthNumber  
- QueueName → QueueKey

### 4.5 Modeling Constraints
- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; avoid M2M.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory
| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Utilization % | res.utilization.pct | Productive vs paid | 11_Service | 0.0% | KPI |
| Occupancy % | res.occupancy.pct | Active vs available | 11_Service | 0.0% | KPI |
| SLA Attainment % | svc.sla.attainment.pct | Service level | 11_Service | 0.0% | KPI |
| Overtime % | res.overtime.pct | Cost/fatigue | 11_Service | 0.0% | KPI |
| Shrinkage % | res.shrinkage.pct | Non-productive | 11_Service | 0.0% | KPI |
| Backlog Count | svc.backlog.count | Workload | 11_Service | #,0 | KPI |
| Work Time Minutes | Supporting | Productive time | 11_Service | #,0.0 | Supporting |
| Paid Time Minutes | Supporting | Denominator | 11_Service | #,0.0 | Supporting |
| Talk+Wrap Minutes | Supporting | Active time | 11_Service | #,0.0 | Supporting |
| Idle Time Minutes | Supporting | Idle | 11_Service | #,0.0 | Supporting |
| Overtime Minutes | Supporting | Overtime | 11_Service | #,0.0 | Supporting |
| Shrinkage Minutes | Supporting | Shrinkage | 11_Service | #,0.0 | Supporting |
| Backlog Cases | Supporting | Backlog | 11_Service | #,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// Supporting — Time components
Work Time Minutes :=
    SUM ( fact_wfm[Work Time Minutes] )

Paid Time Minutes :=
    SUM ( fact_wfm[Paid Time Minutes] )

Talk Wrap Minutes :=
    SUM ( fact_wfm[Talk Time Minutes] ) + SUM ( fact_wfm[Wrap Time Minutes] )

Idle Time Minutes :=
    SUM ( fact_wfm[Idle Time Minutes] )

Overtime Minutes :=
    SUM ( fact_wfm[Overtime Minutes] )

Shrinkage Minutes :=
    SUM ( fact_wfm[Shrinkage Minutes] )

Backlog Cases :=
    CALCULATE ( COUNTROWS ( fact_cases ), fact_cases[Backlog Flag] = TRUE )

/// res.utilization.pct — Utilization
Utilization % :=
    DIVIDE ( [Work Time Minutes], [Paid Time Minutes] )

/// res.occupancy.pct — Occupancy
Occupancy % :=
    DIVIDE ( [Talk Wrap Minutes], [Talk Wrap Minutes] + [Idle Time Minutes] )

/// svc.sla.attainment.pct — SLA (reuse from cases)
Cases SLA Met :=
    CALCULATE ( COUNTROWS ( fact_cases ), fact_cases[SLA Met Flag] = TRUE )

Cases Resolved :=
    COUNTROWS ( fact_cases )

SLA Attainment % :=
    DIVIDE ( [Cases SLA Met], [Cases Resolved] )

/// res.overtime.pct — Overtime
Overtime % :=
    DIVIDE ( [Overtime Minutes], [Paid Time Minutes] )

/// res.shrinkage.pct — Shrinkage
Shrinkage % :=
    DIVIDE ( [Shrinkage Minutes], [Paid Time Minutes] )

/// svc.backlog.count — Backlog
Backlog Count :=
    [Backlog Cases]
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
- None required; consider masking agent-level details if client requires (TODO).

---

## 7. Technical Assumptions
- WFM data contains work/idle/wrap, paid time, overtime, shrinkage at agent/queue level.
- SLA/backlog flags available from cases; queue/channel mapping consistent.
- Data latency ≤24h; OneLake canonical dims used (dim_date, dim_org, security_user_org).

---

## 8. Deployment Requirements
- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, by Month/Week.  
- Aggregations: optional for high-volume agent/day data.  
- Workspace/naming: `ARF – Experience` dataset/model per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org keys non-null in facts | 100% | Y | Data Engineering |
| Utilization/Occupancy Validity | No div-by-zero; within plausible bands | 0 errors | Y | BI |
| Overtime/Shrinkage Coverage | Fields populated where applicable | 100% | Y | WFM |
| SLA Coverage | SLA flags populated for cases | 100% | Y | Service Ops |
| RLS Coverage | Users see only authorised regions/channels/queues | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |
