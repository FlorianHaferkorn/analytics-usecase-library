# Glossary

Acronyms and terms that appear across the repo. Look here first when something is unfamiliar.

## Framework concepts

| Term | Meaning |
|---|---|
| **SSOT** | Single Source of Truth. KPI definitions live only in `core/kpi_catalog/`; action logic only in `core/action_codes/`. Use cases reference them — they never redefine them. |
| **Golden Thread** | The end-to-end traceability from a strategic objective down to a triggered action: Strategy → KPI → Use Case → Semantic Model → Report → Action. |
| **Use Case** | A business decision context (e.g. "Sales Performance"). Each use case folder under `core/usecases/core/` contains a Business Factsheet (prose) and a `UseCase_Bracket.yaml` (machine-readable). |
| **Business Factsheet** | Prose-only Markdown describing intent, decisions, KPIs, and actions for a use case. No machine-readable config — that lives in the bracket. |
| **UseCase Bracket** | `UseCase_Bracket.yaml`. Machine-readable orchestration, governance, value-driver model, and UX layout rules for a use case. |
| **KPI Catalog** | `core/kpi_catalog/`. Two-tier catalog: `golden_20.yaml` (strategic spine) + `extended_playbook.md` (supporting/narrow KPIs). |
| **Action Code** | A coded recommendation (e.g. `C-M1.1` = Commercial, Margin, action 1.1) with trigger, impact, KPIs, and execution steps. Stored in `core/action_codes/<Domain>/`. |
| **Decision Spine** | A sequence of action codes wired into a use case via `core/action_codes/decision_spines/`. |
| **Data Contract** | Domain- or source-level YAML in `core/data_contracts/` declaring schema, ownership, and freshness. |
| **Health Scorecard** | Automated H1–H5 metrics measuring framework health (Golden Thread coverage, model stability, data contract coverage, action completeness, factsheet quality). Run `python tooling/health_scorecard.py`. |

## Tooling & validation

| Term | Meaning |
|---|---|
| **Stage 1 Gate** | Mandatory tool-agnostic CI gate. Validates docs, refs, structure, KPI consistency. Run `pwsh ./tooling/run_stage1_checks.ps1`. |
| **Fabric Gate** | Validates TMDL, DAX, PBIP, measures. Run `pwsh ./products/fabric/powerbi/tooling/run_fabric_checks.ps1`. |
| **OSS Gate** | Validates Evidence.dev / dbt / OSS adapters. Run `bash products/open_source_stack/tooling/run_oss_checks.sh`. |
| **Stage 2 Soft Review** | Planned non-blocking guidance pass. Currently advisory only. |
| **Registry Builder** | `tooling/ontology/registry_builder.py`. Builds the master registry graph from all governed artifacts. |
| **IR** | Intermediate Representation. Adapter-neutral dashboard spec (`DashboardSpec`) used by all platform adapters. Generated under `tooling/ir/out/`. |

## Platform terms (Fabric / Power BI)

| Term | Meaning |
|---|---|
| **PBIP** | Power BI Project format — folder-based, source-control-friendly alternative to `.pbix` binary files. |
| **PBIR** | Power BI Report format — JSON-based report definitions inside a PBIP project (visuals, pages, themes). |
| **TMDL** | Tabular Model Definition Language. Text representation of a Power BI semantic model (tables, measures, relationships). Lives under `*.SemanticModel/definition/`. |
| **TOM** | Tabular Object Model. The .NET object model for editing TMDL programmatically (PowerShell / C#). |
| **DAX** | Data Analysis Expressions. The formula language used in measures and calculated columns. |
| **Direct Lake** | Fabric mode that reads Parquet directly from OneLake without import or DirectQuery. |
| **Fabric CLI (`fab`)** | Command-line tool for Fabric workspaces, models, reports, notebooks. Used for all Fabric data-plane operations in this repo. |
| **Aurora** | The internal showcase brand (`showcases/aurora_group/`) used as a worked example throughout the framework. |

## Platform terms (OSS stack)

| Term | Meaning |
|---|---|
| **Evidence.dev** | Static-site BI tool (`products/open_source_stack/`). The primary OSS frontend. |
| **dbt** | Data transformation framework. Used by the OSS stack for metric definitions. |
| **Adapter** | A renderer that turns the IR `DashboardSpec` into a target tool's native format. Lives under `products/oss_adapters/tooling/adapters/` (Grafana, Metabase, Superset stubs) and `products/fabric/` (Power BI). |

## AI / agent terms

| Term | Meaning |
|---|---|
| **MCP** | Model Context Protocol. Tool-server protocol used by Studio (`studio/mcp-server.mjs`) and by the agent integrations to expose validators, deployers, and DAX execution to AI tools. |
| **Skill** | A reusable agent workflow (e.g. `add-usecase-scaffold`, `fix-stage1-failure`). Tool-agnostic Markdown in `docs/agent/skills/`; tool-specific wrappers (Cursor / Copilot) are generated. |
| **CLAUDE.md / AGENTS.md** | Operating rules for AI agents working in this repo. `CLAUDE.md` is for Claude Code; `AGENTS.md` documents skills shared across all agents. Both are kept in sync manually. |
| **Hooks (PostToolUse)** | Bash scripts in `.claude/hooks/` that run automatically after Write/Edit on TMDL or PBIR files to enforce style. Configured in `.claude/settings.json`. |

## Domain prefixes

See [`TAXONOMY.md`](TAXONOMY.md) for full ID schemes.

| Prefix | Domain |
|---|---|
| `COM` | Commercial (Sales, Marketing, CRM) |
| `FIN` | Finance |
| `OPS` | Operations |
| `SCM` | Supply Chain |
| `HR`  | People & HR (planned) |
| `MFG` | Manufacturing (planned) |
| `XD`  | Cross-Domain / Executive |
