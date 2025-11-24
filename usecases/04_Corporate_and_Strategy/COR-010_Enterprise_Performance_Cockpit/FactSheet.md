---
id: "COR-010"
title: "Enterprise Performance Cockpit"
domain: "Corporate and Strategy"
owner: "CEO / CFO / COO"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi:
  [
    "Revenue Growth %",
    "Gross Margin %",
    "Working Capital %",
    "CCC Days",
    "Customer Retention %",
    "Headcount Efficiency",
    "ESG-Aligned Revenue %",
  ]
supports_strategic_kpi_ids:
  [
    "sales.revenue.growth_pct",
    "margin.gm.pct",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
    "crm.retention.pct",
    "hr.revenue_per_fte.amount",
    "esg.aligned_revenue.pct",
  ]
action_codes: ["SP1", "SP2", "G1", "W1"]
expected_impact: "Provide a single, board-ready view on growth, profitability, liquidity, efficiency, customer value, people and ESG to enable fact-based, cross-domain steering."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Customer.Segment",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Last 24M", "Org: All"]
qa_asserts: ["RI_OK", "KPI_Definitions_Aligned", "P&L_Reconciles"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.revenue.growth_pct",
    "margin.gm.pct",
    "profit.ebitda_margin",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
    "ops.inventory.turnover",
    "ops.inventory.days",
    "crm.retention.pct",
    "crm.clv.amount",
    "hr.revenue_per_fte.amount",
    "hr.turnover.pct",
    "esg.aligned_revenue.pct",
    "esg.co2.total.tco2e",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.revenue.growth_pct: "Revenue Growth %"
  margin.gm.pct: "Gross Margin %"
  profit.ebitda_margin: "EBITDA Margin %"
  fin.liquidity.working_capital: "Working Capital %"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  crm.retention.pct: "Customer Retention %"
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  hr.revenue_per_fte.amount: "Revenue per FTE Amount"
  hr.turnover.pct: "Employee Turnover %"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
  esg.co2.total.tco2e: "Total CO₂ Emissions (tCO2e)"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_balance
      grain: org_period_balance
      primary_key: [OrgID, Period, BalanceLine]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: BalanceLine, type: string, role: attribute }
        - { name: Amount, type: decimal, role: amount }
    - name: fact_working_capital
      grain: org_period_wc
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "DSO Days", type: decimal, role: helper }
        - { name: "DPO Days", type: decimal, role: helper }
        - { name: "DIO Days", type: decimal, role: helper }
    - name: fact_hr
      grain: org_period_hr
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Headcount FTE", type: decimal, role: helper }
        - { name: "Personnel Cost Amount", type: decimal, role: amount }
        - { name: "Leavers Count", type: int, role: helper }
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "Churn Flag", type: bool, role: indicator }
        - { name: "CLV Amount", type: decimal, role: amount }
    - name: fact_esg
      grain: org_period_esg
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "ESG-Aligned Revenue Amount", type: decimal, role: amount }
        - { name: "Total Revenue Amount", type: decimal, role: amount }
        - { name: "CO2 Emissions tCO2e", type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - {
        from: fact_sales.Date,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.CustomerID,
        to: dim_customer.CustomerID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_balance.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_balance.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_working_capital.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_working_capital.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_hr.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_hr.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_customer_metrics.CustomerID,
        to: dim_customer.CustomerID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_customer_metrics.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_esg.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_esg.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
  "Product": "dim_product[ProductID]"
  "ESG-Aligned Revenue Amount": "fact_esg[ESG-Aligned Revenue Amount]"
  "Total Revenue Amount": "fact_esg[Total Revenue Amount]"
  "CO2 Emissions tCO2e": "fact_esg[CO2 Emissions tCO2e]"
---

# Enterprise Performance Cockpit

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
