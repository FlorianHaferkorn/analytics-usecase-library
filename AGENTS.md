# Agent Instructions — Analytics Use Case Library

This file is the entry point for **non-Claude agents** (Cursor, Copilot, Codex, Aider, …). For Claude Code, see [`CLAUDE.md`](CLAUDE.md).

## Where the rules actually live

The single source of truth for agent rules and skills is **[`docs/agent/`](docs/agent/)** (tool-agnostic Markdown). Tool-specific configs are **generated** — do not edit them directly:

| Tool | Generated files | Generator |
|------|----------------|-----------|
| Cursor | `.cursor/rules/*.mdc`, `.cursor/skills/*/SKILL.md` | `python tooling/agent/generate_tool_configs.py` |
| VS Code Copilot | `.github/copilot-instructions.md` | same generator |
| Claude Code | [`CLAUDE.md`](CLAUDE.md) | maintained manually |
| Other agents | This file (`AGENTS.md`) | maintained manually |

**To change a rule that applies to all agents**, edit the canonical file under `docs/agent/rules/`, then re-run the generator. To change Claude- or Cursor-specific behaviour, edit the wrapper.

## Operating rules

The full operating rules — Golden Thread principle, Use Case / Bracket / Factsheet conventions, KPI catalog and action code rules, scripts and CI gates, TMDL conventions — are documented once in [`CLAUDE.md`](CLAUDE.md) and apply to all agents. Read it.

A condensed version is also in:

- [`docs/agent/rules/framework-conventions.md`](docs/agent/rules/framework-conventions.md) — framework conventions
- [`docs/agent/rules/stage1-awareness.md`](docs/agent/rules/stage1-awareness.md) — Stage 1 gate
- [`docs/agent/rules/tmdl-dax.md`](docs/agent/rules/tmdl-dax.md) — TMDL / DAX style

## Skills (tool-agnostic)

Reusable workflows for AI agents and humans. Each skill is a complete workflow with validation, error handling, and a learning loop. Source files live in `docs/agent/skills/`; metadata in `docs/agent/skills/_index.yaml`.

### Core skills

| Skill | When to use |
|-------|-------------|
| [`add-usecase-scaffold`](docs/agent/skills/add-usecase-scaffold.md) | Create a new use case with Business Factsheet and UseCase_Bracket |
| [`edit-factsheet-safely`](docs/agent/skills/edit-factsheet-safely.md) | Edit Business factsheets without breaking Stage 1 |
| [`edit-usecase-bracket-safely`](docs/agent/skills/edit-usecase-bracket-safely.md) | Edit UseCase_Bracket.yaml without breaking orchestration |
| [`add-kpi-reference-safely`](docs/agent/skills/add-kpi-reference-safely.md) | Add a KPI reference only if it exists in the catalog |
| [`add-action-code-and-wire-up`](docs/agent/skills/add-action-code-and-wire-up.md) | Create/update action codes and wire them into use cases |
| [`assess-change-impact`](docs/agent/skills/assess-change-impact.md) | Assess blast radius before renaming/deleting IDs |
| [`fix-stage1-failure`](docs/agent/skills/fix-stage1-failure.md) | Diagnose and fix Stage 1 CI failures |
| [`stage1-pre-commit`](docs/agent/skills/stage1-pre-commit.md) | Run Stage 1 checks before committing |

### Fabric / Power BI skills

| Skill | When to use |
|-------|-------------|
| [`generate-and-validate-pbi-report`](docs/agent/skills/generate-and-validate-pbi-report.md) | Generate Power BI reports with iterative validation |
| [`fix-pbi-report-errors`](docs/agent/skills/fix-pbi-report-errors.md) | Diagnose and fix Power BI report / semantic model errors |
| [`fabric-powerbi-validation`](docs/agent/skills/fabric-powerbi-validation.md) | Validate Fabric output (TMDL, DAX, measures) |

### OSS stack skills

| Skill | When to use |
|-------|-------------|
| [`generate-oss-dashboard`](docs/agent/skills/generate-oss-dashboard.md) | Generate Evidence.dev dashboard pages from IR and bracket |
| [`fix-oss-dashboard-errors`](docs/agent/skills/fix-oss-dashboard-errors.md) | Diagnose and fix Evidence / OSS validation errors |
| [`oss-stack-validation`](docs/agent/skills/oss-stack-validation.md) | Validate OSS stack artifacts (adapter, pages, theme, SQL) |

## Learning loop

After fixing any new class of error, add a row to [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) (Symptom | Cause | Fix). This is mandatory — it's how the framework gets smarter.
