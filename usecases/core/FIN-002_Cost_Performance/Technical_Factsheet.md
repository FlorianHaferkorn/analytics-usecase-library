---
id: FIN-002
factsheet_type: technical
---

# FIN-002 - Cost Performance  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Finance / Operations
- **Technical Owner:** Finance BI Lead / Ops Finance
- **Model ID:** finance_cost_performance
- **Source Systems:** ERP (FI/CO), MES/production, DWH
- **Business Factsheet:** usecases/core/FIN-002_Cost_Performance/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** data_contracts/domains/finance.yaml
- **Source Data Contract:** data_contracts/sources/finance.yaml (if present)
- **Semantic Model Definition:** semantic_models/domains/finance/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** semantic_models/domains/Finance/Measure_Dictionary_Finance.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: cost.unit.amount
    kpi_name: Unit Cost Amount
    measure_name: [Unit Cost Amount]
    format: EUR#,0.00
    folder: 10_Finance

  - kpi_id: margin.cogs.pct
    kpi_name: COGS % of Sales
    measure_name: [COGS % of Sales]
    format: 0.0%
    folder: 10_Finance

  - kpi_id: cost.opex.vs_plan.pct
    kpi_name: OpEx vs Plan %
    measure_name: [OpEx vs Plan %]
    format: 0.0%
    folder: 10_Finance

  - kpi_id: cost.material.pct
    kpi_name: Material Cost %
    measure_name: [Material Cost %]
    format: 0.0%
    folder: 10_Finance

  - kpi_id: ops.labor.productivity.pct
    kpi_name: Labor Productivity %
    measure_name: [Labor Productivity %]
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

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: Entity, type: text}
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}
      - {name: Region, type: text, nullable: true}

  - name: dim_product
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

fact:
  - name: fact_finance
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Material Cost Amount, type: currency, agg: sum, nullable: true}
      - {name: OpEx Amount, type: currency, agg: sum, nullable: true}
      - {name: Plan OpEx Amount, type: currency, agg: sum, nullable: true}

  - name: fact_cost
    grain: plant_line_product_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Material Cost Amount, type: currency, agg: sum, nullable: true}
      - {name: Overhead Amount, type: currency, agg: sum, nullable: true}

  - name: fact_output
    grain: plant_line_product_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Output Units, type: decimal, agg: sum}

  - name: fact_labor
    grain: plant_line_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Labor Hours, type: decimal, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_finance  
- fact_cost  
- fact_output  
- fact_labor  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> all facts on OrgKey  
- dim_product (1) -> fact_cost/fact_output on ProductKey  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month  
- Org: Entity -> Plant -> Line  
- Product: Category -> ProductName

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
| Unit Cost Amount | cost.unit.amount | Cost efficiency | 10_Finance | EUR#,0.00 | KPI |
| COGS % of Sales | margin.cogs.pct | Margin impact | 10_Finance | 0.0% | KPI |
| OpEx vs Plan % | cost.opex.vs_plan.pct | Overhead control | 10_Finance | 0.0% | KPI |
| Material Cost % | cost.material.pct | Material efficiency | 10_Finance | 0.0% | KPI |
| Labor Productivity % | ops.labor.productivity.pct | Labor efficiency | 05_Ops | 0.0% | KPI |
| Net Sales Amount | Supporting | Revenue base | 10_Finance | EUR#,0 | Supporting |
| COGS Amount | Supporting | Cost base | 10_Finance | EUR#,0 | Supporting |
| OpEx Amount | Supporting | Overhead | 10_Finance | EUR#,0 | Supporting |
| Plan OpEx Amount | Supporting | Plan | 10_Finance | EUR#,0 | Supporting |
| Output Units | Supporting | Unit cost denominator | 10_Finance | #,0 | Supporting |
| Material Cost Amount | Supporting | Material share | 10_Finance | EUR#,0 | Supporting |
| Labor Hours | Supporting | Productivity denominator | 05_Ops | #,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// Supporting - Bases
Net Sales Amount :=
    SUM ( fact_finance[Net Sales Amount] )

/// Supporting - COGS Amount
COGS Amount :=
    SUM ( fact_finance[COGS Amount] )

/// Supporting - Material Cost Amount
Material Cost Amount :=
    SUM ( fact_finance[Material Cost Amount] )

/// Supporting - OpEx Amount
OpEx Amount :=
    SUM ( fact_finance[OpEx Amount] )

/// Supporting - Plan OpEx Amount
Plan OpEx Amount :=
    SUM ( fact_finance[Plan OpEx Amount] )

/// Supporting - Output Units
Output Units :=
    SUM ( fact_output[Output Units] )

/// Supporting - Labor Hours
Labor Hours :=
    SUM ( fact_labor[Labor Hours] )

/// cost.unit.amount - Unit cost
Unit Cost Amount :=
    DIVIDE ( SUM ( fact_cost[COGS Amount] ), [Output Units] )

/// margin.cogs.pct - COGS share
COGS % of Sales :=
    DIVIDE ( [COGS Amount], [Net Sales Amount] )

/// cost.opex.vs_plan.pct - OpEx variance
OpEx vs Plan % :=
    DIVIDE ( [OpEx Amount] - [Plan OpEx Amount], [Plan OpEx Amount] )

/// cost.material.pct - Material share
Material Cost % :=
    DIVIDE ( [Material Cost Amount], [Net Sales Amount] )

/// ops.labor.productivity.pct - Labor efficiency (simple)
Labor Productivity % :=
    DIVIDE ( [Output Units], [Labor Hours] )
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

- None required; cost details could be masked by role if needed (TODO).

---

## 7. Technical Assumptions

- Plan vs actual available for OpEx and unit cost; material/labor/overhead separated.
- Output units provided for denominator; labor hours available for productivity.
- Data latency <=24h; currency EUR.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, by Month (and plant_line granularity if needed).  
- Aggregations: optional; monthly aggregates sufficient for most visuals.  
- Workspace/naming: `ARF - Finance` dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product keys non-null in facts | 100% | Y | Data Engineering |
| Unit Cost Validity | No div-by-zero; unit cost within plausible range | 0 errors | Y | BI/Finance |
| OpEx Plan Coverage | Plan OpEx populated for plan periods | 100% plan scope | Y | Finance |
| Material Share Integrity | Material cost populated where applicable | 100% | Y | Finance |
| RLS Coverage | Users see only authorised entities/plants/lines | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md


