---
id: "OPS-014"
title: "On-Shelf Availability & Stockout Root Causes"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Retail Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Revenue Growth %"]
supports_strategic_kpi_ids:
  ["ops.otif.pct", "sales.revenue.growth_pct"]
action_codes: ["I1", "I2", "D1", "O2"]
expected_impact: "Improve on-shelf availability by identifying where along the supply chain stockouts are created and which actions prevent lost sales."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Store",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12W", "Org: All"]
qa_asserts: ["Stockout_Definition_Documented", "Service_Level_Consistent"]
required_kpi_ids:
  [
    "ops.stockout.pct",
    "ops.otif.pct",
    "ops.order_accuracy.pct",
    "sales.net_sales.amount",
  ]
required_kpis:
  ops.stockout.pct: "Stockout Rate %"
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
  ops.order_accuracy.pct: "Order Accuracy %"
  sales.net_sales.amount: "Net Sales Amount"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
        - { name: "Order Lines OTIF", type: int, role: quantity }
        - { name: "Order Lines Accurate", type: int, role: quantity }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Order Lines OTIF": "fact_service_level[Order Lines OTIF]"
  "Order Lines Accurate": "fact_service_level[Order Lines Accurate]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# On-Shelf Availability & Stockout Root Causes

## 1. Business Goal
Increase on-shelf availability and avoid lost sales by understanding where stockouts are generated along the supply chain and which root causes dominate.

---

## 2. Business Context
Out-of-Stock im Regal führt direkt zu Umsatzverlusten und schlechter Kundenerfahrung.  
Gleichzeitig ist die Verantwortung verteilt: Forecasting, Replenishment, Warehouse, Transport und Store Execution können alle zu Stockouts beitragen.  
Dieser Use Case bringt die Sicht auf Stockout-Rate, OTIF und Order Accuracy zusammen und erlaubt Root-Cause-Analysen von Zentrallager bis Regal.

---

## 3. Key Questions
- Wo (Region, Store, Kategorie) treten die meisten Stockouts auf und wie groß ist der resultierende Umsatzverlust?
- Welche Root Causes dominieren: Forecast-Fehler, falsche Bestellmengen, Kommissionierfehler, Transportverzögerungen oder In-Store-Handling?
- Welche Kombination aus Maßnahmen (Parameteranpassungen, Prozessänderungen, Training) liefert den größten Service-Level-Gewinn?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Order Accuracy % | Correctly picked/shipped order lines / Total order lines | % |
| Net Sales Amount | Sales revenue, used to quantify lost sales | EUR |

---

## 5. Required Attributes (Business-Level)
- Org: Region, Store, ggf. Warehouse.
- Product: Category, Subcategory, SKU.
- Time: Week, Month.
- Service-Events: OTIF, Stockout, Order Accuracy per order/line.

---

## 6. Segmentation & Hierarchies
- Time: Year > Month > Week.
- Org: Region > Store > Warehouse (optional).
- Product: Category > Subcategory > SKU.

---

## 7. Scope & Assumptions
- Stockout-Definition (z.B. „nicht verfügbar zum Zeitpunkt der Nachfrage“) ist klar dokumentiert und technisch abbildbar (Order Lines, Store-Inventory).
- Root-Cause-Codes (z.B. Forecast, Picking, Transport, Shelf) können nach und nach ergänzt werden; initial reichen Service- und Prozess-KPIs.

---

## 8. Data Freshness & Cadence
- Service-Level-Daten: täglich/wöchentlich.
- Reporting: wöchentlich und monatlich für Operations- und Commercial-Reviews.

---

## 9. Edge Cases & QA Rules
- Returns, Stornos und Nachlieferungen müssen je nach Definition in Order-/Service-KPIs korrekt berücksichtigt werden.
- Datenqualität in logistischen Events (z.B. Fehlbuchungen) kann Root-Cause-Analysen verzerren und sollte überwacht werden.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Order-/Service-Level-Daten (OTIF, Stockout, Order Accuracy) nach Org/Produkt/Periode.
  - Sales zur Quantifizierung von Lost Sales (z.B. Umsatz in Vergleichsperioden).
- Optional:
  - Warehouse- und Transport-Ereignisdaten zur feineren Root-Cause-Analyse.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Adjust replenishment rules and safety stock for chronic stockout SKUs | I1 | Weniger Stockouts bei kritischen Artikeln |
| Improve order accuracy and picking processes in warehouses | I2 | Höhere Service-Level und weniger Fehlerkosten |
| Remove or redesign promotions that systematisch zu Stockouts führen | D1 | Stabilere Verfügbarkeit bei Aktionen |
| Establish joint Commercial–Supply Chain reviews for stockout hotspots | O2 | Bessere end-to-end Abstimmung und nachhaltigere Lösungen |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Höhere on-shelf availability und OTIF | Stockout Rate %, OTIF % |
| Revenue | Weniger lost sales durch Stockouts | Umsatzentwicklung in Hotspot-Segmenten |
| Efficiency | Weniger manuelle Firefighting-Aktivitäten | Anzahl Ad-hoc-Expedite / Notfallaktionen |

---

## 13. Related Processes
Demand Planning -> Replenishment -> Warehouse & Transport Execution -> Store Execution -> Service-Level Reporting.

---

## 14. Insights & Learnings
Typische Insights: Ein kleiner Teil von Stores und SKUs ist für den Großteil der Stockouts verantwortlich; häufig wiederkehrende Muster wie bestimmte Lieferwege, Wochentage oder Promotionsphasen stehen im Fokus.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health & Stock-Out Prevention](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-004 Replenishment Optimization & Service Level Management](../OPS-004_Replenishment_Optimization/FactSheet.md)`  
  `[OPS-007 Stockout & Service Level](../OPS-007_Stockout_and_Service_Level/FactSheet.md)`  
  `[OPS-017 OTIF Root Cause Analysis](../OPS-017_OTIF_Root_Cause_Analysis/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Supply Chain / Retail Operations] |
| Technical Reviewer | [Supply Chain Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first stockout reviews] |

---

_Last updated: 19.11.2025_

