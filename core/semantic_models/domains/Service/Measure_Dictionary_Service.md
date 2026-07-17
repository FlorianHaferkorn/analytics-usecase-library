# Measure Dictionary - Service / Experience

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: SLA Attainment %
  is_kpi_measure: true
  kpi_id_ref: svc.sla.attainment.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: SLA Attainment % = Cases with SLA Met Flag = 1 divided by total cases in period.
    aggregation_method: ratio
  documentation:
    description: Cases meeting SLA divided by total cases.
    notes: 'Grain: day_queue. Unit: %.

      Lineage: fact_cases[SLA Met Flag].

      QA: One row per case; SLA flag logic consistent.

      '
  dependencies:
    columns:
    - fact_cases[SLA Met Flag]
    measures:
    - Cases SLA Met
    - Cases Resolved
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: FCR %
  is_kpi_measure: true
  kpi_id_ref: svc.fcr.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: FCR % = Cases with FCR Flag = 1 divided by total cases.
    aggregation_method: ratio
  documentation:
    description: Cases resolved on first contact divided by total cases.
    notes: 'Grain: day_queue. Unit: %.

      Lineage: fact_cases[FCR Flag].

      QA: Flag accuracy; exclude reopened cases if policy requires.

      '
  dependencies:
    columns:
    - fact_cases[FCR Flag]
    measures:
    - Cases FCR
    - Cases Resolved
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: AHT Minutes
  is_kpi_measure: true
  kpi_id_ref: svc.aht.minutes
  semantic_model: Service_SemanticModel
  display_folder: 02_Efficiency
  category: KPI
  expression:
    logical: AHT Minutes = Total handle time divided by number of cases/contacts.
    aggregation_method: sum
  documentation:
    description: Average handle time per case/contact.
    notes: 'Grain: day_queue. Unit: minutes.

      Lineage: fact_cases[Handle Time Minutes].

      QA: Include talk + wrap; ensure time unit consistency.

      '
  dependencies:
    columns:
    - fact_cases[Handle Time Minutes]
    measures:
    - Total Handle Time Minutes
    - Cases Resolved
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Backlog Count
  is_kpi_measure: true
  kpi_id_ref: svc.backlog.count
  semantic_model: Service_SemanticModel
  display_folder: 03_Backlog
  category: KPI
  expression:
    logical: Backlog Count = Count of open cases at period end.
    aggregation_method: count
  documentation:
    description: Open cases not resolved.
    notes: 'Grain: day_queue. Unit: count.

      Lineage: fact_cases[Backlog Flag/Open Cases].

      QA: One row per case; status logic consistent.

      '
  dependencies:
    measures:
    - Backlog Cases
    columns:
    - fact_cases[Backlog Flag]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Escalation %
  is_kpi_measure: true
  kpi_id_ref: svc.escalation.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: Escalation % = Escalated cases divided by total cases.
    aggregation_method: ratio
  documentation:
    description: Escalated cases / total cases.
    notes: 'Grain: day_queue. Unit: %.

      Lineage: fact_cases[Escalation Flag].

      QA: Escalation definition consistent; total cases > 0.

      '
  dependencies:
    columns:
    - fact_cases[Escalation Flag]
    measures:
    - Escalated Cases
    - Cases Resolved
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Utilization %
  is_kpi_measure: true
  kpi_id_ref: res.utilization.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: Utilization % = Productive time divided by paid time.
    aggregation_method: ratio
  documentation:
    description: Productive time vs paid time.
    notes: 'Grain: agent_day or queue_day. Unit: %.

      Lineage: fact_wfm[Work Time Minutes], fact_wfm[Paid Time Minutes].

      QA: Paid Time > 0; align time zones.

      '
  dependencies:
    columns:
    - fact_wfm[Work Time Minutes]
    - fact_wfm[Paid Time Minutes]
    measures:
    - Work Time Minutes
    - Paid Time Minutes
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Occupancy %
  is_kpi_measure: true
  kpi_id_ref: res.occupancy.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: Occupancy % = (Talk + Wrap) / (Talk + Wrap + Idle).
    aggregation_method: ratio
  documentation:
    description: 'Active vs available time: (Talk + Wrap) / (Talk + Wrap + Idle).'
    notes: 'Grain: agent_day or queue_day. Unit: %.

      Lineage: fact_wfm[Talk Time Minutes], fact_wfm[Wrap Time Minutes], fact_wfm[Idle Time Minutes].

      QA: Ensure no double counting; time totals align.

      '
  dependencies:
    columns:
    - fact_wfm[Talk Time Minutes]
    - fact_wfm[Wrap Time Minutes]
    - fact_wfm[Idle Time Minutes]
    measures:
    - Talk+Wrap Minutes
    - Idle Time Minutes
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Overtime %
  is_kpi_measure: true
  kpi_id_ref: res.overtime.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: Overtime % = Overtime hours divided by total hours.
    aggregation_method: ratio
  documentation:
    description: Overtime minutes / paid time minutes.
    notes: 'Grain: agent_day or region_week. Unit: %.

      Lineage: fact_wfm[Overtime Minutes], fact_wfm[Paid Time Minutes].

      QA: Paid Time > 0; overtime rules consistent.

      '
  dependencies:
    columns:
    - fact_wfm[Overtime Minutes]
    - fact_wfm[Paid Time Minutes]
    measures:
    - Overtime Minutes
    - Paid Time Minutes
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Shrinkage %
  is_kpi_measure: true
  kpi_id_ref: res.shrinkage.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: Shrinkage % = Non-productive time divided by paid time.
    aggregation_method: ratio
  documentation:
    description: Shrinkage minutes / paid time minutes.
    notes: 'Grain: agent_day. Unit: %.

      Lineage: fact_wfm[Shrinkage Minutes], fact_wfm[Paid Time Minutes].

      QA: Paid Time > 0; shrinkage components defined.

      '
  dependencies:
    columns:
    - fact_wfm[Shrinkage Minutes]
    - fact_wfm[Paid Time Minutes]
    measures:
    - Shrinkage Minutes
    - Paid Time Minutes
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Cases Resolved
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: Cases Resolved = Total number of cases in scope.
    aggregation_method: sum
  documentation:
    description: Total number of cases in scope.
    notes: 'Grain: case. Unit: count.

      '
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Cases SLA Met
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: Cases SLA Met = SUM(fact_cases[SLA Met Flag])
    aggregation_method: sum
  documentation:
    description: Cases where SLA was met.
    notes: ''
  dependencies:
    columns:
    - fact_cases[SLA Met Flag]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Cases FCR
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: Cases FCR = SUM(fact_cases[FCR Flag])
    aggregation_method: sum
  documentation:
    description: Cases resolved on first contact.
    notes: ''
  dependencies:
    columns:
    - fact_cases[FCR Flag]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Escalated Cases
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: Escalated Cases = SUM(fact_cases[Escalation Flag])
    aggregation_method: sum
  documentation:
    description: Cases that were escalated.
    notes: ''
  dependencies:
    columns:
    - fact_cases[Escalation Flag]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Backlog Cases
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 03_Backlog
  category: Helper
  expression:
    logical: Backlog Cases = SUM(fact_cases[Backlog Flag])
    aggregation_method: sum
  documentation:
    description: Open cases not yet resolved.
    notes: ''
  dependencies:
    columns:
    - fact_cases[Backlog Flag]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Total Handle Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 02_Efficiency
  category: Base
  expression:
    logical: Total Handle Time Minutes = SUM(fact_cases[Handle Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total handle time across cases.
    notes: ''
  dependencies:
    columns:
    - fact_cases[Handle Time Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Work Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Work Time Minutes = SUM(fact_wfm[Work Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total productive work time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Work Time Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Paid Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Paid Time Minutes = SUM(fact_wfm[Paid Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total paid time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Paid Time Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Talk+Wrap Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Talk+Wrap Minutes = SUM(fact_wfm[Talk Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total talk plus wrap-up time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Talk Time Minutes]
    - fact_wfm[Wrap Time Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Idle Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Idle Time Minutes = SUM(fact_wfm[Idle Time Minutes])
    aggregation_method: sum
  documentation:
    description: Total idle time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Idle Time Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Overtime Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Overtime Minutes = SUM(fact_wfm[Overtime Minutes])
    aggregation_method: sum
  documentation:
    description: Total overtime minutes.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Overtime Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Shrinkage Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Shrinkage Minutes = SUM(fact_wfm[Shrinkage Minutes])
    aggregation_method: sum
  documentation:
    description: Total shrinkage minutes.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Shrinkage Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Talk Wrap Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: Talk Wrap Minutes = SUM(fact_wfm[Talk Wrap Minutes])
    aggregation_method: sum
  documentation:
    description: Total talk + wrap time in minutes.
    notes: 'Source: fact_wfm[Talk Wrap Minutes].'
  dependencies:
    columns:
    - fact_wfm[Talk Wrap Minutes]
  governance:
    owner: Service Analytics
    status: active
    version: v1.2
    last_review: TBD

- measure_name: Tickets Created Count
  is_kpi_measure: true
  kpi_id_ref: svc.tickets.created.count
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: Tickets Created Count = Count of newly created service tickets.
    aggregation_method: count
  documentation:
    description: Count of newly created service tickets.
    notes: 'Grain: ticket_day. Unit: count.

      Lineage: fact_ticket[Ticket ID].

      QA: De-duplicate re-opened tickets if tracked separately.

      '
  dependencies:
    columns:
    - fact_ticket[Ticket ID]
  governance:
    owner: Service Analytics
    status: active
    version: v0.1
    last_review: TBD

- measure_name: Tickets Closed Count
  is_kpi_measure: true
  kpi_id_ref: svc.tickets.closed.count
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: Tickets Closed Count = Count of closed service tickets.
    aggregation_method: count
  documentation:
    description: Count of closed service tickets.
    notes: 'Grain: ticket_day. Unit: count.

      Lineage: fact_ticket[Tickets Closed Count].

      QA: Closure definition consistent with SLA reporting.

      '
  dependencies:
    columns:
    - fact_ticket[Tickets Closed Count]
  governance:
    owner: Service Analytics
    status: active
    version: v0.1
    last_review: TBD

- measure_name: Average Handling Time (minutes)
  is_kpi_measure: true
  kpi_id_ref: svc.aht.minutes
  semantic_model: Service_SemanticModel
  display_folder: 01_Service_Level
  category: KPI
  expression:
    logical: Average Handling Time (minutes) = DIVIDE ( SUM ( fact_support_cases[Handle Time Minutes] ), COUNTROWS ( fact_support_cases ) )
    aggregation_method: average
  documentation:
    description: Display alias for AHT Minutes; measures average time to handle a contact.
    notes: 'Grain: queue_day. Unit: minutes. Lineage: fact_support_cases[Handle Time Minutes].'
  dependencies:
    columns:
    - fact_support_cases[Handle Time Minutes]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: First Contact Resolution %
  is_kpi_measure: true
  kpi_id_ref: svc.fcr.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service_Level
  category: KPI
  expression:
    logical: First Contact Resolution % = DIVIDE ( CALCULATE ( COUNTROWS ( fact_support_cases ), fact_support_cases[FCR Flag] = TRUE() ), COUNTROWS ( fact_support_cases ) )
    aggregation_method: custom
  documentation:
    description: Share of cases solved on first contact without escalation or rework.
    notes: 'Grain: queue_day. Unit: %. Lineage: fact_support_cases[FCR Flag].'
  dependencies:
    columns:
    - fact_support_cases[FCR Flag]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: First Pass Yield % (XD)
  is_kpi_measure: true
  kpi_id_ref: quality.fpy.pct
  semantic_model: Service_SemanticModel
  display_folder: 02_Quality
  category: KPI
  expression:
    logical: First Pass Yield % (XD) = DIVIDE ( CALCULATE ( COUNTROWS ( fact_fulfillment ), fact_fulfillment[In-Full Flag] = TRUE() ), COUNTROWS ( fact_fulfillment ) )
    aggregation_method: custom
  documentation:
    description: Delivery quality proxy via fulfillment in-full rate — Experience domain proxy for First Pass Yield.
    notes: 'Grain: order_day. Unit: %. Lineage: fact_fulfillment[In-Full Flag].'
  dependencies:
    columns:
    - fact_fulfillment[In-Full Flag]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Revenue at Risk Amount (XD)
  is_kpi_measure: true
  kpi_id_ref: crm.revenue_at_risk.amount
  semantic_model: Service_SemanticModel
  display_folder: 03_P&L
  category: KPI
  expression:
    logical: Revenue at Risk Amount (XD) = [Net Sales Amount (XD)] * DIVIDE ( 1 - [Ops OTIF %] + 1 - [First Pass Yield % (XD)], 2 )
    aggregation_method: custom
  documentation:
    description: Net Sales weighted by average of OTIF failure and First Pass Yield failure rates — Experience domain risk proxy.
    notes: 'Grain: month. Unit: EUR. Lineage: [Net Sales Amount (XD)], [Ops OTIF %], [First Pass Yield % (XD)].'
  dependencies:
    measures:
    - '[Net Sales Amount (XD)]'
    - '[Ops OTIF %]'
    - '[First Pass Yield % (XD)]'
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Net Sales Amount (XD)
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 03_P&L
  category: Base
  expression:
    logical: Net Sales Amount (XD) = SUM ( fact_sales[Net Sales Amount] )
    aggregation_method: sum
  documentation:
    description: Total invoiced revenue net of discounts and returns — Experience domain view.
    notes: 'Grain: invoice_line, reported monthly. Unit: EUR. Lineage: fact_sales[Net Sales Amount].'
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Gross Margin % (XD)
  is_kpi_measure: true
  kpi_id_ref: margin.gm.pct
  semantic_model: Service_SemanticModel
  display_folder: 02_Quality
  category: KPI
  expression:
    logical: Gross Margin % (XD) = DIVIDE ( [Net Sales Amount (XD)] - SUM ( fact_sales[Cost of Goods Sold Amount] ), [Net Sales Amount (XD)] )
    aggregation_method: custom
  documentation:
    description: Gross Margin % for Experience domain reporting and cross-domain P&L reconciliation.
    notes: 'Grain: month. Unit: %. Lineage: [Net Sales Amount (XD)], fact_sales[Cost of Goods Sold Amount].'
  dependencies:
    measures:
    - '[Net Sales Amount (XD)]'
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Delta% Net Sales (XD)
  is_kpi_measure: true
  kpi_id_ref: sales.net_sales.delta_pct.ly
  semantic_model: Service_SemanticModel
  display_folder: 03_P&L
  category: KPI
  expression:
    logical: Delta% Net Sales (XD) = DIVIDE ( [Net Sales Amount (XD)] - SUM ( fact_sales[Last Year Sales Amount] ), ABS ( SUM ( fact_sales[Last Year Sales Amount] ) ) )
    aggregation_method: custom
  documentation:
    description: Relative variance of Net Sales vs Last Year — Experience domain view.
    notes: 'Grain: month. Unit: %. Lineage: [Net Sales Amount (XD)], fact_sales[Last Year Sales Amount].'
  dependencies:
    measures:
    - '[Net Sales Amount (XD)]'
    columns:
    - fact_sales[Last Year Sales Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: DSO Days (XD)
  is_kpi_measure: true
  kpi_id_ref: wc.dso.days
  semantic_model: Service_SemanticModel
  display_folder: 04_WorkingCapital
  category: KPI
  expression:
    logical: DSO Days (XD) = DIVIDE ( SUM ( fact_sales[Net Sales Amount] ) * 0.12 * 365, SUM ( fact_sales[Net Sales Amount] ) )
    aggregation_method: custom
  documentation:
    description: Receivables days estimate for CCC cross-domain view — Experience domain proxy.
    notes: 'Grain: month. Unit: days. Lineage: fact_sales[Net Sales Amount] (scaled proxy).'
  dependencies:
    columns:
    - fact_sales[Net Sales Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: DIO Days (XD)
  is_kpi_measure: true
  kpi_id_ref: wc.dio.days
  semantic_model: Service_SemanticModel
  display_folder: 04_WorkingCapital
  category: KPI
  expression:
    logical: DIO Days (XD) = DIVIDE ( SUM ( fact_sales[Cost of Goods Sold Amount] ) * 0.15 * 365, SUM ( fact_sales[Cost of Goods Sold Amount] ) )
    aggregation_method: custom
  documentation:
    description: Inventory days estimate for CCC cross-domain view — Experience domain proxy.
    notes: 'Grain: month. Unit: days. Lineage: fact_sales[Cost of Goods Sold Amount] (scaled proxy).'
  dependencies:
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: DPO Days (XD)
  is_kpi_measure: true
  kpi_id_ref: wc.dpo.days
  semantic_model: Service_SemanticModel
  display_folder: 04_WorkingCapital
  category: KPI
  expression:
    logical: DPO Days (XD) = DIVIDE ( SUM ( fact_sales[Cost of Goods Sold Amount] ) * 0.08 * 365, SUM ( fact_sales[Cost of Goods Sold Amount] ) )
    aggregation_method: custom
  documentation:
    description: Payables days estimate for CCC cross-domain view — Experience domain proxy.
    notes: 'Grain: month. Unit: days. Lineage: fact_sales[Cost of Goods Sold Amount] (scaled proxy).'
  dependencies:
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Action Outcome Rate % (XD Log)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_outcome_rate.pct
  semantic_model: Service_SemanticModel
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Outcome Rate % (XD Log) = DIVIDE ( CALCULATE ( COUNTROWS ( fact_action_log ), fact_action_log[Outcome Status] = "Achieved" ), COUNTROWS ( fact_action_log ) )
    aggregation_method: custom
  documentation:
    description: Measures share of actions that achieved the intended outcome — routed actions log view.
    notes: 'Grain: month. Unit: %. Lineage: fact_action_log[Outcome Status].'
  dependencies:
    columns:
    - fact_action_log[Outcome Status]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026

- measure_name: Actions Executed Count (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.actions_executed.count
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Actions Executed Count (XD) = COUNTROWS ( FILTER ( fact_action_outcome, NOT ISBLANK ( fact_action_outcome[outcome_status] ) ) )
    aggregation_method: count
  documentation:
    notes: 'Grain: month. Unit: count. Lineage: fact_action_outcome[outcome_status].'
    description: Number of action codes with a recorded outcome — Service cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Service BI
  semantic_model: Service_SemanticModel

- measure_name: Action Outcome Rate % (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_outcome_rate.pct
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Outcome Rate % (XD) = DIVIDE ( CALCULATE ( COUNTROWS ( fact_action_outcome ), fact_action_outcome[outcome_status] = "achieved" ), COUNTROWS ( fact_action_outcome ) )
    aggregation_method: custom
  documentation:
    notes: 'Grain: month. Unit: %. Lineage: fact_action_outcome[outcome_status].'
    description: Percentage of executed actions with a confirmed achieved outcome — Service cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Service BI
  semantic_model: Service_SemanticModel

- measure_name: Avg Time-to-Outcome Days (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.avg_time_to_outcome.days
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Avg Time-to-Outcome Days (XD) = AVERAGEX ( fact_action_outcome, fact_action_outcome[days_to_outcome] )
    aggregation_method: average
  documentation:
    notes: 'Grain: month. Unit: days. Lineage: fact_action_outcome[days_to_outcome].'
    description: Average days between action execution and outcome confirmation — Service cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[days_to_outcome]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Service BI
  semantic_model: Service_SemanticModel

- measure_name: Action ROI % (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_roi.pct
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action ROI % (XD) = DIVIDE ( SUMX ( fact_action_outcome, fact_action_outcome[impact_value] ), SUMX ( fact_action_outcome, fact_action_outcome[cost_to_execute] ) ) - 1
    aggregation_method: custom
  documentation:
    notes: 'Grain: month. Unit: %. Lineage: fact_action_outcome[impact_value], fact_action_outcome[cost_to_execute].'
    description: Average ROI of executed actions — Service cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[cost_to_execute]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Service BI
  semantic_model: Service_SemanticModel

- measure_name: Action Effectiveness Delta (XD)
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_effectiveness_delta.amount
  display_folder: 08_Action_Outcomes
  category: KPI
  expression:
    logical: Action Effectiveness Delta (XD) = AVERAGEX ( FILTER ( fact_action_outcome, fact_action_outcome[outcome_status] = "achieved" ), fact_action_outcome[impact_value] )
    aggregation_method: average
  documentation:
    notes: 'Grain: month. Unit: EUR. Lineage: fact_action_outcome[impact_value], fact_action_outcome[outcome_status].'
    description: Average EUR impact per achieved action execution — Service cross-domain proxy.
  dependencies:
    columns:
    - fact_action_outcome[impact_value]
    - fact_action_outcome[outcome_status]
  governance:
    status: active
    version: v1.0
    last_review: 28.04.2026
    owner: Service BI
  semantic_model: Service_SemanticModel

- measure_name: Cost of Goods Sold Amount (XD)
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 03_P&L
  category: Base
  expression:
    logical: Cost of Goods Sold Amount (XD) = SUM ( fact_sales[Cost of Goods Sold Amount] )
    aggregation_method: sum
  documentation:
    description: Total cost of goods sold — Experience domain base measure for cross-domain margin calculations.
    notes: 'Grain: invoice_line, reported monthly. Unit: EUR. Lineage: fact_sales[Cost of Goods Sold Amount].'
  dependencies:
    columns:
    - fact_sales[Cost of Goods Sold Amount]
  governance:
    owner: Service BI
    status: active
    version: v1.0
    last_review: 28.04.2026
```

