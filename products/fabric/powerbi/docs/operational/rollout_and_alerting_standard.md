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
3. Alert ownership exists
   - at least one owner assigned per alert category above
4. A rollback path exists
   - either Git revert redeploy or artifact backup restore steps are documented

---

Last reviewed: 2026-06-04
