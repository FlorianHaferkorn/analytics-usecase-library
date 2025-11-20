# KPI Catalog - Risk

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Credit Risk (PD/LGD/EAD)
```yaml
- kpi_id: "fin.risk.pd.pct"
  kpi_key: "Probability of Default (PD) %"
  kpi_type: "diagnostic"
  strategic_ref: "Credit Risk"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy","Financial Services"]
  use_case_ref:
    - "COR-016"
  calc_type: "rate"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Measure the probability that a counterparty or exposure defaults within a defined time horizon."
    definition: "Estimated default probability per exposure or segment, typically over a 12-month horizon, derived from internal or regulatory credit risk models."
    grain_scope: "Exposure, counterparty or segment; aggregated by portfolio, region, product."
    unit_format: "% (1 decimal)"
    interpretation: "Higher PD indicates higher credit risk; interpret together with LGD % and EAD Amount for expected loss and capital calculations."
  technical:
    dax_name: "PD %"
    dax_expression: ""
    formatString: "0.0 %"
    displayFolder: "06_Risk\\Credit Risk"
    description: "Probability of Default per exposure or segment; used in expected loss and capital calculations."
    lineage:
      - "fact_credit_risk.PD"
    source_grain: "exposure"
    source_column_ref:
      - "fact_credit_risk.pd_pct"
    source_system: "Risk Engine / Core Banking"
    verified: false
  governance:
    business_owner: "Chief Risk Officer"
    data_owner: "Risk Analytics"
    steward: "Credit Risk Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Model validated per internal model governance and regulatory requirements"
    version: "v0.1"
    last_review: "19.11.2025"

- kpi_id: "fin.risk.lgd.pct"
  kpi_key: "Loss Given Default (LGD) %"
  kpi_type: "diagnostic"
  strategic_ref: "Credit Risk"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy","Financial Services"]
  use_case_ref:
    - "COR-016"
  calc_type: "rate"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Estimate the percentage loss on an exposure if a default occurs."
    definition: "Expected loss amount divided by EAD Amount, conditional on default, taking into account recoveries, collateral and workout costs."
    grain_scope: "Exposure, collateral type or segment; aggregated by portfolio, region, product."
    unit_format: "% (1 decimal)"
    interpretation: "Higher LGD indicates lower recovery and higher loss severity; interpret together with PD % and EAD Amount."
  technical:
    dax_name: "LGD %"
    dax_expression: ""
    formatString: "0.0 %"
    displayFolder: "06_Risk\\Credit Risk"
    description: "Loss Given Default percentage per exposure or segment."
    lineage:
      - "fact_credit_risk.LGD"
    source_grain: "exposure"
    source_column_ref:
      - "fact_credit_risk.lgd_pct"
    source_system: "Risk Engine / Core Banking"
    verified: false
  governance:
    business_owner: "Chief Risk Officer"
    data_owner: "Risk Analytics"
    steward: "Credit Risk Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "LGD assumptions and recovery curves documented and approved"
    version: "v0.1"
    last_review: "19.11.2025"

- kpi_id: "fin.risk.ead.amount"
  kpi_key: "Exposure at Default (EAD) Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Credit Risk"
  impact_dimension: "Governance"
  domain_tag: ["Corporate & Strategy","Financial Services"]
  use_case_ref:
    - "COR-016"
  calc_type: "amount"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose: "Measure the outstanding exposure amount expected at the time of default."
    definition: "Outstanding principal plus undrawn committed amounts (converted via credit conversion factors) at the moment of default."
    grain_scope: "Facility or exposure; aggregated by counterparty, portfolio, region, product."
    unit_format: "EUR (2 decimals)"
    interpretation: "Higher EAD increases expected loss and capital requirements; interpret with PD % and LGD %."
  technical:
    dax_name: "EAD Amount"
    dax_expression: ""
    formatString: "EUR #,0.00"
    displayFolder: "06_Risk\\Credit Risk"
    description: "Exposure at Default amount per facility or segment."
    lineage:
      - "fact_credit_risk.EAD"
    source_grain: "exposure"
    source_column_ref:
      - "fact_credit_risk.ead_amount"
    source_system: "Risk Engine / Core Banking"
    verified: false
  governance:
    business_owner: "Chief Risk Officer"
    data_owner: "Risk Analytics"
    steward: "Credit Risk Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "EAD reconciles with regulatory and internal risk reports"
    version: "v0.1"
    last_review: "19.11.2025"
```

