# OPS-001 – Operations Performance (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/operations.yaml`
- **Semantic Model Definition:** `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: OPS-001)

---

## 1. Data Contract (Scope for OPS-001)

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

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Plant, type: text }
      - { name: Line, type: text }

  - name: dim_product
    columns:
      - { name: ProductKey, type: int, role: key }
      - { name: ProductCode, type: text }
      - { name: ProductName, type: text }
      - { name: Category, type: text }
      - { name: UoM, type: text }

  - name: dim_downtime_reason
    columns:
      - { name: DowntimeReasonKey, type: int, role: key }
      - { name: DowntimeReason, type: text }
      - { name: DowntimeCategory, type: text }

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Plant, type: text }
      - { name: Line, type: text }

fact:
  - name: fact_production
    grain: line_shift_product
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: DowntimeReasonKey, type: int, ref: dim_downtime_reason }
      - { name: PlannedTimeMinutes, type: number, agg: sum }
      - { name: RunTimeMinutes, type: number, agg: sum }
      - { name: DowntimeMinutes, type: number, agg: sum }
      - { name: GoodUnits, type: number, agg: sum }
      - { name: ScrapUnits, type: number, agg: sum }
      - { name: IdealRateUnitsPerMin, type: number, agg: avg }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_production → `ops.fact_production`
- dim_date → `shared.dim_date`
- dim_org → `shared.dim_org`
- dim_product → `shared.dim_product`
- dim_downtime_reason → `ops.dim_downtime_reason`
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `operations_oee`

**Tables:** fact_production, dim_date, dim_org, dim_product, dim_downtime_reason, security_user_org (RLS only)

**Relationships**
- fact_production[DateKey] → dim_date[DateKey] (1:* | single)
- fact_production[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_production[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_production[DowntimeReasonKey] → dim_downtime_reason[DowntimeReasonKey] (1:* | single)
- security_user_org attribute join to dim_org by Region/Country/Plant/Line (RLS mapping)

**Hierarchies**
- Org: Region > Country > Plant > Line
- Date: Year > Quarter > Month > Date > Shift
- Product: Category > ProductName

**Display Folders**
- 01_OEE: OEE %, Availability %, Performance %, Quality %
- 02_Output: Throughput Units, Good Units, Scrap Units
- 03_Downtime: Downtime Minutes, Downtime Minutes %

---

## 3. Measure Inventory

| Measure Name       | kpi_id                | Type       | Folder      | Format |
|--------------------|-----------------------|------------|-------------|--------|
| OEE %              | ops.oee.pct           | KPI        | 01_OEE      | 0.0 % |
| Availability %     | ops.availability.pct  | KPI        | 01_OEE      | 0.0 % |
| Performance %      | ops.performance.pct   | KPI        | 01_OEE      | 0.0 % |
| Quality %          | ops.quality.pct       | KPI        | 01_OEE      | 0.0 % |
| Throughput Units   | ops.throughput.units  | Supporting | 02_Output   | #,0   |
| Downtime Minutes   | ops.downtime.minutes  | Supporting | 03_Downtime | #,0   |
| Downtime Minutes % | ops.downtime.pct      | Supporting | 03_Downtime | 0.0 % |

---

## 4. Measures (DAX)

```DAX
Availability % =
DIVIDE (
    SUM ( fact_production[RunTimeMinutes] ),
    SUM ( fact_production[PlannedTimeMinutes] )
)
```

```DAX
Performance % =
DIVIDE (
    SUM ( fact_production[GoodUnits] ),
    SUM ( fact_production[RunTimeMinutes] ) * AVERAGE ( fact_production[IdealRateUnitsPerMin] )
)
```

```DAX
Quality % =
DIVIDE (
    SUM ( fact_production[GoodUnits] ),
    SUM ( fact_production[GoodUnits] ) + SUM ( fact_production[ScrapUnits] )
)
```

```DAX
OEE % = [Availability %] * [Performance %] * [Quality %]
```

```DAX
Throughput Units = SUM ( fact_production[GoodUnits] )
```

```DAX
Downtime Minutes = SUM ( fact_production[DowntimeMinutes] )
```

```DAX
Downtime Minutes % =
DIVIDE ( [Downtime Minutes], SUM ( fact_production[PlannedTimeMinutes] ) )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format | Summarization | Display Folder |
|---------------|--------|---------------|----------------|
| OEE %, Availability %, Performance %, Quality %, Downtime Minutes % | 0.0 % | None | 01_OEE / 03_Downtime |
| Throughput Units, Good Units, Scrap Units, Downtime Minutes | #,0 | Sum | 02_Output / 03_Downtime |
| Time fields (minutes) | #,0 | Sum | 03_Downtime |

---

## 6. Visual Requirements (Technical)
- KPI cards: OEE %, Availability %, Performance %, Quality %.
- Trend line: OEE %, Availability %, Performance %, Quality % by dim_date[Month].
- Pareto bar: Downtime Minutes by dim_downtime_reason[DowntimeReason] (Top N, filterable by Plant/Line).
- Bar/Column: OEE % by dim_org[Plant] and [Line]; cross-filter with downtime reasons.
- Matrix: Region > Plant > Line > Shift with OEE %, Availability %, Performance %, Quality %, Throughput Units; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; enforce Region/Country/Plant/Line filters on dim_org and propagate to fact_production.
- OLS (optional): hide downtime reason columns for external partners; deny dim_downtime_reason[DowntimeReason] and [DowntimeCategory] for restricted roles.

---

## 8. Performance & Refresh
- Storage: Import; incremental refresh by month, retain 36 months.
- Partition by dim_date[Month]; filter out open production days until closed to avoid churn.
- Avoid calculated columns; pre-calculate IdealRate in source if static.
- Consider monthly aggregation table by Plant/Line for OEE and Throughput if >50M rows.

---

## 9. QA & Validation

| Check Type                | Object                            | Rule                                           | Tolerance |
|---------------------------|-----------------------------------|------------------------------------------------|-----------|
| Referential Integrity     | fact_production → dimensions      | ≥ 99.9 % matched keys                          | 0.1 %     |
| OEE Consistency           | OEE % vs component product        | Difference < 0.1 pp                            | ±0.1 pp   |
| Time Balance              | Run + Downtime vs Planned Time    | Difference < 1 %                               | ±1.0 %    |
| Throughput Reconciliation | GoodUnits vs production log       | Match on daily grain                           | ±0.5 %    |
| Downtime Capture          | DowntimeMinutes coverage          | Logged minutes / Planned minutes               | ≥ 98 %    |
