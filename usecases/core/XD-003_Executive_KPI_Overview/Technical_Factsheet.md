---
id: XD-003
factsheet_type: technical
---

# XD-003 - Executive KPI Overview  

## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Domain:** Executive / Cross-Functional
- **Technical Owner:** Enterprise BI Lead
- **Model ID:** executive_kpi_overview
- **Source Systems:** Finance, Commercial, Supply Chain, HR, DWH
- **Business Factsheet:** ./Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** data_contracts/domains/executive.yaml
- **Source Data Contracts:** data_contracts/domains/finance.yaml; data_contracts/domains/supply_chain.yaml; data_contracts/domains/hr.yaml; data_contracts/domains/commercial_sales.yaml
- **Semantic Model Definition (core):** ../../../semantic_models/core_action_ready/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionaries:** semantic_models/domains/Commercial/Measure_Dictionary_Commercial.md; semantic_models/domains/Profitability/Measure_Dictionary_Profitability.md; semantic_models/domains/CustomerValue/Measure_Dictionary_CustomerValue.md; semantic_models/domains/Service/Measure_Dictionary_Service.md; semantic_models/domains/SupplyChain/Measure_Dictionary_SupplyChain.md; semantic_models/domains/Efficiency/Measure_Dictionary_Efficiency.md; semantic_models/domains/InnovationPeople/Measure_Dictionary_InnovationPeople.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: sales.net_sales.delta_pct.ly
    measure_name: Net Sales % vs LY
    format: "0.0%"
    folder: 01_Growth

  - kpi_id: margin.gm.pct
    measure_name: Gross Margin %
    format: "0.0%"
    folder: 02_Margin

  - kpi_id: crm.clv.amount
    measure_name: Customer Lifetime Value Amount
    format: "EUR #,0"
    folder: 03_Customer

  - kpi_id: svc.sla.attainment.pct
    measure_name: SLA Attainment %
    format: "0.0%"
    folder: 04_Service

  - kpi_id: ops.otif.pct
    measure_name: OTIF %
    format: "0.0%"
    folder: 04_Service

  - kpi_id: ops.working_capital.ccc.days
    measure_name: Cash Conversion Cycle (Days)
    format: "#,0.0"
    folder: 05_Liquidity

  - kpi_id: people.digital_adoption.pct
    measure_name: Digital Adoption %
    format: "0.0%"
    folder: 06_People

  - kpi_id: people.attrition_risk.pct
    measure_name: Attrition Risk %
    format: "0.0%"
    folder: 06_People
```

---

## 3. Data Contract Scope (Subset YAML)

```yaml
required_facts:
  - fact_sales
  - fact_margin
  - fact_supply_chain / OTIF
  - fact_inventory
  - fact_working_capital
  - fact_hr
required_dimensions:
  - dim_date
  - dim_org
  - dim_product
  - dim_customer
  - dim_employee

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
      - {name: Entity, type: text}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: Segment, type: text, nullable: true}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text, nullable: true}

  - name: dim_customer
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: CustomerCode, type: text}
      - {name: CustomerName, type: text}
      - {name: Segment, type: text, nullable: true}
      - {name: Region, type: text, nullable: true}

  - name: dim_employee
    columns:
      - {name: EmployeeKey, type: int, role: key}
      - {name: EmployeeId, type: text}
      - {name: Department, type: text, nullable: true}
      - {name: Region, type: text, nullable: true}

  - name: security_user_org
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}

fact:
  - name: fact_revenue
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Net Sales Amount, type: currency, agg: sum}

  - name: fact_finance
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Gross Margin Amount, type: currency, agg: sum}
      - {name: EBITDA Amount, type: currency, agg: sum}

  - name: fact_customer_value
    grain: customer_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: CLV Amount, type: currency, agg: sum}

  - name: fact_service
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Service Level %, type: decimal, agg: avg}

  - name: fact_fulfillment
    grain: order
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: OTIF Flag, type: boolean}
      - {name: Order Qty, type: decimal, agg: sum}

  - name: fact_wc
    grain: entity_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: CCC Days, type: decimal}

  - name: fact_digital
    grain: user_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Active Users, type: int, agg: sum}
      - {name: Eligible Users, type: int, agg: sum}

  - name: fact_hr
    grain: month_entity
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Attrition Risk %, type: decimal, agg: avg}
      - {name: Leavers, type: int, agg: sum}
      - {name: Headcount, type: int, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 4. Semantic Model Requirements

- Certified monthly aggregates per KPI; fact tables provide monthly grain or higher with certified calculations upstream.
- Conformed dimensions (Date, Org, Product, Customer, Employee) required; no local dimension copies.
- No new measures introduced locally; use certified measures from core_action_ready where available.

### 4.1 Tables

- dim_date, dim_org, dim_product, dim_customer, dim_employee, security_user_org  
- fact_revenue, fact_finance, fact_customer_value, fact_service, fact_fulfillment, fact_wc, fact_digital, fact_hr

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> org keys in revenue/finance/service/fulfillment/wc/digital/hr  
- dim_customer (1) -> fact_customer_value  
- dim_product (optional) (1) -> applicable facts if product analysis is enabled  
- dim_employee (optional) (1) -> fact_digital/fact_hr where applicable  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-directional except RLS bridge if needed.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month  
- Org: Region -> Entity -> Segment  
- Customer: Segment -> CustomerName

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- Entity -> OrgKey  
- CustomerName -> CustomerCode

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; display folders follow dictionary.  
- Surrogate keys mandatory; avoid M2M; use conformed dimensions; aggregation tables optional but must retain grain integrity.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Net Sales % vs LY | sales.net_sales.delta_pct.ly | Growth rate | 01_Growth | 0.0% | KPI |
| Gross Margin % | margin.gm.pct | Profitability quality | 02_Margin | 0.0% | KPI |
| Customer Lifetime Value Amount | crm.clv.amount | Customer value base | 03_Customer | EUR #,0 | KPI |
| SLA Attainment % | svc.sla.attainment.pct | Service performance | 04_Service | 0.0% | KPI |
| OTIF % | ops.otif.pct | Fulfillment reliability | 04_Service | 0.0% | KPI |
| Cash Conversion Cycle (Days) | ops.working_capital.ccc.days | Liquidity efficiency | 05_Liquidity | #,0.0 | KPI |
| Digital Adoption % | people.digital_adoption.pct | Adoption rate | 06_People | 0.0% | KPI |
| Attrition Risk % | people.attrition_risk.pct | Attrition exposure | 06_People | 0.0% | KPI |

### 5.2 DAX Definitions

No local DAX added; measures sourced from certified semantic model. Existing certified expressions apply.

---

## 6. RLS / OLS Requirements

- Executives require full-company visibility.
- If needed, existing Org-hierarchy RLS applies (security_user_org filtering dim_org cascading to facts).
- No new RLS rules may be created.

---

## 7. Technical Assumptions

- Cross-domain data aligned by entity/region and month; conformed dimensions enforce joins.
- Plan/LY data available for growth and margin KPIs; CCC provided upstream per liquidity standards.
- Digital adoption and attrition risk sourced monthly from HR/IT systems; currency/fiscal settings per data governance.

---

## 8. Deployment Requirements

- Mode: DirectLake or Import depending on SLA; incremental refresh by Month.
- Aggregations optional for long history; avoid grain distortion.
- Workspace and naming per governance; display folders per measure dictionary.

---

## 9. QA & Validation Rules

- KPIs must reconcile with domain reports.
- Only certified measures allowed.
- No local KPI calculations.

---

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md


