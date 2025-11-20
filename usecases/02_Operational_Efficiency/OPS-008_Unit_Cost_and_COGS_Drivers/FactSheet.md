---
id: "OPS-008"
title: "Unit Cost & COGS Drivers"
domain: "Operational Efficiency"
owner: "Head of Operations / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "COGS % of Sales"]
supports_strategic_kpi_ids: ["margin.gm.pct", "cost.cogs.amount"]
action_codes: ["PC2", "M1", "O2"]
expected_impact: "-2–4 % unit cost; +0.5–1.0 pp gross margin %."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Plant>Line",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All"
]
qa_asserts: ["RI_OK", "COGS_Positive", "UnitCost_Reconciles"]
required_kpi_ids: [
  "cost.cogs.amount",
  "ops.process.cost_per_unit.amount"
]
required_kpis:
  cost.cogs.amount: "COGS Amount"
  ops.process.cost_per_unit.amount: "Process Cost per Unit"
data_requirements:
  facts:
    - name: fact_production
      grain: product_line_day
      primary_key: [ProductionID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Produced Units Qty", type: decimal, role: quantity }
        - { name: "Direct Labor Cost Amount", type: decimal, role: amount }
        - { name: "Energy Cost Amount", type: decimal, role: amount }
        - { name: "Material Cost Amount", type: decimal, role: amount }
        - { name: "Other Production Cost Amount", type: decimal, role: amount }
    - name: fact_cogs
      grain: product_org_period
      primary_key: [CogsID]
      required_columns:
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Plant, type: string }
        - { name: Line, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_production.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_production.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_production.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Produced Units Qty": "fact_production[Produced Units Qty]"
  "Direct Labor Cost Amount": "fact_production[Direct Labor Cost Amount]"
  "Energy Cost Amount": "fact_production[Energy Cost Amount]"
  "Material Cost Amount": "fact_production[Material Cost Amount]"
  "Other Production Cost Amount": "fact_production[Other Production Cost Amount]"
  "COGS Amount": "fact_cogs[COGS Amount]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Date": "dim_date[Date]"
---

# Unit Cost & COGS Drivers

## 1. Business Goal
Understand and reduce unit cost (cost per produced/sold unit) and COGS by decomposing them into main cost drivers such as material, labor, and energy.

---

## 2. Business Context
COGS and unit production cost are core drivers of margin.  
Many organizations see COGS only as a total in the P&L and lack visibility into the underlying operational drivers at plant, line, or SKU level.  
This Use Case bridges COGS and operational cost data to allow targeted efficiency measures.

---

## 3. Key Questions
- What is our unit cost per product, line, and plant, and how has it evolved?
- How much of unit cost is driven by material, labor, energy, or other components?
- Where are the largest improvement opportunities (e.g., energy efficiency, labor productivity)?

---

## 4. Key KPIs
| KPI                  | Definition                                        | Unit | Format   |
|----------------------|---------------------------------------------------|------|----------|
| COGS Amount          | Total cost of goods sold                          | EUR  | € #,0.00 |
| Process Cost per Unit| (Sum of production costs) / produced units        | EUR  | € #,0.000|
| Material Cost Share %| Material cost / total production cost             | %    | 1 decimal|
| Labor Cost Share %   | Direct labor cost / total production cost         | %    | 1 decimal|

---

## 5. Required Attributes (Business-Level)
- Product, Org (plant, line)
- Produced units and cost components (material, labor, energy, other)
- COGS at product/plant/period level

---

## 6. Segmentation & Hierarchies
- Org: Region > Plant > Line  
- Product: Category > Subcategory > SKU  
- Time: Year > Month  

---

## 7. Scope & Assumptions
- COGS is aligned with production cost attribution for the analysis period.
- Depreciation and overhead allocation rules are documented and, if included, applied consistently.

---

## 8. Data Freshness & Cadence
- Production data: daily.
- COGS: monthly (aligned with financial close).

---

## 9. Edge Cases & QA Rules
- Periods with zero or very low production volume are flagged to avoid distorted unit costs.
- Cost component sums must reconcile with total cost within a small tolerance.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Production fact with units and cost components.
  - COGS fact aligned to products and org.

---

## 11. Typical Actions
| Action                               | Code | Expected Effect             |
|--------------------------------------|------|-----------------------------|
| Optimize material yields             | PC2  | Lower material cost share   |
| Improve line efficiency and uptime   | M1   | Lower unit cost             |
| Adjust product/plant allocations     | O2   | Better utilization and cost |

---

## 12. Expected Business Impact
| Dimension   | Expected Impact   | Measurement  |
|-------------|-------------------|--------------|
| Profitability| +0.5–1.0 pp GM % | vs baseline  |
| Efficiency  | -2–4 % unit cost  | vs baseline  |

---

## 13. Related Processes
Production Planning → Execution → Costing → Margin Analysis.

---

## 14. Insights & Learnings
Typical findings include plants or lines with significantly higher unit costs and products where material or energy dominates cost structure.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-002 Gross Margin % vs Plan & Last Year](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[OPS-005 Capacity Utilization](../OPS-005_Capacity_Utilization/FactSheet.md)`  

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

