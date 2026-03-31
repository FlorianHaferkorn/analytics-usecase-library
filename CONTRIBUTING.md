# Contributing

Thank you for considering a contribution to the Analytics Strategy-to-Action Framework.

## Prerequisites

| Tool | Required for | Install |
|------|-------------|---------|
| **PowerShell** (or `pwsh`) | Stage 1 checks, Fabric tooling | Ships with Windows; `brew install powershell` on macOS |
| **Python 3.9+** | Registry builder, health scorecard, scaffold generator | [python.org](https://www.python.org/downloads/) |
| **Node.js 18+** | JSON-schema validation | [nodejs.org](https://nodejs.org/) |

## Quick setup

```bash
# Clone and enter the repo
git clone <repo-url> && cd analytics-usecase-library

# Install Python dependencies
pip install -r requirements.txt

# Install Node validation dependencies (one-time)
cd tooling/validation && npm ci && cd ../..
```

## Development workflow

1. **Pick a task** — browse open issues or choose a use case to extend.
2. **Create a branch** — `git checkout -b <type>/<short-name>` (e.g. `feat/add-hr-usecases`).
3. **Make changes** — follow the conventions below.
4. **Run Stage 1 checks** — `.\tooling\run_stage1_checks.ps1` (must pass before merge).
5. **Run the health scorecard** — `python tooling/health_scorecard.py` to verify framework metrics.
6. **Commit & push** — use conventional-style messages (`fix:`, `feat:`, `docs:`, `refactor:`).
7. **Open a PR** — target `main`; describe what changed and why.

## Code conventions

- **Core ontology** (YAML/Markdown in `core/`): follow existing naming (`snake_case` IDs, `PascalCase` filenames).
- **Python**: follow PEP 8; use `logging` instead of bare `print` for diagnostics; no bare `except:`.
- **PowerShell**: use `Write-Verbose` in non-critical `catch` blocks; prefer splatting over long parameter lists.
- **Tests**: add or update tests for any code change under `tooling/` or `products/`. Run with `python -m pytest`.

## File naming

| Layer | Pattern | Example |
|-------|---------|---------|
| Use case bracket | `UseCase_Bracket_v2.0.yaml` | `COM-001_Sales_Performance/UseCase_Bracket_v2.0.yaml` |
| Business factsheet | `Business_Factsheet.md` | `COM-001_Sales_Performance/Business_Factsheet.md` |
| Action code | `<ID>.yaml` | `core/action_codes/Commercial/C-M1.1.yaml` |
| Measure dictionary | `Measure_Dictionary_<Domain>.md` | `Measure_Dictionary_Commercial.md` |
| Data contract | `DC_<domain>_<source>.yaml` | `DC_commercial_sales.yaml` |

## Taxonomy & ID schemes

See [`TAXONOMY.md`](TAXONOMY.md) for the full taxonomy reference including:
- Domain prefixes (COM, FIN, OPS, SCM, HR, MFG)
- KPI ID format (`<domain>.<entity>.<metric>`)
- Action code ID format (`<Domain_Prefix>-<Type><Sequence>`)
- Use case ID format (`<Domain_Prefix>-<Sequence>`)

## Validation gates

| Gate | Command | Scope |
|------|---------|-------|
| **Stage 1** (CI) | `.\tooling\run_stage1_checks.ps1` | Docs, refs, structure, KPI consistency |
| **Fabric checks** | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` | TMDL, measures, DAX |
| **Full local** | `.\tooling\run_all_checks.ps1` | Stage 1 + Fabric |
| **Health scorecard** | `python tooling/health_scorecard.py` | H1-H5 framework metrics |
| **Registry** | `python tooling/ontology/registry_builder.py --strict` | Ontology graph integrity |

## Adding a new use case

1. Create folder: `core/usecases/core/<ID>_<Name>/`
2. Add `Business_Factsheet.md` (use `core/templates/` as starting point)
3. Add `UseCase_Bracket_v2.0.yaml`
4. Link KPIs in `core/kpi_catalog/` (create if missing)
5. Add action codes in `core/action_codes/<Domain>/`
6. Run Stage 1 + health scorecard to verify the Golden Thread
