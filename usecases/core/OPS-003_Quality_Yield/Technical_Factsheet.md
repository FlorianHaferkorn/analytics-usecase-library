---
id: OPS-003
factsheet_type: technical
---

# OPS-003 - Quality & Yield  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Operations
- **Technical Owner:** Quality Analytics / Ops BI Lead
- **Model ID:** ops_quality_yield
- **Source Systems:** MES/SCADA, QMS/LIMS, ERP (production/complaints), DWH
- **Business Factsheet:** usecases/core/OPS-003_Quality_Yield/Business_Factsheet.md

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

  - kpi_id: quality.fpy.pct
    kpi_name: First Pass Yield %
    measure_name: [First Pass Yield %]
    format: 0.0%
    folder: 07_Quality

  - kpi_id: quality.scrap.pct
    kpi_name: Scrap Rate %
    measure_name: [Scrap Rate %]
    format: 0.0%
    folder: 07_Quality

  - kpi_id: quality.rework.pct
    kpi_name: Rework Rate %
    measure_name: [Rework Rate %]
    format: 0.0%
    folder: 07_Quality

  - kpi_id: quality.copq.amount
    kpi_name: Cost of Poor Quality
    measure_name: [Cost of Poor Quality]
    format: EUR#,0
    folder: 07_Quality

  - kpi_id: quality.complaint.pct
    kpi_name: Complaint Rate %
    measure_name: [Complaint Rate %]
    format: 0.0%
    folder: 07_Quality

  - kpi_id: quality.defect_density
    kpi_name: Defect Density
    measure_name: [Defect Density]
    format: #,0.00
    folder: 07_Quality
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

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: ProductFamily, type: text, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}

fact:
  - name: fact_quality
    grain: line_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Total Units, type: decimal, agg: sum}
      - {name: Good Units, type: decimal, agg: sum}
      - {name: Scrap Units, type: decimal, agg: sum}
      - {name: Rework Units, type: decimal, agg: sum}
      - {name: Defect Count, type: decimal, agg: sum}

  - name: fact_quality_costs
    grain: month_product or line_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: COPQ Amount, type: currency, agg: sum}

  - name: fact_complaints
    grain: complaint
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Complaint Count, type: int, agg: sum}
      - {name: Severity, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}

  - name: fact_shipments
    grain: shipment_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Shipped Units, type: decimal, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_quality  
- fact_quality_costs  
- fact_complaints  
- fact_shipments  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> fact_quality/fact_quality_costs/fact_complaints/fact_shipments on OrgKey (where present)  
- dim_product (1) -> all product-bearing facts on ProductKey  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month -> Week  
- Org: Plant -> Line -> Shift  
- Product: ProductFamily -> Category -> ProductName

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
| First Pass Yield % | quality.fpy.pct | FPY | 07_Quality | 0.0% | KPI |
| Scrap Rate % | quality.scrap.pct | Scrap | 07_Quality | 0.0% | KPI |
| Rework Rate % | quality.rework.pct | Rework | 07_Quality | 0.0% | KPI |
| Cost of Poor Quality | quality.copq.amount | COPQ | 07_Quality | EUR#,0 | KPI |
| Complaint Rate % | quality.complaint.pct | Complaints | 07_Quality | 0.0% | KPI |
| Defect Density | quality.defect_density | Defect conc. | 07_Quality | #,0.00 | KPI |
| Total Units | Supporting | Volume base | 07_Quality | #,0 | Supporting |
| Good Units | Supporting | FPY base | 07_Quality | #,0 | Supporting |
| Scrap Units | Supporting | Waste | 07_Quality | #,0 | Supporting |
| Rework Units | Supporting | Rework | 07_Quality | #,0 | Supporting |
| Complaint Count | Supporting | Complaints | 07_Quality | #,0 | Supporting |
| Shipped Units | Supporting | Denominator for complaint rate | 07_Quality | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Volume
Total Units :=
    SUM ( fact_quality[Total Units] )

/// Supporting - Good Units
Good Units :=
    SUM ( fact_quality[Good Units] )

/// Supporting - Scrap Units
Scrap Units :=
    SUM ( fact_quality[Scrap Units] )

/// Supporting - Rework Units
Rework Units :=
    SUM ( fact_quality[Rework Units] )

/// Supporting - Defect Count
Defect Count :=
    SUM ( fact_quality[Defect Count] )

/// quality.fpy.pct - FPY
First Pass Yield % :=
    DIVIDE ( [Good Units], [Total Units] )

/// quality.scrap.pct - Scrap
Scrap Rate % :=
    DIVIDE ( [Scrap Units], [Total Units] )

/// quality.rework.pct - Rework
Rework Rate % :=
    DIVIDE ( [Rework Units], [Total Units] )

/// quality.copq.amount - COPQ
Cost of Poor Quality :=
    SUM ( fact_quality_costs[COPQ Amount] )

/// Supporting - Complaints
Complaint Count :=
    SUM ( fact_complaints[Complaint Count] )

/// Supporting - Shipped Units
Shipped Units :=
    SUM ( fact_shipments[Shipped Units] )

/// quality.complaint.pct - Complaint rate
Complaint Rate % :=
    DIVIDE ( [Complaint Count], [Shipped Units] )

/// quality.defect_density - Defects per 1k units
Defect Density :=
    DIVIDE ( [Defect Count], [Total Units] ) * 1000
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

- None required; COPQ can be sensitive-mask if client requests (TODO if needed).

---

## 7. Technical Assumptions

- Quality events captured at line/day with good/scrap/rework counts; defect codes provided.
- COPQ costs available or allocated to product/line/month; complaints linked to shipments.
- Data latency <=24h; timezone consistent.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import depending on MES/QMS connectivity; prefer DirectLake if stable.  
- Incremental refresh: yes, partition by DateKey (e.g., last 12-24 months).  
- Aggregations: optional; day-level aggregates for speed.  
- Workspace/naming: `ARF - Operations` dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in facts | 100% | Y | Data Engineering |
| FPY/Scrap/Rework Consistency | Good + Scrap + Rework = Total Units | 100% | Y | BI/Quality |
| Complaint Rate Coverage | Complaints and shipments linked by product/period | 100% linkage | Y | BI |
| COPQ Coverage | COPQ populated for priority lines/products | 100% priority scope | Y | Quality/Finance |
| RLS Coverage | Users see only authorised plants/lines | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md


