---
id: "COR-013"
title: "Customer Profitability Across Lifecycle"
domain: "Corporate and Strategy"
owner: "CCO / CFO"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "CLV %", "Customer Retention %"]
supports_strategic_kpi_ids:
  ["margin.gm.pct", "crm.clv.amount", "crm.retention.pct"]
action_codes: ["P2", "M3", "C1", "SP1"]
expected_impact: "Understand and manage profitability of customers across their lifecycle, from acquisition to churn, enabling targeted investments and de-investments."
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
    "sales.net_sales.amount",
    "margin.customer.amount",
    "margin.customer.pct",
    "crm.clv.amount",
    "crm.acquisition.cac.amount",
    "crm.retention.pct",
    "crm.churn.pct",
    "crm.complaint.rate.pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.customer.amount: "Customer Margin Amount"
  margin.customer.pct: "Customer Margin %"
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.acquisition.cac.amount: "Customer Acquisition Cost (CAC) Amount"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
  crm.complaint.rate.pct: "Complaint Rate %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
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
        - { name: "Churn Flag", type: bool, role: indicator }
        - { name: "CLV Amount", type: decimal, role: amount }
    - name: fact_marketing_spend
      grain: customer_campaign
      primary_key: [CustomerID, CampaignID]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Acquisition Spend Amount", type: decimal, role: amount }
    - name: fact_complaint
      grain: complaint
      primary_key: [ComplaintID]
      required_columns:
        - { name: ComplaintID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Complaint Cost Amount", type: decimal, role: amount }
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
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_marketing_spend.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_complaint.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_complaint.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Acquisition Spend Amount": "fact_marketing_spend[Acquisition Spend Amount]"
  "Complaint Cost Amount": "fact_complaint[Complaint Cost Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# Customer Profitability Across Lifecycle

## 1. Business Goal
Measure and manage customer profitability over the entire lifecycle – from acquisition to retention and churn – in order to reallocate spend towards high-value segments and reduce investments in unprofitable relationships.

---

## 2. Business Context
Viele Unternehmen steuern Kunden primär über Umsatz oder Volumen, ohne deren volle Profitabilität über Zeit zu berücksichtigen.  
Marketing investiert in Akquisition, Sales in Discounts und Service in Beschwerdemanagement – oft ohne eine gemeinsame Sicht auf CLV, CAC, Servicekosten und Margenbeitrag.  
Dieser Use Case verbindet Commercial, Customer & Finance Perspektiven in einer durchgängigen Lifecycle-Sicht auf Kundenprofitabilität.

---

## 3. Key Questions
- Welche Kundensegmente liefern über ihren Lifecycle die höchste und niedrigste Profitabilität?
- Wie verhalten sich CAC und CLV nach Kanal, Segment und Kampagne?
- Welche Muster erkennen wir bei Churn, Complaints und Rückgabe-/Servicekosten?
- Wo investieren wir heute zu viel Akquisitionsbudget für Kunden mit schwacher Margen- oder Wiederkaufs-Performance?
- Welche konkreten Maßnahmen zur Verbesserung von CLV (Cross-Sell, Retention, Servicequalität) sind am wirkungsvollsten?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue per customer/segment | EUR |
| Customer Margin Amount | Net Sales - COGS per customer/segment | EUR |
| Customer Margin % | Customer Margin / Net Sales | % |
| CLV Amount | Diskontierter Margin-Beitrag über den Lifecycle | EUR |
| CAC Amount | Acquisition spend per newly acquired customer | EUR |
| Retention % | Retained Customers / Active Customers Start | % |
| Churn Rate % | Churned Customers / Active Customers Start | % |
| Complaint Rate % | Complaints / Customers or Orders | % |

---

## 5. Required Attributes (Business-Level)
- Time: Year, Quarter, Month.
- Customer: ID, Segment, Lifecycle Stage (z.B. New, Active, Loyal, At Risk, Churned).
- Org: Region, Business Unit.
- Product (optional für Drilldowns): Category, Subcategory.
- Marketing: Kampagnen- oder Kanalattribute für CAC-Zuordnung.
- Service: Complaint-Typ, Kosten, Severity (optional).

---

## 6. Segmentation & Hierarchies
- Customer: Segment > Lifecycle Stage > Key Account.
- Time: Year > Quarter > Month.
- Org: Region > Business Unit.
- Product (optional): Category > Subcategory.

---

## 7. Scope & Assumptions
- CLV kann vollständig modelliert sein oder auf einfacheren Proxies (z.B. 12M-Margin extrapoliert) basieren – Definition muss dokumentiert werden.
- CAC wird primär auf Neukunden bezogen; Bestandskundenkampagnen werden separat analysiert.
- Beschwerde- und Servicekosten werden soweit verfügbar auf Kunden- oder Segmentebene zugeordnet, ansonsten als pauschaler Overhead betrachtet.
- Lifecycle-Stufen sind konsistent definiert (z.B. Inaktivität > X Monate = Churn).

---

## 8. Data Freshness & Cadence
- Sales und Margin: täglich/wöchentlich geladen, im Use Case auf Monats-/Quartelebene verdichtet.
- CLV: monatlich/vierteljährlich aktualisiert.
- CAC: abhängig vom Kampagnenabschluss (z.B. monatlich).
- Complaints: zeitnah (täglich/wöchentlich).

---

## 9. Edge Cases & QA Rules
- Kunden ohne ausreichende Historie werden in CLV-Betrachtungen separat gekennzeichnet (z.B. „Early Stage“).
- Negative Margen (z.B. aufgrund massiver Discounts oder Servicekosten) müssen explizit sichtbar sein.
- CAC-Berechnung muss definieren, wie Multi-Touch-Kampagnen und Brand-Spend zugeordnet werden.
- Datenschutzvorgaben (z.B. Anonymisierung bei kleinen Segmenten) sind zu beachten.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Sales (Net Sales, COGS) nach Kunde, Segment, Zeitraum.
  - Einfacher CLV-Proxy oder CLV-Modell (z.B. per Faktentabelle).
  - Marketing-Spend für Neukundengewinnung.
  - Complaint-Counts nach Kunde/Segment.
- Optional:
  - Detaillierte Service-/Retourenkosten nach Kunde.
  - Loyalty-/Engagement-Scores.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Reallocate acquisition and retention spend towards high-CLV segments | P2 | Höhere Gesamtprofitabilität bei gleichem Budget |
| Adjust pricing and discount policies for structurally unprofitable segments | M3 | Verbesserte Customer Margin % |
| Implement targeted retention programmes for profitable but at-risk segments | C1 | Höhere Retention %, stabilere CLV |
| Sunset oder restrukturieren von Kundengruppen mit dauerhaft negativer Profitabilität | SP1 | Fokus auf wertstiftende Kundenbasis |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Höhere durchschnittliche Customer Margin % und CLV | Margin %, CLV |
| Efficiency | Bessere Allokation von Marketing- und Servicebudget | CAC, Servicekosten/Customer |
| Growth Quality | Weniger „unprofitables Wachstum“ | Anteil unprofitabler Kunden/Segmente |

---

## 13. Related Processes
Customer Acquisition Planning -> Onboarding -> Cross-/Upselling -> Retention & Loyalty -> Churn Management & Winback.

---

## 14. Insights & Learnings
Typische Insights zeigen, dass ein relativ kleiner Teil der Kundenbasis den Großteil der Profitabilität trägt, während bestimmte Segmente trotz hohen Umsatzes kaum oder negative Margen liefern. Die Lifecycle-Sicht macht zudem deutlich, in welchen Phasen (Onboarding, Nutzung, Service, Churn) die größten Wertverluste auftreten.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-006 Customer Profitability](../../01_Commercial/COM-006_Customer_Profitability/FactSheet.md)`  
  `[CST-001 Customer Retention & Churn](../../03_Customer_and_Market/CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[CST-003 Customer Lifetime Value Analysis](../../03_Customer_and_Market/CST-003_Customer_Lifetime_Value_Analysis/FactSheet.md)`  
  `[CST-007 Complaint Rate & Service Quality](../../03_Customer_and_Market/CST-007_Complaint_Rate_and_Service_Quality/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [CCO / Head of CRM] |
| Technical Reviewer | [CRM BI Lead / Data Scientist] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first lifecycle analyses] |

---

_Last updated: 19.11.2025_

