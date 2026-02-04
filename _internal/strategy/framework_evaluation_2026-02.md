# Framework Evaluation Report (2026-02)

Evaluation of the Analytics Use Case Library against **ease of use** and **ease of implementation** to support improvement toward best-in-class BI framework adoption.

---

## 1. Evaluation dimensions and audiences

### Ease of use

How quickly the right person finds the right artifact and can trust it.

| Audience | Primary need | Success = |
|----------|--------------|------------|
| Executives / strategy | Link strategy to KPIs to outcomes | Single path: strategy doc to KPI list to use case value |
| Business / domain leads | Decision-oriented use cases and actions | Clear "what question / what action" per use case |
| Data & analytics teams | Build semantic models and reports from specs | One implementation path, templates + validation |
| New implementers (customer or delivery) | Adopt framework without deep dive | Documented "first 2 hours" path and single entry checklist |

### Ease of implementation

How few steps and decisions from "we adopt the framework" to "first use case is build-ready and validated."

| Dimension | What was assessed |
|-----------|-------------------|
| Onboarding path | One canonical "get started" sequence; prerequisites and first commands in one place |
| Implementation path | Strategy to pick use case to run tools to TMDL/report scaffold without hunting across READMEs |
| Tooling discoverability | Stage 1 vs "run all checks" vs generation scripts clearly distinguished and linked |
| Consistency | Paths, IDs, and script defaults match repo layout; key docs point to same commands and paths |
| Friction | Ambiguous decisions (e.g. which check script to run, which root to pass) |

---

## 2. Phase A: Document and tooling audit

### 2.1 Entry points mapped

| Document | Promises | Sends reader to |
|----------|----------|------------------|
| [README.md](../../README.md) | Strategy-to-action framework; get started in 3 steps | 1) docs/company (strategy, reporting principles), 2) docs/operating_model (overview, golden_thread), 3) usecases/core + UseCase_Inventory; then Stage 1 command + npm ci under validation. Does not link to implementations/microsoft_fabric_powerbi/guide, `_internal/tools/README`, or run_all_checks. |
| [framework/strategy_operating_model/README.md](../../framework/strategy_operating_model/README.md) | Single navigation entry; Golden Thread order | 1) docs/company, 2) docs/operating_model, 3) framework/, 4) usecases/data_contracts/semantic_models, 5) showcases/aurora_group. \"Run validation tools in `_internal/tools/validation/` before delivery\" — no script name. |
| [implementations/microsoft_fabric_powerbi/guide/README.md](../../implementations/microsoft_fabric_powerbi/guide/README.md) | Platform-specific implementation (Fabric/Power BI) | fabric_powerbi.md, tmdl_best_practices.md. \"Next Step: fabric_powerbi.md\". No link back to use case factsheets, KPI catalog path, or `_internal/tools`. |
| [showcases/aurora_group/README.md](../../showcases/aurora_group/README.md) | End-to-end demo with synthetic company | company/, data/, models/, usecases/, reporting/. \"How to use\": company profile, load data per data/sample_data/README.md, build model from models/core_action_ready_model.yaml, implement pages, align with usecases/core/. Does not say \"run X then Y to reproduce\"; no command to generate model or run checks. |

### 2.2 Single path test

From "I am new":

- **Strategy to use case:** README and docs/README give a clear sequence: company strategy and reporting principles, then operating model, then usecases/core and UseCase_Inventory. No dead end here.
- **Use case to implementation:** After "Explore the Core Use Cases", README does **not** link to implementation guides, generation scripts, or validation. A reader who wants to "implement" a use case has no next step in the main README.
- **Validation:** README mentions only Stage 1 (`run_stage1_checks.ps1`) and npm ci. usecase_DoD_Core.md and _internal/tools/README.md cite `run_all_checks.ps1`. No single place explains when to use which.

**Finding:** One recommended sequence exists for understanding (strategy to operating model to use cases). No single path is documented from "pick a use case" to "run generation and pass validation."

### 2.3 Check script clarity

| Source | Script cited | Context |
|--------|--------------|---------|
| README.md | `run_stage1_checks.ps1` | "Stage 1 CI Gate (local / CI)" |
| AGENTS.md | `run_stage1_checks.ps1` | "Before committing ... run Stage 1" |
| usecases/usecase_DoD_Core.md | `run_all_checks.ps1` | "Tooling & Automation DoD"; lists validate_factsheets, validate_kpi_catalog, check_factsheet_vs_kpi |
| _internal/tools/README.md | `run_all_checks.ps1` | "Master quality runner"; runs KPI validation, factsheet validation, KPI-use case checks, measure checks, PBIP, linters |

**Finding:** Stage 1 is the CI-mandated subset (fail-fast). run_all_checks is the broader local suite. No document states this distinction or links both from the main "How to get started" flow. New implementers may not know which to run when.

### 2.4 Prerequisites

- README mentions only: run from repo root; one-time `cd _internal\tools\validation` and `npm ci` for schema validation.
- **Missing in one place:** PowerShell (version), Node (for validation), Git clone, and that scripts must be run from repo root. No "Before you start" checklist.

---

## 3. Phase B: Consistency and correctness audit

### 3.1 Path and ID consistency

| Issue | Evidence | Impact |
|-------|----------|--------|
| new_usecase.ps1 cluster paths | [`_internal/tools/generation/new_usecase.ps1`](../../_internal/tools/generation/new_usecase.ps1): `Get-ClusterPath` returns `usecases/01_Commercial`, `usecases/02_Operational_Efficiency`, etc. Actual structure is `usecases/core/<ID>_<Name>`. Folders `01_Commercial`, `02_Operational_Efficiency` do not exist. | Script throws \"Cluster folder 'usecases/01_Commercial' not found\" for COM-*; unusable for scaffolding new use cases. |
| usecase_DoD_Core.md KPI template path | [`framework/usecases/usecase_DoD_Core.md`](../../framework/usecases/usecase_DoD_Core.md) section 2: `framework/templates/KPI_Catalog_templates/KPI_Catalog_SCHEMA.md`. Actual folder is `framework/templates/kpi_catalog_templates/` (lowercase `kpi_catalog`). | Broken link / wrong path for schema reference. |
| Action code documentation_links | Multiple action code YAMLs (e.g. [`framework/action_codes/SupplyChain/S-I1.1.yaml`](../../framework/action_codes/SupplyChain/S-I1.1.yaml)): `governance.documentation_links` use `usecases/core/SCM-001/Business_Factsheet.md`. Actual path is `usecases/core/SCM-001_Inventory_Performance/Business_Factsheet.md`. | Links resolve to wrong or missing path (folder name includes suffix). |
| SupplyChain action code filenames | ~~`S-F.3.1`–`S-F.3.3`~~ **Resolved:** Renamed to `S-F3.1`–`S-F3.3`; rationale references updated. Single convention: `S-F3.x.yaml`. | — |

### 3.2 UseCase_Inventory vs UseCase_ActionCode_Map

- **UseCase_Inventory.md** "Main Action Codes" column uses short codes: P2, P4, M3, D1, PC2, C1, W1, I1, W2, O2, L2, etc.
- **UseCase_ActionCode_Map.yaml** uses full IDs: C-M2.1, C-S1.1, C-S1.2, F-C1.1, O-O1.1, S-I1.1, etc.

**Finding:** The inventory table does not match the canonical map. Either the inventory uses a separate alias/legacy scheme (not documented) or it is drift. Readers cannot reliably go from inventory to map or vice versa.

### 3.3 VSCode tasks

- [`.vscode/tasks.json`](../../.vscode/tasks.json) exposes: \"Run all checks\" (run_all_checks.ps1), \"Generate measures for Use Case\", \"Generate all measures\", \"Generate all & run all checks\".
- **No task for `run_stage1_checks.ps1`.** README and AGENTS.md designate Stage 1 as the CI-mandated command; new users relying on tasks will not see it.

---

## 4. Phase C: Implementation path simulation

### 4.1 "Implement one use case" path (e.g. COM-001)

Trace from "I want to implement COM-001" to "TMDL generated and Stage 1 passed":

1. **Business Factsheet:** usecases/core/COM-001_Sales_Performance/Business_Factsheet.md — required KPIs, layout_330300, action code refs.
2. **Technical Factsheet:** usecases/core/COM-001_Sales_Performance/Technical_Factsheet.md — kpi_to_measure_mapping, data contract scope.
3. **KPI catalog:** framework/kpi_catalog/ — all required_kpis must exist here.
4. **Action code map:** usecases/UseCase_ActionCode_Map.yaml — COM-001 lists C-M2.1, C-S1.1, C-S1.2.
5. **Generation:** `.\_internal\tools\generation\generate_tmdl_measures.ps1 -UseCase COM-001 -UseCasesRoot framework/usecases -KpiCatalogRoot framework/kpi_catalog -DistRoot implementations/microsoft_fabric_powerbi/dist` (or DistRoot showcases/aurora_group/semantic_models for Aurora). Script defaults are framework/usecases, framework/kpi_catalog, implementations/microsoft_fabric_powerbi/dist when run from repo root.
6. **Validation:** `.\_internal\tools\run_stage1_checks.ps1` from repo root.

**Missing in docs:** No single page or checklist that lists this sequence. README "How to get started" stops at "Explore use cases"; it does not link to generation or implementations/microsoft_fabric_powerbi/guide. Implementation guide (fabric_powerbi.md) does not reference use case factsheets, KPI catalog path, or _internal/tools.

### 4.2 Aurora showcase

- [showcases/aurora_group/README.md](../../showcases/aurora_group/README.md): **Resolved.** Now points to `data/gold/` and framework data contracts; \"To reproduce\" steps added.
- [showcases/aurora_group/usecases/core/COM-001.md](../../showcases/aurora_group/usecases/core/COM-001.md): **Resolved.** Data reference updated to `showcases/aurora_group/data/gold/` (facts/dimensions).
- No "run X then Y to reproduce" instructions; no reference to generate_tmdl_measures.ps1 or run_stage1_checks.ps1.

### 4.3 Implementation guide links

- [implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md](../../implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md): Covers operating model to Fabric mapping, PBIP, measures, action codes, RLS/OLS. Does not link to usecases/, framework/kpi_catalog/, or `_internal/tools` (validation/generation). A delivery team reading only this guide cannot find factsheet or tooling entry points from the same doc.

---

## 5. Phase D: Synthesis

### 5.1 Strengths

- **Golden thread and SSOT**: Strategy to KPIs to use cases to action codes to templates is clearly articulated in docs and in repo structure. KPI catalog and action codes are the single source of truth; use cases reference them.
- **Stage 1 CI:** A well-defined fail-fast gate with a single command and a clear list of checks; run_stage1_checks.ps1 is documented in README and AGENTS.md.
- **Schemas and validation:** `_internal/ai/schemas/` and `_internal/tools/validation/` provide machine-readable rules and automated checks.
- **One reference showcase**: Aurora Group demonstrates end-to-end structure (company, data, models, use cases, reporting) and points to canonical factsheets.
- **Clear audience framing:** README and docs/README state who the framework is for (executives, business leads, data/analytics teams, architects).

### 5.2 Gaps summary

| Dimension | Gap | Evidence |
|-----------|-----|----------|
| Onboarding | No single "before you start" list (PowerShell, Node, repo root, npm ci). | Only npm ci mentioned under Stage 1; no consolidated prerequisites. |
| Implementation path | No documented path from "pick use case" to "generate TMDL and pass Stage 1". | README stops at "Explore use cases"; no link to generation or implementation guide. |
| Tooling discoverability | Stage 1 vs run_all_checks not explained; Stage 1 not in VSCode tasks. | README/AGENTS cite Stage 1; DoD and _internal/tools/README cite run_all_checks; tasks.json has only run_all_checks. |
| Consistency | new_usecase.ps1 uses non-existent cluster paths; DoD has wrong KPI template path; action code doc links use short use case path; Aurora references non-existent data paths; S-F.3.x vs S-F3.x filename inconsistency. | See Phase B and Phase C. |
| Friction | Ambiguity on which check script to run; generation script defaults assume parent-folder layout. | Multiple scripts; no "when to use which"; generate_tmdl_measures.ps1 defaults require override when run from repo root. |
| UseCase_Inventory | "Main Action Codes" column uses short codes (P2, M3, …) that do not match UseCase_ActionCode_Map (C-M2.1, …). | Inventory and map are out of sync; no documented alias table. |

### 5.3 Prioritized recommendations

1. **Fix path and ID consistency (high)**  
   - Update new_usecase.ps1 to use `usecases/core` and create `<ID>_<Name>` under it (or document current layout and align script).  
   - Correct usecase_DoD_Core.md to `framework/templates/kpi_catalog_templates/`.  
   - Correct action code `governance.documentation_links` to full use case folder names (e.g. SCM-001_Inventory_Performance).  
   - Align SupplyChain action code filenames with map IDs (S-F3.1 … S-F3.4 consistently).  
   - Fix Aurora README and showcase use case refs: point to existing data paths (e.g. data/gold) or add sample_data and document; remove or fix sample_data_contracts reference.

2. **Clarify Stage 1 vs run_all_checks and expose Stage 1 (high)**  
   - Add one short subsection (e.g. in README or _internal/tools/README): "Use run_stage1_checks.ps1 for CI and before merge; use run_all_checks.ps1 for full local validation including linters and PBIP."  
   - Add a VSCode task for run_stage1_checks.ps1 so the CI-mandated command is discoverable.

3. **Single "get started" and "implement one use case" path (high)**  
   - Add a "Prerequisites" section (PowerShell, Node, repo root, one-time npm ci) in README or a dedicated get-started page.  
   - Add a fourth step to README "How to get started" (or a linked page): "Implement a use case" with a minimal sequence: pick use case → open Business/Technical factsheets → run generate_tmdl_measures.ps1 (with explicit roots from repo root) → run run_stage1_checks.ps1.  
   - Optionally add a "First 2 hours" checklist (clone, prerequisites, read strategy + golden thread, run Stage 1, generate for one use case).

4. **Align implementation guide with framework entry points (medium)**  
   - In implementations/microsoft_fabric_powerbi/guide/README.md or fabric_powerbi.md, add pointers: use case factsheets (usecases/core/), KPI catalog (framework/kpi_catalog/), validation and generation (_internal/tools/run_stage1_checks.ps1, generate_tmdl_measures.ps1).

5. **UseCase_Inventory vs UseCase_ActionCode_Map (medium)**  
   - Either update the Inventory "Main Action Codes" column to full action code IDs from the map, or document the short codes as aliases and provide a mapping. Prefer aligning the table with the map for single source of truth.

6. **Aurora reproducibility (medium)**  
   - Add explicit "To reproduce" steps: e.g. run Stage 1 from repo root, run generate_tmdl_measures.ps1 for COM-001 (and list other demo use cases) with DistRoot pointing at showcase; fix data path references so they match existing folders or add the missing ones and document.

---

## 6. Optional: "First 2 hours" flow (proposed)

- Clone repo; ensure PowerShell and Node available; from repo root run `cd _internal\tools\validation && npm ci`.  
- Read README "How to get started" steps 1–3 (strategy, operating model, use cases).  
- Run `.\_internal\tools\run_stage1_checks.ps1` and fix any failures.  
- Pick one use case (e.g. COM-001); open its Business and Technical factsheets; run `.\_internal\tools\generation\generate_tmdl_measures.ps1 -UseCase COM-001 -UseCasesRoot framework/usecases -KpiCatalogRoot framework/kpi_catalog -DistRoot implementations/microsoft_fabric_powerbi/dist -OverwriteExisting`; run Stage 1 again.  
- Skim implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md if implementing in Fabric/Power BI.

This flow can be added to README or _internal/strategy once the path and consistency fixes above are in place.

---

## 7. Document and location

- **Report:** _internal/strategy/framework_evaluation_2026-02.md  
- **Next step:** Review this report; implement recommendations in separate tasks. Re-evaluate after changes to close onboarding, implementation path, and consistency gaps.
