# Enterprise Performance Cockpit - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_sales
  grain: invoice_line
  primary_key:
  - InvoiceLineID
  required_columns:
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: ProductID
    type: string
    role: product_key
- name: fact_balance
  grain: org_period_balance
  primary_key:
  - OrgID
  - Period
  - BalanceLine
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: BalanceLine
    type: string
    role: attribute
  - name: Amount
    type: decimal
    role: amount
- name: fact_working_capital
  grain: org_period_wc
  primary_key:
  - OrgID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: DSO Days
    type: decimal
    role: helper
  - name: DPO Days
    type: decimal
    role: helper
  - name: DIO Days
    type: decimal
    role: helper
- name: fact_hr
  grain: org_period_hr
  primary_key:
  - OrgID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Headcount FTE
    type: decimal
    role: helper
  - name: Personnel Cost Amount
    type: decimal
    role: amount
  - name: Leavers Count
    type: int
    role: helper
- name: fact_customer_metrics
  grain: customer_period
  primary_key:
  - CustomerID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: Active Flag
    type: bool
    role: indicator
  - name: Churn Flag
    type: bool
    role: indicator
  - name: CLV Amount
    type: decimal
    role: amount
- name: fact_esg
  grain: org_period_esg
  primary_key:
  - OrgID
  - Period
  required_columns:
  - name: Period
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ESG-Aligned Revenue Amount
    type: decimal
    role: amount
  - name: Total Revenue Amount
    type: decimal
    role: amount
  - name: CO2 Emissions tCO2e
    type: decimal
    role: amount
dims:
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
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: BusinessUnit
    type: string
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
- name: dim_product
  grain: product
  primary_key:
  - ProductID
  required_columns:
  - name: Category
    type: string
  - name: Subcategory
    type: string
relationships:
- from: fact_sales.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_sales.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_sales.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_sales.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_balance.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_balance.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_working_capital.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_working_capital.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_hr.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_hr.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_customer_metrics.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_metrics.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_esg.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_esg.Period
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
- Revenue Growth % (ID: sales.revenue.growth_pct)
- Gross Margin % (ID: margin.gm.pct)
- EBITDA Margin % (ID: profit.ebitda_margin)
- Working Capital % (ID: fin.liquidity.working_capital)
- Cash Conversion Cycle (Days) (ID: ops.working_capital.ccc.days)
- Inventory Turnover (ID: ops.inventory.turnover)
- Inventory Days on Hand (DIO) (ID: ops.inventory.days)
- Customer Retention % (ID: crm.retention.pct)
- Customer Lifetime Value (CLV) Amount (ID: crm.clv.amount)
- Revenue per FTE Amount (ID: hr.revenue_per_fte.amount)
- Employee Turnover % (ID: hr.turnover.pct)
- ESG-Aligned Revenue % (ID: esg.aligned_revenue.pct)
- Total CO Emissions (tCO2e) (ID: esg.co2.total.tco2e)

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
- KPI_Definitions_Aligned
- P&L_Reconciles

## 9. Model Mapping Reference
- Net Sales Amount -> fact_sales[Net Sales Amount]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
- Customer -> dim_customer[CustomerID]
- Product -> dim_product[ProductID]
- ESG-Aligned Revenue Amount -> fact_esg[ESG-Aligned Revenue Amount]
- Total Revenue Amount -> fact_esg[Total Revenue Amount]
- CO2 Emissions tCO2e -> fact_esg[CO2 Emissions tCO2e]
