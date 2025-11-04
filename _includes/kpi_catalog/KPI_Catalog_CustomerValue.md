# KPI Catalog — Customer Value

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_key: "Customer Retention %"
  kpi_type: "strategic"
  strategic_ref: "Customer Retention %"
  impact_dimension: "Customer Value"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-001"]
  depends_on: ["Active Customers","Churned Customers"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures customer loyalty and recurring engagement."
    definition: "(Active Customers − Churned Customers) / Active Customers (Start of Period)"
    grain_scope: "Customer level aggregated monthly."
    unit_format: "% (1 decimal)"
    interpretation: "Higher retention indicates customer satisfaction and strong relationships."
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
```

```yaml
- kpi_key: "Net Promoter Score (NPS)"
  kpi_type: "strategic"
  strategic_ref: "Net Promoter Score (NPS)"
  impact_dimension: "Customer Value"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-005"]
  depends_on: ["Promoters Count","Detractors Count","Total Respondents"]
  calc_type: ratio
  refresh: quarterly
  status: Active
  business:
    purpose: "Measures customer satisfaction and likelihood to recommend."
    definition: "% Promoters − % Detractors"
    grain_scope: "Survey responses; aggregated per quarter."
    unit_format: "index (−100 to 100)"
    interpretation: "Core metric for brand loyalty and service quality."
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
      - "Valid responses ≥ 80% of surveyed population"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.95
    lineage_verified: true
    copilot_ready: true
```

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_id: "crm.retention.pct"
  kpi_key: "Retention %"
  kpi_type: "strategic"
  domain_tag: ["Customer & Market"]
  calc_type: rate
  technical:
    dax_name: "Retention %"
    description: "Retained Customers / Total Customers (prior period)"
    formatString: "0.0 %"
    verified: false
```

```yaml
- kpi_id: "crm.churn.pct"
  kpi_key: "Churn %"
  kpi_type: "strategic"
  domain_tag: ["Customer & Market"]
  calc_type: rate
  technical:
    dax_name: "Churn %"
    description: "1 - Retention %"
    formatString: "0.0 %"
    verified: false
```

```yaml
- kpi_id: "crm.clv.amount"
  kpi_key: "CLV (Customer Lifetime Value)"
  kpi_type: "diagnostic"
  domain_tag: ["Customer & Market"]
  calc_type: amount
  technical:
    dax_name: "CLV"
    description: "∑ (Gross Margin per period / discount factor)"
    formatString: "€ #,0.00"
    verified: false
```

```yaml
- kpi_id: "crm.reactivation.pct"
  kpi_key: "Reactivation Rate %"
  kpi_type: "diagnostic"
  domain_tag: ["Customer & Market"]
  calc_type: rate
  technical:
    dax_name: "Reactivation Rate %"
    description: "Reactivated Customers / Lost Customers"
    formatString: "0.0 %"
    verified: false
```

```yaml
- kpi_id: "crm.at_risk_share.pct"
  kpi_key: "At-Risk Share %"
  kpi_type: "diagnostic"
  domain_tag: ["Customer & Market"]
  calc_type: rate
  technical:
    dax_name: "At-Risk Share %"
    description: "Customers flagged as churn-risk / Active Base"
    formatString: "0.0 %"
    verified: false
```
```yaml
- kpi_key: "Customer Churn Rate %"
  kpi_type: "supporting"
  strategic_ref: "Customer Retention %"
  impact_dimension: "Customer Value"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-002"]
  depends_on: ["Churned Customers","Active Customers"]
  calc_type: ratio
  refresh: monthly
  status: Active
  business:
    purpose: "Measures proportion of customers lost during a period."
    definition: "Churned Customers / Active Customers Start"
    grain_scope: "Customer level aggregated monthly."
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
      - "Churn Rate ≤ 100 %"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_key: "Active Customers"
  kpi_type: "base"
  strategic_ref: "Customer Retention %"
  impact_dimension: "Customer Value"
  domain_tag: ["Customer & Market"]
  use_case_ref: ["CST-001"]
  depends_on: []
  calc_type: count
  refresh: monthly
  status: Active
  business:
    purpose: "Number of unique active customers in the reporting period."
    definition: "Distinct count of customers with at least one purchase in the period."
    grain_scope: "Customer level."
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

## 4. Governance Summary
| Metric | Value |
|--------|--------|
| **Total KPIs (Customer Value)** | 31 |
| **Completeness Score (avg)** | 0.97 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Quarterly |
| **Business Owner** | Head of Marketing |
| **Data Owner** | CRM BI |
| **Steward** | Customer Insights Analyst |
| **Validation Process** | Automated |

---

_Last updated: 12.10.2025_
