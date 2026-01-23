# KPI Catalog - Service & Experience

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
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
    - Cases SLA Met
    - Cases Resolved
    lineage:
    - fact_cases[SLA Met Flag]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: svc.fcr.pct
  kpi_key: First Contact Resolution %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
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
    - Cases FCR
    - Cases Resolved
    lineage:
    - fact_cases[FCR Flag]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: svc.aht.minutes
  kpi_key: Average Handling Time (minutes)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
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
    - Total Handle Time Minutes
    - Cases Resolved
    lineage:
    - fact_cases[Handle Time Minutes]
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
    completeness_score: 0.9
    last_review: TBD

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
    - Backlog Cases
    lineage:
    - fact_cases[Backlog Flag]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: svc.nps.index
  kpi_key: NPS Index
  kpi_type: index
  kpi_role: strategic
  impact_dimension: Experience
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
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
    - fact_nps[NPS Score]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: svc.escalation.pct
  kpi_key: Escalation %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
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
    - Escalated Cases
    - Cases Resolved
    lineage:
    - fact_cases[Escalation Flag]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: res.utilization.pct
  kpi_key: Utilization %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
  calc_type: ratio
  business:
    purpose: Measures productive time versus paid time for agents.
    definition: Productive time divided by paid time.
    grain_scope: agent_day or queue_day; aggregated to week/month.
    unit_format: '% (1 decimal)'
    interpretation: Typical healthy band 75�85%; balance with SLA/NPS.
  technical:
    dax_name: Utilization %
    depends_on_measures:
    - Utilization %
    lineage:
    - fact_wfm[Work Time]
    - fact_wfm[Paid Time]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: res.occupancy.pct
  kpi_key: Occupancy %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
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
    - fact_wfm[Talk]
    - fact_wfm[Wrap]
    - fact_wfm[Idle]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: res.overtime.pct
  kpi_key: Overtime %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
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
    - fact_wfm[Overtime Hours]
    - fact_wfm[Total Hours]
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
    completeness_score: 0.9
    last_review: TBD

- kpi_id: res.shrinkage.pct
  kpi_key: Shrinkage %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Workforce
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-002
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
    - fact_wfm[Shrinkage]
    - fact_wfm[Paid Time]
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
    completeness_score: 0.9
    last_review: TBD

```

## KPIs - Supporting / Diagnostic

```yaml
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
  calc_type: count
  business:
    purpose: Counts customer service tickets created in the period.
    definition: Count of newly created service tickets.
    grain_scope: Ticket; aggregated by period and channel.
    unit_format: count
    interpretation: Higher counts indicate higher inbound demand.
  technical:
    dax_name: Tickets Created Count
    depends_on_measures: []
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
    last_review: TBD

- kpi_id: svc.tickets.closed.count
  kpi_key: Tickets Closed Count
  kpi_type: activity
  kpi_role: supporting
  impact_dimension: Service
  domain_tag:
  - Service & Experience
  use_case_ref:
  - XD-001
  - XD-002
  calc_type: count
  business:
    purpose: Counts customer service tickets closed in the period.
    definition: Count of closed service tickets.
    grain_scope: Ticket; aggregated by period and channel.
    unit_format: count
    interpretation: Higher counts indicate higher resolution throughput.
  technical:
    dax_name: Tickets Closed Count
    depends_on_measures: []
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
    last_review: TBD
```

