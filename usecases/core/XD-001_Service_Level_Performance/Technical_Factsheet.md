# XD-001 — Service Level Performance  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Experience / Service
- **Technical Owner:** Service Ops / CX BI Lead
- **Model ID:** experience_service_level
- **Source Systems:** CRM/Service Desk, Telephony/CCaaS, Survey (NPS), DWH
- **Business Factsheet:** usecases/core/XD-001_Service_Level_Performance/Business_Factsheet.md

---

## 1. Model References
- **Domain Data Contract:** data_contracts/domains/experience.yaml
- **Source Data Contract:** data_contracts/sources/experience.yaml (if present)
- **Semantic Model Definition:** semantic_models/domains/experience/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/KPI_Catalog_Service.md
- **Measure Dictionary:** semantic_models/domains/Service/Measure_Dictionary_Service.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs → Measure Mapping (Mandatory)
```yaml
kpi_to_measure_mapping:
  - kpi_id: svc.sla.attainment.pct
    kpi_name: SLA Attainment %
    measure_name: [SLA Attainment %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: svc.fcr.pct
    kpi_name: First Contact Resolution %
    measure_name: [FCR %]
    format: 0.0%
    folder: 11_Service
  - kpi_id: svc.aht.minutes
    kpi_name: Average Handling Time (minutes)
    measure_name: [AHT Minutes]
    format: 0.0
    folder: 11_Service
  - kpi_id: svc.backlog.count
    kpi_name: Backlog Count
    measure_name: [Backlog Count]
    format: #,0
    folder: 11_Service
  - kpi_id: svc.nps.index
    kpi_name: NPS Index
    measure_name: [NPS Index]
    format: #,0
    folder: 11_Service
  - kpi_id: svc.escalation.pct
    kpi_name: Escalation %
    measure_name: [Escalation %]
    format: 0.0%
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

  - name: dim_queue    # optional if separate
    columns:
      - {name: QueueKey, type: int, role: key}
      - {name: QueueName, type: text}
      - {name: Channel, type: text, nullable: true}
      - {name: Region, type: text, nullable: true}

  - name: dim_issue    # optional
    columns:
      - {name: IssueKey, type: int, role: key}
      - {name: IssueType, type: text}
      - {name: Severity, type: text, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_cases
    grain: case
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: QueueKey, type: int, ref: dim_queue, nullable: true}
      - {name: IssueKey, type: int, ref: dim_issue, nullable: true}
      - {name: SLA Met Flag, type: boolean}
      - {name: FCR Flag, type: boolean}
      - {name: Handle Time Minutes, type: decimal}
      - {name: Escalation Flag, type: boolean}
      - {name: Backlog Flag, type: boolean}
      - {name: Open Case Flag, type: boolean}

  - name: fact_nps
    grain: survey
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: QueueKey, type: int, ref: dim_queue, nullable: true}
      - {name: NPS Score, type: int}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables
- fact_cases  
- fact_nps  
- dim_date  
- dim_org  
- dim_queue (optional)  
- dim_issue (optional)  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)
- dim_date (1) → fact_cases/fact_nps on DateKey  
- dim_org (1) → fact_cases/fact_nps on OrgKey  
- dim_queue (1) → fact_cases/fact_nps on QueueKey (if used)  
- dim_issue (1) → fact_cases on IssueKey (if used)  
- security_user_org filters dim_org → cascades to facts; use channel/region as needed.  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies
- Date: Year → Quarter → Month → Week  
- Org: Region → Channel → Queue  
- Queue: Channel → QueueName (if separate)

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
| SLA Attainment % | svc.sla.attainment.pct | Service level | 11_Service | 0.0% | KPI |
| FCR % | svc.fcr.pct | Quality/Efficiency | 11_Service | 0.0% | KPI |
| AHT Minutes | svc.aht.minutes | Efficiency | 11_Service | 0.0 | KPI |
| Backlog Count | svc.backlog.count | Workload | 11_Service | #,0 | KPI |
| NPS Index | svc.nps.index | Experience | 11_Service | #,0 | KPI |
| Escalation % | svc.escalation.pct | Quality/risk | 11_Service | 0.0% | KPI |
| Cases Resolved | Supporting | SLA/FCR denominators | 11_Service | #,0 | Supporting |
| Escalated Cases | Supporting | Escalation numerator | 11_Service | #,0 | Supporting |
| Backlog Cases | Supporting | Backlog count | 11_Service | #,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// Supporting — Counts
Cases Resolved :=
    COUNTROWS ( fact_cases )

Cases SLA Met :=
    CALCULATE ( COUNTROWS ( fact_cases ), fact_cases[SLA Met Flag] = TRUE )

Cases FCR :=
    CALCULATE ( COUNTROWS ( fact_cases ), fact_cases[FCR Flag] = TRUE )

Escalated Cases :=
    CALCULATE ( COUNTROWS ( fact_cases ), fact_cases[Escalation Flag] = TRUE )

Backlog Cases :=
    CALCULATE ( COUNTROWS ( fact_cases ), fact_cases[Backlog Flag] = TRUE )

Total Handle Time Minutes :=
    SUM ( fact_cases[Handle Time Minutes] )

/// svc.sla.attainment.pct — SLA
SLA Attainment % :=
    DIVIDE ( [Cases SLA Met], [Cases Resolved] )

/// svc.fcr.pct — FCR
FCR % :=
    DIVIDE ( [Cases FCR], [Cases Resolved] )

/// svc.aht.minutes — AHT
AHT Minutes :=
    DIVIDE ( [Total Handle Time Minutes], [Cases Resolved] )

/// svc.backlog.count — Backlog
Backlog Count :=
    [Backlog Cases]

/// svc.escalation.pct — Escalations
Escalation % :=
    DIVIDE ( [Escalated Cases], [Cases Resolved] )

/// svc.nps.index — NPS
NPS Index :=
    AVERAGE ( fact_nps[NPS Score] )
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
- None required; consider masking NPS verbatims/sensitive attributes if added (TODO per client).

---

## 7. Technical Assumptions
- SLA, FCR, AHT flags/times captured; backlog/escalation flags available.
- NPS survey data aligned by channel/period; queue/channel mapping consistent.
- Data latency ≤24h; OneLake canonical dims (dim_date, dim_org, security_user_org) used.

---

## 8. Deployment Requirements
- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, by Month/Week.  
- Aggregations: optional for high-volume case data.  
- Workspace/naming: `ARF – Experience` dataset/model per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org keys non-null in facts | 100% | Y | Data Engineering |
| SLA/FCR Integrity | SLA/FCR flags populated | 100% of cases | Y | Service Ops |
| AHT Validity | Handle time >0 and within plausible bounds | Exceptions <0.5% | Y | BI |
| NPS Coverage | NPS scores present for survey periods | 100% in-scope surveys | Y | CX |
| RLS Coverage | Users see only authorised regions/channels/queues | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md
