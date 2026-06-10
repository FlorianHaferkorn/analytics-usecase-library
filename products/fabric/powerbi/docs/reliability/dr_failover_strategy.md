# DR and Failover Strategy (Fabric workloads)

This document defines a practical target approach for recovery and failover for workloads delivered via this repo into Microsoft Fabric.

Primary reference (Reliability + architecture patterns context):
- Microsoft Fabric architecture patterns: https://learn.microsoft.com/de-de/azure/well-architected/microsoft-fabric/overview#architecture-pattern

## Scope and boundaries

In Fabric, Microsoft operates most platform-resilience primitives. This repo can still define and operationalize:
- workload segmentation (workspaces/capacities),
- backup/restore posture for *definitions and deployed artifacts*,
- deployment reproducibility (Git-based PBIP + deterministic generation),
- a tested recovery workflow (“how we restore what we control”).

## Target architecture principles

1. Separate concerns using workspaces and (when needed) capacities
   - Use workspace boundaries as the primary containment mechanism.
   - Use dedicated capacities for workloads that require stronger isolation guarantees.

2. Treat Git + PBIP as the source for restore
   - Repo generation already produces PBIP artifacts under `products/fabric/powerbi/dist/`.
   - Recovery should be possible by re-deploying the same PBIP from Git rather than manual service edits.

3. Back up the things you can restore without ambiguity
   - Backup definitions: PBIP export, semantic model export, and report/page JSON.
   - Backup operational state: refresh schedules and key configuration parameters (as much as org practice allows).

## DR tiers (minimum viable vs strict)

### Tier 0 (default / best effort)
Use when workloads are non-critical or when business tolerance is high.
- Keep Git history + artifacts reproducible.
- On incident: redeploy from Git, then trigger refresh.

### Tier 1 (business critical)
Use when the workload is important for daily operations.
- Add scheduled “artifact exports” (PBIP and semantic models) to an external, access-controlled backup location.
- Run periodic “restore rehearsal” (at least quarterly): export -> wipe test env -> restore -> validate pages load and semantic model refreshes.

### Tier 2 (mission critical)
Use when outage risk must be minimized with a stronger target.
- Plan multi-region strategy for the capacities and/or the workload landing zones.
- Ensure runbooks describe which environment/capacity is the standby target.
- Add faster restore validation and enforce smaller recovery windows through rehearsals.

## Backup strategy (what to export, and why)

### Definitions to export
- Fabric items as PBIP artifacts (semantic model + report definition folders).
- Orchestrator outputs (if the workflow generates deterministic PBIP, backups can be aligned to those outputs).

### Where to store backups
- Store backups in a location separate from the Fabric service (so service outages do not eliminate backups).
- Access control: backups must follow the same least-privilege expectations as source artifacts.

Evidence in repo:
- `internal/continuity/runbook.md` includes backup-oriented commands (for example exports of semantic models as a continuity step).
- `internal/continuity/architecture_overview.md` describes regeneration and recovery sequence.

## Restore strategy (runbook outline)

1. Confirm blast radius
   - Which workspace/capacity/items are affected?
   - What is broken: deployed artifacts, refresh connectivity, or semantic model load?

2. Restore from known-good artifacts
   - Re-deploy semantic model and reports from the repo’s generated PBIP.
   - If “definitions-only” recovery is insufficient, restore from the external PBIP export backups.

3. Validate after restore
   - Validate report loads in Power BI Desktop (at least for the critical pages).
   - Validate semantic model loads and `_Measures` is present and syntactically valid (TMDL checks).

4. Refresh and verify data correctness
   - Trigger dataset refresh.
   - Spot-check KPI output for drift (use deterministic measures and known KPI references).

## Recovery rehearsal (tests)

Minimum rehearsal checks:
- Restore rehearsal validates “openability”: reports load and pages render.
- Refresh rehearsal validates “data pipeline health”: refresh completes or fails with known errors.

Suggested cadence:
- Tier 1: quarterly.
- Tier 2: monthly (or tied to meaningful changes), plus additional rehearsals after major template/generator changes.

## Practical ownership model
- Platform/infra owner: manages capacities/workspace placement and standby capacity policies.
- Analytics engineering owner (repo): ensures generated PBIP can be rebuilt and deployed from Git.
- Data owner: validates KPI meaning and expected data ranges post-restore.

---

Last reviewed: 2026-06-04
