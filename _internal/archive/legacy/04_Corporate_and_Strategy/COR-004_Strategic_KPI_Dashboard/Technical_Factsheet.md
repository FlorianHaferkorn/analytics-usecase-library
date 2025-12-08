# Strategic KPI Dashboard (Enterprise Performance Overview) - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_kpi_scores
  grain: kpi_org_month
  primary_key:
  - KpiID
  - OrgID
  - Month
  required_columns:
  - name: KpiID
    type: string
    role: attribute
  - name: OrgID
    type: string
    role: org_key
  - name: Month
    type: date
    role: date_key
  - name: Domain
    type: string
    role: attribute
  - name: ActualValue
    type: decimal
    role: amount
  - name: PlanValue
    type: decimal
    role: amount
  - name: TargetValue
    type: decimal
    role: amount
  - name: Status
    type: string
    role: status
  - name: Owner
    type: string
    role: attribute
  - name: Commentary
    type: string
    role: text
- name: fact_initiatives
  grain: initiative
  primary_key:
  - InitiativeID
  required_columns:
  - name: InitiativeName
    type: string
    role: attribute
  - name: LinkedKpiID
    type: string
    role: attribute
  - name: Status
    type: string
    role: status
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: BusinessUnit
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
- name: dim_kpi
  grain: kpi
  primary_key:
  - KpiID
  required_columns:
  - name: KPIName
    type: string
  - name: Domain
    type: string
  - name: SourceUseCase
    type: string
  - name: Frequency
    type: string
relationships:
- from: fact_kpi_scores.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_kpi_scores.Month
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_kpi_scores.KpiID
  to: dim_kpi.KpiID
  cardinality: many-to-one
  direction: single
- from: fact_initiatives.LinkedKpiID
  to: dim_kpi.KpiID
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required facts/dims per contract above.
- Ensure relationships are single-direction many-to-one (role-playing dates if needed).
- Provide conformed Org/Product/Initiative hierarchies.

## 3. Measures (DAX + Description)
Following KPIs require measures (DAX delivered separately):
- "% Net Sales (ID: sales.net_sales.delta_pct.ly)
- Gross Margin % (ID: margin.gm.pct)
- Cash Conversion Cycle (Days) (ID: ops.working_capital.ccc.days)
- Turnover Rate % (ID: hr.turnover.pct)
- ESG-Aligned Revenue % (ID: esg.aligned_revenue.pct)
- Project ROI % (ID: corp.project.roi.pct)

## 4. Defaults & Formatting
- Apply correct format strings (currency, %, integer).
- Use display folders (01_Strategic, 02_Variance, etc.).
- Set data categories for Org/Initiative/Timeline fields.

## 5. Visual / Interaction Requirements
- Map visuals (cards, bridges, funnels) to required fields.
- Define drill paths for Org, Initiative, Time.
- Specify tooltip fields and sort-by logic.

## 6. Performance & Refresh
- Storage mode: Import (unless monthly snapshot suggests Hybrid).
- Refresh cadence aligned with corporate close cadence.
- Partitioning by FiscalPeriod where data volume is high.

## 7. RLS/OLS Requirements
- Org-based RLS (Region/Entity).
- Optional Initiative-based restrictions for project owners.

## 8. QA & Validation Rules
- RI_OK
- KPI_Source_Registered
- Plan_Actual_Alignment

## 9. Model Mapping Reference
- Actual Value -> fact_kpi_scores[ActualValue]
- Plan Value -> fact_kpi_scores[PlanValue]
- Target Value -> fact_kpi_scores[TargetValue]
- Status -> fact_kpi_scores[Status]
- Owner -> fact_kpi_scores[Owner]
- Commentary -> fact_kpi_scores[Commentary]
- KPI Name -> dim_kpi[KPIName]
- Domain -> dim_kpi[Domain]
- Source Use Case -> dim_kpi[SourceUseCase]
- Org -> dim_org[OrgID]
- Date -> dim_date[Date]
