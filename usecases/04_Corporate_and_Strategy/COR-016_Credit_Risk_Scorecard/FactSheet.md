---
id: "COR-016"
title: "Credit Risk Scorecard (PD/LGD/EAD)"
domain: "Corporate and Strategy"
owner: "Chief Risk Officer / Head of Credit Risk"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Credit Risk", "Capital Adequacy"]
supports_strategic_kpi_ids:
  ["fin.risk.pd.pct", "fin.risk.lgd.pct", "fin.risk.ead.amount"]
action_codes: ["G1", "SP1"]
expected_impact: "Provide a PD/LGD/EAD-based view on credit risk across portfolios and segments to support pricing, limits, provisioning and capital decisions."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>LegalEntity",
    "Portfolio.Type>Product",
    "Customer.Segment",
    "Time.Year>Quarter",
  ]
filters_default: ["Time: Last 8Q", "Org: All"]
qa_asserts: ["Model_Validated", "Exposure_Reconciles"]
required_kpi_ids:
  [
    "fin.risk.pd.pct",
    "fin.risk.lgd.pct",
    "fin.risk.ead.amount",
  ]
required_kpis:
  fin.risk.pd.pct: "Probability of Default (PD) %"
  fin.risk.lgd.pct: "Loss Given Default (LGD) %"
  fin.risk.ead.amount: "Exposure at Default (EAD) Amount"
data_requirements:
  facts:
    - name: fact_credit_risk
      grain: exposure
      primary_key: [ExposureID]
      required_columns:
        - { name: ExposureID, type: string, role: attribute }
        - { name: OrgID, type: string, role: org_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Product", type: string, role: attribute }
        - { name: "Portfolio Type", type: string, role: attribute }
        - { name: "PD %", type: decimal, role: attribute }
        - { name: "LGD %", type: decimal, role: attribute }
        - { name: "EAD Amount", type: decimal, role: amount }
        - { name: "Default Flag", type: bool, role: indicator }
        - { name: "Default Date", type: date, role: helper }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: LegalEntity, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
  relationships:
    - { from: fact_credit_risk.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_credit_risk.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "PD %": "fact_credit_risk[PD %]"
  "LGD %": "fact_credit_risk[LGD %]"
  "EAD Amount": "fact_credit_risk[EAD Amount]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# Credit Risk Scorecard (PD/LGD/EAD)

## 1. Business Goal
Provide a PD/LGD/EAD-based view on credit risk across portfolios and segments to support pricing, limit setting, provisioning and capital allocation decisions.

---

## 2. Business Context
In Banken, Leasing- und Finanzdienstleistungsunternehmen sind PD, LGD und EAD zentrale Kenngrößen für Kreditrisiko – sowohl regulatorisch (z.B. Basel, IFRS 9) als auch ökonomisch.  
Oft werden diese Kennzahlen jedoch nur in Spezialreports oder Risikomodellen betrachtet, nicht in einem einheitlichen Scorecard-Format für Business- und Management-Entscheidungen.  
Dieser Use Case fasst PD/LGD/EAD zu einer Scorecard zusammen und ermöglicht eine einheitliche Sicht auf Portfolio-Risiko und Rendite.

---

## 3. Key Questions
- Wie verteilen sich PD, LGD und EAD über Portfolios, Produkte, Regionen und Kundensegmente?
- Welche Portfolios tragen überproportional zum erwarteten Verlust und Kapitalbedarf bei?
- Wie entwickeln sich PD/LGD/EAD über Zeit – und wie wirken sich Maßnahmen (z.B. Limitanpassungen, Besicherungsanforderungen, Pricing) aus?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| PD % | Probability of Default per exposure/segment | % |
| LGD % | Loss Given Default per exposure/segment | % |
| EAD Amount | Exposure at Default per exposure/segment | EUR |

---

## 5. Required Attributes (Business-Level)
- Portfolio: Product, Portfolio Type (Retail/Wholesale, Secured/Unsecured etc.).
- Org: Region, Legal Entity.
- Customer: Segment (Retail, SME, Corporate, Industry).
- Time: Reporting Date (Quarter/Year).

---

## 6. Segmentation & Hierarchies
- Portfolio: Portfolio Type > Product.
- Org: Region > Legal Entity.
- Customer: Segment > Rating/Stufe (optional).
- Time: Year > Quarter.

---

## 7. Scope & Assumptions
- PD/LGD/EAD stammen aus validierten Risikomodellen; Governance und Validierung liegen außerhalb dieses FactSheets und werden im Risk Framework dokumentiert.
- Aggregationen für Scorecards (z.B. Portfolio-Level PD) werden mit aufsichtsrechtlichen Vorgaben abgestimmt.

---

## 8. Data Freshness & Cadence
- Scorecard-Aktualisierung: monatlich/vierteljährlich, je nach Risiko- und Reporting-Rhythmus.
- Modellupdates: nach internen Model-Governance-Zyklen.

---

## 9. Edge Cases & QA Rules
- Exposures ohne validen PD/LGD/EAD-Wert werden separat ausgewiesen und in Abdeckungskennzahlen berücksichtigt.
- Veränderungen in Portfoliostruktur oder Modellparametern (z.B. Migration, neue Produkte) müssen dokumentiert werden, um Zeitreihenvergleich zu ermöglichen.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - PD, LGD, EAD pro Exposure/Portfolio-Segment.
  - Zuordnung zu Portfolio, Org, Kunden-Segment.
- Optional:
  - Historische Defaults und Recovery-Daten für Backtesting.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Adjust risk appetite and limits based on portfolio PD/LGD/EAD | G1 | Besser ausbalanciertes Risiko-/Rendite-Profil |
| Align pricing und Terms (z.B. Collateral, Covenants) mit Risikoprofil | SP1 | Höhere risikoadjustierte Rendite |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Risk | Besser gesteuerte Risikopositionen je Portfolio | PD, LGD, EAD-Anteile je Segment |
| Profitability | Verbesserte risikoadjustierte Rendite | Risk-adjusted Return, Expected Loss vs Pricing |

---

## 13. Related Processes
Credit Risk Modelling & Validation -> Limit & Pricing Policy -> Origination & Monitoring -> Provisioning & Capital Planning.

---

## 14. Insights & Learnings
Typische Insights: Bestimmte Produkte/Segmente tragen überproportional viel Expected Loss und Kapitalbedarf; andere sind deutlich risikoärmer und können gezielt wachsen.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-010 Enterprise Performance Cockpit](../COR-010_Enterprise_Performance_Cockpit/FactSheet.md)`  
  `[COR-009 Investment & CapEx Tracking](../COR-009_Investment_and_CapEx_Tracking/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Chief Risk Officer] |
| Technical Reviewer | [Head of Credit Risk Modelling] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first risk committee reviews] |

---

_Last updated: 19.11.2025_

