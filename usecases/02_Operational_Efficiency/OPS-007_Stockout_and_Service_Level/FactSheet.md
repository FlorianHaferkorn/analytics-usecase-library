---
id: "OPS-007"
title: "Stockout & Service Level"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Customer Service"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Working Capital %"]
supports_strategic_kpi_ids: ["ops.otif.pct", "ops.stockout.pct", "ops.working_capital.pct"]
action_codes: ["I1", "I2", "O2", "D1"]
expected_impact: "≥ 97–99 % service level with fewer stockouts and optimized inventory."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "OTIF_InRange", "Stockout_Events_Tracked"]
required_kpi_ids: [
  "ops.otif.pct",
  "ops.stockout.pct",
  "ops.order_accuracy.pct"
]
required_kpis:
  ops.otif.pct: "On-Time In-Full (OTIF) %"
  ops.stockout.pct: "Stockout Rate %"
  ops.order_accuracy.pct: "Order Accuracy %"
data_requirements:
  facts:
    - name: fact_orders
      grain: order_line
      primary_key: [OrderLineID]
      required_columns:
        - { name: OrderLineID, type: string, role: attribute }
        - { name: "Requested Date", type: date, role: date_key }
        - { name: "Delivered Date", type: date, role: helper }
        - { name: "Requested Qty", type: decimal, role: quantity }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Stockout Flag", type: bool, role: indicator }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Area, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_orders.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_orders.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_orders."Requested Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Requested Qty": "fact_orders[Requested Qty]"
  "Delivered Qty": "fact_orders[Delivered Qty]"
  "Stockout Flag": "fact_orders[Stockout Flag]"
  "Requested Date": "fact_orders[Requested Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Channel": "fact_orders[Channel]"
  "Date": "dim_date[Date]"
---

# Stockout & Service Level

## 1. Business Goal
Improve customer service levels by reducing stockouts and order errors across locations, products, and channels, while keeping inventory within targeted ranges.

---

## 2. Business Context
Stockouts and delivery issues directly impact customer satisfaction, churn, and revenue.  
At the same time, over-buffering inventory to avoid stockouts ties up working capital.  
This Use Case provides a standardized view on stockout rate, OTIF, and order accuracy to balance service and efficiency.

---

## 3. Key Questions
- What is our current OTIF and stockout rate by region, store, product, and channel?
- Where do stockouts cluster (by SKU, location, time), and what are the root causes?
- How do service levels correlate with inventory levels and forecast quality?

---

## 4. Key KPIs
| KPI            | Definition                                           | Unit | Format    |
|----------------|------------------------------------------------------|------|-----------|
| OTIF %         | On-time, in-full deliveries / total order lines      | %    | 1 decimal |
| Stockout Rate %| Lines with stockout / total requested lines          | %    | 1 decimal |
| Order Accuracy %| Correctly delivered lines / total delivered lines   | %    | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Order line, requested and delivered quantities
- Dates (requested, delivered)
- Org (region/area/store), Product (category/subcategory/SKU), Channel
- Stockout flag, reason (optional)

---

## 6. Segmentation & Hierarchies
- Org: Region > Area > Store  
- Product: Category > Subcategory > SKU  
- Channel: Channel Group > Channel  
- Time: Year > Month > Week  

---

## 7. Scope & Assumptions
- OTIF is defined based on agreed delivery window and completeness thresholds.
- Stockout is captured at order line level (no available inventory at requested date).

---

## 8. Data Freshness & Cadence
- Data refresh: daily.
- Reporting cadence: daily/weekly operations huddle and monthly service review.

---

## 9. Edge Cases & QA Rules
- Orders without requested or delivered dates are flagged.
- OTIF and stockout rates must be calculated only for lines with complete information.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Order line fact with requested and delivered quantities, dates, org, product, channel, and stockout flag.

---

## 11. Typical Actions
| Action                                  | Code | Expected Effect             |
|-----------------------------------------|------|-----------------------------|
| Address recurrent stockout SKUs/locations | I1  | Lower stockout rate         |
| Improve order picking and confirmation  | O2   | Higher OTIF and accuracy    |
| Align safety stocks with service targets| I2   | Stable service with less overstock |

---

## 12. Expected Business Impact
| Dimension    | Expected Impact         | Measurement   |
|--------------|-------------------------|---------------|
| Service Level| +1–3 pp OTIF           | vs baseline   |
| Efficiency   | -5–10 % emergency orders| vs baseline  |

---

## 13. Related Processes
Demand Planning → Replenishment → Order Fulfilment → Customer Service.

---

## 14. Insights & Learnings
Typical findings include specific SKUs or locations driving most stockouts and systemic issues in certain channels or processes.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health & Stock-Out Prevention](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-004 Replenishment Optimization & Service Level Management](../OPS-004_Replenishment_Optimization/FactSheet.md)`  

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

