# XD-002 – Resource Utilization (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/experience.yaml`
- **Semantic Model Definition:** `semantic_models/domains/experience/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: XD-002)

---

## 1. Data Contract (Scope for XD-002)

```yaml
dimension:
  - name: dim_date
    columns:
      - { name: DateKey, type: int, role: key }
      - { name: Date, type: date }
      - { name: Year, type: int }
      - { name: Month, type: text }
      - { name: Week, type: int }
      - { name: Day, type: int }
      - { name: Interval, type: text }   # e.g., HH:MM block

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }

  - name: dim_channel
    columns:
      - { name: ChannelKey, type: int, role: key }
      - { name: Channel, type: text }

  - name: dim_queue
    columns:
      - { name: QueueKey, type: int, role: key }
      - { name: QueueName, type: text }
      - { name: Priority, type: text }
      - { name: Product, type: text }
      - { name: Segment, type: text }

  - name: dim_agent
    columns:
      - { name: AgentKey, type: int, role: key }
      - { name: AgentName, type: text }
      - { name: SkillGroup, type: text }

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }

fact:
  - name: fact_wfm_schedule
    grain: agent_interval
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ChannelKey, type: int, ref: dim_channel }
      - { name: QueueKey, type: int, ref: dim_queue }
      - { name: AgentKey, type: int, ref: dim_agent }
      - { name: PaidMinutes, type: number, agg: sum }
      - { name: PlannedWorkMinutes, type: number, agg: sum }
      - { name: OvertimeMinutes, type: number, agg: sum }
      - { name: ShrinkageMinutes, type: number, agg: sum }

  - name: fact_wfm_actuals
    grain: agent_interval
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ChannelKey, type: int, ref: dim_channel }
      - { name: QueueKey, type: int, ref: dim_queue }
      - { name: AgentKey, type: int, ref: dim_agent }
      - { name: LoggedInMinutes, type: number, agg: sum }
      - { name: HandleMinutes, type: number, agg: sum }
      - { name: WrapMinutes, type: number, agg: sum }
      - { name: IdleMinutes, type: number, agg: sum }

  - name: fact_workload
    grain: queue_interval
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ChannelKey, type: int, ref: dim_channel }
      - { name: QueueKey, type: int, ref: dim_queue }
      - { name: Volume, type: int, agg: sum }
      - { name: SLA_Attained, type: int, agg: sum }
      - { name: SLA_Target, type: int, agg: sum }
      - { name: BacklogCount, type: int, agg: avg }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_wfm_schedule → `exp.fact_wfm_schedule`
- fact_wfm_actuals → `exp.fact_wfm_actuals`
- fact_workload → `exp.fact_workload`
- dim_* → shared/experience dimensions
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `experience_resource_utilization`

**Tables:** fact_wfm_schedule, fact_wfm_actuals, fact_workload, dim_date, dim_org, dim_channel, dim_queue, dim_agent, security_user_org (RLS only)

**Relationships**
- fact_wfm_schedule/actuals/workload[DateKey] → dim_date[DateKey] (1:* | single)
- fact_*[OrgKey] → dim_org[OrgKey]; fact_*[ChannelKey] → dim_channel[ChannelKey]; fact_*[QueueKey] → dim_queue[QueueKey]
- fact_*[AgentKey] → dim_agent[AgentKey] (schedule/actuals only)
- security_user_org attribute join to dim_org by Region/Country (RLS mapping)

**Hierarchies**
- Org: Region > Country
- Queue: Segment > QueueName > Priority
- Date: Year > Month > Week > Date > Interval
- Channel: Channel

**Display Folders**
- 01_Productivity: Utilization %, Occupancy %, AHT
|- 02_Cost: Overtime %, Shrinkage %
|- 03_Service: SLA %, Backlog

---

## 3. Measure Inventory

| Measure Name        | kpi_id                   | Type       | Folder           | Format |
|---------------------|--------------------------|------------|------------------|--------|
| Utilization %       | res.utilization.pct      | KPI        | 01_Productivity  | 0.0 % |
| Occupancy %         | res.occupancy.pct        | KPI        | 01_Productivity  | 0.0 % |
| Overtime %          | res.overtime.pct         | KPI        | 02_Cost          | 0.0 % |
| Shrinkage %         | res.shrinkage.pct        | KPI        | 02_Cost          | 0.0 % |
| SLA Attainment %    | svc.sla.attainment.pct   | KPI        | 03_Service       | 0.0 % |
| Backlog Count       | svc.backlog.count        | KPI        | 03_Service       | #,0   |
| Volume              | svc.volume.count         | Supporting | 03_Service       | #,0   |

---

## 4. Measures (DAX)

```DAX
Utilization % =
DIVIDE (
    SUM ( fact_wfm_actuals[HandleMinutes] ) + SUM ( fact_wfm_actuals[WrapMinutes] ),
    SUM ( fact_wfm_schedule[PaidMinutes] )
)
```

```DAX
Occupancy % =
DIVIDE (
    SUM ( fact_wfm_actuals[HandleMinutes] ) + SUM ( fact_wfm_actuals[WrapMinutes] ),
    SUM ( fact_wfm_actuals[LoggedInMinutes] )
)
```

```DAX
Overtime % =
DIVIDE ( SUM ( fact_wfm_schedule[OvertimeMinutes] ), SUM ( fact_wfm_schedule[PaidMinutes] ) )
```

```DAX
Shrinkage % =
DIVIDE ( SUM ( fact_wfm_schedule[ShrinkageMinutes] ), SUM ( fact_wfm_schedule[PaidMinutes] ) )
```

```DAX
SLA Attainment % =
DIVIDE ( SUM ( fact_workload[SLA_Attained] ), SUM ( fact_workload[SLA_Target] ) )
```

```DAX
Backlog Count = AVERAGE ( fact_workload[BacklogCount] )
```

```DAX
Volume = SUM ( fact_workload[Volume] )
```

---

## 5. Defaults & Formatting

| Field/Measure                           | Format | Summarization | Display Folder   |
|-----------------------------------------|--------|---------------|------------------|
| Utilization %, Occupancy %, Overtime %, Shrinkage %, SLA % | 0.0 % | None | 01/02/03       |
| Backlog Count, Volume                   | #,0    | Sum/Avg       | 03_Service       |
| Time fields (minutes)                   | #,0.0  | Sum           | 01_Productivity  |

---

## 6. Visual Requirements (Technical)
- KPI cards: Utilization %, Occupancy %, SLA %, Overtime %, Shrinkage %, Backlog.
- Trend: Occupancy %, Utilization %, SLA % by dim_date[Week/Day]; slicer by Channel/Queue.
|- Column: Utilization % vs target by Queue; Overtime % by Week.
|- Backlog by Queue/Priority; Capacity vs Volume by interval.
|- Matrix: Region > Channel > Queue > Interval with Utilization %, Occupancy %, SLA %, Backlog; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; apply Region/Country filters on dim_org and propagate to facts.
- OLS (optional): hide AgentName for privacy; restrict overtime details for external viewers.

---

## 8. Performance & Refresh
- Storage: Import; incremental by day/week; archive granular intervals older than 90 days to weekly aggregates.
- Partition fact_wfm_actuals/schedule by Date; pre-calc interval buckets in source.
- Avoid calculated columns; maintain targets and interval calendars upstream.
- Consider aggregation table Week x Queue x Channel for long history if >50M rows.

---

## 9. QA & Validation

| Check Type                  | Object                         | Rule                                         | Tolerance |
|-----------------------------|--------------------------------|----------------------------------------------|-----------|
| Referential Integrity       | facts → dimensions             | ≥ 99.9 % matched keys                        | 0.1 %     |
| Utilization/Occupancy Calc  | Minutes balance                | Paid vs Logged vs Handle/Wrap/Idle balance   | ±2 %      |
| SLA Calculation             | SLA_Attained vs SLA_Target     | Matches operational SLA reporting            | ±1.0 pp   |
| Overtime Capture            | OvertimeMinutes completeness   | Coverage ≥ 98 %                              | 2 % gap   |
| Interval Coverage           | Intervals per day              | No gaps for open hours                       | informational |
