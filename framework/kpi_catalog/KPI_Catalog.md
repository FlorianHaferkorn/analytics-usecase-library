# KPI Catalog

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs

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
    depends_on_measures:
    - Customer Lifetime Value Amount
    lineage:
    - fact_customer_value.CLV Amount
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
    completeness_score: 1.0
    last_review: 23.01.2026

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
    depends_on_measures:
    - Revenue at Risk Amount
    lineage:
    - fact_customer_events.Attrition Risk %
    - fact_customer_value.CLV Remaining Amount
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - At-risk revenue reconciles to CLV remaining and attrition risk inputs within +/- 1 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

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
    depends_on_measures:
    - Customer Complaints Count
    lineage:
    - fact_experience.Complaint ID
    business_owner: Head of Customer Service
    data_owner: Service BI
    steward: Service Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Complaints reconciled to service desk reports
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

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
    - Customer Retention %
    lineage: []
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
    last_review: 23.01.2026

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
    - NPS Score
    lineage:
    - fact_nps.NPS Score
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
    completeness_score: 1.0
    last_review: 23.01.2026

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
    depends_on_measures:
    - Churned Customers Count
    lineage:
    - dim_customer.CustomerKey
    - fact_customer_events.Churn Flag
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
    completeness_score: 1.0
    last_review: 23.01.2026

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
    depends_on_measures:
    - Customer Lifetime Revenue Amount
    lineage:
    - dim_customer.CustomerKey
    business_owner: Head of Marketing
    data_owner: CRM BI
    steward: Customer Insights Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to customer revenue history within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

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
    depends_on_measures:
    - Active Customers Count
    lineage:
    - dim_customer.CustomerKey
    - fact_customer_events.Activity Flag
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
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.performance.pct
  kpi_key: Performance %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref:
  - O-O1.2
  calc_type: rate
  business:
    purpose: Throughput speed versus theoretical maximum.
    definition: Actual output / Theoretical maximum output
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher performance indicates faster throughput; values above 100 % require validation of standard rates.
  technical:
    dax_name: Performance %
    depends_on_measures:
    - Performance %
    lineage:
    - fact_ops.Output Units
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Production Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Performance % bounded between 0 % and 150 %; investigate values outside expected range by line.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.quality.pct
  kpi_key: Quality %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref:
  - O-O1.3
  calc_type: rate
  business:
    purpose: Yield of conforming units relative to total units produced.
    definition: Good units / Total units
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher quality means fewer defects; low values indicate scrap/rework issues.
  technical:
    dax_name: Quality %
    depends_on_measures:
    - Quality %
    lineage:
    - fact_ops.Good Units
    - fact_ops.Output Units
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Quality Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Quality % bounded between 0 % and 100 %; reconcile to scrap/rework reporting within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.labor.productivity.pct
  kpi_key: Labor Productivity %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.3
  calc_type: rate
  business:
    purpose: Shows output efficiency relative to labor input.
    definition: Output Units or Net Sales divided by Labor Hours (normalized to % baseline).
    grain_scope: Line/site; reported weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better labor efficiency; validate against mix effects.
  technical:
    dax_name: Labor Productivity %
    depends_on_measures:
    - Labor Productivity %
    lineage:
    - fact_labor.Labor Hours
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Labor Hours > 0
    - Outliers reviewed for mix/shift effects
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.mtbf.hours
  kpi_key: MTBF (hours)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.2
  - O-A2.4
  calc_type: amount
  business:
    purpose: Measures average operating time between failures.
    definition: Operating Time Hours / Number of Failures.
    grain_scope: Asset/line; aggregated monthly.
    unit_format: hours
    interpretation: Higher is better; declining MTBF indicates reliability issues.
  technical:
    dax_name: MTBF (hours)
    depends_on_measures:
    - MTBF (hours)
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Reliability Engineer
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Failures count > 0 for ratio
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: ops.mttr.hours
  kpi_key: MTTR (hours)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.3
  - O-A2.5
  calc_type: amount
  business:
    purpose: Measures average repair time after failures.
    definition: Total Repair Time Hours / Number of Failures.
    grain_scope: Asset/line; aggregated monthly.
    unit_format: hours
    interpretation: Lower is better; high MTTR indicates slow recovery or parts issues.
  technical:
    dax_name: MTTR (hours)
    depends_on_measures:
    - MTTR (hours)
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Maintenance Lead
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Failures count > 0 for ratio
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: ops.pm_compliance.pct
  kpi_key: PM Compliance %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.4
  calc_type: rate
  business:
    purpose: Tracks adherence to preventive maintenance plan.
    definition: Completed PM Orders / Planned PM Orders.
    grain_scope: Site/asset; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low compliance increases breakdown risk.
  technical:
    dax_name: PM Compliance %
    depends_on_measures:
    - PM Compliance %
    lineage: []
  governance:
    business_owner: Head of Maintenance
    data_owner: Operations BI
    steward: Maintenance Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Planned PM Orders > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: ops.spare_parts.stockout.pct
  kpi_key: Spare Parts Stockout %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.5
  calc_type: rate
  business:
    purpose: Measures stockout frequency for critical spare parts.
    definition: Stockout Events / Total Parts Requests.
    grain_scope: Site/part; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; stockouts drive downtime and MTTR.
  technical:
    dax_name: Spare Parts Stockout %
    depends_on_measures:
    - Spare Parts Stockout %
    lineage:
    - fact_maintenance.Parts Stockout Flag
  governance:
    business_owner: Head of Maintenance
    data_owner: Operations BI
    steward: Spare Parts Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Requests count > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.throughput.units
  kpi_key: Throughput Units
  kpi_type: quantity
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref:
  - O-O1.2
  - O-O1.4
  calc_type: count
  business:
    purpose: Measures total output volume in units.
    definition: Sum of produced units in the period.
    grain_scope: Line/day; aggregated to site and month.
    unit_format: units
    interpretation: Higher values indicate higher output; analyze against capacity and demand.
  technical:
    dax_name: Throughput Units
    depends_on_measures:
    - Throughput Units
    lineage:
    - fact_ops.Output Units
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Output Units >= 0
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: quality.fpy.pct
  kpi_key: First Pass Yield %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  action_code_ref:
  - O-Q3.1
  - O-Q3.2
  calc_type: rate
  business:
    purpose: Measures share of units produced without rework or scrap.
    definition: Good Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low FPY indicates process instability.
  technical:
    dax_name: First Pass Yield %
    depends_on_measures:
    - First Pass Yield %
    lineage:
    - fact_quality.Good Units
    - fact_quality.Total Units
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: quality.scrap.pct
  kpi_key: Scrap Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  action_code_ref:
  - O-Q3.1
  - O-Q3.3
  - O-Q3.4
  calc_type: rate
  business:
    purpose: Measures share of units scrapped in production.
    definition: Scrap Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; rising scrap increases cost and reduces yield.
  technical:
    dax_name: Scrap Rate %
    depends_on_measures:
    - Scrap Rate %
    lineage:
    - fact_quality.Scrap Units
    - fact_quality.Total Units
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: quality.rework.pct
  kpi_key: Rework Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  action_code_ref:
  - O-Q3.1
  - O-Q3.3
  calc_type: rate
  business:
    purpose: Measures share of units requiring rework.
    definition: Reworked Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high rework impacts throughput and cost.
  technical:
    dax_name: Rework Rate %
    depends_on_measures:
    - Rework Rate %
    lineage:
    - fact_quality.Rework Units
    - fact_quality.Total Units
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: quality.copq.amount
  kpi_key: Cost of Poor Quality
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  action_code_ref:
  - O-Q3.4
  - O-Q3.5
  calc_type: amount
  business:
    purpose: Captures financial impact of scrap, rework, and warranty/complaints.
    definition: Sum of cost impacts for quality failures in period.
    grain_scope: Site/month; aggregated to business unit.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; high COPQ indicates process and supplier issues.
  technical:
    dax_name: Cost of Poor Quality
    depends_on_measures:
    - Cost of Poor Quality
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to quality cost ledger within +/-2 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: quality.complaint.pct
  kpi_key: Complaint Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  action_code_ref:
  - O-Q3.5
  calc_type: rate
  business:
    purpose: Measures customer complaints relative to shipped units.
    definition: Complaint Count / Units Shipped.
    grain_scope: Product/month; aggregated to business unit.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; spikes indicate quality or service issues.
  technical:
    dax_name: Complaint Rate %
    depends_on_measures:
    - Complaint Rate %
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Units Shipped > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026
  aliases:
  - crm.complaint.rate.pct

- kpi_id: quality.defect_density
  kpi_key: Defect Density
  kpi_type: rate
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  action_code_ref:
  - O-Q3.2
  calc_type: rate
  business:
    purpose: Measures defect count per 1,000 units produced.
    definition: (Defect Count / Total Units) * 1,000.
    grain_scope: Line/day; aggregated monthly.
    unit_format: defects per 1k units
    interpretation: Lower is better; indicates process stability.
  technical:
    dax_name: Defect Density
    depends_on_measures:
    - Defect Density
    lineage:
    - fact_quality.Defect Count
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Defect Count >= 0
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: inv.dio.days
  kpi_key: Days in Inventory
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  action_code_ref:
  - S-I1.1
  - S-I1.2
  - S-I1.4
  - S-I1.5
  calc_type: amount
  business:
    purpose: Measures inventory holding period in days.
    definition: Average Inventory / (COGS / 365).
    grain_scope: SKU/location; aggregated monthly.
    unit_format: days
    interpretation: Higher values indicate slower movement and more cash tied up.
  technical:
    dax_name: Days in Inventory
    depends_on_measures:
    - Days in Inventory
    lineage:
    - fact_cogs.COGS Amount
    - fact_inventory.Average Inventory Amount
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory and COGS reconciled to ledger
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: inv.stockout.pct
  kpi_key: Stockout Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  action_code_ref:
  - S-I1.1
  - S-I1.3
  - S-I1.5
  calc_type: rate
  business:
    purpose: Measures how often inventory is unavailable when demanded.
    definition: Stockout Events / Total Demand Events.
    grain_scope: SKU/location; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high stockout rate impacts service and revenue.
  technical:
    dax_name: Stockout Rate %
    depends_on_measures:
    - Stockout Rate %
    lineage:
    - fact_stockout.Stockout Flag
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Demand Events > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: inv.obsolete.pct
  kpi_key: Obsolete Inventory %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  action_code_ref:
  - S-I1.4
  calc_type: rate
  business:
    purpose: Measures share of inventory considered obsolete.
    definition: Obsolete Inventory Value / Total Inventory Value.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high obsolescence indicates slow movement or aging.
  technical:
    dax_name: Obsolete Inventory %
    depends_on_measures:
    - Obsolete Inventory %
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Value between 0 % and 100 %
    - Obsolete definition documented
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: plan.forecast.accuracy.pct
  kpi_key: Forecast Accuracy %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  - SCM-003
  action_code_ref:
  - S-F3.1
  - S-F3.2
  - S-F3.4
  - S-I1.5
  calc_type: rate
  business:
    purpose: Measures how close forecasted demand is to actual demand.
    definition: 1 - |Forecast - Actual| / Actual.
    grain_scope: SKU/week; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low accuracy drives inventory and service issues.
  technical:
    dax_name: Forecast Accuracy %
    depends_on_measures:
    - Forecast Accuracy %
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: plan.forecast.bias.pct
  kpi_key: Forecast Bias %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  action_code_ref:
  - S-F3.1
  - S-F3.2
  calc_type: rate
  business:
    purpose: Measures systematic over- or under-forecasting.
    definition: (Forecast - Actual) / Actual.
    grain_scope: SKU/week; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Values near 0 are best; positive bias indicates over-forecasting.
  technical:
    dax_name: Forecast Bias %
    depends_on_measures:
    - Bias %
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Bias bounded and reviewed for outliers
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026
  aliases:
  - sales.forecast.bias_pct

- kpi_id: plan.replan.count
  kpi_key: Re-Plan Count
  kpi_type: activity
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  action_code_ref:
  - S-F3.1
  - S-F3.4
  calc_type: count
  business:
    purpose: Counts number of replanning cycles in a period.
    definition: Total replan events logged in planning system.
    grain_scope: Planning cycle; aggregated monthly.
    unit_format: count
    interpretation: High values indicate planning instability or frequent disruptions.
  technical:
    dax_name: Re-Plan Count
    depends_on_measures:
    - Re-Plan Count
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Replan events counted once per cycle
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: supply.otif.pct
  kpi_key: OTIF %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  - SCM-002
  - SCM-003
  action_code_ref:
  - S-F3.3
  - S-I1.1
  - S-I1.3
  - S-R2.1
  - S-R2.2
  - S-R2.5
  calc_type: rate
  business:
    purpose: Measures share of orders delivered on time and in full.
    definition: OTIF Orders / Total Orders.
    grain_scope: Order/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; key service level indicator.
  technical:
    dax_name: OTIF %
    depends_on_measures:
    - OTIF %
    lineage:
    - fact_fulfillment.OTIF Flag
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Orders > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: supply.on_time.pct
  kpi_key: On-Time %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  action_code_ref:
  - S-R2.1
  - S-R2.2
  calc_type: rate
  business:
    purpose: Measures share of deliveries arriving on time.
    definition: On-Time Deliveries / Total Deliveries.
    grain_scope: Delivery/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; analyze by carrier and lane.
  technical:
    dax_name: On-Time %
    depends_on_measures:
    - On-Time %
    lineage:
    - fact_fulfillment.On-Time Flag
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Deliveries > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: supply.stockout_impact.pct
  kpi_key: Stockout Impact %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  action_code_ref:
  - S-R2.3
  calc_type: rate
  business:
    purpose: Measures lost demand share due to stockouts.
    definition: Lost Demand Qty / Total Demand Qty.
    grain_scope: SKU/location/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; ties inventory and service performance.
  technical:
    dax_name: Stockout Impact %
    depends_on_measures:
    - Stockout Impact %
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Demand Qty > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: supply.expedite.amount
  kpi_key: Expedite Cost Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  action_code_ref:
  - S-R2.4
  - S-R2.5
  calc_type: amount
  business:
    purpose: Captures additional cost for expedited shipments.
    definition: Sum of expedite fees and premium freight charges.
    grain_scope: Shipment/month.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; high values indicate planning or supply issues.
  technical:
    dax_name: Expedite Cost Amount
    depends_on_measures:
    - Expedite Cost Amount
    lineage:
    - fact_fulfillment.Expedite Cost
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Expedite costs reconciled to logistics ledger
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: supply.penalty.amount
  kpi_key: Penalty Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  action_code_ref:
  - S-R2.4
  calc_type: amount
  business:
    purpose: Captures penalties for service level breaches.
    definition: Sum of penalty charges incurred in the period.
    grain_scope: Order/month.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; high penalties signal delivery or quality issues.
  technical:
    dax_name: Penalty Amount
    depends_on_measures:
    - Penalty Amount
    lineage:
    - fact_fulfillment.Penalty Amount
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Penalties reconciled to claims ledger
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: plan.forecast.service_impact.pct
  kpi_key: Service Impact %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  use_case_ref:
  - SCM-003
  action_code_ref:
  - S-F3.3
  calc_type: rate
  business:
    purpose: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage (units-based demand forecast).
    definition: Service Impact % = Stockout Impact % x (Under-Forecast Lost Demand / Total Lost Demand). Under-forecast is defined as a negative forecast error below a configurable threshold; all inputs are unit-based (qty), not revenue.
    grain_scope: Calculated at location_sku_day or sku_week; reported at sku_month aggregated by Date, Org, Product.
    unit_format: "%"
    interpretation: Lower values are better; high impact indicates forecast under-coverage driving service loss.
  technical:
    dax_name: Service Impact %
    depends_on_measures:
    - Service Impact %
    lineage:
    - fact_forecast.Forecast Units
    - fact_stockout.Demand Units
    - fact_stockout.Lost Demand Units
  governance:
    business_owner: Head of Supply Chain Planning
    data_owner: Supply Chain BI
    steward: Demand Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
      - KPI only valid when Total Demand Qty > 0.
      - Service Impact % must be <= Stockout Impact %.
      - Under-Forecast Lost Demand Share must be between 0 % and 100 %.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.oee.pct
  kpi_key: Overall Equipment Effectiveness (OEE) %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref:
  - O-O1.1
  - O-O1.3
  - O-O1.4
  calc_type: ratio
  business:
    purpose: Measures manufacturing performance combining availability, performance, and quality.
    definition: Availability % * Performance % * Quality %
    grain_scope: Production line; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher OEE indicates better utilization; capped at 100 %.
  technical:
    dax_name: OEE %
    depends_on_measures:
    - OEE %
    lineage:
    - fact_ops.Good Units
    - fact_ops.Output Units
    - fact_ops.Planned Time Minutes
    - fact_ops.Run Time Minutes
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: MES Analyst
    review_cycle: quarterly
    validation_process: automated + manual spot checks
    qa_rules:
    - Subcomponents validated against MES feed; OEE = 100 %
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.failure.count
  kpi_key: Failure Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.2
  - O-A2.3
  - O-A2.5
  calc_type: count
  business:
    purpose: Counts equipment or process failures in the period.
    definition: Count of recorded failure events.
    grain_scope: Asset or line; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate lower reliability.
  technical:
    dax_name: Failure Count
    depends_on_measures:
    - Failure Count
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Maintenance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Failures reconcile with maintenance logs.
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: ops.inventory.value.amount
  kpi_key: Inventory Value Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - OPS-002
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Tracks inventory value for maintenance-relevant items.
    definition: Sum of inventory value amount for the selected scope.
    grain_scope: SKU/location; aggregated by period.
    unit_format: EUR (2 decimals)
    interpretation: Higher values indicate more capital tied in spare parts.
  technical:
    dax_name: Inventory Value Amount
    depends_on_measures:
    - Inventory Value Amount
    lineage: []
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: ops.planned_output.units
  kpi_key: Planned Output Units
  kpi_type: quantity
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - OPS-003
  action_code_ref:
  - O-O1.4
  - O-Q3.1
  - O-Q3.2
  - O-Q3.3
  calc_type: count
  business:
    purpose: Captures planned production output volume.
    definition: Sum of planned output units for the period.
    grain_scope: Line/site; aggregated by period.
    unit_format: units
    interpretation: Baseline for comparing actual throughput.
  technical:
    dax_name: Planned Output Units
    depends_on_measures:
    - Planned Output Units
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Production Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: ops.pm.task.count
  kpi_key: Preventive Maintenance Task Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.4
  calc_type: count
  business:
    purpose: Counts preventive maintenance tasks executed or scheduled.
    definition: Count of PM tasks in the period.
    grain_scope: Asset; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate more planned maintenance activity.
  technical:
    dax_name: Preventive Maintenance Task Count
    depends_on_measures:
    - Preventive Maintenance Task Count
    lineage: []
  governance:
    business_owner: Head of Maintenance
    data_owner: Maintenance BI
    steward: Maintenance Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: ops.production.volume
  kpi_key: Production Volume Units
  kpi_type: quantity
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.3
  calc_type: count
  business:
    purpose: Measures total produced volume in units.
    definition: Sum of produced units for the period.
    grain_scope: Line/site; aggregated by period.
    unit_format: units
    interpretation: Higher values indicate higher output.
  technical:
    dax_name: Production Volume Units
    depends_on_measures:
    - Production Volume Units
    lineage:
    - fact_ops.Output Units
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Production Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.quality.defect_rate.pct
  kpi_key: Quality Defect Rate %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of defective units in production.
    definition: Defective Units / Total Produced Units.
    grain_scope: Line/shift; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Lower values indicate better quality.
  technical:
    dax_name: Quality Defect Rate %
    depends_on_measures:
    - Quality Defect Rate %
    lineage:
    - fact_ops.Output Units
    - fact_quality.Defect Count
  governance:
    business_owner: Head of Quality
    data_owner: Quality BI
    steward: Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.safety.incident.count
  kpi_key: Safety Incident Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref: []
  calc_type: count
  business:
    purpose: Counts safety incidents recorded in the period.
    definition: Count of recorded safety incidents.
    grain_scope: Site; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate higher safety risk.
  technical:
    dax_name: Safety Incident Count
    depends_on_measures:
    - Safety Incident Count
    lineage: []
  governance:
    business_owner: EHS Manager
    data_owner: EHS BI
    steward: Safety Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: ops.service_level.pct
  kpi_key: Operations Service Level %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures on-time or in-full performance for operational delivery.
    definition: On-Time or In-Full Deliveries / Total Deliveries.
    grain_scope: Site/product; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better service performance.
  technical:
    dax_name: Operations Service Level %
    depends_on_measures:
    - Operations Service Level %
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: ops.yield.pct
  kpi_key: Yield %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures ratio of good output to total input.
    definition: Good Units / Total Units Produced.
    grain_scope: Line/shift; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Higher yield indicates better process efficiency.
  technical:
    dax_name: Yield %
    depends_on_measures:
    - Yield %
    lineage:
    - fact_ops.Good Units
    - fact_ops.Output Units
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Process Engineer
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: order.lines
  kpi_key: Order Lines Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - SCM-002
  - SCM-003
  action_code_ref:
  - S-F3.3
  - S-R2.3
  calc_type: count
  business:
    purpose: Counts order lines processed in the period.
    definition: Count of order line items.
    grain_scope: Order line; aggregated by period and channel.
    unit_format: count
    interpretation: Higher counts indicate higher order volume.
  technical:
    dax_name: Order Lines Count
    depends_on_measures:
    - Order Lines Count
    lineage: []
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Order Management Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: plans.count
  kpi_key: Plans Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Forecast Planning
  use_case_ref:
  - SCM-003
  action_code_ref:
  - S-F3.4
  calc_type: count
  business:
    purpose: Counts planning cycles or plan versions in the period.
    definition: Count of plan records or plan versions.
    grain_scope: Plan; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate more planning activity.
  technical:
    dax_name: Plans Count
    depends_on_measures:
    - Plans Count
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: shipments.count
  kpi_key: Shipments Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - SCM-002
  action_code_ref:
  - S-R2.1
  - S-R2.2
  - S-R2.4
  - S-R2.5
  calc_type: count
  business:
    purpose: Counts shipments executed in the period.
    definition: Count of shipment records.
    grain_scope: Shipment; aggregated by period and carrier.
    unit_format: count
    interpretation: Higher counts indicate higher fulfillment activity.
  technical:
    dax_name: Shipments Count
    depends_on_measures:
    - Shipments Count
    lineage: []
  governance:
    business_owner: Head of Logistics
    data_owner: Logistics BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: scm.service_level.pct
  kpi_key: Supply Chain Service Level %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - FIN-001
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures supply chain service level performance.
    definition: On-Time In-Full Orders / Total Orders.
    grain_scope: Customer/order; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better service reliability.
  technical:
    dax_name: Supply Chain Service Level %
    depends_on_measures:
    - Supply Chain Service Level %
    lineage:
    - fact_fulfillment.OTIF Flag
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Service Level Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.availability.pct
  kpi_key: Availability %
  kpi_type: percentage
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - OPS-002
  action_code_ref:
  - O-A2.1
  - O-A2.3
  - O-O1.1
  calc_type: rate
  business:
    purpose: Uptime share relative to planned production time.
    definition: Available time / Planned time
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher availability indicates less downtime; low values typically reflect maintenance or scheduling issues.
  technical:
    dax_name: Availability %
    depends_on_measures:
    - Availability %
    lineage:
    - fact_ops.Planned Time Minutes
    - fact_ops.Run Time Minutes
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Availability % bounded between 0 % and 100 %; reconciles to planned/available time from MES within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.otif.pct
  kpi_key: OTIF %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Delivery reliability measured by orders delivered on-time and in-full.
    definition: On-Time In-Full deliveries / Total Deliveries
    grain_scope: Order/shipment level; aggregated weekly/monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher OTIF indicates better delivery reliability; low values reflect service and execution issues.
  technical:
    dax_name: OTIF %
    depends_on_measures:
    - OTIF %
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Finance
    data_owner: Supply Chain BI
    steward: Inventory Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory days reconcile to inventory and COGS within +/- 1 day
    - 'Bounded: DSO/DIO/DPO derived days must be >= 0'
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: ops.working_capital.ccc.days
  kpi_key: Cash Conversion Cycle (Days)
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Combines receivables, inventory, and payables days to show cash efficiency.
    definition: DSO + DIO - DPO.
    grain_scope: Company / region level.
    unit_format: days
    interpretation: Lower CCC means faster cash conversion and lower working capital.
  technical:
    dax_name: Cash Conversion Cycle (Days)
    depends_on_measures:
    - Cash Conversion Cycle (Days)
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Input metrics reconciled before aggregation
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026
  aliases:
  - fin.liquidity.cash_conversion_cycle_days

- kpi_id: ops.downtime.pct
  kpi_key: Downtime %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of planned production time lost to downtime.
    definition: Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; analyze downtime drivers and loss categories.
  technical:
    dax_name: Downtime %
    depends_on_measures:
    - Downtime %
    lineage:
    - fact_ops.Downtime Minutes
    - fact_ops.Planned Time Minutes
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Planned Time Minutes > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.downtime.unplanned.pct
  kpi_key: Unplanned Downtime %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  action_code_ref:
  - O-A2.1
  - O-A2.2
  calc_type: rate
  business:
    purpose: Measures unplanned downtime share of planned time.
    definition: Unplanned Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; track reliability and maintenance effectiveness.
  technical:
    dax_name: Unplanned Downtime %
    depends_on_measures:
    - Unplanned Downtime %
    lineage:
    - fact_ops.Planned Time Minutes
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Maintenance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Planned Time Minutes > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: inv.turnover
  kpi_key: Inventory Turnover
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  action_code_ref:
  - S-I1.2
  calc_type: ratio
  business:
    purpose: Measures how often inventory is sold and replaced.
    definition: COGS / Average Inventory.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: turns
    interpretation: Higher turnover indicates better inventory velocity; too high may risk stockouts.
  technical:
    dax_name: Inventory Turnover
    depends_on_measures:
    - Inventory Turnover
    lineage:
    - fact_cogs.COGS Amount
    - fact_inventory.Average Inventory Amount
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - COGS and inventory reconciled to ledger
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  aliases:
  - ops.inventory.turnover

- kpi_id: plan.forecast.mape.pct
  kpi_key: Forecast MAPE %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  action_code_ref:
  - S-F3.2
  calc_type: rate
  business:
    purpose: Measures mean absolute percentage error in forecast.
    definition: Mean(|Forecast - Actual| / Actual).
    grain_scope: SKU/week; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high MAPE indicates unstable demand or poor model fit.
  technical:
    dax_name: Forecast MAPE %
    depends_on_measures:
    - MAPE %
    lineage:
    - fact_forecast.Forecast Units
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Review outliers for promotions or anomalies
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: supply.in_full.pct
  kpi_key: In-Full %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  action_code_ref:
  - S-R2.1
  - S-R2.3
  calc_type: rate
  business:
    purpose: Measures share of deliveries with complete quantities.
    definition: In-Full Deliveries / Total Deliveries.
    grain_scope: Delivery/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low values indicate allocation or stock issues.
  technical:
    dax_name: In-Full %
    depends_on_measures:
    - In-Full %
    lineage:
    - fact_fulfillment.In-Full Flag
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Deliveries > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: enterprise.action_outcome_rate.pct
  kpi_key: Action Outcome Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - XD-003
  action_code_ref:
  - X-E3.3
  calc_type: rate
  business:
    purpose: Measures share of actions that achieved the intended outcome.
    definition: Successful Actions / Routed Actions.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better execution effectiveness.
  technical:
    dax_name: Action Outcome Rate %
    depends_on_measures:
    - Action Outcome Rate %
    lineage: []
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: enterprise.action_routed.count
  kpi_key: Actions Routed Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Governance
  domain_tag:
  - Governance
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: count
  business:
    purpose: Counts action codes routed for execution.
    definition: Count of routed action instances in the period.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: count
    interpretation: Higher counts indicate more routed actions.
  technical:
    dax_name: Actions Routed Count
    depends_on_measures:
    - Actions Routed Count
    lineage: []
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: sales.price.realization_pct
  kpi_key: Price Realization %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-004
  action_code_ref:
  - C-M2.1
  calc_type: rate
  business:
    purpose: Shows how much of list price is realized after discounts.
    definition: Net Price Amount / List Price Amount.
    grain_scope: Invoice line aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Values below 100% indicate discounting; values above 100% indicate uplift vs list price.
  technical:
    dax_name: Price Realization %
    depends_on_measures:
    - Price Realization %
    lineage:
    - fact_sales.List Price Amount
    - fact_sales.Net Price Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Pricing Team
    steward: Pricing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Bounds [0%; 150%]
    - List price source reconciled to price books
    version: v1.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.pvm.mix_effect.amount
  kpi_key: Mix Effect Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-M2.2
  calc_type: amount
  business:
    purpose: Captures the residual effect from changes in product, channel, or region mix.
    definition: Total variance - Price Effect - Volume Effect.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Explains whether composition shifts drive positive or negative outcomes.
  technical:
    dax_name: Mix Effect Amount
    depends_on_measures:
    - Mix Effect Amount
    lineage: []
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Price + Volume + Mix reconcile to total variance
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: sales.net_sales.amount
  kpi_key: Net Sales Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-S1.1
  - C-S1.2
  calc_type: amount
  business:
    purpose: Total invoiced revenue net of discounts and returns.
    definition: Sum of all invoice line amounts net of VAT and returns.
    grain_scope: Invoice line.
    unit_format: EUR (2 decimals)
    interpretation: Represents total top-line sales.
  technical:
    dax_name: Net Sales Amount
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules: []
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.net_sales.delta_pct.ly
  kpi_key: Delta% Net Sales
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - XD-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Relative variance of Net Sales vs Last Year.
    definition: (Net Sales - LY) / LY
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Shows growth rate vs prior year.
  technical:
    dax_name: Delta% Net Sales
    depends_on_measures:
    - Net Sales Delta % vs LY
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to Net Sales and LY revenue within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  aliases:
  - Delta% Net Sales

- kpi_id: sales.net_sales.delta_pct.plan
  kpi_key: Net Sales % vs Plan
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-S1.2
  calc_type: rate
  business:
    purpose: Relative variance of Net Sales vs Plan.
    definition: (Net Sales Amount - Plan Sales Amount) / Plan Sales Amount
    grain_scope: Aggregated to reporting period.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate outperformance vs plan; negative values indicate shortfall.
  technical:
    dax_name: Net Sales % vs Plan
    depends_on_measures:
    - Net Sales % vs Plan
    lineage:
    - fact_sales.Plan Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to Net Sales and Plan revenue within +/- 0.1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.pvm.price_effect.amount
  kpi_key: Price Effect Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-004
  action_code_ref:
  - C-S1.1
  calc_type: amount
  business:
    purpose: Quantifies the pure price impact in the PVM bridge.
    definition: (Actual Price - Plan Price) x Actual Quantity.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Positive values indicate price gains; negative values represent price pressure.
  technical:
    dax_name: Price Effect Amount
    depends_on_measures:
    - Price Effect Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Plan Quantity
    - fact_sales.Plan Sales Amount
    - fact_sales.Quantity
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan price locked before period
    - Exclude items without plan price
    version: v1.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.pvm.volume_effect.amount
  kpi_key: Volume Effect Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Measures the variance caused purely by quantity changes at plan price.
    definition: (Actual Quantity - Plan Quantity) x Plan Price.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: EUR (2 decimals)
    interpretation: Positive values indicate higher volume than plan; negative values indicate volume shortfalls.
  technical:
    dax_name: Volume Effect Amount
    depends_on_measures:
    - Volume Effect Amount
    lineage:
    - fact_sales.Plan Quantity
    - fact_sales.Plan Sales Amount
    - fact_sales.Quantity
  governance:
    business_owner: Head of Sales Controlling
    data_owner: BI Engineering
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan quantity frozen
    - Exclude negative plan quantities
    version: v1.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.units
  kpi_key: Sales Units
  kpi_type: quantity
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - OPS-003
  - SCM-001
  - SCM-003
  action_code_ref:
  - O-Q3.5
  - S-F3.1
  - S-F3.2
  - S-I1.1
  - S-I1.2
  - S-I1.3
  - S-I1.5
  calc_type: count
  business:
    purpose: Measures sold units volume in the period.
    definition: Sum of sold units across transactions.
    grain_scope: Transaction line; aggregated by period and segment.
    unit_format: units
    interpretation: Higher values indicate higher volume sold.
  technical:
    dax_name: Sales Units
    depends_on_measures:
    - Sales Units
    lineage:
    - fact_sales.Sales Units
  governance:
    business_owner: Head of Sales
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: people.digital_adoption.pct
  kpi_key: Digital Adoption Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Innovation & People
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Measure how much of all eligible process transactions are executed via digital tools instead of manual channels.
    definition: Digital Transactions Count / Total Transactions Count for eligible processes.
    grain_scope: Process area / org; aggregated monthly or quarterly.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate greater adoption of digital processes; low values show manual work and automation potential.
  technical:
    dax_name: Digital Adoption Rate %
    depends_on_measures:
    - Digital Adoption %
    lineage:
    - fact_hr.Headcount
    - fact_it.Digital Users
  governance:
    business_owner: Head of Digital Transformation
    data_owner: Corporate BI
    steward: Digital Adoption Analyst
    review_cycle: quarterly
    validation_process: comparison with process mining and application telemetry
    qa_rules:
    - Eligible processes flagged correctly; adoption bounded between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: people.attrition_risk.pct
  kpi_key: Attrition Risk %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: governance
  domain_tag:
  - Human Resources
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Monitor risk of employee attrition across key roles and segments.
    definition: Probability of attrition for the selected population in the period.
    grain_scope: Org/role/segment; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher values signal retention risk and require targeted actions.
  technical:
    dax_name: Attrition Risk %
    depends_on_measures:
    - Attrition Risk %
    lineage: []
    business_owner: Head of HR
    data_owner: People Analytics
    steward: HR Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Attrition risk bounded between 0 % and 100 %
    - Headcount > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: wc.dso.days
  kpi_key: DSO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.2
  calc_type: amount
  business:
    purpose: Measures days sales outstanding for receivables.
    definition: Receivables / (Net Sales / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower is better; rising DSO indicates collection issues.
  technical:
    dax_name: DSO Days
    depends_on_measures:
    - DSO Days
    lineage:
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Net Sales > 0
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: wc.dio.days
  kpi_key: DIO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.3
  calc_type: amount
  business:
    purpose: Measures days inventory outstanding.
    definition: Inventory / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower is better; high DIO increases cash tied up in stock.
  technical:
    dax_name: DIO Days
    depends_on_measures:
    - DIO Days
    lineage: []
  governance:
    business_owner: Head of Treasury / Supply Chain Finance
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - COGS > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: wc.dpo.days
  kpi_key: DPO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.4
  calc_type: amount
  business:
    purpose: Measures days payables outstanding.
    definition: Payables / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Higher values improve cash but may impact supplier terms.
  technical:
    dax_name: DPO Days
    depends_on_measures:
    - DPO Days
    lineage: []
  governance:
    business_owner: Head of Treasury / Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - COGS > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: wc.ccc.days
  kpi_key: CCC Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.1
  calc_type: amount
  business:
    purpose: Measures cash conversion cycle length.
    definition: DSO + DIO - DPO.
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower values indicate faster cash recovery.
  technical:
    dax_name: CCC Days
    depends_on_measures:
    - CCC Days
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - DSO, DIO, DPO available for period
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: fin.cash.balance
  kpi_key: Cash Balance
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.1
  - F-C1.2
  calc_type: amount
  business:
    purpose: Tracks cash and cash equivalents at period end.
    definition: Cash and cash equivalents balance.
    grain_scope: Company/segment; monthly close.
    unit_format: EUR (2 decimals)
    interpretation: Higher balance improves liquidity buffer; consider seasonality and debt strategy.
  technical:
    dax_name: Cash Balance
    depends_on_measures:
    - Cash Balance
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Management Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to balance sheet cash accounts within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: fin.cash.ocf
  kpi_key: Operating Cash Flow
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.2
  - F-C1.3
  - F-C1.4
  calc_type: amount
  business:
    purpose: Measures cash generated by operating activities.
    definition: Net cash flows from operations for the period.
    grain_scope: Company/segment; monthly close.
    unit_format: EUR (2 decimals)
    interpretation: Positive values improve liquidity; negative values require investigation.
  technical:
    dax_name: Operating Cash Flow
    depends_on_measures:
    - Operating Cash Flow
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Flow Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Reconciles to cashflow statement within +/- 1 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026
  aliases:
  - fin.liquidity.operating_cash_flow

- kpi_id: fin.cash.vs_plan.pct
  kpi_key: Cash vs Plan %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.1
  calc_type: rate
  business:
    purpose: Measures deviation of cash balance versus plan.
    definition: (Cash Balance - Cash Plan) / Cash Plan.
    grain_scope: Company/segment; monthly close.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate higher cash than planned.
  technical:
    dax_name: Cash vs Plan %
    depends_on_measures:
    - Cash vs Plan %
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Flow Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan Amount > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: margin.gm.pct
  kpi_key: Gross Margin % (Operational)
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  - XD-003
  action_code_ref:
  - C-M2.1
  - C-M2.2
  - C-S1.1
  calc_type: ratio
  business:
    purpose: Provide the Gross Margin % used in commercial and management reporting at the same granularity as Net Sales.
    definition: (Net Sales Amount - COGS Amount) / Net Sales Amount
    grain_scope: Invoice line aggregated to reporting period, org, customer or product segments.
    unit_format: '% (1 decimal)'
    interpretation: Values above 0 % indicate positive gross profit; trend over time shows structural profitability changes.
  technical:
    dax_name: Gross Margin %
    depends_on_measures:
    - Gross Margin %
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to strategic Gross Margin % within +/- 0.1 pp for the same slice
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.promo.roi.pct
  kpi_key: Promo ROI %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: ratio
  business:
    purpose: Measures profitability of promotions relative to spend.
    definition: (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount
    grain_scope: Promo campaign / product / period.
    unit_format: '% (1 decimal)'
    interpretation: Values > 0 indicate promotions adding value.
  technical:
    dax_name: Promo ROI %
    depends_on_measures:
    - Promotion ROI %
    lineage: []
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Promo cost > 0 required
    - Variance vs finance ROI < 2 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.82
    last_review: 23.01.2026

- kpi_id: margin.promo.gm.pct
  kpi_key: GM % During Promo
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: ratio
  business:
    purpose: Gross margin rate during promo periods.
    definition: (Promo NS - Promo COGS) / Promo NS
    grain_scope: Promo period/product
    unit_format: '% (1 decimal)'
    interpretation: Profitability of promotions.
  technical:
    dax_name: GM % During Promo
    depends_on_measures:
    - Promo Gross Margin %
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
    - fact_sales.Promo Flag
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Promo mapping consistent with finance
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: cost.cogs_per_unit.amount
  kpi_key: COGS per Unit
  kpi_type: rate
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Shows unit cost level relative to sold volume.
    definition: COGS Amount / Units Sold.
    grain_scope: Product / period.
    unit_format: EUR per unit
    interpretation: Lower is better; rising unit cost erodes margin.
  technical:
    dax_name: COGS per Unit
    depends_on_measures:
    - COGS per Unit
    lineage:
    - fact_sales.Quantity
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Units Sold > 0
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.promo.cannibalization.pct
  kpi_key: Cannibalization %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-004
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of promo uplift offset by decline in non-promoted sales.
    definition: Cannibalized Sales / Promo Uplift Sales.
    grain_scope: Promo campaign / product / period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high cannibalization reduces net gain.
  technical:
    dax_name: Cannibalization %
    depends_on_measures:
    - Cannibalization %
    lineage:
    - fact_promo.Baseline Non-Promo Sales Amount
    - fact_sales.Net Sales Amount
    - fact_sales.Promo Flag
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Promo uplift > 0 for ratio
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: cost.material.pct
  kpi_key: Material Cost %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.2
  calc_type: rate
  business:
    purpose: Shows material cost share of net sales.
    definition: Material Cost Amount / Net Sales Amount.
    grain_scope: Company/segment; monthly close.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; increases indicate supplier or price pressure.
  technical:
    dax_name: Material Cost %
    depends_on_measures:
    - Material Cost %
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: cost.opex.vs_plan.pct
  kpi_key: OpEx vs Plan %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.4
  calc_type: rate
  business:
    purpose: Measures OpEx variance versus plan.
    definition: (OpEx Amount - OpEx Plan Amount) / OpEx Plan Amount.
    grain_scope: Company/segment; monthly close.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate overspend; negative values indicate savings.
  technical:
    dax_name: OpEx vs Plan %
    depends_on_measures:
    - OpEx vs Plan %
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Plan Amount > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: cost.unit.amount
  kpi_key: Unit Cost Amount
  kpi_type: rate
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.1
  - F-K2.2
  - F-K2.3
  - F-K2.4
  calc_type: ratio
  business:
    purpose: Measures total cost per unit produced or sold.
    definition: Total Cost Amount / Units Produced or Sold.
    grain_scope: Product / period.
    unit_format: EUR per unit
    interpretation: Lower is better; used to track cost efficiency.
  technical:
    dax_name: Unit Cost Amount
    depends_on_measures:
    - Unit Cost Amount
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Units > 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: profit.gross_margin
  kpi_key: Gross Margin %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Measures gross margin relative to net sales.
    definition: (Net Sales Amount - COGS Amount) / Net Sales Amount
    grain_scope: Invoice line aggregated to Org, Product, Date.
    unit_format: '% (1 decimal)'
    interpretation: Core profitability metric showing sales efficiency vs cost.
  technical:
    dax_name: Gross Margin %
    depends_on_measures:
    - Gross Margin %
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Value in [-100%; 100%]
    - Reconcile with P&L Gross Margin +/-0.5 pp
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: margin.gm.amount
  kpi_key: Gross Margin Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-M2.1
  - C-M2.2
  calc_type: amount
  business:
    purpose: Absolute gross margin in currency.
    definition: Net Sales Amount - COGS Amount
    grain_scope: Aggregated from invoice_line to reporting period.
    unit_format: EUR (2 decimals)
    interpretation: Explains profitability magnitude before OpEx.
  technical:
    dax_name: Gross Margin Amount
    depends_on_measures:
    - Gross Margin Amount
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconcile with P&L GM within +/-0.5%
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  aliases:
  - hr.gm.amount

- kpi_id: sales.promo.incremental.amount
  kpi_key: Incremental Sales Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  - COM-003
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: amount
  business:
    purpose: Additional sales due to promotion.
    definition: Promo Sales Amount - Baseline Sales Amount
    grain_scope: Promo period/product
    unit_format: EUR (2 decimals)
    interpretation: Input to promo ROI.
  technical:
    dax_name: Incremental Sales Amount
    depends_on_measures:
    - Incremental Sales Amount
    lineage:
    - fact_promo.Baseline Sales Amount
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Baseline method documented; overlap handling
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: margin.cogs.pct
  kpi_key: COGS % of Sales
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.1
  calc_type: rate
  business:
    purpose: Shows cost share relative to net sales.
    definition: COGS Amount / Net Sales Amount.
    grain_scope: Invoice line aggregated to period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; complements gross margin %.
  technical:
    dax_name: COGS % of Sales
    depends_on_measures:
    - COGS % of Sales
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: margin.gm.vs_plan.pct
  kpi_key: Gross Margin % vs Plan
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures gross margin rate variance versus plan.
    definition: (Gross Margin % - Plan Gross Margin %) / Plan Gross Margin %.
    grain_scope: Company/segment; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Positive values indicate better-than-plan margin.
  technical:
    dax_name: Gross Margin % vs Plan
    depends_on_measures:
    - Gross Margin % vs Plan
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Plan GM % available for reported period
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: cost.base_volume.amount
  kpi_key: Cost Base Volume Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.1
  - F-K2.2
  calc_type: amount
  business:
    purpose: Baseline cost volume used for variance analysis.
    definition: Baseline amount of cost volume for the selected period.
    grain_scope: Cost center or product; aggregated by period.
    unit_format: EUR (2 decimals)
    interpretation: Provides a stable base for cost variance comparisons.
  technical:
    dax_name: Cost Base Volume Amount
    depends_on_measures:
    - Cost Base Volume Amount
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Cost Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: cost.opex.base.amount
  kpi_key: Opex Base Amount
  kpi_type: amount
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-002
  action_code_ref:
  - F-K2.4
  calc_type: amount
  business:
    purpose: Baseline operating expense amount for variance tracking.
    definition: Baseline operating expense amount for the selected period.
    grain_scope: Cost center; aggregated by period.
    unit_format: EUR (2 decimals)
    interpretation: Used to compare actual Opex against the base.
  technical:
    dax_name: Opex Base Amount
    depends_on_measures:
    - Opex Base Amount
    lineage: []
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Cost Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: enterprise.value_at_risk.index
  kpi_key: Enterprise Value-at-Risk Index
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Risk
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - XD-003
  action_code_ref:
  - X-E3.2
  calc_type: ratio
  business:
    purpose: Aggregates downside risk across domains into a single index.
    definition: Weighted index of normalized domain risk signals.
    grain_scope: Entity or business unit; aggregated by period.
    unit_format: index
    interpretation: Higher index indicates higher enterprise risk exposure.
  technical:
    dax_name: Enterprise Value-at-Risk Index
    depends_on_measures:
    - Enterprise Value-at-Risk Index
    lineage: []
  governance:
    business_owner: Chief Risk Officer
    data_owner: Enterprise Risk
    steward: Risk Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: scm.supplier_risk.score
  kpi_key: Supplier Risk Score
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Risk
  domain_tag:
  - Supply Chain
  use_case_ref:
  - FIN-001
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Rates suppliers based on risk indicators.
    definition: Composite risk score derived from supplier risk factors.
    grain_scope: Supplier; aggregated by period.
    unit_format: score
    interpretation: Higher scores indicate higher supplier risk.
  technical:
    dax_name: Supplier Risk Score
    depends_on_measures:
    - Supplier Risk Score
    lineage: []
  governance:
    business_owner: Head of Procurement
    data_owner: Supply Chain BI
    steward: Supplier Risk Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: svc.sla.attainment.pct
  kpi_key: SLA Attainment %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  - XD-002
  - XD-003
  action_code_ref:
  - X-S1.1
  - X-S1.2
  - X-S1.4
  calc_type: ratio
  business:
    purpose: Measures how many cases meet the committed SLA.
    definition: Cases with SLA Met Flag = 1 divided by total cases in period.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; interpret jointly with backlog and escalation %.
  technical:
    dax_name: SLA Attainment %
    depends_on_measures:
    - SLA Attainment %
    lineage:
    - fact_cases.SLA Met Flag
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Ops Analyst
    review_cycle: monthly
    validation_process: automated + spot checks
    qa_rules:
    - Total cases > 0 for reported slice
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.fcr.pct
  kpi_key: First Contact Resolution %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  action_code_ref:
  - X-S1.3
  calc_type: ratio
  business:
    purpose: Shows the share of cases solved on first contact.
    definition: Cases with FCR Flag = 1 divided by total cases.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; keep in balance with AHT and escalation %.
  technical:
    dax_name: FCR %
    depends_on_measures:
    - FCR %
    lineage:
    - fact_cases.FCR Flag
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Ops Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Total cases > 0; reopened cases handled per policy
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.aht.minutes
  kpi_key: Average Handling Time (minutes)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  action_code_ref:
  - X-S1.4
  calc_type: ratio
  business:
    purpose: Measures average time to handle a contact.
    definition: Total handle time divided by number of cases/contacts.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: 'minutes (1 decimal)'
    interpretation: Lower is better, but balance with FCR and NPS.
  technical:
    dax_name: AHT Minutes
    depends_on_measures:
    - AHT Minutes
    lineage:
    - fact_cases.Handle Time Minutes
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Ops Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Handle time unit consistent; exclude outliers per policy
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.backlog.count
  kpi_key: Backlog Count
  kpi_type: count
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  - XD-002
  action_code_ref:
  - X-S1.1
  - X-S1.2
  calc_type: count
  business:
    purpose: Quantifies unresolved work in queue.
    definition: Count of open cases at period end.
    grain_scope: queue_day; aggregated to month by Org/Channel/Queue.
    unit_format: 'count'
    interpretation: Lower is better; assess with SLA attainment and staffing KPIs.
  technical:
    dax_name: Backlog Count
    depends_on_measures:
    - Backlog Count
    lineage:
    - fact_cases.Backlog Flag
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Ops Analyst
    review_cycle: weekly
    validation_process: automated + manual reconciliation
    qa_rules:
    - Status logic consistent; one row per case
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.nps.index
  kpi_key: NPS Index
  kpi_type: index
  kpi_role: strategic
  impact_dimension: Experience
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Measures customer advocacy and experience quality.
    definition: %Promoters minus %Detractors from NPS survey.
    grain_scope: survey_event aggregated to month by Org/Channel.
    unit_format: 'index'
    interpretation: Higher is better; explain shifts with FCR, AHT, escalation %.
  technical:
    dax_name: NPS Index
    depends_on_measures:
    - NPS Index
    lineage:
    - fact_nps.NPS Score
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: CX Analyst
    review_cycle: monthly
    validation_process: survey QA + automation
    qa_rules:
    - Score in [-100;100]; promoter/detractor thresholds documented
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.escalation.pct
  kpi_key: Escalation %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  action_code_ref:
  - X-S1.1
  - X-S1.3
  calc_type: ratio
  business:
    purpose: Measures frequency of escalated cases.
    definition: Escalated cases divided by total cases.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; balance with FCR and SLA.
  technical:
    dax_name: Escalation %
    depends_on_measures:
    - Escalation %
    lineage:
    - fact_cases.Escalation Flag
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Ops Analyst
    review_cycle: monthly
    validation_process: automated
    qa_rules:
    - Total cases > 0; escalation definition consistent
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: res.utilization.pct
  kpi_key: Utilization %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
  action_code_ref:
  - X-R2.1
  - X-R2.2
  - X-R2.3
  - X-R2.4
  calc_type: ratio
  business:
    purpose: Measures productive time versus paid time for agents.
    definition: Productive time divided by paid time.
    grain_scope: agent_day or queue_day; aggregated to week/month.
    unit_format: '% (1 decimal)'
    interpretation: Typical healthy band 75?85%; balance with SLA/NPS.
  technical:
    dax_name: Utilization %
    depends_on_measures:
    - Utilization %
    lineage:
    - fact_wfm.Paid Time Minutes
    - fact_wfm.Work Time Minutes
  governance:
    business_owner: Head of Service
    data_owner: WFM Analytics
    steward: WFM Analyst
    review_cycle: weekly
    validation_process: automated
    qa_rules:
    - Paid Time > 0; time zones consistent
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: res.occupancy.pct
  kpi_key: Occupancy %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
  action_code_ref:
  - X-R2.1
  - X-R2.2
  calc_type: ratio
  business:
    purpose: Measures active vs idle share of time.
    definition: (Talk + Wrap) / (Talk + Wrap + Idle).
    grain_scope: agent_day or queue_day; aggregated to week/month.
    unit_format: '% (1 decimal)'
    interpretation: Balanced occupancy supports SLA and quality.
  technical:
    dax_name: Occupancy %
    depends_on_measures:
    - Occupancy %
    lineage:
    - fact_wfm.Idle Time Minutes
    - fact_wfm.Talk Time Minutes
    - fact_wfm.Wrap Time Minutes
  governance:
    business_owner: Head of Service
    data_owner: WFM Analytics
    steward: WFM Analyst
    review_cycle: weekly
    validation_process: automated
    qa_rules:
    - Time totals align; no double counting
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: res.overtime.pct
  kpi_key: Overtime %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
  action_code_ref:
  - X-R2.1
  - X-R2.4
  calc_type: ratio
  business:
    purpose: Shows overtime share of total hours.
    definition: Overtime hours divided by total hours.
    grain_scope: agent_day; aggregated to week/month.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; monitor sustainability and cost.
  technical:
    dax_name: Overtime %
    depends_on_measures:
    - Overtime %
    lineage:
    - fact_wfm.Overtime Minutes
    - fact_wfm.Paid Time Minutes
  governance:
    business_owner: Head of Service
    data_owner: WFM Analytics
    steward: WFM Analyst
    review_cycle: weekly
    validation_process: automated
    qa_rules:
    - Total Hours > 0
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: res.shrinkage.pct
  kpi_key: Shrinkage %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
  action_code_ref:
  - X-R2.3
  calc_type: ratio
  business:
    purpose: Measures non-productive share of paid time.
    definition: Non-productive time divided by paid time.
    grain_scope: agent_day; aggregated to week/month.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; compare vs plan.
  technical:
    dax_name: Shrinkage %
    depends_on_measures:
    - Shrinkage %
    lineage:
    - fact_wfm.Paid Time Minutes
    - fact_wfm.Shrinkage Minutes
  governance:
    business_owner: Head of Service
    data_owner: WFM Analytics
    steward: WFM Analyst
    review_cycle: weekly
    validation_process: automated
    qa_rules:
    - Paid Time > 0; components of shrinkage defined
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.tickets.created.count
  kpi_key: Tickets Created Count
  kpi_type: activity
  kpi_role: supporting
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  - XD-002
  action_code_ref:
  - X-R2.1
  - X-R2.2
  - X-R2.3
  - X-R2.4
  - X-S1.1
  - X-S1.2
  calc_type: count
  business:
    purpose: Counts customer service tickets created in the period.
    definition: Count of newly created service tickets.
    grain_scope: Ticket; aggregated by period and channel.
    unit_format: count
    interpretation: Higher counts indicate higher inbound demand.
  technical:
    dax_name: Tickets Created Count
    depends_on_measures:
    - Tickets Created Count
    lineage: []
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Analyst
    review_cycle: weekly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026

- kpi_id: svc.tickets.closed.count
  kpi_key: Tickets Closed Count
  kpi_type: activity
  kpi_role: supporting
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  action_code_ref:
  - X-S1.3
  - X-S1.4
  calc_type: count
  business:
    purpose: Counts customer service tickets closed in the period.
    definition: Count of closed service tickets.
    grain_scope: Ticket; aggregated by period and channel.
    unit_format: count
    interpretation: Higher counts indicate higher resolution throughput.
  technical:
    dax_name: Tickets Closed Count
    depends_on_measures:
    - Tickets Closed Count
    lineage: []
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Analyst
    review_cycle: weekly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: 23.01.2026
```
