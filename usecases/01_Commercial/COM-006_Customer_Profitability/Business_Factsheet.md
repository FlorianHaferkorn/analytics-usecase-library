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

# Customer Profitability - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a transparent view of profitability by customer and customer segment to focus commercial efforts on the right accounts, improve mix, and address loss-making relationships.
- **Target Audience:** Head of Sales Controlling / Key Account Management
- **Business Priority:** High
- **Expected Impact:** +1 pp Gross Margin %, +2 % CLV by focusing on profitable segments and addressing loss-making customers.

## 2. Core Questions
- n/a

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Gross Margin %, Gross Margin Amount, Net Sales Amount, COGS Amount, Customer Margin Amount with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a