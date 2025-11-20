---
id: "OPS-017"
title: "OTIF Root Cause Analysis"
domain: "Operational Efficiency"
owner: "Head of Logistics / Supply Chain"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["ops.otif.pct", "fin.liquidity.working_capital"]
action_codes: ["I1", "I2", "O2", "D1"]
expected_impact: "Explain OTIF deviations by root causes across planning, warehouse, transport and customer processes, and prioritize corrective actions."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>DC",
    "Customer.Segment",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["OTIF_Definition_Documented", "Event_Codes_Defined"]
required_kpi_ids:
  [
    "ops.otif.pct",
    "ops.order_accuracy.pct",
    "ops.stockout.pct",
  ]
required_kpis:
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
  ops.order_accuracy.pct: "Order Accuracy %"
  ops.stockout.pct: "Stockout Rate %"
data_requirements:
  facts:
    - name: fact_deliveries
      grain: delivery
      primary_key: [DeliveryID]
      required_columns:
        - { name: DeliveryID, type: string, role: attribute }
        - { name: "Planned Delivery Date", type: date, role: date_key }
        - { name: "Actual Delivery Date", type: date, role: helper }
        - { name: OrgID, type: string, role: org_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Delivered Lines Total", type: int, role: quantity }
        - { name: "Delivered Lines OTIF", type: int, role: quantity }
        - { name: "Delivered Lines Inaccurate", type: int, role: quantity }
        - { name: "Delivery Issue Code", type: string, role: attribute }
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
        - { name: "Distribution Center", type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
  relationships:
    - { from: fact_deliveries."Planned Delivery Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_deliveries.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_deliveries.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Delivered Lines Total": "fact_deliveries[Delivered Lines Total]"
  "Delivered Lines OTIF": "fact_deliveries[Delivered Lines OTIF]"
  "Delivered Lines Inaccurate": "fact_deliveries[Delivered Lines Inaccurate]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# OTIF Root Cause Analysis

## 1. Business Goal
Improve OTIF performance by identifying and quantifying the main root causes of delivery failures across the end-to-end supply chain.

---

## 2. Business Context
OTIF ist einer der wichtigsten Service-KPIs für Kunden und Supply Chain.  
Schlechte OTIF-Werte führen zu Unzufriedenheit, Vertragsstrafen und Umsatzverlust. Gleichzeitig liegen Ursachen in unterschiedlichen Bereichen: Planung, Lager, Transport oder beim Kunden selbst.  
Dieser Use Case strukturiert OTIF-Abweichungen nach Root Causes und macht sichtbar, welche Ursachen am stärksten wirken und priorisiert werden sollten.

---

## 3. Key Questions
- Wie unterscheiden sich OTIF-Werte nach Region, DC, Kunde und Segment?
- Welche Root Causes (z.B. Planungsfehler, Pickingfehler, Transportverzögerungen) dominieren?
- Welche Kunden- oder Produktsegmente sind besonders anfällig für OTIF-Probleme?
- Welche Maßnahmen haben die größte Wirkung auf OTIF – und in welchem Zeitrahmen?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Order Accuracy % | Correctly delivered lines / Total lines | % |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |

---

## 5. Required Attributes (Business-Level)
- Org: Region, DC/Lager.
- Customer: ID, Segment.
- Time: Week, Month.
- Delivery: Planned vs Actual Delivery Date, Issue Code (z.B. „No Stock“, „Late Transport“, „Order Error“).

---

## 6. Segmentation & Hierarchies
- Org: Region > DC.
- Customer: Segment > Key Account.
- Time: Year > Month > Week.

---

## 7. Scope & Assumptions
- OTIF-Definition (z.B. Toleranzfenster für „On-Time“) ist klar dokumentiert.
- Root-Cause-Codes sind standardisiert und werden im Lieferprozess erfasst.

---

## 8. Data Freshness & Cadence
- Delivery-/Service-Level-Daten: täglich aktualisiert.
- Reporting: wöchentlich und monatlich für Supply-Chain-Reviews und Kundenmeetings.

---

## 9. Edge Cases & QA Rules
- Lieferungen mit unvollständigen oder fehlenden Issue Codes werden separat ausgewiesen.
- Rücksendungen und Reklamationen sollten je nach Servicedefinition berücksichtigt werden.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Lieferdaten mit OTIF-Status und Issue Code.
  - Kunden- und Org-Hierarchien.
- Optional:
  - Detaillierte Transport- und Lagerereignisdaten zur feineren Root-Cause-Analyse.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Introduce targeted corrective actions for dominant root causes (e.g., picking process changes) | I1 | Deutliche Verbesserung der OTIF-Werte in betroffenen Bereichen |
| Align planning and cut-off times with transport and customer constraints | I2 | Weniger verspätete Lieferungen |
| Adjust customer and SLA settings for strukturell kritische Kombinationen | O2 | Realistischere Service-Level und weniger Vertragsstrafen |
| Remove or redesign processes that regelmäßig Fehler verursachen | D1 | Weniger systematische OTIF-Probleme |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Höhere OTIF-Werte und bessere Kundenzufriedenheit | OTIF %, Service-Level-Feedback |
| Cost | Weniger Eilaufträge, Strafzahlungen und Reklamationen | Sonderkosten, Penalties |
| Efficiency | Weniger Firefighting und Ad-hoc-Lösungen | Anzahl Notfallaktionen, Stabilität im Lieferprozess |

---

## 13. Related Processes
Demand & Supply Planning -> Order Management -> Warehouse & Picking -> Transport Execution -> Delivery & Feedback.

---

## 14. Insights & Learnings
Typische Insights: Bestimmte Kunden, Strecken oder Produkte verursachen überproportional viele OTIF-Verletzungen; häufig wiederkehrende Muster in Planung und Ausführung lassen sich gezielt adressieren.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-002 Inventory Health & Stock-Out Prevention](../OPS-002_Inventory_Health/FactSheet.md)`  
  `[OPS-007 Stockout & Service Level](../OPS-007_Stockout_and_Service_Level/FactSheet.md)`  
  `[OPS-014 On-Shelf Availability & Stockout Root Causes](../OPS-014_On_Shelf_Availability_and_Stockout_Root_Causes/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Logistics / Supply Chain] |
| Technical Reviewer | [Logistics Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first OTIF improvement cycles] |

---

_Last updated: 19.11.2025_

