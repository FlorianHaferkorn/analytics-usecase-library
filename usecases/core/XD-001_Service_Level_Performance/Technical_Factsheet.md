# XD-001 – Service Level Performance (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/experience.yaml`
- **Semantic Model Definition:** `semantic_models/domains/experience/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: XD-001)

---

## 1. Data Contract (Scope for XD-001)

```yaml
dimension:
  - name: dim_date
    columns:
      - { name: DateKey, type: int, role: key }
      - { name: Date, type: date }
      - { name: Year, type: int }
      - { name: Quarter, type: text }
      - { name: Month, type: text }
      - { name: Week, type: int }
      - { name: DayOfWeek, type: text }

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }

  - name: dim_channel
    columns:
      - { name: ChannelKey, type: int, role: key }
      - { name: Channel, type: text }          # Phone, Chat, Email, Social, App

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

  - name: dim_sla
    columns:
      - { name: SLAKey, type: int, role: key }
      - { name: QueueKey, type: int }
      - { name: SLA_Target_Minutes, type: number }
      - { name: SLA_Type, type: text }      # response / resolution

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }

fact:
  - name: fact_interaction
    grain: interaction
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ChannelKey, type: int, ref: dim_channel }
      - { name: QueueKey, type: int, ref: dim_queue }
      - { name: AgentKey, type: int, ref: dim_agent, nullable: true }
      - { name: SLAKey, type: int, ref: dim_sla, nullable: true }
      - { name: IsWithinSLA, type: boolean }
      - { name: IsResolved, type: boolean }
      - { name: IsEscalated, type: boolean }
      - { name: HandleTimeMinutes, type: number, agg: sum }
      - { name: WaitTimeMinutes, type: number, agg: sum }
      - { name: Volume, type: int, agg: sum }

  - name: fact_backlog
    grain: queue_day
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: QueueKey, type: int, ref: dim_queue }
      - { name: BacklogCount, type: int, agg: avg }

  - name: fact_experience
    grain: survey
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ChannelKey, type: int, ref: dim_channel }
      - { name: QueueKey, type: int, ref: dim_queue }
      - { name: NPSIndex, type: number, agg: avg }
      - { name: CSATScore, type: number, agg: avg }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_interaction → `exp.fact_interaction`
- fact_backlog → `exp.fact_backlog`
- fact_experience → `exp.fact_experience`
- dim_* → corresponding shared/exp dimensions
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `experience_service_performance`

**Tables:** fact_interaction, fact_backlog, fact_experience, dim_date, dim_org, dim_channel, dim_queue, dim_agent, dim_sla, security_user_org (RLS only)

**Relationships**
- fact_interaction[DateKey] → dim_date[DateKey]; fact_backlog[DateKey] → dim_date[DateKey]; fact_experience[DateKey] → dim_date[DateKey]
- fact_interaction[OrgKey] → dim_org[OrgKey]; fact_experience[OrgKey] → dim_org[OrgKey]
- fact_interaction[ChannelKey] → dim_channel[ChannelKey]; fact_experience[ChannelKey] → dim_channel[ChannelKey]
- fact_interaction[QueueKey] → dim_queue[QueueKey]; fact_backlog[QueueKey] → dim_queue[QueueKey]; fact_experience[QueueKey] → dim_queue[QueueKey]
- fact_interaction[AgentKey] → dim_agent[AgentKey] (optional)
- fact_interaction[SLAKey] → dim_sla[SLAKey] (optional)
- security_user_org attribute join to dim_org by Region/Country (RLS mapping)

**Hierarchies**
- Org: Region > Country
- Queue: Segment > QueueName > Priority
- Date: Year > Quarter > Month > Week > Date
- Channel: Channel

**Display Folders**
- 01_SLA: SLA Attainment %, Wait/Handle times
- 02_Quality: FCR %, Escalation %
- 03_Capacity: Backlog, Volume
- 04_Experience: NPS/CSAT

---

## 3. Measure Inventory

| Measure Name               | kpi_id                        | Type       | Folder       | Format  |
|----------------------------|-------------------------------|------------|--------------|---------|
| SLA Attainment %           | svc.sla.attainment.pct        | KPI        | 01_SLA       | 0.0 %  |
| First Contact Resolution % | svc.fcr.pct                   | KPI        | 02_Quality   | 0.0 %  |
| Escalation Rate %          | svc.escalation.pct            | KPI        | 02_Quality   | 0.0 %  |
| Average Handle Time (min)  | svc.aht.minutes               | KPI        | 01_SLA       | #,0.0  |
| Backlog Count              | svc.backlog.count             | KPI        | 03_Capacity  | #,0    |
| NPS Index                  | svc.nps.index                 | KPI        | 04_Experience| #,0.0  |
| Volume                     | svc.volume.count              | Supporting | 03_Capacity  | #,0    |

---

## 4. Measures (DAX)

```DAX
SLA Attainment % =
DIVIDE (
    SUMX ( fact_interaction, IF ( fact_interaction[IsWithinSLA], fact_interaction[Volume], 0 ) ),
    SUM ( fact_interaction[Volume] )
)
```

```DAX
First Contact Resolution % =
DIVIDE (
    SUMX ( fact_interaction, IF ( fact_interaction[IsResolved], fact_interaction[Volume], 0 ) ),
    SUM ( fact_interaction[Volume] )
)
```

```DAX
Escalation Rate % =
DIVIDE (
    SUMX ( fact_interaction, IF ( fact_interaction[IsEscalated], fact_interaction[Volume], 0 ) ),
    SUM ( fact_interaction[Volume] )
)
```

```DAX
Average Handle Time (min) =
DIVIDE ( SUM ( fact_interaction[HandleTimeMinutes] ), SUM ( fact_interaction[Volume] ) )
```

```DAX
Backlog Count = AVERAGE ( fact_backlog[BacklogCount] )
```

```DAX
NPS Index = AVERAGE ( fact_experience[NPSIndex] )
```

```DAX
Volume = SUM ( fact_interaction[Volume] )
```

---

## 5. Defaults & Formatting

| Field/Measure                              | Format | Summarization | Display Folder  |
|--------------------------------------------|--------|---------------|-----------------|
| SLA %, FCR %, Escalation %                 | 0.0 %  | None          | 01_SLA / 02_Quality |
| AHT (minutes)                              | #,0.0  | Average       | 01_SLA          |
| Backlog Count, Volume                      | #,0    | Sum/Avg       | 03_Capacity     |
| NPS Index                                  | #,0.0  | Average       | 04_Experience   |

---

## 6. Visual Requirements (Technical)
- KPI cards: SLA %, FCR %, AHT, Backlog, NPS, Escalation %.
- Trend: SLA %, FCR %, AHT by dim_date[Week/Month].
- Bar: SLA %, FCR %, Escalation % by dim_queue[QueueName]/dim_channel[Channel].
- Scatter: AHT vs Volume by channel/queue.
- Matrix: Region > Channel > Queue with SLA %, FCR %, AHT, Backlog, NPS; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; apply Region/Country filters on dim_org and propagate to facts.
- OLS (optional): hide AgentName for privacy in external views; restrict NPS verbatim if added later.

---

## 8. Performance & Refresh
- Storage: Import; incremental by day/week; aggregate older history weekly.
- Partition fact_interaction by Date; pre-calculate SLA target match in source if possible.
- Avoid calculated columns; maintain SLA mapping table upstream.
- Consider summarised table by Week x Queue for long history if >50M rows.

---

## 9. QA & Validation

| Check Type                  | Object                         | Rule                                        | Tolerance |
|-----------------------------|--------------------------------|---------------------------------------------|-----------|
| Referential Integrity       | facts → dimensions             | ≥ 99.9 % matched keys                       | 0.1 %     |
| SLA Calculation             | IsWithinSLA flag accuracy      | Matches operational SLA reporting           | ±1.0 pp   |
| FCR Calculation             | Resolved vs Volume             | Consistent with process definition          | ±1.0 pp   |
| Backlog Consistency         | Backlog vs arrivals/completions| Balance within tolerance                    | ±2 %      |
| Survey Coverage             | NPS/CSAT sampling              | Coverage rate tracked; warn if < target     | informational |
