# Open-Source Stack — Architecture Plan

> Status: **Draft v1.0** · Last updated: 2026-03-28

This document defines the open-source (OSS) stack that mirrors the
Fabric / Power BI connector — same governance, same agent workflow, same
3-30-300 page model — but built entirely on OSS components that can run
on any hyperscaler or on-premises.

---

## 1 Design Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **IR-first** | The OSS adapter consumes `ir_v1.json` — never reads `core/` directly. Same contract as Fabric adapter. |
| 2 | **Core stays untouched** | KPI catalog, use-case brackets, action codes, data contracts, page templates — all reused as-is. |
| 3 | **One adapter, three commands** | `build(ir) → dist/`, `validate(dist) → report`, `deploy(dist, env) → audit`. Matches `adapter_manifest.schema.json`. |
| 4 | **Hyperscaler-agnostic base** | Pick one primary cloud (AWS, GCP, or Azure) and layer OSS on top; avoid vendor lock-in in the adapter itself. |
| 5 | **Test-driven from day one** | Every generator, validator, and builder has pytest coverage before it ships. |

---

## 2 Stack Decision Matrix

### 2.1 Visualization Layer — Evidence.dev (confirmed)

| Candidate | Strengths | Weaknesses | Verdict |
|-----------|-----------|------------|---------|
| **Evidence.dev** | Code-as-dashboard (Markdown + SQL), Git-native, Tailwind themes, SSG/SSR, lightweight | Smaller community than Superset | **Selected** |
| Apache Superset | Rich UI, wide SQL support | Heavy (Docker), dashboard-as-config not Git-native, hard to template | Rejected |
| Metabase | Easy setup, embedded analytics | YAML-driven dashboards limited, less programmatic control | Rejected |
| Grafana | Best for time-series / ops | Not suited for business-analytics 3-30-300 pattern | Rejected |
| Redash | Simple SQL → chart | Maintenance mode, no active development | Rejected |

**Why Evidence.dev wins:**

- **Git-native**: Pages are Markdown files with embedded SQL — perfect for our agent workflow where pages are generated from IR/KPI catalog and committed to Git.
- **Template-driven**: Our `evidence_page_template.md` already defines the 3-30-300 pattern with design tokens. A page generator can produce Evidence Markdown the same way `page_scaffold_generator` produces PBIP JSON.
- **Tailwind theming**: Maps directly to our `theme_config.json` design tokens.
- **Static build**: `npm run build` produces a static site — easy to deploy behind any auth proxy.
- **SQL-first**: Queries run against the configured source (DuckDB dev, Postgres/warehouse prod) — no proprietary query language.

### 2.2 Data Platform

The OSS data platform mirrors Fabric's medallion architecture (Bronze → Silver → Gold → Semantic) using open components:

| Layer | Fabric Equivalent | OSS Component | Role |
|-------|-------------------|---------------|------|
| **Object Storage** | OneLake | S3 / GCS / ADLS (or MinIO on-prem) | Raw file landing zone |
| **Table Format** | Delta Lake (Fabric) | **Apache Iceberg** (primary) or Delta Lake | ACID tables, time-travel, schema evolution |
| **Query Engine** | Spark + T-SQL (Warehouse) | **DuckDB** (dev/CI) + **Trino** (prod) | Federated SQL across Iceberg tables |
| **Transformation** | Dataflows / Notebooks | **dbt-core** (with dbt-trino or dbt-duckdb adapter) | Bronze→Silver→Gold transformations |
| **Orchestration** | Data Factory / Pipelines | **Dagster** (or Airflow) | Pipeline scheduling, observability, lineage |
| **Semantic Layer** | Power BI Semantic Model (DAX) | **dbt Semantic Layer** (MetricFlow) | KPI definitions as code, metric governance |
| **Catalog / Governance** | Purview | **DataHub** (or OpenMetadata) | Metadata catalog, lineage, data quality |

**Why this combination:**

- **Iceberg** is the industry-converging open table format (supported by AWS, GCP, Snowflake, Databricks). Delta Lake is an alternative if deploying on Azure/Databricks.
- **DuckDB** for local/CI means developers and the CI pipeline can run the full stack without a cluster. The same SQL works against Trino in production.
- **dbt-core** for transformations gives us version-controlled, tested SQL models — the OSS equivalent of Fabric notebooks/dataflows.
- **dbt Semantic Layer (MetricFlow)** maps to our KPI catalog: each KPI becomes a dbt metric with dimensions, filters, and grain — replacing DAX measures.
- **Trino** as the production query engine provides federated SQL across Iceberg, Postgres, and other sources.
- **Dagster** for orchestration because it's asset-centric (like our use-case-driven model) and has built-in dbt integration.

### 2.3 Hyperscaler Base Options

Any of these work — the adapter is cloud-agnostic, only the infrastructure provisioning differs:

| Hyperscaler | Object Storage | Compute | Managed Trino | Managed Iceberg |
|-------------|---------------|---------|---------------|-----------------|
| **AWS** | S3 | ECS / EKS | Amazon Athena (Trino-based) | AWS Glue Iceberg tables |
| **GCP** | GCS | Cloud Run / GKE | Starburst on GKE (or BigLake) | BigLake Iceberg |
| **Azure** | ADLS Gen2 | ACI / AKS | Starburst on AKS | OneLake Iceberg shortcuts |
| **On-prem** | MinIO | Docker / K8s | Self-hosted Trino | Hive Metastore + Iceberg |

**Recommendation:** Start with **AWS** (Athena + S3 + Iceberg) for the reference deployment — widest Iceberg support, Athena is serverless Trino, and the free tier covers development. Provide Terraform/Pulumi modules for each cloud.

---

## 3 Component Parity with Fabric / Power BI

Every Fabric component has an OSS counterpart:

| Fabric Component | Location | OSS Counterpart | OSS Location |
|------------------|----------|-----------------|--------------|
| Page Scaffold Generator | `products/fabric/powerbi/tooling/page_scaffold_generator/` | **Evidence Page Generator** | `products/open_source_stack/tooling/page_generator/` |
| PBIP Writer | `…/pbip_writer.py` | **Markdown Writer** | `…/page_generator/markdown_writer.py` |
| Visual Builder | `…/visual_builder.py` | **Component Builder** | `…/page_generator/component_builder.py` |
| Grid Calculator | `…/grid_calculator.py` | **Layout Calculator** (CSS grid) | `…/page_generator/layout_calculator.py` |
| Visual Validator | `…/visual_validator.py` | **Page Validator** | `…/page_generator/page_validator.py` |
| Theme Application | `…/apply_report_theme.py` | **Theme Builder** | `…/tooling/theme_builder.py` |
| Report Doc Generator | `…/report_documentation_generator/` | **Dashboard Doc Generator** | `…/tooling/doc_generator/` |
| TMDL Measure Generator | `tooling/generation/generate_tmdl_measures.ps1` | **dbt Metric Generator** | `…/tooling/metric_generator/` |
| Fabric Orchestrator | `products/fabric/orchestrator/` | **Infra Provisioner** (Terraform) | `…/deploy/terraform/` |
| Fabric Validation Checks | `tooling/validation/validate_tmdl.ps1` etc. | **OSS Validation Checks** | `…/tooling/validate_oss.py` |
| Agent Skills (PBI) | `.cursor/skills/fabric-powerbi-validation/` | **Agent Skills (OSS)** | `.cursor/skills/oss-stack-validation/` |
| Deployment Scripts | `…/deployment/scripts/fabric_*.py` | **Deploy CLI** | `…/deploy/deploy_cli.py` |

---

## 4 Evidence Page Generator — Design

The page generator is the heart of the OSS stack, mirroring the Fabric
`PageScaffoldGenerator`. It reads IR + UseCase Bracket and produces
Evidence Markdown pages.

### 4.1 Input → Output Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  ir_v1.json      │────▶│  Evidence Page    │────▶│ evidence_app/pages/ │
│  UseCase_Bracket │     │  Generator        │     │   com_001_overview.md│
│  theme_config    │     │  (Python)         │     │   com_001_detail.md  │
│  page_templates  │     └──────────────────┘     └─────────────────────┘
└─────────────────┘              │
                                 ▼
                        ┌──────────────────┐
                        │  Page Validator   │
                        │  (lint + schema)  │
                        └──────────────────┘
```

### 4.2 Module Structure

```
products/open_source_stack/tooling/page_generator/
├── __init__.py
├── generator.py          # Main orchestrator (like scaffold_generator.py)
├── config_loader.py      # Load IR, bracket, governance files
├── component_builder.py  # Map visual slots → Evidence components
├── markdown_writer.py    # Emit .md files with SQL + components
├── layout_calculator.py  # CSS grid mapping from 12×12 governance grid
├── page_validator.py     # Validate generated pages against rules
├── sql_builder.py        # Generate SQL from KPI catalog / data contracts
└── tests/
    ├── conftest.py
    ├── test_generator.py
    ├── test_component_builder.py
    ├── test_markdown_writer.py
    ├── test_layout_calculator.py
    ├── test_sql_builder.py
    └── test_page_validator.py
```

### 4.3 Visual Slot → Evidence Component Mapping

| Power BI Visual | Evidence Component | Notes |
|-----------------|-------------------|-------|
| KPI Card with Delta | `<BigValue>` + `<Delta>` | 3-second layer |
| Trend Line | `<LineChart>` | 30-second layer |
| Bar Chart | `<BarChart>` | 30-second layer |
| Matrix with Data Bars | `<DataTable>` | 300-second layer |
| Slicer (Top Bar) | `<Dropdown>` / `<ButtonGroup>` | Filter controls |
| Slicer (Left Pane) | `<Dropdown>` in sidebar | Filter controls |
| Smart Narrative | `<Value>` + Markdown prose | AI-generated text |
| Action Panel | Custom `<Alert>` / `<Callout>` | Decision prompts |

---

## 5 dbt Metric Generator — Design

Replaces TMDL/DAX measure generation. Reads KPI catalog from IR and produces
dbt metric YAML files.

### 5.1 Output Structure

```
products/open_source_stack/dbt_project/
├── dbt_project.yml
├── models/
│   ├── staging/          # Bronze → Silver
│   ├── marts/            # Silver → Gold (star schema)
│   │   ├── dim_time.sql
│   │   ├── dim_organization.sql
│   │   ├── fact_sales.sql
│   │   └── ...
│   └── metrics/          # Generated from KPI catalog
│       ├── _metrics.yml  # dbt metric definitions
│       └── ...
├── seeds/                # Reference data
└── tests/                # dbt tests (schema + data)
```

### 5.2 KPI → dbt Metric Mapping

```yaml
# KPI catalog entry (in ir_v1.json)
# kpi_id: KPI-COM-001
# kpi_key: Net Sales
# dax_expression: SUM(fact_sales[net_sales_amount])

# Generated dbt metric:
metrics:
  - name: net_sales
    label: "Net Sales"
    description: "Total net sales amount"
    type: simple
    type_params:
      measure: sum_net_sales_amount
    filter: null
    meta:
      kpi_id: KPI-COM-001
      source: ir_v1.json
```

---

## 6 Validation & Quality Gates

### 6.1 OSS-Specific Checks (mirrors Fabric checks)

| Check | What it validates | Fabric equivalent |
|-------|-------------------|-------------------|
| `validate_evidence_pages` | Markdown structure, SQL syntax, component usage | `validate_report.ps1` |
| `validate_dbt_models` | dbt model compilation, metric refs | `validate_tmdl.ps1` |
| `validate_dbt_metrics` | Metric ↔ KPI catalog alignment | `validate_dax.ps1` |
| `validate_sql_style` | SQL best practices (no SELECT *, explicit JOINs) | `bpa-rules-dax.json` |
| `validate_theme_tokens` | Evidence pages use only governed design tokens | `validate_semanticmodel.ps1` |
| `check_metrics_vs_kpi` | Every KPI in bracket has a dbt metric | `check_measures_vs_kpi.ps1` |

### 6.2 CI Integration

```yaml
# .github/workflows/stage1.yml addition:
- name: Run OSS stack checks
  if: contains(github.event.pull_request.labels.*.name, 'oss-stack')
  run: python products/open_source_stack/tooling/validate_oss.py --root $GITHUB_WORKSPACE
```

### 6.3 Test Strategy

| Layer | Tool | What |
|-------|------|------|
| **Unit tests** | pytest | Page generator, component builder, SQL builder, layout calculator |
| **Schema tests** | ajv (existing) | Evidence config YAML, dbt metric YAML against schemas |
| **dbt tests** | dbt test | Model integrity (not_null, unique, relationships) |
| **Integration tests** | pytest + DuckDB | End-to-end: IR → generate pages → build Evidence → assert output |
| **Visual regression** | Playwright (optional) | Screenshot comparison of rendered Evidence pages |

---

## 7 Agent Skills (OSS)

New skills to add alongside existing Fabric skills:

### 7.1 `generate-oss-dashboard` Skill

Mirrors `generate-and-validate-pbi-report.md`:

1. Read `UseCase_Bracket.yaml` for the target use case
2. Run `build_ir.py --kpi-catalog` to refresh IR
3. Run the Evidence Page Generator for the use case
4. Run `validate_oss.py` on generated pages
5. If validation passes → commit pages to `evidence_app/pages/`
6. If validation fails → report errors with fix suggestions

### 7.2 `fix-oss-dashboard-errors` Skill

Mirrors `fix-pbi-report-errors.md`:

1. Read validation output from `validate_oss.py`
2. Map error → root cause → fix path
3. Apply fixes (SQL corrections, component swaps, token fixes)
4. Re-run validation to confirm

### 7.3 `oss-stack-validation` Skill

Mirrors `fabric-powerbi-validation`:

1. Run `validate_evidence_pages`
2. Run `validate_dbt_models` (if dbt project exists)
3. Run `check_metrics_vs_kpi`
4. Report results with links to failing files

---

## 8 Directory Structure (Target)

```
products/open_source_stack/
├── README.md                         # Updated overview
├── ARCHITECTURE.md                   # This document
├── adapter.json                      # Adapter manifest (adapter_manifest.schema.json)
│
├── tooling/
│   ├── page_generator/               # Evidence page generator (Python)
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── config_loader.py
│   │   ├── component_builder.py
│   │   ├── markdown_writer.py
│   │   ├── layout_calculator.py
│   │   ├── page_validator.py
│   │   ├── sql_builder.py
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_generator.py
│   │       ├── test_component_builder.py
│   │       ├── test_markdown_writer.py
│   │       ├── test_layout_calculator.py
│   │       ├── test_sql_builder.py
│   │       └── test_page_validator.py
│   │
│   ├── metric_generator/             # dbt metric generator from IR
│   │   ├── __init__.py
│   │   ├── generate_dbt_metrics.py
│   │   └── tests/
│   │       └── test_generate_dbt_metrics.py
│   │
│   ├── theme_builder.py              # Generate Evidence theme from theme_config.json
│   ├── validate_oss.py               # OSS validation runner (like run_fabric_checks.ps1)
│   ├── doc_generator/                # Dashboard documentation generator
│   │   ├── generate_dashboard_docs.py
│   │   └── tests/
│   │       └── test_generate_dashboard_docs.py
│   └── requirements.txt
│
├── evidence_app/                     # Evidence.dev application
│   ├── pages/                        # Generated dashboard pages (.md)
│   ├── components/                   # Reusable Evidence components
│   ├── sources/                      # Data source configs
│   ├── evidence.config.yaml          # Evidence configuration
│   └── package.json
│
├── dbt_project/                      # dbt-core project (semantic layer)
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/
│   │   ├── marts/
│   │   └── metrics/
│   ├── seeds/
│   └── tests/
│
├── themes/                           # Tailwind config + CSS variables
│   ├── README.md
│   └── tailwind.config.js
│
└── deploy/
    ├── README.md
    ├── docker-compose.yml            # Local: Evidence + DuckDB + auth proxy
    ├── deploy_cli.py                 # Deployment CLI (mirrors fabric_setup.py)
    └── terraform/                    # Cloud provisioning
        ├── aws/                      # S3 + Athena + ECS
        ├── gcp/                      # GCS + BigQuery + Cloud Run
        └── azure/                    # ADLS + Synapse + ACI
```

---

## 9 Development Phases

### Phase 1 — Foundation (current milestone)

- [x] Architecture plan (this document)
- [ ] Adapter manifest (`adapter.json`)
- [ ] Evidence Page Generator with tests
  - `generator.py`, `config_loader.py`, `component_builder.py`
  - `markdown_writer.py`, `layout_calculator.py`, `page_validator.py`
  - `sql_builder.py`
- [ ] Validation script (`validate_oss.py`)
- [ ] Agent skill: `oss-stack-validation`

### Phase 2 — Semantic Layer

- [ ] dbt project scaffold (`dbt_project/`)
- [ ] dbt Metric Generator from IR
- [ ] `check_metrics_vs_kpi` validation
- [ ] Agent skill: `generate-oss-dashboard`

### Phase 3 — Deployment & Infrastructure

- [ ] Docker Compose (Evidence + DuckDB + Authentik)
- [ ] Deploy CLI (`deploy_cli.py`)
- [ ] Terraform modules (AWS first, then GCP/Azure)
- [ ] CI workflow extension for OSS checks

### Phase 4 — Parity & Polish

- [ ] Dashboard documentation generator
- [ ] Theme builder (auto-generate from `theme_config.json`)
- [ ] Agent skill: `fix-oss-dashboard-errors`
- [ ] Integration tests (IR → pages → build → assert)
- [ ] Showcase: Aurora Group on OSS stack

---

## 10 Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-28 | Evidence.dev as visualization layer | Git-native, Markdown+SQL, template-driven, Tailwind themes — best fit for agent workflow |
| 2026-03-28 | Apache Iceberg as table format | Industry convergence, multi-cloud, time-travel, schema evolution |
| 2026-03-28 | DuckDB (dev) + Trino (prod) as query engines | Zero-infra dev, same SQL in prod, Iceberg support |
| 2026-03-28 | dbt-core for transformations + semantic layer | Version-controlled SQL, metric governance, replaces DAX measures |
| 2026-03-28 | Dagster for orchestration | Asset-centric model fits use-case-driven architecture, native dbt integration |
| 2026-03-28 | AWS as reference hyperscaler | Widest Iceberg support (Athena = serverless Trino), free tier for dev |
| 2026-03-28 | Python for all OSS tooling | Consistency with existing generators, pytest ecosystem, dbt/Dagster are Python |
