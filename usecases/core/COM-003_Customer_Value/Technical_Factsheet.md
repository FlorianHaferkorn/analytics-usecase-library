# COM-003 — Customer Value  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Sales Ops BI Lead
- **Model ID:** commercial_customer_value
- **Source Systems:** ERP/CRM, DWH
- **Business Factsheet:** usecases/core/COM-003_Customer_Value/Business_Factsheet.md

---

## 1. Model References
- **Domain Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** data_contracts/sources/commercial.yaml
- **Semantic Model Definition:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** framework/kpi_catalog/domain_measure_dictionary.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs → Measure Mapping (Mandatory)
```yaml
kpi_to_measure_mapping:
  - kpi_id: crm.clv.amount
    kpi_name: Customer Lifetime Value
    measure_name: [Customer Lifetime Value]
    format: €#,0
    folder: 04_Customer
  - kpi_id: margin.customer.amount
    kpi_name: Customer Margin Amount
    measure_name: [Customer Margin Amount]
    format: €#,0
    folder: 02_Margin
  - kpi_id: crm.retention.pct
    kpi_name: Retention Rate %
    measure_name: [Retention %]
    format: 0.0%
    folder: 04_Customer
  - kpi_id: crm.churn.pct
    kpi_name: Churn Rate %
    measure_name: [Churn %]
    format: 0.0%
    folder: 04_Customer
  - kpi_id: sales.customer.revenue.amount
    kpi_name: Customer Revenue Amount
    measure_name: [Customer Revenue Amount]
    format: €#,0
    folder: 01_Revenue
```

---

## 3. Data Contract Scope (Subset YAML)
```yaml
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
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity, type: decimal, agg: sum}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}

  - name: fact_customer_activity
    grain: customer_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: Active Flag, type: boolean}
      - {name: Churn Flag, type: boolean}

  - name: fact_customer_value   # if separate CLV calc
    grain: customer
    columns:
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: CLV Amount, type: currency}
      - {name: Horizon Months, type: int, nullable: true}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 4. Semantic Model Requirements

### 4.1 Tables
- fact_sales  
- fact_customer_activity  
- fact_customer_value (if present)  
- dim_date  
- dim_org  
- dim_customer  
- dim_product  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)
- dim_date (1) → fact_sales / fact_customer_activity / fact_customer_value on DateKey (where applicable)  
- dim_org (1) → fact_sales on OrgKey  
- dim_customer (1) → fact_sales / fact_customer_activity / fact_customer_value on CustomerKey  
- dim_product (1) → fact_sales on ProductKey  
- security_user_org filters dim_org (Region/Country/Channel/OrgKey) → cascades to fact_sales; if needed, map dim_customer to dim_org via a bridge or ensure org attribution on customer.
- Single direction; no ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies
- Date: Year → Quarter → Month  
- Org: Region → Country → Channel → OrgName  
- Customer: Segment → CustomerName  
- Product: Category → Subcategory → ProductName

### 4.4 Sort-by Columns
- Month → MonthNumber  
- CustomerName → CustomerCode  
- ProductName → ProductCode

### 4.5 Modeling Constraints
- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; display folders per dictionary.  
- Surrogate keys mandatory; avoid M2M; use bridge if customer-org mapping needed.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory
| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Customer Lifetime Value | crm.clv.amount | CLV | 04_Customer | €#,0 | KPI |
| Customer Margin Amount | margin.customer.amount | Margin | 02_Margin | €#,0 | KPI |
| Retention % | crm.retention.pct | Retention | 04_Customer | 0.0% | KPI |
| Churn % | crm.churn.pct | Churn | 04_Customer | 0.0% | KPI |
| Customer Revenue Amount | sales.customer.revenue.amount | Revenue | 01_Revenue | €#,0 | KPI |
| Net Sales Amount | Supporting | Revenue base | 01_Revenue | €#,0 | Supporting |
| COGS Amount | Supporting | Cost base | 02_Margin | €#,0 | Supporting |
| Active Customers | Supporting | Retention denominator | 04_Customer | #,0 | Supporting |
| Churned Customers | Supporting | Churn numerator | 04_Customer | #,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// Supporting — Revenue
Net Sales Amount :=
    SUM ( fact_sales[Net Sales Amount] )

/// Supporting — Cost
COGS Amount :=
    SUM ( fact_sales[Cost of Goods Sold Amount] )

/// sales.customer.revenue.amount — Customer revenue
Customer Revenue Amount :=
    CALCULATE ( [Net Sales Amount], ALLEXCEPT ( dim_customer, dim_customer[CustomerKey] ) )

/// margin.customer.amount — Customer margin
Customer Margin Amount :=
    CALCULATE ( [Net Sales Amount] - [COGS Amount], ALLEXCEPT ( dim_customer, dim_customer[CustomerKey] ) )

/// Supporting — Active and churned counts
Active Customers :=
    CALCULATE ( DISTINCTCOUNT ( dim_customer[CustomerKey] ), fact_customer_activity[Active Flag] = TRUE )

Churned Customers :=
    CALCULATE ( DISTINCTCOUNT ( dim_customer[CustomerKey] ), fact_customer_activity[Churn Flag] = TRUE )

/// crm.retention.pct — Retention
Retention % :=
    DIVIDE ( [Active Customers], [Active Customers] + [Churned Customers] )

/// crm.churn.pct — Churn
Churn % :=
    DIVIDE ( [Churned Customers], [Active Customers] + [Churned Customers] )

/// crm.clv.amount — CLV (placeholder if precomputed)
Customer Lifetime Value :=
    SUM ( fact_customer_value[CLV Amount] )
```

---

## 6. RLS / OLS Requirements

### 6.1 Security Table Pattern
```yaml
security_table:
  name: security_user_org
  keys:
    - UserPrincipalName
    - Region
    - Country
    - OrgKey
    - Channel
  mapping_target: dim_org[OrgKey]
  fallback_behavior: deny_all_if_no_match
```

### 6.2 RLS Rule (Fabric / Power BI)
```DAX
dim_org[OrgKey] IN
    CALCULATETABLE (
        VALUES ( security_user_org[OrgKey] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
    )
```

### 6.3 OLS (optional)
- None required; CLV may be sensitive—consider masking for roles if needed (TODO if client requires).

---

## 7. Technical Assumptions
- Churn/retention flags supplied in fact_customer_activity; definition consistent across channels.
- CLV either precomputed (preferred) or computed upstream; if computed in model, align methodology with finance.
- Data latency ≤24h; currency EUR.
- Customer-to-org mapping available for RLS alignment.

---

## 8. Deployment Requirements
- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, for fact_sales and fact_customer_activity (e.g., last 24 months).  
- Aggregations: optional for large sales volume tables.  
- Workspace/naming: `ARF – Commercial` dataset/model naming per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Customer/Product keys non-null in facts | 100% | Y | Data Engineering |
| Revenue/Cost Balancing | Net Sales and COGS match source per month | ±0.1% | Y | Controlling |
| Retention/Churn Consistency | Active + Churned reconciles to prior base | Exact | Y | BI |
| CLV Availability | CLV present for top segments | 100% of priority segments | Y | BI/Finance |
| RLS Coverage | Users see only authorised regions/channels/customers (if mapped) | 0 leaks | Y | Security |
| Performance | Main visuals <2s on 24M row sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md
