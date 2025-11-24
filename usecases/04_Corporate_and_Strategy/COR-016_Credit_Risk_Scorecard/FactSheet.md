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

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
