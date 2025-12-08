# Unit Cost & COGS Drivers ? Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_production
  grain: product_line_day
  primary_key:
  - ProductionID
  required_columns:
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
  - name: Produced Units Qty
    type: decimal
    role: quantity
  - name: Direct Labor Cost Amount
    type: decimal
    role: amount
  - name: Energy Cost Amount
    type: decimal
    role: amount
  - name: Material Cost Amount
    type: decimal
    role: amount
  - name: Other Production Cost Amount
    type: decimal
    role: amount
- name: fact_cogs
  grain: product_org_period
  primary_key:
  - CogsID
  required_columns:
  - name: COGS Amount
    type: decimal
    role: amount
  - name: Date
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: ProductID
    type: string
    role: product_key
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Plant
    type: string
  - name: Line
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
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_production.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_production.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_production.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_cogs.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_cogs.ProductID
  to: dim_product.ProductID
  cardinality: many-to-one
  direction: single
- from: fact_cogs.Date
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
```

## 2. Model Mapping
- Produced Units Qty: fact_production[Produced Units Qty]
- Direct Labor Cost Amount: fact_production[Direct Labor Cost Amount]
- Energy Cost Amount: fact_production[Energy Cost Amount]
- Material Cost Amount: fact_production[Material Cost Amount]
- Other Production Cost Amount: fact_production[Other Production Cost Amount]
- COGS Amount: fact_cogs[COGS Amount]
- Org: dim_org[OrgID]
- Product: dim_product[ProductID]
- Date: dim_date[Date]

## 3. Dataset & QA
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- RI_OK
- COGS_Positive
- UnitCost_Reconciles

## 4. Measures / DAX
TODO: add KPI measures following the template.

## 5. Visual / Formatting / RLS
TODO: capture formatting, visuals, RLS per template.
