# OPS-003 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/operations.yaml`
- **Semantic Model Definition:**  
  `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: OPS-003)

---

## 1. Data Contract (YAML – OPS-003 Scope)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}
      - {name: Shift, type: text}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
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

  - name: dim_defect
    columns:
      - {name: DefectKey, type: int, role: key}
      - {name: DefectCategory, type: text}
      - {name: DefectReason, type: text}

fact:
  - name: fact_quality
    grain: line_shift_product
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: DefectKey, type: int, ref: dim_defect, nullable: true}
      - {name: Good Units, type: number, agg: sum}
      - {name: Rework Units, type: number, agg: sum}
      - {name: Scrap Units, type: number, agg: sum}
      - {name: Scrap Cost Amount, type: currency, agg: sum}
      - {name: Rework Cost Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_quality → `lh_ops.fact_quality`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`
- dim_defect → `lh_ops.dim_defect`

---

## 2. Semantic Model Requirements

### Model Name
`operations_quality_yield`

### Tables
- fact_quality  
- dim_date  
- dim_org  
- dim_product  
- dim_defect  

### Relationships
- fact_quality[DateKey] → dim_date[DateKey] (1:* | single)
- fact_quality[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_quality[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_quality[DefectKey] → dim_defect[DefectKey] (1:* | single, optional)

### Hierarchies
- Org: Region → Country → Plant → Line
- Product: Category → Subcategory → ProductName
- Date: Year → Quarter → Month → Date → Shift
- Defect: Category → Reason

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name            | kpi_id                         | Type        | Folder          | Format |
|-------------------------|--------------------------------|-------------|-----------------|--------|
| First Pass Yield %      | quality.fpy.pct                | KPI         | 01_Quality      | 0.0 %  |
| Scrap Rate %            | quality.scrap.pct              | KPI         | 01_Quality      | 0.0 %  |
| Rework Rate %           | quality.rework.pct             | KPI         | 01_Quality      | 0.0 %  |
| Cost of Poor Quality    | quality.copq.amount            | KPI         | 02_Cost         | €#,0.00|
| Complaint Rate %        | quality.complaint.pct          | KPI         | 03_Complaints   | 0.0 %  |
| Scrap Units             | quality.scrap.units            | Supporting  | 01_Quality      | #,0    |

---

## 4. Measures (DAX)

```DAX
First Pass Yield % =
    DIVIDE (
        SUM ( fact_quality[Good Units] ),
        SUM ( fact_quality[Good Units] ) +
        SUM ( fact_quality[Rework Units] ) +
        SUM ( fact_quality[Scrap Units] )
    )
```

```DAX
Scrap Rate % =
    DIVIDE ( SUM ( fact_quality[Scrap Units] ),
             SUM ( fact_quality[Good Units] ) + SUM ( fact_quality[Scrap Units] ) + SUM ( fact_quality[Rework Units] ) )
```

```DAX
Rework Rate % =
    DIVIDE ( SUM ( fact_quality[Rework Units] ),
             SUM ( fact_quality[Good Units] ) + SUM ( fact_quality[Scrap Units] ) + SUM ( fact_quality[Rework Units] ) )
```

```DAX
Cost of Poor Quality =
    SUM ( fact_quality[Scrap Cost Amount] ) +
    SUM ( fact_quality[Rework Cost Amount] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder |
|---------------|----------|---------------|----------------|
| Percentages   | 0.0 %    | None          | Quality/Complaints |
| Amounts       | €#,0.00  | Sum           | Cost           |
| Units         | #,0      | Sum           | Quality        |

---

## 6. Visual Requirements (Technical)

- KPI cards: FPY, Scrap %, Rework %, COPQ, Complaint Rate.
- Pareto: Scrap/Defect by category.
- Bar: FPY by line/product/shift.
- Trend: FPY and Scrap over time.
- Matrix: Org → Line → Product → Shift with KPIs; export enabled.

---

## 7. RLS / OLS

- Org-based RLS (Region/Country/Plant/Line).  
- Optional OLS to hide defect reasons for external partners.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (36 months).  
- If fact_quality large, aggregate long history by month/product/line; keep 12-month detail.  
- Hide technical columns; avoid calculated columns.

---

## 9. QA & Validation

| Check Type              | Object                   | Rule                                     | Tolerance |
|-------------------------|--------------------------|------------------------------------------|-----------|
| Referential Integrity   | fact → dims              | ≥ 99.9 % matched keys                    | 0.1 %     |
| FPY Calculation         | FPY recomputes correctly | Good + Rework + Scrap = total units      | ±0.1 %    |
| COPQ Reconciliation     | Scrap+Rework cost        | Matches source cost records              | ±0.5 %    |
| Defect Coding Completeness | DefectKey coverage    | % of rows with valid defect category     | >95 %     |
