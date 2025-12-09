# OPS-002 – Asset Performance (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/operations.yaml`
- **Semantic Model Definition:** `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: OPS-002)

---

## 1. Data Contract (Scope for OPS-002)

```yaml
dimension:
  - name: dim_date
    columns:
      - { name: DateKey, type: int, role: key }
      - { name: Date, type: date }
      - { name: Year, type: int }
      - { name: Quarter, type: text }
      - { name: Month, type: text }
      - { name: MonthNumber, type: int }
      - { name: Week, type: int }
      - { name: Shift, type: text }

  - name: dim_asset
    columns:
      - { name: AssetKey, type: int, role: key }
      - { name: AssetId, type: text }
      - { name: AssetName, type: text }
      - { name: AssetClass, type: text }
      - { name: Criticality, type: text }
      - { name: Plant, type: text }

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Plant, type: text }

  - name: dim_failure
    columns:
      - { name: FailureKey, type: int, role: key }
      - { name: FailureCategory, type: text }
      - { name: FailureReason, type: text }

  - name: dim_part
    columns:
      - { name: PartKey, type: int, role: key }
      - { name: PartNumber, type: text }
      - { name: PartName, type: text }
      - { name: PartCategory, type: text }
      - { name: Criticality, type: text }

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Plant, type: text }

fact:
  - name: fact_workorder
    grain: workorder
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: AssetKey, type: int, ref: dim_asset }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: FailureKey, type: int, ref: dim_failure, nullable: true }
      - { name: WorkOrderId, type: text }
      - { name: WorkOrderType, type: text }          # PM / CM
      - { name: DowntimeMinutes, type: number, agg: sum }
      - { name: RepairMinutes, type: number, agg: sum }
      - { name: LaborHours, type: number, agg: sum }
      - { name: PartsCost, type: currency, agg: sum }
      - { name: ServiceCost, type: currency, agg: sum }

  - name: fact_asset_runtime
    grain: asset_day
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: AssetKey, type: int, ref: dim_asset }
      - { name: PlannedTimeMinutes, type: number, agg: sum }
      - { name: RunTimeMinutes, type: number, agg: sum }

  - name: fact_parts_stock
    grain: part_day
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: PartKey, type: int, ref: dim_part }
      - { name: OnHandQty, type: number, agg: avg }
      - { name: StockoutFlag, type: boolean, agg: max }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_workorder → `ops.fact_workorder`
- fact_asset_runtime → `ops.fact_asset_runtime`
- fact_parts_stock → `ops.fact_parts_stock`
- dim_date → `shared.dim_date`
- dim_asset → `ops.dim_asset`
- dim_org → `shared.dim_org`
- dim_failure → `ops.dim_failure`
- dim_part → `ops.dim_part`
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `operations_asset_performance`

**Tables:** fact_workorder, fact_asset_runtime, fact_parts_stock, dim_date, dim_asset, dim_org, dim_failure, dim_part, security_user_org (RLS only)

**Relationships**
- fact_workorder[DateKey] → dim_date[DateKey] (1:* | single)
- fact_workorder[AssetKey] → dim_asset[AssetKey] (1:* | single)
- fact_workorder[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_workorder[FailureKey] → dim_failure[FailureKey] (1:* | single, nullable)
- fact_asset_runtime[AssetKey] → dim_asset[AssetKey] (1:* | single)
- fact_asset_runtime[DateKey] → dim_date[DateKey] (1:* | single)
- fact_parts_stock[PartKey] → dim_part[PartKey] (1:* | single)
- fact_parts_stock[DateKey] → dim_date[DateKey] (1:* | single)
- security_user_org attribute join to dim_org by Region/Country/Plant (RLS mapping)

**Hierarchies**
- Org: Region > Country > Plant
- Asset: Plant > AssetClass > AssetName
- Date: Year > Quarter > Month > Date > Shift
- Failure: Category > Reason
- Part: Category > PartName

**Display Folders**
- 01_Reliability: Availability %, MTBF, MTTR
- 02_Downtime: Downtime Minutes, Unplanned Downtime %, Failure breakdown
- 03_Spares: Spare Parts Stockout %, Parts Cost
- 04_Maintenance: PM Compliance %, Work Order counts

---

## 3. Measure Inventory

| Measure Name               | kpi_id                          | Type       | Folder        | Format  |
|----------------------------|---------------------------------|------------|---------------|---------|
| Availability %             | ops.availability.pct            | KPI        | 01_Reliability| 0.0 %  |
| MTBF (hours)               | ops.mtbf.hours                  | KPI        | 01_Reliability| #,0.0  |
| MTTR (hours)               | ops.mttr.hours                  | KPI        | 01_Reliability| #,0.0  |
| Unplanned Downtime %       | ops.downtime.unplanned.pct      | KPI        | 02_Downtime   | 0.0 %  |
| Spare Parts Stockout %     | ops.spare_parts.stockout.pct    | KPI        | 03_Spares     | 0.0 %  |
| PM Compliance %            | ops.pm_compliance.pct           | KPI        | 04_Maintenance| 0.0 %  |
| Downtime Minutes           | ops.downtime.minutes            | Supporting | 02_Downtime   | #,0    |
| Work Orders                | ops.workorders.count            | Supporting | 04_Maintenance| #,0    |

---

## 4. Measures (DAX)

```DAX
Availability % =
DIVIDE (
    SUM ( fact_asset_runtime[RunTimeMinutes] ),
    SUM ( fact_asset_runtime[PlannedTimeMinutes] )
)
```

```DAX
MTBF (hours) =
DIVIDE (
    SUM ( fact_asset_runtime[RunTimeMinutes] ) / 60,
    CALCULATE ( DISTINCTCOUNT ( fact_workorder[WorkOrderId] ), fact_workorder[WorkOrderType] = "CM" )
)
```

```DAX
MTTR (hours) =
DIVIDE (
    SUM ( fact_workorder[RepairMinutes] ),
    CALCULATE ( DISTINCTCOUNT ( fact_workorder[WorkOrderId] ), fact_workorder[WorkOrderType] = "CM" )
) / 60
```

```DAX
Unplanned Downtime % =
DIVIDE (
    CALCULATE ( SUM ( fact_workorder[DowntimeMinutes] ), fact_workorder[WorkOrderType] = "CM" ),
    SUM ( fact_workorder[DowntimeMinutes] )
)
```

```DAX
Spare Parts Stockout % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_parts_stock ), fact_parts_stock[StockoutFlag] = TRUE () ),
    COUNTROWS ( fact_parts_stock )
)
```

```DAX
PM Compliance % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_workorder ), fact_workorder[WorkOrderType] = "PM" && fact_workorder[RepairMinutes] >= 0 ),
    CALCULATE ( COUNTROWS ( fact_workorder ), fact_workorder[WorkOrderType] = "PM" )
)
```

```DAX
Downtime Minutes = SUM ( fact_workorder[DowntimeMinutes] )
```

```DAX
Work Orders = DISTINCTCOUNT ( fact_workorder[WorkOrderId] )
```

---

## 5. Defaults & Formatting

| Field/Measure                                    | Format  | Summarization | Display Folder  |
|--------------------------------------------------|---------|---------------|-----------------|
| Availability %, Unplanned Downtime %, Stockout %, PM Compliance % | 0.0 % | None          | 01/02/03/04     |
| MTBF (hours), MTTR (hours)                       | #,0.0   | Average       | 01_Reliability  |
| Downtime Minutes, Work Orders                    | #,0     | Sum           | 02_Downtime/04  |
| Costs (PartsCost, ServiceCost)                   | €#,0.00 | Sum           | 03_Spares       |

---

## 6. Visual Requirements (Technical)
- KPI cards: Availability %, MTBF, MTTR, Unplanned Downtime %, Spare Parts Stockout %, PM Compliance %.
- Trend lines: Availability %, MTBF, MTTR by dim_date[Month] (with targets).
- Pareto: Downtime Minutes by dim_failure[FailureReason] and by dim_asset[AssetName].
- Column: Availability % and Unplanned Downtime % by dim_asset[AssetName] with dim_asset[Criticality] filter.
- PM Compliance: Column by dim_org[Plant] and dim_asset[AssetClass].
- Parts: Stockout % by dim_part[PartCategory]; link to MTTR impact where possible.
- Matrix: Region > Plant > AssetClass > Asset with KPIs; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; enforce Region/Country/Plant filters on dim_org and propagate to fact_workorder/fact_asset_runtime.
- OLS (optional): hide cost fields (PartsCost, ServiceCost) for external roles; restrict dim_failure details for vendors.

---

## 8. Performance & Refresh
- Storage: Import; incremental refresh by month, 36 months retained.
- Partition by dim_date[Month]; consider summarising fact_workorder older than 18 months to monthly grain by Asset and FailureCategory.
- Ensure WorkOrderType is encoded in source (no string parsing); pre-clean failure codes.
- Maintain small helper table for targets per asset class; do not hardcode in DAX.

---

## 9. QA & Validation

| Check Type                  | Object                                   | Rule                                           | Tolerance |
|-----------------------------|------------------------------------------|------------------------------------------------|-----------|
| Referential Integrity       | fact_workorder/runtime/parts → dimensions| ≥ 99.9 % matched keys                          | 0.1 %     |
| Availability Balance        | RunTime + Downtime vs PlannedTime        | Difference < 1 %                               | ±1.0 %    |
| MTBF/MTTR Consistency       | CM workorders vs runtime and repair time | MTBF/MTTR recomputed within band               | ±5 %      |
| PM Compliance Calculation   | PM completed vs planned                  | Matches schedule counts                        | ±2 %      |
| Stockout Coverage           | StockoutFlag completeness                | Coverage ≥ 98 % for critical parts             | 2 % gap   |
