---
id: "CST-014"
title: "Subscription Churn & Next-Best-Action"
domain: "Customer and Market"
owner: "Head of Customer Success / Subscription Business"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Churn %", "CLV %"]
supports_strategic_kpi_ids:
  ["crm.churn.pct", "crm.clv.amount"]
action_codes: ["C1", "P2", "M3", "SP1"]
expected_impact: "Reduce churn in subscription models by predicting risk and recommending targeted next-best-actions per subscriber."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Customer.Segment",
    "Customer.LifecycleStage",
    "Subscription.Plan",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["Subscription_Status_Consistent", "Churn_Definition_Documented"]
required_kpi_ids:
  [
    "crm.clv.amount",
    "crm.retention.pct",
    "crm.churn.pct",
  ]
required_kpis:
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
data_requirements:
  facts:
    - name: fact_subscription
      grain: subscription_period
      primary_key: [SubscriptionID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: SubscriptionID, type: string, role: attribute }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Plan", type: string, role: attribute }
        - { name: "MRR Amount", type: decimal, role: amount }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "Churn Flag", type: bool, role: indicator }
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "CLV Amount", type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: LifecycleStage, type: string }
  relationships:
    - { from: fact_subscription.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_subscription.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "MRR Amount": "fact_subscription[MRR Amount]"
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Customer": "dim_customer[CustomerID]"
  "Date": "dim_date[Date]"
---

# Subscription Churn & Next-Best-Action

## 1. Business Goal
Reduce subscription churn and increase CLV by predicting churn risk and recommending tailored next-best-actions per subscriber.

---

## 2. Business Context
In abonnementbasierten Geschäftsmodellen (Telecom, SaaS, Media, FS) sind wenige Prozentpunkte Churn-Differenz ein massiver Werttreiber.  
Gleichzeitig sind Customer Success, Marketing und Sales oft nicht mit einer gemeinsamen, datenbasierten Sicht auf Risiko, Wert und geeignete Maßnahmen ausgestattet.  
Dieser Use Case kombiniert Churn- und CLV-Kennzahlen mit NBA-Logik, um pro Abo-Kontext konkrete Handlungsempfehlungen zu geben.

---

## 3. Key Questions
- Welche Abonnenten sind akut churngefährdet und welchen Wert (CLV) repräsentieren sie?
- Welche Maßnahmen (Preis, Planwechsel, Service-Intervention, Zusatzleistungen) sind pro Segment am wirksamsten?
- Wie verändern sich Churn und CLV nach Umsetzung von NBA-Strategien?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| CLV Amount | Diskontierter Margenbeitrag pro Abonnent | EUR |
| Customer Retention % | Retained Subscribers / Subscribers Start | % |
| Customer Churn Rate % | Churned Subscribers / Subscribers Start | % |

---

## 5. Required Attributes (Business-Level)
- Subscription: ID, Plan, Price, Start/End, Status.
- Customer: Segment, Lifecycle Stage.
- Time: Month, Quarter.

---

## 6. Segmentation & Hierarchies
- Subscription: Plan > Tier.
- Customer: Segment > Lifecycle Stage.
- Time: Year > Quarter > Month.

---

## 7. Scope & Assumptions
- Churn-Definition (z.B. Kündigung, Downgrade, Nicht-Verlängerung) ist klar dokumentiert.
- NBA-Modelle (Churn Risk, Propensity) werden außerhalb des FactSheets gepflegt; hier werden Output-Scores verwendet.

---

## 8. Data Freshness & Cadence
- Subscription- und Churndaten: täglich/wöchentlich aktualisiert.
- NBA-Scores: mindestens monatlich, ideal wöchentlich.

---

## 9. Edge Cases & QA Rules
- Kurzfristige Test- oder Trial-Abos können separat behandelt werden, um CLV/Churn-Kennzahlen nicht zu verzerren.
- Mehrfach-Abos pro Kunde (z.B. mehrere Lines) werden konsistent aggregiert.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Subscription-Historie mit Status und Planinformationen.
  - CLV-/Churn-Information pro Kunde/Abonnement.
- Optional:
  - Nutzungsdaten (Usage Patterns), NPS/CSAT, Tickets.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Targeted retention campaigns for high-value, high-risk subscribers | C1 | 1–2 pp Churn-Reduktion in Zielsegmenten |
| Plan/Pricing-Optimierung für risikobehaftete, aber wertvolle Abos | P2 | Höherer CLV bei stabilerer Kundenzahl |
| Up-/Cross-Sell für stabile, hochengagierte Abonnenten | M3 | Zusätzlicher Revenue und CLV-Zuwachs |
| Governance und Playbooks für churne-sensitive Segmente | SP1 | Skalierbare, wiederholbare Churn-Reduktionsprogramme |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Churn | 1–2 pp niedrigere Churn-Rate in relevanten Segmenten | Churn %, Retention % |
| CLV | Höherer durchschnittlicher CLV durch gezielte Maßnahmen | CLV Amount, CLV-Delta vs Baseline |

---

## 13. Related Processes
Subscription Lifecycle Management -> Customer Success & Support -> Pricing & Packaging -> NBA Execution -> KPI Review.

---

## 14. Insights & Learnings
Typische Insights: bestim
