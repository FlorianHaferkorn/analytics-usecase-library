# Analytics Strategy-to-Action Framework

A pragmatic, scalable framework to translate **business strategy into action-ready analytics**.

This repository provides a complete, enterprise-grade blueprint to move from
**strategic objectives → KPIs → insights → decisions → actions** — consistently and sustainably.

## Why this framework exists

Most analytics initiatives fail not because of missing tools, but because of missing structure: KPI definitions get debated, reports explain deviations without enabling decisions, and new requirements pile up new logic instead of reusing it.

This framework explicitly connects **strategy → KPIs → use cases → semantic models → actions** in a way that is durable, governed, and scalable — so analytics becomes a strategic capability, not a cost center.

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

## Getting started

**New to the repo?** Start with [`ONBOARDING.md`](ONBOARDING.md) — single Day-1 guide covering setup, reading order, glossary, and a first task.

```bash
pip install -r requirements.txt                  # Python deps
cd tooling/validation && npm ci && cd ../..      # Schema validation deps (Node)
```

Run all commands from the **repository root**.

**Other entry points:**

- [`docs/README.md`](docs/README.md) — global navigation hub for all audiences
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — workflow, validation gates, conventions
- [`TAXONOMY.md`](TAXONOMY.md) — IDs, domain prefixes, naming
- [`GLOSSARY.md`](GLOSSARY.md) — TMDL, PBIP, IR, MCP, and other acronyms

**Implementing a use case end-to-end (Fabric example, COM-001):**

```powershell
# Generate TMDL measures from the KPI catalog
.\tooling\generation\generate_tmdl_measures.ps1 -UseCase COM-001 -UseAuroraShowcase -OverwriteExisting

# Validate
.\tooling\run_stage1_checks.ps1
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

Output lands in `products/fabric/powerbi/dist/<Domain>.SemanticModel/`. Layout, PBIP, and theme details live in `products/fabric/powerbi/docs/`.

## Validation gates

| Gate | Scope | Command |
|---|---|---|
| **Stage 1** (mandatory before merge) | Tool-agnostic — `core/`, `tooling/`, `docs/` | `.\tooling\run_stage1_checks.ps1` |
| **Fabric** | TMDL, DAX, PBIP, measures | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` |
| **OSS** | Evidence, dbt, OSS adapters | `bash products/open_source_stack/tooling/run_oss_checks.sh` |
| **Full local** | Stage 1 + Fabric | `.\tooling\run_all_checks.ps1` |
| **Health scorecard** | H1–H5 framework metrics | `python tooling/health_scorecard.py` |

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow details and [`internal/ci/stage2_soft_review.md`](internal/ci/stage2_soft_review.md) for the planned non-blocking Stage 2 review.

## Repository Structure (high level)

```yaml
core/           # Tool-agnostic SSOT: strategy, use cases, KPIs, semantic models, data contracts
  strategy_operating_model/  # Strategy (WHY) and operating model (HOW)
  usecases/                  # core/, extended/, industry/ — business decisions
  kpi_catalog/               # Governed KPI definitions (golden_20.yaml + extended_playbook.md)
  action_codes/              # Action logic and decision spines
  semantic_models/           # Measure dictionaries, core blueprint
  data_contracts/            # Domain- and source-level contracts
  templates/                 # Page, measure, data-contract templates

products/        # Platform-specific implementations
  fabric/powerbi/   # Power BI / Fabric: TMDL, PBIP, deployment
  open_source_stack/ # Evidence.dev + dbt frontend
  oss_adapters/     # Grafana / Metabase / Superset adapter stubs

studio/          # Next.js Studio UI (Interaction Layer) — visual editor over core/

showcases/       # Reference implementations (aurora_group, sample_pbip_report)

tooling/         # Shared validators, generators, registry, hooks (run_stage1_checks.ps1 etc.)
docs/            # Global entry points and architecture docs
internal/        # Archive, strategy, CI specs, audits (maintainer-only)
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

