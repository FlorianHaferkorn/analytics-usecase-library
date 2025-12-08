# OPS-002 – Technical Factsheet

## 1. Data Contract (YAML)
```yaml
dimension:
  - name: dim_date
    columns:
      - { name: Date, type: date, role: key }
      - { name: Year, type: int }
      - { name: Month, type: int }
  - name: dim_org
    columns:
      - { name: OrgID, type: string, role: key }
      - { name: Region, type: string }
      - { name: Warehouse, type: string }
  - name: dim_product
    columns:
      - { name: ProductID, type: string, role: key }
      - { name: Category, type: string }
      - { name: Subcategory, type: string }
fact:
  - name: fact_inventory_snapshot
    grain: sku_location_day
    columns:
      - { name: SnapshotDate, type: date, role: date_key, ref: dim_date }
      - { name: OrgID, type: string, ref: dim_org }
      - { name: ProductID, type: string, ref: dim_product }
      - { name: Inventory Units, type: decimal, role: qty }
      - { name: Inventory Value, type: decimal, role: amount }
      - { name: Demand Qty, type: decimal, role: qty }
      - { name: Delivered Qty, type: decimal, role: qty }
      - { name: Safety Stock Qty, type: decimal, role: helper }
      - { name: Lead Time Days, type: int, role: helper }
  - name: fact_sales
    grain: invoice_line
    columns:
      - { name: Date, type: date, role: date_key, ref: dim_date }
      - { name: OrgID, type: string, ref: dim_org }
      - { name: ProductID, type: string, ref: dim_product }
      - { name: Net Sales Amount, type: decimal, role: amount }
      - { name: COGS Amount, type: decimal, role: amount }
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

## 2. Semantic Model Requirements
- **Fact tables:** `fact_inventory_snapshot` (daily snapshot), `fact_sales` (invoice line).
- **Dimensions:** `dim_date`, `dim_org`, `dim_product` (plus optional Supplier, Channel if available).
- **Relationships:** Snapshot fact → dimensions (many-to-one single direction). Sales fact shares the same dims for joined KPIs (Inventory Turns).
- **Role-playing:** optional `dim_date` as Snapshot vs Invoice date, handled via calculated table or inactive relationship.
- **Sort-by:** MonthName sorted by MonthNumber; Product ABC classification (if added) sorted by weight.
- **Hidden fields:** raw units/values, lead time, safety stock for QC.
- **Hierarchies:** Org (Region > Area > Store/Warehouse), Product (Category > Subcategory > SKU), Time (Year > Quarter > Month > Week).

## 3. Measures (DAX + Description)

```
Average Inventory Value =
AVERAGEX(
    VALUES(dim_date[Date]),
    [Inventory Value]
)
```

```
Inventory Days =
DIVIDE([Average Inventory Value],[COGS Amount], BLANK()) * 365
```
Description: Capital binding expressed als Tage; Format `0`; QA 0–365.

```
Inventory Turnover =
DIVIDE([COGS Amount],[Average Inventory Value], BLANK())
```
Description: COGS / Inventory; Format `0.0`; QA >=0.

```
Stock-Out Rate % =
VAR _demand = [Demand Qty]
VAR _fulfilled = [Delivered Qty]
VAR _lost = MAX(0, _demand - _fulfilled)
RETURN DIVIDE(_lost, _demand, BLANK())
```
Description: Lost demand share; Format `0.0 %`; QA 0–100 %.

```
Obsolescence % =
DIVIDE([Obsolete Inventory Value],[Inventory Value], BLANK())
```
Description: Anteil Aging > Threshold. Hinweis: `[Obsolete Inventory Value]` wird aus Snapshot-Flags berechnet (TODO, abhängig von Aging Logic).

```
OTIF % =
DIVIDE([OTIF Deliveries Count],[Total Deliveries Count], BLANK())
```
Description: On-Time In-Full, falls OTIF-Facts vorhanden; sonst via operational KPI.

Hilfsmaßnahmen (TODO falls nicht vorhanden):
- `[Obsolete Inventory Value]` = SUMX(Filter auf Aging>Threshold, value)
- `[Demand Qty]`, `[Delivered Qty]` als Summen bzw. AVERAGE wenn pro Snapshot.

Jeder Measure bekommt `Description/Purpose/Lineage/QA` wie oben beschrieben.

## 4. Defaults & Formatting

| Field / Measure | Setting | Notes |
|-----------------|---------|-------|
| Inventory Value | Sum, Currency `EUR #,0.0` | Folder: 01_Inventory/Base |
| COGS Amount | Sum, Currency | Reuse existing Sales measure |
| Inventory Days | Whole number `0` | Folder: 02_Inventory/KPIs |
| Inventory Turnover | Decimal `0.0` | Folder: 02_Inventory/KPIs |
| Stock-Out Rate % | Percentage `0.0 %` | Folder: 02_Service/KPIs |
| Obsolescence % | Percentage `0.0 %` | Folder: 02_Inventory/KPIs |
| OTIF % | Percentage `0.0 %` | Folder: 02_Service/KPIs |
| Demand/Delivered Qty | Sum, `#,0` | Hidden from visuals, used in measures |

## 5. Visual Requirements (Technical)

| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Highlight Inventory Days, Stock-Out %, Inventory Turnover, Obsolescence, OTIF | Measures + Plan/LY variants | Conditional formatting per threshold. |
| Line Chart | Trend 12–24 M | Date hierarchy + Inventory Days/OTIF | Dual-axis optional. |
| Waterfall | Inventory Value Δ | Baseline, Demand, Supply, Policy contributions (calculated measures) | Need bridging logic. |
| Heatmap / Matrix | SKU × Location risk | Org/Product dims + Stock-Out %, Inventory Days | Use Data Bars / Colors. |
| Drill Table | Detail analysis | Attributes + KPIs + Lead Time, Safety Stock | Exportable CSV. |

## 6. Performance & Refresh
- Storage: Import.
- Refresh cadence: Daily Snapshot load (05:00); incremental partitions by SnapshotDate (rolling 18–24 M).
- Partition strategy: Year-Month for snapshot fact; Sales can leverage existing partitioning.
- Performance guards: Pre-aggregate Inventory Value by Month to avoid scanning full snapshot history in main visuals; leverage aggregation tables if dataset grows.

## 7. RLS/OLS Requirements
- RLS on `dim_org` (Region/Area). Example filter: `dim_org[Region] IN USERPRINCIPALNAME()` mapping table.
- Optional Product security (Category-level) for partner views.
- Roles: `Global_SC`, `Region_SC`, `Warehouse_Manager`.

## 8. QA & Validation Rules

| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_inventory_snapshot → dims | ≥ 99.5 % matched keys | ≤ 0.5 % missing |
| Value Bounds | Inventory Value / Units | Must be ≥ 0 | Hard stop |
| Stock-Out Rate % | Measure | 0–100 % | Alert outside range |
| OTIF % | Measure | 0–100 % | Alert outside range |
| Aging Logic | Obsolete Inventory Value | Validate vs ERP aging report | ±0.5 % |
