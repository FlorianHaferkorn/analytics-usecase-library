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

---

## Sources & Grounding

The AI-first operating model in this document — AI performs mechanical work under gates, while
humans approve semantic changes and production actions — aligns with established MLOps/LLMOps
automation practices (CI/CD, continuous training, pipeline-driven deployment) and with the
human-in-the-loop pattern for agentic workflows. Grounded in:

- **MLOps automation** (CI/CD and continuous training/delivery via ML pipelines; maturity levels
  that motivate the gate-driven, PR-first, reproducible workflow here) — Google Cloud,
  *MLOps: Continuous delivery and automation pipelines in machine learning*:
  <https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning>
- **MLOps on Azure** (DevOps-based model lifecycle: reproducible pipelines, deployment, monitoring,
  and end-to-end lineage that underpin the required gates and audit events) — Microsoft Learn,
  *MLOps: Model management, deployment, and monitoring with Azure Machine Learning*:
  <https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-management-and-deployment> ·
  *MLOps Maturity Model* (Azure Architecture Center):
  <https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/mlops-maturity-model>
- **Human-in-the-loop & agentic workflows** (predefined checkpoints where an agent pauses for human
  review/approval before continuing — the basis for "semantics require humans" and "autopilot with
  human approval") — Google Cloud, *Choose a design pattern for your agentic AI system*
  (human-in-the-loop pattern):
  <https://cloud.google.com/architecture/choose-design-pattern-agentic-ai-system> ·
  *Multi-agent AI system on Google Cloud*:
  <https://cloud.google.com/architecture/multiagent-ai-system>
- **AI risk governance** (auditability, accountability, and human oversight as binding controls
  that justify the non-negotiable gates and logged, reproducible AI actions) — NIST AI Risk
  Management Framework (AI RMF 1.0): <https://www.nist.gov/itl/ai-risk-management-framework>

> This document defines binding guardrails for *operating* the framework with AI; it does not
> introduce new business meaning. The cited MLOps/agentic sources motivate *how* AI automates
> mechanical work safely under gates, not the framework's specific KPI/Action-Code/contract
> semantics, which remain human-owned (see "Core policy").

