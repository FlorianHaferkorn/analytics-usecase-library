# Customer Profitability Across Lifecycle - Technical Factsheet

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
  - name: COGS Amount
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
- name: fact_marketing_spend
  grain: customer_campaign
  primary_key:
  - CustomerID
  - CampaignID
  required_columns:
  - name: CustomerID
    type: string
    role: customer_key
  - name: Acquisition Spend Amount
    type: decimal
    role: amount
- name: fact_complaint
  grain: complaint
  primary_key:
  - ComplaintID
  required_columns:
  - name: ComplaintID
    type: string
    role: attribute
  - name: Date
    type: date
    role: date_key
  - name: CustomerID
    type: string
    role: customer_key
  - name: Complaint Cost Amount
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
  - name: LifecycleStage
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
- from: fact_customer_metrics.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_metrics.Period
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_marketing_spend.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_complaint.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_complaint.Date
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
- Customer Margin Amount (ID: margin.customer.amount)
- Customer Margin % (ID: margin.customer.pct)
- Customer Lifetime Value (CLV) Amount (ID: crm.clv.amount)
- Customer Acquisition Cost (CAC) Amount (ID: crm.acquisition.cac.amount)
- Customer Retention % (ID: crm.retention.pct)
- Customer Churn Rate % (ID: crm.churn.pct)
- Complaint Rate % (ID: crm.complaint.rate.pct)

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
- Customer_ID_Consistent
- Lifecycle_Stage_Defined

## 9. Model Mapping Reference
- Net Sales Amount -> fact_sales[Net Sales Amount]
- COGS Amount -> fact_sales[COGS Amount]
- CLV Amount -> fact_customer_metrics[CLV Amount]
- Acquisition Spend Amount -> fact_marketing_spend[Acquisition Spend Amount]
- Complaint Cost Amount -> fact_complaint[Complaint Cost Amount]
- Date -> dim_date[Date]
- Org -> dim_org[OrgID]
- Customer -> dim_customer[CustomerID]
