# Fabric / Power BI Architecture — Best Practices

**Purpose:** A single, easy-to-set-up and maintain Fabric/Power BI architecture that fits the ActionReady framework (use cases, KPI catalog, semantic model, validation) and aligns with industry best practices for CI/CD, workspace strategy, and governance.

**Scope:** Workspace layout, repo and Git strategy, CI/CD pipeline design, governance boundaries. Implementation details (TMDL, measures, RLS) remain in `fabric/powerbi.md` and `tmdl_best_practices.md`.

---

## 1. Principles

| Principle | Implication |
|-----------|-------------|
| **Framework-first** | Strategy → KPIs → use cases → action codes → semantic model → reports. Fabric is the implementation adapter; framework artifacts in `core/` are the source of truth. |
| **Easy to set up** | Parameterized, environment-aware setup (dev/tst/prd). Minimal manual steps; automation where it reduces human error. |
| **Easy to maintain** | Clear ownership (see operating model RACI). Validation gates (Stage 1 + Fabric checks) catch drift before merge. Single place for workspace and pipeline definitions. |
| **Git as source of truth** | PBIP (TMDL, report) and pipeline definitions live in Git. Fabric service state is derived from repo + deployment runs. |

---

## 2. Workspace Strategy

### 2.1 Framework-Aligned Workspace Layout

The implementation guide already recommends a workspace split by function. This architecture standardizes naming and purpose:

| Workspace prefix | Purpose | Typical contents |
|------------------|---------|------------------|
| **DE_** (Data Engineering) | Ingestion, lakehouse, dataflows | DE_Lakehouse, DE_Dataflows, DE_Sources |
| **DM_** (Data Models) | Semantic models, core and domain datasets | DM_Core, DM_Domains, DM_ActionReady |
| **BI_** (Reporting) | Reports, apps, experiments | BI_Apps, BI_Reports, BI_Experiments |
| **Shared_** | Reusable assets | Shared_Datasets, Shared_Parameters, Shared_Tools |

**Per-environment naming:** `{Prefix}_{Name} [{env}]` e.g. `DE_Lakehouse [dev]`, `DM_Core [tst]`, `BI_Apps [prd]`. Capacity and permissions are environment-specific.

### 2.2 Optional: Layer-Based Mapping (FabricAutomation-style)

If you adopt automation that deploys by “layer” (e.g. Fabric CLI + JSON env files), map framework workspaces to layers as follows:

| Layer | Git directory (example) | Maps to framework |
|-------|-------------------------|-------------------|
| Core | `solution/core` | Metadata DB / config (optional) |
| Store | `solution/store` | Lakehouse (gold/silver); DE_ |
| Ingest | `solution/ingest` | Pipelines/sources; DE_ |
| Prepare | `solution/prepare` | Notebooks / prep; DE_ |
| Orchestrate | `solution/orchestrate` | Orchestration; DE_ |
| Model | `solution/model` | Semantic models (PBIP); DM_ |
| Present | `solution/present` | Reports / apps; BI_ |

Use one convention consistently: either **workspace-per-function** (DE_/DM_/BI_) or **workspace-per-layer** (Core, Store, …). This repo’s guide and validation assume the DE_/DM_/BI_/Shared naming; automation can still drive creation from a layer-based JSON if you map layer → workspace name.

### 2.3 Workspace Strategy for Data Engineering (W23-style)

- **One workspace per concern** (e.g. one for lakehouse, one for pipelines) to simplify permissions and deployment.
- **Clear promotion path:** DEV → TEST → PROD; no mixing of environment data in one workspace.
- **Identity and connections:** Use workspace identity where needed; centralise connection definitions and assign to workspaces via automation to avoid duplication.

### 2.4 Fabric Deployment Patterns (Microsoft Learn)

Fabric has four hierarchical levels: **tenant → capacity → workspace → item**. Choose a deployment pattern based on scale, governance, and isolation needs:

| Pattern | When to use | Trade-offs |
|--------|-------------|------------|
| **1. Monolithic** | Single workspace for all use cases; small user base; single region; no Git/deployment pipelines needed. | No deployment pipelines; no workspace-scoped Git; all items share one capacity; variable job times. |
| **2. Multiple workspaces, single capacity** | Hub-and-spoke; separate workspaces per team/layer (e.g. bronze/silver/gold); DTAP with multiple workspaces; no strict performance SLAs. | Shared capacity; throttling possible at peak. |
| **3. Multiple workspaces, separate capacities** | Data mesh; multi-region; strict SLAs; chargeback per team; scale beyond one capacity. | Higher cost; more admin. Use **Fabric domains** to group workspaces per business unit; **OneLake data hub** for discovery. |
| **4. Multiple tenants** | Acquisitions; legally separate subsidiaries. | Full segregation; data sharing only via pipelines or data engineering. |

**Recommendation for this framework:** Pattern 2 or 3 — multiple workspaces (DE_/DM_/BI_) with deployment pipelines and Git; single capacity for small orgs, separate capacities when you need performance isolation or chargeback.

### 2.5 Domains and OneLake Data Hub

- **Fabric domains:** Group workspaces belonging to the same business unit; delegate some tenant-level settings to domain admins. Use when multiple workspaces span one domain (e.g. Commercial, Finance).
- **OneLake data hub:** Central discovery for Fabric items; integrates with Teams/Excel. Use for cross-workspace discovery and certification.
- **OneSecurity:** Configure data security policies at scale; use with workspace roles and item-level permissions.

---

## 3. Repository and Git Strategy

### 3.1 What Lives Where (This Repo)

| Location | Content | Deployed to Fabric |
|----------|---------|--------------------|
| `core/` | Use cases, KPI catalog, action codes, data contracts, templates | No (spec only) |
| `products/fabric/powerbi/` | Guide, validation, tools, **dist** (generated TMDL per use case) | dist or customer copy |
| `showcases/aurora_group/` | Domain semantic models (Commercial, Finance, etc.), gold data, reports | Optional; proof of framework |

**Golden rule:** Use cases and reports **reference** governed definitions; they do **not** define KPI meaning or action logic. Single source of truth for KPIs is `core/kpi_catalog/`; for semantic output it is generated TMDL and PBIP in `dist/` or showcase.

### 3.2 Branch Strategy (Best Practice for CI/CD and Collaboration)

- **main** — Protected; all changes via PR. Stage 1 + Fabric checks must pass before merge.
- **feature/*** — Short-lived; for development. Optional: trigger feature-workspace creation in Fabric (see FabricAutomation feature_fabric_branch pattern).
- **releases/release*** — Promotion to tst/prd. Triggers multi-stage release (e.g. build → release tst → release prd) when using automation.

No direct commits to main; no long-lived branches that bypass validation.

### 3.3 PBIP and Git Integration

- Semantic models and reports are developed as **PBIP** (TMDL + report folder) in Git.
- Connect Fabric workspaces (e.g. DM_Core, BI_Reports) to the repo via **Git integration** (GitHub or Azure Repos); one connection per tenant/environment, scoped to the right repos and branches.
- Deployment pipelines (Fabric’s built-in or CI/CD) deploy from Git; Fabric does not become the source of truth for definition content.

---

### 3.4 Content Preparation (Microsoft Learn)

- **Separate development between teams:** Different teams can have separate workspaces, different repos, and different release cadence. Items can still connect across workspaces, so collaboration on the same data is possible.
- **Plan permission model:** Decide who has access to source code (Git), who can deploy to each pipeline stage (dev/test/prod), who reviews test, who deploys to production, and which branch each workspace connects to. Restrict production deploy to a small set; give production workspace Viewer to most users.
- **Connect different stages to different databases:** Do not point dev/test semantic models at production databases. Use separate dev/test databases to protect production and avoid overloading dev with full prod volume.
- **Use parameters for config that changes between stages:** Add parameters for connections, internal item references, query filters, and user-facing text. Use deployment rules (or `parameter.yml` with fabric-cicd) to set different values per stage.

### 3.5 Development Workflow (Back up, Rollback, Isolation)

- **Back up to Git:** Work in an isolated environment (Desktop/VS Code or a private workspace); commit to a branch only you use; commit related changes together; avoid huge commits (report size limits).
- **Rollback:** Use Undo for uncommitted changes; for committed changes use `git revert` or `git reset` and then sync workspace. Reverting data items (e.g. Lakehouse) can break existing data — validate before reverting.
- **Private workspace:** Use a workspace connected to your feature branch as a "working directory"; switch the same workspace to a new branch when starting a new task. Developers using Desktop/VS Code can work without a workspace until they need to test in service.
- **Client tools:** Use Power BI Desktop for semantic models/reports, VS Code for notebooks; push to remote and sync workspace. Ensure item structure matches [Git source code format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format).

---

## 4. CI/CD Pipeline Design

### 4.1 Mandatory Gates (This Repo)

Run from **repository root**:

1. **Stage 1 (hard gate):**  
   `.\tooling\run_stage1_checks.ps1`  
   Validates factsheets, KPI catalog, action codes, UseCase_ActionCode_Map, duplicate IDs, SSOT, docs.

2. **Fabric checks (when touching Fabric/Power BI output):**  
   `.\products\fabric/powerbi\tooling\run_fabric_checks.ps1`  
   TMDL syntax, PBIP readiness, measures vs KPI catalog, TMDL vs measure dictionary, DAX best practices.

**Recommendation:** Run Stage 1 on every PR targeting main. Run Fabric checks on every PR that changes `core/kpi_catalog/`, `core/semantic_models/`, `products/fabric/powerbi/dist/`, or Aurora showcase semantic models under `products/fabric/showcases/aurora_group/semantic_models/`.

### 4.2 Optional: Environment Setup and Release (FabricAutomation Pattern)

To make Fabric **easy to set up and tear down** in a repeatable way:

- **Setup (one-time or per env):**  
  - Input: environment (dev/tst/prd), tenant/client/secret, optional Git PAT.  
  - Actions: Authenticate (e.g. Fabric CLI), create workspaces from parameterised definition, create connections, configure Git integration, assign permissions.  
  - Implement via scripts (e.g. Python + Fabric CLI) and env-specific JSON (e.g. `infrastructure.json` + `infrastructure.dev.json`).  

- **Release (per deployment):**  
  - Input: environment, repo path, optional layer/item-type filter.  
  - Actions: Publish items from Git (Notebook, Lakehouse, Semantic Model, etc.) into the right workspace; optionally unpublish orphans.  
  - Keep release idempotent and environment-aware.

**Placement:** Such automation can live in `products/fabric/powerbi/deployment/` (or a separate automation repo that references this repo). Prefer reusing or adapting the [FabricAutomation](https://github.com/peerinsights/FabricAutomation) patterns (solution_setup, solution_release_multistages, parameter files) rather than reinventing.

### 4.3 Parameterization (Environment-Specific Config)

When using fabric-cicd or similar automation, put a **`parameter.yml`** in the root of the repository directory (per workspace/layer). Use it to replace environment-specific values at deploy time:

- **find_replace:** Replace connection IDs, lakehouse IDs, workspace IDs in notebooks, pipelines, reports. Optional filters: `item_type`, `item_name`, `file_path`; use `is_regex: true` for regex patterns. Use dynamic variables: `$workspace.$id`, `$items.<ItemType>.<ItemName>.$id` (and `.$sqlendpoint`, `.$sqlendpointid` for Lakehouse) so IDs are resolved at deploy time.
- **key_value_replace:** Replace values in JSON/YAML via JSONPath (e.g. pipeline connection, schedule `enabled` per env).
- **spark_pool:** Map dev Spark pool instance ID to environment-specific pool type and name (Capacity or Workspace).
- **semantic_model_binding:** Bind semantic models to the correct connection after deploy (cloud/on-prem).

See [fabric-cicd parameterization](https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/). Deployment pipelines (Fabric UI) use [deployment rules](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/create-rules) for data sources and parameters instead of `parameter.yml`.

### 4.4 Test and Production Best Practices (Microsoft Learn)

**Test stage:**

- **Simulate production:** Test stage should mirror prod in data volume, usage volume, and similar capacity (use a separate capacity for load testing to avoid impacting prod).
- **Deployment rules with real-life data:** Use data source rules (or parameterization) to point test semantic models at test databases, not dev.
- **Check related items:** Use lineage/impact analysis to verify changes do not break dependent items.
- **Data items:** When updating Lakehouse/warehouse definitions, test in dev then in a staging env with real-life-like data before prod; plan timing and recovery for breaking changes.
- **Test the app:** Publish/update the app in the test stage and validate from an end-user perspective. Deployment does not update app content/settings — update the app manually in each stage or via [deployment pipelines API](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation).

**Production stage:**

- **Manage who can deploy:** Restrict production deploy to a small set; give others production workspace Viewer only. Limit repo and pipeline access to content creators.
- **Set rules for availability:** Configure production deployment rules for data sources and parameters so deployments run without disturbing users.
- **Update the production app:** Deployment (UI) updates workspace content only. To update the app after deploy, use the deployment pipelines API; it is not possible via the UI.
- **Quick fixes:** Always implement fixes in dev, then promote through test to prod. Do not deploy untested fixes directly to production.

### 4.5 Pipeline Stages (Conceptual)

| Stage | Trigger | Actions |
|-------|---------|---------|
| **Validate** | PR to main | Stage 1 + Fabric checks (and schema validation if configured). |
| **Build** | Merge to main or release branch | Build parameter files, build artifacts (e.g. dacpac if used), upload artifacts. |
| **Release DEV** | Merge to main (or manual) | Deploy to dev workspace(s). |
| **Release TEST** | Release branch or manual | Deploy to tst workspace(s). |
| **Release PROD** | After TEST, manual or release branch | Deploy to prd workspace(s); then update app via API if needed. |

Multi-stage release (tst → prd) should require explicit promotion; avoid auto-deploy to production.

---

## 5. Governance and Security

- **Manage, govern, protect:** Classify data and apply RLS/OLS from the semantic model (dimension-based RLS; OLS for sensitive columns). Use workspace and item-level permissions aligned with the operating model (e.g. Viewer, Analyst, Admin, Data Steward).
- **Workspace roles (Microsoft Learn):** Admin, Member, Contributor, Viewer — each with different capabilities for managing access and data. Plan who gets which role per workspace and stage.
- **Item permissions:** Read (metadata), ReadData (SQL endpoint), ReadAll (OneLake data). Use for granular access to specific items within a workspace.
- **Compute permissions:** Configure via SQL Endpoints and semantic models (table/row-level security). Use for data-plane isolation.
- **Connections:** Create and assign Fabric connections (e.g. Data Pipeline, SQL) via automation; assign to workspaces and principals via role assignments. Avoid hardcoded credentials; use service principal or managed identity for automation.
- **OneSecurity:** Use for data security policies at scale; integrate with workspace and item-level permissions.
- **Descriptions and lineage:** Every measure and key table/column has descriptions (e.g. TMDL `///` comments) for Copilot and governance. KPI Catalog and measure dictionary remain the authority for meaning. Use [impact analysis](https://learn.microsoft.com/en-us/fabric/governance/lineage) to trace dependencies before changes.

---

## 6. Adoption Paths

| Path | Scope | Effort |
|------|--------|--------|
| **Minimal** | Use `fabric/powerbi.md` + `tmdl_best_practices.md`; run Stage 1 + Fabric checks locally or in CI. No Fabric automation. | Low; fits teams that deploy manually. |
| **Standard** | Add Git integration for PBIP; use Fabric deployment pipelines (DEV → TEST → PROD) with manual promotion. Keep validation gates in CI. | Medium. |
| **Full** | Add parameterised setup and release (FabricAutomation-style): env JSON, Fabric CLI, setup + release workflows. Feature branches optionally create feature workspaces. | Higher; best for multiple envs and many contributors. |

Start with **Minimal** or **Standard**; introduce **Full** when you need repeatable env creation and release automation across many workspaces.

---

## 7. Setup Plan: From Scratch, Adjust, Scale

A phased plan to create this architecture from scratch, adjust it to your org, and scale it without big-bang rewrites.

### Phase 1 — Foundation (create from scratch)

| Step | Action | Outcome |
|------|--------|---------|
| 1.1 | **Tenant and capacity:** Ensure Fabric capacity (or Power BI Premium); enable tenant switches: "Users can create Fabric items", "Users can synchronize workspace items with their Git repositories". | Fabric ready for Git and deployment pipelines. |
| 1.2 | **Choose deployment pattern:** Decide monolithic vs multiple workspaces (recommended: Pattern 2 or 3). Define workspace naming: `{Prefix}_{Name} [{env}]` (e.g. DE_Lakehouse [dev], DM_Core [tst], BI_Apps [prd]). | Clear workspace strategy. |
| 1.3 | **Create workspaces (manual or script):** One set per environment (dev/tst/prd) — e.g. DE_*, DM_*, BI_*, Shared_*. Assign capacity; set Admin/Member/Contributor/Viewer per role. | Workspaces exist; no content yet. |
| 1.4 | **Repo and branch policy:** Create or adopt repo; protect main; require PRs. Branch strategy: main, feature/*, optional releases/release*. | Git as source of truth; no direct commits to main. |
| 1.5 | **Framework alignment (this repo):** Clone or fork analytics-usecase-library; run Stage 1 and Fabric checks from repo root. Ensure `core/` (KPI catalog, use cases, action codes) is the spec; `products/fabric/powerbi/dist/` or showcase is the Fabric output. | Validation gates in place; framework golden thread respected. |

**Exit criteria:** Workspaces exist; repo has branch policy; Stage 1 + Fabric checks run and pass (or are configured in CI).

### Phase 2 — Connect and deploy (adjust to your org)

| Step | Action | Outcome |
|------|--------|---------|
| 2.1 | **Git integration:** Connect each relevant workspace (e.g. DM_Core [dev], BI_Reports [dev]) to the repo; map to branch (e.g. main for dev). Create Fabric Git connection (GitHub or Azure Repos); assign permissions. | Workspaces sync with Git; PBIP/TMDL in repo. |
| 2.2 | **Deployment pipeline (Fabric UI):** Create a pipeline with Dev / Test / Production stages. Assign dev workspace to Dev, tst to Test, prd to Production. Configure deployment rules for data sources and parameters so each stage points to the right DBs and connections. | Promotion path dev → test → prod without manual copy-paste. |
| 2.3 | **Permission model:** Document and apply who can: edit in Git, deploy to each stage, view production. Restrict production deploy; give production Viewer to most users. | Clear RACI for deploy and access. |
| 2.4 | **Parameters and rules:** Add parameters to semantic models/pipelines for anything that changes per env (connections, server names, etc.). Use deployment rules (Fabric UI) or `parameter.yml` (fabric-cicd) so dev/tst/prd get correct values. | No manual reconfiguration when promoting. |
| 2.5 | **CI validation:** Run Stage 1 and Fabric checks on every PR to main (e.g. GitHub Actions or Azure Pipelines). Fail the PR if checks fail. | Drift and violations caught before merge. |

**Exit criteria:** Git connected; deployment pipeline promotes content; parameters/rules set; CI runs Stage 1 + Fabric checks.

### Phase 3 — Automate and scale (scale)

| Step | Action | Outcome |
|------|--------|---------|
| 3.1 | **Setup automation (optional):** If you need to recreate or clone environments, add setup scripts (e.g. Fabric CLI + Python) and env JSON (e.g. `infrastructure.json`, `infrastructure.dev.json`). Create workspaces, connections, Git connection, role assignments from code. Place in `products/fabric/powerbi/deployment/` or a dedicated automation repo. | Idempotent, parameterized env creation. |
| 3.2 | **Release automation (optional):** Use fabric-cicd or FabricAutomation-style release script to publish items from repo to workspace(s) by env; optionally unpublish orphans. Trigger from CI (e.g. on merge to main for dev; on release branch for tst/prd). | Repeatable deploy from Git without manual "Deploy" in UI. |
| 3.3 | **Feature branches (optional):** If many developers work in parallel, consider feature-workspace creation on feature/* branch creation (FabricAutomation pattern); tear down on branch delete. | Isolated dev per feature without crowding shared dev workspace. |
| 3.4 | **Domains and data hub (scale):** As workspace count grows, group workspaces into Fabric domains (e.g. Commercial, Finance). Use OneLake data hub for discovery and certification. | Federated governance; single place to find and govern assets. |
| 3.5 | **Capacity and performance (scale):** If specific workloads need guaranteed performance, move them to dedicated capacities (Pattern 3). Use separate capacities for load testing so prod is not affected. | SLA and chargeback possible. |

**Exit criteria:** Setup and release are scripted (if chosen); feature branches supported (if chosen); domains/data hub in use at scale; capacity strategy clear.

### Checklist: Am I ready to scale?

- [ ] Workspace naming and deployment pattern are consistent and documented.
- [ ] Git integration and deployment pipeline are in place; parameters/rules prevent manual reconfig.
- [ ] Stage 1 + Fabric checks run in CI on every PR to main.
- [ ] Permission model is defined (who deploys, who has Viewer, who has Git access).
- [ ] Production deploy is restricted; app update after deploy is done (e.g. via API) if you use apps.
- [ ] (Optional) Setup and release are automated; feature workspaces available if needed.
- [ ] (At scale) Domains and OneLake data hub are used; capacity strategy is clear.

---

## 8. References

- **This implementation:** `products/fabric/powerbi/docs/fabric/powerbi.md`, `tmdl_best_practices.md`, `deployment/README.md`.
- **Framework:** `core/strategy_operating_model/`, `AGENTS.md`, `docs/agent/rules/stage1-awareness.md`.
- **Validation:** `tooling/run_stage1_checks.ps1`, `products/fabric/powerbi/tooling/run_fabric_checks.ps1`.
- **Microsoft Learn — Best practices for lifecycle management:** [Best practices for lifecycle management in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/best-practices-cicd) (content preparation, dev/test/prod, permissions, parameters, deployment rules, app update).
- **Microsoft Learn — Fabric deployment patterns:** [Microsoft Fabric deployment patterns](https://learn.microsoft.com/en-us/azure/architecture/analytics/architecture/fabric-deployment-patterns) (tenant/capacity/workspace/item; monolithic vs multiple workspaces vs multiple tenants; domains, OneLake data hub).
- **Microsoft Learn — Deployment pipelines:** [Introduction to deployment pipelines](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines), [Create deployment rules](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/create-rules), [Pipeline automation (API)](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation-fabric).
- **Microsoft Learn — Git integration:** [Git integration source code format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format), [Manage branches](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/manage-branches).
- **fabric-cicd (Python):** [fabric-cicd](https://microsoft.github.io/fabric-cicd/latest/) — publish items from repo to workspace; [parameterization](https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/) (find_replace, key_value_replace, spark_pool, semantic_model_binding; dynamic variables).
- **FabCon Europe 2025 – T26:** *Git Good - Best Practices for CI/CD and Collaboration in Microsoft Fabric* (PDF in FabricAutomation repo: `presentations/`).
- **FabCon Sep 25:** *Manage, Govern and Protect your data in Fabric* (governance and security context).
- **W23:** *Workspace Strategy for Data Engineering in Fabric* (Asgeir Gunnarsson) — workspace layout and separation of concerns.
- **FabricAutomation:** [FabricAutomation](https://github.com/peerinsights/FabricAutomation) — solution setup, release (single/multi-stage), feature branch workflows, Python scripts and env JSON; can be adapted for this framework.

---

**Location:** `products/fabric/powerbi/docs/fabric_architecture_best_practices.md`
