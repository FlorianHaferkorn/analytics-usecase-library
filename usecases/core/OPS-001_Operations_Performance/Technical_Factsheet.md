# OPS-001 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: OPS-001)

---

## 1. Data Contract (YAML – OPS-001 Scope)

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
      - {name: Plant, type: text}
      - {name: Line, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: UoM, type: text}

fact:
  - name: fact_production
    grain: line_shift_product
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Planned Time (min), type: number, agg: sum}
      - {name: Run Time (min), type: number, agg: sum}
      - {name: Downtime (min), type: number, agg: sum}
      - {name: Downtime Reason, type: text}
      - {name: Good Units, type: number, agg: sum}
      - {name: Scrap Units, type: number, agg: sum}
      - {name: Ideal Rate (units/min), type: number, agg: avg}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_production → `lh_ops.fact_production`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`

---

## 2. Semantic Model Requirements

### Model Name
`operations_oee`

### Tables
- fact_production  
- dim_date  
- dim_org  
- dim_product  

### Relationships
- fact_production[DateKey] → dim_date[DateKey] (1:* | single)
- fact_production[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_production[ProductKey] → dim_product[ProductKey] (1:* | single)

### Hierarchies
- Org: Region → Country → Plant → Line
- Date: Year → Quarter → Month → Date → Shift
- Product: Category → ProductName

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name        | kpi_id                       | Type        | Folder           | Format |
|---------------------|------------------------------|-------------|------------------|--------|
| OEE %               | ops.oee.pct                  | KPI         | 01_OEE           | 0.0 %  |
| Availability %      | ops.availability.pct         | KPI         | 01_OEE           | 0.0 %  |
| Performance %       | ops.performance.pct          | KPI         | 01_OEE           | 0.0 %  |
| Quality %           | ops.quality.pct              | KPI         | 01_OEE           | 0.0 %  |
| Throughput Units    | ops.throughput.units         | Supporting  | 02_Output        | #,0    |
| Downtime (min)      | ops.downtime.minutes         | Supporting  | 03_Downtime      | #,0    |

---

## 4. Measures (DAX)

```DAX
Availability % =
    DIVIDE ( SUM ( fact_production[Run Time (min)] ),
             SUM ( fact_production[Planned Time (min)] ) )
```

```DAX
Performance % =
    DIVIDE (
        SUM ( fact_production[Good Units] ),
        SUM ( fact_production[Run Time (min)] ) * AVERAGE ( fact_production[Ideal Rate (units/min)] )
    )
```

```DAX
Quality % =
    DIVIDE ( SUM ( fact_production[Good Units] ),
             SUM ( fact_production[Good Units] ) + SUM ( fact_production[Scrap Units] ) )
```

```DAX
OEE % =
    [Availability %] * [Performance %] * [Quality %]
```

```DAX
Throughput Units =
    SUM ( fact_production[Good Units] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format | Summarization | Display Folder |
|---------------|--------|---------------|----------------|
| Percentages   | 0.0 %  | None          | 01_OEE         |
| Units         | #,0    | Sum           | 02_Output      |
| Time (min)    | #,0    | Sum           | 03_Downtime    |

---

## 6. Visual Requirements (Technical)

- KPI cards: OEE, Availability, Performance, Quality.
- Trend: OEE and sub-KPIs over time.
- Pareto: Downtime by reason.
- Bar: OEE by plant/line.
- Matrix: Org → Line → Shift with KPIs; export enabled.

---

## 7. RLS / OLS

- Org-based RLS (Region/Country/Plant/Line) via dim_org.
- Optional OLS to hide downtime reasons for external users.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (36 months).  
- Avoid calculated columns; materialize downtime reason dimension if large.  
- Aggregations optional on Good Units by month/line.

---

## 9. QA & Validation

| Check Type              | Object                 | Rule                                   | Tolerance |
|-------------------------|------------------------|----------------------------------------|-----------|
| Referential Integrity   | fact → dims            | ≥ 99.9 % matched keys                  | 0.1 %     |
| OEE Consistency         | Availability×Perf×Qual | Matches OEE % within rounding          | ±0.1 pp   |
| Throughput Reconciliation | Good Units           | Matches source production records      | ±0.5 %    |
| Downtime Capture        | Downtime (min)         | Run+Down ≈ planned time                | ±1.0 %    |
