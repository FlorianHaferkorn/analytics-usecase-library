# Agent Task Workflow

When working on an assigned GitHub Issue or task, follow this workflow. Set issue status to In progress after creating the branch and document relevant delivery notes in the PR body.

## Workday note (before starting any new implementation)

1. If your team uses a workday guard, run `tooling/project_mgmt/workday_start.ps1` before starting implementation.

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
