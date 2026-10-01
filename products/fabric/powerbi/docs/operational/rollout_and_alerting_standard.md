# Rollout and Alerting Standard (Fabric deployments)

This document defines a repo-aligned operational standard for:
- how we roll changes out across dev/test/prod,
- how we observe deployment/runtime health,
- what “Definition of Done” means for alerts and response readiness.

Primary references (operational excellence themes):
- Microsoft Fabric workloads overview (operational efficiency + architecture patterns): https://learn.microsoft.com/de-de/azure/well-architected/microsoft-fabric/overview

## What we already have in the repo (baseline)

Deployment and operation concepts already exist in repo artifacts:
- Stage-based validation gates (Stage 1 + Fabric checks)
- Deployment gates (deploy_gate) and deploy orchestration (deploy.ps1)
- Structured logging and health checks for deployments

Evidence in repo:
- `products/fabric/powerbi/deployment/ENHANCEMENTS.md` (pre-flight checks, health checks, structured logging)
- `products/fabric/powerbi/orchestrator/AUTOMATION_FLOW.md` (deploy gate orchestration flow)
- `internal/continuity/architecture_overview.md` (monitor + health scorecard and registry strict gates)

## Change classification (so rollout is predictable)

When a PR changes something in these buckets, treat it as “deployment impacting” and follow this standard:
1. Semantic model / TMDL changes
   - measures, `_Measures.tmdl`, relationships, RLS/OLS definitions, Direct Lake partition configs
2. Report/page changes
   - `definition/report.json`, pages metadata, visual containers/visual.json bindings
3. Orchestrator/generator changes
   - code that changes emitted PBIP structure
4. Governance/security adjacent changes
   - workspace roles, sensitive item handling, secrets handling logic

## Rollout model (dev -> test -> prod)

1. Dev
   - deploy as early as possible (to catch generator/TMDL/PBIP issues quickly).
2. Test
   - mirror prod usage patterns as much as feasible (data volume + refresh cadence).
3. Prod
   - restrict production deploy permissions
   - deploy using the same pipeline but with production deployment rules/parameters

### Optional: canary / progressive rollout

If your org supports partial user exposure:
- deploy to prod workspace(s) first,
- then enable consumption gradually (app visibility, sharing settings, or staged audience onboarding).

This is especially useful for report changes with large template/visual contract updates.

## Alerting standard (what to watch)

We define “minimum alert categories” for any meaningful release:
1. Deployment health
   - deploy_gate success/failure
   - item import/export success/failure counts
2. Runtime refresh health
   - dataset/table refresh failures
   - unusually long refresh times (threshold-based)
3. Access and security symptom alerts
   - unexpected permission denials for consumer roles
   - “role mapping mismatch” symptoms after RLS/OLS changes
4. Data correctness symptom alerts (lightweight)
   - KPI output anomalies beyond a defined tolerance window (if you have automated checks)

## Platform alerting surfaces (Fabric, checked 2026-10-01)

The categories above say *what* to watch. This section says *where* Fabric raises the signal,
with the values a delivery starts from. Every platform statement carries its Microsoft Learn
page; all pages were read on 2026-10-01 via the Microsoft Learn MCP server. Statements Learn does
not make are marked `ANNAHME, ungeprüft` or *observation*.

**Single source.** The values below are not defined here. They are encoded in the mirrored
Meridian emitter `tooling/superversion/vendor/meridian_dataarch/provision_monitoring.py`
(constants `CAPACITY_ALERT_METRICS`, `CAPACITY_ALERT_DEFAULT_THRESHOLD`, `CAPACITY_STATES`,
`MONITORING_POLITIK_VORGABE`, `MONITORING_UNVERAENDERLICH`, `JOB_ALERT_TYPES`,
`JOB_ALERT_NOT_COVERED`), which emits `monitoring/capacity_alerts.md`,
`monitoring/workspace_monitoring_item.json` and `monitoring/job_alerts.json` per delivery.
Change a value there (in Meridian, then re-mirror), never only in this document.

### Capacity alerts (Real-Time hub → Set capacity alert)

Path: **Real-Time → Fabric events → Capacity overview events → Set alert**. The *Set capacity
alert* dialog offers templates; Activator pre-fills Monitor and Condition. Prerequisites: a
non-trial capacity and the **Capacity Admin** role.
Sources: [Set alerts on Fabric capacity overview events](https://learn.microsoft.com/fabric/real-time-hub/set-alerts-fabric-capacity-overview-events),
[Tutorial: Monitor capacity health](https://learn.microsoft.com/fabric/real-time-hub/tutorial-monitor-capacity-threshold).

| Template (Learn name) | Field | Condition | Start value | Meaning |
|---|---|---|---|---|
| Alert when a capacity metric exceeds a threshold | `backgroundRejectionThresholdPercentage` | increases to or above | 80 | background jobs are rejected under capacity pressure (pipelines fail) |
| Alert when a capacity metric exceeds a threshold | `interactiveDelayThresholdPercentage` | increases to or above | 80 | interactive operations are delayed (reports slow) |
| Alert when a capacity metric exceeds a threshold | `interactiveRejectionThresholdPercentage` | increases to or above | 80 | interactive operations are rejected (reports fail) |
| Alert when a capacity changes state | `capacityState` | changes to | `Overloaded` | state change; Learn offers *Any state change*, *Overloaded*, *Active*, *Suspended*, *Deleted* |

- **80 is Learn's example value**, not a recommendation ("Adjust this threshold based on your
  operational policy"). A different threshold goes into the monitoring policy
  (`kapazitaet_schwellen`), not only into the portal dialog.
- The template condition is a *numeric change grouped by `capacityId`*: one alert per crossing,
  no stream of alerts while the value stays high.
- Actions: e-mail, Teams message, run a Fabric item, or a custom action; *Run function* (UDF) for
  auto-mitigation. Default recipient set: the `capacity` entry of the delivery's `alerts` map,
  otherwise a `<VERIFY>` placeholder; recipients are never invented.
- Save the Activator item in the monitoring workspace, not on the capacity it watches, where the
  topology allows it. A workspace with **outbound access protection** needs the data connection
  rule for the **Real-Time Events** connector, or cross-workspace event consumption is blocked.
- No create-API is emitted: build the rule in the portal (the emitter's `create_api` field
  carries the reason).
- **Deviation from the mirror:** Learn lists a third template, *Alert when capacity usage %
  exceeds a threshold* (tracks `interactiveDelayThresholdPercentage`, default 80). The mirrored
  emitter does not emit it; the `interactiveDelayThresholdPercentage` metric rule above covers the
  same field. Raised for Meridian, not changed here.

**Capacity operation events (preview)** — one event per operation
(`Microsoft.Fabric.CapacityOperationEvents.Operation`), high volume. Off by default in the policy
(`operation_events: false`). Only switch on with a pre-filter (`itemKind`, `utilizationType`,
`status`) and grouping (`workspaceId`, `itemId` or `operationName`) on a measure such as
`capacityUnitMs`, `durationMs` or `throttlingDelayMs`; per-operation thresholds are customer
input and have no default. Source:
[Set alerts on Fabric capacity operation events](https://learn.microsoft.com/fabric/real-time-hub/set-alerts-fabric-capacity-operation-events).

The Capacity Metrics app has **no** alerting; the built-in *Throttling notifications* capacity
setting (OneLake catalog → Govern → Capacities → the capacity → More options → Settings) is the
low-effort complement, not a replacement for the rules above. Sources:
[Manage your capacities in the OneLake catalog](https://learn.microsoft.com/fabric/governance/onelake-catalog-capacities)
(settings table) and the mirrored `_metrics_app_setup_md` in `provision_monitoring.py`.

### Workspace monitoring (Monitoring item)

Path: **Workspace settings → Monitoring → Enable**. This provisions a Monitoring item (Eventhouse
with a read-only KQL database, Eventstream, Activator; optionally an Operations Agent). Data
collection starts only after **Turn on data collection**; there is no backfill.
Prerequisites: workspace on a Fabric or Premium capacity, tenant setting *Workspace admins can
turn on monitoring for their workspaces*, tenant setting *Users can create Fabric items* for the
person enabling it (otherwise *Monitoring* is greyed out with no error), workspace Admin role.
Source: [Configure workspace monitoring](https://learn.microsoft.com/fabric/fundamentals/enable-workspace-monitoring).

**Topology (default: central).** Learn recommends as few Eventhouses as possible and a workspace
on its **own capacity** for the central monitoring Eventhouse: it shields monitoring from
throttling of the workload and the workload from monitoring. Source workspaces choose *Send data
to Eventhouse in another Monitoring Item*.

| Rule | Value | Source |
|---|---|---|
| Destination workspace and source workspaces | same Azure region | enable-workspace-monitoring, *Limitations* |
| KQL databases in the destination | one per source workspace, each counts toward the 1,000-item workspace limit | same |
| Monitoring items per workspace | one at a time | same |
| Deviation (`topologie: je-workspace`) | allowed, but recorded as a deliberate deviation from the Learn recommendation | emitter `_monitoring_item_spec` |

**Checkbox policy.** Learn: "By default, all additional monitoring capabilities are enabled,
including diagnostic data, telemetry data, and AI powered investigations. These capabilities
aren't required for Activator-based alerts" (*Set up job alerts in the Monitor hub*). The policy
therefore decides each box explicitly; irreversible boxes get no silent default.

| Checkbox | Microsoft default | Policy default (`MONITORING_POLITIK_VORGABE`) | Reversible |
|---|---|---|---|
| Diagnostic data | on | on (`diagnosedaten: true`); ingestion cost on the capacity | yes |
| AI powered investigations (adds the Operations Agent) | on | **open** (`ki_untersuchungen: null`) until GDPR/Copilot clearance; needs the Operations Agent, Copilot and Azure OpenAI tenant settings, no trial | **no** |
| Custom endpoint (Event Hubs/Kafka/AMQP) | off | **open** (`custom_endpoint: null`) | **no** (preview: creation time only) |

**Irreversible decisions** (decide before *Enable*; field `MONITORING_UNVERAENDERLICH`):

1. Destination (this vs. another Monitoring item) cannot be changed after configuration.
2. Central destination only within the same Azure region.
3. Each source workspace adds a KQL database to the destination's 1,000-item limit.
4. Custom endpoint can only be enabled at creation time (preview).
5. "If you enable the Operations Agent, you can't disable it later."

Retention is **not** fixed: 30 days by default, changeable in the monitoring KQL database under
**Manage → Data policies**; the caching period must be ≤ the retention period (policy fields
`aufbewahrung_tage`, `cache_tage`). Source: enable-workspace-monitoring, *Manage retention and
caching*.

### Job alerts (Monitor hub, preview)

Two alert types, managed together under **Monitor → Manage → Alerts**. Source:
[Set up job alerts in the Monitor hub](https://learn.microsoft.com/fabric/admin/monitoring-hub-alerts).

| Alert type | Path | Cost | Scope |
|---|---|---|---|
| Schedule failure emails | Job runs → … → *Create and manage alerts* → *Schedule failure emails (free)* | free | scheduled runs only, not manual runs; semantic models not yet supported; Contributor or Write on the item |
| Activator-based alert rules | Job runs → … → *Create and manage alerts* → *Alerts (paid)* | Activator capacity usage | events such as Started, Succeeded, Failed; e-mail, Teams, automated actions; needs workspace monitoring (the Monitoring item stores the alerts, no Eventhouse or extra capability required) and workspace Owner or Contributor |

- Activator job alerts cover nine job types: pipeline, Spark job, notebook, user data function,
  warehouse, lakehouse, mirrored database, SQL database, KQL database (`JOB_ALERT_TYPES`).
- **Not covered** by the job alerts: semantic model, Dataflow Gen2, Copy job
  (`JOB_ALERT_NOT_COVERED`). For these the KQL queryset rule over `ItemJobEventLogs`
  (`monitoring/workspace_job_failures.kql`) stays the only alert. This maps to category 2
  (*Runtime refresh health*) above: semantic-model refresh failures need the KQL rule.
- Default rule per job type: event *Failed* → Teams message to the `jobs` recipients. The check
  mode *On every value* comes from a FabCon photo (2026-09-29): `ANNAHME, ungeprüft`.
- **Job runs** page (preview): last-run status, duration and success rate per item; for a failed
  pipeline run, **Investigate** starts a read-only Operations Agent investigation. Source:
  [Monitor job runs in the Monitor hub](https://learn.microsoft.com/fabric/admin/monitoring-hub-jobs).
  A *Retry* action on that page is a FabCon observation only: `ANNAHME, ungeprüft`.
- Create-API for the Monitoring item: not documented (Learn search 2026-10-01): `UNKLAR`.

### Capacity health views and operating KPIs

Two views replace "open the Metrics app and look":

- **Capacity Metrics app → Health page** (last 24 h / last 1 h): cards *Avg. utilization %*,
  *# Throttled capacities*, *# Interactive rejected*, *# Background rejected*; per capacity a
  *Health* state (*Healthy*, *At Risk of Throttling*, *At Risk of Overage Billing*, *Overage
  Billing Active*, *Throttling*, *(At Risk of) Interactive Rejection*, *(At Risk of) Background
  Rejection*, *Suspended*) and the columns *Cumulative debt*, *Throttling (s)*, *P95 interactive
  delay / interactive rejection / background rejection*, *Blocked workspaces* (workspace-level
  surge protection). Source:
  [Understand the metrics app Health page](https://learn.microsoft.com/fabric/enterprise/metrics-app-health-page).
- **Monitor hub → Capacities** (preview): health tiles *Healthy / At risk / Degraded / Paused*;
  per capacity the cards *Utilization*, *Current throttling*, *Current activity*, *Carry forward
  CUs*, *Surge protection*; actions Pause, Resize, Reassign workspaces, Configure surge
  protection, Set capacity overage limit. Fabric administrator or capacity administrator.
  Source: [Manage capacities in the Monitor hub](https://learn.microsoft.com/fabric/admin/monitoring-hub-capacity).
  The Monitor hub also has the pages *Job runs*, *Applications*, *Agents* and *Alerts*
  ([What is the Monitor hub?](https://learn.microsoft.com/fabric/admin/monitoring-hub)).

Workspace surge classes (I-21 W1.11): the setup script declares one class per environment in
`SURGE_CLASS_BY_ENVIRONMENT` (`deployment/scripts/fabric_setup.py`): **prd = mission_critical**
(workspace state *Mission critical*: exempt from surge protection and never auto-blocked, but
capacity-level throttling still applies), **dev and tst = capped** (state *Available*: blocked
once the workspace's rolling 24-hour usage exceeds the capacity's rejection threshold). The
threshold is one percentage per capacity that applies to every workspace not marked mission
critical; it is `generic.surge_protection.workspace_cu_limit_pct` in `infrastructure.json`, ships
empty and is set by the capacity administrator, never guessed. Usage is checked every five
minutes, so the limit is soft. Learn documents workspace surge protection
(preview) as portal steps only, so the script prints them as a manual step
([Surge protection](https://learn.microsoft.com/fabric/enterprise/surge-protection), read
2026-10-01). Alert on it via the KPI *Workspaces blocked by workspace surge protection per 24 h*
below: a blocked prd workspace means the class was not applied.

Operating KPIs and where to read them (Meridian `KAPAZITAETS_KPIS` in
`core/dataarch_engine/blueprint/betriebskanon.py`; **not mirrored** into this repo, so the list
is restated here with its Learn source):

| KPI | Where | Status |
|---|---|---|
| Throttling seconds per 24 h | Metrics app → Health → *Throttling (s)* | Learn (metrics-app-health-page) |
| P95 interactive delay / interactive rejection / background rejection | Metrics app → Health → *P95 …* | Learn (same) |
| Average utilization % | Metrics app → Health → *Avg. utilization %* | Learn (same) |
| Billed overage CU hours per day | Metrics app → Compute → Overages → *Overage (Billed)*; Azure Cost Management meter *Capacity Overage Capacity Usage CU* | Learn ([metrics-app-compute-page](https://learn.microsoft.com/fabric/enterprise/metrics-app-compute-page), [capacity-overage-overview](https://learn.microsoft.com/fabric/enterprise/capacity-overage-overview)) |
| Workspaces blocked by workspace surge protection per 24 h | Metrics app → Health → *Blocked workspaces* | Learn (metrics-app-health-page) |
| Carry-forward CUs | Monitor hub → Capacities → card *Carry forward CUs* | Learn (monitoring-hub-capacity) |
| **Time in throttling / surge protection / overage (%)** | Metrics app "Preview" → Compute → time-share tiles | *observation* (FabCon demo 2026-09-29), not described on Learn (search 2026-10-01): `ANNAHME, ungeprüft`. Measure today via *Throttling (s)*, *Blocked workspaces* and Health state *Overage Billing Active* |
| Heatmap day × hour | Metrics app "Preview" → Compute | *observation*, `ANNAHME, ungeprüft`; today: Compute → Throttling charts over the 14-day window |

## Response readiness (“who does what”)

For each alert category, define:
- owner role (who responds),
- first action (what to verify first),
- rollback option (what to revert/redeploy quickly),
- escalation path (when to page an infra/security owner).

Recommended rollback options:
- revert the PR in Git and redeploy
- or redeploy the last known-good PBIP artifacts from backups (if available)

## Definition of Done (release checklist)

Before releasing a change to prod:
1. Validation gates pass in CI
   - Stage 1 and relevant Fabric checks
2. Deployment automation is “observable”
   - structured logs are emitted
   - pre-flight and health checks are executed (or documented as not applicable)
   - capacity alert rules exist for the target capacity (three metric rules + state rule, see
     *Capacity alerts*), and job alerts or the KQL fallback cover every job type the release runs
   - the Monitoring item's irreversible options (destination, Operations Agent, custom endpoint)
     were decided before *Enable*, not left at the Microsoft default
3. Alert ownership exists
   - at least one owner assigned per alert category above
4. A rollback path exists
   - either Git revert redeploy or artifact backup restore steps are documented

---

Last reviewed: 2026-10-01
