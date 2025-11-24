# Headcount Efficiency & Revenue per FTE - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_headcount
  grain: org_function_month
  primary_key:
  - OrgID
  - FunctionID
  - Month
  required_columns:
  - name: OrgID
    type: string
    role: org_key
  - name: FunctionID
    type: string
    role: attribute
  - name: Month
    type: date
    role: date_key
  - name: FTE Count
    type: decimal
    role: helper
  - name: Personnel Cost Amount
    type: decimal
    role: amount
- name: fact_financials
  grain: org_month
  primary_key:
  - OrgID
  - Month
  required_columns:
  - name: OrgID
    type: string
    role: org_key
  - name: Month
    type: date
    role: date_key
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Gross Margin Amount
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
- name: dim_function
  grain: function
  primary_key:
  - FunctionID
  required_columns:
  - name: FunctionName
    type: string
  - name: Department
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Month
    type: int
relationships:
- from: fact_headcount.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_headcount.FunctionID
  to: dim_function.FunctionID
  cardinality: many-to-one
  direction: single
- from: fact_headcount.Month
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_financials.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_financials.Month
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
- Revenue per FTE (ID: hr.revenue_per_fte.amount)
- Personnel Cost Ratio % (ID: hr.personnel_cost_ratio.pct)
- Gross Margin per FTE (ID: hr.gm_per_fte.amount)

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
- Headcount_Positive
- FTE_Calculation_Consistent

## 9. Model Mapping Reference
- FTE Count -> fact_headcount[FTE Count]
- Personnel Cost Amount -> fact_headcount[Personnel Cost Amount]
- Net Sales Amount -> fact_financials[Net Sales Amount]
- Gross Margin Amount -> fact_financials[Gross Margin Amount]
- Org -> dim_org[OrgID]
- Function -> dim_function[FunctionID]
- Date -> dim_date[Date]
