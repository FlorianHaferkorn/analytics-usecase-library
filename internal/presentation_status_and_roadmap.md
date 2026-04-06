# Presentation Status and Roadmap

**Purpose:** Single source for internal presentations and stakeholder updates — current status, metrics, roadmap, product maturity, tooling, and Aurora proof in one document.

**Language:** English. This document is maintained in English only. When recreating or doing major updates, keep it in English.

**Last updated:** 2026-02-22  
**Next planned update:** Before next presentation or quarterly

---

## Summary (for presentations)

The framework is in production: the Golden Thread (Strategy → KPIs → Use Cases → Action Codes) is end-to-end, with 14 use cases, 107 KPIs, and 53 action codes. Customers can already implement decision-oriented use cases from the specs and Aurora as reference, generate measures and report structure, and keep everything consistent via Stage 1 and the Registry Gate. Delivery is supported by project tooling and short assistant briefings focused on priorities and blockers. Still open: the full 300-second page in the report and Strategy Pattern / AI urgency (backlog).

---

## 1. Metrics (framework scope)

| Artefact | Count | Source for updates |
|----------|-------|--------------------|
| Use Cases | 14 | [core/usecases/UseCase_Inventory.md](../core/usecases/UseCase_Inventory.md) (rows with \| COM- \| FIN- \| OPS- \| SCM- \| XD-) |
| KPIs | 107 | [core/kpi_catalog/KPI_Catalog.md](../core/kpi_catalog/KPI_Catalog.md) (occurrences of `kpi_id:`) |
| Action Codes | 53 | [core/action_codes/](../core/action_codes/) — all `*.yaml` except under `decision_spines/` |
| Decision Spines | 12 | [core/action_codes/decision_spines/](../core/action_codes/decision_spines/) |

---

## 2. Current status (functional)

The following applies when **Stage 1 is green** (CI gate: `.\tooling\run_stage1_checks.ps1`). Technical status = Stage 1 passed.

### What we have from the target picture today

- **End-to-end chain:** From strategy to concrete action: Strategy → KPIs → Use Cases → Action Codes. Each use case answers a clear business question, references only KPIs from the catalog, and links to concrete action options (action codes).
- **Concrete outputs:** Use case inventory; per use case: clear decision question plus machine-readable config (bracket). From this we generate measures (TMDL/DAX) and report scaffolds. Action codes with escalation levels (L1–L3); text usable in Power BI (action payload).
- **Single KPI catalog:** One business definition per KPI with owner/steward; use cases and action codes only reference these definitions.
- **Quality and trust:** No use case without valid KPI and action references (Stage 1). Registry keeps the Golden Thread consistent. When a data contract is broken, dependent KPIs can be marked as "untrusted" in the report.

### What we can already produce

- Use case inventory, KPI and action library, generated measures/report scaffolds; 3-second and 30-second layers in the report are in place.
- Per–use case documentation (question, context, KPIs, actions).

### What is still open (functional)

- **3–30–300 complete:** The principle is defined. The **300s layer layout** is now defined in [core/templates/page_templates/layout_330300_300s_layer.md](../core/templates/page_templates/layout_330300_300s_layer.md) and schema `layout_330300.schema.json`. Still to implement: full generation of action text and evidence table from action-code YAML in the report.
- **Strategy Pattern / AI urgency:** Strategy pattern document exists; automatic urgency derivation and automated reasoning are target/backlog. Scope and limits of automated reasoning are documented in [internal/vision/automated_reasoning_scope_and_limits.md](vision/automated_reasoning_scope_and_limits.md).
- **Strategic layer (optional):** The link Strategy → KPIs → Use Cases works; company_strategy has canonical anchors (§5, §6, §7) and references.
- **Technical open items:** Technical TODOs and stubs (MCP, Fabric API, synthetic data, scaffold) are listed in [internal/technical_backlog.md](technical_backlog.md). **Aurora Operations:** [products/fabric/powerbi/blueprints/Operations.yaml](../products/fabric/powerbi/blueprints/Operations.yaml) has relationships and display_folders (measures) defined; DAX in KPI Catalog for OPS-001/002/003 still to be added.

---

## 3. Tooling and gates

| Component | Purpose | Details |
|-----------|----------|---------|
| **Registry Gate** | Referential integrity and consistent Golden Thread. No merge on failure. | Checks: all KPI and action-code references exist; detects orphans (ghosts), governance gaps, logical breaks. Run: `py tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict`; included in Stage 1. See [tooling/README.md](../tooling/README.md). |
| **Semantic models & UX** | Best practices for TMDL, DAX, 3-30-300, accessibility. | [products/fabric/powerbi/docs/tmdl_best_practices.md](../products/fabric/powerbi/docs/tmdl_best_practices.md), [fabric/powerbi.md](../products/fabric/powerbi/docs/fabric_powerbi.md) §11. |
| **Report documentation generator** | Standardised report documentation (Markdown) from PBIP and use-case factsheets. | Traceability: metadata, business questions, KPIs, per page. Usable when PBIP and factsheets exist. Spec: [report_documentation_generator_spec.md](../products/fabric/powerbi/tooling/report_documentation_generator_spec.md). |
| **Theme generator** | Power BI themes (JSON) from colour/concept; WCAG and CVD checks. | [products/fabric/powerbi/docs/fabric_powerbi.md](../products/fabric/powerbi/docs/fabric_powerbi.md) §9.4; apply to reports e.g. via `apply_report_theme.py`. |
| **Fabric architecture (code-based)** | Git as source of truth; workspace strategy (DE_/DM_/BI_); deployment pipelines; Stage 1 + Registry before deploy. | [products/fabric/powerbi/docs/fabric_architecture_best_practices.md](../products/fabric/powerbi/docs/fabric_architecture_best_practices.md), [products/fabric/powerbi/deployment/README.md](../products/fabric/powerbi/deployment/README.md). |

---

## 4. Roadmap

### Project completion (definition)

The project is considered substantively and technically complete with **blocker resolution**, **review adjustments**, and **zero-tolerance documentation** (items 1–3 of the project completion plan). Source: [internal/vision/phase2_backlog.md](vision/phase2_backlog.md).

### Project completion status (items 1–3)

- **Done:** Blocker resolution (company_strategy anchors and factsheet paths per [internal/core_content_review_results.md](core_content_review_results.md); anchors and paths verified/fixed).
- **Done:** Remaining review adjustments (style, link-backs, encoding) per content review (Issue #17).
- **Done:** CI/release without Stage-1 skip documented in [docs/README.md](../docs/README.md) § Quality gates.

### Phase 2 / Backlog (after completion)

- **3-30-300 complete:** 300s page with action text and evidence from action-code YAML end-to-end in the report.
- **Strategy Pattern / AI urgency:** Precision for automated reasoning; conceptually present, not proven in tooling.

Details: [internal/vision/phase2_backlog.md](vision/phase2_backlog.md).

### Operational (ongoing)

- Log Stage 1 incidents and skill usage; weekly snapshot; monthly retrospective. See [internal/metrics/README.md](metrics/README.md).

---

## 5. Project management and delivery

Delivery is driven by the **GitHub Project** (SSOT for status) and agent-supported workflow so that manual steps are minimised.

### Status flow and automation

| Status | Meaning | Automation |
|--------|--------|------------|
| **Backlog** / **Planned** | Not started / scheduled | New items default to Backlog. |
| **In progress** | Work in progress (Implementer agent) | Set via `start_next_task.ps1` (picks next by priority, moves one item). |
| **In review** | PR open | Project workflow: when a PR is linked to an issue → Status = In review. |
| **Done** | PR merged | Project workflow: when linked PR is merged → Status = Done. |

- **Scripts** (repo root): `.\tooling\project_mgmt\start_next_task.ps1` (pick next task, set In progress, output issue # and expert); `.\tooling\project_mgmt\set_issue_status.ps1 -Issue N -Status "…"`; `.\tooling\project_mgmt\refresh_project_snapshot.ps1` (writes PROJECT_SNAPSHOT.md for the Assistant, no status change).

### Assistant Agent and daily briefing

- **Assistant Agent** ([.cursor/rules/assistant-agent.mdc](../.cursor/rules/assistant-agent.mdc)): On request ("Daily Briefing", "Briefing", "Was steht an?") reads [internal/presentation_status_and_roadmap.md](presentation_status_and_roadmap.md) and [internal/technical_backlog.md](technical_backlog.md), and produces a short briefing with focus, bottlenecks, and a recommended next task.
- **Minimal manual steps:** (1) Optionally refresh snapshot, then ask the Assistant for a daily briefing. (2) When starting work: run the script and tell the Implementer the issue number. (3) Review PR (using the summary comment) and merge. Everything else (status transitions, PR summary) is automated.

References: [tooling/project_mgmt/README.md](../tooling/project_mgmt/README.md), [docs/agent/rules/assistant-agent.md](../docs/agent/rules/assistant-agent.md).

---

## 6. Product maturity

| Product | Process status | Customer-ready (Aurora proof) | Still to develop | Planned |
|---------|----------------|------------------------------|------------------|---------|
| **Framework (Core)** | In production | Yes | — | Phase 2 backlog (3-30-300 complete, AI urgency) |
| **Fabric / Power BI** | In production | Yes (Aurora) | Stabilise report-doc generator; 300s page | Refine theme/scaffold |
| **Aurora Showcase** | Proof point | Reference for customers | Expand report pages for FIN/OPS/SCM | More use cases (OPS-002/003, SCM-002/003, XD) |
| **Proposal Costing** | Implemented | Yes (CLI, scenarios, TCO) | — | Optional: proposal-workflow integration |
| **Fabric Orchestrator V2** | Implemented | Yes (workspaces, pipelines) | Optional: dbt/notebook templates | Document V1/V2 split |

### What Aurora concretely proves

- **Open PBIP:** Open a domain semantic model (e.g. `showcases/aurora_group/semantic_models/Commercial.SemanticModel`) or a generated report in Power BI Desktop; report and semantic model load together.
- **Report loads:** Report with scaffolded pages (e.g. COM-001 Overview/Detail) in PBIR format under `products/fabric/powerbi/dist/<UC>.Report`; visuals use the domain semantic model.
- **Measures:** One _Measures.tmdl with all measures, displayFolder per use case (COM-001 to COM-004, OPS-001, SCM-001, FIN-001 etc.); generated from KPI catalog.
- **3-30-300 layouts:** Overview/Insights/Explorer follow [core/templates/page_templates/](../core/templates/page_templates/) and [products/fabric/powerbi/docs/reporting/pbip_layouts.md](../products/fabric/powerbi/docs/reporting/pbip_layouts.md).
- **RLS:** Aurora Organization Access; gold data under `showcases/aurora_group/data/gold/`.

Reference: [showcases/aurora_group/README.md](../showcases/aurora_group/README.md).

---

## 7. How to keep this document current

### Metrics

- **Use cases:** Row count in [core/usecases/UseCase_Inventory.md](../core/usecases/UseCase_Inventory.md) (table from line 8) or number of entries.
- **KPIs:** Count of `kpi_id:` in [core/kpi_catalog/KPI_Catalog.md](../core/kpi_catalog/KPI_Catalog.md).
- **Action codes:** Count of `*.yaml` under [core/action_codes/](../core/action_codes/) excluding `decision_spines/`.
- **Decision spines:** Number of files under [core/action_codes/decision_spines/](../core/action_codes/decision_spines/).

### Status and product maturity

- Review when framework or tooling changes significantly; optionally align with [internal/docs_claims_checklist.md](docs_claims_checklist.md) and [internal/vision/phase2_backlog.md](vision/phase2_backlog.md).
- Update table and short prose on release or when Aurora/products change.

### Update triggers

- **Metrics:** New use case, new KPI, new action code.
- **Maturity:** Aurora or product release, new showcase scope.
- **Project management:** Changes to task orchestration scripts or assistant briefing rules.
- **General:** Before internal presentation; optionally before release candidate.

### Recommended frequency

- Review before each use for a presentation; at least quarterly or before release candidate.

### Optional

- Assign and document responsibility (role/name) here.
