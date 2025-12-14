# Measure Dictionary - Service / Experience

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "SLA Attainment %"
  is_kpi_measure: true
  kpi_id_ref: "svc.sla.attainment.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "01_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Cases = COUNTROWS ( fact_cases )
      VAR Met   = SUM ( fact_cases[SLA Met Flag] )
      RETURN DIVIDE ( Met, Cases )
    formatString: "0.0%"
  documentation:
    description: "Cases meeting SLA divided by total cases."
    notes: |
      Grain: day_queue. Unit: %.
      Lineage: fact_cases[SLA Met Flag].
      QA: One row per case; SLA flag logic consistent.
  dependencies:
    columns:
      - "fact_cases[SLA Met Flag]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "First Contact Resolution %"
  is_kpi_measure: true
  kpi_id_ref: "svc.fcr.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "01_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Cases = COUNTROWS ( fact_cases )
      VAR Fcr   = SUM ( fact_cases[FCR Flag] )
      RETURN DIVIDE ( Fcr, Cases )
    formatString: "0.0%"
  documentation:
    description: "Cases resolved on first contact divided by total cases."
    notes: |
      Grain: day_queue. Unit: %.
      Lineage: fact_cases[FCR Flag].
      QA: Flag accuracy; exclude reopened cases if policy requires.
  dependencies:
    columns:
      - "fact_cases[FCR Flag]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Average Handling Time (minutes)"
  is_kpi_measure: true
  kpi_id_ref: "svc.aht.minutes"
  semantic_model: "Service_SemanticModel"
  display_folder: "02_Efficiency"
  category: "KPI"
  expression:
    dax: |
      DIVIDE ( SUM ( fact_cases[Handle Time] ), COUNTROWS ( fact_cases ) )
    formatString: "0.0"
  documentation:
    description: "Average handle time per case/contact."
    notes: |
      Grain: day_queue. Unit: minutes.
      Lineage: fact_cases[Handle Time].
      QA: Include talk + wrap; ensure time unit consistency.
  dependencies:
    columns:
      - "fact_cases[Handle Time]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Backlog Count"
  is_kpi_measure: true
  kpi_id_ref: "svc.backlog.count"
  semantic_model: "Service_SemanticModel"
  display_folder: "03_Backlog"
  category: "KPI"
  expression:
    dax: "SUM(fact_cases[Backlog Flag])"
    formatString: "#,0"
  documentation:
    description: "Open cases not resolved."
    notes: |
      Grain: day_queue. Unit: count.
      Lineage: fact_cases[Backlog Flag/Open Cases].
      QA: One row per case; status logic consistent.
  dependencies:
    columns:
      - "fact_cases[Backlog Flag]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "NPS Index"
  is_kpi_measure: true
  kpi_id_ref: "svc.nps.index"
  semantic_model: "Service_SemanticModel"
  display_folder: "04_Experience"
  category: "KPI"
  expression:
    dax: |
      VAR Responses = COUNTROWS ( fact_nps )
      VAR Promoters = SUM ( fact_nps[Is Promoter] )
      VAR Detractors = SUM ( fact_nps[Is Detractor] )
      VAR PromoterPct = DIVIDE ( Promoters, Responses )
      VAR DetractorPct = DIVIDE ( Detractors, Responses )
      RETURN ( PromoterPct - DetractorPct ) * 100
    formatString: "0.0"
  documentation:
    description: "NPS score from surveys: %Promoters - %Detractors."
    notes: |
      Grain: month. Unit: index.
      Lineage: fact_nps[NPS Score].
      QA: Score in [0;10]; promoter/detractor rules consistent.
  dependencies:
    columns:
      - "fact_nps[NPS Score]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Escalation %"
  is_kpi_measure: true
  kpi_id_ref: "svc.escalation.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "01_Service"
  category: "KPI"
  expression:
    dax: |
      VAR Cases = COUNTROWS ( fact_cases )
      VAR Escalated = SUM ( fact_cases[Escalation Flag] )
      RETURN DIVIDE ( Escalated, Cases )
    formatString: "0.0%"
  documentation:
    description: "Escalated cases / total cases."
    notes: |
      Grain: day_queue. Unit: %.
      Lineage: fact_cases[Escalation Flag].
      QA: Escalation definition consistent; total cases > 0.
  dependencies:
    columns:
      - "fact_cases[Escalation Flag]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Utilization %"
  is_kpi_measure: true
  kpi_id_ref: "res.utilization.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "05_Workforce"
  category: "KPI"
  expression:
    dax: |
      VAR Work = SUM ( fact_wfm[Work Time] )
      VAR Paid = SUM ( fact_wfm[Paid Time] )
      RETURN DIVIDE ( Work, Paid )
    formatString: "0.0%"
  documentation:
    description: "Productive time vs paid time."
    notes: |
      Grain: agent_day or queue_day. Unit: %.
      Lineage: fact_wfm[Work Time], fact_wfm[Paid Time].
      QA: Paid Time > 0; align time zones.
  dependencies:
    columns:
      - "fact_wfm[Work Time]"
      - "fact_wfm[Paid Time]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Occupancy %"
  is_kpi_measure: true
  kpi_id_ref: "res.occupancy.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "05_Workforce"
  category: "KPI"
  expression:
    dax: |
      VAR TalkWrap = SUM ( fact_wfm[Talk] ) + SUM ( fact_wfm[Wrap] )
      VAR Idle    = SUM ( fact_wfm[Idle] )
      RETURN DIVIDE ( TalkWrap, TalkWrap + Idle )
    formatString: "0.0%"
  documentation:
    description: "Active vs available time: (Talk + Wrap) / (Talk + Wrap + Idle)."
    notes: |
      Grain: agent_day or queue_day. Unit: %.
      Lineage: fact_wfm[Talk], fact_wfm[Wrap], fact_wfm[Idle].
      QA: Ensure no double counting; time totals align.
  dependencies:
    columns:
      - "fact_wfm[Talk]"
      - "fact_wfm[Wrap]"
      - "fact_wfm[Idle]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Overtime %"
  is_kpi_measure: true
  kpi_id_ref: "res.overtime.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "05_Workforce"
  category: "KPI"
  expression:
    dax: |
      VAR OT    = SUM ( fact_wfm[Overtime Hours] )
      VAR Total = SUM ( fact_wfm[Total Hours] )
      RETURN DIVIDE ( OT, Total )
    formatString: "0.0%"
  documentation:
    description: "Overtime hours / total hours."
    notes: |
      Grain: agent_day or region_week. Unit: %.
      Lineage: fact_wfm[Overtime Hours], fact_wfm[Total Hours].
      QA: Total Hours > 0; overtime rules consistent.
  dependencies:
    columns:
      - "fact_wfm[Overtime Hours]"
      - "fact_wfm[Total Hours]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Shrinkage %"
  is_kpi_measure: true
  kpi_id_ref: "res.shrinkage.pct"
  semantic_model: "Service_SemanticModel"
  display_folder: "05_Workforce"
  category: "KPI"
  expression:
    dax: |
      DIVIDE ( SUM ( fact_wfm[Shrinkage] ), SUM ( fact_wfm[Paid Time] ) )
    formatString: "0.0%"
  documentation:
    description: "Non-productive time / paid time."
    notes: |
      Grain: agent_day. Unit: %.
      Lineage: fact_wfm[Shrinkage], fact_wfm[Paid Time].
      QA: Paid Time > 0; shrinkage components defined.
  dependencies:
    columns:
      - "fact_wfm[Shrinkage]"
      - "fact_wfm[Paid Time]"
  governance:
    owner: "Service Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
