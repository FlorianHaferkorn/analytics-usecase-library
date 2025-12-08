# Profitability Overview (EBITDA & Net Margin) - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_pnl
  grain: org_period_pnl
  primary_key:
  - OrgID
  - Period
  - PnLLine
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: PnLLine
    type: string
    role: attribute
  - name: Amount
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
  - name: BusinessUnit
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
- from: fact_pnl.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_pnl.Period
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
- Net Sales Amount (ID: sales.net_sales.amount)
- COGS Amount (ID: cost.cogs.amount)
- EBITDA Margin % (ID: profit.ebitda_margin)

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
- P&L_Reconciles
- GrossMargin_Consistent

## 9. Model Mapping Reference
- PnL Amount -> fact_pnl[Amount]
- PnL Line -> fact_pnl[PnLLine]
- Org -> dim_org[OrgID]
- Date -> dim_date[Date]
