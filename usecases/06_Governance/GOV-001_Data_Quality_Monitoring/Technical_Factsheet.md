# GOV-001 Data Quality Monitoring - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

```yaml
dimension:
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
fact:
  - name: fact_dq_checks
    grain: table_day
    columns:
      - {name: Domain, type: text, role: attribute}
      - {name: SubjectArea, type: text, role: attribute}
      - {name: TableName, type: text, role: attribute}
      - {name: CheckDate, type: date_key, ref: dim_date}
      - {name: ValidRecords, type: integer, role: amount}
      - {name: TotalRecords, type: integer, role: amount}
    primary_key:
      - Domain
      - SubjectArea
      - TableName
      - CheckDate
relationships:
  - from: fact_dq_checks.CheckDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

## 2. Semantic Model Requirements
- Dataset: Contoso Sales Sample for Power BI Desktop.SemanticModel (DQ subject area workspace).
- Required fact table: `fact_dq_checks` loaded at least daily; must keep 12M history.
- Required dimension: `dim_date` with standard Date hierarchy (Year > Quarter > Month > Day).
- Relationships: single direction from Date to fact to keep row-level security stable.
- Sort-by: `SubjectArea` sorted by `SubjectArea` (alphabetic), `TableName` by itself; maintain alphabetical domain order.
- Hidden technical fields: raw rule identifiers, load timestamp, and pipeline run ID (kept hidden but available for troubleshooting).
- Hierarchies: Domain > SubjectArea > TableName for navigation; Date hierarchy reused from `dim_date`.

## 3. Measures (DAX + Description)
```
Data Quality % =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Valid Records Count], [Total Records Count])
```
Description:
  Purpose: Primary KPI for stewardship and dashboard alerting.
  Definition: Ratio of passing records to total validated records for selected grain.
  Grain & Scope: Table-day aggregated to any slicer context.
  Unit/Format: Percentage with 1 decimal.
  Lineage: fact_dq_checks[ValidRecords], fact_dq_checks[TotalRecords].
  QA: Compare vs source DQ engine logs; variance <= 0.5 pp.

```
Valid Records Count =
    // TODO: Provide DAX via Power BI MCP summing fact_dq_checks[ValidRecords]
```
Description:
  Purpose: Supporting measure for volume context.
  Definition: Sum of ValidRecords respecting current filters.
  Grain & Scope: Table-day aggregated to any slicer context.
  Unit/Format: Whole number.
  Lineage: fact_dq_checks[ValidRecords].
  QA: Must always be <= Total Records Count.

```
Total Records Count =
    // TODO: Provide DAX via Power BI MCP summing fact_dq_checks[TotalRecords]
```
Description:
  Purpose: Denominator baseline for Data Quality % and issue sizing.
  Definition: Sum of TotalRecords respecting current filters.
  Grain & Scope: Table-day aggregated to any slicer context.
  Unit/Format: Whole number.
  Lineage: fact_dq_checks[TotalRecords].
  QA: Compare vs ingestion logs; variance <= 0.5 %.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Data Quality % | No summarization, Percentage, 1 decimal | Display folder: 01_DataQuality |
| Valid Records Count | Sum, Whole number | Display folder: 01_DataQuality |
| Total Records Count | Sum, Whole number | Display folder: 01_DataQuality |
| Domain / SubjectArea / TableName | Do not summarize | Sorting alphabetical; use Domain hierarchy |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Show current KPI vs prior period | Data Quality %, Valid Records Count, Total Records Count | Add conditional formatting for thresholds |
| Heatmap | Highlight weakest tables | Domain hierarchy, Data Quality % | Use table conditional color scale (red <95 %) |
| Trend Line | Monitor KPI over time | Date hierarchy, Data Quality %, Valid Records Count | 12-24 weeks rolling window |
| Detail Table | Rule-level diagnostics | Domain hierarchy, TableName, rule metadata, Data Quality %, Valid Records Count | Include drill-through to raw rule run |

## 6. Performance & Refresh
- Storage mode: Import with incremental refresh (last 60 days daily, historical monthly).
- Refresh window: pipeline writes snapshots nightly at 02:00 CET; dataset refresh scheduled at 02:30 CET.
- Partitioning by CheckDate (month) to speed backfill.
- Monitor memory footprint since table_day grain can grow quickly; consider aggregations for >12M horizon.

## 7. RLS/OLS Requirements
- RLS on Domain using stewardship mapping table (Domain -> Allowed Users).
- Additional role for Data Governance Office with full access.
- Technical users (service principals) bypass RLS for data quality automation.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_dq_checks -> dim_date | >= 99.9 % of CheckDate keys must exist in dim_date | 0.1 % |
| DQ_Score_Within_Range | Data Quality % | KPI must stay within 0 % - 100 % | Hard limit |
| Issue Log Tie-Out | Valid Records Count | Compare vs DQ engine export | +/- 0.5 % |
