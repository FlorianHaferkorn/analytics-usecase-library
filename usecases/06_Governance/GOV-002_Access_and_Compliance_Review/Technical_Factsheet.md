# GOV-002 Access and Compliance Review - Technical Factsheet

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
  - name: fact_compliance
    grain: incident
    columns:
      - {name: IncidentID, type: text, role: primary_key}
      - {name: System, type: text, role: attribute}
      - {name: Application, type: text, role: attribute}
      - {name: RoleName, type: text, role: attribute}
      - {name: Severity, type: text, role: attribute}
      - {name: IsBreach, type: boolean, role: indicator}
      - {name: Status, type: text, role: attribute}
      - {name: OpenDate, type: date_key, ref: dim_date}
      - {name: CloseDate, type: date, role: helper}
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
relationships:
  - from: fact_compliance.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_compliance.OpenDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

## 2. Semantic Model Requirements
- Semantic model: Contoso Sales Sample for Power BI Desktop.SemanticModel (Governance subject area workspace).
- Required fact `fact_compliance` sourced from centralized GRC tool; refresh daily.
- Conformed dimensions: `dim_org`, `dim_date`; optional `dim_severity` derived in Power Query for grouping.
- Relationship structure: star schema, single direction filters from dimensions to fact to simplify RLS.
- Sort-by columns: Severity sorted by custom numeric severity rank; RoleName sorted by RoleName.
- Hidden technical fields: rule/event ID, ingestion timestamp; necessary for lineage but hidden from report view.
- Hierarchies: Org Region > Business Unit > System; Date hierarchy reused from `dim_date`.

## 3. Measures (DAX + Description)
```
Compliance Incidents Count =
    // TODO: Provide DAX via Power BI MCP counting distinct IncidentID respecting filters
```
Description:
  Purpose: Base KPI for workload and trend analysis.
  Definition: Distinct count of IncidentID over selected period.
  Grain & Scope: Incident-level aggregated to any slicer context.
  Unit/Format: Whole number.
  Lineage: fact_compliance[IncidentID].
  QA: Must reconcile with incident register export (variance <= 1 case per cycle).

```
Compliance Breach Count =
    // TODO: Provide DAX via Power BI MCP filtering IsBreach = TRUE()
```
Description:
  Purpose: Highlights regulatory-impact incidents.
  Definition: Count of incidents flagged as breach.
  Grain & Scope: Incident-level aggregated.
  Unit/Format: Whole number.
  Lineage: fact_compliance[IsBreach].
  QA: Should equal compliance breach log; manual review after each refresh.

```
Incident Closure Rate % =
    // TODO: Provide DAX via Power BI MCP calculating Closed incidents / Total incidents
```
Description:
  Purpose: Measures process efficiency.
  Definition: Ratio of incidents with Status = "Closed" to all incidents in selected period.
  Grain & Scope: Incident-level aggregated.
  Unit/Format: Percentage with 1 decimal.
  Lineage: fact_compliance[Status].
  QA: Validate vs workflow tool using sample-based reconciliation.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Compliance Incidents Count | Sum, Whole number | Display folder: 01_Compliance |
| Compliance Breach Count | Sum, Whole number | Display folder: 01_Compliance |
| Incident Closure Rate % | No summarization, Percentage, 1 decimal | Display folder: 01_Compliance |
| Severity | Ordered categorical | Sort by severity rank column |
| Org Region hierarchy | Do not summarize | Provide drill path Region > Business Unit > System |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline status | Incidents Count, Breach Count, Closure Rate % | Compare vs target lines |
| Tree Map | Concentration of issues | Org hierarchy, Incidents Count | Color by Severity |
| Line Chart | Trend over time | Date hierarchy, Incidents/Breaches | 12M rolling window |
| Table | SLA + remediation detail | IncidentID, Status, Owner, Action Code | Include conditional formatting on overdue items |

## 6. Performance & Refresh
- Storage mode: Import; incremental logic filtering OpenDate by rolling 24M window.
- Refresh cadence: daily (02:15 CET) plus on-demand run before steering meetings.
- Partition fact by OpenDate month to limit refresh footprint.
- Add query folding filters in dataflow to restrict to governed systems only.

## 7. RLS/OLS Requirements
- Role: `Compliance_Global` full access.
- Role: `Org_Restricted` with filter `dim_org[OrgID] IN USERPRINCIPALNAME()` mapping table.
- Optional Application Owner role filtering by System column using bridge table.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_compliance -> dim_org/dim_date | >= 99.5 % row match | 0.5 % |
| RI_OK | Dataset | No orphan incidents after refresh | Hard fail |
| Violations_Tracked | Measures | Every incident with Severity = High must have Status populated | 0 missing |
