# GOV-003 Risk and Control Testing - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

```yaml
dimension:
  - name: dim_control
    grain: control
    columns:
      - {name: ControlID, type: text, role: primary_key}
      - {name: RiskCategory, type: text}
      - {name: Process, type: text}
      - {name: ControlName, type: text}
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
fact:
  - name: fact_controls
    grain: control_test
    columns:
      - {name: ControlTestID, type: text, role: primary_key}
      - {name: ControlID, type: text, role: control_key, ref: dim_control}
      - {name: TestDate, type: date_key, ref: dim_date}
      - {name: Result, type: text, role: attribute}
      - {name: Tester, type: text, role: attribute}
      - {name: EvidenceURL, type: text, role: helper}
  - name: fact_findings
    grain: finding
    columns:
      - {name: FindingID, type: text, role: primary_key}
      - {name: ControlID, type: text, role: control_key, ref: dim_control}
      - {name: Severity, type: text, role: attribute}
      - {name: IsOpen, type: boolean, role: indicator}
      - {name: OpenDate, type: date_key, ref: dim_date}
      - {name: CloseDate, type: date, role: helper}
relationships:
  - from: fact_controls.ControlID
    to: dim_control.ControlID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_controls.TestDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
  - from: fact_findings.ControlID
    to: dim_control.ControlID
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
- Fact tables: `fact_controls` (test executions) and `fact_findings` (issues) within same dataset.
- Conformed dimension `dim_control` shared across both facts to enable lineage from control to findings.
- Additional helper dimension `dim_riskcategory` optional for standardizing taxonomy; can be derived from dim_control.
- Relationship directions single (dimension -> fact) to enable additive RLS by Control Owner.
- Sort-by: ControlName sorted by ControlID to keep naming consistent.
- Hidden columns: EvidenceURL, tester comments, sampling details (exposed only in drill-through page).
- Hierarchies: Risk Category > Process > ControlName; Date hierarchy reused for both facts.

## 3. Measures (DAX + Description)
```
Audit Findings Count =
    // TODO: Provide DAX via Power BI MCP counting distinct FindingID
```
Description:
  Purpose: Total findings raised during selected period.
  Definition: Distinct count of finding IDs filtered by slicers.
  Grain & Scope: Finding-level aggregated.
  Unit/Format: Whole number.
  Lineage: fact_findings[FindingID].
  QA: Tie out with audit workpaper export (variance <= 1 per cycle).

```
Open Audit Findings Count =
    // TODO: Provide DAX via Power BI MCP filtering IsOpen = TRUE()
```
Description:
  Purpose: Shows outstanding backlog.
  Definition: Count of findings where IsOpen = TRUE().
  Grain & Scope: Finding-level aggregated.
  Unit/Format: Whole number.
  Lineage: fact_findings[IsOpen].
  QA: Compare vs remediation tracking tool; expect 100 % alignment.

```
Control Pass Rate % =
    // TODO: Provide DAX via Power BI MCP dividing Passed tests by Total tests
```
Description:
  Purpose: KPI for control effectiveness.
  Definition: Number of tests with Result = "Pass" divided by all completed tests.
  Grain & Scope: Control-test level aggregated.
  Unit/Format: Percentage with 1 decimal.
  Lineage: fact_controls[Result].
  QA: Validate vs manual test logs; tolerance +/- 1 pp.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Audit Findings Count | Sum, Whole number | Display folder: 02_Risk & Control |
| Open Audit Findings Count | Sum, Whole number | Display folder: 02_Risk & Control |
| Control Pass Rate % | No summarization, Percentage, 1 decimal | Display folder: 02_Risk & Control |
| Severity | Ordered categorical | Sort by severity rank column |
| Risk Category Hierarchy | Do not summarize | Provide drill Risk Category > Process > ControlName |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline metrics | Control Pass Rate %, Audit Findings Count, Open Findings Count | Provide delta vs prior quarter |
| Heatmap | Risk/process concentration | Risk Category hierarchy, Control Pass Rate % | Diverging colors (green >=90 %, red <80 %) |
| Line Chart | Findings trend | Date hierarchy, Audit Findings Count, Open Findings Count | Plot opened vs closed per quarter |
| Table | Remediation tracker | FindingID, Severity, Owner, Action Code, Due Date | Add conditional formatting for overdue |

## 6. Performance & Refresh
- Storage mode: Import; incremental refresh on OpenDate/TestDate (rolling 36 months) to keep long trend.
- Partition both facts by Year-Month; ensure query folding via parameterized dataflow.
- Refresh daily; additional refresh after Internal Audit uploads new cycles.
- Monitor composite size; consider aggregations for historical pass rate if dataset exceeds capacity.

## 7. RLS/OLS Requirements
- Role `Control_Owner`: filter dim_control[OwnerUPN] matches USERPRINCIPALNAME().
- Role `Audit_Viewer`: unrestricted read for Internal Audit team (list in security table).
- Optional Process-specific roles using mapping table (Process -> Allowed Groups).

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_controls -> dim_control | >= 99.9 % ControlID match | 0.1 % |
| Referential Integrity | fact_findings -> dim_control | >= 99.9 % ControlID match | 0.1 % |
| Controls_Tested | fact_controls | Every planned control must show at least one test per cycle | Alert if missing |
| Findings_Tracked | fact_findings | IsOpen and Severity must be populated for all findings | 0 blanks |
