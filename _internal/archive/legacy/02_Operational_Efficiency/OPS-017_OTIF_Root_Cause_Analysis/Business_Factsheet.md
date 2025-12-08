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

# OTIF Root Cause Analysis - Business Factsheet

## 1. Summary
- **Business Goal:** Improve OTIF performance by identifying and quantifying the main root causes of delivery failures across the end-to-end supply chain.
- **Target Audience:** Head of Logistics / Supply Chain
- **Business Priority:** High
- **Expected Impact:** Explain OTIF deviations by root causes across planning, warehouse, transport and customer processes, and prioritize corrective actions.

## 2. Core Questions
- Wie unterscheiden sich OTIF-Werte nach Region, DC, Kunde und Segment?
- Welche Root Causes (z.B. Planungsfehler, Pickingfehler, Transportverzgerungen) dominieren?
- Welche Kunden- oder Produktsegmente sind besonders anfllig fr OTIF-Probleme?
- Welche Manahmen haben die grte Wirkung auf OTIF - und in welchem Zeitrahmen?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Order Accuracy % | Correctly delivered lines / Total lines | % |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |

## 4. Business Logic & Thresholds
- Lieferungen mit unvollstndigen oder fehlenden Issue Codes werden separat ausgewiesen.
- Rcksendungen und Reklamationen sollten je nach Servicedefinition bercksichtigt werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Introduce targeted corrective actions for dominant root causes (e.g., picking process changes) | I1 | Deutliche Verbesserung der OTIF-Werte in betroffenen Bereichen |
| Align planning and cut-off times with transport and customer constraints | I2 | Weniger versptete Lieferungen |
| Adjust customer and SLA settings for strukturell kritische Kombinationen | O2 | Realistischere Service-Level und weniger Vertragsstrafen |
| Remove or redesign processes that regelmig Fehler verursachen | D1 | Weniger systematische OTIF-Probleme |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for On-Time-In-Full (OTIF) %, Order Accuracy %, Stockout Rate % with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- OTIF-Definition (z.B. Toleranzfenster fr On-Time") ist klar dokumentiert.
- Root-Cause-Codes sind standardisiert und werden im Lieferprozess erfasst.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Hhere OTIF-Werte und bessere Kundenzufriedenheit | OTIF %, Service-Level-Feedback |
| Cost | Weniger Eilauftrge, Strafzahlungen und Reklamationen | Sonderkosten, Penalties |
| Efficiency | Weniger Firefighting und Ad-hoc-Lsungen | Anzahl Notfallaktionen, Stabilitt im Lieferprozess |