---
id: "COR-012"
title: "Commercial & Supply Chain Reconciliation"
domain: "Corporate and Strategy"
owner: "COO / Head of Commercial & Supply Chain"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "CCC Days"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "margin.gm.pct", "ops.working_capital.ccc.days"]
action_codes: ["P2", "W1", "D1", "SP1"]
expected_impact: "Avoid siloed commercial and operations decisions by reconciling promotions, pricing and forecast changes with stock, capacity and working capital."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts:
  [
    "Promo_Flag_Consistent",
    "Forecast_Version_Frozen",
    "Inventory_Valuation_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.promo.roi.pct",
    "sales.promo.uplift_pct",
    "margin.promo.incremental.amount",
    "ops.stockout.pct",
    "ops.inventory.days",
    "ops.inventory.turnover",
    "ops.working_capital.ccc.days",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.promo.roi.pct: "Promo ROI %"
  sales.promo.uplift_pct: "Promo Uplift %"
  margin.promo.incremental.amount: "Incremental GM Amount"
  ops.stockout.pct: "Stockout Rate %"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
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
        - { name: "Promo Flag", type: bool, role: indicator }
        - { name: "Promo ID", type: string, role: attribute }
    - name: fact_inventory
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Amount", type: decimal, role: amount }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
    - name: fact_working_capital
      grain: org_period_wc
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "DSO Days", type: decimal, role: helper }
        - { name: "DPO Days", type: decimal, role: helper }
        - { name: "DIO Days", type: decimal, role: helper }
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
        - { name: BusinessUnit, type: string }
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
    - { from: fact_inventory.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_working_capital.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_working_capital.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Promo Flag": "fact_sales[Promo Flag]"
  "Promo ID": "fact_sales[Promo ID]"
  "Inventory Amount": "fact_inventory[Inventory Amount]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Commercial & Supply Chain Reconciliation

## 1. Business Goal
Ensure that commercial decisions (pricing, promotions, demand changes) are reconciled with supply chain realities (stock, capacity, working capital) to avoid stockouts, overstocks and margin dilution.

---

## 2. Business Context
Commercial teams often push for revenue growth via promotions, price changes or forecast uplifts, während Supply Chain und Finance mit den Folgen kämpfen: Leerversorgungen, Überbestände, Eilfrachten und gebundenes Kapital.  
Ohne einen strukturierten Abgleich zwischen Commercial KPIs (Promo ROI, Uplift, Channel Mix) und Supply-Chain-KPIs (Stockout, DIO, CCC) entstehen Entscheidungen, die lokal optimiert, aber global wertvernichtend sind.  
Dieser Use Case bringt Sales, Supply Chain und Finance an einen Tisch, indem er Promotions und Forecast-Änderungen systematisch mit Inventory, Service Level und Working Capital verknüpft.

---

## 3. Key Questions
- Welche Promotions und Preismaßnahmen haben zu Stockouts oder Überbeständen geführt?
- Wo sehen wir hohe Promo-Uplifts bei gleichzeitig kritischen Service-Leveln?
- Welche Segmente oder Produkte treiben Working-Capital-Aufbau ohne entsprechenden Margenbeitrag?
- Gibt es systematische Forecast-Shifts in Commercial, die Supply Chain nicht rechtzeitig spiegeln kann?
- Wo müssen wir Prozesse oder Governance anpassen, um Commercial- und Supply-Chain-Pläne besser abzustimmen?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sum of invoiced net sales | EUR |
| Promo ROI % | (Incremental GM - Promo Cost) / Promo Cost | % |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % |
| Incremental GM Amount | GM during promo minus baseline GM | EUR |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |
| Inventory Turnover | COGS / Avg Inventory | ratio |
| CCC Days | DSO + DIO - DPO | days |

---

## 5. Required Attributes (Business-Level)
- Time: Month (optional Week) für Promo- und Lagersteuerung.
- Org: Region, Business Unit, ggf. Site/Store.
- Product: Category, Subcategory, SKU.
- Promo: Promo ID, Promo Type, Kalenderwoche(n).
- Service Level: Order Lines, Stockout Indicator.
- Finance: AR/AP/Inventory auf aggregiertem Level zur CCC-Berechnung.

---

## 6. Segmentation & Hierarchies
- Time: Year > Quarter > Month (optional Week).
- Org: Region > Business Unit > Site/Store.
- Product: Category > Subcategory > SKU.
- Promo: Type > Mechanic (Price Cut / Bundle / Display).

---

## 7. Scope & Assumptions
- Fokus liegt auf materialisierten Promotions und größeren Preis-/Forecast-Änderungen, nicht auf jeder Kleinstmaßnahme.
- Inventory- und Service-Level-Daten werden mindestens monatlich, idealerweise wöchentlich aktualisiert.
- Working-Capital-View ist auf Vereinfachte Kennzahlen (DSO, DPO, DIO) fokussiert; detaillierte Finance-Analysen erfolgen in COR-001.
- Es wird vorausgesetzt, dass Promotions im Sales- und ERP-System konsistent gekennzeichnet sind (Promo ID, Zeitraum).

---

## 8. Data Freshness & Cadence
- Promotions & Sales: täglich/wöchentlich.
- Inventory & Service-Level: wöchentlich.
- Working Capital (DSO, DPO, DIO, CCC): monatlich nach Financial Close.

---

## 9. Edge Cases & QA Rules
- Promotions ohne saubere Flagging oder ohne Kostenallokation werden markiert und aus ROI-Analysen ausgeschlossen.
- Produkte ohne belastbare Inventory- und Service-Level-Daten werden separat ausgewiesen.
- Starke Wechselkurseffekte sollten in Kommentaren oder gesonderten Kennzahlen sichtbar gemacht werden, falls relevant.
- Reconciliation-Regeln zwischen Promo-Uplift, Inventory-Veränderungen und CCC müssen definiert sein (z.B. Zeitraum, Scope).

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Sales mit Promo-ID/Flag, Org, Produkt, Datum.
  - Inventory-Bestände und -Werte nach Org/Produkt/Periode.
  - Service-Level-Proxy (Order Lines Total, Stockout Lines).
  - DSO/DPO/DIO bzw. CCC aus Finance.
- Optional:
  - Promo-Kosten, detaillierte Logistik-Kosten (Eilfracht, Out-of-Stock-Kosten).

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Remove or redesign promos that systematically create stockouts or overstocks | D1 | Weniger Service-Probleme, geringere Abwertungskosten |
| Adjust inventory and replenishment parameters for promo-sensitive SKUs | W1 | Besser ausbalancierte Bestände vs. Promotionsplan |
| Introduce governance gates between Commercial and Supply Chain for major plan changes | SP1 | Weniger Ad-hoc-Entscheidungen, bessere Planbarkeit |
| Align promo calendar with capacity and inventory constraints | P2 | Weniger Peak-Belastung, gleichmäßigere Auslastung |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Weniger stockbedingte Verkaufsverluste | Stockout Rate %, OTIF |
| Efficiency | Reduzierte Überbestände und Eilfrachten | Inventory Days, Logistikkosten |
| Liquidity | Besser gesteuerter CCC durch abgestimmte Promotions und Lager | CCC Days, Working Capital % |
| Profitability | Promotions mit stabilerer GM und weniger Folgekosten | GM %, Promo ROI % |

---

## 13. Related Processes
Commercial Planning -> Promo Planning -> Supply Chain Planning & Replenishment -> Execution -> Post-Event Review (Commercial & Supply Chain).

---

## 14. Insights & Learnings
Typische Findings sind Promotions, die zwar Umsatz hochziehen, aber systematisch Stockouts verursachen, sowie Segmente, in denen aggressive Forecast-Uplifts zu dauerhaft erhöhten Beständen führen. Durch den gemeinsamen Blick von Commercial, Supply Chain und Finance werden solche Muster sichtbar und können in künftigen Planungszyklen vermieden werden.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-003 Promotion Effectiveness (ROI & Uplift)](../../01_Commercial/COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[COM-005 Promotion ROI & Effectiveness](../../01_Commercial/COM-005_Promotion_ROI_and_Effectiveness/FactSheet.md)`  
  `[OPS-001 Cash Conversion Cycle](../../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-006 Inventory Turnover & DIO](../../02_Operational_Efficiency/OPS-006_Inventory_Turnover_and_DIO/FactSheet.md)`  
  `[OPS-007 Stockout & Service Level](../../02_Operational_Efficiency/OPS-007_Stockout_and_Service_Level/FactSheet.md)`  
  `[COR-001 Working Capital & CCC](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Commercial / Head of Supply Chain] |
| Technical Reviewer | [BI Lead Supply Chain / Commercial BI Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first reconciliation cycles] |

---

_Last updated: 19.11.2025_

