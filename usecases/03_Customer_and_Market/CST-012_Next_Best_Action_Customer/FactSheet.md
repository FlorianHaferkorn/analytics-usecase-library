---
id: "CST-012"
title: "Next-Best-Action Customer (NBA)"
domain: "Customer and Market"
owner: "Head of CRM / Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Customer Retention %", "CLV %"]
supports_strategic_kpi_ids: ["crm.retention.pct", "crm.clv.amount"]
action_codes: ["C1", "P2", "M3", "SP1"]
expected_impact: "Increase CLV and retention by recommending the best next action per customer (offer, channel, timing) based on propensity, risk and value."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Customer.Segment",
    "Customer.LifecycleStage",
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["Customer_ID_Consistent", "Consent_Settings_Respected"]
required_kpi_ids:
  [
    "crm.retention.pct",
    "crm.churn.pct",
    "crm.clv.amount",
    "crm.cross_sell_ratio.pct",
    "crm.basket_size.amount",
    "crm.basket_size.units",
    "crm.acquisition.cac.amount",
  ]
required_kpis:
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.cross_sell_ratio.pct: "Cross-Sell Ratio %"
  crm.basket_size.amount: "Average Basket Value"
  crm.basket_size.units: "Average Basket Units"
  crm.acquisition.cac.amount: "Customer Acquisition Cost (CAC) Amount"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "CLV Amount", type: decimal, role: amount }
    - name: fact_marketing_interactions
      grain: interaction
      primary_key: [InteractionID]
      required_columns:
        - { name: InteractionID, type: string, role: attribute }
        - { name: DateTime, type: datetime, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Channel", type: string, role: channel }
        - { name: "CampaignID", type: string, role: attribute }
        - { name: "Response Flag", type: bool, role: indicator }
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
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: LifecycleStage, type: string }
        - { name: "Consent Marketing Flag", type: bool }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_marketing_interactions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# Next-Best-Action Customer (NBA)

## 1. Business Goal
Increase customer lifetime value and retention by recommending the best next action per customer, based on their risk, propensity and value, and by orchestrating actions across channels.

---

## 2. Business Context
CRM- und Marketing-Teams planen häufig Kampagnen nach einfachen Regeln (z.B. „alle Kunden im Segment X“) ohne individuelle Risiko- oder Wertperspektive.  
Dadurch werden wertvolle Kunden mit generischen Angeboten überversorgt, während abwanderungsgefährdete Kunden zu spät oder gar nicht angesprochen werden.  
Der NBA-Use Case stellt für jeden Kunden eine priorisierte Liste von Aktionen bereit (z.B. Rabatt, Service-Call, Cross-Sell-Angebot) und macht deren erwarteten Impact transparent.

---

## 3. Key Questions
- Welche Kunden sind akut churngefährdet und sollten mit welcher Maßnahme angesprochen werden?
- Welche Kunden haben hohe Cross-Sell- oder Upsell-Potenziale?
- Welche Aktionen liefern die beste Kombination aus CLV-Impact und Kosten?
- Über welche Kanäle (E-Mail, App, Call-Center, Außendienst) sollten wir welche Aktionen aussteuern?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Customer Retention % | Retained Customers / Active Customers Start | % |
| Customer Churn Rate % | Churned Customers / Active Customers Start | % |
| CLV Amount | Diskontierter Margenbeitrag je Kunde | EUR |
| Cross-Sell Ratio % | Kunden mit >1 Kategorie / Aktive Kunden | % |
| Average Basket Value | Net Sales / Orders | EUR |
| Average Basket Units | Units / Orders | units per order |
| CAC Amount | Acquisition spend / New Customers | EUR |

---

## 5. Required Attributes (Business-Level)
- Customer: Segment, Lifecycle Stage, Consent-Status, Key Account Flag.
- Time: Month/Quarter (für Retention, CLV), ggf. Tag (für Kampagnen).
- Org: Region, Business Unit.
- Channel: E-Mail, App, Call-Center, Field Sales etc.
- Campaign/Offer: ID, Typ, Kosten (optional).

---

## 6. Segmentation & Hierarchies
- Customer: Segment > Lifecycle Stage > Key Account.
- Time: Year > Quarter > Month.
- Org: Region > Business Unit.
- Channel: Digital > Offline > Assisted.

---

## 7. Scope & Assumptions
- NBA liefert Vorschläge, keine automatische Ausführung; letzte Entscheidung liegt bei Marketing/CRM.
- ML-Modelle (Churn-Risiko, Propensity) sind außerhalb dieses FactSheets definiert; hier werden ihre Outputs genutzt, nicht die Berechnungsdetails.
- Datenschutz und Consent-Management müssen vor Aktivierung geklärt sein (z.B. Opt-in-Anforderungen).

---

## 8. Data Freshness & Cadence
- Churn- und Propensity-Modelle: wöchentlich/monatlich recalculated.
- Kunden- und Transaktionsdaten: täglich/wöchentlich aktualisiert.
- NBA-Empfehlungen: mindestens wöchentlich, ideal täglich für aktive Kanäle.

---

## 9. Edge Cases & QA Rules
- Kunden ohne gültige Marketing-Einwilligung dürfen nicht für bestimmte Aktionen/Kanäle vorgeschlagen werden.
- Zu kleine Segmente oder unsichere Modell-Outputs werden mit konservativen Regeln behandelt.
- A/B-Tests für neue Aktionen werden getrennt ausgewertet, um Modelle nicht zu verzerren.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Historische Käufe und CLV/Churn-Informationen pro Kunde.
  - Segmentierung (Segment, Lifecycle Stage).
  - Basis-Metriken wie Retention %, Churn %, CLV.
- Optional:
  - Feine Kanal- und Interaktionsdaten für detailliertere NBA-Logiken.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Targeted retention offers for high-CLV at-risk customers | C1 | Höhere Retention %, stabilerer CLV |
| Cross-sell campaigns for high-propensity segments | P2 | Höhere Basket-Größe und Cross-Sell Ratio |
| Reduction of spend on low-CLV, low-propensity segments | SP1 | Bessere Budgetallokation, höherer ROI |
| Product and price recommendations in digital channels | M3 | Höhere Conversion und Warenkorbwerte |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Retention | Höhere Kundenbindung bei wertvollen Kunden | Retention %, Churn % nach Segment |
| CLV | Steigende durchschnittliche CLV in Zielsegmenten | CLV Amount, CLV-Delta |
| Efficiency | Besserer ROI von Marketingkampagnen | Revenue/Cost per Campaign, CAC |

---

## 13. Related Processes
Customer Segmentation -> Model Training & Scoring -> NBA Generation -> Campaign Execution -> Performance Measurement & Model Tuning.

---

## 14. Insights & Learnings
Typische Insights sind, dass ein kleiner Anteil von Kunden und Aktionen für den Großteil des CLV-Zuwachses verantwortlich ist und dass bestimmte Segmente sehr gut auf gezielte Maßnahmen reagieren, während andere kaum auf Kampagnen ansprechen.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[CST-003 Customer Lifetime Value Analysis](../CST-003_Customer_Lifetime_Value_Analysis/FactSheet.md)`  
  `[CST-008 Cross-Sell & Basket Analysis](../CST-008_Cross_Sell_and_Basket_Analysis/FactSheet.md)`  
  `[CST-010 Acquisition Funnel Performance](../CST-010_Acquisition_Funnel_Performance/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of CRM / Marketing] |
| Technical Reviewer | [Data Science Lead / CRM BI Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after NBA pilot] |

---

_Last updated: 19.11.2025_

