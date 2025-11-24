# Sales Funnel & Win–Loss Analysis ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_opportunity
  grain: opportunity
  primary_key:
  - OpportunityID
  required_columns:
  - name: OpportunityID
    type: string
    role: attribute
  - name: Opportunity Amount
    type: decimal
    role: amount
  - name: Close Amount
    type: decimal
    role: amount
  - name: Open Date
    type: date
    role: date_key
  - name: Close Date
    type: date
    role: date_key
  - name: Stage
    type: string
    role: attribute
  - name: Status
    type: string
    role: status
  - name: SalesRepID
    type: string
    role: attribute
  - name: CustomerID
    type: string
    role: customer_key
  - name: OrgID
    type: string
    role: org_key
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Area
    type: string
  - name: SalesTeam
    type: string
- name: dim_customer
  grain: customer
  primary_key:
  - CustomerID
  required_columns:
  - name: Segment
    type: string
  - name: Industry
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_opportunity.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_opportunity.CustomerID
  to: dim_customer.CustomerID
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Opportunity Amount: fact_opportunity[Opportunity Amount]
- Close Amount: fact_opportunity[Close Amount]
- Stage: fact_opportunity[Stage]
- Status: fact_opportunity[Status]
- Org: dim_org[OrgID]
- Customer: dim_customer[CustomerID]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- Opp_Stage_Consistent
- Pipeline_Reconciles

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
