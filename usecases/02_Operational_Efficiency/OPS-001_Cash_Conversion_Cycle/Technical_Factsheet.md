# OPS-001 – Technical Factsheet

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
      - { name: Entity, type: string }
fact:
  - name: fact_working_capital
    grain: period_end
    columns:
      - { name: PeriodEndDate, type: date, role: snapshot_date }
      - { name: OrgID, type: string, ref: dim_org }
      - { name: Date, type: date, ref: dim_date }
      - { name: AR Balance, type: decimal, role: receivables }
      - { name: AP Balance, type: decimal, role: payables }
      - { name: Inventory Value, type: decimal, role: inventory }
      - { name: Net Sales Amount, type: decimal, role: amount }
      - { name: COGS Amount, type: decimal, role: amount }
      - { name: Days In Period, type: int, role: helper }
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

## 2. Semantic Model Requirements
- **Facts:** `fact_working_capital` (period_end grain).
- **Dimensions:** `dim_date`, `dim_org`, optional `dim_customer`, `dim_supplier` for drill-down.
- **Relationships:** Date → dimension (many-to-one, single); Org → dimension (many-to-one, single); optional role-playing dates for Plan/LY snapshots.
- **Sort-by:** MonthName sorted by MonthNumber, Org by Region.
- **Hidden fields:** Keys and raw balances for IR checks.
- **Hierarchies:** Org (Region > Entity > Business Unit); Time (Year > Quarter > Month); optional Customer/Supplier hierarchies for diagnostics.

## 3. Measures (DAX + Description)

```
DSO (Days) =
VAR _AR = [Average AR Amount]
VAR _Sales = [Net Sales Amount]
RETURN DIVIDE(_AR, _Sales, BLANK()) * [Days in Period]
```
Description:
- Purpose: Days Sales Outstanding.
- Definition: Average AR divided by Net Sales times actual days.
- Grain & Scope: Period-end snapshot, actuals only.
- Unit/Format: Days (integer).
- Lineage: fact_working_capital[AR Balance], fact_working_capital[Net Sales Amount], fact_working_capital[Days In Period].
- QA: Must stay within 0–180 days; reconcile vs source AR aging.

```
DIO (Days) =
DIVIDE([Average Inventory Amount],[COGS Amount], BLANK()) * [Days in Period]
```
Description: Days Inventory Outstanding; same grain as DSO; 0–365 days guardrail; lineage = Inventory Value + COGS.

```
DPO (Days) =
DIVIDE([Average AP Amount],[COGS Amount], BLANK()) * [Days in Period]
```
Description: Days Payables Outstanding; 0–180 days; lineage = AP Balance + COGS.

```
Cash Conversion Cycle (Days) =
[DSO (Days)] + [DIO (Days)] - [DPO (Days)]
```
Description: Sum of sub-components; 0–365 expected.

```
Delta CCC (Days) =
[Cash Conversion Cycle (Days)] - [CCC Baseline (Days)]
```
Description: Variance vs Plan/LY; requires baseline measure (Plan or LY CCC).

Baseline measure placeholder:
```
CCC Baseline (Days) =
CALCULATE([Cash Conversion Cycle (Days)], SELECTEDMEASURENAME()) // replace with actual Plan/LY filter
```
(Flagged as TODO in backlog.)

## 4. Defaults & Formatting

| Field / Measure | Setting | Notes |
|-----------------|---------|-------|
| AR/AP/Inventory Balances | Sum, Currency (EUR #,0.0) | Hidden in visuals, used for QC. |
| Net Sales Amount, COGS Amount | Sum, Currency (EUR #,0.0) | Display Folder: 01_WorkingCapital/Base. |
| DSO / DIO / DPO / CCC | No summarization, integer format `0` | Folder: 02_WorkingCapital/KPIs. |
| Delta CCC | Signed integer with prefix `+0;-0` | Folder: 02_WorkingCapital/KPIs. |

## 5. Visual Requirements (Technical)

| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards (3-second) | Headline DSO/DIO/DPO/CCC/ΔCCC | Measures + Plan/LY comparisons | Use conditional formatting per threshold. |
| Line Chart | Trend 12–24M | Date hierarchy, all KPI measures | Show actual vs Plan/LY. |
| Waterfall | Explain CCC variance | Baseline CCC, contributions (DSO Δ, DIO Δ, DPO Δ) | Use bridging logic from Plan to Actual. |
| Matrix | Segment diagnostics | Org/Customer/Supplier hierarchies + KPIs | Enable drill and conditional formatting. |
| Detail Table | Export | Granular attributes + KPIs + Action code status | Provide CSV export button. |

## 6. Performance & Refresh
- Storage Mode: Import.
- Refresh: daily after month-end close; incremental partitions by Month (36 months history).
- Partition strategy: PeriodEndDate month-based; ensures fast reload of latest month.
- Considerations: DAX measures reference averages, ensure pre-aggregations for AR/AP/Inv to avoid large scans.

## 7. RLS/OLS Requirements
- RLS on `dim_org` (Region/Entity); filter expression: `dim_org[Region] IN USERPRINCIPALNAME()` mapping.
- Optional Customer/Supplier RLS depending on deployment (inherit from CRM/Procurement roles).
- Roles: `Global`, `Region_Manager`, `Legal_Entity_Controller`.

## 8. QA & Validation Rules

| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_working_capital → dim_date/dim_org | ≥ 99.9 % matched keys | ≤ 0.1 % missing |
| Measure Bounds | DSO/DIO/DPO | 0–180 days (DIO 0–365) | Flag when outside |
| CCC Variance | Delta CCC | Only compute where Baseline > 0 | Skip otherwise |
| Reconciliation | Balances vs Source | AR/AP/Inventory match GL accounts | ±0.5 % |
