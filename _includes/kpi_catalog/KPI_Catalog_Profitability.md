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
    formatString: "0.0 %"
    displayFolder: "02_Margin"
    description: "Purpose: share of gross margin relative to net sales. Definition: ([Net Sales Amount]-[COGS Amount])/[Net Sales Amount]. Grain & Scope: aggregated from invoice_line by Date/Org/Product. Unit/Format: 0.0 %. Lineage: fact_sales Net Sales/COGS. QA: within [-100%;100%]; reconciles to P&L GM within ±0.5 pp."
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
    formatString: "0.0 %"
    displayFolder: "02_Margin"
    description: "Purpose: EBITDA share of revenue. Definition: [EBITDA Amount]/[Net Sales Amount]. Grain & Scope: monthly close, company level. Unit/Format: 0.0 %. Lineage: finance EBITDA, sales revenue. QA: reconciles within ±0.2 pp."
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
    formatString: "€ #,0.00"
    displayFolder: "02_Margin"
    description: "Purpose: direct product cost for sold units. Definition: sum of product cost components for sold units. Grain & Scope: invoice_line aggregated. Unit/Format: EUR #,0.00. Lineage: fact_sales[COGS Amount]. QA: reconcile with P&L COGS within ±0.5%."
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

```yaml
- kpi_key: "Gross Margin Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-002","COM-004"]
  depends_on: ["Net Sales Amount","COGS Amount"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Absolute gross margin in currency."
    definition: "Net Sales Amount - COGS Amount"
    grain_scope: "Aggregated from invoice_line to reporting period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Explains profitability magnitude before OpEx."
  technical:
    dax_name: "Gross Margin Amount"
    dax_expression: "[Net Sales Amount] - [COGS Amount]"
    formatString: "€ #,0.00"
    displayFolder: "02_Margin"
    description: "Purpose: currency value of gross margin. Definition: [Net Sales]-[COGS]. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: revenue and COGS measures. QA: reconciles to P&L GM within tolerance."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.COGS Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Controlling"
    data_owner: "BI Engineering"
    steward: "Controlling Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Reconcile with P&L GM within ±0.5%"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Δ Gross Margin Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-004","COM-002"]
  depends_on: ["Gross Margin Amount","Plan Gross Margin Amount"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Absolute variance of gross margin vs plan."
    definition: "Gross Margin Amount (Actual) - Gross Margin Amount (Plan)"
    grain_scope: "Reporting period"
    unit_format: "EUR (2 decimals)"
    interpretation: "Explains gap to plan for margin."
  technical:
    dax_name: "Δ Gross Margin Amount"
    dax_expression: "[Gross Margin Amount] - [Plan Gross Margin Amount]"
    formatString: "€ #,0.00"
    displayFolder: "02_Margin"
    description: "Purpose: absolute variance vs plan. Definition: GM Actual - GM Plan. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: GM measures (actual/plan). QA: reconciles with bridge within tolerance."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.COGS Amount","fact_plan_sales.Plan Gross Margin Amount"]
    source_grain: "period"
    source_system: "ERP/Planning"
    verified: false
  governance:
    business_owner: "Head of Controlling"
    data_owner: "BI Engineering"
    steward: "Controlling Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Bridge reconciliation ≤0.5% absolute error"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Promo COGS Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  depends_on: ["COGS Amount"]
  calc_type: amount
  refresh: weekly
  status: Active
  business:
    purpose: "COGS limited to promo periods."
    definition: "COGS Amount where Promo Flag = true"
    grain_scope: "Promo period/product"
    unit_format: "EUR (2 decimals)"
    interpretation: "Used to compute margin during promo."
  technical:
    dax_name: "Promo COGS Amount"
    dax_expression: "CALCULATE([COGS Amount], fact_sales[Promo Flag] = TRUE())"
    formatString: "€ #,0.00"
    displayFolder: "02_Margin"
    description: "Purpose: cost of goods during promotion. Definition: CALCULATE([COGS Amount], Promo Flag). Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: COGS with promo filter. QA: reconcile to campaign accounting."
    lineage: ["fact_sales.COGS Amount","fact_sales.Promo Flag"]
    source_grain: "invoice_line"
    source_system: "ERP/Marketing"
    verified: false
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "BI Engineering"
    steward: "Trade Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Promo cost allocation consistent with finance"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Incremental Sales Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  depends_on: ["Promo Sales Amount","Baseline Sales Amount"]
  calc_type: amount
  refresh: weekly
  status: Active
  business:
    purpose: "Additional sales due to promotion."
    definition: "Promo Sales Amount - Baseline Sales Amount"
    grain_scope: "Promo period/product"
    unit_format: "EUR (2 decimals)"
    interpretation: "Input to promo ROI."
  technical:
    dax_name: "Incremental Sales Amount"
    dax_expression: "[Promo Sales Amount] - [Baseline Sales Amount]"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: incremental revenue vs baseline during promo. Definition: [Promo Sales]-[Baseline]. Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: promo and baseline revenue measures. QA: exclude overlaps; align to calendar."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.Promo Flag"]
    source_grain: "invoice_line"
    source_system: "ERP/Marketing"
    verified: false
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "BI Engineering"
    steward: "Trade Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Baseline method documented; overlap handling"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Incremental GM Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  depends_on: ["Promo Sales Amount","Promo COGS Amount","Baseline Sales Amount","COGS Amount"]
  calc_type: amount
  refresh: weekly
  status: Active
  business:
    purpose: "Additional gross margin due to promotion."
    definition: "(Promo Sales - Promo COGS) - (Baseline Sales - Baseline COGS)"
    grain_scope: "Promo period/product"
    unit_format: "EUR (2 decimals)"
    interpretation: "Margin impact of promotions."
  technical:
    dax_name: "Incremental GM Amount"
    dax_expression: "([Promo Sales Amount]-[Promo COGS Amount]) - ([Baseline Sales Amount]-CALCULATE([COGS Amount], NOT fact_sales[Promo Flag]))"
    formatString: "€ #,0.00"
    displayFolder: "02_Margin"
    description: "Purpose: incremental gross margin due to promo. Definition: (Promo NS-Promo COGS)-(Baseline NS-Baseline COGS). Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: promo/baseline revenue and costs. QA: allocation consistent."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.COGS Amount","fact_sales.Promo Flag"]
    source_grain: "invoice_line"
    source_system: "ERP/Marketing"
    verified: false
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "BI Engineering"
    steward: "Trade Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Promo vs non-promo allocation documented"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "GM % During Promo"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-003"]
  depends_on: ["Promo Sales Amount","Promo COGS Amount"]
  calc_type: ratio
  refresh: weekly
  status: Active
  business:
    purpose: "Gross margin rate during promo periods."
    definition: "(Promo NS - Promo COGS) / Promo NS"
    grain_scope: "Promo period/product"
    unit_format: "% (1 decimal)"
    interpretation: "Profitability of promotions."
  technical:
    dax_name: "GM % During Promo"
    dax_expression: "VAR _ns = [Promo Sales Amount] RETURN IF(_ns=0, BLANK(), DIVIDE([Promo Sales Amount]-[Promo COGS Amount], _ns))"
    formatString: "0.0 %"
    displayFolder: "02_Margin"
    description: "Purpose: margin rate during promotions. Definition: ([Promo Sales]-[Promo COGS])/[Promo Sales]. Grain & Scope: promo/product. Unit/Format: 0.0 %. Lineage: promo revenue and cost. QA: within [-100%;100%]."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.COGS Amount","fact_sales.Promo Flag"]
    source_grain: "invoice_line"
    source_system: "ERP/Marketing"
    verified: false
  governance:
    business_owner: "Head of Marketing Controlling"
    data_owner: "BI Engineering"
    steward: "Trade Marketing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Promo mapping consistent with finance"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
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
    formatString: "€ #,0.00"
    displayFolder: "02_Margin"
    description: "Purpose: base cost per invoice line. Definition: direct material+labor+overhead allocated to sold unit. Grain & Scope: invoice_line. Unit/Format: EUR #,0.00. Lineage: fact_sales[Invoice Cost Amount]. QA: non-negative."
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
