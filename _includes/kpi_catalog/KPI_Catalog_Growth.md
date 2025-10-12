# KPI Catalog – Growth

---

## 1. Strategic KPIs
```yaml
- kpi_key: "Revenue Growth %"
  kpi_type: "strategic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001", "COM-002"]
  depends_on: ["Net Sales Amount", "Net Sales Amount LY"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Measures top-line expansion versus Plan and Last Year."
    definition: "((Net Sales Amount - Net Sales Amount LY) / Net Sales Amount LY)"
    grain_scope: "Aggregated at month and org level."
    unit_format: "% (1 decimal)"
    interpretation: "Shows revenue momentum and market success."
  technical:
    dax_name: "Revenue Growth %"
    dax_expression: "DIVIDE([Net Sales Amount]-[Net Sales Amount LY],[Net Sales Amount LY])"
    lineage: ["fact_sales.Net Sales Amount","fact_sales.Net Sales Amount LY"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.net_sales_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Variance within ±0.1 pp of plan reconciliation"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_key: "Net Sales Amount"
  kpi_type: "supporting"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: ["Invoice Line Amount"]
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Total invoiced revenue net of discounts and returns."
    definition: "Sum of all invoice line amounts net of VAT and returns."
    grain_scope: "Invoice line."
    unit_format: "€ (2 decimals)"
    interpretation: "Represents total top-line sales."
  technical:
    dax_name: "Net Sales Amount"
    dax_expression: "SUM(fact_sales[Net Sales Amount])"
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.net_sales_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Reconciles with P&L Revenue ±0.1 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_key: "Invoice Line Amount"
  kpi_type: "base"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: []
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Monetary value of a single invoice line before discounts."
    definition: "Quantity × Unit Price"
    grain_scope: "Invoice line"
    unit_format: "€ (2 decimals)"
    interpretation: "Base element of revenue."
  technical:
    dax_name: "Invoice Line Amount"
    dax_expression: "SUM(fact_sales[Invoice Line Amount])"
    lineage: ["fact_sales.Invoice Line Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.invoice_amt"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Data Steward Sales"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Must be ≥ 0"
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
| **Total KPIs (Growth)** | 31 |
| **Completeness Score (avg)** | 0.96 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Quarterly |
| **Business Owner** | Head of Sales |
| **Data Owner** | BI Engineering |
| **Steward** | Sales Analyst |
| **Validation Process** | Dual Control |

---

_Last updated: 12.10.2025_
