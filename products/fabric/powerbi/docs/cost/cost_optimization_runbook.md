# Cost Optimization Runbook (Fabric)

This runbook provides a practical cost-optimization standard aligned with Microsoft Fabric “cost optimization” guidance.

Primary reference:
- Microsoft Fabric architecture patterns (Cost optimization pillar is part of the overview): https://learn.microsoft.com/de-de/azure/well-architected/microsoft-fabric/overview

## Goals

1. Avoid paying for unused or inefficient compute
2. Prevent shared capacity contention from degrading performance and causing rework
3. Ensure dev/test/prod alignment is intentional (not accidental overprovisioning)
4. Use capacity/workspace segmentation as a cost-governance tool

## Repo-aligned baseline (what you already do well)

This repo already documents capacity/workspace strategies:
- recommended deployment patterns (monolithic vs multiple workspaces vs separate capacities)
- using separate capacities for load testing
- using Git-driven deployment and environment separation (DTAP)

Evidence:
- `products/fabric/powerbi/docs/fabric_architecture_best_practices.md`

## Operational steps

### 1) Inventory workloads and map to isolation needs

For each domain/use case family (COM/FIN/OPS/SCM/XD), identify:
- criticality (who depends on it),
- expected workload intensity (refresh frequency, report interactivity),
- governance sensitivity (who must be isolated from whom).

Then decide:
- shared capacity vs separate capacities,
- which workspaces must be split by environment and/or business unit.

### 2) Capacity right-sizing by environment

Minimum policy:
- dev and test may be smaller than prod when feasible,
- load testing must not impact prod (use dedicated load capacity if applicable).

Quality policy:
- simulate production scale in test where the org can afford it (to avoid “works in dev, fails in prod”).

Evidence in repo:
- `fabric_architecture_best_practices.md` includes “simulate production” guidance for test stage.

### 3) Scaling and pausing policy (org-dependent)

If your org supports pausing or scaling policies for non-prod:
- define which workspaces/items are eligible,
- define schedule windows (business hours vs off-hours),
- define the owner who can change the schedule.

If pausing is not supported in your environment, document alternative cost controls (for example stricter dev usage rules and optimized refresh cadence).

### 4) Refresh and retention cost control

Cost drivers often come from refresh cadence and retained data size.

Minimum actions:
- prefer incremental/partitioned refresh strategies where possible,
- ensure refresh scheduling aligns to business needs (avoid “always on” if not required),
- define data retention windows for gold-layer artifacts (as your org policy requires).

Evidence in repo:
- Lakehouse/gold architecture is partition-focused; semantic models use direct consumption patterns.
- Retention and backup policies are defined in compliance docs (see `compliance/retention_policy.md`).

### 5) Utilization monitoring and thresholds

Define and document:
- which utilization signals you track (capacity utilization, refresh durations, failure rates),
- warning thresholds (when you start investigating),
- critical thresholds (when you stop/reduce load or split capacities).

Read the signals from the two capacity views, not from ad-hoc exports (all Learn pages below read
2026-10-01 via the Microsoft Learn MCP server):

- **Capacity Metrics app → Health page** (last 24 h / last 1 h) for the cost review: *Avg.
  utilization %*, *Throttling (s)*, *Cumulative debt* (carry-forward), the P95 delay/rejection
  columns, *Blocked workspaces*, and the per-capacity *Health* state including *At Risk of
  Overage Billing* and *Overage Billing Active*. Source:
  [Understand the metrics app Health page](https://learn.microsoft.com/fabric/enterprise/metrics-app-health-page).
- **Capacity Metrics app → Compute → Overages**: *Overage (Carryforward)* (add, burndown,
  cumulative) and *Overage (Billed)* (rolling 24-hour billed overage CU hours against the
  overage billing limit). Source:
  [Compute page](https://learn.microsoft.com/fabric/enterprise/metrics-app-compute-page).
- **Monitor hub → Capacities** (preview) for the current state and the action: *Utilization*,
  *Current throttling*, *Carry forward CUs*, *Surge protection*; actions Pause, Resize, Set
  capacity overage limit. Source:
  [Manage capacities in the Monitor hub](https://learn.microsoft.com/fabric/admin/monitoring-hub-capacity).

Cost KPIs (review monthly, and at the quarterly sizing review):

| KPI | Where | Cost meaning | Status |
|---|---|---|---|
| Average utilization % | Health → *Avg. utilization %* | sizing: persistently near the top → scale or split; persistently low → consolidate or downsize | Learn |
| Throttling seconds per 24 h | Health → *Throttling (s)* | rework and lost user time; a cost without a meter | Learn |
| Billed overage CU hours per day | Compute → Overages → *Overage (Billed)*; Azure Cost Management meter *Capacity Overage Capacity Usage CU* | direct extra spend at 3 × pay-as-you-go | Learn |
| Carry-forward CUs | Monitor hub → Capacities → *Carry forward CUs* | debt that throttles or is billed as overage | Learn |
| Workspaces blocked by surge protection per 24 h | Health → *Blocked workspaces* | protected capacity at the price of blocked jobs | Learn |
| **Time in throttling / surge protection / overage (%)** | Metrics app "Preview" → Compute → time-share tiles | the share of the period the capacity was not running at its paid size | *observation* (FabCon demo 2026-09-29), not on Learn (search 2026-10-01): `ANNAHME, ungeprüft`; measure today via *Throttling (s)*, *Blocked workspaces*, Health state *Overage Billing Active* |

Alert thresholds for the same signals live in the rollout standard
(`products/fabric/powerbi/docs/operational/rollout_and_alerting_standard.md`, *Capacity alerts*),
not here.

### 6) Capacity overage as a cost control

Facts (Learn, read 2026-10-01:
[Capacity overage](https://learn.microsoft.com/fabric/enterprise/capacity-overage-overview),
[Enable capacity overage](https://learn.microsoft.com/fabric/enterprise/enable-capacity-overage)):

- F SKUs only; **on by default** for a new capacity, default rolling 24-hour threshold **25 %**.
- Billed at **3 × the pay-as-you-go rate** through a separate meter; no standing charge.
- Keep the threshold **below one third of the SKU's daily CU hours** (CU × 24); there the cost
  roughly equals the next larger SKU.
- The threshold is **not a hard cap**: evaluated every 5 minutes, running operations continue.
- Quota: the threshold needs 1/24 of its value in Fabric CU quota (48 CU h → 2 CU).
- Switching overage on during heavy throttling bills the whole cumulative carry-forward at that
  moment.
- Path: OneLake catalog → Govern → Capacities → the capacity → Settings → *Capacity overage*;
  fallback Settings (gear) → Admin portal → Capacity settings.

The arithmetic (daily CU hours, one-third recommendation, quota, maximum cost per day) is encoded
in the mirrored `tooling/superversion/vendor/meridian_dataarch/capacity_recommend.py`
(`overage_kalkulation`, `OVERAGE_PREISFAKTOR`, `OVERAGE_EMPFEHLUNG_NENNER`,
`OVERAGE_VOREINSTELLUNG_PCT`); its cost line is derived, not measured, and stays empty without a
regional price. Whether the 25 % default refers to the SKU's daily CU hours is
`ANNAHME, ungeprüft` (Learn says only "extra daily capacity consumption").

## Definition of Done (cost standard)

For a new environment or a significant cost change:
1. Workspaces and capacities follow the repo’s documented pattern (Pattern 2/3 recommended by default).
2. dev/test/prod sizing is explicitly justified (not accidental defaults).
3. Non-prod cost controls are documented (pause/refresh schedule approach).
4. Retention/refresh policies have an owner.
5. Utilization monitoring plan exists with thresholds and response actions, reading the KPIs of step 5.
6. Capacity overage is decided per capacity (on with a threshold below one third of the daily CU hours, or off), not left at the default.

---

Last reviewed: 2026-10-01
