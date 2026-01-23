# KPI Catalog - CustomerValue

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: crm.clv.amount
  kpi_key: CLV (Customer Lifetime Value)
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  - XD-003
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Estimate long-term value of a customer to prioritize retention, acquisition, and service investments.
    definition: Sum of expected future gross margin per customer discounted over the chosen time horizon.
    grain_scope: Customer level; calculated on cohort or segment basis.
    unit_format: EUR (2 decimals)
    interpretation: Higher CLV indicates more valuable segments; compare against acquisition cost and churn risk.
  technical:
    dax_name: CLV
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to CLV model outputs within an agreed tolerance
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.revenue_at_risk.amount
  kpi_key: Revenue at Risk Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Quantify revenue exposure from customers flagged as churn-risk.
    definition: CLV Remaining Amount * Attrition Risk %.
    grain_scope: Customer/segment; monthly.
    unit_format: EUR (0 decimals)
    interpretation: Higher values indicate more revenue at risk; prioritize retention actions.
  technical:
    dax_name: Revenue at Risk Amount
    depends_on_measures: []
    lineage:
    - fact_customer_value.CLV Remaining Amount
    - fact_customer_events.Attrition Risk %
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - At-risk revenue reconciles to CLV remaining and attrition risk inputs within +/- 1 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.complaint.count
  kpi_key: Complaint Count
  kpi_type: activity
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: count
  business:
    purpose: Provide the absolute number of logged complaints.
    definition: Count of complaint records in the complaint/service system.
    grain_scope: Complaint / ticket; aggregated to org / channel / product / period.
    unit_format: count
    interpretation: Higher values indicate more issues; interpret with Complaint Rate % to normalize by volume.
  technical:
    dax_name: Complaint Count
    depends_on_measures: []
    lineage:
    - fact_complaint.ComplaintID
  governance:
    business_owner: Head of Customer Service
    data_owner: Service BI
    steward: Service Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Complaints reconciled to service desk reports
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.retention.pct
  kpi_key: Customer Retention %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measure the share of customers that remain active from one period to the next, as a core loyalty KPI.
    definition: (Active Customers at end of period) / (Active Customers at start of period).
    grain_scope: Customer / segment / org; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Higher retention indicates better loyalty and relationship quality; interpret jointly with churn and CLV.
  technical:
    dax_name: Customer Retention %
    depends_on_measures:
    - Active Customers Start Count
    - Active Customers End Count
    lineage:
    - dim_customer.CustomerKey
    - fact_sales.CustomerActivity
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: automated
    qa_rules:
    - Retention % within [0;100]
    - Active Customers Start > 0 for any reported slice
    version: v2.0
  metadata_quality:
    completeness_score: 0.97
    last_review: 12.10.2025

- kpi_id: crm.nps.index
  kpi_key: Net Promoter Score (NPS)
  kpi_type: index
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures customer advocacy and likelihood to recommend.
    definition: (%Promoters - %Detractors) from survey responses in the period.
    grain_scope: Survey response aggregated by period, segment, or region.
    unit_format: Index (-100 to 100)
    interpretation: '>0 is positive, >50 strong advocacy; track trend and segment gaps.'
  technical:
    dax_name: NPS Score
    depends_on_measures:
    - Promoters Count
    - Detractors Count
    - Total Respondents
    lineage:
    - fact_survey.Promoters
    - fact_survey.Detractors
    - fact_survey.Respondents
  governance:
    business_owner: Head of Customer Experience
    data_owner: CX BI
    steward: Customer Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Valid responses >= 80% of surveyed population
    version: v2.0
  metadata_quality:
    completeness_score: 0.95
    last_review: 12.10.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: crm.churned_customers.count
  kpi_key: Churned Customers
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: count
  business:
    purpose: Count customers that have stopped purchasing in the observation window as basis for churn calculations.
    definition: Distinct customers with no qualifying transactions in the current period but active in the look-back window.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: count
    interpretation: Higher counts indicate deteriorating retention; validate against cohort definitions.
  technical:
    dax_name: Churned Customers
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to churn cohort counts within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.lifetime_revenue.amount
  kpi_key: Customer Lifetime Revenue Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Sum of realized revenue across the customer lifecycle.
    definition: Sum of net sales amount from first purchase to date for the customer.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: EUR (0 decimals)
    interpretation: Base for concentration and CLV inputs.
  technical:
    dax_name: Customer Lifetime Revenue Amount
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    - dim_customer.CustomerKey
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to customer revenue history within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.active_customers.count
  kpi_key: Active Customers
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: count
  business:
    purpose: Number of unique active customers in the reporting period.
    definition: Distinct customers with at least one qualifying transaction in the period.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: count
    interpretation: Base for retention, churn and at-risk share calculations.
  technical:
    dax_name: Active Customers
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: automated + manual review
    qa_rules:
    - Reconciles to monthly active customer stats within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

```
