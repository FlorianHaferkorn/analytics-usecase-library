# FIN-002 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/finance.yaml`
- **Semantic Model Definition:**  
  `semantic_models/domains/finance/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: FIN-002)

---

## 1. Data Contract (YAML – FIN-002 Scope)

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

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: UoM, type: text}

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

---

## 2. Semantic Model Requirements

### Model Name
`finance_cost_performance`

### Tables
- fact_cost  
- dim_date  
- dim_org  
- dim_product  

### Relationships
- fact_cost[DateKey] → dim_date[DateKey] (1:* | single)
- fact_cost[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_cost[ProductKey] → dim_product[ProductKey] (1:* | single)

### Hierarchies
- Org: Region → Country → Plant → OrgName
- Product: Category → Subcategory → ProductName
- Date: Year → Quarter → Month → Date

### Sort-by Columns
- Month → MonthNumber  
- ProductName → ProductCode  
- OrgName → OrgCode  

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name           | kpi_id                         | Type        | Folder              | Format    |
|------------------------|--------------------------------|-------------|---------------------|-----------|
| Unit Cost              | cost.unit.amount               | KPI        | 01_Cost             | €#,0.00   |
| Unit Cost vs Plan %    | cost.unit.vs_plan.pct          | KPI        | 01_Cost             | 0.0 %     |
| COGS % of Sales        | margin.cogs.pct                | KPI        | 02_Margin           | 0.0 %     |
| Material Cost %        | cost.material.pct              | KPI        | 01_Cost             | 0.0 %     |
| Labor Cost %           | cost.labor.pct                 | Supporting | 01_Cost             | 0.0 %     |
| Overhead Cost %        | cost.overhead.pct              | Supporting | 01_Cost             | 0.0 %     |
| OpEx vs Plan %         | cost.opex.vs_plan.pct          | KPI        | 03_OpEx             | 0.0 %     |
| Labor Productivity %   | ops.labor.productivity.pct     | KPI        | 04_Productivity     | 0.0 %     |

---

## 4. Measures (DAX)

```DAX
Unit Cost =
    DIVIDE ( [Total Cost Amount], [Units] )
```

```DAX
Total Cost Amount =
    [Material Cost Amount] +
    [Labor Cost Amount] +
    [Overhead Cost Amount] +
    [Energy Cost Amount]
```

```DAX
Unit Cost vs Plan % =
    DIVIDE ( [Unit Cost] - AVERAGE ( fact_cost[Plan Unit Cost] ),
             AVERAGE ( fact_cost[Plan Unit Cost] ) )
```

```DAX
COGS % of Sales =
    DIVIDE ( [Total Cost Amount], [Net Sales Amount] )
```

```DAX
OpEx vs Plan % =
    DIVIDE ( SUM ( fact_cost[OpEx Amount] ) - SUM ( fact_cost[Plan OpEx Amount] ),
             SUM ( fact_cost[Plan OpEx Amount] ) )
```

```DAX
Labor Productivity % =
    DIVIDE ( [Units], SUM ( fact_cost[Labor Cost Amount] ) )
```

---

## 5. Defaults & Formatting

| Field/Measure     | Format   | Summarization | Display Folder   |
|-------------------|----------|---------------|------------------|
| Amounts           | €#,0.00  | Sum           | Cost / Margin    |
| Percentages       | 0.0 %    | None          | KPI folders      |
| Units             | #,0      | Sum           | Volume           |

---

## 6. Visual Requirements (Technical)

- KPI cards: Unit Cost, Unit Cost vs Plan %, COGS % of Sales, OpEx vs Plan %, Labor Productivity %.
- Waterfall: Cost variance vs Plan by component (material, labor, energy, overhead, OpEx).
- Bar: Unit Cost by plant/line/product.
- Line: OpEx vs Plan trend; Unit Cost trend.
- Matrix: Org → Product with cost components and variance; export enabled.

---

## 7. RLS / OLS

- Standard Org-based RLS via dim_org region/country/plant.
- Optional OLS to hide detailed cost components for non-finance roles.

---

## 8. Performance & Refresh

- Storage: Import or Direct Lake.  
- Incremental refresh on DateKey (36 months history).  
- No calculated columns; hide technical fields.  
- Partitions by month; ensure materialized views for heavy fact_cost.

---

## 9. QA & Validation

| Check Type            | Object                    | Rule                                    | Tolerance |
|-----------------------|---------------------------|-----------------------------------------|-----------|
| Referential Integrity | fact_cost → dims          | ≥ 99.9 % matched keys                   | 0.1 %     |
| Cost Reconciliation   | Total Cost Amount         | Matches source                          | ±0.5 %    |
| Plan Reconciliation   | Plan Unit Cost / OpEx     | Matches planning system                 | ±0.5 %    |
| Variance Consistency  | Σ components = variance   | Components reconcile to total variance  | ±1.0 %    |
