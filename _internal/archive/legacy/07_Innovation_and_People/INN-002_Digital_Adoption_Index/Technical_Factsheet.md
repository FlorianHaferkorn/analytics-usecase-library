# INN-002 Digital Adoption Index - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

`yaml
dimension:
  - name: dim_process
    grain: process
    columns:
      - {name: ProcessID, type: text, role: primary_key}
      - {name: ProcessArea, type: text}
      - {name: Subprocess, type: text}
      - {name: Owner, type: text}
      - {name: TargetAdoptionPct, type: decimal}
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
  - name: fact_digital_usage
    grain: process_user_day
    primary_key:
      - UserID
      - ProcessID
      - UsageDate
    columns:
      - {name: UserID, type: text, role: attribute}
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
      - {name: ProcessID, type: text, role: process_key, ref: dim_process}
      - {name: UsageDate, type: date_key, ref: dim_date}
      - {name: IsDigital, type: boolean, role: indicator}
      - {name: IsAutomated, type: boolean, role: indicator}
      - {name: TransactionsCount, type: int, role: amount}
      - {name: ManualHandlingMinutes, type: decimal, role: amount}
  - name: fact_process_baseline
    grain: process
    primary_key:
      - ProcessID
    columns:
      - {name: ProcessID, type: text, role: process_key, ref: dim_process}
      - {name: EligibleForDigital, type: boolean, role: indicator}
      - {name: StandardHandlingMinutes, type: decimal, role: amount}
relationships:
  - from: fact_digital_usage.ProcessID
    to: dim_process.ProcessID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_digital_usage.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_digital_usage.UsageDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
  - from: fact_process_baseline.ProcessID
    to: dim_process.ProcessID
    cardinality: one-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
`

## 2. Semantic Model Requirements
- Usage events streamed from process telemetry or application logs into act_digital_usage; refreshed daily with at least 12M history.
- Baseline table maintains eligibility and standard handling minutes; join via ProcessID to derive manual effort hours.
- Org hierarchy reused from corporate semantic model for consistent security and drill paths.
- Sort-by columns: ProcessAreaSort, SubprocessSort; maintain alphabetical fallback.
- Hidden helper fields: UserID, raw session identifiers, and event IDs kept for troubleshooting but hidden from visuals.
- Hierarchies: Org Region > Business Unit > Department (optional), Process Area > Subprocess.

## 3. Measures (DAX + Description)
`
Digital Transactions =
    // TODO: Provide DAX via Power BI MCP summing TransactionsCount where IsDigital = TRUE()
`
Description:
  Purpose: Numerator for adoption KPI.
  Definition: Sum of TransactionsCount filtered to IsDigital true.
  Unit/Format: Whole number.
  Lineage: fact_digital_usage.
  QA: Compare vs telemetry export.

`
Eligible Transactions =
    // TODO: Provide DAX via Power BI MCP summing TransactionsCount where EligibleForDigital = TRUE()
`
Description:
  Purpose: Denominator for adoption KPI.
  Definition: Sum of TransactionsCount where process eligible for digital execution (via baseline table).
  Unit/Format: Whole number.
  Lineage: fact_digital_usage joined to fact_process_baseline.
  QA: Eligible transactions must be >= digital transactions.

`
Digital Adoption Rate % =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Digital Transactions], [Eligible Transactions])
`
Description:
  Purpose: Headline KPI for transformation.
  Definition: Ratio of digital to eligible transactions.
  Unit/Format: Percentage 1 decimal.
  Lineage: measures above.
  QA: Compare vs digital program scorecards.

`
Automation Rate % =
    // TODO: Provide DAX via Power BI MCP summing IsAutomated transactions divided by Eligible Transactions
`
Description:
  Purpose: Measures fully automated volume.
  Definition: Automated transactions / eligible transactions.
  Unit/Format: Percentage 1 decimal.
  Lineage: fact_digital_usage[IsAutomated].
  QA: Validate vs automation platform logs.

`
Manual Effort Hours =
    // TODO: Provide DAX via Power BI MCP multiplying manual transactions by StandardHandlingMinutes / 60
`
Description:
  Purpose: Quantifies remaining manual workload.
  Definition: (Eligible Transactions - Digital Transactions) * Standard handling minutes / 60.
  Unit/Format: Decimal hours (1 decimal).
  Lineage: fact_digital_usage, fact_process_baseline.
  QA: Check vs process time studies; tolerance +/- 5 %.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Digital Adoption Rate % | No summarization, Percentage 1 | Display folder: 01_Digital |
| Automation Rate % | No summarization, Percentage 1 | Display folder: 01_Digital |
| Manual Effort Hours | Sum, Decimal 1 | Display folder: 02_Effort |
| Digital Transactions | Sum, Whole number | Display folder: 01_Digital |
| Eligible Transactions | Sum, Whole number | Hidden helper |
| Process hierarchy fields | Do not summarize | Provide Process Area > Subprocess |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline adoption metrics | Digital Adoption Rate %, Automation Rate %, Manual Effort Hours | Show variance vs target from dim_process.TargetAdoptionPct |
| Heatmap | Identify gaps | Org hierarchy, Process Area, Digital Adoption Rate % | Diverging color scale |
| Line Chart | Trend monitoring | Date hierarchy, Digital Adoption Rate %, Automation Rate % | 12M window |
| Waterfall | Explain adoption change | Drivers table (user growth, UX release) | Built using calculation table |
| Detail Table | Action tracking | Process, Owner, KPIs, Action Code | Include RAG indicators |

## 6. Performance & Refresh
- Storage mode: Import with incremental refresh on UsageDate (rolling 18M) due to large row counts; consider DirectLake if telemetry volume grows.
- Partition by UsageDate month; ensure Power Query filters fold to delta lake or SQL source.
- Refresh nightly (02:15 CET) plus intraday refresh for priority processes; baseline table refreshed weekly or on change.
- Apply compression by removing unused columns from telemetry feed.

## 7. RLS/OLS Requirements
- Role Digital_Global: unrestricted access.
- Role Org_Restricted: filter dim_org[OrgID] via mapping table per manager.
- Role Process_Owner: filter dim_process[Owner] to enforce process-level visibility.
- Optionally hide Manual Effort Hours for non transformation users via object-level security.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_digital_usage -> dim_process/dim_org/dim_date | >= 99.5 % match | 0.5 % |
| UsageEvents_Tracked | fact_digital_usage | No negative TransactionsCount; manual >= 0 | Hard fail |
| Adoption_Target_Check | dim_process | TargetAdoptionPct populated for all tracked processes | 0 blanks |
| Manual_Effort_Sanity | Manual Effort Hours | Eligible Transactions >= Digital Transactions | Hard fail |
| Change_Log_Consistency | Baseline vs telemetry | EligibleForDigital flag must exist before adoption calculation | Hard fail |
