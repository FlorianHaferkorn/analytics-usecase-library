# KPI Catalog – Liquidity

---

## 1. Strategic KPIs
```yaml
- kpi_key: "Working Capital %"
  kpi_type: "strategic"
  strategic_ref: "Working Capital %"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-001"]
  depends_on: ["Receivables Amount","Inventory Amount","Payables Amount","Net Sales Amount"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Share of capital tied up in operations relative to sales."
    definition: "(Receivables + Inventory − Payables) / Net Sales Amount"
    grain_scope: "Monthly close level, companywide."
    unit_format: "% (1 decimal)"
    interpretation: "Indicates liquidity efficiency and cash tied up in operations."
  technical:
    dax_name: "Working Capital %"
    dax_expression: "DIVIDE([Receivables Amount]+[Inventory Amount]-[Payables Amount],[Net Sales Amount])"
    lineage: ["fact_balance.Receivables","fact_balance.Inventory","fact_balance.Payables","fact_sales.Net Sales Amount"]
    source_grain: "financial_statement"
    source_column_ref: ["fact_balance.receivables_amt","fact_balance.inventory_amt","fact_balance.payables_amt"]
    source_system: "Finance Dataflow"
    verified: true
  governance:
    business_owner: "Head of Treasury"
    data_owner: "Finance BI"
    steward: "Treasury Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Reconcile with balance sheet ±1 %"
      - "Inventory coverage ratio cross-checked monthly"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Free Cash Flow"
  kpi_type: "strategic"
  strategic_ref: "Free Cash Flow"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-004"]
  depends_on: ["Operating Cash Flow","CapEx Amount"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Net cash generated after capital expenditures."
    definition: "Operating Cash Flow − CapEx Amount"
    grain_scope: "Monthly companywide."
    unit_format: "€ (2 decimals)"
    interpretation: "Indicates cash generation capability after investment."
  technical:
    dax_name: "Free Cash Flow"
    dax_expression: "[Operating Cash Flow]-[CapEx Amount]"
    lineage: ["fact_cashflow.OperatingCashFlow","fact_cashflow.CapEx"]
    source_grain: "cashflow_statement"
    source_column_ref: ["fact_cashflow.ocf_amt","fact_cashflow.capex_amt"]
    source_system: "Finance"
    verified: true
  governance:
    business_owner: "Head of Treasury"
    data_owner: "Finance BI"
    steward: "Cashflow Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Reconcile with cashflow statement ±1 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_key: "Days Sales Outstanding (DSO)"
  kpi_type: "supporting"
  strategic_ref: "Working Capital %"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-002"]
  depends_on: ["Receivables Amount","Net Sales Amount"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Average number of days it takes to collect receivables."
    definition: "(Receivables Amount / Net Sales Amount) * Days in Period"
    grain_scope: "Company level per fiscal month."
    unit_format: "days"
    interpretation: "Lower values indicate faster cash conversion."
  technical:
    dax_name: "Days Sales Outstanding (DSO)"
    dax_expression: "DIVIDE([Receivables Amount],[Net Sales Amount])*[Days in Period]"
    lineage: ["fact_balance.Receivables","fact_sales.Net Sales Amount"]
    source_grain: "financial_statement"
    source_column_ref: ["fact_balance.receivables_amt"]
    source_system: "Finance"
    verified: true
  governance:
    business_owner: "Head of Treasury"
    data_owner: "Finance BI"
    steward: "Treasury Analyst"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "DSO < 90 days under normal conditions"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_key: "Receivables Amount"
  kpi_type: "base"
  strategic_ref: "Working Capital %"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-001"]
  depends_on: []
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Outstanding receivables at end of period."
    definition: "Sum of all unpaid invoices."
    grain_scope: "Company and customer level."
    unit_format: "€ (2 decimals)"
    interpretation: "Represents open cash position from customers."
  technical:
    dax_name: "Receivables Amount"
    dax_expression: "SUM(fact_balance[Receivables Amount])"
    lineage: ["fact_balance.Receivables Amount"]
    source_grain: "balance_line"
    source_column_ref: ["fact_balance.receivables_amt"]
    source_system: "Finance"
    verified: true
  governance:
    business_owner: "Head of Treasury"
    data_owner: "Finance BI"
    steward: "Treasury Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "No negative values allowed"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 1.00
    lineage_verified: true
    copilot_ready: true
```

---

## 4. Governance Summary
| Metric | Value |
|--------|--------|
| **Total KPIs (Liquidity)** | 31 |
| **Completeness Score (avg)** | 0.97 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Quarterly |
| **Business Owner** | Head of Treasury |
| **Data Owner** | Finance BI |
| **Steward** | Treasury Analyst |
| **Validation Process** | Dual Control |

---

_Last updated: 12.10.2025_
