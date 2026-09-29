# Analytics Framework — Navigation Hub

New to the repo? Start with **[`ONBOARDING.md`](../ONBOARDING.md)** — pick Reader or Contributor track and follow it.

Want the architecture picture first? See **[`docs/architecture/README.md`](architecture/README.md)** — Golden Thread diagram, folder map, source vs. generated.

---

## Role-based entry points

### Explorer / New colleague (no technical background required)

You want to understand what this framework is, what it contains, and how it works.

| Start here | Purpose |
|---|---|
| [`ONBOARDING.md`](../ONBOARDING.md) — Reader track | 45-minute guided path, no installation needed |
| [`docs/reference/GLOSSARY.md`](reference/GLOSSARY.md) | Plain-language definitions of all terms and acronyms |
| [`core/usecases/UseCase_Inventory.md`](../core/usecases/UseCase_Inventory.md) | One-line overview of every use case in the framework |

After the Reader track you can answer: what is the Golden Thread, where are KPIs defined, and what is a use case.

---

### Business / Domain Lead

You define KPIs, own use cases, and drive decision-oriented analytics.

| Start here | Purpose |
|---|---|
| [`core/usecases/core/`](../core/usecases/core/) | Browse existing use cases by domain |
| [`core/kpi_catalog/golden_20.yaml`](../core/kpi_catalog/golden_20.yaml) | The 20 strategic KPIs that form the Golden Thread |
| [`core/action_codes/`](../core/action_codes/) | Action recommendations triggered by KPI deviations |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) → "Adding a new use case" | How to add your use case |

### Power BI Developer

You build and maintain semantic models and reports on Microsoft Fabric.

| Start here | Purpose |
|---|---|
| [`products/fabric/powerbi/README.md`](../products/fabric/powerbi/README.md) | Fabric entry point — folder structure, workflow, validation |
| [`products/fabric/powerbi/dist/`](../products/fabric/powerbi/dist/) | Generated semantic models and reports (read to understand output) |
| [`products/fabric/powerbi/orchestrator/`](../products/fabric/powerbi/orchestrator/) | Source scripts for generation and orchestration |
| [`products/fabric/powerbi/docs/`](../products/fabric/powerbi/docs/) | Fabric-specific architecture, TMDL conventions, PBIR structure |
| `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` | Fabric validation gate |

### Data Engineer

You build and own the data pipelines that feed Silver and Gold layers.

| Start here | Purpose |
|---|---|
| [`core/data_contracts/`](../core/data_contracts/) | Silver-layer schemas (domains and sources) |
| [`core/strategy_operating_model/operating_model/`](../core/strategy_operating_model/operating_model/) | Data layer standard (Silver-first model) |
| [`core/implementation_guides/playbook_strategy_to_first_report.md`](../core/implementation_guides/playbook_strategy_to_first_report.md) | Step 3: Silver contracts and semantic requirements |

### Consultant / Delivery Lead

You scope and facilitate an engagement, convert decisions into architecture, and lead a
verified implementation.

| Start here | Purpose |
|---|---|
| [`docs/architecture/research/discovery-to-deployment-workbench.md`](architecture/research/discovery-to-deployment-workbench.md) | Proposed scope-driven operating model from customer discovery to verified tenant state, including selectable Data Governance |
| [`core/implementation_guides/playbook_strategy_to_first_report.md`](../core/implementation_guides/playbook_strategy_to_first_report.md) | Concrete first-report delivery profile |
| [`docs/plans/PRODUCT_PLAN.md`](plans/PRODUCT_PLAN.md) | Product target, quality floors and build phases |
| [`docs/plans/_INDEX.md`](plans/_INDEX.md) | All plans, concepts and reviews (Superversion, report quality, layout system, agentic loop) — pick one document |

### Maintainer / Platform Engineer

You own CI, tooling, governance, and releases.

| Start here | Purpose |
|---|---|
| [`tooling/README.md`](../tooling/README.md) | Overview of all validators, generators, and automation |
| `.\tooling\run_stage1_checks.ps1` | Mandatory pre-merge gate |
| [`internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`](../internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) | Curated error knowledge base |
| [`internal/continuity/runbook.md`](../internal/continuity/runbook.md) | Release and maintenance runbook |

### AI Agent User (Cursor / Claude / Copilot)

You use AI tools to accelerate development inside this repo.

| Start here | Purpose |
|---|---|
| [`AGENTS.md`](../AGENTS.md) | Agent operating rules (all tools) |
| [`CLAUDE.md`](../CLAUDE.md) | Claude Code–specific rules and TMDL/DAX conventions |
| [`docs/agent/README.md`](agent/README.md) | Skills index — reusable agent workflows |
| [`docs/agent/skills/`](agent/skills/) | Individual skill files (add-usecase-scaffold, fix-stage1-failure, …) |

---

## Canonical reading path (any role, 60 min)

Follow [`ONBOARDING.md`](../ONBOARDING.md). It is structured to get you productive in one hour without reading this index end-to-end.

---

## Maintaining onboarding docs

Each doc has a defined role. Before adding new content, check [`docs/ONBOARDING_OWNERS.md`](ONBOARDING_OWNERS.md) to confirm where it belongs.

---

## Quality gates (run from repo root)

| Gate | Command | Required |
|---|---|---|
| Stage 1 (always) | `.\tooling\run_stage1_checks.ps1` | Before every merge |
| Fabric | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` | When changing Fabric output |
| OSS | `bash products/open_source_stack/tooling/run_oss_checks.sh` | When changing OSS stack |
| Full local | `.\tooling\run_all_checks.ps1` | Before release |
| Health scorecard | `python tooling/health_scorecard.py` | Recommended |
