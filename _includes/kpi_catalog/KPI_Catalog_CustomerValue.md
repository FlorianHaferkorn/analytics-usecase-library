# KPI Catalog - Customer Value

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "crm.retention.pct"
  kpi_key: "Customer Retention %"
  kpi_type: "strategic"
  strategic_ref: "Customer Retention %"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-001"]
  depends_on: ["Active Customers","Churned Customers"]
  depends_on_ids: ["crm.active_customers.count","crm.churned_customers.count"]
  calc_type: rate
  refresh: monthly
  status: Active
  technical:
    dax_name: "Customer Retention %"
    description: "Share of customers retained in period."
    formatString: "0.0 %"
    verified: false
  business:
  purpose: "Measures customer loyalty and recurring engagement."
  definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"
  grain_scope: "Monthly; active base at period start."
  unit_format: "% (1 decimal)"

  technical:
    dax_name: "Customer Retention %"
    dax_expression: "DIVIDE(([Active Customers]-[Churned Customers]),[Active Customers Start])"
    lineage: ["dim_customer.CustomerKey","fact_sales.CustomerActivity"]
    source_grain: "customer"
    source_column_ref: ["fact_sales.customer_activity"]
    source_system: "CRM"
    verified: true
  governance:
    business_owner: "Head of Marketing"
    data_owner: "CRM BI"
    steward: "Customer Insights Analyst"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "Retention % within [0;100]"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true


- kpi_id: "crm.nps.index"
  kpi_key: "Net Promoter Score (NPS)"
  kpi_type: "strategic"
  strategic_ref: "Net Promoter Score (NPS)"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-005"]
  depends_on: ["Promoters Count","Detractors Count","Total Respondents"]
  calc_type: rate
  refresh: quarterly
  status: Active
  business:
  purpose: "Measures customer loyalty and recurring engagement."
  definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"
  grain_scope: "Monthly; active base at period start."
  unit_format: "% (1 decimal)"

  technical:
    dax_name: "NPS Score"
    dax_expression: "([Promoters Count]-[Detractors Count])/[Total Respondents]*100"
    lineage: ["fact_survey.Promoters","fact_survey.Detractors","fact_survey.Respondents"]
    source_grain: "survey_response"
    source_column_ref: ["fact_survey.promoter_flag"]
    source_system: "Survey Tool"
    verified: true
  governance:
    business_owner: "Head of Customer Experience"
    data_owner: "CX BI"
    steward: "Customer Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "Valid responses >= 80% of surveyed population"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.95
    lineage_verified: true
    copilot_ready: true
```

## KPIs - Supporting / Diagnostic
```yaml
- kpi_id: "crm.churn.pct"
  kpi_key: "Customer Churn Rate %"
  kpi_type: "diagnostic"
  strategic_ref: "Customer Retention %"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-002"]
  depends_on: ["Churned Customers","Active Customers Start"]
  depends_on_ids: ["crm.churned_customers.count","crm.active_customers_start.count"]
  calc_type: rate
  refresh: monthly
  status: Active
  business:
    purpose: "Measures proportion of customers lost during a period."
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "Customer level aggregated monthly."
    unit_format: "% (1 decimal)"
    interpretation: "Lower churn = better retention."
  technical:
    dax_name: "Churn Rate %"
    dax_expression: "DIVIDE([Churned Customers],[Active Customers Start])"
    lineage: ["fact_sales.CustomerStatus"]
    source_grain: "customer"
    source_column_ref: ["fact_sales.customer_status"]
    source_system: "CRM"
    verified: true
  governance:
    business_owner: "Head of Marketing"
    data_owner: "CRM BI"
    steward: "Customer Insights Analyst"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "Churn Rate <= 100 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
  copilot_ready: true


- kpi_id: "crm.active_customers_start.count"
  kpi_key: "Active Customers Start"
  kpi_type: "supporting"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  calc_type: count
  technical:
    dax_name: "Active Customers Start"
    description: "Active customers at start of period (opening balance)"
    formatString: "0"
    verified: false


  business:
    purpose: "TBD"
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "TBD"
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

- kpi_id: "crm.churned_customers.count"
  kpi_key: "Churned Customers"
  kpi_type: "supporting"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  calc_type: count
  technical:
    dax_name: "Churned Customers"
    description: "Customers lost during the period"
    formatString: "0"
    verified: false

  business:
    purpose: "TBD"
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "TBD"
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

- kpi_id: "crm.clv.amount"
  kpi_key: "CLV (Customer Lifetime Value)"
  kpi_type: "diagnostic"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  calc_type: amount
  technical:
    dax_name: "CLV"
    description: "Î£ (Gross Margin per period / discount factor)"
    formatString: "€ #,0.00"
    verified: false


  business:
    purpose: "TBD"
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "TBD"
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

- kpi_id: "crm.reactivation.pct"
  kpi_key: "Reactivation Rate %"
  kpi_type: "diagnostic"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  calc_type: rate
  technical:
    dax_name: "Reactivation Rate %"
    description: "Reactivated Customers / Lost Customers"
    formatString: "0.0 %"
    verified: false


  business:
    purpose: "TBD"
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "TBD"
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

- kpi_id: "crm.at_risk_share.pct"
  kpi_key: "At-Risk Share %"
  kpi_type: "diagnostic"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  calc_type: rate
  technical:
    dax_name: "At-Risk Share %"
    description: "Customers flagged as churn-risk / Active Base"
    formatString: "0.0 %"
    verified: false


  business:
    purpose: "TBD"
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "TBD"
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

- kpi_id: "crm.active_customers.count"
  kpi_key: "Active Customers"
  kpi_type: "supporting"
  strategic_ref: "Customer Retention %"
  impact_dimension: "Customer"
  domain_tag: ["Customer & Market"]
  calc_type: count
  refresh: monthly
  status: Active
  business:
    purpose: "Number of unique active customers in the reporting period."
    definition: "(Active Customers - Churned Customers) / Active Customers (Start of Period)"`r`n    grain_scope: "Monthly; active base at period start."`r`n    unit_format: "% (1 decimal)"`r`n    grain_scope: "Customer level."
    unit_format: "count"
    interpretation: "Base for retention and churn calculation."
  technical:
    dax_name: "Active Customers"
    dax_expression: "DISTINCTCOUNT(fact_sales[CustomerKey])"
    lineage: ["dim_customer.CustomerKey","fact_sales.OrderDate"]
    source_grain: "customer"
    source_column_ref: ["fact_sales.customerkey"]
    source_system: "CRM"
    verified: true
  governance:
    business_owner: "Head of Marketing"
    data_owner: "CRM BI"
    steward: "Customer Data Steward"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "CustomerKey must be unique per period"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 1.00
    lineage_verified: true
    copilot_ready: true
```

---

Last updated: 04.11.2025







