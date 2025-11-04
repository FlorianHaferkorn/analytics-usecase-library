---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
required_kpi_ids: [
  "ops.inventory.days",
  "ops.stockout.pct",
  "ops.inventory.turnover",
  "ops.inventory.obsolescence.pct",
  "ops.otif.pct"
]
required_kpis:
  ops.inventory.days: "Inventory Days"
  ops.stockout.pct: "Stock-Out Rate %"
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.obsolescence.pct: "Obsolescence %"
  ops.otif.pct: "OTIF %"

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Org.Region>Area>Store","Product.Category>Subcategory>SKU","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

data_requirements:
  facts:
    - name: fact_main
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_main.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_main.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_main.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }

model_mapping:
  "Net Sales Amount": "fact_main[Net Sales Amount]"
  "Units Qty": "fact_main[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"---

# Inventory Health & Stock-Out Prevention

## 1. Business Goal
Ensure optimal stock levels by minimizing both overstock (capital tied up) and stock-outs (lost sales), balancing service levels and working capital efficiency.

## 3. Key Questions
- Which SKUs or locations show excess or obsolete inventory?  
- Where do stock-outs or low coverage threaten sales?  
- What is the optimal target coverage given demand variability?  
- How does forecast accuracy affect safety stock?  
- What actions improve inventory turns without service loss?

## 5. Required Attributes (Business-Level)
- Date (snapshot or daily balance)  
- Org (warehouse, store, region)  
- Product (category, subcategory, SKU)  
- Inventory Value, Units Qty  
- COGS Amount, Demand Qty, Delivered Qty  
- Optional: Safety Stock Target, Lead Time, Service Level Target

## 7. Scope & Assumptions
- Inventory valued at standard cost.  
- Daily snapshots aggregated to month-end for trend analysis.  
- Service Level = Delivered / Requested Qty.  
- Exclude consignment or third-party-managed stock.  
- Currency = EUR; reporting by company code.

## 9. Edge Cases & QA Rules
- Inventory Value >= 0; Units Qty >= 0.  
- Stock-Out Rate % <= 100 %.  
- Referential integrity >= 99.9 % across Date/Org/Product.  
- Exclude discontinued items from active coverage ratio.  
- Safety Stock recalculated monthly based on updated demand volatility.

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust replenishment parameters (min/max levels, reorder points) | I1 | DIO -5-10 days; Stock-Outs reduce |
| Prioritize allocation of limited stock to high-margin SKUs or key stores | I2 | Revenue loss reduces; service stability improves |
| Reduce obsolete inventory via targeted markdown or redistribution | O2 | Inventory value reduces 5-10 % |
| Improve forecast accuracy through demand segmentation | D1 | Service improves; DIO stable |
| Strengthen supplier reliability (lead time, fill rate) | PC4 | OTIF improves; Stock-Outs reduce |

## 13. Related Processes
Replenishment Planning -> Demand Forecasting -> Procurement -> S&OP -> Warehouse Management.

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

_Last updated: 04.11.2025_



