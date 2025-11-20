---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
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
qa_asserts: ["RI_OK", "Inventory_Value_Positive", "Coverage_InRange"]
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
data_requirements:
  facts:
    - name: fact_inventory_snapshot
      grain: sku_location_day
      primary_key: [SnapshotDate, OrgID, ProductID]
      required_columns:
        - { name: SnapshotDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Units", type: decimal, role: quantity }
        - { name: "Inventory Value", type: decimal, role: amount }
        - { name: "Demand Qty", type: decimal, role: quantity }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Safety Stock Qty", type: decimal, role: helper }
        - { name: "Lead Time Days", type: int, role: helper }
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
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
        - { name: Warehouse, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_inventory_snapshot.SnapshotDate, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.5%" }
    - { from: fact_inventory_snapshot.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory_snapshot.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Inventory Units": "fact_inventory_snapshot[Inventory Units]"
  "Inventory Value": "fact_inventory_snapshot[Inventory Value]"
  "Demand Qty": "fact_inventory_snapshot[Demand Qty]"
  "Delivered Qty": "fact_inventory_snapshot[Delivered Qty]"
  "Safety Stock Qty": "fact_inventory_snapshot[Safety Stock Qty]"
  "Lead Time Days": "fact_inventory_snapshot[Lead Time Days]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Inventory Health & Stock-Out Prevention

## 1. Business Goal
Ensure optimal stock levels by minimizing both overstock (capital tied up) and stock-outs (lost sales), balancing service levels and working capital efficiency.

---

## 2. Business Context
Inventory acts as the buffer between volatile demand and rigid supply lead times. Without a unified perspective on coverage, obsolescence, and service levels, teams oscillate between firefighting stock-outs and writing off excess goods. This FactSheet aligns Demand Planning, Replenishment, Logistics, and Commercial stakeholders on a single KPI set so that every replenishment decision is traceable to OTIF and working-capital impact. The analysis highlights SKU/location combinations that need action and quantifies whether corrections should come from forecast, supplier, or policy adjustments.

---

## 3. Key Questions
- Which SKUs or locations show excess or obsolete inventory?
- Where do stock-outs or low coverage threaten sales?
- What is the optimal target coverage given demand variability?
- How does forecast accuracy affect safety stock?
- What actions improve inventory turns without service loss?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Inventory Days | Inventory Value / COGS * 365 | days | 0 decimals |
| Stock-Out Rate % | Lost demand / Requested demand | % | 1 decimal |
| Inventory Turnover | COGS / Average Inventory | x | 1 decimal |
| Obsolescence % | (Aged Stock > Threshold) / Total Inventory | % | 1 decimal |
| OTIF % | On-Time In-Full Deliveries / Orders | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (snapshot or daily balance)
- Org (warehouse, store, region)
- Product (category, subcategory, SKU)
- Inventory Value and Units Qty
- Demand Qty, Delivered Qty, Safety Stock Target, Lead Time
- Optional: Supplier, Lifecycle Stage, ABC classification

---

## 6. Segmentation & Hierarchies
- Org: Region > Area > Store/Warehouse
- Product: Family > Category > Subcategory > SKU
- Channel: Retail / eCom / Wholesale
- Time: Year > Quarter > Month > Week
- Supplier: Group > Vendor (for lead-time analysis)

---

## 7. Scope & Assumptions
- Inventory valued at standard cost; adjustments logged separately.
- Daily snapshots aggregated to month-end for trend analysis.
- Service Level = Delivered / Requested Qty; OTIF pulled from fulfillment system.
- Exclude consignment or third-party-managed stock.
- Currency = EUR; reporting by company code.

---

## 8. Data Freshness & Cadence
- Snapshot refresh: daily at 05:00 local warehouse time.
- Latency <= 12h for stock, <= 24h for demand/fulfillment signals.
- Historical depth: 18-24 months for seasonality.
- Data Owner: Supply Chain Planning; Technical Owner: Operations BI.

---

## 9. Edge Cases & QA Rules
- Inventory Value >= 0; Units Qty >= 0.
- Stock-Out Rate % <= 100 %.
- Referential integrity >= 99.9 % across Date/Org/Product.
- Exclude discontinued items from active coverage ratio.
- Safety Stock recalculated monthly based on updated demand volatility.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Inventory Units, Inventory Value, COGS, Demand Qty, Delivered Qty.
- Optional: Safety Stock, Lead Time, Supplier info, Lifecycle stage.
- Extended: Forecast Accuracy %, ABC/XYZ tags, inbound shipment ETA data.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust replenishment parameters (min/max levels, reorder points) | I1 | DIO -5-10 days; Stock-Outs reduce |
| Prioritize allocation of limited stock to high-margin SKUs or key stores | I2 | Revenue loss reduces; service stability improves |
| Reduce obsolete inventory via targeted markdown or redistribution | O2 | Inventory value reduces 5-10 % |
| Improve forecast accuracy through demand segmentation | D1 | Service improves; DIO stable |
| Strengthen supplier reliability (lead time, fill rate) | PC4 | OTIF improves; Stock-Outs reduce |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Working Capital | Inventory value -10-15 % | vs Plan |
| Service Level | OTIF >= 97 %; Stock-Out Rate <= 3 % | weekly dashboard |
| Obsolescence | Slow-mover share -20 % | vs Prior Quarter |

---

## 13. Related Processes
Replenishment Planning -> Demand Forecasting -> Procurement -> S&OP -> Warehouse Management.

---

## 14. Insights & Learnings
Most excess inventory originates from misaligned lifecycle status rather than absolute forecast error. Highlighting OTIF alongside stock levels triggers supplier conversations earlier and prevents a blame game between Planning and Logistics.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_
