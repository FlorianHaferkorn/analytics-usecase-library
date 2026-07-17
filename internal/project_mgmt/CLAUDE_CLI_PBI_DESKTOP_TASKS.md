# Claude CLI (VS Code) — Power BI Desktop report tasks

## Why this file exists

**Any task that edits a PBIP report or semantic model and needs Power BI Desktop to validate must
run in the Claude CLI inside VS Code on a Windows dev box** — not in a cloud/Linux session. Only that
environment has all of: Power BI **Desktop** (the authoritative load/render gate), the **Fabric CLI**
(`fab`), the Windows-only **Stage-1 / Fabric quality-gate** PowerShell scripts, and the **MCP servers**
(Microsoft Learn for PBIR/TMDL/DAX docs, GitHub for the PR/CI). Linux sessions can edit and run the
Python/drift gates, but they **cannot** confirm a report still loads — that only shows up in Desktop
(the columnless / `get_Islands()` failure class in `KNOWN_ERRORS_AND_FIXES.md`).

This doc is the pickup brief for those tasks. A ready-to-paste **prompt is at the bottom**.

## Prerequisites (Windows dev box)

- Power BI **Desktop** installed and able to open the PBIP files under `products/fabric/powerbi/dist/`.
- Repo cloned; work on branch **`claude/report-quality-roadmap-m997dz`** (PR #390). Pull latest first.
- Python env for the gates; **PowerShell** for `tooling/run_stage1_checks.ps1` and
  `tooling/quality/run_quality_gate.ps1` (Windows-only — the reason this runs here).
- **Fab CLI**: run `fab config set mode command_line` once per session before any non-interactive
  `fab` call (else it opens blocking prompts).
- **MCP servers** available in the CLI: **Microsoft Learn** (search/fetch official PBIR, TMDL, DAX,
  ISO/Fabric docs before inventing structure), **GitHub** (PR + CI). Use them instead of guessing.

## Ground rules (read before editing — repo doctrine overrides defaults)

1. Read `CLAUDE.md` + `AGENTS.md` first (router + TMDL/PBIR hardrules + Golden Thread).
2. **PostToolUse hooks are non-bypassable**: `validate_tmdl_style.sh` blocks Tab/`:=`/`description:`
   issues in `.tmdl`; `validate_pbir_structure.sh` blocks JSON syntax errors in PBIP `.json`/`.pbir`.
   If a hook blocks → **fix and retry, never bypass**.
3. TMDL hardrules: tabs (not spaces), `=` not `:=`, `/// Purpose:` comment not `description:`, set
   `summarizeBy`/`formatString`. Reference-don't-redefine: KPIs live in `core/kpi_catalog/`, never
   redefined in reports/models.
4. Commit footer (every commit):
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` then
   `Claude-Session: <your session URL>`. **Never** put the model id in any pushed artifact.
5. ALUCA and Meridian are separate products — no co-branding.
6. GitHub Actions is in a known usage-limit outage (~2 s red, `runner_id:0`, HTTP 404 logs) — don't
   chase it; validate locally + in Desktop.

## Standard workflow for a PBI Desktop report/model task

1. **Understand** the target: which `.SemanticModel` and which `.Report` (a report's model is in
   `<Report>/definition.pbir` → `datasetReference.byPath.path`). Confirm measure names in the model's
   `definition/tables/_Measures.tmdl`. Note that a report's `nativeQueryRef` can be a **display alias**
   that differs from the defined measure name — reconcile in Desktop, don't assume.
2. **Edit** SSOT first (catalog/brackets/measure-defs), then the curated dist (`.tmdl` / `visual.json`).
   Dist is `no_overwrite` — it does not regenerate from the catalog; hand-edit it.
3. **Desktop-validate**: open each edited `.SemanticModel` and its report in Power BI Desktop; confirm
   it loads with no columnless/relationship errors and the visuals bind. This is the gate a Linux
   session cannot run.
4. **Gates**: `bash tooling/run_local_ci_check.sh` (drift-gate, pytest, `check_standard_ref.py --strict`,
   `check_usecase_quality.py --strict`, `validate_bindings.py`) **and** the Windows
   `tooling/run_stage1_checks.ps1` + `tooling/quality/run_quality_gate.ps1`.
5. **Regenerate** any generated artifacts touched: `tooling/codegen/kpi_catalog_files.py render`,
   ontology (`tooling/ir/build_ir.py`, `tooling/ontology/registry_builder.py`), goldens
   (`python -m tooling.superversion.from_aluca <bracket> --out tooling/superversion/tests/golden/<UC>.json`).
6. **Commit + push** to the branch; keep PR #390 updated.

---

## Current task: physical KPI de-duplication (Desktop-gated)

**Full technical spec:** [`KPI_DEDUP_MIGRATION_RUNBOOK.md`](KPI_DEDUP_MIGRATION_RUNBOOK.md) — follow it
exactly. Summary so the CLI session has context:

- The SSOT dedup is **already done** (each twin KPI has a `canonical_kpi_id` pointer;
  `tooling/validation/check_standard_ref.py` reports the duplicate sets). This task does the **physical**
  removal the Linux session could not validate.
- **7 twins → canonical:** `ops.otif.pct`, `scm.service_level.pct`, `ops.service_level.pct` →
  `supply.otif.pct`; `ops.inventory.value.amount` → `fin.liquidity.inventory.amount`;
  `ops.production.volume` → `ops.throughput.units`; `ops.yield.pct` → `ops.quality.pct`;
  `svc.nps.index` → `crm.nps.index`.
- **Report bindings are small:** only **FIN-001** (`Supply Chain Service Level %`) and **FIN-002**
  (`Production Volume Units`, `Yield %`) bind a twin measure. Reconcile measure names per model (the
  two Finance service-level twins collapse to one `OTIF %`; Experience already has `OTIF % (XD)`).
- Do it **one twin at a time**: SSOT edits → dist rename/rebind → **open the affected model(s) +
  report in Desktop** → gates → commit. Don't batch blind.

### Definition of done
- All 7 twin KPI files deleted; every reference rewired + deduped; `check_standard_ref.py --strict`
  duplicate-set report = **0 open** sets.
- Duplicate measures renamed/removed in the domain models; FIN-001 + FIN-002 reports rebound.
- **Every edited `.SemanticModel` and the FIN-001/FIN-002 reports open cleanly in Power BI Desktop.**
- Goldens regenerated; `run_local_ci_check.sh` green; Windows Stage-1 + Fabric quality gate green.
- Committed to `claude/report-quality-roadmap-m997dz`; PR #390 updated.

---

## Prompt — paste this into the Claude CLI (VS Code, Windows)

```
You are running in the Claude CLI in VS Code on a Windows dev box with Power BI Desktop, the Fabric
CLI, and the MCP servers (Microsoft Learn, GitHub). Repo: analytics-usecase-library, branch
claude/report-quality-roadmap-m997dz (PR #390). Pull latest first.

Read these before touching anything: CLAUDE.md, AGENTS.md, and
internal/project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md (the handoff brief) plus
internal/project_mgmt/KPI_DEDUP_MIGRATION_RUNBOOK.md (the technical spec).

Task: execute the physical KPI de-duplication in the runbook — delete the 7 twin KPIs, rewire and
dedupe all references, rename/remove the duplicate measures in the domain semantic models, and rebind
the FIN-001 and FIN-002 reports to the canonical measures.

Do it ONE twin at a time, and for each: (1) make the SSOT + dist edits, (2) OPEN the affected
.SemanticModel and its report in Power BI Desktop and confirm it loads with no errors and the visuals
bind correctly — this Desktop check is the whole reason we're in the CLI, so do not skip it, (3) run
`bash tooling/run_local_ci_check.sh` plus the Windows `tooling/run_stage1_checks.ps1` and
`tooling/quality/run_quality_gate.ps1`, (4) regenerate goldens/ontology/catalog for the affected use
cases, (5) commit. Respect the non-bypassable TMDL/PBIR hooks (fix, never bypass), run
`fab config set mode command_line` before any non-interactive fab call, and use the Microsoft Learn
MCP for any PBIR/TMDL/DAX detail rather than guessing.

Done = all 7 twins gone, check_standard_ref --strict shows 0 open duplicate sets, every edited model +
the FIN-001/FIN-002 reports open cleanly in Desktop, all local + Windows gates green, goldens
regenerated, pushed to the branch with PR #390 updated. Commit footer:
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com> and the Claude-Session line. Do not put the
model id in any pushed artifact; do not co-brand ALUCA with Meridian.

Start by pulling latest, reading the four docs, and printing the twin→canonical plan with the exact
files you'll touch for the first twin before editing.
```
