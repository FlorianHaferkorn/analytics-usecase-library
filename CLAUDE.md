# Analytics Use Case Library

An analytics strategy-to-action framework that traces the **Golden Thread** from business strategy through KPIs, use cases, semantic models, reports, and action codes.

## Project Structure

```
core/                    # Tool-agnostic framework artifacts
  action_codes/          # YAML action code definitions (by domain)
  kpi_catalog/           # KPI catalog Markdown files with fenced YAML blocks
  usecases/core/         # Use case folders: UseCase_Bracket.yaml + Business_Factsheet.md
  semantic_models/       # Domain semantic models + Measure_Dictionary_*.md
  data_contracts/        # Domain and source data contracts (YAML)
  brand/                 # Brand design system specs
  templates/             # Page and report templates

tooling/                 # Python tooling and validation
  ontology/              # registry_builder.py — builds master_registry.json
  validation/            # Stage 1 PowerShell checks + JSON schemas (Node.js Ajv)
  health_scorecard.py    # Framework health metrics (H1-H5)
  tests/                 # Python test suite (pytest)

products/                # Tool-specific implementations
  fabric/powerbi/        # Microsoft Fabric / Power BI (TMDL, DAX, deployment)
  open_source_stack/     # Evidence.dev / dbt (OSS alternative)
  proposal_costing/      # Cost estimation tool

internal/                # Project management, backlog, archive
```

## Key Commands

```bash
# Run all Python tests
python -m pytest

# Run tooling tests only
python -m pytest tooling/tests/ -v

# Run product tests only
python -m pytest products/ -v

# Local preflight (mirrors CI — run before pushing)
python tooling/preflight.py

# Registry builder (strict mode — used in CI)
python tooling/ontology/registry_builder.py --strict

# Health scorecard
python tooling/health_scorecard.py

# Stage 1 checks (PowerShell, runs in CI on Windows)
# ./tooling/run_stage1_checks.ps1 -Root .
```

## Naming Conventions

### KPI IDs
Format: `<domain>.<entity>.<metric>[.<qualifier>]` — 2-5 dot-separated lowercase segments.
Examples: `sales.net_sales.amount`, `crm.clv.amount`, `ops.oee.pct`

### Use Case IDs
Format: `<DOMAIN>-<NNN>` — uppercase prefix + 3-digit number.
Examples: `COM-001`, `FIN-002`, `SCM-003`

### Action Code IDs
Format: `<Prefix>-<Type><Seq>.<Sub>` — domain letter, action type, sequence, sub-version.
Examples: `C-M1.1`, `F-C2.1`, `O-P1.1`

### Data Contracts
Domain: `<domain_name>.yaml` (snake_case). Source: `<domain>_<source>.yaml`.

## Architecture Principles

- **Golden Thread**: Strategy → KPIs → Use Cases → Semantic Models → Reports → Actions
- **SSOT**: Each artifact is defined once; references point to the canonical source
- **Tool-agnostic core**: `core/` has no TMDL, DAX, SQL, or other tool syntax
- **Tool-specific products**: `products/<tool>/` adapts the core for specific BI platforms

## Health Scorecard (H1-H5)

| Metric | What it measures |
|--------|-----------------|
| H1 | Golden Thread: strategic KPIs fully traced through action codes + data contracts |
| H2 | Semantic Model Stability: percentage of measures with `status: active` |
| H3 | Data Contract Coverage: all domain contracts reference existing semantic models |
| H4 | Action Code Completeness: all action codes have required fields |
| H5 | Factsheet Quality: all factsheets have required sections (1-10) |

## CI Pipeline

- **Stage 1** (`.github/workflows/stage1.yml`): Runs on `windows-latest` with 17+ PowerShell validation checks. Hard gate for PRs.
- **Python checks**: Runs pytest, registry builder, and health scorecard on `ubuntu-latest`.

## Key Files

- `tooling/ontology/registry_builder.py` — Builds `master_registry.json`, validates referential integrity
- `tooling/health_scorecard.py` — Computes H1-H5 health metrics
- `tooling/validation/_index.yaml` — Taxonomy definitions (ID regexes, allowed roles/statuses)
- `TAXONOMY.md` — Human-readable naming conventions reference
