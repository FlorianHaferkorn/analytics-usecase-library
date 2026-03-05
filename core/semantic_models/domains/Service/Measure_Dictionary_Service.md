# Measure Dictionary - Service / Experience

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: SLA Attainment %
  is_kpi_measure: true
  kpi_id_ref: svc.sla.attainment.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: FCR %
  is_kpi_measure: true
  kpi_id_ref: svc.fcr.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: AHT Minutes
  is_kpi_measure: true
  kpi_id_ref: svc.aht.minutes
  semantic_model: Service_SemanticModel
  display_folder: 02_Efficiency
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Backlog Count
  is_kpi_measure: true
  kpi_id_ref: svc.backlog.count
  semantic_model: Service_SemanticModel
  display_folder: 03_Backlog
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: NPS Index
  is_kpi_measure: true
  kpi_id_ref: svc.nps.index
  semantic_model: Service_SemanticModel
  display_folder: 04_Experience
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: 'NPS score from surveys: %Promoters - %Detractors.'
    notes: 'Grain: month. Unit: index.

      Lineage: fact_nps[NPS Score].

      QA: Score in [0;10]; promoter/detractor rules consistent.

      '
  dependencies:
    columns:
    - fact_nps[NPS Score]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Escalation %
  is_kpi_measure: true
  kpi_id_ref: svc.escalation.pct
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Utilization %
  is_kpi_measure: true
  kpi_id_ref: res.utilization.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Occupancy %
  is_kpi_measure: true
  kpi_id_ref: res.occupancy.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: 'Active vs available time: (Talk + Wrap) / (Talk + Wrap + Idle).'
    notes: 'Grain: agent_day or queue_day. Unit: %.

      Lineage: fact_wfm[Talk Time Minutes], fact_wfm[Wrap Time Minutes], fact_wfm[Idle
      Time Minutes].

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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Overtime %
  is_kpi_measure: true
  kpi_id_ref: res.overtime.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Shrinkage %
  is_kpi_measure: true
  kpi_id_ref: res.shrinkage.pct
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Cases Resolved
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total number of cases in scope.
    notes: 'Grain: case. Unit: count.

      '
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Cases SLA Met
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Cases where SLA was met.
    notes: ''
  dependencies:
    columns:
    - fact_cases[SLA Met Flag]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Cases FCR
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Cases resolved on first contact.
    notes: ''
  dependencies:
    columns:
    - fact_cases[FCR Flag]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Escalated Cases
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: Helper
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Cases that were escalated.
    notes: ''
  dependencies:
    columns:
    - fact_cases[Escalation Flag]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Backlog Cases
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 03_Backlog
  category: Helper
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Open cases not yet resolved.
    notes: ''
  dependencies:
    columns:
    - fact_cases[Backlog Flag]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Total Handle Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 02_Efficiency
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total handle time across cases.
    notes: ''
  dependencies:
    columns:
    - fact_cases[Handle Time Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Work Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total productive work time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Work Time Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Paid Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total paid time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Paid Time Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Talk+Wrap Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total talk plus wrap-up time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Talk Time Minutes]
    - fact_wfm[Wrap Time Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Idle Time Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total idle time.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Idle Time Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Overtime Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total overtime minutes.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Overtime Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Shrinkage Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total shrinkage minutes.
    notes: ''
  dependencies:
    columns:
    - fact_wfm[Shrinkage Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Talk Wrap Minutes
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Service_SemanticModel
  display_folder: 05_Workforce
  category: Base
  expression:
    logical: 'Fabric: see overlay / TMDL.'
  documentation:
    description: Total talk + wrap time in minutes.
    notes: 'Source: fact_wfm[Talk Wrap Minutes].'
  dependencies:
    columns:
    - fact_wfm[Talk Wrap Minutes]
  governance:
    owner: Service Analytics
    status: draft
    version: v1.2
    last_review: TBD
- measure_name: Tickets Created Count
  is_kpi_measure: true
  kpi_id_ref: svc.tickets.created.count
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v0.1
    last_review: TBD
- measure_name: Tickets Closed Count
  is_kpi_measure: true
  kpi_id_ref: svc.tickets.closed.count
  semantic_model: Service_SemanticModel
  display_folder: 01_Service
  category: KPI
  expression:
    logical: 'Fabric: see overlay / TMDL.'
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
    status: draft
    version: v0.1
    last_review: TBD
```

