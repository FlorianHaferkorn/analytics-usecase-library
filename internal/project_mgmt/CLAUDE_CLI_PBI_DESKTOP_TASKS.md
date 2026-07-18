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
- Repo cloned; **check out the feature branch, not `main`** —
  `git fetch origin && git checkout claude/report-quality-roadmap-m997dz && git pull` (PR #390). The
  task's preconditions (canonical pointers, `check_standard_ref.py`, the SSOT dedup) live only on this
  branch; `main` does not have them, and all work commits back to this branch.
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

## ✅ DONE (merged in PR #390): physical KPI de-duplication

This task is **complete** — executed via the CLI, Desktop-validated, and merged to `main` in PR #390
(catalog 127→119). Kept below as the reference example of the workflow. The **active** tasks are #2/#3
in the "Follow-up tasks" section further down; use the prompt at the very bottom of this file.

**Full technical spec (historical):** [`KPI_DEDUP_MIGRATION_RUNBOOK.md`](KPI_DEDUP_MIGRATION_RUNBOOK.md).
Summary of what was done:

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
CLI, and the MCP servers (Microsoft Learn, GitHub). Repo: analytics-usecase-library.

FIRST, check out the feature branch — do NOT work on main. The task's preconditions (the
canonical_kpi_id pointers, tooling/validation/check_standard_ref.py, the whole SSOT dedup) exist ONLY
on this branch, and all work commits back to it:
    git fetch origin && git checkout claude/report-quality-roadmap-m997dz && git pull
(PR #390 tracks this branch.)

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

---

## Follow-up tasks after PR #390 merge (#2 data-gap, #2b $schema lint, #3 checker)

PR #390 is merged to `main`. These are **new** work → branch fresh from `main`
(`git fetch origin main && git checkout -B claude/report-quality-roadmap-m997dz origin/main`)
and open a **new** PR. All three are Desktop/Fabric-gated (that's why they're here, not done on Linux).

### #2 — Source quality data into the Finance model (decided: "source the data")
FIN-002 (Cost Performance) shows `Quality % (FIN)` and `Quality Defect Rate %` as unit-cost drivers,
but their Finance measures reference tables the Finance model lacks — **dangling refs, broken columns**:
- `Quality % (FIN)` = `DIVIDE(SUM(fact_ops[Good Units]), SUM(fact_ops[Output Units]))` — `fact_ops` absent.
- `Quality Defect Rate %` = `DIVIDE(SUM(fact_quality[Defect Count]), SUM(fact_ops[Output Units]))` —
  `fact_quality` + `fact_ops` absent.
- (`Throughput Units (FIN)` is already correct on `fact_output` — leave it.)

Fix = give the Finance model the data (mirror how the Operations model sources it):
1. **Contract** `core/data_contracts/domains/finance.yaml`, table `fact_output` (grain
   plant_line_product_month): add `- {name: Good Units, type: decimal, agg: sum}` and
   `- {name: Defect Count, type: decimal, agg: sum}`; add `quality_rules` (Good Units ≤ Output Units;
   both ≥ 0; Defect Count ≥ 0).
2. **Semantic model** `Finance.SemanticModel`: add the two columns to `fact_output.tmdl`
   (mirror the existing `column 'Output Units'` block — `summarizeBy`, `sourceColumn`), and repoint the
   two measures in `_Measures.tmdl` off `fact_ops`/`fact_quality` onto `fact_output`:
   `Quality % (FIN)` → `DIVIDE(SUM(fact_output[Good Units]), SUM(fact_output[Output Units]))`;
   `Quality Defect Rate %` → `DIVIDE(SUM(fact_output[Defect Count]), SUM(fact_output[Output Units]))`.
   Drop the `/// NOTE: fact_ops … Finance model lacks it` comments.
3. **Seed data** — the crux: regenerate the Finance gold-layer `fact_output` (parquet + `_delta_log`)
   with the two new columns populated realistically (Good Units ≈ 0.96–0.99 × Output Units;
   Defect Count ≈ 0.01–0.04 × Output Units). Use the synthetic generator, not a hand-edit; verify with
   `scripts/check_showcase_delta.py`. Declaring the columns WITHOUT populating the parquet guarantees
   the columnless/`get_Islands` crash (KNOWN_ERRORS) — do them together.
4. **Generator** — update the Finance `fact_output` synthesizer so future regens emit the columns.
5. **Regenerate + validate**: goldens for FIN-002, catalog/ontology; `run_local_ci_check.sh`;
   **open Finance.SemanticModel + FIN-002 report in Desktop** and confirm both quality columns compute
   (non-blank) and the model loads clean.

### #2b — Pre-existing `$schema` PBIR lint (2 errors, identical on all 16 reports)
Fabric/`fab-inspector`-gated (no runnable validator on Linux). Run the report `$schema` validator
(`fab-inspector` / `powerbi-report-author validate`), read the 2 errors, fix at the source (likely a
stale/incorrect `$schema` URL or a missing required property in each `report.json`/`definition.pbir`),
and re-validate. 0-new from the dedup, so this is cleanup — batch the identical fix across all 16.

### #3 — Report measure-resolution check (close the validator gap)
`validate_bindings.py` checks projection structure only; nothing verifies a report's
`nativeQueryRef` resolves to a `measure '<name>'` in the model named by `definition.pbir →
datasetReference.byPath.path`. Build that check, BUT calibrate for PBIR `nativeQueryRef` being a
**display alias** that can differ from the defined measure name (e.g. reports bind `OTIF %` while the
Experience model defines `OTIF % (XD)`) — resolve via the actual measure entity reference in the
projection, not the alias string. Confirm it's green on the current dist in Desktop before wiring
`--strict` into `run_local_ci_check.sh`; run advisory first (BC-NARR→BC-CHART ratchet pattern).

---

## Prompt for the ACTIVE follow-up tasks (#2 + #3) — paste into the Claude CLI (VS Code, Windows)

```
You are running in the Claude CLI in VS Code on a Windows dev box with Power BI Desktop, the Fabric
CLI, and the MCP servers (Microsoft Learn, GitHub). Repo: analytics-usecase-library.

PR #390 (KPI standards program + use-case quality + KPI de-duplication) is already MERGED to main.
These are NEW tasks — branch fresh from main and open a NEW PR:
    git fetch origin main && git checkout -B claude/report-quality-roadmap-m997dz origin/main

Read first: CLAUDE.md, AGENTS.md, and internal/project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md
(the "Follow-up tasks after PR #390 merge" section has the exact per-surface steps for all three).

Do these three, each Desktop/Fabric-gated, one at a time with a Power BI Desktop load-check before commit:

#2 — Source quality data into the Finance model (decision already taken: "source the data", not remove).
  FIN-002's Quality % (FIN) and Quality Defect Rate % reference fact_ops/fact_quality, which the Finance
  model lacks → broken columns. Add Good Units + Defect Count to Finance fact_output (contract +
  fact_output.tmdl + REGENERATE the gold-layer parquet/_delta_log via the synthetic generator, populated
  realistically), repoint the two measures off fact_ops/fact_quality onto fact_output, regenerate goldens,
  and confirm in Desktop that both quality columns compute non-blank and the model loads clean. Declaring
  the columns without regenerating the seed data WILL cause the columnless/get_Islands crash — do them
  together.

#2b — Fix the pre-existing $schema PBIR lint (2 identical errors on all 16 reports) via fab-inspector /
  powerbi-report-author validate; batch the same fix across all reports; re-validate.

#3 — Build a report measure-resolution check (every report nativeQueryRef must resolve to a measure in
  the model its definition.pbir points at), calibrated for nativeQueryRef being a display alias that can
  differ from the defined name (resolve via the projection's real measure entity, not the alias). Run it
  advisory first, confirm green on current dist in Desktop, then wire --strict into run_local_ci_check.sh.

For each: run bash tooling/run_local_ci_check.sh plus the Windows tooling/run_stage1_checks.ps1 and
tooling/quality/run_quality_gate.ps1; respect the non-bypassable TMDL/PBIR hooks (fix, never bypass);
fab config set mode command_line before non-interactive fab; use the Microsoft Learn MCP for PBIR/TMDL/DAX
detail. Commit footer: Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com> + your own Claude-Session
line. No model id in pushed artifacts; no ALUCA/Meridian co-branding. Push to the branch and open a NEW
draft PR (do NOT reuse #390 — it is merged). Start by branching from main, reading the docs, and printing
your plan + exact files for #2 before editing.
```
