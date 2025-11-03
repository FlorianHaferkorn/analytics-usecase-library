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
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: total invoiced sales excluding returns and taxes. Definition: sum of invoice line amounts net of VAT/returns. Grain & Scope: invoice_line aggregated to reporting period by Date/Org/Product. Unit/Format: EUR #,0.00. Lineage: fact_sales[Net Sales Amount]. QA: reconciles with P&L revenue within ±0.1%."
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

```yaml
- kpi_key: "Net Sales Amount LY"
  kpi_type: "supporting"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: ["Net Sales Amount"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Last year's net sales for period-over-period comparison."
    definition: "Net Sales Amount shifted by one year (same period last year)."
    grain_scope: "Aggregated from invoice line to period granularity."
    unit_format: "EUR (2 decimals)"
    interpretation: "Baseline reference for growth and variance."
  technical:
    dax_name: "Net Sales Amount LY"
    dax_expression: "CALCULATE([Net Sales Amount], SAMEPERIODLASTYEAR('Date'[Date]))"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: prior year reference for revenue comparison. Definition: [Net Sales Amount] shifted by SAMEPERIODLASTYEAR. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: fact_sales[Net Sales Amount], dim_date[Date]. QA: reconciles to prior year totals within ±0.1%."
    lineage: ["fact_sales.Net Sales Amount","dim_date.Date"]
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
      - "Reconciles with prior-year revenue within ±0.1 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Δ Net Sales Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  depends_on: ["Net Sales Amount","Net Sales Amount LY"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Absolute variance of Net Sales vs Last Year."
    definition: "Net Sales Amount - Net Sales Amount LY"
    grain_scope: "Aggregated to reporting period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Explains magnitude of change in revenue."
  technical:
    dax_name: "Δ Net Sales Amount"
    dax_expression: "[Net Sales Amount] - [Net Sales Amount LY]"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: absolute variance of revenue vs LY. Definition: [Net Sales Amount]-[Net Sales Amount LY]. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: measures above. QA: variance reconciliation within ±0.1 pp."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Variance reconciliation within ±0.1 pp"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Δ% Net Sales"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001"]
  depends_on: ["Δ Net Sales Amount","Net Sales Amount LY"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Relative variance of Net Sales vs Last Year."
    definition: "(Net Sales - LY) / LY"
    grain_scope: "Aggregated to reporting period."
    unit_format: "% (1 decimal)"
    interpretation: "Shows growth rate vs prior year."
  technical:
    dax_name: "Δ% Net Sales"
    dax_expression: "DIVIDE([Δ Net Sales Amount],[Net Sales Amount LY])"
    formatString: "0.0 %"
    displayFolder: "01_Sales"
    description: "Purpose: relative variance of revenue vs LY. Definition: [Δ Net Sales Amount]/[Net Sales Amount LY]. Grain & Scope: period-level. Unit/Format: 0.0 %. Lineage: measures above. QA: within ±0.1 pp of Revenue Growth %."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Within ±0.1 pp of Revenue Growth %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.96
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Price Realization %"
  kpi_type: "supporting"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-002"]
  depends_on: ["Net Sales Amount","List Price Amount"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures achieved net price relative to list price."
    definition: "Net Price / List Price (averaged at item level)."
    grain_scope: "Invoice line aggregated to reporting period."
    unit_format: "% (1 decimal)"
    interpretation: "Indicates pricing power and discount leakage."
  technical:
    dax_name: "Price Realization %"
    dax_expression: "DIVIDE([Net Sales Amount],[List Price Amount])"
    formatString: "0.0 %"
    displayFolder: "02_Margin"
    description: "Purpose: achieved net price relative to list price. Definition: [Net Sales Amount]/[List Price Amount] (averaged at item level as needed). Grain & Scope: invoice_line aggregated. Unit/Format: 0.0 %. Lineage: fact_sales[Net Sales Amount], fact_sales[List Price Amount]. QA: bounded within [0%;150%]."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.List Price Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.list_price_amt"]
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Pricing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Bounded within [0%; 150%]"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Promo Uplift %"
  kpi_type: "supporting"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-003"]
  depends_on: ["Promo Sales Amount","Baseline Sales Amount"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Measures incremental sales during promotion vs baseline."
    definition: "(Promo Sales - Baseline) / Baseline"
    grain_scope: "Aggregated per promotion period and product."
    unit_format: "% (1 decimal)"
    interpretation: "Indicates effectiveness of promotions."
  technical:
    dax_name: "Promo Uplift %"
    dax_expression: "DIVIDE([Promo Sales Amount]-[Baseline Sales Amount],[Baseline Sales Amount])"
    formatString: "0.0 %"
    displayFolder: "01_Sales"
    description: "Purpose: incremental sales during promo vs baseline. Definition: ([Promo Sales]-[Baseline])/ [Baseline]. Grain & Scope: product/promo-period. Unit/Format: 0.0 %. Lineage: fact_sales promo/baseline measures. QA: exclude overlapping promos; cap within [-100%;+500%]."
    lineage: ["fact_sales.Promo Sales Amount","fact_sales.Baseline Sales Amount"]
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
      - "Exclude overlapping promos; cap within [-100%; +500%]"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Price Effect Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-004","COM-001"]
  depends_on: ["Actual Unit Price","Plan Unit Price","Units Qty"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Quantifies portion of variance due to price change."
    definition: "(Actual Unit Price - Plan Unit Price) × Actual Qty"
    grain_scope: "Invoice line aggregated to reporting period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Isolates pricing from mix and volume."
  technical:
    dax_name: "Price Effect Amount"
    dax_expression: "SUMX(fact_sales, ([Actual Unit Price]-[Plan Unit Price])*[Units Qty])"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: portion of variance due to price change. Definition: (Actual Unit Price-Plan Unit Price)×Actual Qty. Grain & Scope: invoice_line aggregated. Unit/Format: EUR #,0.00. Lineage: unit price and quantity fields. QA: Price+Volume+Mix ≈ Δ Revenue (≤0.5% error)."
    lineage: ["fact_sales.Actual Unit Price","fact_sales.Plan Unit Price","fact_sales.Units Qty"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Sum of effects ≈ Δ Net Sales Amount (≤0.5 % absolute error)"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Volume Effect Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-004","COM-001"]
  depends_on: ["Units Qty","Plan Units Qty","Plan Unit Price"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Quantifies portion of variance due to quantity change."
    definition: "(Actual Qty - Plan Qty) × Plan Unit Price"
    grain_scope: "Invoice line aggregated to reporting period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Isolates volume from price and mix."
  technical:
    dax_name: "Volume Effect Amount"
    dax_expression: "SUMX(fact_sales, ([Units Qty]-[Plan Units Qty])*[Plan Unit Price])"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: portion of variance due to quantity change. Definition: (Actual Qty-Plan Qty)×Plan Unit Price. Grain & Scope: invoice_line aggregated. Unit/Format: EUR #,0.00. Lineage: quantities and plan unit price. QA: Price+Volume+Mix ≈ Δ Revenue (≤0.5% error)."
    lineage: ["fact_sales.Units Qty","fact_sales.Plan Units Qty","fact_sales.Plan Unit Price"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Sum of effects ≈ Δ Net Sales Amount (≤0.5 % absolute error)"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Mix Effect Amount"
  kpi_type: "diagnostic"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-004","COM-001"]
  depends_on: ["Δ Net Sales Amount","Price Effect Amount","Volume Effect Amount"]
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Residual variance after price and volume; composition change."
    definition: "Δ Net Sales Amount − Price Effect Amount − Volume Effect Amount"
    grain_scope: "Invoice line aggregated to reporting period."
    unit_format: "EUR (2 decimals)"
    interpretation: "Explains impact of product/channel/region mix."
  technical:
    dax_name: "Mix Effect Amount"
    dax_expression: "[Δ Net Sales Amount] - [Price Effect Amount] - [Volume Effect Amount]"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: residual variance after price and volume; composition change. Definition: Δ Net Sales - Price Effect - Volume Effect. Grain & Scope: period-level. Unit/Format: EUR #,0.00. Lineage: measures above. QA: Price+Volume+Mix ≈ Δ Revenue (≤0.5% error)."
    lineage: ["fact_sales.Net Sales Amount"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Sum of effects ≈ Δ Net Sales Amount (≤0.5 % absolute error)"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
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

```yaml
- kpi_key: "Units Qty"
  kpi_type: "base"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  depends_on: []
  calc_type: count
  refresh: daily
  status: Active
  business:
    purpose: "Number of units sold."
    definition: "Sum of sold units at invoice line grain."
    grain_scope: "Invoice line"
    unit_format: "pcs (integer)"
    interpretation: "Primary driver for volume effects."
  technical:
    dax_name: "Units Qty"
    dax_expression: "SUM(fact_sales[Units Qty])"
    formatString: "#,0"
    displayFolder: "01_Sales"
    description: "Purpose: count of units sold. Definition: sum of fact_sales[Units Qty]. Grain & Scope: invoice_line aggregated. Unit/Format: integer #,0. Lineage: fact_sales[Units Qty]. QA: non-negative; reconcile to shipments."
    lineage: ["fact_sales.Units Qty"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.units_qty"]
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales"
    data_owner: "BI Engineering"
    steward: "Sales Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Non-negative; reconcile to shipment totals"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.99
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "List Price Amount"
  kpi_type: "base"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-002"]
  depends_on: []
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Undiscounted price per line (catalog price)."
    definition: "Quantity × List Price per unit."
    grain_scope: "Invoice line"
    unit_format: "EUR (2 decimals)"
    interpretation: "Reference for price realization and discount leakage."
  technical:
    dax_name: "List Price Amount"
    dax_expression: "SUM(fact_sales[List Price Amount])"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: undiscounted line value at catalog price. Definition: quantity × list price per unit, summed. Grain & Scope: invoice_line. Unit/Format: EUR #,0.00. Lineage: fact_sales[List Price Amount]. QA: non-negative; discount corridor respected."
    lineage: ["fact_sales.List Price Amount"]
    source_grain: "invoice_line"
    source_column_ref: ["fact_sales.list_price_amt"]
    source_system: "ERP"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Pricing Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Non-negative; average discount within expected corridor"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Promo Sales Amount"
  kpi_type: "base"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-003"]
  depends_on: []
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Sales attributed to promotion periods/flags."
    definition: "Sum of net sales where Promo Flag = true."
    grain_scope: "Invoice line"
    unit_format: "EUR (2 decimals)"
    interpretation: "Input for uplift and promo ROI."
  technical:
    dax_name: "Promo Sales Amount"
    dax_expression: "CALCULATE([Net Sales Amount], fact_sales[Promo Flag] = TRUE())"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: revenue during promo periods. Definition: CALCULATE([Net Sales Amount], Promo Flag = TRUE). Grain & Scope: invoice_line aggregated. Unit/Format: EUR #,0.00. Lineage: net sales with promo filter. QA: reconcile to campaign calendar."
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
      - "Promo periods reconciled to campaign calendar"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Baseline Sales Amount"
  kpi_type: "base"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-003"]
  depends_on: []
  calc_type: amount
  refresh: weekly
  status: Active
  business:
    purpose: "Estimated sales without promotion."
    definition: "Modeled baseline (e.g., rolling non-promo average)."
    grain_scope: "Aggregated to product/period"
    unit_format: "EUR (2 decimals)"
    interpretation: "Reference for incremental uplift."
  technical:
    dax_name: "Baseline Sales Amount"
    dax_expression: "/* model-dependent */"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: modeled non-promo baseline revenue. Definition: method-dependent (e.g., rolling average of non-promo periods). Grain & Scope: product/period. Unit/Format: EUR #,0.00. Lineage: fact_sales with promo exclusions. QA: document baseline method; exclude overlaps."
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
      - "Exclude promo periods; document baseline method"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.85
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Actual Unit Price"
  kpi_type: "base"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-001","COM-004"]
  depends_on: ["Net Sales Amount","Units Qty"]
  calc_type: amount
  refresh: daily
  status: Active
  business:
    purpose: "Observed price per unit."
    definition: "Net Sales Amount / Units Qty"
    grain_scope: "Aggregated from invoice line"
    unit_format: "EUR (2 decimals)"
    interpretation: "Used in price effect calculations."
  technical:
    dax_name: "Actual Unit Price"
    dax_expression: "DIVIDE([Net Sales Amount],[Units Qty])"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: observed unit price. Definition: [Net Sales Amount]/[Units Qty]. Grain & Scope: aggregated from invoice_line. Unit/Format: EUR #,0.00. Lineage: measures above. QA: guard against divide-by-zero."
    lineage: ["fact_sales.Net Sales Amount","fact_sales.Units Qty"]
    source_grain: "invoice_line"
    source_system: "ERP"
    verified: true
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Pricing Analyst"
    review_cycle: "quarterly"
    validation_process: "dual control"
    qa_rules:
      - "Bound within realistic corridor (no division by 0)"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Plan Unit Price"
  kpi_type: "base"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-004","COM-001"]
  depends_on: []
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Planned unit price for comparison in PVM."
    definition: "Plan unit price at product/period."
    grain_scope: "Plan line / product-period"
    unit_format: "EUR (2 decimals)"
    interpretation: "Reference for price and volume effects."
  technical:
    dax_name: "Plan Unit Price"
    dax_expression: "AVERAGE(fact_plan_sales[Plan Unit Price])"
    formatString: "€ #,0.00"
    displayFolder: "01_Sales"
    description: "Purpose: planned unit price for PVM comparison. Definition: average plan unit price at product/period. Grain & Scope: plan_line. Unit/Format: EUR #,0.00. Lineage: fact_plan_sales[Plan Unit Price]. QA: plan freeze and versioning documented."
    lineage: ["fact_plan_sales.Plan Unit Price"]
    source_grain: "plan_line"
    source_system: "Planning"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Planning Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Plan freeze documented; reconcile to approved version"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
    copilot_ready: true
```

```yaml
- kpi_key: "Plan Units Qty"
  kpi_type: "base"
  strategic_ref: "Revenue Growth %"
  impact_dimension: "Growth"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-004","COM-001"]
  depends_on: []
  calc_type: count
  refresh: monthly
  status: Active
  business:
    purpose: "Planned quantity for PVM volume effect."
    definition: "Plan quantity at product/period."
    grain_scope: "Plan line / product-period"
    unit_format: "pcs (integer)"
    interpretation: "Reference for volume effect."
  technical:
    dax_name: "Plan Units Qty"
    dax_expression: "SUM(fact_plan_sales[Plan Units Qty])"
    formatString: "#,0"
    displayFolder: "01_Sales"
    description: "Purpose: planned quantity for volume effect. Definition: sum of plan quantity per product/period. Grain & Scope: plan_line. Unit/Format: integer #,0. Lineage: fact_plan_sales[Plan Units Qty]. QA: reconciles to approved plan snapshot."
    lineage: ["fact_plan_sales.Plan Units Qty"]
    source_grain: "plan_line"
    source_system: "Planning"
    verified: false
  governance:
    business_owner: "Head of Sales Controlling"
    data_owner: "BI Engineering"
    steward: "Planning Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Reconcile to plan version snapshot"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.9
    lineage_verified: false
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
