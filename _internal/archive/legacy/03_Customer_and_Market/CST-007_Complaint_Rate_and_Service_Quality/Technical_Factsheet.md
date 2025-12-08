# Complaint Rate & Service Quality - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_complaints
  grain: complaint
  primary_key:
  - ComplaintID
  required_columns:
  - name: ComplaintID
    type: string
    role: attribute
  - name: CustomerID
    type: string
    role: customer_key
  - name: OrderID
    type: string
    role: attribute
  - name: Complaint Date
    type: date
    role: date_key
  - name: Category
    type: string
    role: attribute
  - name: Reason
    type: string
    role: attribute
  - name: Severity
    type: string
    role: status
  - name: Status
    type: string
    role: status
- name: fact_customer_transactions
  grain: customer_day
  primary_key:
  - CustomerID
  - Date
  required_columns:
  - name: CustomerID
    type: string
    role: customer_key
  - name: Date
    type: date
    role: date_key
  - name: Net Sales Amount
    type: decimal
    role: amount
  - name: Channel
    type: string
    role: channel
dims:
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Region
    type: string
  - name: Market
    type: string
  - name: Segment
    type: string
  - name: LoyaltyTier
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_complaints.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_complaints."Complaint Date"
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_customer_transactions.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_customer_transactions.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required conform dimensions as per data contract.
- Relationships follow the structure listed above (single-direction many-to-one).
- Ensure role-playing dates/channel dimensions as needed for customer journeys.

## 3. Measures (DAX + Description)
Following KPIs need measures (DAX to be provided separately):
- Complaint Rate % (ID: crm.complaint.rate.pct)
- Complaint Count (ID: crm.complaint.count)
- Customer Retention % (ID: crm.retention.pct)

## 4. Defaults & Formatting
- Apply appropriate format strings (Currency, %, whole numbers) per KPI.
- Provide display folders (e.g., 01_Customer, 02_Journey).
- Set data categories for Customer, Channel, Touchpoint columns.

## 5. Visual / Interaction Requirements
- Map each visual (cards, trends, heatmaps) to required fields and measures.
- Specify sort-by columns for segment hierarchies.
- Define tooltips/drill-through targets for survey comments or journeys.

## 6. Performance & Refresh
- Refresh cadence aligned with survey uploads (daily/weekly).
- Storage mode: Import.
- Partitioning by survey month where volumes are high.

## 7. RLS/OLS Requirements
- Customer/Region-based RLS as per dim_customer attributes.
- Optional channel-based restrictions for partner views.

## 8. QA & Validation Rules
- RI_OK
- Complaints_Mapped_To_Orders
- Complaint_Rate_Within_0_100

## 9. Model Mapping Reference
- Complaint ID -> fact_complaints[ComplaintID]
- Complaint Date -> fact_complaints[Complaint Date]
- Complaint Reason -> fact_complaints[Reason]
- Complaint Severity -> fact_complaints[Severity]
- Complaint Status -> fact_complaints[Status]
- Customer ID -> dim_customer[CustomerID]
- Channel -> fact_customer_transactions[Channel]
- Date -> dim_date[Date]
