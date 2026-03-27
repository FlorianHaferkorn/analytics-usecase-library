# AI-first Operations (Autopilot with Human Approval)

## Purpose

Define how the framework is operated in an **AI-first** mode:

- AI performs the mechanical work (generation, validation, packaging, deployment steps).
- Humans provide **final review and approval** for semantic changes and production actions.

This document defines **binding guardrails**. It does not introduce new business meaning.

## Core policy (non-negotiable)

1. **PR-first**: AI must propose changes via pull requests (or equivalent change sets).
2. **Gate-driven**: no merge, no deploy, no publish unless all mandatory gates are green.
3. **Bounded self-healing**: AI may auto-fix only mechanical issues within defined scopes.
4. **Semantics require humans**: changes to KPI meaning, action logic, governance roles, or contract meaning require explicit human approval.
5. **Auditability**: every AI action must be logged and reproducible.

## Scope classification (what AI may do autonomously)

### A) Mechanical changes (AI may auto-fix)

- formatting and encoding fixes (BOM, mojibake)
- deterministic scaffold generation (measures/report scaffolds) from governed sources
- adding missing non-semantic metadata (format strings, display folders) if derived from catalog rules
- fixing broken references when the fix is an obvious typo and validated by gates

### B) Semantic changes (human approval required)

- KPI definitions / interpretation / target meaning in the KPI catalog
- Action Code trigger logic, thresholds, escalation semantics
- Governance role assignments and ownership semantics
- Changes to canonical schemas (Stage 1 / SSOT / bracket/action schemas)
- Changes that affect contract meaning (grains, required facts/dims, business keys)

## Required gates (minimum)

- **Stage 1**: `tooling/run_stage1_checks.ps1`
- **Registry strict**: `tooling/ontology/registry_builder.py --strict` (included via Stage 1 registry check)
- **Tool validation**: adapter-specific validation (e.g. Fabric checks via `products/fabric/powerbi/tooling/run_fabric_checks.ps1`)
- **Deploy gate** (when deploying): zero-tolerance gate for contracts + registry (e.g. `products/fabric/powerbi/orchestrator/deploy_gate.ps1`)

## Operating workflow (AI-first)

1. **Change intent** captured (issue / request) with scope classification (mechanical vs semantic).
2. AI creates a **branch + PR** with:
   - the minimal diffs
   - gate outputs as artifacts (Stage 1 results, registry outputs, tool validate report)
3. Mandatory gates run automatically; failures create actionable findings.
4. AI may attempt bounded self-healing for mechanical failures (retry loop).
5. Human reviewer approves:
   - semantic changes
   - any production deploy
6. Deploy only via gated pipeline; emit audit events.

## Key outcome

AI-first operations are safe only if the framework remains:

- explicitly structured (SSOT),
- validated (gates),
- and versioned (compatibility).

Reference: `ai_readiness.md` and the Core Constitution.

