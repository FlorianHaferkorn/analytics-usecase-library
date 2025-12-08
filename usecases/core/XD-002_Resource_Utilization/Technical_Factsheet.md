# XD-002 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: XD-002)

---

## 1. Data Contract (YAML – XD-002 Scope)

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
      - {name: Site, type: text}
      - {name: Team, type: text}

  - name: dim_resource
    columns:
      - {name: ResourceKey, type: int, role: key}
      - {name: ResourceId, type: text}
      - {name: ResourceType, type: text}   # person / asset
      - {name: Role, type: text}
      - {name: SkillGroup, type: text}

fact:
  - name: fact_time
    grain: resource_shift
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ResourceKey, type: int, ref: dim_resource}
      - {name: Available Hours, type: number, agg: sum}
      - {name: Productive Hours, type: number, agg: sum}
      - {name: Overtime Hours, type: number, agg: sum}
      - {name: Idle Hours, type: number, agg: sum}
      - {name: Schedule Adherence Flag, type: boolean}

  - name: fact_output
    grain: resource_shift_output
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ResourceKey, type: int, ref: dim_resource}
      - {name: Output Units, type: number, agg: sum}
      - {name: Output UoM, type: text}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_time → `lh_ops.fact_time`
- fact_output → `lh_ops.fact_output`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_resource → `lh_ops.dim_resource`

---

## 2. Semantic Model Requirements

### Model Name
`resource_utilization`

### Tables
- fact_time  
- fact_output  
- dim_date  
- dim_org  
- dim_resource  

### Relationships
- fact_time[DateKey] → dim_date[DateKey] (1:* | single)
- fact_time[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_time[ResourceKey] → dim_resource[ResourceKey] (1:* | single)
- fact_output joins similarly to date/org/resource.

### Hierarchies
- Org: Region → Country → Site → Team
- Resource: Type → Role → Resource
- Date: Year → Quarter → Month → Date → Shift

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name           | kpi_id                          | Type        | Folder            | Format |
|------------------------|---------------------------------|-------------|-------------------|--------|
| Utilization %          | ops.utilization.pct             | KPI         | 01_Utilization    | 0.0 %  |
| Overtime %             | ops.overtime.pct                | KPI         | 02_Time           | 0.0 %  |
| Idle Time %            | ops.idle.pct                    | KPI         | 02_Time           | 0.0 %  |
| Throughput per Hour    | ops.throughput.per_hour         | KPI         | 03_Productivity   | #,0.0  |
| Schedule Adherence %   | ops.schedule_adherence.pct      | KPI         | 04_Process        | 0.0 %  |

---

## 4. Measures (DAX)

```DAX
Utilization % =
    DIVIDE ( SUM ( fact_time[Productive Hours] ),
             SUM ( fact_time[Available Hours] ) )
```

```DAX
Overtime % =
    DIVIDE ( SUM ( fact_time[Overtime Hours] ),
             SUM ( fact_time[Available Hours] ) )
```

```DAX
Idle Time % =
    DIVIDE ( SUM ( fact_time[Idle Hours] ),
             SUM ( fact_time[Available Hours] ) )
```

```DAX
Throughput per Hour =
    DIVIDE ( SUM ( fact_output[Output Units] ),
             SUM ( fact_time[Productive Hours] ) )
```

```DAX
Schedule Adherence % =
    DIVIDE (
        SUMX ( fact_time, IF ( fact_time[Schedule Adherence Flag], 1, 0 ) ),
        COUNTROWS ( fact_time )
    )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format | Summarization | Display Folder   |
|---------------|--------|---------------|------------------|
| Percentages   | 0.0 %  | None          | Utilization/Time |
| Hours         | #,0.0  | Sum           | Time             |
| Throughput    | #,0.0  | Sum           | Productivity     |

---

## 6. Visual Requirements (Technical)

- KPI cards: Utilization, Overtime, Idle Time, Throughput/hour, Schedule Adherence.
- Bar: Utilization by site/team/resource type.
- Line: Utilization and Overtime trend.
- Pareto: Idle time reasons if captured.
- Matrix: Site → Team → Resource with KPIs; export enabled.

---

## 7. RLS / OLS

- Region/country/site-based RLS via dim_org.  
- Optional OLS to hide resource-level details for privacy; show aggregates only.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (12–24 months at shift level).  
- Aggregate older periods to monthly to control size.  
- Avoid calculated columns; precompute flags upstream.

---

## 9. QA & Validation

| Check Type              | Object                   | Rule                                   | Tolerance |
|-------------------------|--------------------------|----------------------------------------|-----------|
| Referential Integrity   | fact tables → dims       | ≥ 99.9 % matched keys                  | 0.1 %     |
| Time Balance            | Productive+Idle+Overtime | ≈ Available Hours                      | ±2 %      |
| Throughput Plausibility | Units/hour               | Outliers flagged                       | manual    |
| Adherence Capture       | Schedule flag            | Coverage ≥ 95 % of rows                | threshold |
