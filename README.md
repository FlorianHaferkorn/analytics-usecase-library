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

**Documentation hub (single navigation entry):** [`core/strategy_operating_model/README.md`](core/strategy_operating_model/README.md) — Golden Thread order, layer map, and links to all framework docs.

**Prerequisites:** PowerShell (or pwsh); Node.js for schema validation. One-time from repo root: `cd tooling\validation` then `npm ci`. Run all commands from the **repository root**.

### 1. Understand the Strategy Context (WHY)

Start here to understand what the organization wants to achieve.

- `core/strategy_operating_model/company/company_strategy.md`
- `core/strategy_operating_model/company/reporting_principles.md`

### 2. Understand the Operating Model (HOW)

Learn how strategy is translated into analytics and actions.

Start with:

- `core/strategy_operating_model/operating_model/operating_model_overview.md`
- `core/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md`

### 3. Explore the Core Use Cases (WHAT)

See how strategic questions are translated into concrete analytics use cases.

- `core/usecases/core/`
- `core/usecases/UseCase_Inventory.md`

Each use case contains:

- Business intent and decision context
- Required KPIs and actions
- Technical blueprint for implementation

### 4. Implement a use case (optional)

To implement one use case end-to-end (e.g. COM-001):

1. Pick a use case (e.g. COM-001) and open its artifacts: `core/usecases/core/<ID>_<Name>/` (Business_Factsheet.md, UseCase_Bracket.yaml).
2. Generate TMDL measures from the KPI catalog (from repo root):

   ```
   .\tooling\generation\generate_tmdl_measures.ps1 -UseCase COM-001 -UseAuroraShowcase -OverwriteExisting
   ```

   Primary output: `showcases/aurora_group/semantic_models/.../tables/_Measures.tmdl` (single measures table; measures grouped by display folder). Omit `-UseAuroraShowcase` to write to `products/fabric/powerbi/dist` instead.

3. Run **Stage 1** to ensure framework consistency: `.\tooling\run_stage1_checks.ps1`.
4. If you have Fabric/Power BI output, run **Fabric checks**: `products\fabric/powerbi\tooling\run_fabric_checks.ps1`.
5. **Apply report theme (recommended):** `py products/fabric/powerbi/tooling/apply_report_theme.py path/to/Report --theme-name 'Generic__Monochromatic__Light__#118DFF'` (or your showcase default). When generating scaffolds, use `--theme` so the theme is applied in the same step.

For Fabric/Power BI layout, PBIP, and best practices, see `products/fabric/powerbi/docs/`.

**First 2 hours (optional checklist):** Clone repo → run Prerequisites (npm ci in tooling/validation) → read strategy + golden thread (steps 1–2) → run Stage 1 → pick one use case and generate measures (step 2 above).

## Stage 1 CI Gate (local / CI)

**Tool-agnostic only** (facts, KPI catalog, action codes, use case map, doc refs; no Fabric/Power BI output). Canonical command (run from repo root):

```
.\tooling\run_stage1_checks.ps1
```

**When to use which:**

- **`run_stage1_checks.ps1`** — Use for **CI and before merge**. Fast, tool-agnostic gate (docs, refs, structure, KPI ↔ use case consistency). This is the mandated check for merge.
- **`run_all_checks.ps1`** — Use for **full local validation** when you have Fabric/Power BI output: runs Stage 1 plus Fabric checks (measures vs KPI, TMDL vs measure dictionary, DAX best practices, TMDL syntax). Use before releasing or when changing measures/TMDL.
- **`products\fabric/powerbi\tooling\run_fabric_checks.ps1`** — Fabric-only checks (no Stage 1); use when you only need to validate generated TMDL/measures.

## Stage 2 Soft Review (planned)

Non-blocking, tool-agnostic review guidance for changed docs only.
Guidance only; it does not represent approval or rejection.
Spec and contracts:
- `internal/ci/stage2_soft_review.md`
- `tooling/stage2_review/stage2_review.contract.json`
- `tooling/stage2_review/stage2_findings.schema.json`

## Repository Structure (high level)

```yaml
core/           # Tool-agnostic: strategy, use cases, KPIs, semantic model, data contracts
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

products/           # Tool-specific implementations
  fabric/powerbi/
    docs/            # Fabric/Power BI implementation guides
    dist/            # Generated TMDL/artifacts (default output)
    tooling/         # Fabric-specific scripts (e.g. run_fabric_checks.ps1, page scaffold generator)
    orchestrator/    # Semantic model orchestration (table ops, measures, relationships)
    deployment/      # CI/CD pipelines and deployment scripts
  open_source_stack/ # Evidence.dev frontend (planned)
  proposal_costing/  # Proposal cost engine

showcases/          # Example reports and adoptions (e.g. aurora_group, sample_pbip_report)

tooling/            # Validation, generation, maintenance, ontology, schemas (e.g. run_stage1_checks.ps1, registry_builder.py)
internal/           # Archive, strategy, vision, CI (maintainer-only)
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

- `products/fabric/powerbi/docs/` (Fabric/Power BI)

