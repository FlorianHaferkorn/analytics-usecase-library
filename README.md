# Analytics Strategy-to-Action Framework

A pragmatic, scalable framework to translate **business strategy into action-ready analytics**.

This repository provides a complete, enterprise-grade blueprint to move from
**strategic objectives → KPIs → insights → decisions → actions** — consistently and sustainably.

## Why this framework exists

Most analytics initiatives fail not because of missing tools, but because of missing structure.

Across organizations, the same patterns repeatedly occur:

- KPIs exist, but their definitions are debated rather than trusted
- Reports explain deviations, but do not support decisions
- Business and analytics teams work on different interpretations of the same numbers
- New requirements lead to new logic instead of reuse
- AI and automation are discussed, but not structurally prepared

When these patterns persist, the consequences are predictable:

- Strategic KPIs lose credibility instead of providing orientation
- Analytics teams spend more time explaining numbers than improving decisions
- New requirements slow down instead of accelerating insights
- Trust erodes, even if the data itself is correct

At this point, analytics becomes a cost center — not a strategic capability.

This framework exists to explicitly connect:
**strategy → KPIs → use cases → semantic models → actions**  
and to make this connection durable, governed, and scalable.

The goal is not more reporting.
The goal is fewer discussions, faster decisions, and measurable impact.

Doing nothing does not keep the current state — it reinforces it.

## What makes this framework different

- **Strategy-to-Action Golden Thread**  
  Every report, KPI, and model traces back to a strategic objective.

- **Action-Ready Semantic Model**  
  KPIs are designed to trigger actions, not just describe performance.

- **Use Case–Driven Analytics**  
  Analytics is organized around business decisions, not dashboards.

- **Single Source of Truth by Design**  
  Governed KPI catalogs, measure systems, and semantic standards.

- **Automation & AI Ready**  
  Structured metadata enables automation, Copilot, and AI agents without rework.

## How to get started (recommended path)

### 1. Understand the Strategy Context (WHY)

Start here to understand what the organization wants to achieve.

- `framework/strategy_operating_model/company/company_strategy.md`
- `framework/strategy_operating_model/company/reporting_principles.md`

### 2. Understand the Operating Model (HOW)

Learn how strategy is translated into analytics and actions.

Start with:

- `framework/strategy_operating_model/operating_model/operating_model_overview.md`
- `framework/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md`

### 3. Explore the Core Use Cases (WHAT)

See how strategic questions are translated into concrete analytics use cases.

- `framework/usecases/core/`
- `framework/usecases/UseCase_Inventory.md`

Each use case contains:

- Business intent and decision context
- Required KPIs and actions
- Technical blueprint for implementation

## Stage 1 CI Gate (local / CI)

**Tool-agnostic only** (facts, KPI catalog, action codes, use case map, doc refs; no Fabric/Power BI output). Canonical command (run from repo root):

```
.\_internal\tools\run_stage1_checks.ps1
```

For Fabric/Power BI output validation (measures vs KPI, TMDL vs measure dictionary, DAX best practices), use `.\_internal\tools\run_all_checks.ps1` or the Fabric-only script: `implementations\microsoft_fabric_powerbi\tools\run_fabric_checks.ps1`.

Prerequisite (one-time, for schema validation):

```
cd _internal\tools\validation
npm ci
```

## Stage 2 Soft Review (planned)

Non-blocking, tool-agnostic review guidance for changed docs only.
Guidance only; it does not represent approval or rejection.
Spec and contracts:
- `_internal/ci/stage2_soft_review.md`
- `_internal/tools/stage2_review/stage2_review.contract.json`
- `_internal/tools/stage2_review/stage2_findings.schema.json`

## Repository Structure (high level)

```yaml
framework/           # Tool-agnostic: strategy, use cases, KPIs, semantic model, data contracts
  strategy_operating_model/
    company/         # Strategy, principles, domains
    operating_model/ # Analytics operating model (HOW)
  usecases/
    core/            # Core cross-industry use cases
    extended/        # Advanced use cases
    industry/        # Industry-specific use cases
  kpi_catalog/       # Governed KPI definitions
  action_codes/      # Action logic and thresholds
  semantic_models/   # Measure dictionaries, core blueprint
  data_contracts/    # Domain- and source-level contracts
  templates/         # Page, measure, data contract templates

implementations/    # Tool-specific implementations
  microsoft_fabric_powerbi/
    guide/           # Fabric/Power BI implementation guides
    dist/            # Generated TMDL/artifacts (default output)
    tools/           # Fabric-specific scripts (e.g. run_fabric_checks.ps1, theme_generator)

showcases/          # Example reports and adoptions (e.g. sample_pbip_report)

_internal/          # Maintainer tooling, CI, schemas
  tools/             # Validation, generation, automation
  ai/                # Schemas for AI and automation
```

## Who this is for

- **Executives**  
  Clear linkage between strategy, KPIs, and outcomes.

- **Business & Domain Leads**  
  Decision-oriented analytics instead of ad-hoc reporting.

- **Data & Analytics Teams**  
  Clear standards, reduced rework, scalable architecture.

- **Enterprise Architects**  
  Governance without bureaucracy, platform-agnostic by design.

## Platform & Implementation

This framework is **platform-agnostic by design**.  
Platform-specific implementation guides (e.g. Fabric / Power BI) live under:

- `implementations/microsoft_fabric_powerbi/guide/` (Fabric/Power BI)

