# KPI Catalog - Profitability

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "profit.gross_margin"
  kpi_key: "Gross Margin %"
  kpi_type: "strategic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-002"
    - "COM-003"
  depends_on:
    - "Net Sales Amount"
    - "COGS Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
  calc_type: "ratio"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measures gross margin relative to net sales."
    definition:
      "(Net Sales Amount - COGS Amount) / Net Sales Amount"
    grain_scope:
      "Invoice line aggregated to Org, Product, Date."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Core profitability metric showing sales efficiency vs cost."
  technical:
    dax_name:
      "Gross Margin %"
    dax_expression:
      "DIVIDE([Net Sales Amount]-[COGS Amount],[Net Sales Amount])"
    displayFolder:
      "02_Margin"
    formatString:
      "0.0 %"
    description:
      "Purpose: share of gross margin relative to net sales. Definition: ([Net Sales Amount]-[COGS Amount])/[Net Sales Amount]. Grain & Scope: aggregated from invoice_line by Date/Org/Product. Unit/Format: 0.0 %. Lineage: fact_sales Net Sales/COGS. QA: within [-100%;100%]; reconciles to P&L GM within +/-0.5 pp."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
    source_grain:
      "invoice_line"
    source_column_ref:
      - "fact_sales.net_sales_amt"
      - "fact_sales.cogs_amt"
    source_system:
      "ERP / Dataflow: fct_sales"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Controlling Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "dual control"
    qa_rules:
      - "Value in [-100%; 100%]"
      - "Reconcile with P&L Gross Margin +/-0.5 pp"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.97"
    lineage_verified:
      "true"
    copilot_ready:
      "true"

- kpi_id: "profit.ebitda_margin"
  kpi_key: "EBITDA Margin %"
  kpi_type: "strategic"
  strategic_ref: "EBITDA Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-002"
  depends_on:
    - "EBITDA Amount"
    - "Net Sales Amount"
  depends_on_ids:
    - "fin.ebitda.amount"
    - "sales.net_sales.amount"
  calc_type: "ratio"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Shows earnings before interest, taxes, depreciation, and amortization as a share of revenue."
    definition:
      "EBITDA Amount / Net Sales Amount"
    grain_scope:
      "Monthly close data, company level."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Represents operational profitability before financial effects."
  technical:
    dax_name:
      "EBITDA Margin %"
    dax_expression:
      "DIVIDE([EBITDA Amount],[Net Sales Amount])"
    displayFolder:
      "02_Margin"
    formatString:
      "0.0 %"
    description:
      "Purpose: EBITDA share of revenue. Definition: [EBITDA Amount]/[Net Sales Amount]. Grain & Scope: monthly close, company level. Unit/Format: 0.0 %. Lineage: finance EBITDA, sales revenue. QA: reconciles within +/-0.2 pp."
    lineage:
      - "fact_finance.EBITDA Amount"
      - "fact_sales.Net Sales Amount"
    source_grain:
      "financial_statement"
    source_column_ref:
      "fact_finance.ebitda_amt"
    source_system:
      "Finance"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "Finance BI"
    steward:
      "Financial Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "EBITDA reconciles with P&L within +/-0.2 pp"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.95"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
```


## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "cost.cogs.amount"
  kpi_key: "COGS Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  depends_on:
    - "Invoice Cost Amount"
  calc_type: "amount"
  refresh: "daily"
  status: "Active"
  business:
    purpose:
      "Represents cost of goods sold directly linked to sales."
    definition:
      "Sum of all product cost components for sold units."
    grain_scope:
      "Invoice line."
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Input for gross margin calculation."
  technical:
    dax_name:
      "COGS Amount"
    dax_expression:
      "SUM(fact_sales[COGS Amount])"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: direct product cost for sold units. Definition: sum of product cost components for sold units. Grain & Scope: invoice_line aggregated. Unit/Format: EUR #,0.00. Lineage: fact_sales[COGS Amount]. QA: reconcile with P&L COGS within +/-0.5%."
    lineage:
      "fact_sales.COGS Amount"
    source_grain:
      "invoice_line"
    source_column_ref:
      "fact_sales.cogs_amt"
    source_system:
      "ERP"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Finance Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "dual control"
    qa_rules:
      "COGS must reconcile with P&L COGS +/-0.5 %"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.99"
    lineage_verified:
      "true"
  copilot_ready: "true"

- kpi_key: "Δ Gross Margin %"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-002"]
  depends_on: ["Gross Margin %"]
  depends_on_ids: ["margin.gm.pct"]
  calc_type: rate
  refresh: monthly
  status: Draft
  business:
    purpose: "Relative change in Gross Margin % vs baseline (Plan or LY)."
    definition: "Gross Margin % - Baseline GM % (Plan or LY)."
    grain_scope: "Aggregated to reporting period."
    unit_format: "% (1 decimal)"
    interpretation: "Explains directional profitability change."
  technical:
    dax_name: "Δ Gross Margin %"
    dax_expression: "[Gross Margin %] - [Baseline GM %]"  # baseline to be bound to Plan or LY
    formatString: "0.0 %"
    displayFolder: "02_Margin"
    description: "Diagnostic GM variance relative to chosen baseline (Plan or LY)."
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "Commercial BI"
    steward: "Margin Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "GM variance reconciles to financial GM bridge within +/- 0.5 pp"
    version: "v1.0"
    last_review: "2025-11-04"

- kpi_id: "margin.gm.amount"
  kpi_key: "Gross Margin Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-002"
    - "COM-004"
  depends_on:
    - "Net Sales Amount"
    - "COGS Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Absolute gross margin in currency."
    definition:
      "Net Sales Amount - COGS Amount"
    grain_scope:
      "Aggregated from invoice_line to reporting period."
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Explains profitability magnitude before OpEx."
  technical:
    dax_name:
      "Gross Margin Amount"
    dax_expression:
      "[Net Sales Amount] - [COGS Amount]"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: currency value of gross margin. Definition: [Net Sales]-[COGS]. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: revenue and COGS measures. QA: reconciles to P&L GM within tolerance."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
    source_grain:
      "invoice_line"
    source_system:
      "ERP"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Controlling Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "dual control"
    qa_rules:
      "Reconcile with P&L GM within +/-0.5%"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.98"
    lineage_verified:
      "true"
  copilot_ready: "true"

- kpi_id: "margin.gm.pct"
  kpi_key: "Gross Margin % (Operational)"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-001"
    - "COM-002"
    - "COM-004"
    - "COM-006"
    - "COR-004"
  depends_on:
    - "Net Sales Amount"
    - "COGS Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
    - "cost.cogs.amount"
  calc_type: "ratio"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Provide the Gross Margin % used in commercial and management reporting at the same granularity as Net Sales."
    definition:
      "(Net Sales Amount - COGS Amount) / Net Sales Amount"
    grain_scope:
      "Invoice line aggregated to reporting period, org, customer or product segments."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Values above 0 % indicate positive gross profit; trend over time shows structural profitability changes."
  technical:
    dax_name:
      "Gross Margin %"
    dax_expression:
      "DIVIDE([Net Sales Amount]-[COGS Amount],[Net Sales Amount])"
    displayFolder:
      "02_Margin"
    formatString:
      "0.0 %"
    description:
      "Operational Gross Margin % measure used in COM and COR reports; aligned with strategic Gross Margin % definition."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
    source_grain:
      "invoice_line"
    source_system:
      "ERP / Dataflow: fct_sales"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Controlling Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      - "Reconciles to strategic Gross Margin % within +/- 0.1 pp for the same slice"
    version:
      "v1.0"
    last_review:
      "19.11.2025"
  metadata_quality:
    completeness_score:
      "0.9"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "margin.gm.delta_amount"
  kpi_key: "? Gross Margin Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-002"
    - "COM-004"
  depends_on:
    - "Gross Margin Amount"
    - "Baseline GM Amount"
  depends_on_ids:
    - "margin.gm.amount"
    - "margin.gm.plan.amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Explains absolute change in gross margin vs Plan or Last Year."
    definition:
      "Gross Margin Amount - Baseline GM Amount (Plan/LY)."
    grain_scope:
      "Aggregated to reporting period."
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Quantifies bridge contribution of gross margin variance."
  technical:
    dax_name:
      "? Gross Margin Amount"
    dax_expression:
      "[Gross Margin Amount] - [Baseline GM Amount]"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Absolute gross margin variance to the selected baseline (Plan or Last Year)."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "fact_plan_sales.Plan Gross Margin Amount"
    source_grain:
      "invoice_line"
    source_system:
      "ERP"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Controlling Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Variance reconciles to financial bridge within +/-0.5%"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.85"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "margin.gm.delta_pct"
  kpi_key: "Gross Margin % Δ%"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-002"
  depends_on:
    - "Gross Margin %"
  depends_on_ids:
    - "margin.gm.pct"
  calc_type: "rate"
  refresh: "monthly"
  status: "Draft"
  business:
    purpose:
      "Relative change in Gross Margin % vs Last Year."
    definition:
      "([Gross Margin %] - CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date]))) / CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date]))"
    grain_scope:
      "Aggregated to reporting period."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Shows relative profitability improvement vs LY."
  technical:
    dax_name:
      "Gross Margin % Δ%"
    dax_expression:
      "DIVIDE([Gross Margin %] - CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date])), CALCULATE([Gross Margin %], SAMEPERIODLASTYEAR('Date'[Date])))"
    displayFolder:
      "02_Margin"
    formatString:
      "0.0 %"
    description:
      "Relative change vs LY of Gross Margin %."
    verified:
      "false"
  governance:
    business_owner:
      "Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Finance Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Cross-check against GM% and LY base"
    version:
      "v1.0"
    last_review:
      "2025-11-06"

kpi_key: "Δ Gross Margin Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-004"
    - "COM-002"
  depends_on:
    - "Gross Margin Amount"
    - "Plan Gross Margin Amount"
  depends_on_ids: "margin.gm.plan.amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Absolute variance of gross margin vs plan."
    definition:
      "Gross Margin Amount (Actual) - Gross Margin Amount (Plan)"
    grain_scope:
      "Reporting period"
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Explains gap to plan for margin."
  technical:
    dax_name:
      "Δ Gross Margin Amount"
    dax_expression:
      "[Gross Margin Amount] - [Plan Gross Margin Amount]"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: absolute variance vs plan. Definition: GM Actual - GM Plan. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: GM measures (actual/plan). QA: reconciles with bridge within tolerance."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "fact_plan_sales.Plan Gross Margin Amount"
    source_grain:
      "period"
    source_system:
      "ERP/Planning"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Controlling Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Bridge reconciliation ≤0.5% absolute error"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.9"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "sales.promo.cost.amount"
  kpi_key: "Promo Cost Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  calc_type: "amount"
  refresh: "weekly"
  status: "Active"
  business:
    purpose:
      "Marketing investment spent on a promotion."
    definition:
      "Sum of promo fees, discounts, and marketing spend tagged to promotion ID."
    grain_scope:
      "Promo campaign / product / period."
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Cost basis for promo ROI."
  technical:
    dax_name:
      "Promo Cost Amount"
    dax_expression:
      "SUM(fact_sales[Promo Cost Amount])"
    displayFolder:
      "03_Price_Promo"
    formatString:
      "EUR #,0.00"
    description:
      "Aggregated promotion spend captured in fact_sales[Promo Cost Amount]."
    lineage:
      "fact_sales.Promo Cost Amount"
    source_grain:
      "invoice_line"
    source_system:
      "Trade Marketing"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Marketing Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Trade Marketing Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Promo spend reconciles to marketing accruals within +/-2 %"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.8"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "cost.cogs.promo.amount"
  kpi_key: "Promo COGS Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  depends_on:
    - "COGS Amount"
  depends_on_ids:
    - "cost.cogs.amount"
  calc_type: "amount"
  refresh: "weekly"
  status: "Active"
  business:
    purpose:
      "COGS limited to promo periods."
    definition:
      "COGS Amount where Promo Flag = true"
    grain_scope:
      "Promo period/product"
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Used to compute margin during promo."
  technical:
    dax_name:
      "Promo COGS Amount"
    dax_expression:
      "CALCULATE([COGS Amount], fact_sales[Promo Flag] = TRUE())"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: cost of goods during promotion. Definition: CALCULATE([COGS Amount], Promo Flag). Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: COGS with promo filter. QA: reconcile to campaign accounting."
    lineage:
      - "fact_sales.COGS Amount"
      - "fact_sales.Promo Flag"
    source_grain:
      "invoice_line"
    source_system:
      "ERP/Marketing"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Marketing Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Trade Marketing Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Promo cost allocation consistent with finance"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.9"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "sales.promo.incremental.amount"
  kpi_key: "Incremental Sales Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  depends_on:
    - "Promo Sales Amount"
    - "Baseline Sales Amount"
  depends_on_ids:
    - "sales.promo.amount"
    - "sales.baseline.amount"
  calc_type: "amount"
  refresh: "weekly"
  status: "Active"
  business:
    purpose:
      "Additional sales due to promotion."
    definition:
      "Promo Sales Amount - Baseline Sales Amount"
    grain_scope:
      "Promo period/product"
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Input to promo ROI."
  technical:
    dax_name:
      "Incremental Sales Amount"
    dax_expression:
      "[Promo Sales Amount] - [Baseline Sales Amount]"
    displayFolder:
      "01_Sales"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: incremental revenue vs baseline during promo. Definition: [Promo Sales]-[Baseline]. Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: promo and baseline revenue measures. QA: exclude overlaps; align to calendar."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.Promo Flag"
    source_grain:
      "invoice_line"
    source_system:
      "ERP/Marketing"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Marketing Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Trade Marketing Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Baseline method documented; overlap handling"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.9"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "margin.promo.incremental.amount"
  kpi_key: "Incremental GM Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  depends_on:
    - "Promo Sales Amount"
    - "Promo COGS Amount"
    - "Baseline Sales Amount"
    - "COGS Amount"
  depends_on_ids:
    - "sales.promo.amount"
    - "sales.baseline.amount"
    - "cost.cogs.amount"
    - "cost.cogs.promo.amount"
  calc_type: "amount"
  refresh: "weekly"
  status: "Active"
  business:
    purpose:
      "Additional gross margin due to promotion."
    definition:
      "(Promo Sales - Promo COGS) - (Baseline Sales - Baseline COGS)"
    grain_scope:
      "Promo period/product"
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Margin impact of promotions."
  technical:
    dax_name:
      "Incremental GM Amount"
    dax_expression:
      "([Promo Sales Amount]-[Promo COGS Amount]) - ([Baseline Sales Amount]-CALCULATE([COGS Amount], NOT fact_sales[Promo Flag]))"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: incremental gross margin due to promo. Definition: (Promo NS-Promo COGS)-(Baseline NS-Baseline COGS). Grain & Scope: promo/product. Unit/Format: EUR #,0.00. Lineage: promo/baseline revenue and costs. QA: allocation consistent."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "fact_sales.Promo Flag"
    source_grain:
      "invoice_line"
    source_system:
      "ERP/Marketing"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Marketing Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Trade Marketing Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Promo vs non-promo allocation documented"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.9"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "sales.promo.roi.pct"
  kpi_key: "Promo ROI %"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  depends_on:
    - "Incremental GM Amount"
    - "Promo Cost Amount"
  depends_on_ids:
    - "margin.promo.incremental.amount"
    - "sales.promo.cost.amount"
  calc_type: "ratio"
  refresh: "weekly"
  status: "Active"
  business:
    purpose:
      "Measures profitability of promotions relative to spend."
    definition:
      "(Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount"
    grain_scope:
      "Promo campaign / product / period."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Values > 0 indicate promotions adding value."
  technical:
    dax_name:
      "Promo ROI %"
    dax_expression:
      "DIVIDE([Incremental GM Amount] - [Promo Cost Amount],[Promo Cost Amount])"
    displayFolder:
      "03_Price_Promo"
    formatString:
      "0.0 %"
    description:
      "Return on promotion investments using incremental gross margin uplift."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "fact_sales.Promo Cost Amount"
    source_grain:
      "invoice_line"
    source_system:
      "Trade Marketing"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Marketing Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Trade Marketing Analyst"
    review_cycle:
      "monthly"
    validation_process:
      "manual review"
    qa_rules:
      - "Promo cost > 0 required"
      - "Variance vs finance ROI < 2 pp"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.82"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "margin.promo.gm.pct"
  kpi_key: "GM % During Promo"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-003"
  depends_on:
    - "Promo Sales Amount"
    - "Promo COGS Amount"
  depends_on_ids:
    - "sales.promo.amount"
    - "cost.cogs.promo.amount"
  calc_type: "ratio"
  refresh: "weekly"
  status: "Active"
  business:
    purpose:
      "Gross margin rate during promo periods."
    definition:
      "(Promo NS - Promo COGS) / Promo NS"
    grain_scope:
      "Promo period/product"
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Profitability of promotions."
  technical:
    dax_name:
      "GM % During Promo"
    dax_expression:
      "VAR _ns = [Promo Sales Amount] RETURN IF(_ns=0, BLANK(), DIVIDE([Promo Sales Amount]-[Promo COGS Amount], _ns))"
    displayFolder:
      "02_Margin"
    formatString:
      "0.0 %"
    description:
      "Purpose: margin rate during promotions. Definition: ([Promo Sales]-[Promo COGS])/[Promo Sales]. Grain & Scope: promo/product. Unit/Format: 0.0 %. Lineage: promo revenue and cost. QA: within [-100%;100%]."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "fact_sales.Promo Flag"
    source_grain:
      "invoice_line"
    source_system:
      "ERP/Marketing"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Marketing Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Trade Marketing Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Promo mapping consistent with finance"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.9"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

kpi_key: "Invoice Cost Amount"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: "COM-003"
  calc_type: "amount"
  refresh: "daily"
  status: "Active"
  business:
    purpose:
      "Base cost recorded per invoice line."
    definition:
      "Direct material + labor + overhead allocated to sold unit."
    grain_scope:
      "Invoice line"
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Primary element of cost for margin analysis."
  technical:
    dax_name:
      "Invoice Cost Amount"
    dax_expression:
      "SUM(fact_sales[Invoice Cost Amount])"
    displayFolder:
      "02_Margin"
    formatString:
      "EUR #,0.00"
    description:
      "Purpose: base cost per invoice line. Definition: direct material+labor+overhead allocated to sold unit. Grain & Scope: invoice_line. Unit/Format: EUR #,0.00. Lineage: fact_sales[Invoice Cost Amount]. QA: non-negative."
    lineage:
      "fact_sales.Invoice Cost Amount"
    source_grain:
      "invoice_line"
    source_column_ref:
      "fact_sales.invoice_cost_amt"
    source_system:
      "ERP"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Finance Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "dual control"
    qa_rules:
      "Invoice cost ≥ 0"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "1.00"
    lineage_verified:
      "true"
    copilot_ready:
      "true"

- kpi_id: "fin.ebitda.amount"
  kpi_key: "EBITDA Amount"
  kpi_type: "supporting"
  impact_dimension: "Profitability"
  domain_tag: ["Corporate & Strategy"]
  calc_type: "amount"
  business:
    purpose:
      "Provide EBITDA as key profitability indicator before financing and non-cash charges."
    definition:
      "Earnings before interest, taxes, depreciation and amortization for the period."
    grain_scope:
      "Company/segment; monthly or quarterly closing."
    unit_format:
      "EUR (2 decimals)"
  technical:
    dax_name:
      "EBITDA Amount"
    formatString:
      "EUR #,0.00"
    description:
      "Earnings before interest, taxes, depreciation, and amortization"
    verified:
      "false"
  governance:
    business_owner:
      "Head of FP&A"
    data_owner:
      "Finance BI"
    steward:
      "Financial Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "EBITDA reconciles to management P&L within +/- 0.5 %."
    version:
      "v1.0"
    last_review:
      "2025-11-04"

- kpi_id: "margin.gm.plan.amount"
  kpi_key: "Plan Gross Margin Amount"
  kpi_type: "supporting"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  calc_type: "amount"
  business:
    purpose:
      "Store planned gross margin to compare actual profitability against budget."
    definition:
      "Gross margin amount from approved plan or budget for the period."
    grain_scope:
      "Company/segment/product; aligned with planning hierarchy and calendar."
    unit_format:
      "EUR (2 decimals)"
  technical:
    dax_name:
      "Plan Gross Margin Amount"
    formatString:
      "EUR #,0.00"
    description:
      "Planned gross margin value for the period"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sales Controlling"
    data_owner:
      "Commercial BI"
    steward:
      "Margin Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Plan GM reconciles to approved budget/plan version; single source of truth for comparisons."
    version:
      "v1.0"
    last_review:
      "2025-11-04"

- kpi_id: "margin.customer.amount"
  kpi_key: "Customer Margin Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-006"
  depends_on:
    - "Net Sales Amount"
    - "COGS Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
    - "cost.cogs.amount"
  calc_type: "amount"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measure gross margin generated by a specific customer or customer segment."
    definition:
      "Net Sales Amount - COGS Amount aggregated by customer."
    grain_scope:
      "Customer / customer group / region / period."
    unit_format:
      "EUR (2 decimals)"
    interpretation:
      "Shows absolute profitability contribution of a customer or segment."
  technical:
    dax_name:
      "Customer Margin Amount"
    dax_expression:
      "[Net Sales Amount] - [COGS Amount]"
    displayFolder:
      "02_Margin"
    formatString:
      "€ #,0.00"
    description:
      "Gross margin amount per customer or customer segment (Net Sales - COGS)."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "dim_customer.CustomerID"
    source_grain:
      "invoice_line"
    source_system:
      "ERP"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sales Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Sales Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review and reconciliation vs margin bridge"
    qa_rules:
      - "Aggregated margin by customer reconciles to P&L gross margin within +/- 0.5 %"
    version:
      "v1.0"
    last_review:
      "2025-11-19"
  metadata_quality:
    completeness_score:
      "0.85"
    lineage_verified:
      "false"
    copilot_ready:
      "true"

- kpi_id: "margin.customer.pct"
  kpi_key: "Customer Margin %"
  kpi_type: "diagnostic"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref:
    - "COM-006"
  depends_on:
    - "Customer Margin Amount"
    - "Net Sales Amount"
  depends_on_ids:
    - "margin.customer.amount"
    - "sales.net_sales.amount"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Show gross margin rate for a customer or segment."
    definition:
      "Customer Margin Amount / Net Sales Amount."
    grain_scope:
      "Customer / customer group / region / period."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Values below target indicate unprofitable or weakly priced relationships."
  technical:
    dax_name:
      "Customer Margin %"
    dax_expression:
      "DIVIDE([Customer Margin Amount],[Net Sales Amount])"
    displayFolder:
      "02_Margin"
    formatString:
      "0.0 %"
    description:
      "Gross margin percentage per customer or segment."
    lineage:
      - "fact_sales.Net Sales Amount"
      - "fact_sales.COGS Amount"
      - "dim_customer.CustomerID"
    source_grain:
      "invoice_line"
    source_system:
      "ERP"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sales Controlling"
    data_owner:
      "BI Engineering"
    steward:
      "Sales Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review and comparison vs overall GM %"
    qa_rules:
      - "Weighted average customer margin % reconciles to overall GM % within +/- 0.2 pp"
    version:
      "v1.0"
    last_review:
      "2025-11-19"
  metadata_quality:
    completeness_score:
      "0.85"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```


