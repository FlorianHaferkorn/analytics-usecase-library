<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. Run: python tooling/generator/generate_tool_configs.py -->

# Copilot Instructions

# Agent Task Workflow

When working on an assigned GitHub Issue or task, follow this workflow. Set issue status to In progress after creating the branch and document relevant delivery notes in the PR body.

## Obtain issue number (if user said "start next task" or similar)

If the user asked to **start the next task**, **take the next task**, **next task**, or similar and did **not** give an issue number: run from the **repo root** (PowerShell):

```powershell
.\tooling\project_mgmt\start_next_task.ps1
```

Parse the script output for the **issue number** (e.g. "Issue #17" or "Issue number for scripts: 17") and, if present, the **task title**. Use that issue number and title for the rest of the workflow (branch name, PR, Closes #N). Then continue with "Before starting" and "During implementation".

## Before starting

1. Read the assigned GitHub Issue / task description fully (if you ran start_next_task.ps1, you already have the issue number and title; you may still fetch the full description from the issue).
2. Identify which artifacts are affected (use case, action code, KPI, tooling, docs) and which expert context applies:
   - **Framework / Docs (framework topics):** Use Framework-Expert context (`docs/agent/rules/framework-expert.md`): core/, tooling/ir/, data_contracts/, tooling/validation/, tooling/ontology/. No tool-specific syntax.
   - **FabricPowerBI / products/fabric/powerbi/:** Use Fabric-Expert context (`docs/agent/rules/fabric-expert.md`): TMDL, DAX, run_fabric_checks. Use the **Power BI Modeling MCP** (server `powerbi-modeling-mcp`) for semantic model operations; see `fabric-expert.md` and `products/fabric/powerbi/docs/references/powerbi-modeling-mcp-setup.md`.
   - **Aurora (showcases/aurora_group):** Aurora is the showcase for every tool (Fabric first, others later). If the task involves Fabric implementation (DAX, TMDL, Measure_Dictionary, reports) → use Fabric-Expert. If the task is showcase structure only (YAML in showcases/aurora_group/models/, model definition, no tool syntax) → use Framework-Expert.
   - **Other areas:** Apply the skill that matches the artifact type below.
3. Read the relevant skill from `docs/agent/skills/` for the artifact type before editing:
   - Factsheet edit → `edit-factsheet-safely`
   - Bracket edit → `edit-usecase-bracket-safely`
   - New use case → `add-usecase-scaffold` (**read Research-to-Core Standard first: `docs/process/research-to-core-standard.md`**)
   - Domain evidence review → `docs/process/research-to-core-checklist.md`
   - KPI reference → `add-kpi-reference-safely`
   - Action code create/update → `add-action-code-and-wire-up`
   - Fabric/TMDL/DAX → `fabric-powerbi-validation`
   - Rename/delete KPI or action code → `assess-change-impact`
   - Stage 1 failure → `fix-stage1-failure`
   - Pre-commit validation → `stage1-pre-commit`
4. Change only files that belong to the task. Do not modify unrelated artifacts.

## During implementation

1. **Create the feature branch yourself** before editing any files. From the **repo root**, run (PowerShell or Git Bash):
   - `git fetch origin main`
   - `git checkout main`
   - `git pull origin main`
   - `git checkout -b agent/<issue-id>-<short-name>`
   Use the issue number you have (e.g. `16`). For `<short-name>`, derive a short kebab-case slug from the issue title (e.g. "Document automated reasoning scope" → `automated-reasoning-scope`), max ~40 characters. Example: `agent/16-automated-reasoning-scope`.
2. **Set project Status to In progress** for this issue so the board stays correct. From the **repo root** (PowerShell): `.\tooling\project_mgmt\set_issue_status.ps1 -Issue <N> -Status "In progress"` (use the issue number from `start_next_task.ps1` or the assigned issue).
3. Make small, focused changes. One PR per Issue.
4. **If you recognize that this task requires a skill or tool we don't yet have** (e.g. new artifact type, new domain): mention this need in the PR body so it can be prioritized.
5. Follow all rules in `docs/agent/rules/` — especially `framework-conventions.md`, `stage1-awareness.md` and `learning-routing.md`.
6. **Scratch files live in one folder per session** (Meridian D-658, 02.10.2026). Commit messages for
   `git commit -F`, PR bodies for `--body-file`, patch scripts and logs go to `%TEMP%\claude-<session>`
   (Windows) or `${TMPDIR:-/tmp}/claude-<session>`. Cleaning up means deleting that folder, **never** a
   pattern in `%TEMP%` (`msg_*.txt`, `body*.md`): on 02.10.2026 such a pattern removed 101 files,
   including files of other sessions on the same machine.

## SSOT audit findings (insertable remediation)

When an audit reports missing or inconsistent SSOT content (e.g. `audit_ssot_content.ps1`, use-case readiness audit), each finding may include **InsertableRemediation**: ready-to-paste content for the respective SSOT. Workflow: (1) **Highlight** findings in the report. (2) **Propose** the fix using the `insertable_content` and `insert_location` from the report. (3) **After the user confirms** the concrete contents, **insert** the content into the file at the given location. Do not apply insertable remediation without confirmation. Format and examples: [tooling/validation/docs/REMEDIATION_INSERTABLE_FORMAT.md](tooling/validation/docs/REMEDIATION_INSERTABLE_FORMAT.md).

## Before committing

1. Run the quality gate from repo root: `.\tooling\quality\run_quality_gate.ps1`
   (runs Stage 1 + Fabric checks in one pass; equivalent to running both separately)
2. If only core/governance changed (no Fabric artifacts): `.\tooling\run_stage1_checks.ps1` is sufficient.
3. Fix any failures before committing. Use the `fix-stage1-failure` skill if needed.
4. **After fixing any build, validation, or Desktop error:** If that error class is not yet in [internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md), add one row (Symptom | Cause | Fix) to the appropriate section so the same mistake is not repeated. See that file’s “Updating this list” section.

## Before reporting "ready for Desktop / user testing" (Fabric/PBIP)

When changes affect TMDL or reports (measures, tables, .pbip): **validate TMDL first**, then fix, then hand off. Do **not** ask the user to test until validation passes.

- Run **TMDL validation**: from repo root `.\products\fabric/powerbi\tooling\run_fabric_checks.ps1` (or `.\products\fabric/powerbi\tooling\tmdl_render_and_fix.ps1` for render + auto-fix + knowledge-base update).
- If TMDL syntax or PBIP readiness fails: fix the cause (e.g. measure formatString/displayFolder at **t2**; see KNOWN_ERRORS_AND_FIXES.md), regenerate if needed, re-run validation. Repeat until **check_tmdl_syntax** and **check_tmdl_pbip_readiness** pass.
- If a new error class was fixed: add or update a row in [internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md](internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md) (Symptom | Cause | Fix) so the learning loop captures it.
- Only after validation passes: tell the user that they can test (e.g. open the report .pbip in Power BI Desktop).

## PR creation

1. PR title: `[<Issue-ID>] <concise description>`
2. PR body: Summary of changes, link to Issue (e.g. `Closes #42`), checklist of what was verified.
3. Do not merge; leave for human review unless branch protection allows it.

---

# Framework Conventions

## Golden Thread

- **Strategy → KPIs → use cases → action codes → templates → semantic models.** Every artifact traces back; use cases and reports reference governed definitions; they do not define KPI meaning, targets, or lineage.
- **Single source of truth:** KPI definitions live in `core/kpi_catalog/`. Action logic and thresholds live in `core/action_codes/`. Use cases in `usecases/` only reference these; they do not redefine them.
- **Use cases reference, they do not define.** When editing use cases, link to KPI IDs and action code IDs; do not invent new KPI definitions or trigger logic in factsheets.
- **Report BoM:** The UseCase_Bracket represents all components needed to create the use case as a report: KPIs (strategic, influencing, supporting), evidence grain, and data contract. The registry validates that the bracket is complete (supporting KPIs via depends_on closure) and that evidence grain is governed in domain contracts.
- **Evidence grain is use-case-only.** It is defined in the bracket (`ux_layout_rules.page_2_execution.component_300s.evidence_grain`) and must be one of the grains from domain data contracts. Action codes do not define or imply report grain; their step text is shared across use cases and must not prescribe evidence grain (e.g. do not require "entity" in steps for entity_month use cases).

## Tool-agnostic vs. tool-specific

- **Core = tool-agnostisch:** Structure, IDs, lineage, logical formulas only. No DAX, format strings, or PBI visual types in core.
- **products/** = tool-specific realisation: e.g. `products/fabric/powerbi/` for DAX, TMDL, formatString, PBI visualType, PBIP. Same logic for all SSOT artifacts.

## Key Paths

- **Use cases:** `core/usecases/core/`, `core/usecases/templates/` — Business_Factsheet.md, UseCase_Bracket.yaml per use case.
- **Framework:** `core/kpi_catalog/`, `core/action_codes/`, `core/templates/` — KPI catalog, action code YAML, page/measure/data-contract templates.
- **Data contracts:** `core/data_contracts/domains/`, `core/data_contracts/sources/` — domain and source-level contracts.
- **Semantic models:** `core/semantic_models/domains/` — measure dictionaries (tool-agnostic); conceptual design in `core/strategy_operating_model/operating_model/semantic_layer.md`. TMDL/PBIP output lives under `products/fabric/powerbi/dist/`. (Legacy core_action_ready and showcase semantic_models archived.)
- **Docs:** `docs/company/`, `docs/operating_model/` — strategy and operating model; authority for structure and naming.
- **Internal:** `tooling/` — validation, generation, maintenance, Power BI MCP; `tooling/generator/schemas/` — JSON schemas for factsheets, action codes, data contracts, layout_330300.

## Naming and IDs

- Use case IDs: `COM-001`, `FIN-001`, `OPS-001`, `SCM-001`, `XD-001`, etc. (prefix + number).
- Action code IDs: e.g. `C-M2.1`, `F-C1.1`, `O-A2.1` — domain prefix + topic + index.
- KPI IDs: `KPI-<DOMAIN>-<NNN>` (D-594; e.g. `KPI-COM-003`). Must exist in KPI catalog before referencing in use cases or action codes.
- Domains: Commercial, Finance, Operations, Supply Chain, XD (Experience/Enterprise).

## Invariants

- Do not add new artifact types without alignment with `internal/archive/framework_evolution.md`.
- Automation and generation must produce artifacts that pass Stage 1; prefer existing scripts under `tooling/`.

---

# Stage 1 CI (Hard Gate)

Stage 1 is the mandatory CI gate. All checks must pass before merge. When suggesting edits, ensure they do not violate these checks.

## Canonical command (run from repo root)

```powershell
.\tooling\run_stage1_checks.ps1
```

## Checks run (in order)

1. **check_schema_validation.ps1** — Validates artifacts (action codes, UseCase_Bracket, org_roles) against JSON schemas in `tooling/validation/` and `tooling/generator/schemas/`.
2. **validate_factsheets.ps1** — Business factsheets structure; verifies `UseCase_Bracket.yaml` exists for each use case.
3. **check_factsheet_vs_kpi.ps1** — Every KPI referenced in Business factsheets/brackets exists in KPI catalog.
4. **validate_kpi_catalog.ps1** — KPI catalog structure and rules.
5. **check_action_codes_vs_kpi.ps1** — Every KPI ID in action codes exists in KPI catalog.
6. **check_factsheet_action_codes.ps1** — Business factsheet / bracket action code references vs framework action codes.
7. **check_decision_spines.ps1** — Decision spine map and spine files consistent.
8. **check_duplicate_ids.ps1** — No duplicate IDs across governed artifacts.
9. **check_ssot_markers.ps1** — Single source of truth markers respected.
10. **check_docs_refs.ps1** — Doc references valid.
11. **check_forbidden_content.ps1** — No forbidden content in repo.
12. **check_validate_data_contracts.ps1** — Domain data contracts under `core/data_contracts/domains/` valid (structure, dimension/fact keys, grain).
13. **check_registry_builder.ps1** — Registry builder governance validation (`tooling/ontology/registry_builder.py --strict`).

## Prerequisite (one-time, for schema validation)

```powershell
cd tooling\validation
npm ci
```

## If Stage 1 is green locally but fails in GitHub

- **Same command:** CI runs `./tooling/run_stage1_checks.ps1 -Root $env:GITHUB_WORKSPACE` from the repo root. Run the same locally: `.\tooling\run_stage1_checks.ps1 -Root .` (or without `-Root` from repo root).
- **Schema validation (npm):** CI uses `npm ci` in `tooling/validation`. If you changed `package.json` without updating `package-lock.json`, CI fails; commit the lock file after `npm ci` (or `npm install`) in `tooling/validation`.
- **Data contracts (Python):** CI installs deps from `tooling/validation/requirements-data-contracts.txt`. If a check uses Python, ensure `py -3` or `python` works and the same deps are installed locally.
- **Registry builder:** Uses `py -3` or `python`; on the runner only `python` may be on PATH. If you see "Python 3 not found" in CI, the workflow’s `actions/setup-python` step should have run; check that the "Run Stage 1 checks" step uses the same runner (windows-latest) and that no step changed the environment in a way that hides Python.
- **Path/working directory:** The workflow sets `working-directory: ${{ github.workspace }}` and passes `-Root $env:GITHUB_WORKSPACE` so the script always receives the repo root; this avoids failures when the runner’s current directory differs from the workspace.

## When suggesting changes

- New or changed KPI references → must exist in `core/kpi_catalog/`.
- New or changed action code IDs → must be in `core/action_codes/` and subscribed via `UseCase_Bracket.yaml` `orchestration.action_code_ids`.
- Business factsheet edits → human-readable only; no YAML blocks. All machine-readable config in `UseCase_Bracket.yaml`.
- Bracket edits → preserve required keys per `usecase_bracket.schema.json`; governance roles must exist in `core/organization/org_roles.yaml` (or Aurora showcase path; see core/organization/README.md).
- Before committing, run Stage 1 from repo root to confirm no regressions.

---

# Learning Routing (where to store fixes)

Goal: the same error must not recur in a new session. Every learned fix is routed to its
single source of truth (SSOT), and the relevant validation is re-run. This refines the
generic "Learning Loop" in `AGENTS.md`.

## 1. Read early (before starting implementation)

- `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` — error symptom → root cause → fix recipes.
- `core/kpi_catalog/planned.yaml` — catalog KPIs whose measure is not yet implemented in TMDL;
  the catalog↔TMDL drift check (`tooling/validation/check_catalog_tmdl_drift.py`) reports them
  as warnings, not errors.

## 2. Route new learning by error type

- **Catalog↔TMDL drift fails (strict) because a catalog measure is missing in `_Measures.tmdl`
  and is intentionally not implemented yet:**
  - Add or update the entry in `core/kpi_catalog/planned.yaml` with `kpi_id`, `owner`,
    `eta_date` (YYYY-MM-DD) and `reason` (one line). Schema:
    `tooling/generator/schemas/planned_kpi.schema.json`; the `kpi_id` must exist in
    `core/kpi_catalog/KPI_Catalog.md`.
  - Do not add this to `KNOWN_ERRORS_AND_FIXES.md` unless the drift-check logic itself is broken.

- **PBIR/visual binding failure — a measure `Property` in a `visual.json` is not found in the
  domain `_Measures.tmdl`:**
  - Fix the generator/orchestrator so it binds to the correct measure **display name**
    (do not only patch the generated `visual.json`).
  - Add a regression test, or update the existing measure-binding test expectations.
  - If this is a new error class or pattern: add a row to `KNOWN_ERRORS_AND_FIXES.md`.

- **TMDL/DAX/semantic-model structural issues** (`formatString`/`displayFolder` indentation,
  blank stubs, invalid naming):
  - Fix the generator output at its source.
  - If the same structural violation appears again: add a row to `KNOWN_ERRORS_AND_FIXES.md`.

- **Any other recurring failure** (schema state inconsistencies, empty decision fields,
  missing artifacts):
  - Add symptom → root cause → fix steps as a row to `KNOWN_ERRORS_AND_FIXES.md`
    (appropriate section).

## 3. Verify after edits

Always run the most relevant validation after substantive changes (from repo root):

- Core / cross-references: `.\tooling\run_stage1_checks.ps1`
- Fabric / PBIP artifacts: `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1`
  (or `.\tooling\quality\run_quality_gate.ps1` for Stage 1 + Fabric in one pass)
- Catalog↔TMDL drift: `python tooling/validation/check_catalog_tmdl_drift.py --repo-root . --strict`

---

