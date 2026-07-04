# KPI Catalog

> **Generated view.** The source of truth is the per-KPI files under [`kpis/`](kpis/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/kpi_catalog_files.py render`.

---

Schema: see [core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md](../templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md)

## KPIs

```yaml
- kpi_id: crm.clv.amount
  kpi_key: CLV (Customer Lifetime Value)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  - XD-003
  action_code_ref:
  - C-C3.1
  calc_type: amount
  business:
    purpose: Estimate long-term value of a customer to prioritize retention, acquisition, and service investments.
    definition: Sum of expected future gross margin per customer discounted over the chosen time horizon.
    grain_scope: Customer level; calculated on cohort or segment basis.
    unit_format: EUR (2 decimals)
    interpretation: Higher CLV indicates more valuable segments; compare against acquisition cost and churn risk.
  technical:
    measure_name: CLV
    description: Estimate long-term value of a customer to prioritize retention, acquisition, and service investments.
    depends_on_measures: []
    lineage:
    - fact_customer_value.CustomerKey
    - fact_customer_value.CLV Amount
    calculation:
      op: avgx_over_key
      key_column: CustomerKey
      value:
        column: CLV Amount
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  - Operations
  use_case_ref:
  - COM-003
  - XD-003
  action_code_ref:
  - C-C3.1
  calc_type: amount
  business:
    purpose: Quantify revenue exposure proportional to the customer attrition rate.
    definition: Net Sales Amount × (Churned Customers / Active Customers).
    grain_scope: Customer/segment; monthly.
    unit_format: EUR (0 decimals)
    interpretation: Higher values indicate more revenue at risk from customer churn; prioritize retention actions on high-value at-risk segments.
  technical:
    measure_name: Revenue at Risk Amount
    description: Net Sales Amount weighted by the churned-to-active customer ratio.
    depends_on_measures:
    - sales.net_sales.amount
    - crm.churned_customers.count
    - crm.active_customers.count
    lineage:
    - fact_sales.Net Sales Amount
    - fact_customer_events.CustomerKey
    - fact_customer_events.Churn Flag
    - fact_customer_events.Activity Flag
    calculation:
      op: mul
      terms:
      - kpi: sales.net_sales.amount
      - calc:
          op: ratio
          numerator:
            calc:
              op: distinctcount
              column: CustomerKey
              filters:
              - column: Churn Flag
                equals: true
          denominator:
            calc:
              op: distinctcount
              column: CustomerKey
              filters:
              - column: Activity Flag
                equals: true
  governance:
    business_owner: Head of Operations
    data_owner: Ops BI
    steward: Operations Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - At-risk revenue reconciles to Net Sales weighted by the churned/active customer ratio within +/- 1 %
    version: v1.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 20.04.2026

- kpi_id: crm.complaint.count
  kpi_key: Complaint Count
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref:
  - C-C3.2
  calc_type: count
  business:
    purpose: Provide the absolute number of logged complaints.
    definition: Count of complaint records in the complaint/service system.
    grain_scope: Complaint / ticket; aggregated to org / channel / product / period.
    unit_format: count
    interpretation: Higher values indicate more issues; interpret with Complaint Rate % to normalize by volume.
  technical:
    measure_name: Complaint Count
    description: Count of logged customer complaints
    depends_on_measures: []
    lineage:
    - fact_complaints.Complaint Count
    calculation:
      op: sum
      column: Complaint Count
  governance:
    business_owner: Head of Customer Service
    data_owner: Service BI
    steward: Service Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Complaints reconciled to service desk reports
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: crm.retention.pct
  kpi_key: Customer Retention %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref:
  - C-C3.1
  calc_type: rate
  business:
    purpose: Measure the share of customers that remain active from one period to the next, as a core loyalty KPI.
    definition: (Active Customers at end of period) / (Active Customers at start of period).
    grain_scope: Customer / segment / org; monthly or quarterly.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher retention indicates better loyalty and relationship quality; interpret jointly with churn and CLV.
  technical:
    measure_name: Customer Retention %
    description: Measure the share of customers that remain active from one period to the next, as a core loyalty KPI.
    depends_on_measures: []
    lineage:
    - fact_customer_events.CustomerKey
    - fact_customer_events.Activity Flag
    - fact_customer_events.Churn Flag
    calculation:
      op: ratio
      numerator:
        calc:
          op: distinctcount
          column: CustomerKey
          filters:
          - column: Activity Flag
            equals: true
          - column: Churn Flag
            equals: false
      denominator:
        calc:
          op: distinctcount
          column: CustomerKey
          filters:
          - column: Activity Flag
            equals: true
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
  synonyms:
  - Net Promoter Score
  - Promoter Score
  - Weiterempfehlungsrate
  - NPS
  example_question: Which segments are driving the change in NPS this quarter?
  kpi_key: Net Promoter Score (NPS)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref:
  - C-C3.2
  calc_type: rate
  business:
    purpose: Measures customer advocacy and likelihood to recommend.
    definition: (%Promoters - %Detractors) from survey responses in the period.
    grain_scope: Survey response aggregated by period, segment, or region.
    unit_format: Index (-100 to 100)
    interpretation: '''>0 is positive, >50 strong advocacy; track trend and segment gaps.'''
  technical:
    measure_name: NPS Index
    description: Measures customer advocacy and likelihood to recommend.
    depends_on_measures: []
    lineage:
    - fact_nps.NPS Score
    calculation:
      op: round
      digits: 0
      value:
        calc:
          op: ratio
          scale: 100
          numerator:
            calc:
              op: delta
              minuend:
                calc:
                  op: count_threshold
                  column: NPS Score
                  comparator: '>='
                  value: 9
              subtrahend:
                calc:
                  op: count_threshold
                  column: NPS Score
                  comparator: <=
                  value: 6
          denominator:
            calc:
              op: count
              column: NPS Score
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
  kpi_type: diagnostic
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
    measure_name: Churned Customers
    description: Count customers that have stopped purchasing in the observation window as basis for churn calculations.
    depends_on_measures: []
    lineage:
    - fact_customer_events.CustomerKey
    - fact_customer_events.Churn Flag
    calculation:
      op: distinctcount
      column: CustomerKey
      filters:
      - column: Churn Flag
        equals: true
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
  kpi_type: diagnostic
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
    measure_name: Customer Lifetime Revenue Amount
    description: Sum of realized revenue across customer lifecycle
    depends_on_measures:
    - sales.net_sales.amount
    lineage:
    - fact_sales.CustomerKey
    calculation:
      op: sumx_over_key
      key_column: CustomerKey
      value:
        kpi: sales.net_sales.amount
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
    completeness_score: 1.0
    last_review: 27.01.2026

- kpi_id: crm.active_customers.count
  kpi_key: Active Customers
  kpi_type: diagnostic
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
    measure_name: Active Customers
    description: Number of unique active customers in the reporting period.
    depends_on_measures: []
    lineage:
    - fact_customer_events.CustomerKey
    - fact_customer_events.Activity Flag
    calculation:
      op: distinctcount
      column: CustomerKey
      filters:
      - column: Activity Flag
        equals: true
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
  synonyms:
  - Performance Rate
  - Speed Factor
  - Leistungsgrad
  - Leistung
  - Leistungsfaktor
  example_question: Where are speed losses hurting performance this week?
  kpi_key: Performance %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher performance indicates faster throughput; values above 100 % require validation of standard rates.
  technical:
    measure_name: Performance %
    description: Throughput speed versus theoretical maximum.
    depends_on_measures: []
    lineage:
    - fact_ops.Output Units
    - fact_ops.Run Time Minutes
    - fact_ops.Standard Rate Units Per Minute
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
  synonyms:
  - Quality Rate
  - Yield
  - Qualitätsgrad
  - Gutanteil
  - Qualitätsfaktor
  example_question: Which lines are below the quality target this month?
  kpi_key: Quality %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher quality means fewer defects; low values indicate scrap/rework issues.
  technical:
    measure_name: Quality %
    description: Yield of conforming units relative to total units produced.
    depends_on_measures: []
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values indicate better labor efficiency; validate against mix effects.
  technical:
    measure_name: Labor Productivity %
    description: Shows output efficiency relative to labor input.
    depends_on_measures: []
    lineage:
    - fact_output.Output Units
    - fact_labor.Labor Hours
    calculation:
      op: ratio
      numerator:
        column: Output Units
      denominator:
        column: Labor Hours
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
  synonyms:
  - Mean Time Between Failures
  - Reliability Interval
  - Mittlere Betriebsdauer zwischen Ausfällen
  - mittlere Zeit zwischen Ausfällen
  example_question: Which assets have the worst MTBF this quarter?
  kpi_key: MTBF (hours)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: MTBF (hours)
    description: Measures average operating time between failures.
    depends_on_measures:
    - ops.failure.count
    - ops.mttr.hours
    - ops.downtime.unplanned.pct
    - ops.pm_compliance.pct
    - ops.spare_parts.stockout.pct
    - ops.availability.pct
    lineage:
    - fact_ops.Run Time Minutes
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
  synonyms:
  - Mean Time To Repair
  - Mean Time To Restore
  - Mittlere Reparaturdauer
  - mittlere Wiederherstellungszeit
  example_question: Where is MTTR longest, and why?
  kpi_key: MTTR (hours)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: MTTR (hours)
    description: Measures average repair time after failures.
    depends_on_measures: []
    lineage:
    - fact_ops_failures.Repair Duration Hours
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; low compliance increases breakdown risk.
  technical:
    measure_name: PM Compliance %
    description: Tracks adherence to preventive maintenance plan.
    depends_on_measures: []
    lineage:
    - fact_maintenance.Order Type
    - fact_maintenance.Order Status
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; stockouts drive downtime and MTTR.
  technical:
    measure_name: Spare Parts Stockout %
    description: Measures stockout frequency for critical spare parts.
    depends_on_measures: []
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Throughput Units
    description: Measures total output volume in units.
    depends_on_measures: []
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
  synonyms:
  - First Pass Yield
  - First Time Yield
  - Erstausbeute
  - Gutausbeute im ersten Durchgang
  example_question: Which products have the lowest first pass yield?
  kpi_key: First Pass Yield %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; low FPY indicates process instability.
  technical:
    measure_name: First Pass Yield %
    description: Measures share of units produced without rework or scrap.
    depends_on_measures:
    - quality.scrap.pct
    - quality.rework.pct
    - quality.copq.amount
    - quality.complaint.pct
    - quality.defect_density
    lineage:
    - fact_quality.Good Units
    - fact_quality.Total Units
    calculation:
      op: ratio
      numerator:
        column: Good Units
      denominator:
        column: Total Units
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
  synonyms:
  - Scrap Ratio
  - Reject Rate
  - Waste Rate
  - Ausschussquote
  - Ausschussrate
  example_question: What is driving the scrap rate up in Fashion?
  kpi_key: Scrap Rate %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Quality
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; rising scrap increases cost and reduces yield.
  technical:
    measure_name: Scrap Rate %
    description: Measures share of units scrapped in production.
    depends_on_measures: []
    lineage:
    - fact_quality.Scrap Units
    - fact_quality.Total Units
    calculation:
      op: ratio
      numerator:
        column: Scrap Units
      denominator:
        column: Total Units
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; high rework impacts throughput and cost.
  technical:
    measure_name: Rework Rate %
    description: Measures share of units requiring rework.
    depends_on_measures: []
    lineage:
    - fact_quality.Rework Units
    - fact_quality.Total Units
    calculation:
      op: ratio
      numerator:
        column: Rework Units
      denominator:
        column: Total Units
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Cost of Poor Quality
    description: Captures financial impact of scrap, rework, and warranty/complaints.
    depends_on_measures: []
    lineage:
    - fact_quality_costs.COPQ Amount
    calculation:
      op: sum
      column: COPQ Amount
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; spikes indicate quality or service issues.
  technical:
    measure_name: Complaint Rate %
    description: Measures customer complaints relative to shipped units.
    depends_on_measures:
    - crm.complaint.count
    lineage:
    - fact_complaints.Complaint Count
    - fact_shipments.Shipped Units
    calculation:
      op: ratio
      numerator:
        column: Complaint Count
      denominator:
        column: Shipped Units
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Defect Density
    description: Measures defect count per 1,000 units produced.
    depends_on_measures: []
    lineage:
    - fact_quality.Defect Count
    - fact_quality.Total Units
    calculation:
      op: ratio
      numerator:
        column: Defect Count
      denominator:
        column: Total Units
      scale: 1000
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
  synonyms:
  - Days Inventory Outstanding
  - Days of Supply
  - Lagerreichweite
  - Bestandsreichweite
  example_question: Where is days-of-supply highest across the network?
  kpi_key: Days in Inventory
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    measure_name: Days in Inventory
    description: Measures inventory holding period in days.
    depends_on_measures:
    - inv.turnover
    - inv.stockout.pct
    - supply.otif.pct
    - inv.obsolete.pct
    - plan.forecast.accuracy.pct
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
  synonyms:
  - Out-of-Stock Rate
  - OOS
  - Fehlmengenquote
  - Fehlbestandsquote
  example_question: Which SKUs stock out most often?
  kpi_key: Stockout Rate %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; high stockout rate impacts service and revenue.
  technical:
    measure_name: Stockout Rate %
    description: Measures how often inventory is unavailable when demanded.
    depends_on_measures: []
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

- kpi_id: inv.excess_inventory.amount
  kpi_key: Excess Inventory Value
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Working Capital
  domain_tag:
  - Supply Chain
  - Finance
  use_case_ref:
  - SCM-001
  - FIN-001
  action_code_ref:
  - S-I1.1
  - S-I1.4
  calc_type: amount
  business:
    purpose: Measures the value of inventory exceeding forward demand cover.
    definition: Inventory value exceeding X months of forward demand (typically > 6 months of projected consumption). Primary working capital lock-up driver when DIO is high.
    grain_scope: SKU/location; aggregated to product category and plant monthly.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; excess inventory ties up working capital and increases obsolescence risk. Reduction directly improves DIO and cash conversion.
  technical:
    measure_name: Excess Inventory Amount
    description: Inventory value beyond coverage threshold.
    depends_on_measures:
    - inv.dio.days
    lineage:
    - fact_inventory.Stock Value
    - fact_demand_forecast.Monthly Demand Forecast
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Inventory Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Stock Value >= 0
    - Coverage threshold must be documented per product category
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 01.06.2026

- kpi_id: inv.obsolete.pct
  synonyms:
  - Dead Stock %
  - Obsolescence Rate
  - Obsoleszenzquote
  - Ladenhüter-Anteil
  example_question: How much inventory value is obsolete by category?
  kpi_key: Obsolete Inventory %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; high obsolescence indicates slow movement or aging.
  technical:
    measure_name: Obsolete Inventory %
    description: Measures share of inventory considered obsolete.
    depends_on_measures: []
    lineage:
    - fact_inventory.Obsolete Inventory Amount
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
  synonyms:
  - Demand Forecast Accuracy
  - Forecast Attainment
  - Prognosegenauigkeit
  - Vorhersagegenauigkeit
  example_question: Where is forecast accuracy weakest this cycle?
  kpi_key: Forecast Accuracy %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; low accuracy drives inventory and service issues.
  technical:
    measure_name: Forecast Accuracy %
    description: Measures how close forecasted demand is to actual demand.
    depends_on_measures:
    - plan.forecast.mape.pct
    - plan.forecast.bias.pct
    - plan.forecast.service_impact.pct
    - plan.replan.count
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
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026

- kpi_id: plan.forecast.bias.pct
  kpi_key: Forecast Bias %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Values near 0 are best; positive bias indicates over-forecasting.
  technical:
    measure_name: Forecast Bias %
    description: Measures systematic over- or under-forecasting.
    depends_on_measures: []
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
    - Bias bounded and reviewed for outliers
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026
  aliases:
  - sales.forecast.bias_pct

- kpi_id: plan.replan.count
  deprecated: true
  deprecation_reason: No active bracket/action-code references; targeted for removal in v1.1 (see extended_playbook.md)
  kpi_key: Re-Plan Count
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    measure_name: Re-Plan Count
    description: Counts number of replanning cycles in a period.
    depends_on_measures: []
    lineage:
    - fact_forecast.Forecast Version
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
  synonyms:
  - On Time In Full
  - Delivery Reliability
  - DIFOT
  - Liefertreue
  example_question: Which lanes are missing the OTIF target this month?
  kpi_key: OTIF %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; key service level indicator.
  technical:
    measure_name: OTIF %
    description: Measures share of orders delivered on time and in full.
    depends_on_measures:
    - supply.on_time.pct
    - supply.in_full.pct
    - supply.stockout_impact.pct
    lineage:
    - fact_fulfillment.OTIF Flag
    calculation:
      op: rate
      column: OTIF Flag
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
  synonyms:
  - On-Time Delivery
  - OTD
  - Termintreue
  - Liefertermintreue
  example_question: What is driving late deliveries on the DACH lanes?
  kpi_key: On-Time %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; analyze by carrier and lane.
  technical:
    measure_name: On-Time %
    description: Measures share of deliveries arriving on time.
    depends_on_measures: []
    lineage:
    - fact_fulfillment.On-Time Flag
    calculation:
      op: rate
      column: On-Time Flag
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; ties inventory and service performance.
  technical:
    measure_name: Stockout Impact %
    description: Measures lost demand share due to stockouts.
    depends_on_measures: []
    lineage:
    - fact_stockout.Lost Demand Units
    - fact_stockout.Demand Units
    calculation:
      op: ratio
      numerator:
        column: Lost Demand Units
      denominator:
        column: Demand Units
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    measure_name: Expedite Cost Amount
    description: Captures additional cost for expedited shipments.
    depends_on_measures: []
    lineage:
    - fact_fulfillment.Expedite Cost
    calculation:
      op: sum
      column: Expedite Cost
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    measure_name: Penalty Amount
    description: Captures penalties for service level breaches.
    depends_on_measures: []
    lineage:
    - fact_fulfillment.Penalty Amount
    calculation:
      op: sum
      column: Penalty Amount
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - SCM-003
  action_code_ref:
  - S-F3.3
  calc_type: rate
  business:
    purpose: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage (units-based demand forecast).
    definition: Service Impact % = Stockout Impact % x (Under-Forecast Lost Demand / Total Lost Demand). Under-forecast is defined as a negative forecast error below a configurable threshold; all inputs are unit-based (qty), not revenue.
    grain_scope: Calculated at location_sku_day or sku_week; reported at sku_month aggregated by Date, Org, Product.
    unit_format: '%'
    interpretation: Lower values are better; high impact indicates forecast under-coverage driving service loss.
  technical:
    measure_name: Service Impact %
    description: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage.
    depends_on_measures: []
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
  synonyms:
  - Overall Equipment Effectiveness
  - Equipment Effectiveness
  - Gesamtanlageneffektivität
  - GAE
  - Anlageneffektivität
  example_question: Which production lines have the lowest OEE this month?
  kpi_key: Overall Equipment Effectiveness (OEE) %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher OEE indicates better utilization; capped at 100 %.
  technical:
    measure_name: OEE %
    description: Measures manufacturing performance combining availability, performance, and quality.
    depends_on_measures:
    - ops.availability.pct
    - ops.performance.pct
    - ops.quality.pct
    lineage:
    - fact_ops.Run Time Minutes
    - fact_ops.Planned Time Minutes
    - fact_ops.Output Units
    - fact_ops.Good Units
    - fact_ops.Standard Rate Units Per Minute
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
  - Operations
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
    measure_name: Failure Count
    description: Counts equipment or process failures in the period.
    depends_on_measures: []
    lineage:
    - fact_ops_failures
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
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.inventory.value.amount
  kpi_key: Inventory Value Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Inventory Value Amount
    description: Tracks inventory value for maintenance-relevant items.
    depends_on_measures: []
    lineage:
    - fact_inventory.Average Inventory Amount
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.planned_output.units
  kpi_key: Planned Output Units
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Planned Output Units
    description: Captures planned production output volume.
    depends_on_measures: []
    lineage:
    - fact_ops.Planned Time Minutes
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Production Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.pm.task.count
  kpi_key: Preventive Maintenance Task Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Preventive Maintenance Task Count
    description: Counts preventive maintenance tasks executed or scheduled.
    depends_on_measures: []
    lineage:
    - fact_maintenance
  governance:
    business_owner: Head of Maintenance
    data_owner: Maintenance BI
    steward: Maintenance Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.production.volume
  kpi_key: Production Volume Units
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    measure_name: Production Volume Units
    description: Measures total produced volume in units.
    depends_on_measures: []
    lineage:
    - fact_ops.Output Units
    calculation:
      op: sum
      column: Output Units
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
  - Operations
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of defective units in production.
    definition: Defective Units / Total Produced Units.
    grain_scope: Line/shift; aggregated by period.
    unit_format: '''% (1 decimal)'''
    interpretation: Lower values indicate better quality.
  technical:
    measure_name: Quality Defect Rate %
    description: Measures share of defective units in production.
    depends_on_measures: []
    lineage:
    - fact_ops.Output Units
    - fact_quality.Defect Count
    calculation:
      op: ratio
      numerator:
        column: Defect Count
      denominator:
        column: Output Units
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
  - Operations
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
    measure_name: Safety Incident Count
    description: Counts safety incidents recorded in the period.
    depends_on_measures: []
    lineage:
    - fact_safety.Incident Count
  governance:
    business_owner: EHS Manager
    data_owner: EHS BI
    steward: Safety Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.service_level.pct
  kpi_key: Operations Service Level %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures on-time or in-full performance for operational delivery.
    definition: On-Time or In-Full Deliveries / Total Deliveries.
    grain_scope: Site/product; aggregated by period.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values indicate better service performance.
  technical:
    measure_name: Operations Service Level %
    description: Measures on-time or in-full performance for operational delivery.
    depends_on_measures: []
    lineage:
    - fact_fulfillment.OTIF Flag
    calculation:
      op: rate
      column: OTIF Flag
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: ops.yield.pct
  synonyms:
  - Process Yield
  - Throughput Yield
  - Ausbeute
  - Gutausbeute
  - Ausbeutegrad
  example_question: How has process yield trended since the line upgrade?
  kpi_key: Yield %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures ratio of good output to total input.
    definition: Good Units / Total Units Produced.
    grain_scope: Line/shift; aggregated by period.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher yield indicates better process efficiency.
  technical:
    measure_name: Yield %
    description: Measures ratio of good output to total input.
    depends_on_measures: []
    lineage:
    - fact_ops.Good Units
    - fact_ops.Output Units
    calculation:
      op: ratio
      numerator:
        column: Good Units
      denominator:
        column: Output Units
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
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Commercial
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
    measure_name: Order Lines Count
    description: Counts order lines processed in the period.
    depends_on_measures: []
    lineage:
    - fact_fulfillment
    calculation:
      op: count
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Order Management Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: plans.count
  kpi_key: Plans Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    measure_name: Plans Count
    description: Counts planning cycles or plan versions in the period.
    depends_on_measures: []
    lineage:
    - fact_forecast.Forecast Version
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: shipments.count
  kpi_key: Shipments Count
  kpi_type: diagnostic
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
    measure_name: Shipments Count
    description: Counts shipments executed in the period.
    depends_on_measures: []
    lineage:
    - fact_fulfillment
    calculation:
      op: count
  governance:
    business_owner: Head of Logistics
    data_owner: Logistics BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values indicate better service reliability.
  technical:
    measure_name: Supply Chain Service Level %
    description: Measures supply chain service level performance.
    depends_on_measures: []
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
  synonyms:
  - Availability Rate
  - Uptime
  - Verfügbarkeit
  - Anlagenverfügbarkeit
  - Verfügbarkeitsgrad
  example_question: What is dragging availability down on Line B?
  kpi_key: Availability %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher availability indicates less downtime; low values typically reflect maintenance or scheduling issues.
  technical:
    measure_name: Availability %
    description: Uptime share relative to planned production time.
    depends_on_measures: []
    lineage:
    - fact_ops.Run Time Minutes
    - fact_ops.Planned Time Minutes
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
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
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Operational Efficiency
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Delivery reliability measured by orders delivered on-time and in-full.
    definition: On-Time In-Full deliveries / Total Deliveries
    grain_scope: Order/shipment level; aggregated weekly/monthly.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher OTIF indicates better delivery reliability; low values reflect service and execution issues.
  technical:
    measure_name: Ops OTIF %
    description: Delivery reliability measured by orders delivered on-time and in-full.
    depends_on_measures:
    - supply.otif.pct
    lineage:
    - fact_fulfillment.OTIF Flag
    calculation:
      op: rate
      column: OTIF Flag
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
  - Operations
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
    measure_name: Cash Conversion Cycle (Days)
    description: Combines receivables, inventory, and payables days to show cash efficiency.
    depends_on_measures: []
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
  - Operations
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of planned production time lost to downtime.
    definition: Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; analyze downtime drivers and loss categories.
  technical:
    measure_name: Downtime %
    description: Measures share of planned production time lost to downtime.
    depends_on_measures: []
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
  synonyms:
  - Unscheduled Downtime
  - Breakdown Downtime
  - Ungeplante Stillstandszeit
  - ungeplanter Stillstand
  example_question: Which assets cause the most unplanned downtime?
  kpi_key: Unplanned Downtime %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; track reliability and maintenance effectiveness.
  technical:
    measure_name: Unplanned Downtime %
    description: Measures unplanned downtime share of planned time.
    depends_on_measures: []
    lineage:
    - fact_ops_failures.Downtime Minutes
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

- kpi_id: ops.speed_loss.pct
  kpi_key: Speed Loss Rate %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref:
  - O-O1.2
  calc_type: rate
  business:
    purpose: Isolates chronic speed reduction from intermittent minor stops.
    definition: Speed Loss = (1 - Performance Rate) adjusted to exclude minor stop events. Corresponds to Six Big Losses Category 4 (Reduced Speed).
    grain_scope: Line/shift aggregated to plant and period.
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; speed losses are often misclassified as acceptable safety margin versus ISO ideal cycle time.
  technical:
    measure_name: Speed Loss Rate %
    description: Chronic speed reduction component of performance loss.
    depends_on_measures:
    - ops.performance.pct
    lineage:
    - fact_ops.Actual Cycle Time
    - fact_ops.Ideal Cycle Time
    - fact_ops.Minor Stop Count
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: OEE Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - ops.speed_loss.pct + minor_stops_contribution ≤ 1 - ops.performance.pct
    version: v1.0
  metadata_quality:
    completeness_score: 0.7
    last_review: 01.06.2026

- kpi_id: ops.changeover.minutes
  kpi_key: Changeover Time (min)
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  action_code_ref:
  - O-O1.3
  calc_type: duration
  business:
    purpose: Measures time lost to product or format changeovers.
    definition: Average minutes from last good piece of previous run to first good piece of next run, including mechanical setup, parameter adjustment, and trial run waste. Directly drives Six Big Losses Category 2 (Setup & Adjustment).
    grain_scope: Changeover event level; aggregated by line and period.
    unit_format: minutes (1 decimal)
    interpretation: Lower is better; SMED methodology targets < 10 minutes for high-mix lines.
  technical:
    measure_name: Changeover Time Minutes
    description: Average changeover duration per setup event.
    depends_on_measures: []
    lineage:
    - fact_ops_changeover.Start Timestamp
    - fact_ops_changeover.End Timestamp
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Production Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Changeover Time >= 0
    - Outliers > 4 × average require manual review
    version: v1.0
  metadata_quality:
    completeness_score: 0.7
    last_review: 01.06.2026

- kpi_id: inv.turnover
  synonyms:
  - Inventory Turns
  - Stock Turnover
  - Lagerumschlag
  - Umschlagshäufigkeit
  example_question: Which categories have the slowest inventory turnover?
  kpi_key: Inventory Turnover
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    measure_name: Inventory Turnover
    description: Measures how often inventory is sold and replaced.
    depends_on_measures: []
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
  synonyms:
  - Mean Absolute Percentage Error
  - MAPE
  - WMAPE
  - mittlerer absoluter prozentualer Fehler
  example_question: Which product families have the highest MAPE?
  kpi_key: Forecast MAPE %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; high MAPE indicates unstable demand or poor model fit.
  technical:
    measure_name: Forecast MAPE %
    description: Measures mean absolute percentage error in forecast.
    depends_on_measures: []
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
  synonyms:
  - Fill Rate
  - Order Fill Rate
  - Mengentreue
  - Lieferbereitschaftsgrad
  example_question: Which products fall short on in-full delivery?
  kpi_key: In-Full %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; low values indicate allocation or stock issues.
  technical:
    measure_name: In-Full %
    description: Measures share of deliveries with complete quantities.
    depends_on_measures: []
    lineage:
    - fact_fulfillment.In-Full Flag
    calculation:
      op: rate
      column: In-Full Flag
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Governance
  domain_tag:
  - Enterprise & Governance
  - Governance
  use_case_ref:
  - XD-004
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures share of actions that achieved the intended outcome.
    definition: Successful Actions / Routed Actions.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values indicate better execution effectiveness.
  technical:
    measure_name: Action Outcome Rate %
    description: Measures share of actions that achieved the intended outcome.
    depends_on_measures: []
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
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: enterprise.action_effectiveness_delta.amount
  kpi_key: Action Effectiveness Delta
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: governance
  domain_tag:
  - Enterprise & Governance
  - Governance
  use_case_ref:
  - XD-004
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Average EUR impact per achieved action execution — realized KPI delta per code.
    definition: Average impact_value across achieved rows in fact_action_outcome.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: EUR (#,0)
    interpretation: Higher values indicate stronger KPI improvement per action code execution.
  technical:
    measure_name: Action Effectiveness Delta
    description: Average EUR impact per achieved action execution.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.impact_value
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 26.04.2026

- kpi_id: enterprise.action_routed.count
  deprecated: true
  deprecation_reason: No active bracket/action-code references; targeted for removal in v1.1 (see extended_playbook.md)
  kpi_key: Actions Routed Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Governance
  domain_tag:
  - Enterprise & Governance
  - Governance
  use_case_ref:
  - XD-004
  action_code_ref:
  - X-E3.3
  calc_type: count
  business:
    purpose: Counts action codes routed for execution.
    definition: Count of routed action instances in the period.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: count
    interpretation: Higher counts indicate more routed actions.
  technical:
    measure_name: Actions Routed Count
    description: Counts action codes routed for execution.
    depends_on_measures: []
    lineage:
    - fact_action_log
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
    metadata_quality: null
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.price.list.amount
  kpi_key: List Price Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-004
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Total list price (before discounts) for price realization and discount analysis.
    definition: Sum of list price amount at invoice line grain.
    grain_scope: Invoice line aggregated to reporting period.
    unit_format: currency
    interpretation: Base for Price Realization %; required input for sales.price.realization_pct.
  technical:
    measure_name: List Price Amount
    description: Total list price amount from fact_sales; data requirement for semantic model.
    depends_on_measures: []
    lineage:
    - fact_sales.List Price Amount
    calculation:
      op: sum
      column: List Price Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Pricing Team
    steward: Pricing Analyst
    review_cycle: quarterly
    validation_process: reconciled to price books
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 2026-02-22

- kpi_id: sales.price.net.amount
  kpi_key: Net Price Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  - COM-004
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Total net price (after discounts) for price realization and discount analysis.
    definition: Sum of net price amount at invoice line grain.
    grain_scope: Invoice line aggregated to reporting period.
    unit_format: currency
    interpretation: Numerator for Price Realization %; required input for sales.price.realization_pct.
  technical:
    measure_name: Net Price Amount
    description: Total net price amount from fact_sales; data requirement for semantic model.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Price Amount
    calculation:
      op: sum
      column: Net Price Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Pricing Team
    steward: Pricing Analyst
    review_cycle: quarterly
    validation_process: reconciled to revenue
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 2026-02-22

- kpi_id: sales.price.realization_pct
  kpi_key: Price Realization %
  kpi_type: diagnostic
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
    unit_format: '''% (1 decimal)'''
    interpretation: Values below 100% indicate discounting; values above 100% indicate uplift vs list price.
  technical:
    measure_name: Price Realization %
    description: Shows how much of list price is realized after discounts.
    depends_on_measures:
    - sales.price.list.amount
    - sales.price.net.amount
    lineage:
    - fact_sales.List Price Amount
    - fact_sales.Net Price Amount
    calculation:
      op: ratio
      numerator:
        kpi: sales.price.net.amount
      denominator:
        kpi: sales.price.list.amount
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
  kpi_type: diagnostic
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
    measure_name: Mix Effect Amount
    description: Captures the residual effect from changes in product, channel, or region mix.
    depends_on_measures:
    - sales.net_sales.amount
    - sales.pvm.price_effect.amount
    - sales.pvm.volume_effect.amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Plan Sales Amount
    calculation:
      op: delta_chain
      minuend:
        kpi: sales.net_sales.amount
      subtrahends:
      - column: Plan Sales Amount
      - kpi: sales.pvm.price_effect.amount
      - kpi: sales.pvm.volume_effect.amount
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
    measure_name: Net Sales Amount
    description: Total invoiced revenue net of discounts and returns.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    calculation:
      op: sum
      column: Net Sales Amount
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
    unit_format: '''% (1 decimal)'''
    interpretation: Shows growth rate vs prior year.
  technical:
    measure_name: Delta% Net Sales
    description: Relative variance of Net Sales vs Last Year.
    depends_on_measures:
    - sales.net_sales.amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Last Year Sales Amount
    calculation:
      op: delta_pct
      minuend:
        kpi: sales.net_sales.amount
      subtrahend:
        column: Last Year Sales Amount
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
    unit_format: '''% (1 decimal)'''
    interpretation: Positive values indicate outperformance vs plan; negative values indicate shortfall.
  technical:
    measure_name: Net Sales % vs Plan
    description: Relative variance of Net Sales vs Plan.
    depends_on_measures:
    - sales.net_sales.amount
    lineage:
    - fact_sales.Plan Sales Amount
    calculation:
      op: delta_pct
      minuend:
        kpi: sales.net_sales.amount
      subtrahend:
        column: Plan Sales Amount
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
    measure_name: Price Effect Amount
    description: Quantifies the pure price impact in the PVM bridge.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Price Amount
    - fact_sales.Plan Quantity
    - fact_sales.Plan Sales Amount
    - fact_sales.Quantity
    calculation:
      op: pvm_price_effect
      net_price: Net Price Amount
      quantity: Quantity
      plan_sales: Plan Sales Amount
      plan_quantity: Plan Quantity
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
    measure_name: Volume Effect Amount
    description: Measures the variance caused purely by quantity changes at plan price.
    depends_on_measures: []
    lineage:
    - fact_sales.Plan Quantity
    - fact_sales.Plan Sales Amount
    - fact_sales.Quantity
    calculation:
      op: pvm_volume_effect
      quantity: Quantity
      plan_quantity: Plan Quantity
      plan_sales: Plan Sales Amount
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
  kpi_type: diagnostic
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
    measure_name: Sales Units
    description: Measures sold units volume in the period.
    depends_on_measures: []
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Innovation & People
  domain_tag:
  - People & Culture
  - Corporate & Strategy
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Measure how much of all eligible process transactions are executed via digital tools instead of manual channels.
    definition: Digital Transactions Count / Total Transactions Count for eligible processes.
    grain_scope: Process area / org; aggregated monthly or quarterly.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values indicate greater adoption of digital processes; low values show manual work and automation potential.
  technical:
    measure_name: Digital Adoption Rate %
    description: Measure how much of all eligible process transactions are executed via digital tools instead of manual channels.
    depends_on_measures: []
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
  - People & Culture
  use_case_ref:
  - XD-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Monitor risk of employee attrition across key roles and segments.
    definition: Probability of attrition for the selected population in the period.
    grain_scope: Org/role/segment; monthly.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values signal retention risk and require targeted actions.
  technical:
    measure_name: Attrition Risk %
    description: Probability of employee attrition
    depends_on_measures: []
    lineage: []
  governance:
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
    completeness_score: 1.0
    last_review: 27.01.2026

- kpi_id: wc.dso.days
  synonyms:
  - Days Sales Outstanding
  - Receivables Days
  - Average Collection Period
  - Debitorenlaufzeit
  - Forderungslaufzeit
  example_question: Why did DSO increase in the Nordics region last quarter?
  kpi_key: DSO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Finance
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
    measure_name: DSO Days
    description: Measures days sales outstanding for receivables.
    depends_on_measures: []
    lineage:
    - fact_accounts_receivable.AR Amount
    - fact_accounts_receivable.Revenue Amount
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

- kpi_id: fin.liquidity.inventory.amount
  kpi_key: Inventory Amount
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-001
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Provide closing inventory value for working capital and liquidity metrics.
    definition: Inventory value at period end at reporting valuation (e.g., standard or average cost).
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Higher values increase working capital needs; validate against seasonality and service targets.
  technical:
    measure_name: Inventory Amount
    description: Inventory value at period end
    depends_on_measures: []
    lineage:
    - fact_inventory.Inventory Amount
  governance:
    business_owner: Head of Treasury / Supply Chain Finance
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory value reconciles to balance sheet inventory accounts within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 27.01.2026

- kpi_id: fin.liquidity.payables.amount
  deprecated: true
  deprecation_reason: No active bracket/action-code references; targeted for removal in v1.1 (see extended_playbook.md)
  kpi_key: Payables Amount
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-001
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Track accounts payable balances used in DPO and working capital analysis.
    definition: Accounts payable balance at period end.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Higher balances increase working capital funding but can signal payment delays; compare to terms.
  technical:
    measure_name: Payables Amount
    description: Accounts payable balance at period end
    depends_on_measures: []
    lineage:
    - fact_accounts_payable.AP Amount
  governance:
    business_owner: Head of Treasury / Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Payables reconcile to AP ledgers within +/- 0.5 %; non-negative values.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 27.01.2026

- kpi_id: ops.planned.hours
  deprecated: true
  deprecation_reason: No active bracket/action-code references; targeted for removal in v1.1 (see extended_playbook.md)
  kpi_key: Planned Hours
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  use_case_ref:
  - OPS-001
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Scheduled production time allocated for machines/lines.
    definition: Sum of planned production hours
    grain_scope: Machine/line level; per shift/day, aggregated monthly.
    unit_format: hours
    interpretation: Capacity baseline for utilization and downtime; compare with actual runtime and downtime.
  technical:
    measure_name: Planned Hours
    description: Scheduled production time for machines/lines
    depends_on_measures: []
    lineage:
    - fact_ops.Planned Time Minutes
  governance:
    business_owner: Head of Supply Chain Planning
    data_owner: Supply Chain BI
    steward: Demand Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative; reconcile to planning system within +/- 0.1 h
    - Planned vs actual variance monitored in OEE context
    - Reconciles to WMS/OMS order status within +/- 1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 27.01.2026

- kpi_id: wc.dio.days
  synonyms:
  - Days Inventory Outstanding
  - Days Sales of Inventory
  - Inventory Days
  - Lagerreichweite
  - Bestandsreichweite
  example_question: Which product categories are driving up DIO this quarter?
  kpi_key: DIO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - S-I1.2
  calc_type: amount
  business:
    purpose: Measures days inventory outstanding.
    definition: Inventory / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days
    interpretation: Lower is better; high DIO increases cash tied up in stock.
  technical:
    measure_name: DIO Days
    description: Measures days inventory outstanding.
    depends_on_measures:
    - fin.liquidity.inventory.amount
    lineage:
    - fact_inventory.Inventory Amount
    - fact_inventory.COGS Amount
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
  synonyms:
  - Days Payable Outstanding
  - Payables Days
  - Creditor Days
  - Kreditorenlaufzeit
  example_question: Are we extending DPO with our largest suppliers this year?
  kpi_key: DPO Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Finance
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
    measure_name: DPO Days
    description: Measures days payables outstanding.
    depends_on_measures: []
    lineage:
    - fact_accounts_payable.AP Amount
    - fact_accounts_payable.COGS Amount
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
  synonyms:
  - Cash Conversion Cycle
  - Net Operating Cycle
  - Cash Cycle
  - Geldumschlagsdauer
  example_question: What pushed the cash conversion cycle higher this month?
  kpi_key: CCC Days
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Finance
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
    measure_name: CCC Days
    description: Measures cash conversion cycle length.
    depends_on_measures:
    - wc.dso.days
    - wc.dio.days
    - wc.dpo.days
    lineage:
    - fact_accounts_receivable.AR Amount
    - fact_accounts_receivable.Revenue Amount
    - fact_inventory.Inventory Amount
    - fact_inventory.COGS Amount
    - fact_accounts_payable.AP Amount
    - fact_accounts_payable.COGS Amount
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
  synonyms:
  - Cash and Cash Equivalents
  - Cash Position
  - Liquide Mittel
  - Kassenbestand
  example_question: How has our cash balance tracked versus plan this year?
  kpi_key: Cash Balance
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
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
    measure_name: Cash Balance
    description: Tracks cash and cash equivalents at period end.
    depends_on_measures: []
    lineage:
    - fact_cash_position.Cash Balance Amount
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

- kpi_id: fin.overdue_ar.pct
  synonyms:
  - Past-Due AR %
  - Overdue Receivables %
  - Überfällige Forderungen
  - Forderungsüberfälligkeitsquote
  example_question: Which customers are driving the rise in overdue AR?
  kpi_key: Overdue AR %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.2
  calc_type: rate
  business:
    purpose: Measures the proportion of accounts receivable past due date.
    definition: Overdue AR (past due date) / Total AR × 100. Customer-level overdue analysis enables targeted collection.
    grain_scope: Customer/entity level; aggregated monthly.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher overdue AR directly increases DSO. Values > 15 % signal systemic collection issues.
  technical:
    measure_name: Overdue AR %
    description: Share of accounts receivable past due date.
    depends_on_measures: []
    lineage:
    - fact_ar.Overdue Amount
    - fact_ar.Total AR Amount
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Credit Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Bounded between 0 % and 100 %
    - Overdue AR Amount <= Total AR Amount
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 01.06.2026

- kpi_id: fin.cash.ocf
  synonyms:
  - Operating Cash Flow
  - Cash Flow from Operations
  - OCF
  - Operativer Cashflow
  example_question: Why did operating cash flow fall short of plan in Q2?
  kpi_key: Operating Cash Flow
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  - Corporate & Strategy
  use_case_ref:
  - FIN-001
  action_code_ref:
  - F-C1.2
  - S-I1.2
  - F-C1.4
  calc_type: amount
  business:
    purpose: Measures cash generated by operating activities.
    definition: Net cash flows from operations for the period.
    grain_scope: Company/segment; monthly close.
    unit_format: EUR (2 decimals)
    interpretation: Positive values improve liquidity; negative values require investigation.
  technical:
    measure_name: Operating Cash Flow
    description: Measures cash generated by operating activities.
    depends_on_measures: []
    lineage:
    - fact_cash_flow.Operating Cash Flow Amount
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
  synonyms:
  - Cash Plan Variance %
  - Cash Budget Variance
  - Liquiditätsplanabweichung
  example_question: How far is cash tracking from the liquidity plan this month?
  kpi_key: Cash vs Plan %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
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
    unit_format: '''% (1 decimal)'''
    interpretation: Positive values indicate higher cash than planned.
  technical:
    measure_name: Cash vs Plan %
    description: Measures deviation of cash balance versus plan.
    depends_on_measures: []
    lineage:
    - fact_cash_position.Cash Balance Amount
    - fact_cash_position.Plan Cash Amount
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

- kpi_id: cost.cogs.amount
  kpi_key: Cost of Goods Sold Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-001
  - COM-002
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Total cost of goods sold for invoiced revenue; base for margin and PVM.
    definition: Sum of invoice line COGS amounts.
    grain_scope: Invoice line.
    unit_format: EUR (2 decimals)
    interpretation: Input to Gross Margin % and PVM; must align with P&L COGS.
  technical:
    measure_name: Cost of Goods Sold Amount
    description: Total cost of goods sold; base measure for margin and PVM.
    depends_on_measures: []
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    calculation:
      op: sum
      column: Cost of Goods Sold Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconcile with P&L COGS within +/-0.5%
    version: v2.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: margin.gm.pct
  kpi_key: Gross Margin %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
  good_is: higher
  synonyms:
  - GM%
  - Gross Margin Rate
  - Bruttomarge %
  example_question: Why did Gross Margin % drop in Region North last quarter?
  causal_links:
    model_type: local_linear_beta
    as_of: '2026-02-01'
    links:
    - influencing_kpi_id: sales.net_sales.amount
      effect:
        kind: abs_to_abs
        coefficient: 2.0e-06
        direction: positive
        interpretation: Higher net sales improve gross margin % when price and cost structure remain stable.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - Product Category
      formula:
        standardized: Δmargin.gm.pct = 0.000002 * Δsales.net_sales.amount
        latex: \Delta GM = 0.000002 \cdot \Delta NetSales
    - influencing_kpi_id: cost.cogs.amount
      effect:
        kind: abs_to_abs
        coefficient: -2.0e-06
        direction: negative
        interpretation: Higher cost of goods sold reduces gross margin % when revenue does not increase proportionally.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - Product Category
      formula:
        standardized: Δmargin.gm.pct = -0.000002 * Δcost.cogs.amount
        latex: \Delta GM = -0.000002 \cdot \Delta COGS
    - influencing_kpi_id: sales.net_sales.delta_pct.plan
      effect:
        kind: pct_to_pct
        coefficient: 0.3
        direction: positive
        interpretation: Closing the net sales gap versus plan is associated with higher gross margin % through better fixed-cost absorption and mix.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
      formula:
        standardized: Δmargin.gm.pct = 0.3 * Δsales.net_sales.delta_pct.plan
        latex: \Delta GM = 0.3 \cdot \Delta NetSales_{vsPlan}
    - influencing_kpi_id: sales.net_sales.delta_pct.ly
      effect:
        kind: pct_to_pct
        coefficient: 0.25
        direction: positive
        interpretation: Improving net sales growth versus prior year tends to improve gross margin % through scale and operating leverage.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
      formula:
        standardized: Δmargin.gm.pct = 0.25 * Δsales.net_sales.delta_pct.ly
        latex: \Delta GM = 0.25 \cdot \Delta NetSales_{vsLY}
    - influencing_kpi_id: sales.pvm.price_effect.amount
      effect:
        kind: abs_to_abs
        coefficient: 3.0e-06
        direction: positive
        interpretation: Positive price effect contributes directly to gross margin % improvement.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - SKU
      formula:
        standardized: Δmargin.gm.pct = 0.000003 * Δsales.pvm.price_effect.amount
        latex: \Delta GM = 0.000003 \cdot \Delta PVM_{price}
    - influencing_kpi_id: sales.pvm.volume_effect.amount
      effect:
        kind: abs_to_abs
        coefficient: 1.0e-06
        direction: positive
        interpretation: Positive volume effect improves gross margin % when incremental volume carries sufficient contribution margin.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - SKU
      formula:
        standardized: Δmargin.gm.pct = 0.000001 * Δsales.pvm.volume_effect.amount
        latex: \Delta GM = 0.000001 \cdot \Delta PVM_{volume}
    - influencing_kpi_id: sales.pvm.mix_effect.amount
      effect:
        kind: abs_to_abs
        coefficient: 2.0e-06
        direction: positive
        interpretation: Favorable product or customer mix improves gross margin % by shifting revenue toward higher-margin combinations.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - Product Category
      formula:
        standardized: Δmargin.gm.pct = 0.000002 * Δsales.pvm.mix_effect.amount
        latex: \Delta GM = 0.000002 \cdot \Delta PVM_{mix}
    - influencing_kpi_id: sales.price.realization_pct
      effect:
        kind: pp_to_pp
        coefficient: 0.8
        direction: positive
        interpretation: +1pp Price Realization implies +0.8pp Gross Margin (ceteris paribus).
      applicability:
        grain: month
        segments:
        - Region
        - Channel
      formula:
        standardized: Δmargin.gm.pct(pp)=0.8*Δsales.price.realization_pct(pp)
        latex: \\Delta GM_{pp} = 0.8 \\cdot \\Delta PR_{pp}
    - influencing_kpi_id: margin.gm.amount
      effect:
        kind: abs_to_abs
        coefficient: 2.0e-06
        direction: positive
        interpretation: Higher gross margin amount is associated with higher gross margin % when revenue mix remains comparable.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - Product Category
      formula:
        standardized: Δmargin.gm.pct = 0.000002 * Δmargin.gm.amount
        latex: \Delta GM = 0.000002 \cdot \Delta GM_{amount}
    - influencing_kpi_id: sales.price.list.amount
      effect:
        kind: abs_to_abs
        coefficient: 1.0e-06
        direction: positive
        interpretation: Higher list price levels support gross margin % provided realization discipline is maintained.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - SKU
      formula:
        standardized: Δmargin.gm.pct = 0.000001 * Δsales.price.list.amount
        latex: \Delta GM = 0.000001 \cdot \Delta Price_{list}
    - influencing_kpi_id: sales.price.net.amount
      effect:
        kind: abs_to_abs
        coefficient: 2.0e-06
        direction: positive
        interpretation: Higher net realized price improves gross margin % directly.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - SKU
      formula:
        standardized: Δmargin.gm.pct = 0.000002 * Δsales.price.net.amount
        latex: \Delta GM = 0.000002 \cdot \Delta Price_{net}
    - influencing_kpi_id: cost.cogs_per_unit.amount
      effect:
        kind: abs_to_abs
        coefficient: -0.15
        direction: negative
        interpretation: Higher unit COGS reduces gross margin % unless offset by price or mix gains.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
        - SKU
      formula:
        standardized: Δmargin.gm.pct = -0.15 * Δcost.cogs_per_unit.amount
        latex: \Delta GM = -0.15 \cdot \Delta COGS_{unit}
    - influencing_kpi_id: margin.gm.vs_plan.pct
      effect:
        kind: pp_to_pp
        coefficient: 0.9
        direction: positive
        interpretation: Improving gross margin performance versus plan is strongly aligned with higher actual gross margin %.
      applicability:
        grain: month
        segments:
        - Region
        - Channel
      formula:
        standardized: Δmargin.gm.pct = 0.9 * Δmargin.gm.vs_plan.pct
        latex: \Delta GM = 0.9 \cdot \Delta GM_{vsPlan}
  business:
    purpose: Gross margin % for commercial/operational reporting and strategic P&L reconciliation.
    definition: (Net Sales Amount - COGS Amount) / Net Sales Amount
    grain_scope: Invoice line aggregated to reporting period, org, customer or product segments.
    unit_format: '''% (1 decimal)'''
    interpretation: Values above 0 % indicate positive gross profit; trend over time shows structural profitability changes. Used for both operational management reporting and P&L reconciliation.
  technical:
    measure_name: Gross Margin %
    description: Gross Margin % used in commercial and management reporting and P&L reconciliation.
    depends_on_measures:
    - sales.net_sales.amount
    - cost.cogs.amount
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
    calculation:
      op: ratio
      numerator:
        kpi: margin.gm.amount
      denominator:
        kpi: sales.net_sales.amount
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

- kpi_id: sales.promo.cost.amount
  kpi_key: Promo Cost
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
    purpose: Total promotion cost for ROI and spend analysis.
    definition: Sum of promo cost from promo systems.
    grain_scope: Promo / period.
    unit_format: EUR (2 decimals)
    interpretation: Input to Promo ROI %.
  technical:
    measure_name: Promo Cost
    description: Total promotion cost.
    depends_on_measures: []
    lineage:
    - fact_promo.Promo Cost
    calculation:
      op: sum
      column: Promo Cost
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Promo cost > 0 when promo active
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.promo.incremental_gm.amount
  kpi_key: Incremental Gross Margin Amount
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
    purpose: Incremental gross margin from promotions for ROI numerator.
    definition: Incremental sales minus incremental COGS; proxy here as share of incremental sales.
    grain_scope: Promo / period.
    unit_format: EUR (2 decimals)
    interpretation: Input to Promo ROI %.
  technical:
    measure_name: Incremental Gross Margin Amount
    description: Incremental gross margin from promo.
    depends_on_measures:
    - sales.promo.incremental.amount
    - margin.gm.amount
    - sales.net_sales.amount
    - sales.promo.cost.amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Cost of Goods Sold Amount
    - fact_promo.Baseline Sales Amount
    calculation:
      op: delta
      minuend:
        calc:
          op: mul
          terms:
          - kpi: sales.promo.incremental.amount
          - calc:
              op: ratio
              numerator:
                kpi: margin.gm.amount
              denominator:
                kpi: sales.net_sales.amount
      subtrahend:
        kpi: sales.promo.cost.amount
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Refine formula when incremental COGS available
    version: v1.0
  metadata_quality:
    completeness_score: 0.9
    last_review: 23.01.2026

- kpi_id: sales.promo.roi.pct
  kpi_key: Promo ROI %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: ratio
  business:
    purpose: Measures profitability of promotions relative to spend.
    definition: (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount
    grain_scope: Promo campaign / product / period.
    unit_format: '''% (1 decimal)'''
    interpretation: Values > 0 indicate promotions adding value.
  technical:
    measure_name: Promo ROI %
    description: Measures profitability of promotions relative to spend.
    depends_on_measures:
    - sales.promo.incremental_gm.amount
    - sales.promo.cost.amount
    lineage:
    - fact_promo.Promo Cost
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
  - Commercial
  use_case_ref:
  - COM-004
  action_code_ref:
  - C-P4.1
  calc_type: ratio
  business:
    purpose: Gross margin rate during promo periods.
    definition: (Promo NS - Promo COGS) / Promo NS
    grain_scope: Promo period/product
    unit_format: '''% (1 decimal)'''
    interpretation: Profitability of promotions.
  technical:
    measure_name: GM % During Promo
    description: Gross margin rate during promo periods.
    depends_on_measures:
    - sales.net_sales.amount
    - cost.cogs.amount
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
    measure_name: COGS per Unit
    description: Shows unit cost level relative to sold volume.
    depends_on_measures:
    - cost.cogs.amount
    lineage:
    - fact_sales.Quantity
    calculation:
      op: ratio
      numerator:
        kpi: cost.cogs.amount
      denominator:
        column: Quantity
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

- kpi_id: sales.promo.cannibalized_sales.amount
  kpi_key: Cannibalized Sales Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  use_case_ref:
  - COM-004
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Sales lost on non-promoted items versus baseline (cannibalization in value).
    definition: MAX(0, Baseline Non-Promo Sales - Actual Non-Promo Sales).
    grain_scope: Promo campaign / product / period.
    unit_format: EUR (2 decimals)
    interpretation: Numerator for Cannibalization %; higher means more cannibalization.
  technical:
    measure_name: Cannibalized Sales Amount
    description: Sales amount lost on non-promoted items versus baseline.
    depends_on_measures:
    - sales.net_sales.amount
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
    - Lost non-promo floored at 0
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: sales.promo.cannibalization.pct
  kpi_key: Cannibalization %
  kpi_type: diagnostic
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; high cannibalization reduces net gain.
  technical:
    measure_name: Cannibalization %
    description: Measures share of promo uplift offset by decline in non-promoted sales.
    depends_on_measures:
    - sales.promo.incremental.amount
    - sales.promo.cannibalized_sales.amount
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
  synonyms:
  - Material Cost Ratio
  - Material Intensity
  - Materialkostenquote
  - Materialintensität
  example_question: Which products have the highest material cost ratio?
  kpi_key: Material Cost %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; increases indicate supplier or price pressure.
  technical:
    measure_name: Material Cost %
    description: Shows material cost share of net sales.
    depends_on_measures:
    - sales.net_sales.amount
    lineage:
    - fact_finance.Material Cost Amount
    - fact_finance.Net Sales Amount
    calculation:
      op: ratio
      numerator:
        column: Material Cost Amount
      denominator:
        column: Net Sales Amount
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
  synonyms:
  - OpEx Budget Variance %
  - Operating Expense Variance
  - Betriebskostenabweichung
  example_question: Where is OpEx running over plan this quarter?
  kpi_key: OpEx vs Plan %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
    unit_format: '''% (1 decimal)'''
    interpretation: Positive values indicate overspend; negative values indicate savings.
  technical:
    measure_name: OpEx vs Plan %
    description: Measures OpEx variance versus plan.
    depends_on_measures: []
    lineage:
    - fact_finance.OpEx Amount
    - fact_finance.Plan OpEx Amount
    calculation:
      op: delta_pct
      minuend:
        column: OpEx Amount
      subtrahend:
        column: Plan OpEx Amount
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
  synonyms:
  - Cost per Unit
  - Average Cost per Unit
  - Stückkosten
  - Selbstkosten je Stück
  example_question: How did unit cost change after the plant ramp-up?
  kpi_key: Unit Cost Amount
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
    measure_name: Unit Cost Amount
    description: Measures total cost per unit produced or sold.
    depends_on_measures:
    - margin.cogs.pct
    - cost.opex.vs_plan.pct
    - cost.material.pct
    - ops.labor.productivity.pct
    - ops.production.volume
    - ops.quality.defect_rate.pct
    - ops.yield.pct
    lineage:
    - fact_cost.COGS Amount
    - fact_output.Output Units
    calculation:
      op: ratio
      numerator:
        column: COGS Amount
      denominator:
        column: Output Units
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

- kpi_id: margin.gm.amount
  synonyms:
  - Gross Profit
  - Gross Income
  - Rohertrag
  - Bruttoergebnis vom Umsatz
  example_question: What drove the change in gross margin amount this month?
  kpi_key: Gross Margin Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
    measure_name: Gross Margin Amount
    description: Absolute gross margin in currency.
    depends_on_measures:
    - sales.net_sales.amount
    - cost.cogs.amount
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
    calculation:
      op: delta
      minuend:
        kpi: sales.net_sales.amount
      subtrahend:
        kpi: cost.cogs.amount
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

- kpi_id: sales.promo.baseline_sales.amount
  kpi_key: Baseline Sales Amount
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
    purpose: Baseline sales for incremental calculation.
    definition: Sum of baseline sales from promo system.
    grain_scope: Promo period/product
    unit_format: EUR (2 decimals)
    interpretation: Reference level for incremental lift.
  technical:
    measure_name: Baseline Sales Amount
    description: Baseline sales from promo.
    depends_on_measures: []
    lineage:
    - fact_promo.Baseline Sales Amount
    calculation:
      op: sum
      column: Baseline Sales Amount
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

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
    measure_name: Incremental Sales Amount
    description: Additional sales due to promotion.
    depends_on_measures:
    - sales.net_sales.amount
    - sales.promo.baseline_sales.amount
    lineage:
    - fact_promo.Baseline Sales Amount
    - fact_sales.Net Sales Amount
    calculation:
      op: delta
      minuend:
        kpi: sales.net_sales.amount
      subtrahend:
        kpi: sales.promo.baseline_sales.amount
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
  synonyms:
  - COGS Ratio
  - Cost of Sales %
  - Umsatzkostenquote
  - Materialaufwandsquote
  example_question: Why did COGS % of sales rise in Consumer Electronics?
  kpi_key: COGS % of Sales
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; complements gross margin %.
  technical:
    measure_name: COGS % of Sales
    description: Shows cost share relative to net sales.
    depends_on_measures:
    - sales.net_sales.amount
    lineage:
    - fact_finance.COGS Amount
    - fact_finance.Net Sales Amount
    calculation:
      op: ratio
      numerator:
        column: COGS Amount
      denominator:
        column: Net Sales Amount
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
  - Finance
  - Commercial
  use_case_ref:
  - COM-002
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Measures gross margin rate variance versus plan.
    definition: (Gross Margin % - Plan Gross Margin %) / Plan Gross Margin %.
    grain_scope: Company/segment; monthly.
    unit_format: '''% (1 decimal)'''
    interpretation: Positive values indicate better-than-plan margin.
  technical:
    measure_name: Gross Margin % vs Plan
    description: Measures gross margin rate variance versus plan.
    depends_on_measures:
    - margin.gm.amount
    lineage:
    - fact_sales.Plan Sales Amount
    - fact_sales.Plan COGS Amount
    calculation:
      op: delta_pct
      minuend:
        kpi: margin.gm.amount
      subtrahend:
        calc:
          op: delta
          minuend:
            column: Plan Sales Amount
          subtrahend:
            column: Plan COGS Amount
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

- kpi_id: margin.ebitda.pct
  kpi_key: EBITDA Margin
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref: []
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: EBITDA profitability relative to net sales for P&L reporting.
    definition: EBITDA Amount / Net Sales Amount
    grain_scope: Entity-month; finance reporting.
    unit_format: '''% (1 decimal)'''
    interpretation: Higher values indicate stronger operating profitability before interest, tax, depreciation and amortisation.
  technical:
    measure_name: EBITDA Margin
    description: EBITDA divided by net sales.
    depends_on_measures: []
    lineage:
    - fact_finance.EBITDA Amount
    - fact_finance.Net Sales Amount
    calculation:
      op: ratio
      numerator:
        column: EBITDA Amount
      denominator:
        column: Net Sales Amount
  governance:
    business_owner: Head of Controlling
    data_owner: BI Engineering
    steward: Controlling Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Value in [-100%; 100%]
    - Reconcile with P&L EBITDA +/- 0.5 pp
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 12.06.2026

- kpi_id: cost.base_volume.amount
  deprecated: true
  deprecation_reason: No active bracket/action-code references; targeted for removal in v1.1 (see extended_playbook.md)
  kpi_key: Cost Base Volume Amount
  kpi_type: diagnostic
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
    measure_name: Cost Base Volume Amount
    description: Baseline cost volume used for variance analysis.
    depends_on_measures: []
    lineage:
    - fact_cost.COGS Amount
    calculation:
      op: sum
      column: COGS Amount
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Cost Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: cost.opex.base.amount
  deprecated: true
  deprecation_reason: No active bracket/action-code references; targeted for removal in v1.1 (see extended_playbook.md)
  kpi_key: Opex Base Amount
  kpi_type: diagnostic
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
    measure_name: Opex Base Amount
    description: Baseline operating expense amount for variance tracking.
    depends_on_measures: []
    lineage:
    - fact_finance.OpEx Amount
    calculation:
      op: sum
      column: OpEx Amount
  governance:
    business_owner: Head of Controlling
    data_owner: Finance BI
    steward: Cost Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: enterprise.value_at_risk.index
  kpi_key: Enterprise Value-at-Risk Index
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Risk
  domain_tag:
  - Enterprise & Governance
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
    measure_name: Enterprise Value-at-Risk Index
    description: Aggregates downside risk across domains into a single index.
    depends_on_measures:
    - margin.gm.pct
    - sales.net_sales.delta_pct.ly
    - crm.clv.amount
    - svc.sla.attainment.pct
    - ops.otif.pct
    - ops.working_capital.ccc.days
    - people.digital_adoption.pct
    - people.attrition_risk.pct
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
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: scm.supplier_risk.score
  synonyms:
  - Supplier Risk Rating
  - Vendor Risk Index
  - Lieferantenrisiko-Score
  - Lieferantenrisikobewertung
  example_question: Which suppliers carry the highest risk score?
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
    measure_name: Supplier Risk Score
    description: Rates suppliers based on risk indicators.
    depends_on_measures: []
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
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.sla.attainment.pct
  synonyms:
  - Service Level
  - SLA Compliance
  - Telephone Service Factor
  - Servicegrad
  - Servicelevel
  example_question: Which queues are missing the SLA this week?
  kpi_key: SLA Attainment %
  kpi_type: diagnostic
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; interpret jointly with backlog and escalation %.
  technical:
    measure_name: SLA Attainment %
    description: Measures how many cases meet the committed SLA.
    depends_on_measures:
    - svc.backlog.count
    - svc.fcr.pct
    - svc.aht.minutes
    - svc.escalation.pct
    - svc.tickets.created.count
    - svc.tickets.closed.count
    lineage:
    - fact_support_cases.SLA Met Flag
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
  synonyms:
  - First Contact Resolution
  - First Call Resolution
  - One-Touch Resolution
  - Erstlösungsquote
  - Erstkontaktlösung
  example_question: Where is first contact resolution lowest, and why?
  kpi_key: First Contact Resolution %
  kpi_type: diagnostic
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
    unit_format: '''% (1 decimal)'''
    interpretation: Higher is better; keep in balance with AHT and escalation %.
  technical:
    measure_name: FCR %
    description: Shows the share of cases solved on first contact.
    depends_on_measures: []
    lineage:
    - fact_support_cases.FCR Flag
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
  synonyms:
  - Average Handle Time
  - Average Handling Time
  - Handle Time
  - durchschnittliche Bearbeitungszeit
  example_question: What is pushing average handle time up on chat?
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
    unit_format: '''minutes (1 decimal)'''
    interpretation: Lower is better, but balance with FCR and NPS.
  technical:
    measure_name: AHT Minutes
    description: Measures average time to handle a contact.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Handle Time Minutes
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
  synonyms:
  - Support Backlog
  - Open Ticket Backlog
  - Unresolved Tickets
  - Rückstand
  - offene Tickets
  example_question: Which queues have the largest case backlog?
  kpi_key: Backlog Count
  kpi_type: diagnostic
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
    unit_format: '''count'''
    interpretation: Lower is better; assess with SLA attainment and staffing KPIs.
  technical:
    measure_name: Backlog Count
    description: Quantifies unresolved work in queue.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Backlog Flag
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
  synonyms:
  - Net Promoter Score
  - Service NPS
  - Weiterempfehlungsrate
  - NPS
  example_question: Why did NPS dip for the Returns queue?
  kpi_key: NPS Index
  kpi_type: diagnostic
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
    definition: '%Promoters minus %Detractors from NPS survey.'
    grain_scope: survey_event aggregated to month by Org/Channel.
    unit_format: '''index'''
    interpretation: Higher is better; explain shifts with FCR, AHT, escalation %.
  technical:
    measure_name: NPS Index (Service)
    description: Measures customer advocacy and experience quality.
    depends_on_measures: []
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
  synonyms:
  - Escalation Rate
  - Ticket Escalation Rate
  - Transfer Rate
  - Eskalationsquote
  - Eskalationsrate
  example_question: Which issue types escalate most often?
  kpi_key: Escalation %
  kpi_type: diagnostic
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; balance with FCR and SLA.
  technical:
    measure_name: Escalation %
    description: Measures frequency of escalated cases.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Escalation Flag
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Typical healthy band 75?85%; balance with SLA/NPS.
  technical:
    measure_name: Utilization %
    description: Measures productive time versus paid time for agents.
    depends_on_measures:
    - res.occupancy.pct
    - res.overtime.pct
    - res.shrinkage.pct
    - svc.sla.attainment.pct
    - svc.backlog.count
    - svc.tickets.created.count
    lineage:
    - fact_workforce_management.Paid Time Minutes
    - fact_workforce_management.Work Time Minutes
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Balanced occupancy supports SLA and quality.
  technical:
    measure_name: Occupancy %
    description: Measures active vs idle share of time.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Idle Time Minutes
    - fact_workforce_management.Talk Time Minutes
    - fact_workforce_management.Wrap Time Minutes
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; monitor sustainability and cost.
  technical:
    measure_name: Overtime %
    description: Shows overtime share of total hours.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Overtime Minutes
    - fact_workforce_management.Paid Time Minutes
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
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Operations
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
    unit_format: '''% (1 decimal)'''
    interpretation: Lower is better; compare vs plan.
  technical:
    measure_name: Shrinkage %
    description: Measures non-productive share of paid time.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Paid Time Minutes
    - fact_workforce_management.Shrinkage Minutes
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
  kpi_type: diagnostic
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
    measure_name: Tickets Created Count
    description: Counts customer service tickets created in the period.
    depends_on_measures: []
    lineage:
    - fact_support_cases
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Analyst
    review_cycle: weekly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: svc.tickets.closed.count
  kpi_key: Tickets Closed Count
  kpi_type: diagnostic
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
    measure_name: Tickets Closed Count
    description: Counts customer service tickets closed in the period.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Case Closed Date
  governance:
    business_owner: Head of Service
    data_owner: Service Analytics
    steward: Service Analyst
    review_cycle: weekly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026

- kpi_id: enterprise.actions_executed.count
  kpi_key: Actions Executed Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: governance
  domain_tag:
  - ActionReady
  use_case_ref:
  - XD-004
  action_code_ref: []
  calc_type: count
  business:
    purpose: Counts ActionReady actions with a recorded outcome to track governance execution velocity.
    definition: Count of rows in fact_action_outcome where outcome_status is not blank.
    grain_scope: Action execution; aggregated monthly by domain.
    unit_format: count
    interpretation: Higher counts indicate active use of ActionReady recommendations.
  technical:
    measure_name: Actions Executed Count
    description: Number of action codes with a recorded outcome in fact_action_outcome.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.outcome_status
  governance:
    business_owner: Chief Analytics Officer
    data_owner: Enterprise Analytics
    steward: Analytics Governance
    review_cycle: monthly
    validation_process: automated
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 28.04.2026

- kpi_id: enterprise.avg_time_to_outcome.days
  kpi_key: Avg Time-to-Outcome Days
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: governance
  domain_tag:
  - ActionReady
  use_case_ref:
  - XD-004
  action_code_ref: []
  calc_type: quantity
  business:
    purpose: Measures how quickly ActionReady recommendations convert to confirmed outcomes.
    definition: Average of days_to_outcome across all executed action rows.
    grain_scope: Action execution; aggregated monthly by domain.
    unit_format: days (1 decimal)
    interpretation: Lower values indicate faster action-to-outcome cycles.
  technical:
    measure_name: Avg Time-to-Outcome Days
    description: Average days between action execution and outcome confirmation.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.days_to_outcome
  governance:
    business_owner: Chief Analytics Officer
    data_owner: Enterprise Analytics
    steward: Analytics Governance
    review_cycle: monthly
    validation_process: automated
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 28.04.2026

- kpi_id: enterprise.action_roi.pct
  kpi_key: Action ROI %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: governance
  domain_tag:
  - ActionReady
  use_case_ref:
  - XD-004
  action_code_ref: []
  calc_type: percentage
  business:
    purpose: Measures the financial return on ActionReady recommendation investments.
    definition: Total impact value of executed actions / total execution cost - 1.
    grain_scope: Action execution; aggregated monthly by domain.
    unit_format: '% (1 decimal)'
    interpretation: Values above 0% indicate net-positive actions; negative values flag ineffective interventions.
  technical:
    measure_name: Action ROI %
    description: 'Average ROI of executed actions: total impact value / total execution cost - 1.'
    depends_on_measures: []
    lineage:
    - fact_action_outcome.impact_value
    - fact_action_outcome.cost_to_execute
  governance:
    business_owner: Chief Analytics Officer
    data_owner: Enterprise Analytics
    steward: Analytics Governance
    review_cycle: monthly
    validation_process: automated
    qa_rules: []
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 28.04.2026

- kpi_id: retail.category.crosssell_rate.pct
  kpi_key: Category Cross-Sell Rate %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Retail
  use_case_ref:
  - COM-IND-R001
  action_code_ref:
  - C-M3.1
  calc_type: rate
  business:
    purpose: Share of transactions that contain items from two or more distinct product categories.
    definition: Transactions with >=2 distinct categories divided by total transactions in scope.
    grain_scope: Transaction aggregated by Month, Store, Channel, Category pair.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate stronger basket breadth and cross-sell capture; declining values signal weakening category affinity activation.
  technical:
    measure_name: Category Cross-Sell Rate %
    description: Share of transactions spanning two or more product categories.
    depends_on_measures: []
    lineage:
    - fact_sales.Transaction Key
    - fact_sales.Category Key
  governance:
    business_owner: Head of Category Management
    data_owner: Commercial BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: monthly reconciliation against POS transaction counts
    qa_rules:
    - Bounds [0%; 100%]
    - Transaction denominator excludes voided and returns-only baskets
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.06.2026

- kpi_id: retail.basket.items_per_transaction
  kpi_key: Items per Transaction
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Retail
  use_case_ref:
  - COM-IND-R001
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Average number of distinct line items per completed transaction.
    definition: Total line items divided by total transactions in scope.
    grain_scope: Transaction aggregated by Month, Store, Channel.
    unit_format: items (1 decimal)
    interpretation: A core basket-size driver; rising values indicate broader baskets and successful attachment, falling values indicate basket erosion.
  technical:
    measure_name: Items per Transaction
    description: Average distinct line items per completed transaction.
    depends_on_measures: []
    lineage:
    - fact_sales.Line Item Key
    - fact_sales.Transaction Key
  governance:
    business_owner: Head of Category Management
    data_owner: Commercial BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: monthly reconciliation against POS line-item counts
    qa_rules:
    - Bounds [1; 50]
    - Exclude voided and returns-only baskets from the denominator
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.06.2026

- kpi_id: retail.basket.value.average
  kpi_key: Average Basket Value
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Retail
  use_case_ref:
  - COM-IND-R001
  action_code_ref:
  - C-M3.1
  calc_type: amount
  business:
    purpose: Average net sales value of a completed transaction.
    definition: Net sales amount divided by total transactions in scope.
    grain_scope: Transaction aggregated by Month, Store, Channel.
    unit_format: EUR (2 decimals)
    interpretation: The headline basket-economics guardrail; cross-sell actions must grow breadth without eroding average basket value.
  technical:
    measure_name: Average Basket Value
    description: Average net sales value per completed transaction.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Transaction Key
  governance:
    business_owner: Head of Category Management
    data_owner: Commercial BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: monthly reconciliation against POS net sales and transaction counts
    qa_rules:
    - Bounds [0; 100000]
    - Net of VAT and returns; consistent with sales.net_sales.amount basis
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.06.2026

- kpi_id: retail.promotion.attachment_rate.pct
  kpi_key: Promotion Attachment Rate %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Retail
  use_case_ref:
  - COM-IND-R001
  action_code_ref:
  - C-M3.1
  calc_type: rate
  business:
    purpose: Share of promoted-item transactions that also contain at least one attached full-margin item from an affinity category.
    definition: Promoted transactions with an attached affinity-category item divided by all promoted transactions in scope.
    grain_scope: Transaction aggregated by Month, Store, Channel, Promotion.
    unit_format: '% (1 decimal)'
    interpretation: Measures whether promotion mechanics pull margin-accretive attachment rather than standalone deal-seeking; the primary lever for cross-sell rate.
  technical:
    measure_name: Promotion Attachment Rate %
    description: Share of promoted transactions carrying an attached affinity-category item.
    depends_on_measures: []
    lineage:
    - fact_sales.Promotion Key
    - fact_sales.Category Key
  governance:
    business_owner: Head of Trade Marketing
    data_owner: Commercial BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: monthly reconciliation against promotion participation logs
    qa_rules:
    - Bounds [0%; 100%]
    - Denominator restricted to transactions containing at least one promoted item
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.06.2026

- kpi_id: customer.rfm.frequency_score
  kpi_key: RFM Frequency Score
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Customer
  domain_tag:
  - Commercial
  - Retail
  use_case_ref:
  - COM-IND-R001
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Quintile score (1-5) of customer purchase frequency within the RFM model, averaged across the active base.
    definition: Mean of per-customer frequency quintile scores (1=least frequent, 5=most frequent) over the active customer base in scope.
    grain_scope: Customer aggregated to Segment by Month.
    unit_format: score (1-5, 1 decimal)
    interpretation: Higher frequency cohorts respond more strongly to cross-sell prompts; used to target attachment offers where repeat-visit behaviour already exists.
  technical:
    measure_name: RFM Frequency Score
    description: Average customer purchase-frequency quintile score from the RFM model.
    depends_on_measures: []
    lineage:
    - fact_sales.Customer Key
    - fact_sales.Transaction Key
  governance:
    business_owner: Head of Customer Insight
    data_owner: Commercial BI Engineering
    steward: Customer Analytics Lead
    review_cycle: quarterly
    validation_process: quarterly recalibration of RFM quintile boundaries against the active base
    qa_rules:
    - Bounds [1; 5]
    - Quintile boundaries recomputed each quarter on a trailing 12-month window
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.06.2026
```
