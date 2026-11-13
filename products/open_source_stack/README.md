# Open-Source Stack (Evidence.dev)

Platform-agnostic frontend implementation using [Evidence.dev](https://evidence.dev) (MIT license, zero fees). Logic is driven by Core (KPI catalog, use cases, semantic model); this stack is a **connector** that renders dashboards from that logic.

> **Architecture plan:** See [ARCHITECTURE.md](ARCHITECTURE.md) for full stack decisions, component parity with Fabric/Power BI, licensing audit, and development phases.

## Structure

```
open_source_stack/
  adapter.json          # Adapter manifest (build / validate / deploy contract)
  ARCHITECTURE.md       # Full architecture plan and decision log
  evidence_app/         # Evidence.dev application (pages, components, sources)
  dbt_project/          # dbt-core semantic layer (staging, marts, metrics)
  themes/               # Corporate design (Tailwind config, CSS variables)
  deploy/               # Docker, Terraform, auth proxy
  tooling/
    page_generator/     # Evidence page generator (mirrors Fabric PageScaffoldGenerator)
    metric_generator/   # dbt metric generator from IR KPI catalog
    validate_oss.py     # OSS validation runner
    run_oss_checks.sh   # Full OSS gate (validation + tests)
```

## Quick start

```bash
# Generate Evidence pages for a use case
python tooling/ontology/registry_builder.py
python tooling/ir/build_ir.py --kpi-catalog core/kpi_catalog
python -m products.open_source_stack.tooling.page_generator.generator --use-case COM-001

# Run OSS validation
python products/open_source_stack/tooling/validate_oss.py --root .

# Run full OSS gate (validation + tests)
bash products/open_source_stack/tooling/run_oss_checks.sh
```

## Agent workflow

- **Input:** IR (`tooling/ir/out/ir_v1.json`) + UseCase Bracket
- **Template:** `core/templates/evidence_page_template.md` (design tokens: `fill-primary`, `text-brand-header`, `bg-surface`)
- **Output:** Pages under `evidence_app/pages/` (e.g. `com_001_overview.md`) with SQL and Evidence components

When adding a new dashboard for a KPI or use case, use the page generator or the Evidence template and the SQL/logic from the semantic model; do not define new metrics in the page.

**Agent skills:** `docs/agent/skills/generate-oss-dashboard.md`, `docs/agent/skills/oss-stack-validation.md`, `docs/agent/skills/fix-oss-dashboard-errors.md`

## Data (pluggable storage)

| Tier | Storage | Query Engine | Cost |
|------|---------|-------------|------|
| **Zero-cost** | Local Parquet/CSV | DuckDB (embedded) | $0 |
| **Small team** | PostgreSQL | Postgres-native | $0 (self-hosted) |
| **Cloud** | S3/GCS/ADLS + Iceberg | Trino / Athena | Pay-per-query |

- Local/dev: DuckDB source `gold` in `evidence_app/sources/gold/` (`connection.yaml` + one `<table>.sql`
  per table the pages read). Without a dbt build the tables carry their column contract and one
  all-NULL row, so the site builds and shows no values.
- Build: `cd evidence_app && npm ci && npm run sources && npm run build` (Evidence 40; `evidence.config.yaml`
  lists the plugins, `package.json` pins the peers Evidence declares, `validate_oss.py` checks both)
- Production: Postgres or warehouse; credentials outside repo (env or secrets)

## Security and DSGVO

- Protect the app behind an identity proxy (Authentik, Keycloak, or Traefik auth) so that only authenticated users see data.
- No tracking; no telemetry to third parties. All changes are Git-versioned for audit.

## Validation gates

| Gate | Scope | Command |
|------|-------|---------|
| **Stage 1 (Core)** | `core/`, `tooling/` — tool-agnostic | `./tooling/run_stage1_checks.ps1` |
| **Fabric Gate** | `products/fabric/` — TMDL, DAX, PBIP | `./products/fabric/powerbi/tooling/run_fabric_checks.ps1` |
| **OSS Gate** | `products/open_source_stack/` — Evidence, dbt | `bash products/open_source_stack/tooling/run_oss_checks.sh` |
