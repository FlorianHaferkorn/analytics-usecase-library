---
id: COM-003
factsheet_type: technical
---

# COM-003 - Customer Value  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Commercial / CustomerValue
- **Technical Owner:** Sales Ops BI Lead
- **Model ID:** commercial_customer_value
- **Source Systems:** ERP/CRM, DWH
- **Business Factsheet:** ./Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** core/core/core/data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** core/core/core/data_contracts/sources/commercial.yaml
- **Semantic Model Definition:** core/core/core/semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** core/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** core/core/core/semantic_models/domains/CustomerValue/Measure_Dictionary_CustomerValue.md
- **Action Codes:** core/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: crm.clv.amount
    measure_name: Customer Lifetime Value Amount
    format: "EUR #,0"
    folder: 04_Customer

  - kpi_id: crm.lifetime_revenue.amount
    measure_name: Customer Lifetime Revenue Amount
    format: "EUR #,0"
    folder: 01_Revenue

  - kpi_id: crm.retention.pct
    measure_name: Customer Retention %
    format: "0.0%"
    folder: 01_Retention

  - kpi_id: crm.churned_customers.count
    measure_name: Churned Customers Count
    format: "#,0"
    folder: 01_Retention

  - kpi_id: crm.revenue_at_risk.amount
    measure_name: Revenue at Risk Amount
    format: "EUR #,0"
    folder: 01_Retention

  - kpi_id: crm.active_customers.count
    measure_name: Active Customers Count
    format: "#,0"
    folder: 01_Retention

  - kpi_id: crm.nps.index
    measure_name: NPS Score
    format: "0"
    folder: 02_CX

  - kpi_id: crm.complaint.count
    measure_name: Customer Complaints Count
    format: "#,0"
    folder: 02_CX
```

---

## 3. Data Contract Scope (Subset YAML)

```yaml
required_facts:
  - fact_sales
  - fact_customer_events
  - fact_customer_value
  - fact_experience
  - fact_nps
required_dimensions:
  - dim_date
  - dim_org
  - dim_customer
  - dim_product
  - security_user_org
required_grain: customer_month (for retention/churn/risk), invoice_line for revenue/margin
required_time_range: 24 months history
required_slicers: Date, Region/Channel, Customer Segment, Product Category

dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Quarter, type: text}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: OrgCode, type: text}
      - {name: OrgName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Channel, type: text}

  - name: dim_customer
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: CustomerCode, type: text}
      - {name: CustomerName, type: text}
      - {name: Segment, type: text}
      - {name: Channel, type: text}
      - {name: Region, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: Brand, type: text}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_sales
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity, type: decimal, agg: sum}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}

  - name: fact_customer_events
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: Activity Flag, type: boolean}
      - {name: Churn Flag, type: boolean}
      - {name: Attrition Risk %, type: decimal, nullable: true}

  - name: fact_customer_value   # CLV / revenue at risk
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: CLV Amount, type: currency}
      - {name: CLV Remaining Amount, type: currency, nullable: true}

  - name: fact_experience
    columns:
      - {name: Complaint ID, type: text}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: DateKey, type: int, ref: dim_date}
      - {name: Severity, type: text, nullable: true}

  - name: fact_nps
    columns:
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: DateKey, type: int, ref: dim_date}
      - {name: NPS Score, type: int}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 4. Semantic Model Requirements

- Use certified monthly aggregates for retention/churn/CLV/risk; fact tables at customer_month where possible.
- Depend on conformed dimensions (Date, Org, Customer, Product); no local dimension copies.
- No new measures introduced locally; use certified dictionary names.
- Facts for customer events, customer value, experience, and NPS are defined in the domain contract to satisfy KPIs.

### 4.1 Tables

- dim_date, dim_org, dim_customer, dim_product, security_user_org  
- fact_sales, fact_customer_events, fact_customer_value, fact_experience, fact_nps

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> fact_sales on OrgKey  
- dim_customer (1) -> all customer-facing facts on CustomerKey  
- dim_product (1) -> fact_sales on ProductKey  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-directional except RLS bridge if required.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month  
- Org: Region -> Country -> Channel -> OrgName  
- Customer: Segment -> CustomerName  
- Product: Category -> Subcategory -> ProductName

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- CustomerName -> CustomerCode  
- ProductName -> ProductCode

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; display folders per dictionary.  
- Surrogate keys mandatory; avoid M2M; use conformed dimensions; aggregation tables optional but must retain grain integrity.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Customer Lifetime Value Amount | crm.clv.amount | Customer value base | 04_Customer | EUR #,0 | KPI |
| Customer Lifetime Revenue Amount | crm.lifetime_revenue.amount | Lifetime revenue base | 01_Revenue | EUR #,0 | Supporting |
| Customer Retention % | crm.retention.pct | Retention rate | 01_Retention | 0.0% | KPI |
| Churned Customers Count | crm.churned_customers.count | Churn volume | 01_Retention | #,0 | Supporting |
| Revenue at Risk Amount | crm.revenue_at_risk.amount | Revenue exposure | 01_Retention | EUR #,0 | Supporting |
| Active Customers Count | crm.active_customers.count | Active base | 01_Retention | #,0 | Supporting |
| NPS Score | crm.nps.index | Experience score | 02_CX | 0 | KPI |
| Customer Complaints Count | crm.complaint.count | Complaint volume | 02_CX | #,0 | Supporting |

### 5.2 DAX Definitions

No local DAX added; measures sourced from certified semantic model. Existing certified expressions apply.

---

## 6. RLS / OLS Requirements

### 6.1 Security Table Pattern

### 6.2 RLS Rule (Fabric / Power BI)

### 6.3 OLS (optional)

- Executives and commercial leaders require correct region/channel scoping; apply existing Org-hierarchy RLS (security_user_org) cascading to facts.
- No new RLS rules created for this use case; reuse canonical pattern.

---

## 7. Technical Assumptions

- Churn/retention flags and attrition risk available in fact_customer_events.
- CLV and CLV Remaining provided upstream via fact_customer_value.
- Complaint events captured in fact_experience; NPS scores available in fact_nps.
- Currency/fiscal settings per data governance.
- Attrition Risk % delivered as 0-100; model scales to 0-1 for calculations. CLV/Remaining follow finance-approved discount rate and CLV horizon (WACC and agreed horizon).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import depending on SLA; incremental refresh by Month.
- Aggregations optional for long history; avoid grain distortion.
- Workspace and naming per governance; display folders per measure dictionary.

---

## 9. QA & Validation Rules

- KPIs must reconcile with domain reports (sales/churn/CLV/CX).
- Only certified measures allowed; no local KPI calculations.
- Active/churned bases must reconcile to customer events; CLV/risk reconcile to upstream mart; NPS/complaints reconcile to CX sources.

---

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md




