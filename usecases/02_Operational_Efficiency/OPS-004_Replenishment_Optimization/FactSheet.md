---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
 supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
 supports_strategic_kpi_ids: ["ops.otif.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
required_kpi_ids: [
  "ops.replenishment.adherence.pct",
  "ops.order_accuracy.pct",
  "ops.stockout.pct",
  "ops.inventory.days",
  "ops.otif.pct"
]
required_kpis:
  ops.replenishment.adherence.pct: "Replenishment Adherence %"
  ops.order_accuracy.pct: "Order Accuracy %"
  ops.stockout.pct: "Stock-Out Rate %"
  ops.inventory.days: "Inventory Days"
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

# Replenishment Optimization & Service Level Management

## 1. Business Goal
Optimize replenishment parameters and order logic to balance service levels, minimize inventory costs, and reduce lost sales due to stock-outs or delayed replenishment.

## 3. Key Questions
- Are replenishment quantities aligned with real demand and forecast accuracy?  
- Which items or stores frequently under- or over-order?  
- How does supplier lead time variability affect service levels?  
- Where can replenishment frequency or batch sizes be optimized?  
- Which actions yield the best trade-off between cost and service?

## 5. Required Attributes (Business-Level)
- Date (order date / delivery date)  
- Org (store, warehouse, region)  
- Product (category, subcategory, SKU)  
- Ordered Qty, Delivered Qty, Demand Qty  
- Lead Time (days), Target Stock, Safety Stock, Reorder Point  
- Optional: Supplier, Promo Flag, Forecast Qty  

## 7. Scope & Assumptions
- Replenishment logic based on EOQ or Min/Max policy per SKU.  
- Demand forecast updated weekly (rolling horizon).  
- Lead times from supplier master, adjusted by historical average.  
- Service Level Target defined by category (A: 98 %, B: 95 %, C: 90 %).  
- Currency = EUR; values aggregated by store and category.

## 9. Edge Cases & QA Rules
- Reorder Point >= 0; Safety Stock >= 0.  
- Negative order quantities excluded.  
- Service Level % capped at [0; 100].  
- Lead Time deviations > 3Ïƒ standard deviation flagged.  
- Referential integrity >= 99.9 % across Date/Org/Product/Supplier.

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust reorder points based on forecast error and demand variability | I1 | Stock-Outs reduce; Inventory -5-10 % |
| Synchronize supplier delivery cadence with actual consumption patterns | PC4 | Lead Time reduces; OTIF improves |
| Implement dynamic safety stock based on target service level | I2 | Service improves; working capital stable |
| Reduce order batch sizes to avoid overstock | O2 | Inventory Days -5; obsolescence reduces |
| Integrate replenishment optimization into S&OP | SP1 | Forecast accuracy improves; liquidity improves |

## 13. Related Processes
Replenishment Planning -> Inventory Optimization -> Supplier Collaboration -> Demand Forecasting -> S&OP.

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-001 Sales Performance](../../01_Commercial/COM-001_Sales_Performance/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

_Last updated: 04.11.2025_



