# KPI Catalog - Liquidity

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "fin.liquidity.working_capital"
  kpi_key: "Working Capital %"
  kpi_type: "strategic"
  strategic_ref: "Working Capital %"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-001"]
  depends_on: ["Receivables Amount","Inventory Amount","Payables Amount","Net Sales Amount"]
  depends_on_ids: ["fin.liquidity.inventory.amount","fin.liquidity.payables.amount","sales.net_sales.amount"]
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
    description: "Share of (AR + Inventory - AP) relative to Net Sales."
    formatString: "0.0 %"
    verified: true
  governance:
    business_owner: "Head of Treasury"
    data_owner: "Finance BI"
    steward: "Treasury Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Reconcile with balance sheet +/-1 %"
      - "Inventory coverage ratio cross-checked monthly"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_id: "fin.liquidity.free_cash_flow"
  kpi_key: "Free Cash Flow"
  kpi_type: "strategic"
  strategic_ref: "Free Cash Flow"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-004"]
  depends_on: ["Operating Cash Flow","CapEx Amount"]
  depends_on_ids: ["fin.liquidity.operating_cash_flow","fin.liquidity.capex.amount"]
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
    description: "Net cash generated after capital expenditures."
    formatString: "EUR #,0.00"
    verified: true
  governance:
    business_owner: "Head of Treasury"
    data_owner: "Finance BI"
    steward: "Cashflow Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Reconcile with cashflow statement +/-1 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "fin.liquidity.dso_days_sales_outstanding"
  kpi_key: "DSO (Days Sales Outstanding)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Liquidity"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "DSO (Days)"
    formatString: "0"
    description: "(Accounts Receivable / Net Sales) x Days in Period"
    verified: false
  business:
    purpose: "Average number of days to collect receivables."
    definition: "(Accounts Receivable / Net Sales) x Days in Period"
    grain_scope: "Company/segment; monthly closing."
    unit_format: "days"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.operating_cash_flow"
  kpi_key: "Operating Cash Flow"
  kpi_type: "strategic"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  calc_type: amount
  technical:
    dax_name: "Operating Cash Flow"
    description: "Cash generated from operations"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.dio_days_inventory_outstanding"
  kpi_key: "DIO (Days Inventory Outstanding)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Liquidity"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "DIO (Days)"
    formatString: "0"
    description: "(Inventory / COGS) x Days in Period"
    verified: false
  business:
    purpose: "Average number of days inventory is held."
    definition: "(Inventory / COGS) x Days in Period"
    grain_scope: "Company/segment; monthly closing."
    unit_format: "days"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.dpo_days_payables_outstanding"
  kpi_key: "DPO (Days Payables Outstanding)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Liquidity"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "DPO (Days)"
    formatString: "0"
    description: "(Accounts Payable / COGS) x Days in Period"
    verified: false
  business:
    purpose: "Average number of days to pay suppliers."
    definition: "(Accounts Payable / COGS) x Days in Period"
    grain_scope: "Company/segment; monthly closing."
    unit_format: "days"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.cash_conversion_cycle_days"
  kpi_key: "Cash Conversion Cycle (Days)"
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Liquidity"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "CCC (Days)"
    formatString: "0"
    description: "DSO + DIO - DPO"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.cash_conversion_cycle.delta_days"
  kpi_key: "Δ Cash Conversion Cycle (Days)"
  aliases: ["Delta CCC (Days)"]
  kpi_type: "diagnostic"
  strategic_ref: "Cash Conversion Cycle"
  impact_dimension: "Liquidity"
  domain_tag: ["Operational Efficiency"]
  calc_type: amount
  technical:
    dax_name: "Δ CCC (Days)"
    formatString: "0"
    description: "CCC (Days) - Baseline (Plan or LY)"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```
```yaml
- kpi_key: "Days Sales Outstanding (DSO)"
  kpi_type: "supporting"
  strategic_ref: "Working Capital %"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-002"]
  depends_on: ["Receivables Amount","Net Sales Amount"]
  depends_on_ids: ["sales.net_sales.amount"]
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
  kpi_type: "supporting"
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

_Last updated: 04.11.2025_







```yaml
- kpi_id: "fin.liquidity.capex.amount"
  kpi_key: "CapEx Amount"
  kpi_type: "supporting"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  calc_type: amount
  technical:
    dax_name: "CapEx Amount"
    description: "Capital expenditures"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.inventory.amount"
  kpi_key: "Inventory Amount"
  kpi_type: "supporting"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  calc_type: amount
  technical:
    dax_name: "Inventory Amount"
    description: "Inventory value at period end"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```

```yaml
- kpi_id: "fin.liquidity.payables.amount"
  kpi_key: "Payables Amount"
  kpi_type: "supporting"
  impact_dimension: "Liquidity"
  domain_tag: ["Corporate & Strategy"]
  calc_type: amount
  technical:
    dax_name: "Payables Amount"
    description: "Accounts payable at period end"
    formatString: "EUR #,0.00"
    verified: false
  business:
    purpose: "TBD"
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "TBD"
  governance:
    business_owner: "TBD"
    data_owner: "TBD"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "TBD"
    version: "v1.0"
    last_review: "2025-11-04"

```






