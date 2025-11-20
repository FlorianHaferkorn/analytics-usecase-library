---
id: "CST-008"
title: "Cross-Sell & Basket Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Category Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Cross-Sell Ratio %", "Customer Lifetime Value"]
supports_strategic_kpi_ids: ["crm.cross_sell_ratio.pct", "crm.clv.amount"]
action_codes: ["C2", "M3", "P2"]
expected_impact: "+5–10 % basket size and cross-sell ratio in target segments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Region>Market",
  "Customer.Segment>LoyaltyTier",
  "Channel",
  "Product.Category>Subcategory",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Customer_Key_Unique", "Basket_Size_InRange"]
required_kpi_ids: [
  "crm.cross_sell_ratio.pct",
  "crm.basket_size.amount",
  "crm.basket_size.units"
]
required_kpis:
  crm.cross_sell_ratio.pct: "Cross-Sell Ratio %"
  crm.basket_size.amount: "Average Basket Value"
  crm.basket_size.units: "Average Basket Units"
data_requirements:
  facts:
    - name: fact_sales
      grain: transaction_line
      primary_key: [TransactionID, LineID]
      required_columns:
        - { name: TransactionID, type: string, role: attribute }
        - { name: "CustomerID", type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Channel, type: string, role: channel }
        - { name: Category, type: string, role: attribute }
        - { name: Subcategory, type: string, role: attribute }
  dims:
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Region, type: string }
        - { name: Market, type: string }
        - { name: Segment, type: string }
        - { name: LoyaltyTier, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Transaction ID": "fact_sales[TransactionID]"
  "Customer ID": "dim_customer[CustomerID]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Category": "fact_sales[Category]"
  "Subcategory": "fact_sales[Subcategory]"
  "Channel": "fact_sales[Channel]"
  "Date": "dim_date[Date]"
---

# Cross-Sell & Basket Analysis

## 1. Business Goal
Increase average basket value and cross-sell between categories by identifying product affinities and targeting the right offers to the right customers and channels.

---

## 2. Business Context
Cross-selling and increasing basket size are key levers for revenue growth without acquiring new customers.  
Often, cross-sell initiatives are based on intuition rather than data-driven product affinities and segment behaviors.  
This Use Case provides a structured view on basket composition, cross-category relationships, and opportunities for tailored offers.

---

## 3. Key Questions
- What is the current average basket value and number of items per transaction?
- Which product categories are frequently bought together?
- Which customer segments have the highest cross-sell potential?
- How do campaigns or recommendations change basket metrics?

---

## 4. Key KPIs
| KPI                 | Definition                                   | Unit | Format   |
|---------------------|----------------------------------------------|------|----------|
| Cross-Sell Ratio %  | Customers buying >1 category / all customers| %    | 1 decimal |
| Average Basket Value| Net Sales per transaction                    | EUR  | € #,0.00 |
| Average Basket Units| Units per transaction                        | #    | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Transaction ID, Customer ID
- Product category/subcategory
- Net Sales Amount, Units Qty
- Channel, Date

---

## 6. Segmentation & Hierarchies
- Customer: Region > Market > Segment > LoyaltyTier  
- Product: Category > Subcategory  
- Time: Year > Quarter > Month  
- Channel: Channel Group > Channel  

---

## 7. Scope & Assumptions
- Basket = all items in one transaction (or session).
- Returns and cancellations are netted out where possible.

---

## 8. Data Freshness & Cadence
- Data refresh: daily or weekly.
- Reporting cadence: weekly/monthly campaign and category review.

---

## 9. Edge Cases & QA Rules
- Transactions without a customer ID may be included but flagged separately.
- Tiny baskets (e.g., 1 item, low value) might be excluded from some analyses.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Transaction-level sales data with product categories and customers.

---

## 11. Typical Actions
| Action                                   | Code | Expected Effect                  |
|------------------------------------------|------|----------------------------------|
| Design bundles based on frequent co-buys | M3   | Higher basket value              |
| Target cross-sell offers to high-potential segments | C2 | More multi-category customers   |
| Optimize category adjacencies in stores  | P2   | Improved cross-category purchase |

---

## 12. Expected Business Impact
| Dimension | Expected Impact                 | Measurement   |
|-----------|---------------------------------|---------------|
| Revenue   | +5–10 % basket value           | vs baseline   |
| Customer  | +3–5 pp cross-sell ratio       | vs baseline   |

---

## 13. Related Processes
Category Management → Campaign Design → In-Store / Digital Merchandising → Performance Review.

---

## 14. Insights & Learnings
Typical findings include underused cross-sell opportunities between categories and segments with high latent potential.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn Analysis](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[CST-003 Customer Lifetime Value Analysis](../CST-003_Customer_Lifetime_Value_Analysis/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

