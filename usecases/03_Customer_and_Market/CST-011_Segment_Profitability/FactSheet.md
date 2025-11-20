---
id: "CST-011"
title: "Segment Profitability"
domain: "Customer and Market"
owner: "Head of Controlling / Head of Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "Customer Lifetime Value"]
supports_strategic_kpi_ids: ["margin.gm.pct", "crm.clv.amount"]
action_codes: ["P2", "M3", "D1"]
expected_impact: "Shift focus and investment to the most profitable segments and de-prioritize value-destroying segments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Segment>LoyaltyTier",
  "Customer.Region>Market",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Segment_Assignment_Complete", "Margin_Within_Range"]
required_kpi_ids: [
  "margin.customer.amount",
  "margin.customer.pct",
  "crm.clv.amount",
  "crm.retention.pct"
]
required_kpis:
  margin.customer.amount: "Customer Segment Margin Amount"
  margin.customer.pct: "Customer Segment Margin %"
  crm.clv.amount: "Customer Lifetime Value (CLV)"
  crm.retention.pct: "Customer Retention %"
data_requirements:
  facts:
    - name: fact_customer_profitability
      grain: customer_period
      primary_key: [CustomerID, Date]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Service Cost Amount", type: decimal, role: amount }
        - { name: "Marketing Cost Amount", type: decimal, role: amount }
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
    - { from: fact_customer_profitability.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_profitability.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_customer_profitability[Net Sales Amount]"
  "COGS Amount": "fact_customer_profitability[COGS Amount]"
  "Service Cost Amount": "fact_customer_profitability[Service Cost Amount]"
  "Marketing Cost Amount": "fact_customer_profitability[Marketing Cost Amount]"
  "Customer ID": "dim_customer[CustomerID]"
  "Segment": "dim_customer[Segment]"
  "Date": "dim_date[Date]"
---

# Segment Profitability

## 1. Business Goal
Identify and steer the profitability of customer segments and markets by understanding revenue, cost-to-serve, and CLV per segment.

---

## 2. Business Context
Not all customers or segments are equally profitable.  
Some segments generate high revenue but low or negative margins due to high discounts or service costs.  
This Use Case quantifies profitability at segment level and links it to CLV and retention, enabling targeted actions on pricing, service levels, and marketing investments.

---

## 3. Key Questions
- Which segments and markets are most and least profitable?
- How do revenue, discounting, and cost-to-serve differ by segment?
- How does CLV and retention vary across segments?
- Where should we invest, maintain, or de-prioritize?

---

## 4. Key KPIs
| KPI                         | Definition                                      | Unit | Format   |
|-----------------------------|-------------------------------------------------|------|----------|
| Segment Margin Amount       | Segment revenue – COGS – service/marketing cost| EUR  | € #,0.00 |
| Segment Margin %            | Segment margin / segment revenue                | %    | 1 decimal |
| CLV                         | Lifetime value per customer in segment         | EUR  | € #,0.00 |
| Customer Retention %        | Retained customers per segment                  | %    | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Customer ID, Segment, Region, Market, LoyaltyTier
- Revenue, COGS, service cost, marketing cost per period

---

## 6. Segmentation & Hierarchies
- Customer: Region > Market > Segment > LoyaltyTier  
- Time: Year > Quarter > Month  
- Channel: optional breakdown where relevant  

---

## 7. Scope & Assumptions
- Cost allocation rules (service & marketing) are defined and documented.
- Profitability is measured at contribution margin level (before overheads).

---

## 8. Data Freshness & Cadence
- Data refresh: monthly.
- Reporting cadence: monthly segment steering and quarterly strategy reviews.

---

## 9. Edge Cases & QA Rules
- Customers without segment classification are flagged.
- Negative margins are highlighted for review.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Customer-level profitability fact with revenue and costs.
  - Customer dimension with segment attributes.

---

## 11. Typical Actions
| Action                                | Code | Expected Effect                   |
|---------------------------------------|------|-----------------------------------|
| Re-price or re-negotiate in low-margin segments | D1 | Improved segment margin %         |
| Focus marketing on high-CLV segments  | P2   | Higher overall profitability      |
| Adjust service levels for low-value segments | M3 | Lower cost-to-serve              |

---

## 12. Expected Business Impact
| Dimension   | Expected Impact           | Measurement   |
|-------------|---------------------------|---------------|
| Profitability| +1–2 pp segment margin % | vs baseline   |
| Customer    | More revenue from high-value segments | mix analysis |

---

## 13. Related Processes
Segment Strategy → Pricing & Service Model → Campaign Planning → Performance Review.

---

## 14. Insights & Learnings
Typical findings include segments that destroy value despite high revenue and segments with high potential but underinvestment.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-006 Customer Profitability](../../01_Commercial/COM-006_Customer_Profitability/FactSheet.md)`  
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

