---
id: "OPS-006"
title: "Inventory Turnover & Days in Inventory (DIO)"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Inventory Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Working Capital %", "Cash Conversion Cycle"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.working_capital.ccc.days"]
action_codes: ["I1", "I2", "O2"]
expected_impact: "-10–15 % inventory value; improved cash conversion and service level."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All"
]
qa_asserts: ["RI_OK", "Inventory_Value_Positive", "Coverage_InRange"]
required_kpi_ids: [
  "ops.inventory.turnover",
  "ops.inventory.days",
  "ops.working_capital.dio.days"
]
required_kpis:
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.days: "Inventory Days"
  ops.working_capital.dio.days: "Days in Inventory (DIO)"
data_requirements:
  facts:
    - name: fact_inventory
      grain: sku_org_period
      primary_key: [InventoryID]
      required_columns:
        - { name: "Average Inventory Value", type: decimal, role: amount }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_cogs
      grain: sku_org_period
      primary_key: [CogsID]
      required_columns:
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
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
  relationships:
    - { from: fact_inventory.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Average Inventory Value": "fact_inventory[Average Inventory Value]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "COGS Amount": "fact_cogs[COGS Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Inventory Turnover & Days in Inventory (DIO)

## 1. Business Goal
Monitor and optimize inventory turnover and days in inventory across products and locations to reduce working capital and obsolescence without harming service levels.

---

## 2. Business Context
Inventory is a major component of working capital.  
Too much inventory ties up cash and increases obsolescence risk; too little leads to stockouts and lost sales.  
This Use Case standardizes key inventory efficiency KPIs and provides transparency on where inventory is too high or too low.

---

## 3. Key Questions
- What are our inventory turnover and DIO by product, location, and segment?
- Where do we carry excessive slow-moving or obsolete inventory?
- How do changes in demand or lead times impact optimal inventory levels?

---

## 4. Key KPIs
| KPI               | Definition                                  | Unit | Format   |
|-------------------|---------------------------------------------|------|----------|
| Inventory Turnover| COGS / Average Inventory Value              | x    | 1 decimal|
| Inventory Days    | 365 / Inventory Turnover                    | days | 0 decimals|
| DIO               | Days in Inventory (aligned with CCC)        | days | 0 decimals|

---

## 5. Required Attributes (Business-Level)
- Product (category/subcategory/SKU)
- Org (region/area/store/warehouse)
- Average inventory value, COGS

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU  
- Org: Region > Area > Location  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- DIO is calculated on a yearly basis (365 days) unless specified differently.
- Average Inventory Value is calculated as (opening + closing) / 2 or via daily snapshots.

---

## 8. Data Freshness & Cadence
- Data refresh: daily or weekly.
- Reporting cadence: weekly/monthly supply chain review.

---

## 9. Edge Cases & QA Rules
- Inventory values must be positive and non-null.
- DIO is capped at a defined maximum for outlier handling.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Inventory fact with value and units by product and org.
  - COGS fact aligned to the same product and org hierarchies.

---

## 11. Typical Actions
| Action                                 | Code | Expected Effect               |
|----------------------------------------|------|-------------------------------|
| Reduce safety stock for slow movers    | I1   | Lower inventory value         |
| Focus demand-shaping on overstock SKUs | I2   | Improved DIO and fewer write-offs |

---

## 12. Expected Business Impact
| Dimension        | Expected Impact       | Measurement |
|------------------|-----------------------|-------------|
| Working Capital  | -10–15 % inventory   | vs prior year |
| Obsolescence     | -10–20 % write-offs  | vs baseline |

---

## 13. Related Processes
Demand Planning → Inventory Policy Setting → Replenishment → Supply Chain Review.

---

## 14. Insights & Learnings
Typical findings include highly unbalanced inventory levels across locations and categories, and low turnover for long-tail SKUs.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-002 Inventory Health & Stock-Out Prevention](../OPS-002_Inventory_Health/FactSheet.md)`  

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

