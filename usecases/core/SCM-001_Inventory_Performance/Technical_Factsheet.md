# SCM-001 – Inventory Performance (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/supply_chain.yaml`
- **Semantic Model Definition:** `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: SCM-001)

---

## 1. Data Contract (Scope for SCM-001)

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

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Location, type: text }

  - name: dim_product
    columns:
      - { name: ProductKey, type: int, role: key }
      - { name: SKU, type: text }
      - { name: ProductName, type: text }
      - { name: Category, type: text }
      - { name: Subcategory, type: text }
      - { name: Class, type: text }      # ABC/XYZ if available
      - { name: UoM, type: text }

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Location, type: text }

fact:
  - name: fact_inventory_snapshot
    grain: sku_location_day
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: OnHandQty, type: number, agg: avg }
      - { name: OnHandValue, type: currency, agg: avg }
      - { name: AgingBucket, type: text }
      - { name: ObsoleteFlag, type: boolean }
      - { name: SafetyStockQty, type: number, agg: avg }

  - name: fact_orders
    grain: order_line
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: OrderQty, type: number, agg: sum }
      - { name: DeliveredQty, type: number, agg: sum }
      - { name: StockoutFlag, type: boolean }
      - { name: OTIFFlag, type: boolean }

  - name: fact_cogs_monthly
    grain: sku_location_month
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: COGSAmount, type: currency, agg: sum }

  - name: fact_forecast
    grain: sku_location_month_version
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: ForecastQty, type: number, agg: sum }
      - { name: ForecastVersion, type: text }
      - { name: CreatedAt, type: datetime }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_inventory_snapshot → `scm.fact_inventory_snapshot`
- fact_orders → `scm.fact_orders`
- fact_cogs_monthly → `fin.fact_cogs_monthly`
- fact_forecast → `scm.fact_forecast`
- dim_date → `shared.dim_date`
- dim_org → `shared.dim_org`
- dim_product → `shared.dim_product`
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `scm_inventory_performance`

**Tables:** fact_inventory_snapshot, fact_orders, fact_cogs_monthly, fact_forecast, dim_date, dim_org, dim_product, security_user_org (RLS only)

**Relationships**
- fact_inventory_snapshot[DateKey] → dim_date[DateKey] (1:* | single)
- fact_inventory_snapshot[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_inventory_snapshot[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_orders[DateKey] → dim_date[DateKey]; fact_orders[OrgKey] → dim_org[OrgKey]; fact_orders[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_cogs_monthly[DateKey] → dim_date[DateKey]; fact_cogs_monthly[OrgKey] → dim_org[OrgKey]; fact_cogs_monthly[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_forecast[DateKey] → dim_date[DateKey]; fact_forecast[OrgKey] → dim_org[OrgKey]; fact_forecast[ProductKey] → dim_product[ProductKey] (1:* | single)
- security_user_org attribute join to dim_org by Region/Country/Location (RLS mapping)

**Hierarchies**
- Org: Region > Country > Location
- Product: Category > Subcategory > SKU
- Date: Year > Quarter > Month > Date

**Display Folders**
- 01_Inventory: DIO, Inventory Turnover, OnHandValue
- 02_Service: Stockout %, OTIF %
- 03_Risk: Obsolescence %
- 04_Forecast: Forecast Accuracy %

---

## 3. Measure Inventory

| Measure Name            | kpi_id                       | Type       | Folder        | Format  |
|-------------------------|------------------------------|------------|---------------|---------|
| Days in Inventory       | inv.dio.days                 | KPI        | 01_Inventory  | #,0    |
| Inventory Turnover      | inv.turnover                 | KPI        | 01_Inventory  | #,0.0  |
| Stockout Rate %         | inv.stockout.pct             | KPI        | 02_Service    | 0.0 %  |
| OTIF %                  | supply.otif.pct              | KPI        | 02_Service    | 0.0 %  |
| Obsolescence Risk %     | inv.obsolete.pct             | KPI        | 03_Risk       | 0.0 %  |
| Forecast Accuracy %     | plan.forecast.accuracy.pct   | KPI        | 04_Forecast   | 0.0 %  |
| On Hand Value           | inv.onhand.value             | Supporting | 01_Inventory  | €#,0.00|
| Average Inventory Value | inv.avg_inventory.value      | Supporting | 01_Inventory  | €#,0.00|
| COGS Amount             | inv.cogs.amount              | Supporting | 01_Inventory  | €#,0.00|

---

## 4. Measures (DAX)

```DAX
On Hand Value =
    AVERAGE ( fact_inventory_snapshot[OnHandValue] )
```

```DAX
Average Inventory Value =
    CALCULATE (
        AVERAGE ( fact_inventory_snapshot[OnHandValue] ),
        ALL ( dim_date[Date] )
    )
```

```DAX
COGS Amount = SUM ( fact_cogs_monthly[COGSAmount] )
```

```DAX
Inventory Turnover =
DIVIDE ( [COGS Amount], [Average Inventory Value] )
```

```DAX
Days in Inventory =
DIVIDE ( 365, [Inventory Turnover] )
```

```DAX
Stockout Rate % =
DIVIDE (
    SUMX ( fact_orders, IF ( fact_orders[StockoutFlag], fact_orders[OrderQty], 0 ) ),
    SUM ( fact_orders[OrderQty] )
)
```

```DAX
OTIF % =
DIVIDE (
    SUMX ( fact_orders, IF ( fact_orders[OTIFFlag], 1, 0 ) ),
    COUNTROWS ( fact_orders )
)
```

```DAX
Obsolescence Risk % =
DIVIDE (
    SUMX ( fact_inventory_snapshot, IF ( fact_inventory_snapshot[ObsoleteFlag], fact_inventory_snapshot[OnHandValue], 0 ) ),
    SUM ( fact_inventory_snapshot[OnHandValue] )
)
```

```DAX
Forecast Accuracy % =
VAR ActualQty =
    SUM ( fact_orders[DeliveredQty] )
VAR FcstQty =
    CALCULATE ( SUM ( fact_forecast[ForecastQty] ), KEEPFILTERS ( VALUES ( fact_forecast[ForecastVersion] ) ) )
RETURN
    1 - ABS ( DIVIDE ( ActualQty - FcstQty, ActualQty ) )
```

---

## 5. Defaults & Formatting

| Field/Measure                                        | Format  | Summarization | Display Folder |
|------------------------------------------------------|---------|---------------|----------------|
| Percentages (Stockout %, OTIF %, Obsolescence %, Forecast Accuracy %) | 0.0 % | None | 02_Service / 03_Risk / 04_Forecast |
| DIO, Turnover                                        | #,0 / #,0.0 | None       | 01_Inventory   |
| Value measures (On Hand, Avg Inventory, COGS)        | €#,0.00 | Sum/Avg      | 01_Inventory   |
| Quantities                                           | #,0     | Sum          | 02_Service     |

---

## 6. Visual Requirements (Technical)
- KPI cards: DIO, Inventory Turnover, Stockout %, OTIF %, Obsolescence %, Forecast Accuracy %.
- Column: DIO and Turnover by dim_org[Location] and dim_product[Category/Subcategory].
- Line: Stockout % and OTIF % trend by dim_date[Month].
- Pareto: Obsolescence value by dim_product[SKU].
- Column: Forecast Accuracy % by dim_product[SKU] (filter A/B class).
- Matrix: Region > Location > Category > SKU with KPIs and aging buckets; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; enforce Region/Country/Location filters on dim_org and propagate to fact tables.
- OLS (optional): hide value fields (OnHandValue, COGS) for external partners; keep quantity and KPI percentages visible.

---

## 8. Performance & Refresh
- Storage: Import; incremental by month, retain 36 months; for daily inventory, aggregate to month for history beyond 6–12 months.
- Partition fact_inventory_snapshot and fact_orders by Month; keep forecast latest version flag in source to avoid complex DAX.
- Avoid calculated columns; pre-calculate aging bucket and obsolete flag upstream.
- Consider aggregation table Month x Location x Category for inventory value if volume >50M rows.

---

## 9. QA & Validation

| Check Type                | Object                                    | Rule                                                | Tolerance |
|---------------------------|-------------------------------------------|-----------------------------------------------------|-----------|
| Referential Integrity     | facts → dimensions                        | ≥ 99.9 % matched keys                               | 0.1 %     |
| DIO vs Turnover           | DIO and Turnover relationship             | |365 / Turnover - DIO| < 0.5 days                    | 0.5 days  |
| Stockout Calculation      | StockoutFlag capture                      | Stockout lines / total lines matches source         | ±1.0 pp   |
| OTIF Calculation          | OTIFFlag capture                          | Matches logistics SLA reporting                     | ±1.0 pp   |
| Aging Coverage            | AgingBucket completeness                  | ≥ 95 % of inventory rows with valid bucket          | 5 % gap   |
| Forecast Alignment        | Forecast vs DeliveredQty denominators     | No division by zero; version filter applied         | n/a       |
