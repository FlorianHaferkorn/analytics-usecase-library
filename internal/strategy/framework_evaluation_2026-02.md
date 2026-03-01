# Framework Evaluation Report (2026-02)

Evaluation of the Analytics Use Case Library against **ease of use** and **ease of implementation** to support improvement toward best-in-class BI framework adoption.

**Status:** All 6 prioritized recommendations implemented. No open evaluation TODOs.

**Re-audit (2026-02-05):** Phases A–D re-executed against current repo. Three corrections applied: (1) README merge conflict markers removed; (2) implementation guide README script paths corrected from `tooling/validation/` to `tooling/` for run_stage1_checks.ps1 and run_all_checks.ps1; (3) core/strategy_operating_model/README.md updated to name run_stage1_checks.ps1 and run_all_checks.ps1 in "Run validation tools before delivery". All other findings and resolution status confirmed.

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
| [README.md](../../README.md) | Strategy-to-action framework; get started in 4 steps | 1) core/strategy_operating_model/company/ (strategy, reporting principles), 2) core/strategy_operating_model/operating_model/ (overview, golden_thread), 3) core/usecases/core + UseCase_Inventory, 4) "Implement a use case" (generate_tmdl_measures.ps1, Stage 1, run_fabric_checks); Prerequisites (PowerShell, Node, repo root, npm ci); "When to use which" (Stage 1 vs run_all_checks vs Fabric-only). Links to products/fabric/powerbi/docs/ in step 4. |
| [core/strategy_operating_model/README.md](../../core/strategy_operating_model/README.md) | Single navigation entry; Golden Thread order | 1) core/strategy_operating_model/company/, 2) operating_model/, 3) core/, 4) usecases/data_contracts/semantic_models, 5) showcases/aurora_group. "Run validation tools before delivery: run_stage1_checks.ps1 (CI gate); run_all_checks.ps1 (full validation)" from repo root. Resolved in re-audit. |
| [products/fabric/powerbi/docs/README.md](../../products/fabric/powerbi/docs/README.md) | Platform-specific implementation (Fabric/Power BI) | fabric/powerbi.md, tmdl_best_practices.md; "Framework and tooling entry points" table (usecases/core, kpi_catalog, run_stage1_checks.ps1, run_all_checks.ps1, run_fabric_checks.ps1, generate_tmdl_measures.ps1). Paths corrected to tooling/ (not tooling/validation/) for run_stage1_checks and run_all_checks. |
| [showcases/aurora_group/README.md](../../showcases/aurora_group/README.md) | End-to-end demo with synthetic company | company/, data/gold/, usecases/, reporting/, semantic_models/. "To reproduce" lists explicit commands (npm ci, run_stage1_checks.ps1, generate_tmdl_measures.ps1, run_fabric_checks.ps1). Validation tools and framework paths referenced. |

### 2.2 Single path test

From "I am new":

- **Strategy to use case:** README gives a clear sequence: core/strategy_operating_model/company/, then operating_model/, then core/usecases/core and UseCase_Inventory. No dead end.
- **Use case to implementation:** README step 4 "Implement a use case" documents: pick use case, run generate_tmdl_measures.ps1, run Stage 1, run_fabric_checks; links to products/fabric/powerbi/docs/.
- **Validation:** README "When to use which" explains Stage 1 (CI/merge) vs run_all_checks (full local) vs run_fabric_checks (Fabric-only). usecase_DoD_Core.md still cites run_all_checks.ps1 for Tooling DoD; tooling/README explains Stage 1 vs run_all_checks.

**Finding (current state):** Single path exists from strategy to implementation: steps 1–4 in README plus "First 2 hours" checklist. Use case to generation and validation is documented in README step 4.

### 2.3 Check script clarity

| Source | Script cited | Context |
|--------|--------------|---------|
| README.md | `run_stage1_checks.ps1` | "Stage 1 CI Gate (local / CI)" |
| AGENTS.md | `run_stage1_checks.ps1` | "Before committing ... run Stage 1" |
| usecases/usecase_DoD_Core.md | `run_all_checks.ps1` | "Tooling & Automation DoD"; lists validate_factsheets, validate_kpi_catalog, check_factsheet_vs_kpi |
| tooling/README.md | `run_all_checks.ps1` | "Master quality runner"; runs KPI validation, factsheet validation, KPI-use case checks, measure checks, PBIP, linters |

**Finding (current state):** README "When to use which" and tooling/README "Stage 1 vs run_all_checks" state the distinction. Stage 1 is linked from README get-started flow and from VSCode task "Run Stage 1 checks (CI gate)". Resolved.

### 2.4 Prerequisites

- **Current state:** README "How to get started" lists Prerequisites: PowerShell (or pwsh); Node.js for schema validation; one-time `cd tooling\validation` then `npm ci`; run all commands from repository root. "First 2 hours" checklist reinforces clone, npm ci, run Stage 1, pick use case, generate measures. Resolved.

---

## 3. Phase B: Consistency and correctness audit

### 3.1 Path and ID consistency

| Issue | Evidence | Status |
|-------|----------|--------|
| new_usecase.ps1 cluster paths | `Get-ClusterPath` now returns `core/usecases/core` (not 01_Commercial etc.). Script creates `<ID>_<Title>` under core/usecases/core. | **Resolved.** |
| usecase_DoD_Core.md KPI template path | DoD section 2 references `core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md`. Actual file exists at that path. | **Resolved.** |
| Action code documentation_links | Action code YAMLs use full paths (e.g. `core/usecases/core/SCM-001_Inventory_Performance/Business_Factsheet.md`). | **Resolved.** |
| SupplyChain action code filenames | S-F3.1–S-F3.4; single convention S-F3.x.yaml. | **Resolved.** |
| Implementation guide script paths | Guide README previously cited `tooling/validation/run_stage1_checks.ps1` and `run_all_checks.ps1`; scripts live under `tooling/`. | **Fixed in re-audit (2026-02-05).** |

### 3.2 UseCase_Inventory vs UseCase_ActionCode_Map

- **Current state:** UseCase_Inventory.md "Main Action Codes" column uses full action code IDs (C-M2.1, C-S1.1, C-S1.2, S-I1.1, O-O1.1, etc.) matching UseCase_ActionCode_Map.yaml. **Resolved.**
- **Lean 2.0 update:** `UseCase_ActionCode_Map.yaml` has been deleted. Action code subscriptions now live in each `UseCase_Bracket.yaml` (`orchestration.action_code_ids`). `UseCase_Inventory.md` is generated by `registry_builder.py`.

### 3.3 VSCode tasks

- [`.vscode/tasks.json`](../../.vscode/tasks.json): **Resolved.** Task \"Run Stage 1 checks (CI gate)\" added; README and tooling/README now explain Stage 1 vs run_all_checks vs Fabric-only.

---

## 4. Phase C: Implementation path simulation

### 4.1 "Implement one use case" path (e.g. COM-001)

Trace from "I want to implement COM-001" to "TMDL generated and Stage 1 passed":

1. **Business Factsheet:** usecases/core/COM-001_Sales_Performance/Business_Factsheet.md — human context, UX narrative.
2. **UseCase_Bracket.yaml:** usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml — KPI orchestration, action code subscriptions, value driver model, governance. *(Replaces Technical_Factsheet.md and UseCase_ActionCode_Map.yaml since Lean 2.0.)*
3. **KPI catalog:** core/kpi_catalog/ — all referenced KPIs must exist here.
4. **Action codes:** core/action_codes/ — all subscribed action code IDs must exist here.
5. **Generation:** `.\tooling\generation\generate_tmdl_measures.ps1 -UseCase COM-001 -UseCasesRoot core/usecases -KpiCatalogRoot core/kpi_catalog -DistRoot products/fabric/powerbi/dist` (or DistRoot showcases/aurora_group/semantic_models for Aurora). Script defaults are core/usecases, core/kpi_catalog, products/fabric/powerbi/dist when run from repo root.
6. **Validation:** `.\tooling\run_stage1_checks.ps1` from repo root.

**Current state:** README step 4 "Implement a use case" lists the sequence (pick use case, generate_tmdl_measures.ps1, Stage 1, run_fabric_checks) and links to products/fabric/powerbi/docs/. fabric/powerbi.md "Where this fits in the repo" references use case factsheets, KPI catalog, validation scripts, TMDL generation. Resolved.

### 4.2 Aurora showcase

- [showcases/aurora_group/README.md](../../showcases/aurora_group/README.md): **Resolved.** Now points to `data/gold/` and framework data contracts; \"To reproduce\" lists explicit commands (run_stage1_checks.ps1, generate_tmdl_measures.ps1 per use case, run_fabric_checks.ps1, -DistRoot option).
- [showcases/aurora_group/usecases/core/COM-001.md](../../showcases/aurora_group/usecases/core/COM-001.md): **Resolved.** Data reference updated to `showcases/aurora_group/data/gold/` (facts/dimensions).

### 4.3 Implementation guide links

- [products/fabric/powerbi/docs/fabric_powerbi.md](../../products/fabric/powerbi/docs/fabric_powerbi.md): **Resolved.** Guide README and fabric/powerbi.md now include "Framework and tooling entry points" (usecases/core, kpi_catalog, run_stage1_checks, run_all_checks, run_fabric_checks, generate_tmdl_measures) and a "Fabric & Power BI best practices and validation" section (TMDL, DAX rules, run_fabric_checks).

---

## 5. Phase D: Synthesis

### 5.1 Strengths

- **Golden thread and SSOT**: Strategy to KPIs to use cases to action codes to templates is clearly articulated in docs and in repo structure. KPI catalog and action codes are the single source of truth; use cases reference them.
- **Stage 1 CI:** A well-defined fail-fast gate with a single command and a clear list of checks; run_stage1_checks.ps1 is documented in README and AGENTS.md.
- **Schemas and validation:** `tooling/ai/schemas/` and `tooling/validation/` provide machine-readable rules and automated checks.
- **One reference showcase**: Aurora Group demonstrates end-to-end structure (company, data, models, use cases, reporting) and points to canonical factsheets.
- **Clear audience framing:** README and docs/README state who the framework is for (executives, business leads, data/analytics teams, architects).

### 5.2 Gaps summary (addressed by recommendations 1–6; re-audit 2026-02-05)

| Dimension | Original gap | Current state |
|-----------|--------------|---------------|
| Onboarding | No single "before you start" list. | README Prerequisites and "First 2 hours" checklist. Resolved. |
| Implementation path | No documented path from "pick use case" to "generate TMDL and pass Stage 1". | README step 4 and implementation guide entry points. Resolved. |
| Tooling discoverability | Stage 1 vs run_all_checks not explained; Stage 1 not in VSCode tasks. | README "When to use which"; tooling/README "Stage 1 vs run_all_checks"; VSCode task "Run Stage 1 checks (CI gate)". Resolved. |
| Consistency | new_usecase.ps1 cluster paths; DoD KPI path; action code doc links; Aurora data paths; S-F3.x filenames; implementation guide script paths. | All resolved; implementation guide paths fixed in re-audit. |
| Friction | Ambiguity on which check script to run. | README and tooling/README clarify. Resolved. |
| UseCase_Inventory | Short codes vs UseCase_ActionCode_Map. | Inventory uses full action code IDs. Resolved. |

**Resolved in re-audit:** core/strategy_operating_model/README.md updated to name run_stage1_checks.ps1 and run_all_checks.ps1 (from repo root).

### 5.3 Prioritized recommendations

1. **Fix path and ID consistency (high)** — **Done.** new_usecase.ps1 uses `core/usecases/core` and `<ID>_<Name>`; usecase_DoD_Core.md uses `core/templates/kpi_catalog_templates/`; action code `documentation_links` use full folder names (e.g. SCM-001_Inventory_Performance); SupplyChain filenames S-F3.1–S-F3.4; Aurora README and COM-001 refs point to data/gold and "To reproduce" added.

2. **Clarify Stage 1 vs run_all_checks and expose Stage 1 (high)** — **Done.** README "When to use which" subsection; tooling/README "Stage 1 vs run_all_checks" section; VSCode task "Run Stage 1 checks (CI gate)" added.

3. **Single "get started" and "implement one use case" path (high)** — **Done.** README: Prerequisites (PowerShell, Node, repo root, npm ci) under "How to get started"; step 4 "Implement a use case" with sequence and command; "First 2 hours" optional checklist.

4. **Align implementation guide with framework entry points (medium)** — **Done.** Guide README has "Framework and tooling entry points" table; fabric/powerbi.md has "Where this fits in the repo" and section 11 "Fabric & Power BI best practices and validation"; tmdl_best_practices.md References updated (framework paths, run_fabric_checks, DAX rules).

5. **UseCase_Inventory vs UseCase_ActionCode_Map (medium)** — **Done.** UseCase_Inventory "Main Action Codes" column updated to full action code IDs from UseCase_ActionCode_Map.yaml (e.g. COM-001: C-M2.1, C-S1.1, C-S1.2; SCM-003: S-F3.1–S-F3.4).

6. **Aurora reproducibility (medium)** — **Done.** Aurora README "To reproduce" now lists explicit steps from repo root: prerequisites (npm ci), run_stage1_checks.ps1, generate_tmdl_measures.ps1 per use case (COM-001 … FIN-001) with optional -DistRoot showcases/aurora_group, run_fabric_checks.ps1, and point semantic model to data/gold.

---

## 6. Optional: "First 2 hours" flow (proposed)

- Clone repo; ensure PowerShell and Node available; from repo root run `cd tooling\validation && npm ci`.  
- Read README "How to get started" steps 1–3 (strategy, operating model, use cases).  
- Run `.\tooling\run_stage1_checks.ps1` and fix any failures.  
- Pick one use case (e.g. COM-001); open its Business and Technical factsheets; run `.\tooling\generation\generate_tmdl_measures.ps1 -UseCase COM-001 -UseCasesRoot core/usecases -KpiCatalogRoot core/kpi_catalog -DistRoot products/fabric/powerbi/dist -OverwriteExisting`; run Stage 1 again.  
- Skim products/fabric/powerbi/docs/fabric_powerbi.md if implementing in Fabric/Power BI.

This flow is now reflected in README "How to get started" (step 4, "First 2 hours" checklist).

---

## 7. Document and location

- **Report:** internal/strategy/framework_evaluation_2026-02.md  
- **Re-audit:** 2026-02-05. Phases A–D re-executed; README merge conflict and implementation guide script paths corrected; all findings and resolution status confirmed.  
- **Next step:** Re-evaluate when repo structure, entry points, or scope change. No open action items from this evaluation.
