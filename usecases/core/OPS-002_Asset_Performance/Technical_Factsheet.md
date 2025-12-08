# OPS-002 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: OPS-002)

---

## 1. Data Contract (YAML – OPS-002 Scope)

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

  - name: dim_asset
    columns:
      - {name: AssetKey, type: int, role: key}
      - {name: AssetId, type: text}
      - {name: AssetName, type: text}
      - {name: AssetClass, type: text}
      - {name: Criticality, type: text}
      - {name: Plant, type: text}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Plant, type: text}

fact:
  - name: fact_workorder
    grain: workorder
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: AssetKey, type: int, ref: dim_asset}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: WorkOrderId, type: text}
      - {name: WO Type, type: text}              # PM / CM
      - {name: Downtime Minutes, type: number, agg: sum}
      - {name: Repair Minutes, type: number, agg: sum}
      - {name: Failure Reason, type: text}

  - name: fact_asset_runtime
    grain: asset_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: AssetKey, type: int, ref: dim_asset}
      - {name: Planned Time (min), type: number, agg: sum}
      - {name: Run Time (min), type: number, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_workorder → `lh_ops.fact_workorder`
- fact_asset_runtime → `lh_ops.fact_asset_runtime`
- dim_date → `lh_shared.dim_date`
- dim_asset → `lh_ops.dim_asset`
- dim_org → `lh_shared.dim_org`

---

## 2. Semantic Model Requirements

### Model Name
`operations_asset_performance`

### Tables
- fact_workorder  
- fact_asset_runtime  
- dim_date  
- dim_asset  
- dim_org  

### Relationships
- fact_workorder[DateKey] → dim_date[DateKey] (1:* | single)
- fact_workorder[AssetKey] → dim_asset[AssetKey] (1:* | single)
- fact_workorder[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_asset_runtime[AssetKey] → dim_asset[AssetKey] (1:* | single)
- fact_asset_runtime[DateKey] → dim_date[DateKey] (1:* | single)

### Hierarchies
- Asset: Plant → AssetClass → AssetName
- Org: Region → Country → Plant
- Date: Year → Quarter → Month → Date → Shift

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name            | kpi_id                        | Type        | Folder           | Format |
|-------------------------|-------------------------------|-------------|------------------|--------|
| Availability %          | ops.availability.pct          | KPI         | 01_Reliability   | 0.0 %  |
| MTBF (hours)            | ops.mtbf.hours                | KPI         | 01_Reliability   | #,0.0  |
| MTTR (hours)            | ops.mttr.hours                | KPI         | 01_Reliability   | #,0.0  |
| Unplanned Downtime %    | ops.downtime.unplanned.pct    | KPI         | 02_Downtime      | 0.0 %  |
| Spare Parts Stockout %  | ops.spare_parts.stockout.pct  | KPI         | 03_Spares        | 0.0 %  |
| Downtime Minutes        | ops.downtime.minutes          | Supporting  | 02_Downtime      | #,0    |

---

## 4. Measures (DAX)

```DAX
Availability % =
    DIVIDE ( SUM ( fact_asset_runtime[Run Time (min)] ),
             SUM ( fact_asset_runtime[Planned Time (min)] ) )
```

```DAX
MTBF (hours) =
    DIVIDE (
        SUM ( fact_asset_runtime[Run Time (min)] ) / 60,
        DISTINCTCOUNT ( fact_workorder[WorkOrderId] )
    )
```

```DAX
MTTR (hours) =
    DIVIDE (
        SUM ( fact_workorder[Repair Minutes] ),
        DISTINCTCOUNT ( fact_workorder[WorkOrderId] ) * 60
    )
```

```DAX
Unplanned Downtime % =
    DIVIDE (
        CALCULATE ( SUM ( fact_workorder[Downtime Minutes] ), fact_workorder[WO Type] = "CM" ),
        SUM ( fact_workorder[Downtime Minutes] )
    )
```

```DAX
Downtime Minutes =
    SUM ( fact_workorder[Downtime Minutes] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format | Summarization | Display Folder |
|---------------|--------|---------------|----------------|
| Percentages   | 0.0 %  | None          | KPI folders    |
| Time (hours)  | #,0.0  | Average       | Reliability    |
| Minutes       | #,0    | Sum           | Downtime       |

---

## 6. Visual Requirements (Technical)

- KPI cards: Availability, MTBF, MTTR, Unplanned Downtime %, Spare Parts Stockout %.
- Trend: Availability/MTBF/MTTR over time.
- Pareto: Downtime by failure reason.
- Bar: Availability by asset/plant.
- Matrix: Asset hierarchy with KPIs; export enabled.

---

## 7. RLS / OLS

- Org-based RLS (Region/Country/Plant).  
- Optional asset-class-based OLS to hide sensitive assets for vendors.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (36 months).  
- Summarize workorders for long history; keep detailed last 12 months.  
- Avoid row-level calculated columns; pre-aggregate downtime by reason if large.

---

## 9. QA & Validation

| Check Type              | Object                     | Rule                                  | Tolerance |
|-------------------------|----------------------------|---------------------------------------|-----------|
| Referential Integrity   | fact tables → dims         | ≥ 99.9 % matched keys                 | 0.1 %     |
| Availability Calculation| Run + Downtime vs Planned  | Run + Downtime ≈ Planned              | ±1 %      |
| Reliability Consistency | MTBF/MTTR vs downtime      | MTBF/MTTR consistent with WO counts   | ±5 %      |
| Unplanned Downtime Share| CM vs total downtime       | Matches WO type coding                | ±2 %      |
