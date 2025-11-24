# Investment & CapEx Tracking - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_capex
  grain: project_period
  primary_key:
  - ProjectID
  - Period
  required_columns:
  - name: ProjectID
    type: string
    role: attribute
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Capex Category
    type: string
    role: attribute
  - name: Capex Actual Amount
    type: decimal
    role: amount
  - name: Capex Budget Amount
    type: decimal
    role: amount
- name: fact_cashflow
  grain: org_period
  primary_key:
  - OrgID
  - Period
  required_columns:
  - name: OrgID
    type: string
    role: org_key
  - name: Period
    type: date
    role: date_key
  - name: Operating Cash Flow Amount
    type: decimal
    role: amount
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Country
    type: string
  - name: BusinessUnit
    type: string
- name: dim_project
  grain: project
  primary_key:
  - ProjectID
  required_columns:
  - name: Pillar
    type: string
  - name: Program
    type: string
  - name: ProjectName
    type: string
  - name: Status
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Quarter
    type: int
  - name: Month
    type: int
relationships:
- from: fact_capex.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_capex.ProjectID
  to: dim_project.ProjectID
  cardinality: many-to-one
  direction: single
- from: fact_capex.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_cashflow.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_cashflow.Period
  to: dim_date.Date
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
- CapEx Amount (ID: fin.liquidity.capex.amount)
- CapEx Ratio % (ID: fin.liquidity.capex_ratio.pct)
- Operating Cash Flow Amount (ID: fin.liquidity.operating_cash_flow)

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
- Capex_vs_Budget_Reconciles
- Project_Status_Tracked

## 9. Model Mapping Reference
- Capex Actual Amount -> fact_capex[Capex Actual Amount]
- Capex Budget Amount -> fact_capex[Capex Budget Amount]
- Capex Category -> fact_capex[Capex Category]
- Operating Cash Flow Amount -> fact_cashflow[Operating Cash Flow Amount]
- Org -> dim_org[OrgID]
- Project -> dim_project[ProjectID]
- Date -> dim_date[Date]
