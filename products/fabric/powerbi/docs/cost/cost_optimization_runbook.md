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

## Definition of Done (cost standard)

For a new environment or a significant cost change:
1. Workspaces and capacities follow the repo’s documented pattern (Pattern 2/3 recommended by default).
2. dev/test/prod sizing is explicitly justified (not accidental defaults).
3. Non-prod cost controls are documented (pause/refresh schedule approach).
4. Retention/refresh policies have an owner.
5. Utilization monitoring plan exists with thresholds and response actions.

---

Last reviewed: 2026-06-04
