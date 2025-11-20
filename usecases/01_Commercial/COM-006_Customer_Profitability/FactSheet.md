---
id: "COM-006"
title: "Customer Profitability"
domain: "Commercial"
owner: "Head of Sales Controlling / Key Account Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "Customer Lifetime Value %"]
supports_strategic_kpi_ids: ["margin.gm.pct", "crm.clv.amount"]
action_codes: ["P2", "M3"]
expected_impact: "+1 pp Gross Margin %, +2 % CLV by focusing on profitable segments and addressing loss-making customers."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Customer Group>Customer",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Margin_By_Customer_Reconciles", "TopN_Contribution_Stable"]
required_kpi_ids: [
  "margin.gm.pct",
  "margin.gm.amount",
  "sales.net_sales.amount",
  "cost.cogs.amount",
  "margin.customer.amount",
  "margin.customer.pct",
  "sales.customer.revenue_share.pct"
]
required_kpis:
  margin.gm.pct: "Gross Margin %"
  margin.gm.amount: "Gross Margin Amount"
  sales.net_sales.amount: "Net Sales Amount"
  cost.cogs.amount: "COGS Amount"
  margin.customer.amount: "Customer Margin Amount"
  margin.customer.pct: "Customer Margin %"
  sales.customer.revenue_share.pct: "Customer Revenue Share %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Area, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: CustomerGroup, type: string }
        - { name: CustomerName, type: string }
        - { name: ChannelDefault, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Customer": "dim_customer[CustomerID]"
---

# Use Case Fact Sheet

## 1. Business Goal
Provide a transparent view of profitability by customer and customer segment to focus commercial efforts on the right accounts, improve mix, and address loss-making relationships.

## 2. Business Questions
- Which customers and segments contribute most to total gross margin and CLV?
- Which customers generate high revenue but low or negative margin?
- How concentrated is our margin contribution (e.g., Top 10 / Top 20 % of customers)?
- How does customer profitability evolve over time and across regions/channels?

## 3. Scope & Assumptions
- Scope: All invoiced sales to external customers (B2B/B2C) included in `fact_sales`.
- Profitability is measured at gross margin level (Net Sales - COGS), excluding rebates not captured in `fact_sales`.
- CLV % is interpreted via contribution to long-term margin, not full lifetime model if not implemented yet.
- Returns and credit notes are included in Net Sales Amount and impact customer margin.

## 4. Target Users & Decisions
- Target users: Sales Controlling, Key Account Management, Commercial Directors.
- Decisions:
  - Reprioritize customer segmentation and service levels based on profitability tiers.
  - Negotiate price, discount and terms with low-margin customers.
  - Focus growth initiatives on high-margin / high-CLV customers.

## 5. KPIs & Drivers (Overview)
- Strategic KPIs:
  - Gross Margin %
  - Customer Lifetime Value (via margin contribution per customer)
- Analytical KPIs:
  - Customer Margin Amount and %
  - Revenue share per customer / segment
  - Margin concentration (e.g., Top-N share)

## 6. Required KPIs (Detail)
See `required_kpi_ids` and `required_kpis` in the front matter for the exact KPI IDs and labels used for implementation.

## 7. Data & Modelling Notes
- CustomerID must uniquely identify a customer across regions and channels.
- COGS Amount must be consistently allocated to invoice lines to avoid misleading margin.
- Where CLV models are available, they can be joined via `dim_customer`.

## 8. Page Layout / Storyboard
- Overview: Customer profitability heatmap (GM % vs Revenue) with segmentation and filters.
- Drivers: Detail table with Net Sales, COGS, GM Amount and GM % by customer / segment.
- Concentration: Top-N view of customers by margin contribution and cumulative share curve.
