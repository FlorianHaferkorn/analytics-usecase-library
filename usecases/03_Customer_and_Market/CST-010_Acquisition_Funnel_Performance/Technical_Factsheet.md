# Acquisition Funnel Performance - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_leads
  grain: lead
  primary_key:
  - LeadID
  required_columns:
  - name: LeadID
    type: string
    role: attribute
  - name: Lead Source
    type: string
    role: attribute
  - name: Channel
    type: string
    role: channel
  - name: Campaign
    type: string
    role: attribute
  - name: Lead Date
    type: date
    role: date_key
  - name: Lead Status
    type: string
    role: status
- name: fact_acquisitions
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: CustomerID
    type: string
    role: customer_key
  - name: Acquisition Date
    type: date
    role: date_key
  - name: Channel
    type: string
    role: channel
  - name: Campaign
    type: string
    role: attribute
  - name: Acquisition Cost Amount
    type: decimal
    role: amount
dims:
- name: dim_date
  grain: date
  primary_key:
  - Date
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
relationships:
- from: fact_acquisitions.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
- from: fact_acquisitions."Acquisition Date"
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
- Leads Count (ID: crm.acquisition.leads.count)
- New Customers Acquired (ID: crm.acquisition.conversions.count)
- Conversion Rate % (ID: crm.acquisition.conversion_rate.pct)
- Customer Acquisition Cost (CAC) (ID: crm.acquisition.cac.amount)

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
- Funnel_Steps_Consistent
- Attribution_Method_Documented

## 9. Model Mapping Reference
- Lead ID -> fact_leads[LeadID]
- Lead Source -> fact_leads[Lead Source]
- Lead Status -> fact_leads[Lead Status]
- Campaign -> fact_leads[Campaign]
- Acquisition Cost Amount -> fact_acquisitions[Acquisition Cost Amount]
- Customer ID -> dim_customer[CustomerID]
- Date -> dim_date[Date]
