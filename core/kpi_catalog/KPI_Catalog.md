# KPI Catalog

> **Generated view.** The source of truth is the per-KPI files under [`kpis/`](kpis/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/kpi_catalog_files.py render`.

---

Schema: see [core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md](../templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md)

## KPIs

```yaml
- kpi_id: KPI-CUS-001
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
  good_is: higher
  business:
    purpose: Estimate long-term value of a customer to prioritize retention, acquisition, and service investments.
    definition: Sum of expected future gross margin per customer discounted over the chosen time horizon.
    grain_scope: Customer level; calculated on cohort or segment basis.
    unit_format: eur_2
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
  standard_ref:
  - standard: Marketing analytics — CRM (convention)
    name: Customer Lifetime Value
    alignment: none
    note: CLV (discounted expected future gross margin per customer) is a well-established marketing-analytics model, not a governed standard. The GM base ties to IFRS 15 / IAS 2; the forward-looking model is convention.

- kpi_id: KPI-OPS-001
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
  good_is: lower
  business:
    purpose: Quantify revenue exposure proportional to the customer attrition rate.
    definition: Net Sales Amount × (Churned Customers / Active Customers).
    grain_scope: Customer/segment; monthly.
    unit_format: eur_0
    interpretation: Higher values indicate more revenue at risk from customer churn; prioritize retention actions on high-value at-risk segments.
  technical:
    measure_name: Revenue at Risk Amount
    description: Net Sales Amount weighted by the churned-to-active customer ratio.
    depends_on_measures:
    - KPI-COM-005
    - KPI-CUS-004
    - KPI-CUS-006
    lineage:
    - fact_sales.Net Sales Amount
    - fact_customer_events.CustomerKey
    - fact_customer_events.Churn Flag
    - fact_customer_events.Activity Flag
    calculation:
      op: mul
      terms:
      - kpi: KPI-COM-005
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
  standard_ref:
  - standard: Marketing analytics — CRM (convention)
    name: Revenue at risk (churn-weighted)
    alignment: none
    note: Revenue at risk (net sales x churn rate) is a composite CRM convention built on IFRS 15 revenue and the churn convention; no external standard defines it.

- kpi_id: KPI-SVC-001
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
  good_is: lower
  business:
    purpose: Provide the absolute number of logged complaints.
    definition: Count of complaint records in the complaint/service system.
    grain_scope: Complaint / ticket; aggregated to org / channel / product / period.
    unit_format: count_0
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
  standard_ref:
  - standard: ISO 10002
    name: Complaints handling — complaint volume
    url: https://www.iso.org/standard/71580.html
    alignment: partial
    note: Complaint count feeds the ISO 10002:2018 complaints-handling process (the standard governs how complaints are captured/handled, not a specific count formula). Related to crm.nps / svc.* customer-experience measures.

- kpi_id: KPI-CUS-002
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
  good_is: higher
  business:
    purpose: Measure the share of customers that remain active from one period to the next, as a core loyalty KPI.
    definition: (Active Customers at end of period) / (Active Customers at start of period).
    grain_scope: Customer / segment / org; monthly or quarterly.
    unit_format: percent_1
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
  standard_ref:
  - standard: Marketing analytics — CRM (convention)
    name: Customer retention rate
    alignment: none
    note: Retention (end/start active customers) is a CRM-analytics convention. Note it is not the complement of churn unless the customer base and windows are defined consistently — pin both.

- kpi_id: KPI-CUS-003
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
  - XD-001
  action_code_ref:
  - C-C3.2
  - X-S1.3
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures customer advocacy and likelihood to recommend.
    definition: (%Promoters - %Detractors) from survey responses in the period.
    grain_scope: Survey response aggregated by period, segment, or region.
    unit_format: index_signed_0
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
  standard_ref:
  - standard: Bain NPS (proprietary)
    name: Net Promoter Score
    alignment: none
    note: NPS is a proprietary Bain & Company methodology, not an open standard. Duplicate of svc.nps.index — consolidate to one governed NPS. ISO 10002 / general customer-satisfaction monitoring is the standards-based alternative.

- kpi_id: KPI-CUS-004
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
  good_is: lower
  business:
    purpose: Count customers that have stopped purchasing in the observation window as basis for churn calculations.
    definition: Distinct customers with no qualifying transactions in the current period but active in the look-back window.
    grain_scope: Customer/segment; monthly or quarterly.
    unit_format: count_0
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
  standard_ref:
  - standard: Marketing analytics — CRM (convention)
    name: Churned customer count
    alignment: none
    note: Churn count (active in look-back, inactive now) is a CRM-analytics convention; churn-window definition must be pinned. No governing standard.

- kpi_id: KPI-CUS-005
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
    unit_format: eur_0
    interpretation: Base for concentration and CLV inputs.
  technical:
    measure_name: Customer Lifetime Revenue Amount
    description: Sum of realized revenue across customer lifecycle
    depends_on_measures:
    - KPI-COM-005
    lineage:
    - fact_sales.CustomerKey
    calculation:
      op: sumx_over_key
      key_column: CustomerKey
      value:
        kpi: KPI-COM-005
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
  standard_ref:
  - standard: IFRS 15
    name: Customer lifetime revenue (accumulated)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: partial
    note: The revenue base is IFRS 15 (net sales per customer accumulated from first purchase); the lifetime accumulation itself is a CRM-analytics convention, not an IFRS construct.

- kpi_id: KPI-CUS-006
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
    unit_format: count_0
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
  standard_ref:
  - standard: Marketing analytics — CRM (convention)
    name: Active customer count
    alignment: none
    note: Active-customer count (distinct customers with a qualifying transaction) is a CRM-analytics convention; the 'qualifying' window is a definitional choice to pin, not a standard.

- kpi_id: KPI-OPS-002
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
  good_is: higher
  business:
    purpose: Throughput speed versus theoretical maximum.
    definition: Actual output / Theoretical maximum output
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: percent_1
    interpretation: Higher performance indicates faster throughput; values above 100 % require validation of standard rates.
  technical:
    measure_name: Performance %
    description: Throughput speed versus theoretical maximum.
    depends_on_measures: []
    lineage:
    - fact_ops.Output Units
    - fact_ops.Run Time Minutes
    - fact_ops.Standard Rate Units Per Minute
    calculation:
      op: ratio
      numerator:
        column: Output Units
      denominator:
        calc:
          op: mul
          terms:
          - column: Run Time Minutes
          - calc:
              op: avg
              column: Standard Rate Units Per Minute
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
  standard_ref:
  - standard: ISO 22400-2
    id: E
    name: Effectiveness
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: ISO 22400-2 Effectiveness E = (produced quantity x ideal cycle time) / actual production time. Ours ('actual output / theoretical max output') is the same concept; align to the ISO ideal-cycle-time basis.

- kpi_id: KPI-OPS-003
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
  - FIN-002
  - XD-004
  action_code_ref:
  - O-O1.3
  - F-K2.2
  calc_type: rate
  good_is: higher
  business:
    purpose: Yield of conforming units relative to total units produced.
    definition: Good units / Total units
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: percent_1
    interpretation: Higher quality means fewer defects; low values indicate scrap/rework issues.
  technical:
    measure_name: Quality %
    description: Yield of conforming units relative to total units produced.
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
    steward: Quality Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Quality % bounded between 0 % and 100 %; reconcile to scrap/rework reporting within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  standard_ref:
  - standard: ISO 22400-2
    id: QR
    name: Quality ratio
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: ISO 22400-2 Quality ratio QR = good quantity / produced quantity. Matches ours exactly.

- kpi_id: KPI-OPS-004
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
  good_is: higher
  business:
    purpose: Shows output efficiency relative to labor input.
    definition: Output Units or Net Sales divided by Labor Hours (normalized to % baseline).
    grain_scope: Line/site; reported weekly or monthly.
    unit_format: percent_1
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
  standard_ref:
  - standard: ISO 22400-2
    id: WE
    name: Worker efficiency
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: ISO 22400-2 Worker efficiency WE = actual personnel work time / actual personnel attendance time. Ours (output or net sales / labour hours) is an output-based productivity ratio — same intent, different basis. Align the numerator/denominator to WE to claim the standard.

- kpi_id: KPI-OPS-005
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
  good_is: higher
  business:
    purpose: Measures average operating time between failures.
    definition: Operating Time Hours / Number of Failures.
    grain_scope: Asset/line; aggregated monthly.
    unit_format: hours_0
    interpretation: Higher is better; declining MTBF indicates reliability issues.
  technical:
    measure_name: MTBF (hours)
    description: Measures average operating time between failures.
    depends_on_measures:
    - KPI-OPS-012
    lineage:
    - fact_ops.Run Time Minutes
    calculation:
      op: ratio
      numerator:
        calc:
          op: ratio
          numerator:
            column: Run Time Minutes
          denominator:
            literal: 60
      denominator:
        kpi: KPI-OPS-012
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
  standard_ref:
  - standard: ISO 22400-2
    id: MTBF
    name: Mean operating time between failures
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: ISO 22400-2 MTBF = operating time / number of failures. Matches ours.

- kpi_id: KPI-OPS-006
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
  good_is: lower
  business:
    purpose: Measures average repair time after failures.
    definition: Total Repair Time Hours / Number of Failures.
    grain_scope: Asset/line; aggregated monthly.
    unit_format: hours_0
    interpretation: Lower is better; high MTTR indicates slow recovery or parts issues.
  technical:
    measure_name: MTTR (hours)
    description: Measures average repair time after failures.
    depends_on_measures:
    - KPI-OPS-012
    lineage:
    - fact_ops_failures.Repair Duration Hours
    calculation:
      op: ratio
      numerator:
        column: Repair Duration Hours
      denominator:
        kpi: KPI-OPS-012
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
  standard_ref:
  - standard: ISO 22400-2
    id: MTTR
    name: Mean time to restoration
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: ISO 22400-2 defines MTTR as mean time to restoration = total repair time / number of failures. Matches ours (labelled 'time to repair').

- kpi_id: KPI-OPS-007
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
  good_is: higher
  business:
    purpose: Tracks adherence to preventive maintenance plan.
    definition: Completed PM Orders / Planned PM Orders.
    grain_scope: Site/asset; monthly.
    unit_format: percent_1
    interpretation: Higher is better; low compliance increases breakdown risk.
  technical:
    measure_name: PM Compliance %
    description: Tracks adherence to preventive maintenance plan.
    depends_on_measures: []
    lineage:
    - fact_maintenance.Order Type
    - fact_maintenance.Order Status
    calculation:
      op: ratio
      numerator:
        calc:
          op: count_filtered
          column: Order Type
          filters:
          - column: Order Type
            equals: PM
          - column: Order Status
            equals: Completed
      denominator:
        calc:
          op: count_filtered
          column: Order Type
          filters:
          - column: Order Type
            equals: PM
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
  standard_ref:
  - standard: ISO 22400-2
    name: (planned-maintenance compliance)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: 'PM compliance (completed vs planned PM orders) is a maintenance-management KPI; ISO 22400-2 covers corrective-maintenance ratio and reliability but not PM-schedule compliance. Related external reference: EN 15341 maintenance KPIs.'

- kpi_id: KPI-OPS-008
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
  good_is: lower
  business:
    purpose: Measures stockout frequency for critical spare parts.
    definition: Stockout Events / Total Parts Requests.
    grain_scope: Site/part; monthly.
    unit_format: percent_1
    interpretation: Lower is better; stockouts drive downtime and MTTR.
  technical:
    measure_name: Spare Parts Stockout %
    description: Measures stockout frequency for critical spare parts.
    depends_on_measures: []
    lineage:
    - fact_maintenance.Parts Stockout Flag
    calculation:
      op: rate
      column: Parts Stockout Flag
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
  standard_ref:
  - standard: SCOR-DS
    name: Spare-parts (MRO) availability
    url: https://scor.ascm.org/performance/asset-management
    alignment: none
    note: Spare-parts stockout is an MRO/maintenance availability diagnostic; SCOR captures availability inside Reliability/Asset-Management rather than as a standalone metric. Mirrors KPI-SCM-002.

- kpi_id: KPI-OPS-009
  kpi_key: Throughput Units
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - FIN-002
  - XD-004
  action_code_ref:
  - O-O1.2
  - O-O1.4
  - F-K2.3
  calc_type: count
  good_is: higher
  business:
    purpose: Measures total output volume in units.
    definition: Sum of produced units in the period.
    grain_scope: Line/day; aggregated to site and month.
    unit_format: units_0
    interpretation: Higher values indicate higher output; analyze against capacity and demand.
  technical:
    measure_name: Throughput Units
    description: Measures total output volume in units.
    depends_on_measures: []
    lineage:
    - fact_ops.Output Units
    calculation:
      op: sum
      column: Output Units
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
  standard_ref:
  - standard: ISO 22400-2
    id: TR
    name: Throughput rate / Produced quantity
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: ISO 22400-2 Throughput rate TR is per-unit-of-time (produced quantity / time); ours is a produced-quantity sum (the PQ element). Divide by the period to obtain the ISO throughput rate. Duplicate of ops.production.volume.

- kpi_id: KPI-QUA-001
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
  good_is: higher
  business:
    purpose: Measures share of units produced without rework or scrap.
    definition: First-pass good units (no rework, no scrap) / total units entering the process (ISO 22400-2 A.9); Good Units counts first-pass good units only, reworked units are excluded.
    grain_scope: Line/day; aggregated monthly.
    unit_format: percent_1
    interpretation: Higher is better; low FPY indicates process instability.
  technical:
    measure_name: First Pass Yield %
    description: Measures share of units produced without rework or scrap.
    depends_on_measures:
    - KPI-QUA-002
    - KPI-OPS-010
    - KPI-QUA-003
    - KPI-QUA-004
    - KPI-QUA-005
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
  standard_ref:
  - standard: ISO 22400-2
    id: FPY
    name: First pass yield
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: ISO 22400-2 First Pass Yield = units passing first time without rework or scrap / total units. Matches ours. Note it duplicates KPI-OPS-003 / ops.yield.pct when computed at a single stage — FPY is properly the product of stage yields.

- kpi_id: KPI-QUA-002
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
  good_is: lower
  business:
    purpose: Measures share of units scrapped in production.
    definition: Scrap Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: percent_1
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
  standard_ref:
  - standard: ISO 22400-2
    id: SR
    name: Scrap ratio
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: ISO 22400-2 Scrap ratio SR = scrap quantity / produced quantity. Matches ours.

- kpi_id: KPI-OPS-010
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
  good_is: lower
  business:
    purpose: Measures share of units requiring rework.
    definition: Reworked Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: percent_1
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
  standard_ref:
  - standard: ISO 22400-2
    id: RR
    name: Rework ratio
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: ISO 22400-2 Rework ratio RR = reworked quantity / produced quantity. Matches ours.

- kpi_id: KPI-QUA-003
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
  good_is: lower
  business:
    purpose: Captures financial impact of scrap, rework, and warranty/complaints.
    definition: Sum of cost impacts for quality failures in period.
    grain_scope: Site/month; aggregated to business unit.
    unit_format: eur_2
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
  standard_ref:
  - standard: ISO 22400-2
    name: (cost of poor quality)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: 'Cost of Poor Quality is a cost concept (ASQ / Juran Cost-of-Quality framework: prevention–appraisal–failure), not an ISO 22400-2 operations KPI. Keep as a quality-cost metric referenced to the ASQ CoQ model.'

- kpi_id: KPI-QUA-004
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
  good_is: lower
  business:
    purpose: Measures customer complaints relative to shipped units.
    definition: Complaint Count / Units Shipped.
    grain_scope: Product/month; aggregated to business unit.
    unit_format: percent_1
    interpretation: Lower is better; spikes indicate quality or service issues.
  technical:
    measure_name: Complaint Rate %
    description: Measures customer complaints relative to shipped units.
    depends_on_measures:
    - KPI-SVC-001
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
  standard_ref:
  - standard: ISO 22400-2
    name: (customer complaint rate)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Customer-complaint rate is a complaints-handling metric (ISO 10002), not a manufacturing-operations KPI. No ISO 22400-2 equivalent.

- kpi_id: KPI-QUA-005
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
  good_is: lower
  business:
    purpose: Measures defect count per 1,000 units produced.
    definition: (Defect Count / Total Units) * 1,000.
    grain_scope: Line/day; aggregated monthly.
    unit_format: defects_per_1k_0
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
  standard_ref:
  - standard: ISO 22400-2
    name: (defects per 1,000 units)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Defects-per-thousand is not an ISO 22400-2 KPI; it is a Six Sigma defect-rate (DPMO-family) metric. ISO 22400-2 captures the same quality loss via scrap ratio (SR) / rework ratio (RR).

- kpi_id: KPI-SCM-001
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
  good_is: lower
  business:
    purpose: Measures inventory holding period in days.
    definition: Average Inventory / (COGS / 365).
    grain_scope: SKU/location; aggregated monthly.
    unit_format: days_0
    interpretation: Higher values indicate slower movement and more cash tied up.
  technical:
    measure_name: Days in Inventory
    description: Measures inventory holding period in days.
    depends_on_measures: []
    lineage:
    - fact_cogs.COGS Amount
    - fact_inventory.Average Inventory Amount
    calculation:
      op: ratio
      numerator:
        calc:
          op: mul
          terms:
          - column: Average Inventory Amount
          - literal: 365
      denominator:
        column: COGS Amount
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
  standard_ref:
  - standard: SCOR-DS
    id: AM.1.1
    name: Cash-to-Cash Cycle Time — inventory-days component
    url: https://scor.ascm.org/performance/asset-management
    alignment: partial
    note: Maps to the inventory-days input of SCOR Cash-to-Cash Cycle Time (AM.1.1 = DSO + Inventory Days of Supply − DPO). Ours is COGS-based DIO. Twin of KPI-FIN-004 — same formula, different grain (SKU/location vs company/segment); both kept (D-594, 30.09.2026).

- kpi_id: KPI-SCM-002
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
  good_is: lower
  business:
    purpose: Measures how often inventory is unavailable when demanded.
    definition: Stockout Events / Total Demand Events.
    grain_scope: SKU/location; aggregated weekly or monthly.
    unit_format: percent_1
    interpretation: Lower is better; high stockout rate impacts service and revenue.
  technical:
    measure_name: Stockout Rate %
    description: Measures how often inventory is unavailable when demanded.
    depends_on_measures: []
    lineage:
    - fact_stockout.Stockout Flag
    calculation:
      op: rate
      column: Stockout Flag
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
  standard_ref:
  - standard: SCOR-DS
    id: RL.1.1
    name: Perfect Order Fulfillment (availability)
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: none
    note: No direct SCOR L1–L3 metric. Stockout rate is the inverse of item availability/fill, which SCOR captures inside Perfect Order (RL) rather than as a standalone metric.

- kpi_id: KPI-SCM-003
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
  good_is: lower
  business:
    purpose: Measures the value of inventory exceeding forward demand cover.
    definition: Inventory value exceeding X months of forward demand (typically > 6 months of projected consumption). Primary working capital lock-up driver when DIO is high.
    grain_scope: SKU/location; aggregated to product category and plant monthly.
    unit_format: eur_2
    interpretation: Lower is better; excess inventory ties up working capital and increases obsolescence risk. Reduction directly improves DIO and cash conversion.
  technical:
    measure_name: Excess Inventory Amount
    description: Inventory value beyond coverage threshold.
    depends_on_measures:
    - KPI-SCM-001
    lineage:
    - fact_inventory.Stock Value
    - fact_demand_forecast.Monthly Demand Forecast
    calculation:
      op: hitl
      blocked_by: authoring
      reason: New-territory KPI — no legacy DAX counterpart to verify against (not in any products/fabric/powerbi/dist/*.SemanticModel). A months-of-forward-demand coverage threshold comparison per SKU is beyond the current grammar, and no threshold value is specified precisely enough to derive without guessing.
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
  standard_ref:
  - standard: SCOR-DS
    url: https://scor.ascm.org/performance/asset-management
    alignment: none
    note: Excess/obsolete inventory value is an inventory-health practice concern, not a named SCOR performance metric (SCOR treats it under Asset Management practices).

- kpi_id: KPI-SCM-004
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
  good_is: lower
  business:
    purpose: Measures share of inventory considered obsolete.
    definition: Obsolete Inventory Value / Total Inventory Value.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: percent_1
    interpretation: Lower is better; high obsolescence indicates slow movement or aging.
  technical:
    measure_name: Obsolete Inventory %
    description: Measures share of inventory considered obsolete.
    depends_on_measures: []
    lineage:
    - fact_inventory.Obsolete Inventory Amount
    - fact_inventory.Average Inventory Amount
    calculation:
      op: ratio
      numerator:
        column: Obsolete Inventory Amount
      denominator:
        column: Average Inventory Amount
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
  standard_ref:
  - standard: SCOR-DS
    name: Asset Management — obsolete-inventory health
    url: https://scor.ascm.org/performance/asset-management
    alignment: none
    note: Obsolete-inventory share is an inventory-health practice concern under SCOR Asset Management, not a named SCOR performance metric and not ISO 22400-2. Mirrors KPI-SCM-003 from the SCM run.

- kpi_id: KPI-SCM-005
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
  good_is: higher
  business:
    purpose: Measures how close forecasted demand is to actual demand.
    definition: 1 - |Forecast - Actual| / Actual.
    grain_scope: SKU/week; aggregated monthly.
    unit_format: percent_1
    interpretation: Higher is better; low accuracy drives inventory and service issues.
  technical:
    measure_name: Forecast Accuracy %
    description: Measures how close forecasted demand is to actual demand.
    depends_on_measures: []
    lineage:
    - fact_forecast.Forecast Units
    - fact_sales.Sales Units
    calculation:
      op: delta
      minuend:
        literal: 1
      subtrahend:
        calc:
          op: abs
          value:
            calc:
              op: ratio
              numerator:
                calc:
                  op: delta
                  minuend:
                    column: Forecast Units
                  subtrahend:
                    column: Sales Units
              denominator:
                column: Sales Units
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Value between 0 % and 100 %
    - 'Known DAX nuance (I-10.0 follow-up): legacy DAX guards Sales Units = 0 with an explicit IF(...,BLANK(),...); the synthesized 1 - ABS(DIVIDE(...)) relies on DIVIDE''s native BLANK()-on-zero-denominator instead, which in DAX''s "-" operator coerces to 0 — so at exactly Sales Units = 0 the synthesized formula returns 1 where legacy returns BLANK(). Matches everywhere Actual Demand > 0 holds (the documented precondition above); the edge case has no flat-DSL fix without a dedicated IF/blank-guard op.'
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 23.01.2026
  standard_ref:
  - standard: SCOR-DS
    alignment: none
    note: Forecast accuracy is a Plan-process ENABLER in SCOR, not a core RL/RS/AG/CO/AM performance metric. Better external references are the IBF / APICS forecasting standards (MAPE, bias, tracking signal) — a candidate standards domain of its own.

- kpi_id: KPI-SCM-006
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
  good_is: zero
  business:
    purpose: Measures systematic over- or under-forecasting.
    definition: (Forecast - Actual) / Actual.
    grain_scope: SKU/week; aggregated monthly.
    unit_format: percent_1
    interpretation: Values near 0 are best; positive bias indicates over-forecasting.
  technical:
    measure_name: Forecast Bias %
    description: Measures systematic over- or under-forecasting.
    depends_on_measures: []
    lineage:
    - fact_forecast.Forecast Units
    - fact_sales.Sales Units
    calculation:
      op: ratio
      numerator:
        calc:
          op: delta
          minuend:
            column: Forecast Units
          subtrahend:
            column: Sales Units
      denominator:
        column: Sales Units
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
  standard_ref:
  - standard: SCOR-DS
    alignment: none
    note: As KPI-SCM-005 — no SCOR metric home; IBF/APICS forecasting standards are the right external reference.

- kpi_id: KPI-SCM-007
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
  - XD-003
  - FIN-001
  - FIN-002
  action_code_ref:
  - S-F3.3
  - S-I1.1
  - S-I1.3
  - S-R2.1
  - S-R2.2
  - S-R2.5
  - F-K2.4
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures share of orders delivered on time and in full.
    definition: OTIF Orders / Total Orders.
    grain_scope: Order/day; aggregated weekly or monthly.
    unit_format: percent_1
    interpretation: Higher is better; key service level indicator.
  technical:
    measure_name: OTIF %
    description: Measures share of orders delivered on time and in full.
    depends_on_measures:
    - KPI-SCM-008
    - KPI-SCM-018
    - KPI-SCM-009
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
  standard_ref:
  - standard: SCOR-DS
    id: RL.1.1
    name: Perfect Order Fulfillment
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: partial
    note: OTIF here = on-time AND in-full — 2 of SCOR Perfect Order's 4 components; omits Documentation Accuracy (RL.2.3) and Perfect Condition (RL.2.4). SCOR RL.1.1 is order-level and requires all four to pass. To claim SCOR Perfect Order, add the two missing components; otherwise label it OTIF, not Perfect Order.

- kpi_id: KPI-SCM-008
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
  good_is: higher
  business:
    purpose: Measures share of deliveries arriving on time.
    definition: On-Time Deliveries / Total Deliveries.
    grain_scope: Delivery/day; aggregated weekly or monthly.
    unit_format: percent_1
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
  standard_ref:
  - standard: SCOR-DS
    id: RL.2.2
    name: Delivery Performance to Customer Commit Date
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: partial
    note: Reference date is unspecified in our definition; SCOR RL.2.2 measures against the customer COMMIT date, not the requested/scheduled date. Pin the reference date to the commit date to align.

- kpi_id: KPI-SCM-009
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
  good_is: lower
  business:
    purpose: Measures lost demand share due to stockouts.
    definition: Lost Demand Qty / Total Demand Qty.
    grain_scope: SKU/location/day; aggregated weekly or monthly.
    unit_format: percent_1
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
  standard_ref:
  - standard: SCOR-DS
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: none
    note: Lost-demand share is a Plan/service-loss diagnostic, not a named SCOR metric.

- kpi_id: KPI-SCM-010
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
  good_is: lower
  business:
    purpose: Captures additional cost for expedited shipments.
    definition: Sum of expedite fees and premium freight charges.
    grain_scope: Shipment/month.
    unit_format: eur_2
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
  standard_ref:
  - standard: SCOR-DS
    id: CO.1.1
    name: Total Supply Chain Management Cost
    url: https://scor.ascm.org/performance/cost
    alignment: partial
    note: Premium-freight / expedite is one cost component within SCOR CO.1.1 (Total SC Management Cost), not the whole metric.

- kpi_id: KPI-SCM-011
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
  good_is: lower
  business:
    purpose: Captures penalties for service level breaches.
    definition: Sum of penalty charges incurred in the period.
    grain_scope: Order/month.
    unit_format: eur_2
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
  standard_ref:
  - standard: SCOR-DS
    id: CO.1.1
    name: Total Supply Chain Management Cost
    url: https://scor.ascm.org/performance/cost
    alignment: partial
    note: Service-failure penalties are a cost component within SCOR's Cost attribute (CO.1.1), not a named standalone SCOR metric.

- kpi_id: KPI-SCM-012
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
  good_is: lower
  business:
    purpose: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage (units-based demand forecast).
    definition: Service Impact % = Stockout Impact % x (Under-Forecast Lost Demand / Total Lost Demand). Under-forecast is defined as a negative forecast error below a configurable threshold; all inputs are unit-based (qty), not revenue.
    grain_scope: Calculated at location_sku_day or sku_week; reported at sku_month aggregated by Date, Org, Product.
    unit_format: percent_1
    interpretation: Lower values are better; high impact indicates forecast under-coverage driving service loss.
  technical:
    measure_name: Service Impact %
    description: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage.
    depends_on_measures: []
    lineage:
    - fact_forecast.Forecast Units
    - fact_stockout.Demand Units
    - fact_stockout.Lost Demand Units
    calculation:
      op: hitl
      blocked_by: grammar
      reason: Legacy DAX (products/fabric/powerbi/dist/SupplyChain.SemanticModel) is [Stockout Impact %] * DIVIDE ( SUMX ( fact_stockout, IF ( context-filtered Forecast Units < row-level Demand Units, row-level Lost Demand Units, 0 ) ), SUM ( Lost Demand Units ) ) — a per-row conditional SUMX comparing a row-level column to a context-filtered aggregate (CALCULATE(SUM(...)) evaluated per row), beyond the current sum/ratio/mul/sumx_product-shaped grammar.
      pattern: sumx_row_vs_context_aggregate
      occurrences_in_corpus: 1
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
  standard_ref:
  - standard: SCOR-DS
    name: Plan service-loss diagnostic
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: none
    note: Forecast service impact is a Plan-process service-loss diagnostic, not a named SCOR performance metric. Forecast-error references are the IBF/APICS forecasting standards; the service-loss link is SCOR Reliability.

- kpi_id: KPI-OPS-011
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
  good_is: higher
  business:
    purpose: Measures manufacturing performance combining availability, performance, and quality.
    definition: Availability % * Performance % * Quality %
    grain_scope: Production line; aggregated monthly.
    unit_format: percent_1
    interpretation: Higher OEE indicates better utilization; capped at 100 %.
  technical:
    measure_name: OEE %
    description: Measures manufacturing performance combining availability, performance, and quality.
    depends_on_measures:
    - KPI-OPS-016
    - KPI-OPS-002
    - KPI-OPS-003
    lineage:
    - fact_ops.Run Time Minutes
    - fact_ops.Planned Time Minutes
    - fact_ops.Output Units
    - fact_ops.Good Units
    - fact_ops.Standard Rate Units Per Minute
    calculation:
      op: mul
      terms:
      - kpi: KPI-OPS-016
      - kpi: KPI-OPS-002
      - kpi: KPI-OPS-003
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
  standard_ref:
  - standard: ISO 22400-2
    id: OEE
    name: Overall Equipment Effectiveness index
    url: https://www.iso.org/standard/54497.html
    alignment: exact
    note: OEE = Availability x Effectiveness (Performance) x Quality ratio is defined verbatim by ISO 22400-2. Our A x P x Q matches. Pin the time-state model (Planned Busy Time basis) so components reconcile to the standard.

- kpi_id: KPI-OPS-012
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
  good_is: lower
  business:
    purpose: Counts equipment or process failures in the period.
    definition: Count of recorded failure events.
    grain_scope: Asset or line; aggregated by period.
    unit_format: count_0
    interpretation: Higher counts indicate lower reliability.
  technical:
    measure_name: Failure Count
    description: Counts equipment or process failures in the period.
    depends_on_measures: []
    lineage:
    - fact_ops_failures
    calculation:
      op: count
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
  standard_ref:
  - standard: ISO 22400-2
    name: (number of failures element)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Raw failure count is an ISO 22400-2 element (input to MTBF/MTTR), not a headline KPI itself.

- kpi_id: KPI-OPS-013
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
    definition: Sum over line/day of (Standard Rate Units Per Minute * Planned Time Minutes).
    grain_scope: Line/site; aggregated by period.
    unit_format: units_0
    interpretation: Baseline for comparing actual throughput.
  technical:
    measure_name: Planned Output Units
    description: Captures planned production output volume (theoretical output at standard rate).
    depends_on_measures: []
    lineage:
    - fact_ops.Planned Time Minutes
    - fact_ops.Standard Rate Units Per Minute
    calculation:
      op: sumx_product
      factor_a: Standard Rate Units Per Minute
      factor_b: Planned Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    name: Planned quantity element
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Planned output (standard rate x planned time) is the ISO 22400-2 planned-quantity element, an input to Effectiveness, not a KPI.

- kpi_id: KPI-OPS-014
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
    unit_format: count_0
    interpretation: Higher counts indicate more planned maintenance activity.
  technical:
    measure_name: Preventive Maintenance Task Count
    description: Counts preventive maintenance tasks executed or scheduled.
    depends_on_measures: []
    lineage:
    - fact_maintenance
    calculation:
      op: count
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
  standard_ref:
  - standard: ISO 22400-2
    name: (PM task count)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Raw PM-task count is an operational element, not an ISO 22400-2 KPI.

- kpi_id: KPI-QUA-006
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
  good_is: lower
  business:
    purpose: Measures share of defective units in production.
    definition: Defective Units / Total Produced Units.
    grain_scope: Line/shift; aggregated by period.
    unit_format: percent_1
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
  standard_ref:
  - standard: ISO 22400-2
    id: QR
    name: Quality ratio (complement)
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: Defect rate = 1 − Quality ratio; it is the quality-loss complement of ISO 22400-2 QR, decomposed by the standard into scrap ratio (SR) and rework ratio (RR). Report against QR to align.

- kpi_id: KPI-OPS-015
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
  good_is: lower
  business:
    purpose: Counts safety incidents recorded in the period.
    definition: Count of recorded safety incidents.
    grain_scope: Site; aggregated by period.
    unit_format: count_0
    interpretation: Higher counts indicate higher safety risk.
  technical:
    measure_name: Safety Incident Count
    description: Counts safety incidents recorded in the period.
    depends_on_measures: []
    lineage:
    - fact_safety.Incident Count
    calculation:
      op: hitl
      blocked_by: data_contract
      reason: 'Legacy system itself has no real formula here: products/fabric/powerbi/dist/Operations.SemanticModel''s own DAX is a documented placeholder (VAR _pending = "Requires fact_safety_incidents table (not yet in data contract)" RETURN BLANK()) — the source table does not exist yet in the data contract, upstream of any DSL grammar question.'
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
  standard_ref:
  - standard: ISO 22400-2
    name: (safety incident count)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Safety-incident count belongs to occupational health & safety management (ISO 45001), not manufacturing-operations performance (ISO 22400-2).

- kpi_id: KPI-SCM-013
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
    unit_format: count_0
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
  standard_ref:
  - standard: Retail analytics (convention)
    name: Order line count
    alignment: none
    note: Order-line count is an operational volume element, not a standard-defined KPI.

- kpi_id: KPI-SCM-014
  kpi_key: Plans Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  - Forecast Planning
  use_case_ref:
  - SCM-003
  - SCM-001
  - FIN-001
  action_code_ref:
  - S-F3.4
  - S-F3.1
  - S-F3.2
  calc_type: count
  good_is: lower
  business:
    purpose: Counts planning cycles or plan versions in the period.
    definition: Count of plan records or plan versions.
    grain_scope: Plan; aggregated by period.
    unit_format: count_0
    interpretation: Higher counts indicate more planning activity.
  technical:
    measure_name: Plans Count
    description: Counts planning cycles or plan versions in the period.
    depends_on_measures: []
    lineage:
    - fact_forecast.Forecast Version
    calculation:
      op: distinctcount
      column: Forecast Version
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
  standard_ref:
  - standard: SCOR-DS
    name: Plan volume (element)
    url: https://scor.ascm.org/performance/asset-management
    alignment: none
    note: Plan/version count is a Plan element, not a SCOR performance KPI.

- kpi_id: KPI-SCM-015
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
    unit_format: count_0
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
  standard_ref:
  - standard: SCOR-DS
    name: Shipment volume (element)
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: none
    note: Shipment count is a logistics volume element feeding delivery-reliability metrics (SCOR RL), not a standalone SCOR KPI.

- kpi_id: KPI-OPS-016
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
  good_is: higher
  business:
    purpose: Uptime share relative to planned production time.
    definition: Available time / Planned time
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: percent_1
    interpretation: Higher availability indicates less downtime; low values typically reflect maintenance or scheduling issues.
  technical:
    measure_name: Availability %
    description: Uptime share relative to planned production time.
    depends_on_measures: []
    lineage:
    - fact_ops.Run Time Minutes
    - fact_ops.Planned Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Run Time Minutes
      denominator:
        column: Planned Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    id: A
    name: Availability
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: ISO 22400-2 Availability = Actual Production Time / Planned Busy Time. Ours ('Available time / Planned time') is the same concept but the ISO time-state model (PBT, actual production time) must be pinned to align exactly.

- kpi_id: KPI-OPS-017
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
  good_is: lower
  business:
    purpose: Measures share of planned production time lost to downtime.
    definition: Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: percent_1
    interpretation: Lower is better; analyze downtime drivers and loss categories.
  technical:
    measure_name: Downtime %
    description: Measures share of planned production time lost to downtime.
    depends_on_measures: []
    lineage:
    - fact_ops.Downtime Minutes
    - fact_ops.Planned Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Downtime Minutes
      denominator:
        column: Planned Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    name: Down time element (Availability loss)
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: Downtime ratio is an availability-loss element in the ISO 22400-2 time model (down time within Planned Busy Time), not a standalone named KPI; it feeds Availability (A).

- kpi_id: KPI-OPS-018
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
  good_is: lower
  business:
    purpose: Measures unplanned downtime share of planned time.
    definition: Unplanned Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: percent_1
    interpretation: Lower is better; track reliability and maintenance effectiveness.
  technical:
    measure_name: Unplanned Downtime %
    description: Measures unplanned downtime share of planned time.
    depends_on_measures: []
    lineage:
    - fact_ops_failures.Downtime Minutes
    - fact_ops.Planned Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Downtime Minutes
      denominator:
        column: Planned Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    name: Unplanned down time (Availability loss)
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: Unplanned downtime is the failure/breakdown share of the ISO 22400-2 down-time element; feeds Availability (A) and the Six Big Losses breakdown category.

- kpi_id: KPI-OPS-019
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
  good_is: lower
  business:
    purpose: Isolates chronic speed reduction from intermittent minor stops.
    definition: Speed Loss = (1 - Performance Rate) adjusted to exclude minor stop events. Corresponds to Six Big Losses Category 4 (Reduced Speed).
    grain_scope: Line/shift aggregated to plant and period.
    unit_format: percent_1
    interpretation: Lower is better; speed losses are often misclassified as acceptable safety margin versus ISO ideal cycle time.
  technical:
    measure_name: Speed Loss Rate %
    description: Chronic speed reduction component of performance loss.
    depends_on_measures:
    - KPI-OPS-002
    lineage:
    - fact_ops.Actual Cycle Time
    - fact_ops.Ideal Cycle Time
    - fact_ops.Minor Stop Count
    calculation:
      op: hitl
      blocked_by: authoring
      reason: New-territory KPI — no legacy DAX counterpart to verify against (not in products/fabric/powerbi/dist/Operations.SemanticModel). "(1 - Performance Rate) adjusted to exclude minor stop events" is a residual/decomposition formula whose exact minor-stop adjustment isn't specified precisely enough to derive without guessing, and is beyond the current grammar regardless.
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: OEE Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - KPI-OPS-019 + minor_stops_contribution ≤ 1 - KPI-OPS-002
    version: v1.0
  metadata_quality:
    completeness_score: 0.7
    last_review: 01.06.2026
  standard_ref:
  - standard: ISO 22400-2
    id: E
    name: Effectiveness (speed) loss
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: Speed loss = 1 − performance rate is the ISO 22400-2 Effectiveness (E) loss / reduced-speed category of the Six Big Losses; report against E to align.

- kpi_id: KPI-OPS-020
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
  good_is: lower
  business:
    purpose: Measures time lost to product or format changeovers.
    definition: Average minutes from last good piece of previous run to first good piece of next run, including mechanical setup, parameter adjustment, and trial run waste. Directly drives Six Big Losses Category 2 (Setup & Adjustment).
    grain_scope: Changeover event level; aggregated by line and period.
    unit_format: minutes_1
    interpretation: Lower is better; SMED methodology targets < 10 minutes for high-mix lines.
  technical:
    measure_name: Changeover Time Minutes
    description: Average changeover duration per setup event.
    depends_on_measures: []
    lineage:
    - fact_ops_changeover.Start Timestamp
    - fact_ops_changeover.End Timestamp
    calculation:
      op: hitl
      blocked_by: authoring
      reason: New-territory KPI — no legacy DAX counterpart to verify against (not in products/fabric/powerbi/dist/Operations.SemanticModel). Average duration between two timestamp columns (AVERAGEX with a DATEDIFF-style row expression) is beyond the current sum/ratio/delta/count-shaped grammar.
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
  standard_ref:
  - standard: ISO 22400-2
    name: Setup/changeover time element
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: Changeover time maps to the ISO 22400-2 setup-time element (and Six Big Losses setup & adjustment category); it drives Availability loss but is a time element, not a ratio KPI.

- kpi_id: KPI-SCM-016
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
  good_is: higher
  business:
    purpose: Measures how often inventory is sold and replaced.
    definition: COGS / Average Inventory.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: ratio_1
    interpretation: Higher turnover indicates better inventory velocity; too high may risk stockouts.
  technical:
    measure_name: Inventory Turnover
    description: Measures how often inventory is sold and replaced.
    depends_on_measures: []
    lineage:
    - fact_cogs.COGS Amount
    - fact_inventory.Average Inventory Amount
    calculation:
      op: ratio
      numerator:
        column: COGS Amount
      denominator:
        column: Average Inventory Amount
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
  standard_ref:
  - standard: SCOR-DS
    id: AM.1.1
    name: Asset Management — inventory turns
    url: https://scor.ascm.org/performance/asset-management
    alignment: partial
    note: Inventory turnover (COGS / average inventory) is the reciprocal of the inventory-days input to SCOR Cash-to-Cash Cycle Time (AM.1.1); a SCOR Asset-Management metric, not ISO 22400-2. Consistent with KPI-SCM-001 / KPI-FIN-004.

- kpi_id: KPI-SCM-017
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
  good_is: lower
  business:
    purpose: Measures mean absolute percentage error in forecast.
    definition: Mean(|Forecast - Actual| / Actual).
    grain_scope: SKU/week; aggregated monthly.
    unit_format: percent_1
    interpretation: Lower is better; high MAPE indicates unstable demand or poor model fit.
  technical:
    measure_name: Forecast MAPE %
    description: Measures mean absolute percentage error in forecast.
    depends_on_measures: []
    lineage:
    - fact_forecast.ProductKey
    - fact_forecast.Forecast Units
    - fact_sales.Sales Units
    calculation:
      op: avgx_over_key
      key_column: ProductKey
      value:
        calc:
          op: ratio
          numerator:
            calc:
              op: abs
              value:
                calc:
                  op: delta
                  minuend:
                    column: Forecast Units
                  subtrahend:
                    column: Sales Units
          denominator:
            column: Sales Units
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
  standard_ref:
  - standard: SCOR-DS
    alignment: none
    note: As KPI-SCM-005 — no SCOR metric home; MAPE is defined by IBF/APICS forecasting standards, not SCOR.

- kpi_id: KPI-SCM-018
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
  good_is: higher
  business:
    purpose: Measures share of deliveries with complete quantities.
    definition: In-Full Deliveries / Total Deliveries.
    grain_scope: Delivery/day; aggregated weekly or monthly.
    unit_format: percent_1
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
  standard_ref:
  - standard: SCOR-DS
    id: RL.2.1
    name: Percentage of Orders Delivered In Full
    url: https://scor.ascm.org/performance/reliability/RL.1.1
    alignment: partial
    note: 'Grain differs: ours is delivery-level (in-full deliveries / total deliveries); SCOR RL.2.1 is order-level (% of orders delivered in full). Move to order grain to align.'

- kpi_id: KPI-GOV-001
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
  good_is: higher
  business:
    purpose: Measures share of actions that achieved the intended outcome.
    definition: Rows in fact_action_outcome with outcome_status = "achieved" divided by all rows in fact_action_outcome.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: percent_1
    interpretation: Higher values indicate better execution effectiveness.
  technical:
    measure_name: Action Outcome Rate %
    description: Measures share of actions that achieved the intended outcome.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.outcome_status
    calculation:
      op: ratio
      numerator:
        calc:
          op: count_filtered
          column: outcome_status
          filters:
          - column: outcome_status
            equals: achieved
      denominator:
        calc:
          op: count
          column: outcome_status
  governance:
    business_owner: Executive Office
    data_owner: PMO Analytics
    steward: PMO Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - 'Legacy carries two candidate formulas for this KPI id in Experience.SemanticModel: the canonical one used here (fact_action_outcome, lowercase "achieved", part of the actively-maintained Actions Executed/Avg Time-to-Outcome/Action ROI % sibling group) and an older ''Action Outcome Rate % (XD Log)'' variant (fact_action_log, "Achieved" capitalized) that has no surviving sibling measures — treated as a superseded duplicate, not the source of truth.'
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Action outcome rate
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: 'Action outcome rate (achieved / total action outcomes) is the ActionReady framework''s own action-governance construct — no external standard defines it. Conceptual backdrop: ISO 9001 continual improvement (Plan-Do-Check-Act) and Balanced Scorecard, but the metric is proprietary to the framework.'

- kpi_id: KPI-GOV-002
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
  good_is: higher
  business:
    purpose: Average EUR impact per achieved action execution — realized KPI delta per code.
    definition: Average impact_value across achieved rows in fact_action_outcome.
    grain_scope: Action instance; aggregated by period and domain.
    unit_format: eur_0
    interpretation: Higher values indicate stronger KPI improvement per action code execution.
  technical:
    measure_name: Action Effectiveness Delta
    description: Average EUR impact per achieved action execution.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.impact_value
    - fact_action_outcome.outcome_status
    calculation:
      op: avg_filtered
      column: impact_value
      filters:
      - column: outcome_status
        equals: achieved
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
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Action effectiveness delta
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: Average realised impact across achieved actions — the framework's own effectiveness measure. No external standard; PDCA/Balanced-Scorecard is the conceptual backdrop.

- kpi_id: KPI-GOV-003
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
    unit_format: count_0
    interpretation: Higher counts indicate more routed actions.
  technical:
    measure_name: Actions Routed Count
    description: Counts action codes routed for execution.
    depends_on_measures: []
    lineage:
    - fact_action_log
    calculation:
      op: count
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
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Actions routed (element)
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: Routed-action count is an operational element of the action-governance loop, not a named external KPI.

- kpi_id: KPI-COM-001
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
    unit_format: eur_0
    interpretation: Base for Price Realization %; required input for KPI-COM-003.
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
  standard_ref:
  - standard: IFRS 15
    name: List/catalogue price
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: none
    note: List price is a pre-discount catalogue figure — an input to discount/realization analysis, not an IFRS 15 figure (IFRS 15 measures the transaction price actually expected). No standard defines list price.

- kpi_id: KPI-COM-002
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
    unit_format: eur_0
    interpretation: Numerator for Price Realization %; required input for KPI-COM-003.
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
  standard_ref:
  - standard: IFRS 15
    name: Transaction price (net of discounts)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: partial
    note: Net price is the IFRS 15 transaction price after trade discounts and variable consideration. Aligns conceptually; ensure discounts/rebates follow IFRS 15 variable-consideration measurement rather than ad-hoc netting.

- kpi_id: KPI-COM-003
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
  good_is: higher
  business:
    purpose: Shows how much of list price is realized after discounts.
    definition: Net Price Amount / List Price Amount.
    grain_scope: Invoice line aggregated to reporting period.
    unit_format: percent_1
    interpretation: Values below 100% indicate discounting; values above 100% indicate uplift vs list price.
  technical:
    measure_name: Price Realization %
    description: Shows how much of list price is realized after discounts.
    depends_on_measures:
    - KPI-COM-001
    - KPI-COM-002
    lineage:
    - fact_sales.List Price Amount
    - fact_sales.Net Price Amount
    calculation:
      op: ratio
      numerator:
        kpi: KPI-COM-002
      denominator:
        kpi: KPI-COM-001
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
  standard_ref:
  - standard: IFRS 15
    name: Price realization (net/list)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: none
    note: Price realization (net/list) is a management pricing metric, not IFRS-defined. The discount it captures is IFRS 15 variable consideration, but the ratio itself is a commercial-analytics convention.

- kpi_id: KPI-COM-004
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
  good_is: higher
  business:
    purpose: Captures the residual effect from changes in product, channel, or region mix.
    definition: Total variance - Price Effect - Volume Effect.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: eur_0
    interpretation: Explains whether composition shifts drive positive or negative outcomes.
  technical:
    measure_name: Mix Effect Amount
    description: Captures the residual effect from changes in product, channel, or region mix.
    depends_on_measures:
    - KPI-COM-005
    - KPI-COM-010
    - KPI-COM-011
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Plan Sales Amount
    calculation:
      op: delta_chain
      minuend:
        kpi: KPI-COM-005
      subtrahends:
      - column: Plan Sales Amount
      - kpi: KPI-COM-010
      - kpi: KPI-COM-011
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
  standard_ref:
  - standard: Management accounting (CIMA/IMA)
    name: Sales mix variance (residual)
    alignment: partial
    note: Mix effect is the residual (total − price − volume) in the standard three-way variance decomposition. Its magnitude depends on the volume-effect basis (see sales.pvm.volume_effect) — a convention choice, not a governed standard.

- kpi_id: KPI-COM-005
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
  plan_kpi_ref: KPI-COM-006
  business:
    purpose: Total invoiced revenue net of discounts and returns.
    definition: Sum of all invoice line amounts net of VAT and returns.
    grain_scope: Invoice line.
    unit_format: eur_0
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
  standard_ref:
  - standard: IFRS 15
    name: Revenue from contracts with customers
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: partial
    note: 'Net sales is a presentation of IFRS 15 revenue: net of VAT (correctly excluded — amounts collected on behalf of third parties are not revenue) and net of returns (IFRS 15 variable consideration — recognise a refund liability, not revenue). Aligns when returns/rebates are treated as IFRS 15 variable consideration.'

- kpi_id: KPI-COM-006
  kpi_key: Plan Net Sales Amount
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
    purpose: Governed plan baseline for comparing actual Net Sales performance.
    definition: Sum of approved Plan Sales Amount at invoice-line planning grain.
    grain_scope: Invoice line and reporting period.
    unit_format: eur_0
    interpretation: Represents the approved Net Sales baseline; actual values above Plan are favorable, subject to margin guardrails.
  technical:
    measure_name: Plan Sales Amount
    description: Approved Net Sales plan baseline for commercial variance analysis.
    depends_on_measures: []
    lineage:
    - fact_sales.Plan Sales Amount
    calculation:
      op: sum
      column: Plan Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: annual
    validation_process: dual control
    qa_rules:
    - Reconciles to the approved commercial plan within +/- 0.1%.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 27.08.2026
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Approved Net Sales plan baseline
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: none
    note: The plan baseline is an internal management measure; IFRS 15 governs the comparable actual revenue, not the plan.

- kpi_id: KPI-COM-007
  kpi_key: Prior-Year Net Sales Amount
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
    purpose: Governed prior-year baseline for comparable Net Sales trend analysis.
    definition: Sum of Net Sales Amount for the corresponding prior-year reporting period.
    grain_scope: Invoice line and comparable reporting period.
    unit_format: eur_0
    interpretation: Provides the like-for-like prior-year revenue baseline; comparability adjustments must follow the reporting calendar.
  technical:
    measure_name: Last Year Net Sales Amount
    description: Comparable prior-year Net Sales baseline for commercial trend analysis.
    depends_on_measures:
    - KPI-COM-005
    lineage:
    - fact_sales.Last Year Sales Amount
    calculation:
      op: sum
      column: Last Year Sales Amount
  governance:
    business_owner: Head of Sales Controlling
    data_owner: Commercial BI
    steward: Sales Analyst
    review_cycle: quarterly
    validation_process: dual control
    qa_rules:
    - Reconciles to the corresponding prior-year Net Sales period within +/- 0.1%.
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 27.08.2026
  standard_ref:
  - standard: IFRS 15
    name: Prior-year revenue comparison baseline
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: partial
    note: The underlying Net Sales amount follows the governed IFRS 15-aligned revenue definition; the prior-year comparison itself is a management view.

- kpi_id: KPI-COM-008
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
  good_is: higher
  is_variance: true
  business:
    purpose: Relative variance of Net Sales vs Last Year.
    definition: (Net Sales - LY) / LY
    grain_scope: Aggregated to reporting period.
    unit_format: percent_1
    interpretation: Shows growth rate vs prior year.
  technical:
    measure_name: Delta% Net Sales
    description: Relative variance of Net Sales vs Last Year.
    depends_on_measures:
    - KPI-COM-005
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Last Year Sales Amount
    calculation:
      op: delta_pct
      minuend:
        kpi: KPI-COM-005
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
  standard_ref:
  - standard: IFRS 15
    name: Net sales YoY growth
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: none
    note: Year-over-year growth is a management trend metric; the underlying net-sales base is IFRS 15 revenue but the growth ratio is not standard-defined.

- kpi_id: KPI-COM-009
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
  good_is: higher
  is_variance: true
  business:
    purpose: Relative variance of Net Sales vs Plan.
    definition: (Net Sales Amount - Plan Sales Amount) / Plan Sales Amount
    grain_scope: Aggregated to reporting period.
    unit_format: percent_1
    interpretation: Positive values indicate outperformance vs plan; negative values indicate shortfall.
  technical:
    measure_name: Net Sales % vs Plan
    description: Relative variance of Net Sales vs Plan.
    depends_on_measures:
    - KPI-COM-005
    lineage:
    - fact_sales.Plan Sales Amount
    calculation:
      op: delta_pct
      minuend:
        kpi: KPI-COM-005
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
  standard_ref:
  - standard: IFRS 15
    name: Net sales vs plan variance
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: none
    note: Net-sales-vs-plan is an internal budget-variance metric; the actual base is IFRS 15 revenue, the variance is convention.

- kpi_id: KPI-COM-010
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
  good_is: higher
  business:
    purpose: Quantifies the pure price impact in the PVM bridge.
    definition: (Actual Price - Plan Price) x Actual Quantity.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: eur_0
    interpretation: Positive values indicate price gains; negative values represent price pressure.
  technical:
    measure_name: Price Effect Amount
    description: Quantifies the pure price impact in the PVM bridge.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Plan Quantity
    - fact_sales.Plan Sales Amount
    - fact_sales.Quantity
    calculation:
      op: pvm_price_effect
      net_price: Net Sales Amount
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
  standard_ref:
  - standard: Management accounting (CIMA/IMA)
    name: Sales price variance
    alignment: partial
    note: Price effect follows the managerial-accounting sales-price-variance convention (CIMA Official Terminology; IMA Statements on Management Accounting) — not a governed ISO/IFRS standard. Our formula (Δprice × actual quantity) is the standard convention; label it management-accounting variance analysis, not a financial-reporting standard.

- kpi_id: KPI-COM-011
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
  good_is: higher
  business:
    purpose: Measures the variance caused purely by quantity changes at plan price.
    definition: (Actual Quantity - Plan Quantity) x Plan Price.
    grain_scope: Aggregated to reporting period / segment.
    unit_format: eur_0
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
  standard_ref:
  - standard: Management accounting (CIMA/IMA)
    name: Sales volume variance
    alignment: partial
    note: 'Volume effect follows the sales-volume-variance convention. NOTE a real definitional variant: per-row (Δqty × plan unit price) collapses mix to zero, whereas the blended-plan-price basis makes mix material — pin which convention is used so price+volume+mix reconcile to total variance.'

- kpi_id: KPI-COM-012
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
    unit_format: units_0
    interpretation: Higher values indicate higher volume sold.
  technical:
    measure_name: Sales Units
    description: Measures sold units volume in the period.
    depends_on_measures: []
    lineage:
    - fact_sales.Sales Units
    calculation:
      op: sum
      column: Sales Units
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
  standard_ref:
  - standard: IFRS 15
    name: Sales volume (units)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
    alignment: none
    note: Sold units is a volume element underlying revenue; not an IFRS 15 figure itself (IFRS 15 measures the consideration, not the count).

- kpi_id: KPI-SVC-002
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
  good_is: higher
  business:
    purpose: Measure how much of all eligible process transactions are executed via digital tools instead of manual channels.
    definition: Digital Transactions Count / Total Transactions Count for eligible processes.
    grain_scope: Process area / org; aggregated monthly or quarterly.
    unit_format: percent_1
    interpretation: Higher values indicate greater adoption of digital processes; low values show manual work and automation potential.
  technical:
    measure_name: Digital Adoption Rate %
    description: Measure how much of all eligible process transactions are executed via digital tools instead of manual channels.
    depends_on_measures: []
    lineage: []
    calculation:
      op: hitl
      blocked_by: data_contract
      reason: 'Legacy system itself has no real formula here: products/fabric/powerbi/dist/Experience.SemanticModel''s own DAX is a documented placeholder (VAR _pending = "Requires fact_it Digital Users and fact_hr Total Headcount (not yet in data contracts)" RETURN BLANK()) — the source tables/columns do not exist yet in the data contract, upstream of any DSL grammar question.'
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
  standard_ref:
  - standard: ISO 30414
    name: (digital adoption — change management)
    url: https://www.iso.org/standard/69338.html
    alignment: none
    note: Digital adoption (digital / total transactions for eligible processes) is a digital-transformation / change-management metric, not part of ISO 30414's human-capital areas. No governing HR standard; loosely relates to ISO 30414 workforce skills & capabilities.

- kpi_id: KPI-SVC-003
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
  good_is: lower
  business:
    purpose: Monitor risk of employee attrition across key roles and segments.
    definition: Probability of attrition for the selected population in the period.
    grain_scope: Org/role/segment; monthly.
    unit_format: percent_1
    interpretation: Higher values signal retention risk and require targeted actions.
  technical:
    measure_name: Attrition Risk %
    description: Probability of employee attrition
    depends_on_measures: []
    lineage: []
    calculation:
      op: hitl
      blocked_by: data_contract
      reason: 'Legacy system itself has no real formula here: products/fabric/powerbi/dist/Experience.SemanticModel''s own DAX is a documented placeholder (VAR _pending = "Requires predictive attrition model output table (not yet in data contracts)" RETURN BLANK()) — the source table does not exist yet in the data contract, upstream of any DSL grammar question.'
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
  standard_ref:
  - standard: ISO 30414
    name: Human capital — turnover / retention
    url: https://www.iso.org/standard/69338.html
    alignment: partial
    note: ISO 30414:2018 (human capital reporting) defines turnover and retention-rate metrics. Attrition RISK here is a predicted probability — a modelling variant of the ISO turnover family; align the realised-turnover base to ISO 30414 and treat the risk score as a forward-looking overlay.

- kpi_id: KPI-FIN-001
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
  good_is: lower
  business:
    purpose: Measures days sales outstanding for receivables.
    definition: Receivables / (Net Sales / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days_0
    interpretation: Lower is better; rising DSO indicates collection issues.
  technical:
    measure_name: DSO Days
    description: Measures days sales outstanding for receivables.
    depends_on_measures: []
    lineage:
    - dim_date.CalendarYearMonth
    - fact_accounts_receivable.AR Amount
    - fact_accounts_receivable.Revenue Amount
    calculation:
      op: ratio
      numerator:
        calc:
          op: mul
          terms:
          - calc:
              op: avgx_over_key
              key_column: CalendarYearMonth
              value:
                column: AR Amount
          - literal: 365
      denominator:
        calc:
          op: mul
          terms:
          - calc:
              op: avgx_over_key
              key_column: CalendarYearMonth
              value:
                column: Revenue Amount
          - literal: 12
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
  standard_ref:
  - standard: SCOR-DS
    id: AM.1.1
    name: Cash-to-Cash Cycle Time — DSO component
    url: https://scor.ascm.org/performance/asset-management
    alignment: partial
    note: Days Sales Outstanding is the receivables-days input of SCOR Cash-to-Cash Cycle Time (AM.1.1 = DSO + Inventory Days − DPO). Not an IFRS line item; the receivables base is IFRS 9 / IAS 1.

- kpi_id: KPI-FIN-002
  kpi_key: Inventory Amount
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-001
  - OPS-002
  action_code_ref:
  - O-A2.5
  calc_type: amount
  good_is: lower
  business:
    purpose: Provide closing inventory value for working capital and liquidity metrics.
    definition: Inventory value at period end at reporting valuation (e.g., standard or average cost).
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: eur_2
    interpretation: Higher values increase working capital needs; validate against seasonality and service targets.
  technical:
    measure_name: Inventory Amount
    description: Inventory value at period end
    depends_on_measures: []
    lineage:
    - fact_inventory.Average Inventory Amount
    calculation:
      op: sum
      column: Average Inventory Amount
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
  standard_ref:
  - standard: IFRS
    id: IAS 2
    name: Inventories carrying amount
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
    alignment: exact
    note: Closing inventory measured at the lower of cost and net realisable value (IAS 2). Our note allows 'standard or average cost' — IAS 2 prohibits LIFO; confirm the cost formula is FIFO or weighted-average and standard cost approximates actual.

- kpi_id: KPI-FIN-003
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
    unit_format: eur_2
    interpretation: Higher balances increase working capital funding but can signal payment delays; compare to terms.
  technical:
    measure_name: Payables Amount
    description: Accounts payable balance at period end
    depends_on_measures: []
    lineage:
    - fact_accounts_payable.AP Amount
    calculation:
      op: sum
      column: AP Amount
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
  standard_ref:
  - standard: IFRS
    id: IAS 1
    name: Trade and other payables
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-1-presentation-of-financial-statements/
    alignment: partial
    note: Trade payables are an IAS 1 statement-of-financial-position line (a financial liability under IFRS 9). Aligns for trade payables; ensure non-trade accruals/provisions are excluded when this feeds DPO.

- kpi_id: KPI-SCM-019
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
    unit_format: hours_0
    interpretation: Capacity baseline for utilization and downtime; compare with actual runtime and downtime.
  technical:
    measure_name: Planned Hours
    description: Scheduled production time for machines/lines
    depends_on_measures: []
    lineage:
    - fact_ops.Planned Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Planned Time Minutes
      denominator:
        literal: 60
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
  standard_ref:
  - standard: ISO 22400-2
    name: Planned busy time (PBT element)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Planned production hours is the ISO 22400-2 Planned Busy Time element (denominator of Availability), an input rather than a KPI.

- kpi_id: KPI-FIN-004
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
  good_is: lower
  business:
    purpose: Measures days inventory outstanding.
    definition: Inventory / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days_0
    interpretation: Lower is better; high DIO increases cash tied up in stock.
  technical:
    measure_name: DIO Days
    description: Measures days inventory outstanding.
    depends_on_measures: []
    lineage:
    - dim_date.CalendarYearMonth
    - fact_inventory.Average Inventory Amount
    - fact_accounts_payable.COGS Amount
    calculation:
      op: ratio
      numerator:
        calc:
          op: mul
          terms:
          - calc:
              op: avgx_over_key
              key_column: CalendarYearMonth
              value:
                column: Average Inventory Amount
          - literal: 365
      denominator:
        calc:
          op: mul
          terms:
          - calc:
              op: avgx_over_key
              key_column: CalendarYearMonth
              value:
                column: COGS Amount
          - literal: 12
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
  standard_ref:
  - standard: SCOR-DS
    id: AM.1.1
    name: Cash-to-Cash Cycle Time — inventory-days component
    url: https://scor.ascm.org/performance/asset-management
    alignment: partial
    note: Twin of KPI-SCM-001 (same formula, company/segment grain vs SKU/location); both map to the SCOR inventory-days / Cash-to-Cash (AM.1.1) family and both are kept (D-594, 30.09.2026).

- kpi_id: KPI-FIN-005
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
  good_is: higher
  business:
    purpose: Measures days payables outstanding.
    definition: Payables / (COGS / 365).
    grain_scope: Company/segment; monthly close.
    unit_format: days_0
    interpretation: Higher values improve cash but may impact supplier terms.
  technical:
    measure_name: DPO Days
    description: Measures days payables outstanding.
    depends_on_measures: []
    lineage:
    - dim_date.CalendarYearMonth
    - fact_accounts_payable.AP Amount
    - fact_accounts_payable.COGS Amount
    calculation:
      op: ratio
      numerator:
        calc:
          op: mul
          terms:
          - calc:
              op: avgx_over_key
              key_column: CalendarYearMonth
              value:
                column: AP Amount
          - literal: 365
      denominator:
        calc:
          op: mul
          terms:
          - calc:
              op: avgx_over_key
              key_column: CalendarYearMonth
              value:
                column: COGS Amount
          - literal: 12
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
  standard_ref:
  - standard: SCOR-DS
    id: AM.1.1
    name: Cash-to-Cash Cycle Time — DPO component
    url: https://scor.ascm.org/performance/asset-management
    alignment: partial
    note: Days Payables Outstanding is the payables-days input of SCOR Cash-to-Cash Cycle Time (AM.1.1). Not an IFRS line item; the payables base is IAS 1 / IFRS 9.

- kpi_id: KPI-FIN-006
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
  good_is: lower
  business:
    purpose: Measures cash conversion cycle length.
    definition: DSO + DIO - DPO.
    grain_scope: Company/segment; monthly close.
    unit_format: days_0
    interpretation: Lower values indicate faster cash recovery.
  technical:
    measure_name: CCC Days
    description: Measures cash conversion cycle length.
    depends_on_measures:
    - KPI-FIN-001
    - KPI-FIN-004
    - KPI-FIN-005
    lineage:
    - dim_date.CalendarYearMonth
    - fact_accounts_receivable.AR Amount
    - fact_accounts_receivable.Revenue Amount
    - fact_inventory.Average Inventory Amount
    - fact_accounts_payable.AP Amount
    - fact_accounts_payable.COGS Amount
    calculation:
      op: delta
      minuend:
        calc:
          op: add
          terms:
          - kpi: KPI-FIN-001
          - kpi: KPI-FIN-004
      subtrahend:
        kpi: KPI-FIN-005
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
  standard_ref:
  - standard: SCOR-DS
    id: AM.1.1
    name: Cash-to-Cash Cycle Time
    url: https://scor.ascm.org/performance/asset-management
    alignment: exact
    note: CCC (DSO + DIO − DPO) is definitionally SCOR AM.1.1 Cash-to-Cash Cycle Time — a cross-domain finance↔supply-chain metric with no single IFRS equivalent. The fixed-ratio proxy twin was removed (D-594, 30.09.2026).

- kpi_id: KPI-FIN-007
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
  good_is: higher
  business:
    purpose: Tracks cash and cash equivalents at period end.
    definition: Cash and cash equivalents balance.
    grain_scope: Company/segment; monthly close.
    unit_format: eur_0
    interpretation: Higher balance improves liquidity buffer; consider seasonality and debt strategy.
  technical:
    measure_name: Cash Balance
    description: Tracks cash and cash equivalents at period end.
    depends_on_measures: []
    lineage:
    - dim_date.Date
    - fact_cash_position.Cash Balance Amount
    calculation:
      op: last_nonblank_over_key
      key_column: Date
      value:
        column: Cash Balance Amount
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
  standard_ref:
  - standard: IFRS
    id: IAS 7
    name: Cash and cash equivalents
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/
    alignment: exact
    note: Cash and cash equivalents is defined by IAS 7.6–9 (short-term, highly liquid, insignificant risk of value change, typically ≤3-month maturity). Ensure scope matches the IAS 7 definition, not a broader treasury balance.

- kpi_id: KPI-FIN-008
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
  good_is: lower
  business:
    purpose: Measures the proportion of accounts receivable past due date.
    definition: Overdue AR (past due date) / Total AR × 100. Customer-level overdue analysis enables targeted collection.
    grain_scope: Customer/entity level; aggregated monthly.
    unit_format: percent_1
    interpretation: Higher overdue AR directly increases DSO. Values > 15 % signal systemic collection issues.
  technical:
    measure_name: Overdue AR %
    description: Share of accounts receivable past due date.
    depends_on_measures: []
    lineage:
    - fact_ar.Overdue Amount
    - fact_ar.Total AR Amount
    calculation:
      op: ratio
      numerator:
        column: Overdue Amount
      denominator:
        column: Total AR Amount
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
  standard_ref:
  - standard: IFRS
    id: IFRS 9
    name: Trade receivables — credit-risk ageing
    url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/
    alignment: partial
    note: Overdue-AR ageing underpins the IFRS 9 expected-credit-loss simplified (provision-matrix) approach, but the overdue-% itself is a credit-management KPI, not an IFRS-defined figure. Receivables base per IFRS 9 / IAS 1.

- kpi_id: KPI-FIN-009
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
  good_is: higher
  business:
    purpose: Measures cash generated by operating activities.
    definition: Net cash flows from operations for the period.
    grain_scope: Company/segment; monthly close.
    unit_format: eur_2
    interpretation: Positive values improve liquidity; negative values require investigation.
  technical:
    measure_name: Operating Cash Flow
    description: Measures cash generated by operating activities.
    depends_on_measures: []
    lineage:
    - fact_cash_flow.Operating Cash Flow Amount
    calculation:
      op: sum
      column: Operating Cash Flow Amount
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
  standard_ref:
  - standard: IFRS
    id: IAS 7
    name: Cash flows from operating activities
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/
    alignment: exact
    note: Maps to the IAS 7 operating-activities cash-flow section. Aligns; IAS 7 permits the direct or indirect method — pin which one is used so period-over-period comparisons are stable.

- kpi_id: KPI-FIN-010
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
  good_is: higher
  is_variance: true
  business:
    purpose: Measures deviation of cash balance versus plan.
    definition: (Cash Balance - Cash Plan) / Cash Plan.
    grain_scope: Company/segment; monthly close.
    unit_format: percent_1
    interpretation: Positive values indicate higher cash than planned.
  technical:
    measure_name: Cash vs Plan %
    description: Measures deviation of cash balance versus plan.
    depends_on_measures: []
    lineage:
    - fact_cash_position.Cash Balance Amount
    - fact_cash_position.Plan Cash Amount
    calculation:
      op: ratio
      numerator:
        calc:
          op: delta
          minuend:
            column: Cash Balance Amount
          subtrahend:
            column: Plan Cash Amount
      denominator:
        column: Plan Cash Amount
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
  standard_ref:
  - standard: IFRS
    id: IAS 7
    name: Cash budget variance
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/
    alignment: none
    note: Internal budget-variance metric; no external standard defines it. Cash input traces to IAS 7 cash and cash equivalents.

- kpi_id: KPI-FIN-011
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
    unit_format: eur_0
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
  standard_ref:
  - standard: IFRS
    id: IAS 2
    name: Inventories — cost of sales
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
    alignment: exact
    note: COGS is the IAS 2 carrying amount of inventories recognised as an expense when the related revenue is recognised (IAS 2.34), presented as 'cost of sales' under the IAS 1 function-of-expense method. Definition aligns.

- kpi_id: KPI-COM-013
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
  plan_variance_kpi_ref: KPI-FIN-017
  synonyms:
  - GM%
  - Gross Margin Rate
  - Bruttomarge %
  example_question: Why did Gross Margin % drop in Region North last quarter?
  causal_links:
    model_type: local_linear_beta
    as_of: '2026-02-01'
    links:
    - influencing_kpi_id: KPI-COM-005
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
        standardized: ΔKPI-COM-013 = 0.000002 * ΔKPI-COM-005
        latex: \Delta GM = 0.000002 \cdot \Delta NetSales
    - influencing_kpi_id: KPI-FIN-011
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
        standardized: ΔKPI-COM-013 = -0.000002 * ΔKPI-FIN-011
        latex: \Delta GM = -0.000002 \cdot \Delta COGS
    - influencing_kpi_id: KPI-COM-009
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
        standardized: ΔKPI-COM-013 = 0.3 * ΔKPI-COM-009
        latex: \Delta GM = 0.3 \cdot \Delta NetSales_{vsPlan}
    - influencing_kpi_id: KPI-COM-008
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
        standardized: ΔKPI-COM-013 = 0.25 * ΔKPI-COM-008
        latex: \Delta GM = 0.25 \cdot \Delta NetSales_{vsLY}
    - influencing_kpi_id: KPI-COM-010
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
        standardized: ΔKPI-COM-013 = 0.000003 * ΔKPI-COM-010
        latex: \Delta GM = 0.000003 \cdot \Delta PVM_{price}
    - influencing_kpi_id: KPI-COM-011
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
        standardized: ΔKPI-COM-013 = 0.000001 * ΔKPI-COM-011
        latex: \Delta GM = 0.000001 \cdot \Delta PVM_{volume}
    - influencing_kpi_id: KPI-COM-004
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
        standardized: ΔKPI-COM-013 = 0.000002 * ΔKPI-COM-004
        latex: \Delta GM = 0.000002 \cdot \Delta PVM_{mix}
    - influencing_kpi_id: KPI-COM-003
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
        standardized: ΔKPI-COM-013(pp)=0.8*ΔKPI-COM-003(pp)
        latex: \\Delta GM_{pp} = 0.8 \\cdot \\Delta PR_{pp}
    - influencing_kpi_id: KPI-COM-019
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
        standardized: ΔKPI-COM-013 = 0.000002 * ΔKPI-COM-019
        latex: \Delta GM = 0.000002 \cdot \Delta GM_{amount}
    - influencing_kpi_id: KPI-COM-001
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
        standardized: ΔKPI-COM-013 = 0.000001 * ΔKPI-COM-001
        latex: \Delta GM = 0.000001 \cdot \Delta Price_{list}
    - influencing_kpi_id: KPI-COM-002
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
        standardized: ΔKPI-COM-013 = 0.000002 * ΔKPI-COM-002
        latex: \Delta GM = 0.000002 \cdot \Delta Price_{net}
    - influencing_kpi_id: KPI-FIN-013
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
        standardized: ΔKPI-COM-013 = -0.15 * ΔKPI-FIN-013
        latex: \Delta GM = -0.15 \cdot \Delta COGS_{unit}
    - influencing_kpi_id: KPI-FIN-017
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
        standardized: ΔKPI-COM-013 = 0.9 * ΔKPI-FIN-017
        latex: \Delta GM = 0.9 \cdot \Delta GM_{vsPlan}
  business:
    purpose: Gross margin % for commercial/operational reporting and strategic P&L reconciliation.
    definition: (Net Sales Amount - COGS Amount) / Net Sales Amount
    grain_scope: Invoice line aggregated to reporting period, org, customer or product segments.
    unit_format: percent_1
    interpretation: Values above 0 % indicate positive gross profit; trend over time shows structural profitability changes. Used for both operational management reporting and P&L reconciliation.
  technical:
    measure_name: Gross Margin %
    description: Gross Margin % used in commercial and management reporting and P&L reconciliation.
    depends_on_measures:
    - KPI-COM-005
    - KPI-FIN-011
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
    calculation:
      op: ratio
      numerator:
        kpi: KPI-COM-019
      denominator:
        kpi: KPI-COM-005
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
  standard_ref:
  - standard: ESMA-APM
    name: Gross margin ratio (APM)
    url: https://www.esma.europa.eu/document/esma-guidelines-alternative-performance-measures-apms
    alignment: partial
    note: A ratio of two IFRS figures (IFRS 15 revenue, IAS 2 cost of sales); the percentage itself is a non-GAAP APM. Inputs are IFRS-clean — label the ratio as an APM in external reporting.

- kpi_id: KPI-COM-014
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
    unit_format: eur_0
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
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Trade-promotion spend
    alignment: none
    note: Promo cost / trade spend is a TPM concept, not an external-standard figure (though under IFRS 15 certain trade spend is a reduction of revenue rather than an expense — check classification).

- kpi_id: KPI-COM-015
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
    unit_format: eur_0
    interpretation: Input to Promo ROI %.
  technical:
    measure_name: Incremental Gross Margin Amount
    description: Incremental gross margin from promo.
    depends_on_measures:
    - KPI-COM-021
    - KPI-COM-019
    - KPI-COM-005
    - KPI-COM-014
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
          - kpi: KPI-COM-021
          - calc:
              op: ratio
              numerator:
                kpi: KPI-COM-019
              denominator:
                kpi: KPI-COM-005
      subtrahend:
        kpi: KPI-COM-014
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
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Promo incremental gross margin
    alignment: none
    note: Incremental promo GM is a TPM metric; the GM base ties to IFRS 15 revenue / IAS 2 COGS, but the incremental construct itself is convention, not a standard.

- kpi_id: KPI-COM-016
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
  good_is: higher
  business:
    purpose: Measures profitability of promotions relative to spend.
    definition: Incremental GM Amount / Promo Cost Amount
    grain_scope: Promo campaign / product / period.
    unit_format: percent_1
    interpretation: Values > 0 indicate promotions adding value.
  technical:
    measure_name: Promo ROI %
    description: Measures profitability of promotions relative to spend.
    depends_on_measures:
    - KPI-COM-015
    - KPI-COM-014
    lineage:
    - fact_promo.Promo Cost
    calculation:
      op: ratio
      numerator:
        kpi: KPI-COM-015
      denominator:
        kpi: KPI-COM-014
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
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Promo ROI
    alignment: none
    note: Promo ROI (incremental GM / promo cost) is a TPM convention; no governing standard.

- kpi_id: KPI-FIN-012
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
    definition: Incremental Gross Margin Amount / Incremental Sales Amount
    grain_scope: Promo period/product
    unit_format: percent_1
    interpretation: Profitability of promotions.
  technical:
    measure_name: GM % During Promo
    description: Gross margin rate during promo periods.
    depends_on_measures:
    - KPI-COM-015
    - KPI-COM-021
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
    - fact_sales.Promo Flag
    calculation:
      op: ratio
      numerator:
        kpi: KPI-COM-015
      denominator:
        kpi: KPI-COM-021
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
  standard_ref:
  - standard: ESMA-APM
    name: Promo gross-margin ratio
    url: https://www.esma.europa.eu/document/esma-guidelines-alternative-performance-measures-apms
    alignment: none
    note: Internal commercial / trade-promotion metric (incremental GM during promo); not an IFRS or ESMA-named measure. Treated as an internal analytic ratio.

- kpi_id: KPI-FIN-013
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
  good_is: lower
  business:
    purpose: Shows unit cost level relative to sold volume.
    definition: COGS Amount / Units Sold.
    grain_scope: Product / period.
    unit_format: eur_per_unit_0
    interpretation: Lower is better; rising unit cost erodes margin.
  technical:
    measure_name: COGS per Unit
    description: Shows unit cost level relative to sold volume.
    depends_on_measures:
    - KPI-FIN-011
    lineage:
    - fact_sales.Quantity
    calculation:
      op: ratio
      numerator:
        kpi: KPI-FIN-011
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
  standard_ref:
  - standard: IFRS
    id: IAS 2
    name: Unit COGS (cost accounting)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
    alignment: none
    note: Internal cost-accounting metric; the COGS input is IAS 2 cost of sales but per-unit COGS is not an IFRS-defined figure.

- kpi_id: KPI-COM-017
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
  good_is: lower
  business:
    purpose: Sales lost on non-promoted items versus baseline (cannibalization in value).
    definition: 'Proxy: 15% of Baseline Sales Amount, pending real non-promo-segment actuals (target formula: MAX(0, Baseline Non-Promo Sales - Actual Non-Promo Sales) once that segmentation is available).'
    grain_scope: Promo campaign / product / period.
    unit_format: eur_0
    interpretation: Numerator for Cannibalization %; higher means more cannibalization.
  technical:
    measure_name: Cannibalized Sales Amount
    description: Sales amount lost on non-promoted items versus baseline (15% proxy factor).
    depends_on_measures:
    - KPI-COM-020
    lineage:
    - fact_promo.Baseline Sales Amount
    calculation:
      op: mul
      terms:
      - kpi: KPI-COM-020
      - literal: 0.15
  governance:
    business_owner: Head of Marketing Controlling
    data_owner: BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Documented proxy (15% of baseline) — replace with real non-promo actuals once segmentation data is available
    version: v1.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Cannibalized sales (proxy)
    alignment: none
    note: Cannibalized sales is a TPM concept, here a documented 15%-of-baseline proxy pending non-promo-segment actuals — a convention, not a standard.

- kpi_id: KPI-COM-018
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
  good_is: lower
  business:
    purpose: Measures share of promo uplift offset by decline in non-promoted sales.
    definition: Cannibalized Sales / Promo Uplift Sales.
    grain_scope: Promo campaign / product / period.
    unit_format: percent_1
    interpretation: Lower is better; high cannibalization reduces net gain.
  technical:
    measure_name: Cannibalization %
    description: Measures share of promo uplift offset by decline in non-promoted sales.
    depends_on_measures:
    - KPI-COM-021
    - KPI-COM-017
    lineage:
    - fact_promo.Baseline Non-Promo Sales Amount
    - fact_sales.Net Sales Amount
    - fact_sales.Promo Flag
    calculation:
      op: ratio
      numerator:
        kpi: KPI-COM-017
      denominator:
        kpi: KPI-COM-021
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
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Promo cannibalization
    alignment: none
    note: Cannibalization (cannibalized / uplift sales) is a TPM analytics concept, not standard-defined.

- kpi_id: KPI-SCM-020
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
  good_is: lower
  business:
    purpose: Shows material cost share of net sales.
    definition: Material Cost Amount / Net Sales Amount.
    grain_scope: Company/segment; monthly close.
    unit_format: percent_1
    interpretation: Lower is better; increases indicate supplier or price pressure.
  technical:
    measure_name: Material Cost %
    description: Shows material cost share of net sales.
    depends_on_measures:
    - KPI-COM-005
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
  standard_ref:
  - standard: IFRS
    id: IAS 2
    name: Material-cost ratio
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
    alignment: none
    note: Management cost-structure ratio (material cost share of sales); not an IFRS-defined figure. Material cost is an IAS 2 inventory cost input.

- kpi_id: KPI-FIN-014
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
  good_is: lower
  is_variance: true
  business:
    purpose: Measures OpEx variance versus plan.
    definition: (OpEx Amount - OpEx Plan Amount) / OpEx Plan Amount.
    grain_scope: Company/segment; monthly close.
    unit_format: percent_1
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
  standard_ref:
  - standard: IFRS
    id: IAS 1
    name: Operating-expense budget variance
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-1-presentation-of-financial-statements/
    alignment: none
    note: Internal budget-variance management metric; no external financial-reporting standard defines it. Actual and plan inputs trace to IAS 1 operating expenses.

- kpi_id: KPI-FIN-015
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
  good_is: lower
  business:
    purpose: Measures total cost per unit produced or sold.
    definition: Total Cost Amount / Units Produced or Sold.
    grain_scope: Product / period.
    unit_format: eur_per_unit_0
    interpretation: Lower is better; used to track cost efficiency.
  technical:
    measure_name: Unit Cost Amount
    description: Measures total cost per unit produced or sold.
    depends_on_measures:
    - KPI-FIN-016
    - KPI-FIN-014
    - KPI-SCM-020
    - KPI-OPS-004
    - KPI-OPS-009
    - KPI-QUA-006
    - KPI-OPS-003
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
  standard_ref:
  - standard: IFRS
    id: IAS 2
    name: Unit cost (cost accounting)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
    alignment: none
    note: Internal cost-accounting metric (total cost / units); no external financial-reporting standard. Cost inputs relate to IAS 2 inventory costing.

- kpi_id: KPI-COM-019
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
    unit_format: eur_0
    interpretation: Explains profitability magnitude before OpEx.
  technical:
    measure_name: Gross Margin Amount
    description: Absolute gross margin in currency.
    depends_on_measures:
    - KPI-COM-005
    - KPI-FIN-011
    lineage:
    - fact_sales.Cost of Goods Sold Amount
    - fact_sales.Net Sales Amount
    calculation:
      op: delta
      minuend:
        kpi: KPI-COM-005
      subtrahend:
        kpi: KPI-FIN-011
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
  standard_ref:
  - standard: IFRS
    id: IAS 1
    name: Gross profit subtotal
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-1-presentation-of-financial-statements/
    alignment: partial
    note: Gross profit (Revenue − Cost of sales) is an illustrative IAS 1 by-function subtotal, not a mandated line item. Aligns when Net Sales = IFRS 15 revenue and COGS = IAS 2 cost of sales. IFRS 18 (eff. 1 Jan 2027) formalises defined operating subtotals.

- kpi_id: KPI-COM-020
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
    unit_format: eur_0
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
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Promo baseline sales
    alignment: none
    note: Baseline (non-promoted) sales is a trade-promotion-management analytics concept (uplift modelling), not defined by any external standard.

- kpi_id: KPI-COM-021
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
    unit_format: eur_0
    interpretation: Input to promo ROI.
  technical:
    measure_name: Incremental Sales Amount
    description: Additional sales due to promotion.
    depends_on_measures:
    - KPI-COM-005
    - KPI-COM-020
    lineage:
    - fact_promo.Baseline Sales Amount
    - fact_sales.Net Sales Amount
    calculation:
      op: delta
      minuend:
        kpi: KPI-COM-005
      subtrahend:
        kpi: KPI-COM-020
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
  standard_ref:
  - standard: Trade Promotion Management (convention)
    name: Promo incremental/uplift sales
    alignment: none
    note: Incremental (promo − baseline) uplift is a TPM convention; no governing standard.

- kpi_id: KPI-FIN-016
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
  good_is: lower
  business:
    purpose: Shows cost share relative to net sales.
    definition: COGS Amount / Net Sales Amount.
    grain_scope: Invoice line aggregated to period.
    unit_format: percent_1
    interpretation: Lower is better; complements gross margin %.
  technical:
    measure_name: COGS % of Sales
    description: Shows cost share relative to net sales.
    depends_on_measures:
    - KPI-COM-005
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
  standard_ref:
  - standard: ESMA-APM
    name: Cost-of-sales ratio (APM)
    url: https://www.esma.europa.eu/document/esma-guidelines-alternative-performance-measures-apms
    alignment: partial
    note: Inverse of the gross-margin ratio; same APM treatment. Inputs are IFRS (IAS 2 cost of sales / IFRS 15 revenue).

- kpi_id: KPI-FIN-017
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
  good_is: higher
  is_variance: true
  business:
    purpose: Measures gross margin rate variance versus plan.
    definition: (Gross Margin % - Plan Gross Margin %) / Plan Gross Margin %.
    grain_scope: Company/segment; monthly.
    unit_format: percent_1
    interpretation: Positive values indicate better-than-plan margin.
  technical:
    measure_name: Gross Margin % vs Plan
    description: Measures gross margin rate variance versus plan.
    depends_on_measures:
    - KPI-COM-019
    lineage:
    - fact_sales.Plan Sales Amount
    - fact_sales.Plan COGS Amount
    calculation:
      op: delta_pct
      minuend:
        kpi: KPI-COM-019
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
  standard_ref:
  - standard: IFRS
    id: IAS 1
    name: Gross-margin budget variance
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-1-presentation-of-financial-statements/
    alignment: none
    note: Internal budget-variance metric; no external standard. Inputs trace to IAS 1 gross profit / IFRS 15 revenue.

- kpi_id: KPI-FIN-018
  kpi_key: EBITDA Margin
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref: []
  action_code_ref: []
  calc_type: ratio
  good_is: higher
  business:
    purpose: EBITDA profitability relative to net sales for P&L reporting.
    definition: EBITDA Amount / Net Sales Amount
    grain_scope: Entity-month; finance reporting.
    unit_format: percent_1
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
  standard_ref:
  - standard: ESMA-APM
    name: EBITDA margin — Alternative Performance Measure
    url: https://www.esma.europa.eu/document/esma-guidelines-alternative-performance-measures-apms
    alignment: none
    note: 'EBITDA is NOT defined by IFRS. It is an Alternative Performance Measure: under the ESMA APM Guidelines it must be labelled as non-GAAP, reconciled to the most directly reconcilable IFRS line item, and shown with a comparative. Under IFRS 18 (eff. 1 Jan 2027) an EBITDA-type figure used in public communication is a Management-defined Performance Measure (MPM) requiring a dedicated reconciliation note to the nearest IFRS subtotal — IFRS 18''s closest defined analogue is OPDAI (''operating profit before depreciation, amortisation and impairments''). Do not present as an IFRS metric.'

- kpi_id: KPI-FIN-019
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
    unit_format: eur_2
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
  standard_ref:
  - standard: IFRS
    id: IAS 2
    name: Cost-base baseline (variance analysis)
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
    alignment: none
    note: Internal variance-analysis baseline; no external standard. Underlying cost is IAS 2 inventory cost.

- kpi_id: KPI-SCM-021
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
    unit_format: eur_2
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
  standard_ref:
  - standard: IFRS
    id: IAS 1
    name: Operating expenses
    url: https://www.ifrs.org/issued-standards/list-of-standards/ias-1-presentation-of-financial-statements/
    alignment: partial
    note: Operating expenses map to IAS 1 expense presentation (by nature or by function). The 'base' scoping is an internal reporting choice, not an IFRS concept — align the expense population to the IAS 1 classification actually reported.

- kpi_id: KPI-GOV-004
  kpi_key: Enterprise Value-at-Risk Index
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Risk
  domain_tag:
  - Enterprise & Governance
  - Corporate & Strategy
  use_case_ref:
  - XD-003
  - XD-004
  action_code_ref:
  - X-E3.2
  calc_type: ratio
  good_is: lower
  business:
    purpose: Aggregates downside risk across domains into a single index.
    definition: 'Average of three risk shares, scaled to 0-100: (1) Revenue-at-Risk Share = (Net Sales * average(1-OTIF failure, 1-First-Pass-Yield failure)) / Net Sales, (2) Delivery Risk = 1 - OTIF %, (3) Quality Risk = 1 - In-Full %.'
    grain_scope: Entity or business unit; aggregated by period.
    unit_format: index_0
    interpretation: Higher index indicates higher enterprise risk exposure.
  technical:
    measure_name: Enterprise Value-at-Risk Index
    description: Aggregates downside risk across domains into a single index.
    depends_on_measures:
    - KPI-COM-005
    - KPI-SCM-007
    - KPI-SCM-018
    lineage: []
    calculation:
      op: round
      digits: 0
      value:
        calc:
          op: ratio
          scale: 100
          numerator:
            calc:
              op: add
              terms:
              - calc:
                  op: ratio
                  numerator:
                    calc:
                      op: mul
                      terms:
                      - kpi: KPI-COM-005
                      - calc:
                          op: ratio
                          numerator:
                            calc:
                              op: add
                              terms:
                              - calc:
                                  op: delta
                                  minuend:
                                    literal: 1
                                  subtrahend:
                                    kpi: KPI-SCM-007
                              - calc:
                                  op: delta
                                  minuend:
                                    literal: 1
                                  subtrahend:
                                    kpi: KPI-SCM-018
                          denominator:
                            literal: 2
                  denominator:
                    kpi: KPI-COM-005
              - calc:
                  op: delta
                  minuend:
                    literal: 1
                  subtrahend:
                    kpi: KPI-SCM-007
              - calc:
                  op: delta
                  minuend:
                    literal: 1
                  subtrahend:
                    kpi: KPI-SCM-018
          denominator:
            literal: 3
  governance:
    business_owner: Chief Risk Officer
    data_owner: Enterprise Risk
    steward: Risk Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Faithfully reproduces legacy's redundant round-trip (Revenue-at-Risk Share is algebraically ~ average(DeliveryRisk, QualityRisk) already, since it divides Net Sales * that same average back by Net Sales) rather than simplifying it away — the round-trip changes zero-Net-Sales-denominator BLANK() behavior, so collapsing it would be a silent value-level divergence, not a pure simplification.
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 23.01.2026
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Enterprise value-at-risk (composite)
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: A composite index built from already-governed KPIs — SCOR reliability (OTIF, in-full → RL) and ISO 22400 quality (first-pass yield → QR) weighted into a 0-100 risk score. No external standard defines the composite; its inputs are governed by the SCM and Operations runs. Document the weighting so the index is reproducible.

- kpi_id: KPI-SCM-022
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
  good_is: lower
  business:
    purpose: Rates suppliers based on risk indicators.
    definition: Composite risk score derived from supplier risk factors.
    grain_scope: Supplier; aggregated by period.
    unit_format: score_1
    interpretation: Higher scores indicate higher supplier risk.
  technical:
    measure_name: Supplier Risk Score
    description: Rates suppliers based on risk indicators.
    depends_on_measures: []
    lineage:
    - fact_supplier_risk.Risk Score
    calculation:
      op: avg
      column: Risk Score
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
  standard_ref:
  - standard: SCOR-DS
    id: AG
    name: Agility — Value at Risk
    url: https://scor.ascm.org/performance/agility
    alignment: partial
    note: 'Loose link only: SCOR Agility (AG) measures adaptability and overall value-at-risk, not a supplier-risk composite score. Conceptual neighbour, not the same metric.'

- kpi_id: KPI-SVC-004
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
  good_is: higher
  business:
    purpose: Measures how many cases meet the committed SLA.
    definition: Cases with SLA Met Flag = 1 divided by total cases in period.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: percent_1
    interpretation: Higher is better; interpret jointly with backlog and escalation %.
  technical:
    measure_name: SLA Attainment %
    description: Measures how many cases meet the committed SLA.
    depends_on_measures: []
    lineage:
    - fact_support_cases.SLA Met Flag
    calculation:
      op: rate
      column: SLA Met Flag
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
  standard_ref:
  - standard: ISO/IEC 20000-1
    id: 8.3.3
    name: Service level management — SLA attainment
    url: https://www.iso.org/standard/70636.html
    alignment: partial
    note: ISO/IEC 20000-1:2018 clause 8.3.3 (Service level management) requires documented SLAs and monitoring of performance against agreed service-level targets. SLA attainment % is the practice metric for that clause — ISO mandates the SLA and its monitoring, not this specific formula. Pin the target set so attainment is comparable.

- kpi_id: KPI-SVC-005
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
  good_is: higher
  business:
    purpose: Shows the share of cases solved on first contact.
    definition: Cases with FCR Flag = 1 divided by total cases.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: percent_1
    interpretation: Higher is better; keep in balance with AHT and escalation %.
  technical:
    measure_name: FCR %
    description: Shows the share of cases solved on first contact.
    depends_on_measures: []
    lineage:
    - fact_support_cases.FCR Flag
    calculation:
      op: rate
      column: FCR Flag
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
  standard_ref:
  - standard: ITIL 4
    name: Service desk — First Contact Resolution
    url: https://www.axelos.com/certifications/itil-service-management
    alignment: partial
    note: First Contact Resolution is a de-facto ITIL 4 service-desk / incident-management practice metric (and COPC CX Standard), not formally defined by ISO/IEC 20000. Widely standard in service management; pin the 'contact' grain (call vs case, single vs multi-channel) to compare externally.

- kpi_id: KPI-SVC-006
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
  good_is: lower
  business:
    purpose: Measures average time to handle a contact.
    definition: Total handle time divided by number of cases/contacts.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: eur_0
    interpretation: Lower is better, but balance with FCR and NPS.
  technical:
    measure_name: AHT Minutes
    description: Measures average time to handle a contact.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Handle Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Handle Time Minutes
      denominator:
        calc:
          op: count
          column: Handle Time Minutes
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
  standard_ref:
  - standard: ITIL 4
    name: Average Handling Time
    url: https://www.axelos.com/certifications/itil-service-management
    alignment: partial
    note: AHT is a contact-centre / ITIL service-desk practice metric (also COPC CX Standard); not ISO/IEC 20000-defined. Align the handle-time components (talk + hold + wrap) so the average is comparable across teams.

- kpi_id: KPI-SVC-007
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
  good_is: lower
  business:
    purpose: Quantifies unresolved work in queue.
    definition: Count of open cases at period end.
    grain_scope: queue_day; aggregated to month by Org/Channel/Queue.
    unit_format: count_0
    interpretation: Lower is better; assess with SLA attainment and staffing KPIs.
  technical:
    measure_name: Backlog Count
    description: Quantifies unresolved work in queue.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Backlog Flag
    calculation:
      op: count_filtered
      column: Backlog Flag
      filters:
      - column: Backlog Flag
        equals: true
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
  standard_ref:
  - standard: ISO/IEC 20000-1
    id: 8.6.1
    name: Incident & service-request management — open backlog
    url: https://www.iso.org/standard/70636.html
    alignment: partial
    note: Open-case backlog is an operational measure of the ISO/IEC 20000-1 resolution & fulfilment processes (8.6.1 incident / 8.6.2 service request); a count element rather than a named ISO KPI.

- kpi_id: KPI-SVC-008
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
  good_is: lower
  business:
    purpose: Measures frequency of escalated cases.
    definition: Escalated cases divided by total cases.
    grain_scope: queue_day or month; aggregated by Org/Channel/Queue.
    unit_format: percent_1
    interpretation: Lower is better; balance with FCR and SLA.
  technical:
    measure_name: Escalation %
    description: Measures frequency of escalated cases.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Escalation Flag
    calculation:
      op: rate
      column: Escalation Flag
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
  standard_ref:
  - standard: ISO/IEC 20000-1
    id: 8.6.1
    name: Incident escalation ratio
    url: https://www.iso.org/standard/70636.html
    alignment: partial
    note: Escalation ratio relates to ISO/IEC 20000-1 incident-management escalation (8.6.1, functional/hierarchical) and ITIL practice; the % is a practice metric, not an ISO-defined formula.

- kpi_id: KPI-SVC-009
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
  good_is: band
  business:
    purpose: Measures productive time versus paid time for agents.
    definition: Productive time divided by paid time.
    grain_scope: agent_day or queue_day; aggregated to week/month.
    unit_format: percent_1
    interpretation: Typical healthy band 75?85%; balance with SLA/NPS.
  technical:
    measure_name: Utilization %
    description: Measures productive time versus paid time for agents.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Paid Time Minutes
    - fact_workforce_management.Work Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Work Time Minutes
      denominator:
        column: Paid Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    id: UE
    name: Utilization efficiency (workforce)
    url: https://www.iso.org/standard/54497.html
    alignment: partial
    note: Utilization (productive / paid time) parallels ISO 22400-2 Utilization efficiency UE, but this KPI is applied to a contact-centre workforce, not equipment. Concept aligns; population differs — see COPC CX Standard for the contact-centre definition.

- kpi_id: KPI-SVC-010
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
  good_is: band
  business:
    purpose: Measures active vs idle share of time.
    definition: (Talk + Wrap) / (Talk + Wrap + Idle).
    grain_scope: agent_day or queue_day; aggregated to week/month.
    unit_format: percent_1
    interpretation: Balanced occupancy supports SLA and quality.
  technical:
    measure_name: Occupancy %
    description: Measures active vs idle share of time.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Idle Time Minutes
    - fact_workforce_management.Talk Time Minutes
    - fact_workforce_management.Wrap Time Minutes
    calculation:
      op: ratio
      numerator:
        calc:
          op: add
          terms:
          - column: Talk Time Minutes
          - column: Wrap Time Minutes
      denominator:
        calc:
          op: add
          terms:
          - column: Talk Time Minutes
          - column: Wrap Time Minutes
          - column: Idle Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    name: (contact-centre occupancy)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Occupancy ((Talk+Wrap)/(Talk+Wrap+Idle)) is a contact-centre workforce metric governed by the COPC CX Standard / contact-centre WFM, not ISO 22400-2 manufacturing operations.

- kpi_id: KPI-SVC-011
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
  good_is: lower
  business:
    purpose: Shows overtime share of total hours.
    definition: Overtime hours divided by total hours.
    grain_scope: agent_day; aggregated to week/month.
    unit_format: percent_1
    interpretation: Lower is better; monitor sustainability and cost.
  technical:
    measure_name: Overtime %
    description: Shows overtime share of total hours.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Overtime Minutes
    - fact_workforce_management.Paid Time Minutes
    calculation:
      op: ratio
      numerator:
        column: Overtime Minutes
      denominator:
        column: Paid Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    name: (contact-centre overtime)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Overtime share is a workforce-management metric (COPC CX Standard / WFM), not an ISO 22400-2 operations KPI.

- kpi_id: KPI-SVC-012
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
  good_is: lower
  business:
    purpose: Measures non-productive share of paid time.
    definition: Non-productive time divided by paid time.
    grain_scope: agent_day; aggregated to week/month.
    unit_format: percent_1
    interpretation: Lower is better; compare vs plan.
  technical:
    measure_name: Shrinkage %
    description: Measures non-productive share of paid time.
    depends_on_measures: []
    lineage:
    - fact_workforce_management.Paid Time Minutes
    - fact_workforce_management.Shrinkage Minutes
    calculation:
      op: ratio
      numerator:
        column: Shrinkage Minutes
      denominator:
        column: Paid Time Minutes
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
  standard_ref:
  - standard: ISO 22400-2
    name: (contact-centre shrinkage)
    url: https://www.iso.org/standard/54497.html
    alignment: none
    note: Shrinkage (non-productive / paid time) is a contact-centre WFM metric (COPC CX Standard), not ISO 22400-2.

- kpi_id: KPI-SVC-013
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
    unit_format: count_0
    interpretation: Higher counts indicate higher inbound demand.
  technical:
    measure_name: Tickets Created Count
    description: Counts customer service tickets created in the period.
    depends_on_measures: []
    lineage:
    - fact_support_cases
    calculation:
      op: count
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
  standard_ref:
  - standard: ISO/IEC 20000-1
    id: 8.6.1
    name: Incident/request volume (element)
    url: https://www.iso.org/standard/70636.html
    alignment: none
    note: Raw created-ticket count is an incident/service-request volume element (ISO/IEC 20000-1 8.6.1/8.6.2), not a named ISO KPI — it is an input to arrival-rate/backlog measures.

- kpi_id: KPI-SVC-014
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
    definition: Count of cases with Open Case Flag = FALSE (closed).
    grain_scope: Ticket; aggregated by period and channel.
    unit_format: count_0
    interpretation: Higher counts indicate higher resolution throughput.
  technical:
    measure_name: Tickets Closed Count
    description: Counts customer service tickets closed in the period.
    depends_on_measures: []
    lineage:
    - fact_support_cases.Open Case Flag
    calculation:
      op: count_filtered
      column: Open Case Flag
      filters:
      - column: Open Case Flag
        equals: false
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
  standard_ref:
  - standard: ISO/IEC 20000-1
    id: 8.6.1
    name: Incident/request throughput (element)
    url: https://www.iso.org/standard/70636.html
    alignment: none
    note: Raw closed-ticket count is a throughput element feeding backlog and closure-rate; not a named ISO/IEC 20000 KPI on its own.

- kpi_id: KPI-GOV-005
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
    unit_format: count_0
    interpretation: Higher counts indicate active use of ActionReady recommendations.
  technical:
    measure_name: Actions Executed Count
    description: Number of action codes with a recorded outcome in fact_action_outcome.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.outcome_status
    calculation:
      op: count_filtered
      column: outcome_status
      filters:
      - column: outcome_status
        not_blank: true
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
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Actions executed (element)
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: Executed-action count is an operational element of the action-governance loop, not a named external KPI.

- kpi_id: KPI-GOV-006
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
  good_is: lower
  business:
    purpose: Measures how quickly ActionReady recommendations convert to confirmed outcomes.
    definition: Average of days_to_outcome across all executed action rows.
    grain_scope: Action execution; aggregated monthly by domain.
    unit_format: days_1
    interpretation: Lower values indicate faster action-to-outcome cycles.
  technical:
    measure_name: Avg Time-to-Outcome Days
    description: Average days between action execution and outcome confirmation.
    depends_on_measures: []
    lineage:
    - fact_action_outcome.days_to_outcome
    calculation:
      op: avg
      column: days_to_outcome
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
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Average time to outcome
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: Average days-to-outcome is the framework's own action-cycle-time metric; no external standard (PDCA cycle-time is the conceptual backdrop).

- kpi_id: KPI-GOV-007
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
  good_is: higher
  business:
    purpose: Measures the financial return on ActionReady recommendation investments.
    definition: Total impact value of executed actions / total execution cost - 1.
    grain_scope: Action execution; aggregated monthly by domain.
    unit_format: percent_1
    interpretation: Values above 0% indicate net-positive actions; negative values flag ineffective interventions.
  technical:
    measure_name: Action ROI %
    description: 'Average ROI of executed actions: total impact value / total execution cost - 1.'
    depends_on_measures: []
    lineage:
    - fact_action_outcome.impact_value
    - fact_action_outcome.cost_to_execute
    calculation:
      op: delta
      minuend:
        calc:
          op: ratio
          numerator:
            column: impact_value
          denominator:
            column: cost_to_execute
      subtrahend:
        literal: 1
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
  standard_ref:
  - standard: Internal — ActionReady governance
    name: Action ROI
    url: https://www.iso.org/standard/62085.html
    alignment: none
    note: Action ROI (impact value / execution cost − 1) is the ActionReady framework's own governance metric; no external standard. ISO 9001 continual improvement / Balanced Scorecard is the conceptual backdrop.

- kpi_id: KPI-COM-022
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
  good_is: higher
  business:
    purpose: Share of transactions that contain items from two or more distinct product categories.
    definition: Transactions with >=2 distinct categories divided by total transactions in scope.
    grain_scope: Transaction aggregated by Month, Store, Channel, Category pair.
    unit_format: percent_1
    interpretation: Higher values indicate stronger basket breadth and cross-sell capture; declining values signal weakening category affinity activation.
  technical:
    measure_name: Category Cross-Sell Rate %
    description: Share of transactions spanning two or more product categories.
    depends_on_measures: []
    lineage:
    - fact_sales.Transaction Key
    - fact_sales.Category Key
    calculation:
      op: hitl
      blocked_by: authoring
      reason: Anteil Transaktionen mit mehr als einer Kategorie. Kein Legacy-Vorbild im dist — die Zielformel (Zaehlbasis, Grain, Behandlung von Einzelposten) ist fachlich nicht festgelegt.
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
  standard_ref:
  - standard: Retail analytics (convention)
    name: Cross-sell rate
    alignment: none
    note: Cross-sell rate (multi-category transactions / total) is a retail/CRM analytics convention, not standard-defined.

- kpi_id: KPI-COM-023
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
  good_is: higher
  business:
    purpose: Average number of distinct line items per completed transaction.
    definition: Total line items divided by total transactions in scope.
    grain_scope: Transaction aggregated by Month, Store, Channel.
    unit_format: ratio_1
    interpretation: A core basket-size driver; rising values indicate broader baskets and successful attachment, falling values indicate basket erosion.
  technical:
    measure_name: Items per Transaction
    description: Average distinct line items per completed transaction.
    depends_on_measures: []
    lineage:
    - fact_sales.Line Item Key
    - fact_sales.Transaction Key
    calculation:
      op: ratio
      numerator:
        calc:
          op: distinctcount
          column: Line Item Key
      denominator:
        calc:
          op: distinctcount
          column: Transaction Key
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
  standard_ref:
  - standard: Retail analytics (convention)
    name: Units per transaction (UPT)
    alignment: none
    note: Items per transaction (UPT) is a retail-analytics convention; no governing standard.

- kpi_id: KPI-COM-024
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
    unit_format: eur_2
    interpretation: The headline basket-economics guardrail; cross-sell actions must grow breadth without eroding average basket value.
  technical:
    measure_name: Average Basket Value
    description: Average net sales value per completed transaction.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Transaction Key
    calculation:
      op: ratio
      numerator:
        column: Net Sales Amount
      denominator:
        calc:
          op: distinctcount
          column: Transaction Key
  governance:
    business_owner: Head of Category Management
    data_owner: Commercial BI Engineering
    steward: Trade Marketing Analyst
    review_cycle: monthly
    validation_process: monthly reconciliation against POS net sales and transaction counts
    qa_rules:
    - Bounds [0; 100000]
    - Net of VAT and returns; consistent with KPI-COM-005 basis
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.06.2026
  standard_ref:
  - standard: Retail analytics (convention)
    name: Average transaction value
    alignment: none
    note: Average basket value (net sales / transactions) is a standard retail KPI but a market convention, not a governed standard.

- kpi_id: KPI-COM-025
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
    unit_format: percent_1
    interpretation: Measures whether promotion mechanics pull margin-accretive attachment rather than standalone deal-seeking; the primary lever for cross-sell rate.
  technical:
    measure_name: Promotion Attachment Rate %
    description: Share of promoted transactions carrying an attached affinity-category item.
    depends_on_measures: []
    lineage:
    - fact_sales.Promotion Key
    - fact_sales.Category Key
    calculation:
      op: hitl
      blocked_by: authoring
      reason: Anteil Transaktionen mit Promotion-Bezug je Kategorie. Kein Legacy-Vorbild im dist — dieselbe offene Frage wie bei crosssell_rate.
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
  standard_ref:
  - standard: Retail analytics (convention)
    name: Attachment rate
    alignment: none
    note: Promotion attachment rate is a retail merchandising-analytics convention; no external standard.

- kpi_id: KPI-CUS-007
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
    unit_format: score_1
    interpretation: Higher frequency cohorts respond more strongly to cross-sell prompts; used to target attachment offers where repeat-visit behaviour already exists.
  technical:
    measure_name: RFM Frequency Score
    description: Average customer purchase-frequency quintile score from the RFM model.
    depends_on_measures: []
    lineage:
    - fact_sales.Customer Key
    - fact_sales.Transaction Key
    calculation:
      op: hitl
      blocked_by: authoring
      reason: Quantil-Scoring (Transaktionszahl je Kunde -> Rangklasse 1-5). Kein Legacy-Vorbild im dist, also ist die Zielformel nicht festgelegt; ob die Grammatik sie traegt, ist erst nach der Ausformulierung entscheidbar.
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
  standard_ref:
  - standard: Marketing analytics — RFM (convention)
    name: RFM frequency score
    alignment: none
    note: RFM (Recency-Frequency-Monetary) scoring is a long-standing direct-marketing segmentation model (Hughes/DMA lineage), a convention rather than a governed standard.

- kpi_id: KPI-PPL-001
  kpi_key: Attrition %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: governance
  domain_tag:
  - People & Culture
  use_case_ref:
  - HR-001
  - XD-003
  action_code_ref: []
  calc_type: rate
  good_is: lower
  business:
    purpose: Measures realised voluntary employee turnover in the period.
    definition: Voluntary Leavers / Average Headcount (annualised).
    grain_scope: Org/segment; monthly, annualised.
    unit_format: percent_1
    interpretation: Lower is better; sustained rises signal retention and engagement problems.
  technical:
    measure_name: Attrition %
    description: Measures realised voluntary employee turnover in the period.
    depends_on_measures: []
    lineage:
    - fact_workforce.Voluntary Leavers
    - fact_workforce.Headcount FTE
    calculation:
      op: ratio
      numerator:
        column: Voluntary Leavers
      denominator:
        column: Headcount FTE
      scale: 12
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ISO 30414
    name: Human capital — turnover rate
    alignment: exact
    note: ISO 30414:2018 defines turnover/attrition rate; this is the realised voluntary-turnover base metric.

- kpi_id: KPI-PPL-002
  kpi_key: Engagement Index
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: governance
  domain_tag:
  - People & Culture
  use_case_ref:
  - HR-001
  action_code_ref: []
  calc_type: avg
  good_is: higher
  business:
    purpose: Measures employee engagement / eNPS from periodic surveys.
    definition: Mean engagement score (or eNPS) for the population in the period.
    grain_scope: Org/segment; quarterly survey.
    unit_format: index_0
    interpretation: Higher is better; the leading driver of attrition and productivity.
  technical:
    measure_name: Engagement Index
    description: Measures employee engagement / eNPS from periodic surveys.
    depends_on_measures: []
    lineage:
    - fact_engagement_survey.Engagement Score
    calculation:
      op: avg
      column: Engagement Score
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ISO 30414
    name: Human capital — organizational culture / engagement
    alignment: partial
    note: ISO 30414 reports engagement under organizational culture; the index here is a survey-mean variant.

- kpi_id: KPI-PPL-003
  kpi_key: Time to Fill
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: governance
  domain_tag:
  - People & Culture
  use_case_ref:
  - HR-001
  action_code_ref: []
  calc_type: ratio
  good_is: lower
  business:
    purpose: Measures average calendar days to fill an open vacancy.
    definition: Mean(Filled Date - Requisition Open Date) over positions filled in the period.
    grain_scope: Org/role; monthly.
    unit_format: days_0
    interpretation: Lower is better; long fill times amplify workload and attrition risk.
  technical:
    measure_name: Time to Fill
    description: Measures average calendar days to fill an open vacancy.
    depends_on_measures: []
    lineage:
    - fact_recruiting.Days to Fill
    calculation:
      op: avg
      column: Days to Fill
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ISO 30414
    name: Human capital — recruitment (time to fill)
    alignment: exact
    note: ISO 30414 defines time-to-fill within recruitment metrics; definition matches.

- kpi_id: KPI-PPL-004
  kpi_key: Absence Rate %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: governance
  domain_tag:
  - People & Culture
  use_case_ref:
  - HR-001
  action_code_ref: []
  calc_type: rate
  good_is: lower
  business:
    purpose: Measures unplanned absence as a share of scheduled working time.
    definition: Absence Days / Scheduled Working Days.
    grain_scope: Org/segment; monthly.
    unit_format: percent_1
    interpretation: Lower is better; rising absence is an early strain and engagement signal.
  technical:
    measure_name: Absence Rate %
    description: Measures unplanned absence as a share of scheduled working time.
    depends_on_measures: []
    lineage:
    - fact_workforce.Absence Days
    - fact_workforce.Scheduled Working Days
    calculation:
      op: ratio
      numerator:
        column: Absence Days
      denominator:
        column: Scheduled Working Days
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ISO 30414
    name: Human capital — absenteeism
    alignment: exact
    note: ISO 30414 defines absenteeism rate; definition matches.

- kpi_id: KPI-PPL-005
  kpi_key: Workforce Cost per FTE
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Cost
  domain_tag:
  - People & Culture
  use_case_ref:
  - HR-001
  action_code_ref: []
  calc_type: sum
  business:
    purpose: Measures total workforce cost per full-time-equivalent.
    definition: Total Workforce Cost / Headcount FTE.
    grain_scope: Org/segment; monthly.
    unit_format: eur_0
    interpretation: Watch alongside productivity; cost per FTE rising faster than output erodes efficiency.
  technical:
    measure_name: Workforce Cost per FTE
    description: Measures total workforce cost per full-time-equivalent.
    depends_on_measures: []
    lineage:
    - fact_workforce.Workforce Cost Amount
    - fact_workforce.Headcount FTE
    calculation:
      op: ratio
      numerator:
        column: Workforce Cost Amount
      denominator:
        column: Headcount FTE
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ISO 30414
    name: Human capital — workforce costs
    alignment: partial
    note: ISO 30414 reports total workforce cost; per-FTE normalisation is a managerial variant of the ISO cost base.

- kpi_id: KPI-PPL-006
  kpi_key: Headcount FTE
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: governance
  domain_tag:
  - People & Culture
  use_case_ref:
  - HR-001
  action_code_ref: []
  calc_type: count
  business:
    purpose: Measures full-time-equivalent headcount for the population.
    definition: Sum of FTE fractions across active employees in the period.
    grain_scope: Org/segment; monthly snapshot.
    unit_format: count_0
    interpretation: Denominator base for attrition, cost and absence; watch for structural drift.
  technical:
    measure_name: Headcount FTE
    description: Measures full-time-equivalent headcount for the population.
    depends_on_measures: []
    lineage:
    - fact_workforce.Headcount FTE
    calculation:
      op: sum
      column: Headcount FTE
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ISO 30414
    name: Human capital — workforce availability (FTE)
    alignment: exact
    note: ISO 30414 defines FTE headcount within workforce availability; definition matches.

- kpi_id: KPI-COM-026
  kpi_key: Pipeline Coverage
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-005
  - XD-003
  action_code_ref: []
  calc_type: ratio
  good_is: higher
  business:
    purpose: Measures open qualified pipeline against the remaining sales target.
    definition: Open Qualified Pipeline Value / Remaining Period Target.
    grain_scope: Rep/region/segment; weekly snapshot.
    unit_format: ratio_1
    interpretation: Higher is better; a healthy funnel typically carries ≥3x coverage of the remaining gap.
  technical:
    measure_name: Pipeline Coverage
    description: Measures open qualified pipeline against the remaining sales target.
    depends_on_measures: []
    lineage:
    - fact_pipeline.Open Qualified Value Amount
    - fact_sales_target.Remaining Target Amount
    calculation:
      op: ratio
      numerator:
        column: Open Qualified Value Amount
      denominator:
        column: Remaining Target Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Sales pipeline management (convention)
    name: Pipeline coverage ratio (3x rule)
    alignment: none
    note: No ISO/IFRS standard governs pipeline coverage; this is an established commercial-steering convention (typical ≥3x rule), not an external standard.

- kpi_id: KPI-COM-027
  kpi_key: Win Rate %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-005
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures share of decided opportunities won.
    definition: Opportunities Won / (Opportunities Won + Opportunities Lost).
    grain_scope: Rep/segment/stage; monthly.
    unit_format: percent_1
    interpretation: Higher is better; the primary conversion lever behind coverage and attainment.
  technical:
    measure_name: Win Rate %
    description: Measures share of decided opportunities won.
    depends_on_measures: []
    lineage:
    - fact_pipeline.Won Count
    - fact_pipeline.Decided Count
    calculation:
      op: ratio
      numerator:
        column: Won Count
      denominator:
        column: Decided Count
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Sales pipeline management (convention)
    name: Win rate / opportunity conversion
    alignment: none
    note: Win rate is a standard commercial-analytics convention; no external standards body defines it.

- kpi_id: KPI-COM-028
  kpi_key: Stage Conversion %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-005
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures conversion between funnel stages (lead → opportunity → won).
    definition: Records advancing to the next stage / Records entering the stage.
    grain_scope: Stage/segment; monthly.
    unit_format: percent_1
    interpretation: Higher is better; isolates where the funnel leaks.
  technical:
    measure_name: Stage Conversion %
    description: Measures conversion between funnel stages (lead → opportunity → won).
    depends_on_measures: []
    lineage:
    - fact_pipeline.StageKey
    - fact_pipeline.Qualified Flag
    - fact_pipeline.Opportunity Value Amount
    calculation:
      op: hitl
      blocked_by: authoring
      reason: fact_pipeline (opportunity grain) now in Aurora; true per-stage conversion (records advancing to next stage / entering the stage) needs a stage-transition fact or a DAX stage-cohort measure — synthesised in TMDL by CLI.
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Sales pipeline management (convention)
    name: Funnel stage conversion
    alignment: none
    note: Funnel conversion is a commercial-analytics convention, not an external standard.

- kpi_id: KPI-COM-029
  kpi_key: Sales Cycle Length
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-005
  action_code_ref: []
  calc_type: ratio
  good_is: lower
  business:
    purpose: Measures average calendar days from opportunity creation to close.
    definition: Mean(Close Date - Create Date) over opportunities closed in the period.
    grain_scope: Rep/segment; monthly.
    unit_format: days_0
    interpretation: Lower is better; a lengthening cycle slows cash conversion and coverage.
  technical:
    measure_name: Sales Cycle Length
    description: Measures average calendar days from opportunity creation to close.
    depends_on_measures: []
    lineage:
    - fact_pipeline.Cycle Days
    calculation:
      op: avg
      column: Cycle Days
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Sales pipeline management (convention)
    name: Sales-cycle length
    alignment: none
    note: Sales-cycle length is a commercial-analytics convention, not an external standard.

- kpi_id: KPI-COM-030
  kpi_key: Sales Velocity
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-005
  action_code_ref: []
  calc_type: sum
  good_is: higher
  business:
    purpose: Measures revenue generation rate through the pipeline.
    definition: (Open Opportunities x Avg Deal Value x Win Rate) / Sales Cycle Length.
    grain_scope: Rep/segment; monthly.
    unit_format: eur_0
    interpretation: Higher is better; a composite health signal for the funnel engine.
  technical:
    measure_name: Sales Velocity
    description: Measures revenue generation rate through the pipeline.
    depends_on_measures: []
    lineage:
    - fact_pipeline.Opportunity Value Amount
    - fact_pipeline.Won Count
    - fact_pipeline.Decided Count
    - fact_pipeline.Cycle Days
    calculation:
      op: hitl
      blocked_by: authoring
      reason: 'Composite: open-opportunity count x avg deal value x win rate / sales-cycle length; all inputs now in fact_pipeline — assembled as a DAX measure in TMDL by CLI (beyond the neutral single-op DSL).'
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Sales pipeline management (convention)
    name: Sales velocity formula
    alignment: none
    note: Sales velocity is a widely-used commercial convention (opps x value x win-rate / cycle); no external standard defines it.

- kpi_id: KPI-COM-031
  kpi_key: Open Pipeline Value
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-005
  action_code_ref: []
  calc_type: sum
  business:
    purpose: Measures total value of open qualified opportunities.
    definition: Sum of Opportunity Value for open qualified opportunities.
    grain_scope: Rep/region/segment; weekly snapshot.
    unit_format: eur_0
    interpretation: Base for coverage; watch concentration in a few large deals.
  technical:
    measure_name: Open Pipeline Value
    description: Measures total value of open qualified opportunities.
    depends_on_measures: []
    lineage:
    - fact_pipeline.Open Qualified Value Amount
    calculation:
      op: sum
      column: Open Qualified Value Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Sales pipeline management (convention)
    name: Open pipeline value
    alignment: none
    note: Open pipeline value is a commercial-analytics convention, not an external standard.

- kpi_id: KPI-FIN-020
  kpi_key: EBITDA
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-003
  - XD-003
  action_code_ref: []
  calc_type: sum
  business:
    purpose: Measures earnings before interest, tax, depreciation and amortisation.
    definition: Revenue - COGS - Operating Expenses (excl. D&A).
    grain_scope: Entity/BU; monthly.
    unit_format: eur_0
    interpretation: Absolute earnings base for the EBITDA-margin and vs-plan bridge.
  technical:
    measure_name: EBITDA
    description: Measures earnings before interest, tax, depreciation and amortisation.
    depends_on_measures: []
    lineage:
    - fact_finance.EBITDA Amount
    calculation:
      op: sum
      column: EBITDA Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ESMA-APM
    name: EBITDA (Alternative Performance Measure)
    alignment: partial
    note: EBITDA is not defined by IFRS; ESMA APM Guidelines govern its disclosure. Reconcile to the nearest IFRS line (operating profit) per ESMA.

- kpi_id: KPI-FIN-021
  kpi_key: EBITDA Margin vs Plan
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Profitability
  domain_tag:
  - Finance
  use_case_ref:
  - FIN-003
  action_code_ref: []
  calc_type: rate
  good_is: higher
  is_variance: true
  business:
    purpose: Measures the EBITDA-margin gap versus plan.
    definition: EBITDA Margin % (Actual) - EBITDA Margin % (Plan), in percentage points.
    grain_scope: Entity/BU; monthly.
    unit_format: percent_1
    interpretation: 'The steering signal: is earnings tracking plan, and driven by revenue, gross margin or opex?'
  technical:
    measure_name: EBITDA Margin vs Plan
    description: Measures the EBITDA-margin gap versus plan.
    depends_on_measures: []
    lineage:
    - fact_finance.EBITDA Amount
    - fact_finance.Net Sales Amount
    - fact_finance.Plan EBITDA Amount
    - fact_finance.Plan Net Sales Amount
    calculation:
      op: delta
      minuend:
        calc:
          op: ratio
          numerator:
            column: EBITDA Amount
          denominator:
            column: Net Sales Amount
      subtrahend:
        calc:
          op: ratio
          numerator:
            column: Plan EBITDA Amount
          denominator:
            column: Plan Net Sales Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: ESMA-APM
    name: EBITDA vs plan (APM variance)
    alignment: partial
    note: EBITDA-vs-plan variance is an APM comparison; ESMA APM Guidelines require consistent, reconciled definition period-over-period.

- kpi_id: KPI-SCM-023
  kpi_key: Realised Savings %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Cost
  domain_tag:
  - Supply Chain
  - Sourcing
  use_case_ref:
  - SCM-004
  - FIN-002
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures procurement savings realised against the savings target.
    definition: Realised Savings / Savings Target.
    grain_scope: Category/supplier; monthly, YTD.
    unit_format: percent_1
    interpretation: Higher is better; the CPO's headline for value delivery.
  technical:
    measure_name: Realised Savings %
    description: Measures procurement savings realised against the savings target.
    depends_on_measures: []
    lineage:
    - fact_procurement.Savings Amount
    - fact_procurement.Savings Target Amount
    calculation:
      op: ratio
      numerator:
        column: Savings Amount
      denominator:
        column: Savings Target Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Procurement & spend analytics (convention)
    name: Realised savings vs target
    alignment: none
    note: Savings realisation is a procurement-controlling convention; no external standards body defines the metric.

- kpi_id: KPI-SCM-024
  kpi_key: On-Contract Spend %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Cost
  domain_tag:
  - Supply Chain
  - Sourcing
  use_case_ref:
  - SCM-004
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures share of spend routed through negotiated contracts (inverse of maverick buying).
    definition: On-Contract Spend / Total Addressable Spend.
    grain_scope: Category/supplier; monthly.
    unit_format: percent_1
    interpretation: Higher is better; the primary lever for savings realisation and price control.
  technical:
    measure_name: On-Contract Spend %
    description: Measures share of spend routed through negotiated contracts (inverse of maverick buying).
    depends_on_measures: []
    lineage:
    - fact_procurement.On-Contract Amount
    - fact_procurement.Addressable Amount
    calculation:
      op: ratio
      numerator:
        column: On-Contract Amount
      denominator:
        column: Addressable Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Procurement & spend analytics (convention)
    name: On-contract / managed spend
    alignment: none
    note: Contract-compliance / maverick-buying share is a procurement convention, not an external standard.

- kpi_id: KPI-SCM-025
  kpi_key: Purchase Price Variance %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Cost
  domain_tag:
  - Supply Chain
  - Sourcing
  use_case_ref:
  - SCM-004
  action_code_ref: []
  calc_type: rate
  good_is: lower
  business:
    purpose: Measures purchase price variance against baseline/standard price.
    definition: (Actual Price - Baseline Price) / Baseline Price.
    grain_scope: Category/material; monthly.
    unit_format: percent_1
    interpretation: Lower is better; isolates inflation and negotiation slippage.
  technical:
    measure_name: Purchase Price Variance %
    description: Measures purchase price variance against baseline/standard price.
    depends_on_measures: []
    lineage:
    - fact_procurement.PPV Amount
    - fact_procurement.Baseline Spend Amount
    calculation:
      op: ratio
      numerator:
        column: PPV Amount
      denominator:
        column: Baseline Spend Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Procurement & spend analytics (convention)
    name: Purchase price variance (PPV)
    alignment: none
    note: PPV is a standard cost-accounting/procurement convention; align the baseline definition to the internal standard-cost policy.

- kpi_id: KPI-SCM-026
  kpi_key: Supplier On-Time Delivery %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Reliability
  domain_tag:
  - Supply Chain
  - Sourcing
  use_case_ref:
  - SCM-004
  - SCM-002
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures inbound supplier on-time delivery (goods received on/before promise).
    definition: On-Time Inbound Receipts / Total Inbound Receipts.
    grain_scope: Supplier/category; monthly.
    unit_format: percent_1
    interpretation: Higher is better; inbound reliability that feeds downstream OTIF.
  technical:
    measure_name: Supplier On-Time Delivery %
    description: Measures inbound supplier on-time delivery (goods received on/before promise).
    depends_on_measures: []
    lineage:
    - fact_procurement_receipts.On-Time Flag
    calculation:
      op: rate
      column: On-Time Flag
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: SCOR-DS
    name: Source — supplier on-time delivery
    alignment: partial
    note: SCOR governs supplier delivery reliability under Source (sS); grain here is receipt-level inbound OTD, a partial mapping to SCOR's supplier reliability metrics.
    id: RS.3.x

- kpi_id: KPI-SCM-027
  kpi_key: Managed Spend
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Cost
  domain_tag:
  - Supply Chain
  - Sourcing
  use_case_ref:
  - SCM-004
  action_code_ref: []
  calc_type: sum
  business:
    purpose: Measures total addressable spend under procurement management.
    definition: Sum of addressable spend across categories in the period.
    grain_scope: Category/supplier; monthly.
    unit_format: eur_0
    interpretation: Denominator base for on-contract %, PPV and savings; watch coverage of tail spend.
  technical:
    measure_name: Managed Spend
    description: Measures total addressable spend under procurement management.
    depends_on_measures: []
    lineage:
    - fact_procurement.Addressable Amount
    calculation:
      op: sum
      column: Addressable Amount
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 18.07.2026
  standard_ref:
  - standard: Procurement & spend analytics (convention)
    name: Managed / addressable spend
    alignment: none
    note: Addressable-spend scoping is a procurement convention, not an external standard.

- kpi_id: KPI-SCM-028
  synonyms:
  - Picks je Arbeitsstunde
  - Lines picked per hour
  - Pick rate
  kpi_key: Picks per Labor Hour
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  - Logistics
  use_case_ref:
  - SCM-002
  action_code_ref: []
  calc_type: ratio
  good_is: higher
  business:
    purpose: Measures picking productivity in the distribution center as order lines picked per productive picking hour.
    definition: Order lines picked (WMS pick confirmations) / productive labor hours booked on picking (time and attendance).
    grain_scope: Distribution center; daily.
    unit_format: ratio_1
    interpretation: Higher is better; a leading indicator for OTIF and cost-to-serve — falling picks per hour precede late shipments. Compare only within the same pick technology and order profile (lines per order, piece vs. case picking).
  technical:
    measure_name: Picks per Labor Hour
    description: Order lines picked per productive picking hour (ratio of two sums, warehouse/day grain).
    depends_on_measures: []
    lineage:
    - fact_warehouse.Picks Count
    - fact_warehouse.Picking Hours
    calculation:
      op: ratio
      numerator:
        column: Picks Count
      denominator:
        column: Picking Hours
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    - One pick = one confirmed order line (WMS), not one unit
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 02.10.2026
  standard_ref:
  - standard: WERC DC Measures
    name: Lines picked and shipped per hour
    url: https://werc.org/page/ASSESS-Benchmarking_Overview
    alignment: partial
    note: WERC divides lines picked AND shipped by total hours worked in picking and shipping; this KPI counts picked lines over productive picking hours only, so values run higher than the WERC metric. No benchmark entry until a WERC edition is pinned (quintile limits differ between editions).

- kpi_id: KPI-COM-032
  synonyms:
  - E-Commerce Umsatzanteil
  - E-Com share
  - Online revenue share
  kpi_key: E-Commerce Revenue Share
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-006
  action_code_ref: []
  calc_type: ratio
  good_is: higher
  business:
    purpose: Measures the share of revenue generated through e-commerce channels.
    definition: E-commerce channel net sales / total net sales.
    grain_scope: Channel/region; daily, reported monthly.
    unit_format: percent_1
    interpretation: Higher means a larger digital share; depends on clean channel attribution of each sale — mis-tagged channels understate the e-commerce share.
  technical:
    measure_name: E-Commerce Revenue Share
    description: Net sales of the e-commerce channel divided by total net sales.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    - dim_org.Channel
    calculation:
      op: hitl
      blocked_by: decision
      reason: Open decision which dim_org[Channel] values count as e-commerce (Online only, or Online and Marketplace). Once decided the numerator is CALCULATE ( SUM ( fact_sales[Net Sales Amount] ), dim_org[Channel] IN { ... } ), the same cross-table filtered sum as KPI-ESG-001 — the second case makes the grammar operation due.
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    - Every sale carries a channel (no unassigned revenue in the denominator only)
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 02.10.2026
  standard_ref:
  - standard: Retail analytics (convention)
    name: Channel revenue share
    alignment: none
    note: Channel share of revenue is a retail-analytics convention; which channels count as e-commerce (own web shop, marketplace) is set by the channel model, not by an external standard.

- kpi_id: KPI-COM-033
  synonyms:
  - Eigenmarkenanteil
  - Private Label Anteil
  - Private label penetration
  kpi_key: Private Label Penetration %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Profitability
  domain_tag:
  - Commercial
  - Assortment
  use_case_ref:
  - COM-IND-R002
  action_code_ref: []
  calc_type: ratio
  good_is: higher
  business:
    purpose: Measures the share of revenue from private-label (own-brand) products.
    definition: Private-label net sales / total net sales.
    grain_scope: Category/region; weekly, reported monthly.
    unit_format: percent_1
    interpretation: Higher usually lifts gross margin; an outcome of category-management decisions already taken, so read it per category. Requires consistent private-label flagging of every SKU.
  technical:
    measure_name: Private Label Penetration %
    description: Net sales of private-label products divided by total net sales.
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount
    calculation:
      op: hitl
      blocked_by: data_contract
      reason: The commercial_sales contract has no private-label attribute (dim_product carries Brand only, no own-brand flag); the numerator cannot be sourced until dim_product gains one.
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    - Every SKU flagged private label yes/no
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 02.10.2026
  standard_ref:
  - standard: Retail analytics (convention)
    name: Private label share
    alignment: none
    note: Private-label share is a retail-analytics convention; some sources measure it by units instead of revenue — this KPI is revenue-based.

- kpi_id: KPI-COM-034
  synonyms:
  - E-Commerce Konversionsrate
  - Online conversion rate
  kpi_key: E-Commerce Conversion Rate
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: Growth
  domain_tag:
  - Commercial
  - Growth
  use_case_ref:
  - COM-006
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures the share of web-shop sessions that end in a purchase.
    definition: Sessions with at least one purchase / total sessions.
    grain_scope: Web shop/device/traffic source; daily.
    unit_format: percent_1
    interpretation: Higher is better; operational driver of e-commerce revenue. Comparable over time only with a fixed session definition and documented bot filtering; peer values differ strongly by product category.
  technical:
    measure_name: E-Commerce Conversion Rate
    description: Purchasing sessions divided by all sessions (web analytics).
    depends_on_measures: []
    lineage: []
    calculation:
      op: hitl
      blocked_by: data_contract
      reason: No ALUCA data contract carries web-analytics sessions; a session-grain fact (session id, purchase flag) is needed before the rate can be computed.
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    - Bot traffic excluded by a documented rule
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 02.10.2026
  standard_ref:
  - standard: Web analytics (convention)
    name: E-commerce conversion rate
    alignment: none
    note: Session-based conversion is a web-analytics convention; session definition and bot filtering differ between analytics tools, so the value is tool-dependent.

- kpi_id: KPI-ESG-001
  synonyms:
  - Scope 1+2 CO2 Emissionen
  - Scope 1 and 2 GHG emissions
  kpi_key: Scope 1+2 CO2 Emissions
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: ESG
  domain_tag:
  - ESG
  - Environment
  use_case_ref:
  - ESG-001
  action_code_ref: []
  calc_type: quantity
  good_is: lower
  business:
    purpose: Measures greenhouse-gas emissions from own operations and purchased energy.
    definition: Scope 1 emissions + Scope 2 emissions (market-based), in tonnes CO2 equivalent.
    grain_scope: Site/scope; annual inventory, monthly where metered.
    unit_format: tco2e_0
    interpretation: Lower is better; an annual GHG inventory makes in-year trends invisible until consolidation. State the Scope 2 method (market-based) next to the value.
  technical:
    measure_name: Scope 1+2 CO2 Emissions
    description: Sum of Scope 1 and Scope 2 emissions in tCO2e.
    depends_on_measures: []
    lineage:
    - fact_emissions.Emissions tCO2e
    - dim_emission_scope.ScopeCode
    calculation:
      op: hitl
      blocked_by: grammar
      reason: CALCULATE ( SUM ( fact_emissions[Emissions tCO2e] ), dim_emission_scope[ScopeCode] IN { "SCOPE_1", "SCOPE_2" } ) — a sum under a column-value filter; the grammar has no filtered sum over a related dimension's column (count_filtered/avg_filtered filter only the KPI's own lineage table).
      pattern: calculate_sum_with_dimension_filter
      occurrences_in_corpus: 0
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: annually
    validation_process: manual review
    qa_rules:
    - Emissions >= 0
    - Scope 2 method (market-based) documented per reporting year
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 02.10.2026
  standard_ref:
  - standard: GHG Protocol
    name: Corporate Standard — Scope 1 and Scope 2
    url: https://ghgprotocol.org/corporate-standard
    alignment: partial
    note: Scope boundaries follow the GHG Protocol Corporate Standard; its Scope 2 Guidance asks for both location-based and market-based Scope 2 figures, this KPI carries the market-based one only.
  - standard: ESRS E1
    id: E1-6
    name: Gross Scopes 1, 2, 3 and Total GHG emissions
    alignment: partial
    note: ESRS E1-6 discloses Scope 1, Scope 2 and Scope 3 separately plus a total; this KPI is the Scope 1+2 subtotal and not a full E1-6 disclosure.

- kpi_id: KPI-ESG-002
  synonyms:
  - Lieferanten-ESG-Quote (Tier 1)
  - Lieferant-ESG-Compliance
  - Supplier ESG compliance
  kpi_key: Supplier ESG Compliance %
  kpi_type: diagnostic
  kpi_role: influencing
  impact_dimension: ESG
  domain_tag:
  - ESG
  - Sourcing
  use_case_ref:
  - SCM-004
  action_code_ref: []
  calc_type: rate
  good_is: higher
  business:
    purpose: Measures the share of direct (Tier-1) suppliers with a completed and passed ESG audit.
    definition: Tier-1 suppliers with a completed ESG audit and a passing score / all active Tier-1 suppliers. Tier 1 only — sub-suppliers (Tier 2+) are out of scope.
    grain_scope: Supplier/category; quarterly.
    unit_format: percent_1
    interpretation: Higher is better; the quarterly audit cadence lags detection by up to three months. Comparable over years only with a documented, stable pass/fail scoring method.
  technical:
    measure_name: Supplier ESG Compliance %
    description: Share of active Tier-1 suppliers with a passed ESG audit.
    depends_on_measures: []
    lineage: []
    calculation:
      op: hitl
      blocked_by: data_contract
      reason: No ALUCA data contract carries supplier ESG audit results (status, score, Tier flag); a supplier-audit fact or attributes on the procurement supplier dimension are needed.
  governance:
    business_owner: TBD
    data_owner: TBD
    steward: TBD
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Denominator > 0 for reported slices
    - Tier-1 population = suppliers with direct purchase orders in the period
    version: v1.0
  metadata_quality:
    completeness_score: 1.0
    last_review: 02.10.2026
  standard_ref:
  - standard: ISO 20400
    name: Sustainable procurement — Guidance
    alignment: none
    note: ISO 20400 gives guidance on integrating sustainability into procurement but defines no compliance-rate metric; the audit scope and pass threshold are company rules.
```
