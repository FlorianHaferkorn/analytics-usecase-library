# KPI Catalog – Profitability

---

## 1. Strategic KPIs
```yaml
- kpi_key: "Gross Margin %"
  kpi_type: "strategic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-002","COM-003"]
  depends_on: ["Net Sales Amount","COGS Amount"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures gross margin relative to net sales."
    definition: "(Net Sales Amount - COGS Amount) / Net Sales Amount"
    grain_scope: "Invoice line aggregated to Org, Product, Date."
    unit_format: "% (1 decimal)"
    interpretation: "Core profitability metric showing sales efficiency vs cost."
  technical:
    dax_name: "Gross Margin %"
    dax_expression: "DIVIDE([Net Sales Amount]-[COGS Amount],[Net Sales Amount])"
    lineage: ["fact_sales.Net Sales Amount","fact_sales.COGS Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.net_sales_amt","fact_sales.cogs_amt"]
    source_system: "ERP / Dataflow: fct_sales"
    verified: true
  governance:
    business_owner: "Head of Controlling"
    data_owner: "BI Engineering"
    steward: "Controlling Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Value ∈ [−100%; 100%]"
      - "Reconcile with P&L Gross Margin ±0.5 pp"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "EBITDA Margin %"
  kpi_type: "strategic"
  strategic_ref: "EBITDA Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref: ["COR-002"]
  depends_on: ["EBITDA Amount","Net Sales Amount"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Shows earnings before interest, taxes, depreciation, and amortization as a share of revenue."
    definition: "EBITDA Amount / Net Sales Amount"
    grain_scope: "Monthly close data, company level."
    unit_format: "% (1 decimal)"
    interpretation: "Represents operational profitability before financial effects."
  technical:
    dax_name: "EBITDA Margin %"
    dax_expression: "DIVIDE([EBITDA Amount],[Net Sales Amount])"
    lineage: ["fact_finance.EBITDA Amount","fact_sales.Net Sales Amount"]
    source_grain: "financial_statement"
    source_column_ref: ["fact_finance.ebitda_amt"]
    source_system: "Finance"
    verified: true
  governance:
    business_owner: "Head of Controlling"
    data_owner: "Finance BI"
    steward: "Financial Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "EBITDA reconciles with P&L within ±0.2 pp"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.95
    lineage_verified: true
    copilot_ready: true
```

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_key: "COGS Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  depends_on: ["Invoice Cost Amount"]
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Represents cost of goods sold directly linked to sales."
    definition: "Sum of all product cost components for sold units."
    grain_scope: "Invoice line."
    unit_format: "€ (2 decimals)"
    interpretation: "Input for gross margin calculation."
  technical:
    dax_name: "COGS Amount"
    dax_expression: "SUM(fact_sales[COGS Amount])"
    lineage: ["fact_sales.COGS Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.cogs_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Controlling"
    data_owner: "BI Engineering"
    steward: "Finance Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "COGS must reconcile with P&L COGS ±0.5 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.99
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_key: "Invoice Cost Amount"
  kpi_type: "base"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  depends_on: []
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Base cost recorded per invoice line."
    definition: "Direct material + labor + overhead allocated to sold unit."
    grain_scope: "Invoice line"
    unit_format: "€ (2 decimals)"
    interpretation: "Primary element of cost for margin analysis."
  technical:
    dax_name: "Invoice Cost Amount"
    dax_expression: "SUM(fact_sales[Invoice Cost Amount])"
    lineage: ["fact_sales.Invoice Cost Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.invoice_cost_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Controlling"
    data_owner: "BI Engineering"
    steward: "Finance Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Invoice cost ≥ 0"
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
| **Total KPIs (Profitability)** | 31 |
| **Completeness Score (avg)** | 0.96 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Quarterly |
| **Business Owner** | Head of Controlling |
| **Data Owner** | BI Engineering |
| **Steward** | Controlling Analyst |
| **Validation Process** | Dual Control |

---

_Last updated: 12.10.2025_
