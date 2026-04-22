# Architecture Overview

**Audience:** Technical stakeholders, new engineers, architects, escrow agents.  
**Scope:** System design, critical dependencies, file ownership, regeneration requirements.  
**Length:** ~2000 words.

---

## 1. System Context & Purpose

The **Analytics Strategy-to-Action Framework** is a pragmatic, scalable blueprint for translating business strategy into action-ready analytics. Unlike typical BI tools that serve reports, this framework ensures that:

- **Strategy is traced to KPIs** — Every KPI links back to a strategic objective.
- **KPIs are action-ready** — Designed to trigger decisions, not just describe performance.
- **Actions are governed** — Action codes define when, how, and by whom decisions execute.
- **Measures are reusable** — Single source of truth (SSOT) ensures consistency across reports and use cases.

The system is **platform-agnostic by design**: Core logic (KPI definitions, action codes, use case designs) lives in portable YAML/Markdown; platform-specific implementations (Fabric/Power BI, Evidence.dev, Metabase, Superset) are derived from that core.

---

## 2. System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STRATEGY LAYER                              │
│  (company_strategy.md, reporting_principles.md)                    │
│  Strategic objectives, decision domains, KPI governance             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                    CORE DEFINITION LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  KPI Catalog (core/kpi_catalog/)                           │   │
│  │  • 100+ strategic, operational, supporting KPIs            │   │
│  │  • Formulas, lineage, data requirements                    │   │
│  │  • Domain-specific definitions (Sales, Finance, Ops, etc.) │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Action Codes (core/action_codes/)                         │   │
│  │  • 40+ reusable decision/steering rules                    │   │
│  │  • Triggers, guardrails, execution steps                   │   │
│  │  • Domain-owned, cross-use-case reuse                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Use Cases (core/usecases/core/)                           │   │
│  │  • 16 core use cases (COM, FIN, OPS, SCM, XD domains)      │   │
│  │  • Business Factsheet (prose) + UseCase_Bracket.yaml       │   │
│  │  • References KPIs + action codes, not redefines them      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Templates (core/templates/)                               │   │
│  │  • Page layout templates (3-30-300 pattern)                │   │
│  │  • KPI catalog templates                                   │   │
│  │  • Action code templates                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Data Contracts (core/data_contracts/)                     │   │
│  │  • Domain contracts (sales, finance, operations, etc.)     │   │
│  │  • Source contracts (ERP, CRM, warehouse, etc.)            │   │
│  │  • Column lineage and grain definitions                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼────────┐ ┌──────▼────────┐
│  IR GENERATION │ │   GENERATION  │ │  VALIDATION   │
│ (tooling/ir/)  │ │ (tooling/gen) │ │ (tooling/)    │
│                │ │               │ │               │
│ • build_ir.py │ │ • TMDL measure│ │ • Stage 1     │
│ • Bracket YAML│ │   generator    │ │   checks      │
│   → IR JSON   │ │ • Page layout  │ │ • Health card │
│                │ │   generator    │ │ • Registry    │
│                │ │ • Measure dict │ │               │
└────────────────┘ └────────────────┘ └───────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────────────────┐
        │                  │                              │
┌───────▼─────────┐ ┌──────▼──────────┐ ┌──────────────▼──┐
│  FABRIC/POWER   │ │  OSS STACK      │ │  OSS ADAPTERS   │
│  BI PRODUCT     │ │  (Evidence.dev) │ │ (Grafana/etc)   │
│                 │ │                 │ │                 │
│ ./dist/PBIP     │ │ ./oss_reports   │ │ ./adapters/     │
│ TMDL measures   │ │ dbt metrics     │ │ Metabase.py     │
│ semantic model  │ │ Evidence pages  │ │ Superset.py     │
│ Power BI reports│ │ source adapter  │ │ Grafana.py      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │                  │                      │
        └──────────────────┼──────────────────────┘
                           │
        ┌──────────────────┼──────────────────────┐
        │                  │                      │
┌───────▼────────┐ ┌──────▼────────┐ ┌──────────▼──┐
│ FABRIC WORKSPACE│ │ EVIDENCE SITE │ │BI TOOL      │
│ (Microsoft)     │ │ (Cloud or OSS)│ │ (On-Premise)│
│                 │ │               │ │             │
│ Semantic model  │ │ Live dashboard│ │ Dashboards  │
│ Reports         │ │ Self-service  │ │ Embedded    │
│ Refreshes       │ │ Mobile-ready  │ │             │
└─────────────────┘ └───────────────┘ └─────────────┘
```

---

## 3. Data Flow: Strategy to Action

```
1. DEFINE (core/kpi_catalog/)
   └─→ business_strategy.md defines strategic objectives
   └─→ KPI_Catalog.md: 100+ KPIs per domain
       └─→ Each KPI has: definition, lineage, formula, targets
       └─→ Roles: strategic (H1), influencing, operational, supporting

2. COMPOSE (core/usecases/core/)
   └─→ Use Case Bracket: declarative (YAML)
       └─→ orchestration.influencing_kpi_ids: [KPI1, KPI2, ...]
       └─→ orchestration.action_code_ids: [C-M1, F-C2, ...]
       └─→ value_driver_model: formula linking KPIs
       └─→ ux_layout_rules: page structure (3-30-300)

3. VALIDATE (tooling/)
   └─→ Stage 1 checks (YAML syntax, KPI references, refs exist)
   └─→ Health scorecard (Golden Thread coverage H1–H5)
   └─→ Schema validation (Ajv + JSON schemas)

4. GENERATE (tooling/ir/ → tooling/generation/)
   └─→ IR Builder: Bracket YAML → DashboardSpec IR (JSON)
   └─→ TMDL Generator: IR + KPI Catalog → _Measures.tmdl (DAX)
   └─→ Page Generator: IR + Templates → Report.pbir (JSON)
   └─→ OSS Generators: IR → dbt metrics, Evidence.dev pages

5. BUILD (products/fabric/powerbi/orchestrator/)
   └─→ Table Operations: Create/update fact and dim tables
   └─→ Relationship Engine: Link tables per data contract grain
   └─→ TMDL Compiler: Validate DAX syntax, measure dependencies
   └─→ PBIP Assembly: Merge measures + pages into semantic model

6. DEPLOY (products/fabric/powerbi/deployment/)
   └─→ Export PBIP to Fabric workspace
   └─→ Trigger semantic model refresh
   └─→ Publish reports
   └─→ Execute DAX validation checks

7. MONITOR (health_scorecard.py, registry_builder.py)
   └─→ H1: Golden Thread coverage (KPI → use case → measure → contract → action)
   └─→ H2: Semantic Model Stability (TMDL syntax, measure deps)
   └─→ H3: Data Contract Coverage (all data sources defined)
   └─→ H4: Action Code Completeness (actions reference defined KPIs)
   └─→ H5: Factsheet Quality (factsheets have required sections)
```

---

## 4. Key Directories & Ownership

| Directory | Purpose | Owner | Read-only? |
|-----------|---------|-------|-----------|
| `core/kpi_catalog/` | KPI definitions (SSOT) | Business/Finance | Mostly (via CR) |
| `core/action_codes/` | Action logic & execution rules | Domain leaders | Yes (via PR) |
| `core/usecases/core/` | 16 core use cases (YAML + prose) | Business analysts | Yes (via PR) |
| `core/templates/` | Page, measure, data contract templates | Framework team | Mostly (via CR) |
| `core/data_contracts/` | Domain & source grain definitions | Data architects | Mostly (via CR) |
| `tooling/ir/` | Intermediate representation (IR) builder | Framework team | Yes (rarely changes) |
| `tooling/generation/` | TMDL, page, metric generators | Framework team | Yes (rarely changes) |
| `tooling/validation/` | Schema validation, Stage 1 checks | Framework team | Yes (rarely changes) |
| `tooling/ontology/` | Golden Thread discovery, health scorecard | Framework team | Yes (rarely changes) |
| `products/fabric/powerbi/dist/` | Generated PBIP artifacts | Generated | Ignore (auto) |
| `products/fabric/powerbi/orchestrator/` | Table ops, TMDL compilation | Framework team | Yes (rarely changes) |
| `products/open_source_stack/` | Evidence.dev frontend & dbt | Framework team | Yes (rarely changes) |
| `products/oss_adapters/` | Grafana/Metabase/Superset stubs | Framework team | Yes (incomplete) |
| `studio/` | Next.js interaction layer | Framework team | Yes (rarely changes) |
| `showcases/aurora_group/` | Example PBIP report (read-only demo) | Framework team | Ignore (read-only) |

---

## 5. Critical Path: Minimum Viable System

If you can regenerate these files and directories, you can regenerate the entire framework:

### Must-Have Files (Existence)
- `core/kpi_catalog/KPI_Catalog.md` — Authoritative KPI definitions
- `core/kpi_catalog/golden_20.yaml` — Strategic KPI set (H1 metrics)
- `core/action_codes/impactful_15.yaml` — Core action codes
- `core/usecases/core/*/UseCase_Bracket.yaml` — All 16 use case definitions (×16)

### Must-Have Directories (Functionality)
- `tooling/ir/` — IR builder (build_ir.py, IR schema)
- `tooling/generation/` — TMDL, page, metric generators
- `tooling/validation/` — Schema validator, Stage 1 checks
- `tooling/ontology/` — Registry builder, health scorecard
- `products/fabric/powerbi/orchestrator/` — TMDL compiler, table ops
- `core/templates/` — Page templates (3-30-300 layout)
- `core/data_contracts/` — Domain contracts (grain, source truth)

### If These Survive, You Can Recover
All other files and directories can be regenerated. Priority recovery sequence:

1. Clone repo, install deps (pip, npm)
2. Verify critical files exist: `python3 tooling/ontology/registry_builder.py --repo-root . --strict`
3. Run Stage 1: `.\tooling\run_stage1_checks.ps1`
4. Regenerate TMDL measures: `.\tooling\generation\generate_tmdl_measures.ps1`
5. Rebuild Fabric PBIP: `.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1`

---

## 6. Top 10 Dependencies

### Python (Core + Generation)

| Package | Version | License | Maintainer | Used for |
|---------|---------|---------|-----------|----------|
| PyYAML | ≥6.0 | MIT | PyYAML team | YAML parsing (core) |
| jsonschema | ≥4.17.0 | MIT | Julian Berman | Schema validation (Stage 1) |
| typer | ≥0.9.0 | MIT | Sebastián Ramírez | CLI for proposal costing |
| rich | ≥13.7.0 | MIT | Will McGugan | Pretty-printed console output |
| pytest | (test dep) | MIT | pytest team | Test runner |

### Node.js (Validation)

| Package | Version | License | Maintainer | Used for |
|---------|---------|---------|-----------|----------|
| ajv | 8.12.0 | MIT | Evgeny Poberezkin | JSON schema validation |
| yaml | 2.4.2 | ISC | Eemeli Aro | YAML validation |
| next | ^16.2.1 | MIT | Vercel | Studio frontend (optional) |
| react | ^19.2.4 | MIT | Meta | Studio UI (optional) |

### System (Required)

| Tool | Version | License | Purpose |
|------|---------|---------|---------|
| PowerShell | 7+ | MIT | Stage 1 checks, TMDL compiler (Windows/macOS) |
| Python | 3.9+ | PSF | Core tooling, generation, health scorecard |
| Node.js | 18+ | MIT | Schema validation (ajv) |
| Git | 2.30+ | GPL-2.0 | Version control (required) |

**Note:** The framework is intentionally minimal. Fabric SDK and Power BI SDK are only required when deploying to Fabric; they are not part of the core framework.

---

## 7. Regeneration Contract

When regenerating the framework in a new environment:

### Input (SSOT)
```
core/kpi_catalog/KPI_Catalog.md
core/kpi_catalog/golden_20.yaml
core/action_codes/
core/usecases/core/*/UseCase_Bracket.yaml
core/data_contracts/domains/
core/templates/
```

### Generated (Auto, Overwrite OK)
```
products/fabric/powerbi/dist/Domain.SemanticModel/*.tmdl
products/fabric/powerbi/dist/Domain.Report/*.pbir
products/open_source_stack/metrics.yml (dbt)
products/open_source_stack/evidence_app/pages/*.md
tooling/ontology/*.json (registry)
```

### Procedure (From Root)
```powershell
# Windows/CI
.\tooling\run_stage1_checks.ps1                                 # Validate core
.\tooling\generation\generate_tmdl_measures.ps1                 # TMDL → dist/
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 # Assemble PBIP
```

```bash
# Linux/macOS/CI
python3 tooling/ontology/registry_builder.py --repo-root . --strict  # Verify
python3 -m pytest tooling/tests/ -q                                  # Test
python3 products/oss_adapters/orchestrator/orchestrate_oss.py \
  --bracket core/usecases/core/COM-001/UseCase_Bracket.yaml \
  --adapter metabase                                             # Generate for other BI
```

---

## 8. Platform-Specific Notes

### Fabric / Power BI
- **Semantic model:** Direct Lake or Import mode, single fact table family per domain
- **TMDL:** Tab-indented, `=` for DAX, `/// Purpose:` comments above measures
- **PBIP:** JSON-based, supports version control; use `fab import`/`export` for lifecycle
- **Schemas:** `tooling/ai/schemas/usecase_bracket.schema.json`, `kpi_definition.schema.json`

### Evidence.dev (OSS Stack)
- **Frontend:** Node.js + Svelte, self-hosted
- **Data source:** dbt metrics + SQL
- **Config:** `products/open_source_stack/metrics.yml`, Evidence.dev pages in Markdown
- **Zero licensing:** Completely open source

### Grafana / Metabase / Superset (Adapters)
- **Status:** Stub implementations; not yet production-ready
- **Orchestrator:** `products/oss_adapters/orchestrator/orchestrate_oss.py`
- **Integration path:** Extend adapters to emit native JSON/Python configs

---

## 9. Governance & Change Management

### Who Can Modify What

| Artifact | Can Modify | Via |
|----------|-----------|-----|
| KPI definitions | Business + Data architects | PR + CR (SSOT) |
| KPI catalog structure | Framework team | PR + CR |
| Action codes | Domain leads | PR + CR |
| Use cases | Business analysts | PR + CR |
| Generators | Framework team | PR + CR + testing |
| Templates | Framework team | PR + CR |
| CI gates | Framework team | PR + engineering lead review |

### Validation Gates (Before Merge)

1. **Stage 1** (`.\tooling\run_stage1_checks.ps1`) — Must pass; enforces:
   - YAML syntax validity
   - All KPI references exist
   - Use case IDs are unique
   - Action code IDs follow naming scheme

2. **Health Scorecard** (`python tooling/health_scorecard.py`) — Advisory; shows:
   - H1: Golden Thread coverage (%)
   - H2: Semantic Model stability
   - H3: Data contract coverage
   - H4: Action code completeness
   - H5: Factsheet quality

3. **Schema Validation** (`npm ci && npm run validate`) — Must pass; enforces:
   - JSON schema conformance (brackets, KPIs, action codes)
   - Type safety (TypeScript in Studio)

---

## 10. Continuity & Escrow Activation

If vendor engagement ends:

1. **Verify system is alive:** `python3 tooling/ontology/registry_builder.py --repo-root . --strict` (should exit 0)
2. **Inspect critical files:** Ensure all files in Section 5 exist and are not corrupted
3. **Run full validation:** `.\tooling\run_all_checks.ps1` (Windows) or `python3 -m pytest tooling/tests/ -q` (Linux)
4. **Clone + regenerate:** Follow Section 7 (Regeneration Contract) to ensure a fresh build works
5. **Deploy to Fabric:** Follow Runbook Section (c) to verify Fabric integration

All documentation, schemas, and code are in the repo. No external dependencies.

---

## Appendix: Glossary

- **SSOT:** Single Source of Truth (KPI Catalog, Action Codes)
- **IR:** Intermediate Representation (JSON format between YAML and tool-specific output)
- **TMDL:** Tabular Model Definition Language (semantic model YAML for Power BI)
- **PBIP:** Power BI Item Package (JSON export format, Git-friendly)
- **Golden Thread:** Traceability from Strategy → KPI → Use Case → Measure → Action
- **Bracket:** Use case YAML definition (`UseCase_Bracket.yaml`)
- **Factsheet:** Business documentation of a use case (`Business_Factsheet.md`)
- **Data Contract:** Formal agreement on table grain, column lineage, refresh cadence
