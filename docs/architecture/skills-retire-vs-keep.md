# Skill docs — retire-vs-keep against `skills-for-fabric` (ADR-0002)

> Decision artifact for [ADR-0002](adr/0002-official-first-agent-integration-and-guided-workflow.md)
> open item *"which existing ALUCA skill docs are retired in favor of upstream vs.
> kept as overlay"*. Compiled 2026-06-16.

## Principle (from ADR-0002)

**Mechanics are borrowed, governance is ours.** A skill is **KEEP** when it
encodes ALUCA governance the vendor does not provide (KPI catalog, brackets,
Golden Thread, OSS stack, Stage-1). It is **THIN** when it teaches PBIR/TMDL
*authoring mechanics* that `skills-for-fabric` now owns — those shrink to a thin
overlay that calls the vendor skill and keeps only the ALUCA gate. Nothing is a
hard **RETIRE** yet, because every current skill carries some governance value;
RETIRE applies to the pure-mechanics *references* (see bottom).

## Classification — `docs/agent/skills/` (14)

| Skill | Verdict | Rationale |
|---|---|---|
| `add-usecase-scaffold` | **KEEP** | UseCase scaffold (Factsheet + Bracket) — ALUCA-only |
| `add-kpi-reference-safely` | **KEEP** | KPI-catalog governance — no upstream equivalent |
| `add-action-code-and-wire-up` | **KEEP** | Action-code wiring — ALUCA-only |
| `edit-factsheet-safely` | **KEEP** | Factsheet/Lean 2.0 governance — ALUCA-only |
| `edit-usecase-bracket-safely` | **KEEP** | Bracket SSOT + orchestration — ALUCA-only |
| `assess-change-impact` | **KEEP** | Blast-radius across governed refs — ALUCA-only |
| `generate-oss-dashboard` | **KEEP** | Evidence.dev / OSS — no MS upstream |
| `oss-stack-validation` | **KEEP** | OSS-stack artifacts — no MS upstream |
| `fix-oss-dashboard-errors` | **KEEP** | OSS errors — no MS upstream |
| `fix-stage1-failure` | **KEEP** | ALUCA Stage-1 CI — ALUCA-only |
| `stage1-pre-commit` | **KEEP** | ALUCA Stage-1 gate — ALUCA-only |
| `fabric-powerbi-validation` | **THIN** | PBIR/TMDL validation overlaps MS PBIR `validate` + `power-bi-report-authoring`; keep only catalog↔TMDL drift + governance gate, defer raw validation to upstream |
| `fix-pbi-report-errors` | **THIN** | Report-error fixing overlaps upstream report-authoring; keep ALUCA binding/governance specifics |
| `generate-and-validate-pbi-report` | **THIN** | Generation overlaps `power-bi-report-authoring` + `-planner`; keep the ALUCA orchestration (bracket → IR → gates), defer raw PBIR authoring to upstream |

**Tally:** 11 KEEP, 3 THIN, 0 full RETIRE.

## References (pure mechanics) — RETIRE candidates

The PBIR/TMDL **reference docs** under
`products/fabric/powerbi/docs/references/` are the data-goblin "adopt" list
(`pbir-structure`, `rename-cascade`, `visual-container-formatting`, …). These are
pure mechanics now maintained first-party by `skills-for-fabric` → **RETIRE in
favor of upstream** once the Stage-2/3 vendor skills are wired (GADW). Tracked as
a separate batch (they are not skill docs); do not delete before the vendor skill
is actually adopted in the workflow.

## Sequencing

THIN/RETIRE only takes effect **after** the `skills-for-fabric` skills are
actually wired into GADW Stages 2–3 (the remaining ADR-0002 open item: the
generator target). Until then, the THIN skills stay full — they are the Tier-0
fallback for air-gapped/no-Node environments.
