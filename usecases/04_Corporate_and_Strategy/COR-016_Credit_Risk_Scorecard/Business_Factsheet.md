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

# Credit Risk Scorecard (PD/LGD/EAD) - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a PD/LGD/EAD-based view on credit risk across portfolios and segments to support pricing, limit setting, provisioning and capital allocation decisions.

---
- **Target Audience:** Chief Risk Officer / Head of Credit Risk
- **Business Priority:** Very High
- **Expected Impact:** Provide a PD/LGD/EAD-based view on credit risk across portfolios and segments to support pricing, limits, provisioning and capital decisions.

## 2. Core Questions
- Wie verteilen sich PD, LGD und EAD ber Portfolios, Produkte, Regionen und Kundensegmente?
- Welche Portfolios tragen berproportional zum erwarteten Verlust und Kapitalbedarf bei?
- Wie entwickeln sich PD/LGD/EAD ber Zeit " und wie wirken sich Manahmen (z.B. Limitanpassungen, Besicherungsanforderungen, Pricing) aus?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Probability of Default (PD) %, Loss Given Default (LGD) %, Exposure at Default (EAD) Amount with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a