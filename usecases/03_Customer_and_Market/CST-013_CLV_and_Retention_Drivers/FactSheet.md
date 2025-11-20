---
id: "CST-013"
title: "CLV & Retention Drivers"
domain: "Customer and Market"
owner: "Head of CRM / Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["CLV %", "Customer Retention %"]
supports_strategic_kpi_ids:
  ["crm.clv.amount", "crm.retention.pct"]
action_codes: ["C1", "P2", "M3"]
expected_impact: "Understand the drivers of CLV and retention across segments and behaviors to focus marketing and service spend on the most effective levers."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Customer.Segment",
    "Customer.LifecycleStage",
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 24M", "Org: All"]
qa_asserts: ["Customer_ID_Consistent", "Lifecycle_Stage_Defined"]
required_kpi_ids:
  [
    "crm.clv.amount",
    "crm.retention.pct",
    "crm.churn.pct",
    "crm.basket_size.amount",
    "crm.basket_size.units",
    "crm.cross_sell_ratio.pct",
  ]
required_kpis:
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
  crm.basket_size.amount: "Average Basket Value"
  crm.basket_size.units: "Average Basket Units"
  crm.cross_sell_ratio.pct: "Cross-Sell Ratio %"
data_requirements:
  facts:
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "CLV Amount", type: decimal, role: amount }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "Churn Flag", type: bool, role: indicator }
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
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
  relationships:
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Customer": "dim_customer[CustomerID]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---

# CLV & Retention Drivers

## 1. Business Goal
Explain differences in CLV and retention across segments and behaviors to focus acquisition, pricing and service levers on the most profitable customers.

---

## 2. Business Context
Viele Organisationen kennen ihren durchschnittlichen CLV und ihre Retention, aber nicht, welche Segmente und Verhaltensmuster die größten Werttreiber oder -vernichter sind.  
Ohne diese Transparenz fließen Marketing- und Servicebudgets breit verteilt, statt gezielt in die Kundengruppen mit dem höchsten Wertpotenzial.  
Dieser Use Case verbindet CLV, Retention und Transaktionsverhalten (Basket, Cross-Sell) zu einer Treiberanalyse.

---

## 3. Key Questions
- Welche Segmente liefern den höchsten und niedrigsten CLV und wie entwickeln sich Retention und Churn?
- Welche Verhaltensmuster (Kaufhäufigkeit, Warenkorbgröße, Cross-Sell) unterscheiden wertvolle von wenig profitablen Kunden?
- Welche Maßnahmen (z.B. Pricing, Bundles, Loyalty-Programme) korrelieren mit höherem CLV und Retention?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| CLV Amount | Diskontierter Margenbeitrag pro Kunde | EUR |
| Customer Retention % | Retained Customers / Active Customers Start | % |
| Customer Churn Rate % | Churned Customers / Active Customers Start | % |
| Average Basket Value | Net Sales / Orders | EUR |
| Average Basket Units | Units / Orders | units/order |
| Cross-Sell Ratio % | Kunden mit >1 Kategorie / Aktive Kunden | % |

---

## 5. Required Attributes (Business-Level)
- Customer: Segment, Lifecycle Stage, ggf. Channel-Präferenz.
- Time: Month, Quarter, Year.
- Org: Region, Business Unit.

---

## 6. Segmentation & Hierarchies
- Customer: Segment > Lifecycle Stage > Key Account.
- Time: Year > Quarter > Month.
- Org: Region > Business Unit.

---

## 7. Scope & Assumptions
- CLV-Definition ist mit Finance abgestimmt (z.B. Margenbasis, Diskontsatz, Horizont).
- Retention-/Churn-Definitionen sind klar (z.B. Inaktivität > X Monate).

---

## 8. Data Freshness & Cadence
- CLV und Retention: monatlich/vierteljährlich aktualisiert.
- Salesdaten: täglich/wöchentlich, im Use Case aggregiert.

---

## 9. Edge Cases & QA Rules
- Kunden ohne ausreichende Historie werden separat gekennzeichnet (z.B. „New“).
- Negative Margen oder atypische Transaktionen werden bei CLV-Berechnung validiert.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - CLV- und Retention-/Churn-Informationen pro Kunde/Periode.
  - Sales-Historie pro Kunde.
- Optional:
  - Kampagnen-/Interaktionsdaten zur genaueren Attribution.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Increase focus and budget for high-CLV, high-retention segments | P2 | Höherer Anteil wertvoller Kunden im Portfolio |
| Adjust offers/pricing for low-CLV, low-retention Segmente | M3 | Verbesserte Margen bzw. geringere Kosten pro Kunde |
| Design targeted retention programmes for profitable at-risk customers | C1 | Höhere Retention und stabilere CLV in Kernsegmenten |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Höherer durchschnittlicher CLV und Margin | CLV Amount, Margin % |
| Efficiency | Besserer ROI von CRM/Marketing-Maßnahmen | Revenue/Cost per Segment |

---

## 13. Related Processes
Customer Segmentation -> CLV/Churn Modelling -> Campaign Design -> Execution -> Performance Review.

---

## 14. Insights & Learnings
Typische Insights: Ein kleiner Teil der Kunden generiert einen überproportionalen Anteil des CLV; bestimmte Verhaltensmuster (z.B. frühe Cross-Sell-Adoption) korrelieren stark mit hoher Retention.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn Analysis](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[CST-003 Customer Lifetime Value Analysis](../CST-003_Customer_Lifetime_Value_Analysis/FactSheet.md)`  
  `[CST-008 Cross-Sell & Basket Analysis](../CST-008_Cross_Sell_and_Basket_Analysis/FactSheet.md)`  
  `[CST-012 Next-Best-Action Customer (NBA)](../CST-012_Next_Best_Action_Customer/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of CRM / Marketing] |
| Technical Reviewer | [CRM BI Lead / Data Scientist] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first CLV driver analyses] |

---

_Last updated: 19.11.2025_

