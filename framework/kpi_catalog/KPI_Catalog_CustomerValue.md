# KPI Catalog - CustomerValue

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: crm.retention.pct
  kpi_key: Customer Retention %
  kpi_type: strategic
  impact_dimension: customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-001
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
  kpi_type: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-005
  calc_type: rate
  business:
    purpose: Measures customer advocacy and likelihood to recommend.
    definition: (%Promoters - %Detractors) from survey responses in the period.
    grain_scope: Survey response aggregated by period, segment, or region.
    unit_format: Index (-100 to 100)
    interpretation: >0 is positive, >50 strong advocacy; track trend and segment gaps.
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

- kpi_id: market.share.total.pct
  kpi_key: Total Market Share %
  kpi_type: strategic
  impact_dimension: Growth
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-006
  calc_type: rate
  business:
    purpose: Measure the company's share of total addressable market volume or value.
    definition: Company sales (volume or value) divided by total market sales in the same scope.
    grain_scope: Market / segment / region; quarterly or annually.
    unit_format: '% (1 decimal)'
    interpretation: Higher share indicates stronger competitive position; track over time and vs key competitors.
  technical:
    dax_name: Total Market Share %
    depends_on_measures:
    - Net Sales Amount
    - Market Revenue Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_market.TotalMarketSales
  governance:
    business_owner: Head of Strategy
    data_owner: Corporate BI
    steward: Market Insight Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Market size estimates documented and refreshed at least annually
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: mkt.brand.awareness.pct
  kpi_key: Brand Awareness %
  kpi_type: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-009
  calc_type: rate
  business:
    purpose: Measure how many respondents recognize the brand (unaided or aided).
    definition: Number of respondents recognizing the brand divided by total valid respondents.
    grain_scope: Survey population / segment / region.
    unit_format: '% (1 decimal)'
    interpretation: Higher awareness is typically a prerequisite for consideration and preference; interpret together with
      Brand Preference %.
  technical:
    dax_name: Brand Awareness %
    depends_on_measures:
    - Brand Awareness Respondents Count
    - Total Respondents Count
    lineage:
    - fact_survey.BrandAwarenessFlag
  governance:
    business_owner: Head of Brand
    data_owner: Marketing Analytics
    steward: Brand Insight Analyst
    review_cycle: annually
    validation_process: manual review
    qa_rules:
    - Sampling frame and weighting scheme documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: mkt.brand.preference.pct
  kpi_key: Brand Preference %
  kpi_type: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-009
  calc_type: rate
  business:
    purpose: Measure how many respondents state the brand as first choice versus competitors.
    definition: Number of respondents naming the brand as first choice divided by total valid respondents.
    grain_scope: Survey population / segment / region.
    unit_format: '% (1 decimal)'
    interpretation: Higher preference indicates stronger brand equity and competitive position; interpret with Brand Awareness
      %.
  technical:
    dax_name: Brand Preference %
    depends_on_measures:
    - Brand Preference Respondents Count
    - Total Respondents Count
    lineage:
    - fact_survey.BrandPreferenceFlag
  governance:
    business_owner: Head of Brand
    data_owner: Marketing Analytics
    steward: Brand Insight Analyst
    review_cycle: annually
    validation_process: manual review
    qa_rules:
    - Sampling, questioning, and weighting approach documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: crm.churn.pct
  kpi_key: Customer Churn Rate %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-002
  calc_type: rate
  business:
    purpose: Measures proportion of customers lost during a period.
    definition: (Active Customers - Churned Customers) / Active Customers (Start of Period)
    grain_scope: Monthly; active base at period start.
    unit_format: '% (1 decimal)'
    interpretation: Lower churn = better retention.
  technical:
    dax_name: Churn Rate %
    depends_on_measures:
    - Churned Customers
    - Active Customers Start
    lineage:
    - fact_sales.CustomerStatus
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: automated
    qa_rules:
    - Churn Rate <= 100 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 12.10.2025

- kpi_id: crm.active_customers_start.count
  kpi_key: Active Customers Start
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
  calc_type: count
  business:
    purpose: Provide the opening active customer base used as denominator in retention and churn calculations.
    definition: Distinct active customers at the first day of the period.
    grain_scope: Customer/segment; monthly or quarterly at period start.
    unit_format: count
    interpretation: Baseline population; changes vs end-of-period indicate net growth or contraction.
  technical:
    dax_name: Active Customers Start
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to customer base snapshot within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.active_customers_end.count
  kpi_key: Active Customers End
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
  calc_type: count
  business:
    purpose: Provide the closing active customer base used as numerator in retention and at-risk share calculations.
    definition: Distinct active customers at the end of the period.
    grain_scope: Customer/segment; monthly or quarterly at period end.
    unit_format: count
    interpretation: End-of-period baseline for retention; compare with start to assess net change.
  technical:
    dax_name: Active Customers End
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to customer base snapshot within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.churned_customers.count
  kpi_key: Churned Customers
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
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

- kpi_id: crm.reactivated_customers.count
  kpi_key: Reactivated Customers Count
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
  calc_type: count
  business:
    purpose: Count win-back customers as numerator for reactivation KPIs.
    definition: Distinct customers with a prior churn status that show qualifying transactions again in the current period.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: count
    interpretation: Higher counts indicate successful win-back programs; review by segment/channel.
  technical:
    dax_name: Reactivated Customers Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to win-back campaign cohorts within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.clv.amount
  kpi_key: CLV (Customer Lifetime Value)
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
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

- kpi_id: crm.lifetime_revenue.amount
  kpi_key: Customer Lifetime Revenue Amount
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
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

- kpi_id: crm.revenue_at_risk.amount
  kpi_key: Revenue at Risk Amount
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
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

- kpi_id: crm.reactivation.pct
  kpi_key: Reactivation Rate %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Measure success of win-back efforts by showing what share of previously lost customers become active again.
    definition: Number of reactivated customers in the period / Number of customers previously classified as lost.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Higher rates indicate effective reactivation programs; validate cohort definitions.
  technical:
    dax_name: Reactivation Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reactivation cohorts reconcile to campaign exposure counts
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.at_risk_share.pct
  kpi_key: At-Risk Share %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Indicate what portion of the current customer base is flagged as churn-risk by the scoring model.
    definition: Number of customers with churn-risk flag / Total active customers in the period.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Higher share signals increased retention risk; align with risk thresholds and model calibration.
  technical:
    dax_name: At-Risk Share %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - At-risk base reconciles to scoring model output within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.at_risk_customers.count
  kpi_key: At-Risk Customers Count
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
  calc_type: count
  business:
    purpose: Provide the numerator for At-Risk Share % and support targeting of retention actions.
    definition: Distinct customers with an at-risk flag based on the churn model in the current period.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: count
    interpretation: Higher counts indicate more customers needing retention actions; verify scoring coverage.
  technical:
    dax_name: At-Risk Customers Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to scoring model output within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.active_customers.count
  kpi_key: Active Customers
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref: []
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

- kpi_id: sales.customer.revenue_share.pct
  kpi_key: Customer Revenue Share %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-006
  - CST-003
  calc_type: rate
  business:
    purpose: Show what share of total revenue is contributed by a given customer or segment.
    definition: Net Sales Amount of the selected customer or segment divided by total Net Sales Amount across all customers.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Helps identify key customers and concentration risk.
  technical:
    dax_name: Customer Revenue Share %
    depends_on_measures:
    - Net Sales Amount
    - Active Customers
    lineage:
    - fact_sales.Net Sales Amount
    - dim_customer.CustomerKey
  governance:
    business_owner: Head of CRM / Marketing Analytics
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Aggregated revenue share sums to 100 % within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.opportunities.open.amount
  kpi_key: Open Opportunities Amount
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-010
  - CST-010
  calc_type: amount
  business:
    purpose: Show the current value of open sales opportunities in the pipeline.
    definition: Sum of expected revenue (or deal amount) for all open opportunities in scope.
    grain_scope: Opportunity / account / segment; aggregated to org and time period.
    unit_format: EUR (2 decimals)
    interpretation: Indicates short- to mid-term revenue potential; interpret together with win rate and stage conversion.
  technical:
    dax_name: Open Opportunities Amount
    depends_on_measures: []
    lineage:
    - fact_crm_opportunity.ExpectedRevenue
  governance:
    business_owner: Head of Sales
    data_owner: CRM BI
    steward: Sales Operations
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Exclude non-open stages (e.g., Won/Lost) from "Open" definition
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.opportunities.won.amount
  kpi_key: Won Opportunities Amount
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-010
  - CST-010
  calc_type: amount
  business:
    purpose: Measure realized pipeline value from closed-won opportunities.
    definition: Sum of revenue (or booked amount) for all opportunities with status Won.
    grain_scope: Opportunity / account / segment; aggregated to org and time period.
    unit_format: EUR (2 decimals)
    interpretation: Indicates how much pipeline has converted into booked business.
  technical:
    dax_name: Won Opportunities Amount
    depends_on_measures: []
    lineage:
    - fact_crm_opportunity.BookedAmount
  governance:
    business_owner: Head of Sales
    data_owner: CRM BI
    steward: Sales Operations
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Status mapping (Won) documented and stable
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.opportunities.win_rate.pct
  kpi_key: Opportunity Win Rate %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-010
  - CST-010
  calc_type: rate
  business:
    purpose: Measure how many closed opportunities are won versus lost.
    definition: Won Opportunities Count / Total Closed Opportunities Count.
    grain_scope: Org / segment / seller; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Higher win rate indicates more effective selling; interpret jointly with deal size and pipeline quality.
  technical:
    dax_name: Opportunity Win Rate %
    depends_on_measures:
    - Won Opportunities Count
    - Total Closed Opportunities Count
    lineage:
    - fact_crm_opportunity.OpportunityStatus
  governance:
    business_owner: Head of Sales
    data_owner: CRM BI
    steward: Sales Operations
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Status categories for Won/Lost consistently mapped
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.opportunities.stage_conversion.pct
  kpi_key: Opportunity Stage Conversion %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-010
  - CST-010
  calc_type: rate
  business:
    purpose: Measure conversion between pipeline stages (e.g., Qualified -> Won).
    definition: Number of opportunities progressing from stage A to stage B divided by total opportunities in stage A.
    grain_scope: Stage / segment / seller; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Highlights funnel bottlenecks; low conversion indicates issues in qualification, proposal, or negotiation.
  technical:
    dax_name: Opportunity Stage Conversion %
    depends_on_measures: []
    lineage:
    - fact_crm_opportunity.Stage
  governance:
    business_owner: Head of Sales
    data_owner: CRM BI
    steward: Sales Operations
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Stage model and historic changes documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.complaint.rate.pct
  kpi_key: Complaint Rate %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-007
  calc_type: rate
  business:
    purpose: Measure complaints relative to delivered orders or customers.
    definition: Complaint Count divided by total orders (or customers) in period.
    grain_scope: Org / channel / product; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher complaint rate indicates quality or service issues; target is typically to reduce over time.
  technical:
    dax_name: Complaint Rate %
    depends_on_measures: []
    lineage:
    - fact_complaint.ComplaintCount
    - fact_sales.OrdersCount
  governance:
    business_owner: Head of Customer Service
    data_owner: Service BI
    steward: Service Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Complaint categorization and severity mapping documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.complaint.count
  kpi_key: Complaint Count
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-007
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

- kpi_id: crm.cross_sell_ratio.pct
  kpi_key: Cross-Sell Ratio %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-008
  calc_type: rate
  business:
    purpose: Measure the share of customers buying more than one product category.
    definition: Customers with purchases in 2 product categories divided by total active customers.
    grain_scope: Customer / segment; monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Higher ratio indicates better cross-sell performance and broader product adoption.
  technical:
    dax_name: Cross-Sell Ratio %
    depends_on_measures: []
    lineage:
    - fact_sales.CustomerID
    - dim_product.Category
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Customer ID and category mapping validated
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.basket_size.amount
  kpi_key: Average Basket Value
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-008
  calc_type: amount
  business:
    purpose: Measure the average monetary value of a transaction or order.
    definition: Total Net Sales Amount divided by number of orders in the selected period.
    grain_scope: Order / transaction; aggregated to channel / segment / period.
    unit_format: EUR (2 decimals)
    interpretation: Higher basket value typically indicates successful upsell/cross-sell, but must be interpreted with volume
      and margin.
  technical:
    dax_name: Average Basket Value
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.OrderID
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Order count definition consistent with billing rules
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.basket_size.units
  kpi_key: Average Basket Units
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-008
  calc_type: ratio
  business:
    purpose: Measure the average number of units per order.
    definition: Total units sold divided by number of orders.
    grain_scope: Order / transaction; aggregated to channel / segment / period.
    unit_format: units per order
    interpretation: Higher units per order indicate larger baskets; interpret with Average Basket Value for pricing/mix effects.
  technical:
    dax_name: Average Basket Units
    depends_on_measures: []
    lineage:
    - fact_sales.Units Qty
    - fact_sales.OrderID
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Order definition consistent between units and sales aggregation
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.acquisition.leads.count
  kpi_key: Leads Count
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-010
  calc_type: count
  business:
    purpose: Measure the number of new leads generated in the funnel.
    definition: Count of lead records created in the period.
    grain_scope: Lead / campaign; aggregated to channel / segment / period.
    unit_format: count
    interpretation: Higher lead counts indicate stronger top-of-funnel generation, but must be interpreted with conversion
      and CAC.
  technical:
    dax_name: Leads Count
    depends_on_measures: []
    lineage:
    - fact_crm_lead.LeadID
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Demand Generation Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Deduplication and spam filters applied
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.acquisition.conversions.count
  kpi_key: Acquisition Conversions Count
  kpi_type: supporting
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-010
  calc_type: count
  business:
    purpose: Measure how many leads convert to new customers or deals.
    definition: Count of leads that converted to customers or opportunities in the period.
    grain_scope: Lead / customer; aggregated to channel / segment / period.
    unit_format: count
    interpretation: Together with Leads Count shows funnel effectiveness.
  technical:
    dax_name: Acquisition Conversions Count
    depends_on_measures: []
    lineage:
    - fact_crm_lead.ConversionFlag
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Demand Generation Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Conversion definition (customer or opportunity) documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.acquisition.conversion_rate.pct
  kpi_key: Acquisition Conversion Rate %
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-010
  calc_type: rate
  business:
    purpose: Measure how efficiently leads convert into new customers or opportunities.
    definition: Acquisition Conversions Count / Leads Count.
    grain_scope: Channel / campaign / segment; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher conversion rate indicates more effective targeting and messaging; interpret with CAC.
  technical:
    dax_name: Acquisition Conversion Rate %
    depends_on_measures:
    - Leads Count
    - Acquisition Conversions Count
    lineage:
    - fact_crm_lead.LeadID
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Demand Generation Manager
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Leads and conversions definitions consistent across channels
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: crm.acquisition.cac.amount
  kpi_key: Customer Acquisition Cost (CAC) Amount
  kpi_type: diagnostic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-010
  calc_type: amount
  business:
    purpose: Measure average marketing and sales cost per new acquired customer.
    definition: Total acquisition spend divided by number of new customers acquired in the period.
    grain_scope: Channel / campaign / segment; monthly or quarterly.
    unit_format: EUR (2 decimals)
    interpretation: Lower CAC is better, but must be balanced with CLV and growth; extremely low CAC may indicate underinvestment.
  technical:
    dax_name: Customer Acquisition Cost (CAC) Amount
    depends_on_measures: []
    lineage:
    - fact_marketing_spend.AcquisitionSpend
    - dim_customer.CustomerID
  governance:
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Demand Generation Manager
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Acquisition spend allocation and new customer definition documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025

- kpi_id: market.share.relative.pct
  kpi_key: Relative Market Share %
  kpi_type: diagnostic
  impact_dimension: Growth
  domain_tag:
  - Customer & Market
  use_case_ref:
  - CST-006
  calc_type: rate
  business:
    purpose: Measure market share relative to the largest competitor.
    definition: Company market share divided by market share of the largest competitor.
    grain_scope: Market / segment / region; quarterly or annually.
    unit_format: ratio (x)
    interpretation: Values >1 indicate leadership vs the largest competitor; values <1 indicate follower position.
  technical:
    dax_name: Relative Market Share %
    depends_on_measures: []
    lineage:
    - fact_market.CompanyShare
    - fact_market.TopCompetitorShare
  governance:
    business_owner: Head of Strategy
    data_owner: Corporate BI
    steward: Market Insight Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Competitor mapping and estimates documented
    version: v0.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 19.11.2025
```
