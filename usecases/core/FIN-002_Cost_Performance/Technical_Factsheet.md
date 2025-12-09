# FIN-002 – Technical Factsheet

## 0. Metadata (Mandatory)
- **Domain:** Finance / Operations
- **Technical Owner:** Ops Finance / BI Lead
- **Data Product / Model ID:** `finance_cost_performance`
- **Source Systems:** ERP (FI/CO, MM/PP), DWH
- **Use Case Business Factsheet:** `usecases/core/FIN-002_Cost_Performance/Business_Factsheet.md`

---

## 1. Model References
- **Data Contract (Domain):** `data_contracts/domains/finance.yaml`
- **Data Contract (Sources):** `data_contracts/sources/finance.yaml` (if available)
- **Semantic Model Definition:** `semantic_models/domains/finance/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`

---

## 2. Data Contract Scope (YAML – FIN-002)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}
      - {name: Quarter, type: text}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: OrgCode, type: text}
      - {name: OrgName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Plant, type: text}
      - {name: Line, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: UoM, type: text}

  - name: security_user_org   # RLS
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

fact:
  - name: fact_cost
    grain: period_product_org
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Units, type: number, agg: sum}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Material Cost Amount, type: currency, agg: sum}
      - {name: Labor Cost Amount, type: currency, agg: sum}
      - {name: Overhead Cost Amount, type: currency, agg: sum}
      - {name: Energy Cost Amount, type: currency, agg: sum}
      - {name: OpEx Amount, type: currency, agg: sum}
      - {name: Plan Unit Cost, type: currency, agg: avg}
      - {name: Plan OpEx Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_cost → `lh_finance.fact_cost`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`
- security_user_org → `lh_security.security_user_org`

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_cost  
- dim_date  
- dim_org  
- dim_product  
- security_user_org (RLS)

### 3.2 Relationships
- fact_cost[DateKey] → dim_date[DateKey] (1:* | single)
- fact_cost[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_cost[ProductKey] → dim_product[ProductKey] (1:* | single)

### 3.3 Hierarchies
- Org: Region → Country → Plant → Line → OrgName
- Product: Category → Subcategory → ProductName
- Date: Year → Quarter → Month → Date

### 3.4 Sort-by Columns
- Month → MonthNumber  
- ProductName → ProductCode  
- OrgName → OrgCode  

### 3.5 Modeling Rules
- No calculated columns; business logic in measures/ETL.
- Default summarization set; technical fields hidden.
- Display folders: 01_Cost, 02_Margin, 03_OpEx, 04_Productivity.

---

## 4. Measure Inventory

| Measure Name           | KPI ID / Supporting          | Purpose        | Display Folder     | Format    | Type |
|------------------------|------------------------------|----------------|--------------------|-----------|------|
| Unit Cost              | cost.unit.amount             | Cost efficiency| 01_Cost            | €#,0.00   | KPI  |
| Unit Cost vs Plan %    | cost.unit.vs_plan.pct        | Gap to plan    | 01_Cost            | 0.0 %     | KPI  |
| COGS % of Sales        | margin.cogs.pct              | Margin quality | 02_Margin          | 0.0 %     | KPI  |
| Material Cost %        | cost.material.pct            | Material share | 01_Cost            | 0.0 %     | KPI  |
| Labor Cost %           | cost.labor.pct               | Labor share    | 01_Cost            | 0.0 %     | Supporting |
| Overhead Cost %        | cost.overhead.pct            | Overhead share | 01_Cost            | 0.0 %     | Supporting |
| OpEx vs Plan %         | cost.opex.vs_plan.pct        | OpEx control   | 03_OpEx            | 0.0 %     | KPI  |
| Labor Productivity %   | ops.labor.productivity.pct   | Productivity   | 04_Productivity    | 0.0 %     | KPI  |

---

## 5. Measures (DAX)

```DAX
/// cost.unit.amount – Cost per unit
Unit Cost =
    DIVIDE ( [Total Cost Amount], [Units] )
```

```DAX
/// Supporting – Total cost
Total Cost Amount =
    [Material Cost Amount] +
    [Labor Cost Amount] +
    [Overhead Cost Amount] +
    [Energy Cost Amount]
```

```DAX
/// cost.unit.vs_plan.pct – Gap to plan
Unit Cost vs Plan % =
    DIVIDE ( [Unit Cost] - AVERAGE ( fact_cost[Plan Unit Cost] ),
             AVERAGE ( fact_cost[Plan Unit Cost] ) )
```

```DAX
/// margin.cogs.pct – Margin quality
COGS % of Sales =
    DIVIDE ( [Total Cost Amount], [Net Sales Amount] )
```

```DAX
/// cost.opex.vs_plan.pct – OpEx control
OpEx vs Plan % =
    DIVIDE ( SUM ( fact_cost[OpEx Amount] ) - SUM ( fact_cost[Plan OpEx Amount] ),
             SUM ( fact_cost[Plan OpEx Amount] ) )
```

```DAX
/// ops.labor.productivity.pct – Productivity
Labor Productivity % =
    DIVIDE ( [Units], SUM ( fact_cost[Labor Cost Amount] ) )
```

---

## 6. Defaults & Formatting

| Field/Measure     | Format   | Summarization | Display Folder   |
|-------------------|----------|---------------|------------------|
| Amounts           | €#,0.00  | Sum           | Cost / Margin    |
| Percentages       | 0.0 %    | None          | KPI folders      |
| Units             | #,0      | Sum           | Volume           |

---

## 7. Visual Requirements

| Visual Name           | Type      | X-Axis / Category | Y-Axis / Value                                  | Segment / Legend | Filters / Defaults |
|-----------------------|-----------|-------------------|-------------------------------------------------|------------------|--------------------|
| Unit Cost Trend       | Line      | dim_date[Month]   | [Unit Cost], [Unit Cost vs Plan %]              | Plant/Line/BU    | Last 12–24M        |
| Cost Variance Bridge  | Waterfall | Drivers (Material, Labor, Energy, Overhead, OpEx) | Δ Cost vs Plan | n/a               | Period selector    |
| Cost by Plant/Line    | Bar       | dim_org[Plant]/[Line] | [Unit Cost], [Material %, Labor %, Overhead %] | Region/BU        | Top/Bottom N       |
| Detail Matrix         | Matrix    | Plant → Line → Product | Unit Cost, Material %, Labor %, Overhead %, OpEx | Region/BU    | Export enabled     |

---

## 8. RLS / OLS Rules

### 8.1 RLS Pattern
Org-based RLS via security table:
```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

### 8.2 OLS (optional)
- Hide detailed cost components for non-finance roles; show only high-level KPIs.

---

## 9. Performance & Refresh

- Storage: Import or Direct Lake.  
- Incremental refresh on DateKey (36 months history).  
- No calculated columns; hide technical fields.  
- Consider aggregations for heavy fact_cost tables.

---

## 10. QA & Validation Rules

| Check Name            | Object                    | Rule                                      | Tolerance | Automated | Owner          |
|-----------------------|---------------------------|-------------------------------------------|-----------|-----------|----------------|
| RI Check              | fact_cost → dims          | ≥ 99.9 % matched keys                     | 0.1 %     | Y         | Data Engineer  |
| Cost Reconciliation   | Total Cost Amount         | Matches source                            | ±0.5 %    | Y         | Controller     |
| Plan Reconciliation   | Plan Unit Cost / OpEx     | Matches planning system                   | ±0.5 %    | Y         | Controller     |
| Variance Consistency  | Σ components = variance   | Components reconcile to total variance    | ±1.0 %    | Y         | BI Dev         |
