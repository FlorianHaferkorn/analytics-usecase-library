# GOV-004 Audit Findings Management - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

```yaml
dimension:
  - name: dim_org
    grain: org
    columns:
      - {name: OrgID, type: text, role: primary_key}
      - {name: Region, type: text}
      - {name: BusinessUnit, type: text}
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
fact:
  - name: fact_findings
    grain: finding
    columns:
      - {name: FindingID, type: text, role: primary_key}
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
      - {name: Severity, type: text, role: attribute}
      - {name: Status, type: text, role: attribute}
      - {name: ActionOwner, type: text, role: attribute}
      - {name: OpenDate, type: date_key, ref: dim_date}
      - {name: DueDate, type: date, role: helper}
      - {name: CloseDate, type: date, role: helper}
      - {name: ActionCode, type: text, role: attribute}
relationships:
  - from: fact_findings.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_findings.OpenDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

## 2. Semantic Model Requirements
- Dataset: Contoso Sales Sample for Power BI Desktop.SemanticModel (Governance workspace) with focus on audit remediation.
- Fact `fact_findings` provides both open and closed items; retains full history for aging trends.
- Dimensions: `dim_org`, `dim_date`; optional bridging table for severity ranking to drive sort order.
- Relationship directions from dimensions to fact to preserve row-level security.
- Sort-by: Severity sorted by severity rank; Status sorted by workflow order (Open > In Progress > Closed).
- Hidden fields: ActionOwner email, remediation notes, evidence links stored for drill-through only.
- Hierarchies: Org Region > Business Unit; Date Year > Quarter > Month.

## 3. Measures (DAX + Description)
```
Open Audit Findings Count =
    // TODO: Provide DAX via Power BI MCP filtering Status <> "Closed"
```
Description:
  Purpose: Track outstanding workload.
  Definition: Count of findings where Status is not Closed.
  Grain & Scope: Finding-level aggregated.
  Unit/Format: Whole number.
  Lineage: fact_findings[Status].
  QA: Must match remediation tracker export each refresh.

```
Total Audit Findings Count =
    // TODO: Provide DAX via Power BI MCP counting distinct FindingID
```
Description:
  Purpose: Provide context on total audit coverage.
  Definition: Distinct count of FindingID respecting filters.
  Grain & Scope: Finding-level aggregated.
  Unit/Format: Whole number.
  Lineage: fact_findings[FindingID].
  QA: Compare vs audit workpaper log; variance <= 1 per cycle.

```
Findings Aging (Days) =
    // TODO: Provide DAX via Power BI MCP calculating DATEDIFF(OpenDate, COALESCE(CloseDate, TODAY()), DAY)
```
Description:
  Purpose: Show timeliness of remediation.
  Definition: Average days between OpenDate and CloseDate (or today if open).
  Grain & Scope: Finding-level aggregated.
  Unit/Format: Decimal days (1 decimal).
  Lineage: fact_findings[OpenDate], fact_findings[CloseDate].
  QA: Validate sample vs audit tracker; tolerance +/- 2 days.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Open Audit Findings Count | Sum, Whole number | Display folder: 03_Audit |
| Total Audit Findings Count | Sum, Whole number | Display folder: 03_Audit |
| Findings Aging (Days) | Average, Decimal 1 | Display folder: 03_Audit |
| Severity | Ordered categorical | Sort using severity rank column |
| Action Code | Text | Use for grouping remediation approach |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline metrics | Open Findings Count, Aging, Severity mix | Include thresholds for >120 days |
| Heatmap | Exposure by org/severity | Org hierarchy, Severity, Open Findings Count | Diverging colors |
| Timeline | Track openings vs closures | Date hierarchy, Total Findings Count segmented by Status | Combo column/line |
| Detail Table | Operational tracker | FindingID, Severity, Status, Owner, Action Code, Due Date | enable drill-through to evidence |

## 6. Performance & Refresh
- Storage mode: Import with incremental policy (OpenDate >= rolling 36M) and archival table for historical >36M (optional dual-table).
- Refresh daily at 03:00 CET; partial refresh triggered after major audit workshop.
- Partition by OpenDate month; ensure query folding for due-date filters.
- Monitor dataset size as findings history grows; apply incremental close-out to keep dataset < 1 GB.

## 7. RLS/OLS Requirements
- Role `Audit_Global`: unrestricted read (Internal Audit team).
- Role `Org_Manager`: filter dim_org[OrgID] IN authorized list stored in bridge table.
- Optional `Action_Owner` row-level filter on ActionOwnerUPN to show only owned findings.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_findings -> dim_org | >= 99.9 % OrgID match | 0.1 % |
| RI_OK | fact_findings -> dim_date | All OpenDate values exist in dim_date | Hard fail |
| Aging_Captured | Findings Aging measure | Open findings must return aging >= 0 days | Hard fail |
| Owner_Assigned | fact_findings | Every open finding must have ActionOwner populated | 0 blanks |
