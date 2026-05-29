# Contributing

Thank you for considering a contribution to the Analytics Strategy-to-Action Framework.

> **First time here?** See [`ONBOARDING.md`](ONBOARDING.md) for environment setup, reading order, and a first task. This doc covers the development workflow only.

## Development workflow

1. **Pick a task** — open issue, item from [`KNOWN_GAPS.md`](internal/project_mgmt/KNOWN_GAPS.md), or `internal/technical_backlog.md`.
2. **Create a branch** — `git checkout -b <type>/<short-name>` (e.g. `feat/add-hr-usecases`). Types: `feat`, `fix`, `docs`, `refactor`, `chore`.
3. **Make changes** — follow the conventions below.
4. **Run the quality gate** — `.\tooling\quality\run_quality_gate.ps1` (Stage 1 + Fabric; must pass before merge).
5. **Run the health scorecard** — `python tooling/health_scorecard.py` to verify framework metrics.
6. **Commit & push** — conventional-style messages (`feat:`, `fix:`, `docs:`, `refactor:`).
7. **Open a PR** — target `main`; describe what changed and why.

## Validation gates

| Gate | Command | Scope | Required |
|------|---------|-------|----------|
| **Quality gate** | `.\tooling\quality\run_quality_gate.ps1` | Stage 1 + Fabric/PBIR (CI runs this on Windows) | Yes (CI / pre-merge) |
| **Stage 1 only** | `.\tooling\run_stage1_checks.ps1` | Docs, refs, structure, KPI consistency | Subset of quality gate |
| **Fabric only** | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` | TMDL, PBIR, pbir-cli, P0 report quality | Subset of quality gate |
| **OSS** | `bash products/open_source_stack/tooling/run_oss_checks.sh` | Evidence.dev, dbt, adapters | If you changed OSS stack |
| **Full local** | `.\tooling\run_all_checks.ps1` | Stage 1 + Fabric | Recommended before release |
| **Health scorecard** | `python tooling/health_scorecard.py` | H1-H5 framework metrics | Recommended |
| **Registry (strict)** | `python tooling/ontology/registry_builder.py --strict` | Ontology graph integrity | When changing IDs / refs |

Run all commands from the **repository root**.

## Code conventions

- **Core ontology** (YAML/Markdown in `core/`): follow existing naming. IDs and file names are governed by [`TAXONOMY.md`](docs/reference/TAXONOMY.md) and [`SYSTEM_NAMING.md`](docs/reference/SYSTEM_NAMING.md).
- **Python**: follow PEP 8; use `logging` instead of bare `print` for diagnostics; no bare `except:`.
- **PowerShell**: use `Write-Verbose` in non-critical `catch` blocks; prefer splatting over long parameter lists.
- **Tests**: add or update tests for any code change under `tooling/` or `products/`. Run with `python -m pytest`.
- **Script and file naming**: see [`SYSTEM_NAMING.md`](docs/reference/SYSTEM_NAMING.md) (verb-first, snake_case, role-prefixed).
- **TMDL / PBIP**: hard rules enforced by PostToolUse hooks — see [`AGENTS.md`](AGENTS.md) § "TMDL Conventions".

## Adding a new use case

1. Create folder: `core/usecases/core/<ID>_<Name>/` (ID format per [`TAXONOMY.md`](docs/reference/TAXONOMY.md)).
2. Add `Business_Factsheet.md` (start from a template in `core/templates/`).
3. Add `UseCase_Bracket.yaml` matching the schema in `tooling/generator/schemas/`.
4. Reference KPIs from `core/kpi_catalog/` (create the KPI in the catalog first if it's new).
5. Wire action codes via `orchestration.action_code_ids` in the bracket; ensure each exists under `core/action_codes/<Domain>/`.
6. Run Stage 1 + health scorecard to verify the Golden Thread.

For a guided walkthrough use the `add-usecase-scaffold` skill in `docs/agent/skills/`.
