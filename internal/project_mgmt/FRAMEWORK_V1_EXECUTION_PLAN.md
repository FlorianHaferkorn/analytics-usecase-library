# Framework v1.0 Execution Plan — "Lean Core & EcoPulse DoD"

**Owner of execution:** Claude Sonnet 4.6 (model id `claude-sonnet-4-6`)
**Source audit:** commit on branch `claude/audit-bi-framework-pwmGJ` (Opus 4.7 audit, 2026-04-20)
**Timebox:** 8 calendar weeks
**Repository:** `florianhaferkorn/analytics-usecase-library`

---

## 0. Definition of Done (non-negotiable)

A commit on `main` with all of the following green:

1. `rm -rf products/fabric/powerbi/dist/` followed by the orchestrator command regenerates **15 Aurora reports** with **zero errors**, from a single IR pass (no direct bracket-YAML parsing in Phase 2/5).
2. **Golden Thread** validators pass:
   - `validate_tmdl_style.sh` (no violations)
   - `validate_pbir_structure.sh` (no violations)
   - `products/fabric/powerbi/tooling/validate_bindings.py --strict` (0 errors, wired into CI)
   - new `tooling/validation/check_catalog_tmdl_drift.py` (0 drift rows)
3. **Action-code outcome loop** is live: every report in the Impactful 15 has a non-BLANK `[Action Outcome Rate %]` measure and a dynamic `ActionPanel` that renders rows from `fact_action_outcome` (no hard-coded action-code text).
4. **Lean Core v1.0** is the authoritative catalog: `core/kpi_catalog/golden_20.yaml` + `core/action_codes/impactful_15.yaml` exist and are referenced by Aurora without any hard-coded orphan KPI.
5. **Studio** has `(forge)/` and `(registry)/` route groups, and `studio/mcp-server.mjs` exposes `create_bracket`, `publish_draft`, `run_generator`, `validate_bindings`, `execute_dax` write-tools.
6. All `.claude/` hooks stay green throughout execution — no `--no-verify`, no hook bypass.

---

## 1. Branch & Commit Discipline

- Create per-week feature branches off `main`: `v1.0/week-1-cleanup`, `v1.0/week-2-ci-gates`, … `v1.0/week-8-dod-run`.
- **Never** amend or force-push. Always `git push -u origin <branch>`; retry 4x on network error with backoff 2s/4s/8s/16s.
- Conventional commit prefixes: `fix:`, `refactor:`, `feat:`, `docs:`, `chore:`, `test:`.
- Each week closes with a merged PR back into `main`; PR body must list the week's exit criteria and paste validator output.
- After each merge, rebase the next week's branch onto `main` before starting work.

---

## 2. Week-by-Week Tasks

### Week 1 — Reconcile & Cleanup

**Goal:** eliminate ~762 MB of bloat and fix the two catalog-TMDL drifts.

| Task | Files | Acceptance |
|---|---|---|
| Fix `crm.revenue_at_risk.amount` drift | `products/fabric/powerbi/dist/Experience.SemanticModel/definition/tables/_Measures.tmdl` (measure `Revenue at Risk Amount`, ~lines 245-257) | DAX matches catalog definition `CLV Remaining × Attrition Risk %` OR catalog is updated and both agree. Unit test in `tooling/tests/test_catalog_drift.py`. |
| Fix NPS naming drift | `core/kpi_catalog/KPI_Catalog.md:183` vs `products/fabric/powerbi/dist/Experience.SemanticModel/.../⁠_Measures.tmdl:60` | All layers read `NPS Index` (catalog, TMDL, all brackets). |
| Delete build artifacts | `core.zip`, `.tmp/`, `strategy_studio.html`, `generate_aurora_pbip.ps1`, `watch_pbi.ps1`, `internal/reviews/run_all_checks_transcript.txt`, `tooling/generation/generate_all_measures.ps1`, `tooling/generation/generate_measures.ps1` | Files gone; `git grep` confirms no live references. |
| Archive `.tools/` | Move to `.tools/README.md` describing download flow; delete binaries | Repo shrinks by ~758 MB; CI documentation updated in `CONTRIBUTING.md`. |
| Archive obsolete internal docs | `internal/archive/{docs,products,tooling}/` (keep `framework_evolution.md` as anchor), `internal/strategy/*2026-02*.md`, `internal/vision/ACTIONREADY_HOLISTIC_MANIFESTO.md`, `tooling/pbi_auto_fix_daemon.ps1`, `pbi_desktop_smoke_test.ps1`, `pbi_validate_after_impl.ps1`, `tooling/maintenance/*` | Moved to `internal/archive/phase2_experiments/` or deleted with `git rm`. |
| Consolidate tooling tree | Merge `tooling/generation/` + `tooling/agent/` + `tooling/ai/` → `tooling/generator/`; update all call sites and CLAUDE.md | `run_stage1_checks.ps1` still passes; no path is referenced from more than one location. |
| Pin pbi-tools | `.tools/pbi-tools.lock` with sha256 + version; update `run_fabric_checks.ps1` to validate before use | Orchestrator fails fast if binary hash mismatches. |

**Exit gate Week 1:** `.\tooling\run_stage1_checks.ps1` green; repo size under 80 MB (excluding `.git`).

---

### Week 2 — Golden Thread CI Gates

**Goal:** no more silent drift.

| Task | Files | Acceptance |
|---|---|---|
| Wire `validate_bindings.py` into CI | `.github/workflows/stage1.yml`: add matrix step per domain | CI fails on any unbound visual in any of 15 reports. |
| Measure-name uniqueness pre-flight | New `tooling/generator/preflight_measure_names.py`; invoke from Phase 2 of `orchestrate_full_model.ps1` | Orchestrator aborts with clear error when two brackets declare the same measure name within one domain. |
| Catalog↔TMDL semantic diff validator | New `tooling/validation/check_catalog_tmdl_drift.py` comparing `technical.measure_name`, `depends_on_measures`, `lineage` against parsed TMDL; wire into `run_stage1_checks.ps1` AND `stage1.yml` | Exits non-zero on any drift row; produces `drift_report.json` artifact for Studio `(registry)/drift/`. |
| Add unit tests | `tooling/tests/test_catalog_drift.py`, `test_measure_uniqueness.py` | `python3 -m pytest tooling/tests/ -q` green. |

**Exit gate Week 2:** all three validators wired into `.github/workflows/stage1.yml`; sample drift intentionally injected in a test branch produces CI failure.

---

### Week 3 — Lean Core Curation

**Goal:** Golden 20 and Impactful 15 are the authoritative spine.

| Task | Files | Acceptance |
|---|---|---|
| Publish Golden 20 | `core/kpi_catalog/golden_20.yaml` — list of 20 kpi_ids from audit §2A with rationale | Every entry exists in `KPI_Catalog.md`; enforced by new pytest. |
| Publish Impactful 15 | `core/action_codes/impactful_15.yaml` — list of 15 action_code_ids from audit §2B | Every entry exists under `core/action_codes/`. |
| Extended Playbook split | `core/kpi_catalog/extended_playbook.md` — move 78 narrow/supporting KPIs there with back-link | `KPI_Catalog.md` now holds Lean Core only; registry builder reads both. |
| Deprecate true orphans | Remove from catalog: `fin.liquidity.payables.amount`, `ops.planned.hours`, `cost.base_volume.amount`, `cost.opex.base.amount`, `plan.replan.count`, `enterprise.action_routed.count` | No bracket / action code / TMDL references remain. |
| Regenerate Aurora | `.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -All -UseAuroraData` | 15 reports still build; no measure missing. |
| Taxonomy update | `TAXONOMY.md`, `README.md`, `CLAUDE.md` — reflect Lean Core + Extended Playbook tiers | Docs match code. |

**Exit gate Week 3:** Aurora regenerates from Lean Core + Extended Playbook; `check_catalog_tmdl_drift.py` still green.

---

### Week 4 — Force IR through the Fabric path

**Goal:** kill the Fabric-bypass-IR problem — Phase 2 and Phase 5 must consume `DashboardSpec`.

| Task | Files | Acceptance |
|---|---|---|
| Extract shared IR | New `tooling/ir/` Python package exporting `DashboardSpec`, `PageSpec`, `VisualSpec`, `MeasureSpec`; move from `tooling/generator_core/ir/specs.py` | `studio/src/lib/ir/` imports the same types via generated TS (from `ir_v1.schema.json`). |
| Rewrite Phase 2 | `tooling/generator/generate_tmdl_measures.ps1` → call new `tooling/generator/measures_from_ir.py` | Measures generated from IR, not from bracket YAML directly. |
| Rewrite Phase 5 | `products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py` → consume IR `PageSpec` list | Reports generated from IR; no direct `config_loader.py` YAML parse in page emitter. |
| Connect dead `PBIPAdapter.render()` | `products/fabric/powerbi/tooling/adapters/pbip.py` | Adapter is the only emitter of TMDL+PBIR from IR. |
| Retrofit OSS adapters | `products/oss_adapters/tooling/adapters/{metabase,grafana,superset}.py` | All implement `validate()`, `render()`, `diff()`, `deploy()` on the same `DashboardSpec`. |
| Parity test | `tooling/tests/test_ir_roundtrip.py`: bracket YAML → IR → TMDL text diff against golden copies | 15/15 reports byte-identical (modulo whitespace) to pre-refactor output. |

**Exit gate Week 4:** orchestrator only calls `adapter.render(spec)`; no script grep-matches `yaml.safe_load` outside the IR loader.

---

### Week 5 — Action-Code Outcome Loop (DoD-critical)

**Goal:** prove action codes move KPIs.

| Task | Files | Acceptance |
|---|---|---|
| Outcome measures | Add to every domain `_Measures.tmdl`: `[Actions Executed Count]`, `[Action Outcome Rate %]`, `[Avg Time-to-Outcome Days]`, `[Action ROI %]` | Non-BLANK for all 15 Impactful action codes on Aurora data. |
| `fact_action_outcome` data | `showcases/aurora_group/data/gold/facts/fact_action_outcome/` synthetic Parquet (5-year partitions, seeded) + dim table | Partitions match other fact tables; `generate_missing_facts.py` extended. |
| Dynamic ActionPanel | `products/fabric/powerbi/tooling/page_scaffold_generator/visuals/action_panel.py` — render a matrix visual bound to `fact_action_outcome` filtered by current use case | ActionPanel shows L1/L2/L3 recommendations with live outcome metrics; no hard-coded YAML text. |
| XD-004 governance view | `core/usecases/core/XD-004_Executive_Action_Governance/UseCase_Bracket.yaml` report shows outcome rate per Impactful 15 action code | Overview KPI card: `[Action Outcome Rate %]` aggregate across all 15. |
| Outcome CI test | `tooling/tests/test_action_outcomes.py` executes DAX via `fab api` (or offline `pbi-tools`) and asserts non-BLANK results | Fails CI if any Impactful action code has BLANK outcome. |

**Exit gate Week 5:** outcome loop demo on XD-004 shows at least one L1/L2/L3 recommendation per Impactful action code with non-BLANK outcome metrics.

---

### Week 6 — Studio Forge/Registry Split

**Goal:** the SaaS Studio shape supports CDAO, BI Lead, Data Steward roles.

| Task | Files | Acceptance |
|---|---|---|
| Route group refactor | `studio/src/app/(forge)/{discover,blueprint,compose,generate}/` and `studio/src/app/(registry)/{catalog,lineage,drift,health,approvals}/` | Existing 8 pages migrated; navigation reflects two modes. |
| Drift UI | `studio/src/app/(registry)/drift/page.tsx` reading `drift_report.json` from Week 2 validator | Table of drift rows with domain filter; zero rows for green main. |
| Health scorecard wrap | `studio/src/app/(registry)/health/page.tsx` calling `tooling/health_scorecard.py` via `/api/health` | Renders scorecard; refreshable. |
| MCP write tools | `studio/mcp-server.mjs` + `studio/src/lib/mcp/tools.ts` add: `create_kpi`, `create_bracket`, `update_action`, `publish_draft`, `run_generator(connector, use_case_id)`, `validate_bindings`, `execute_dax` | All tools documented in MCP manifest; E2E test in `studio/e2e/mcp.spec.ts`. |
| `Adapter<IR, Output>` interface | `studio/src/lib/connectors/adapter.ts` with `validate / render / diff / deploy`; retrofit fabric, oss, cicd | Each connector implements all four methods. |
| RBAC enforcement | `studio/src/lib/auth/require-role.ts` + apply to every `(registry)/*` API route | Non-admin requests to `/api/governance/*` return 403. |
| Project scoping | Add `project_id` column to all SQLite tables; middleware enforces from JWT claim | Single-tenant still works; multi-tenant prep complete. |

**Exit gate Week 6:** Playwright run covers Forge path (compose → generate) and Registry path (catalog → drift → approve) for a new use case without any shell invocation.

---

### Week 7 — MCP/AOS Automation Wins

**Goal:** replace manual PowerShell ops with MCP tools.

| Task | Files | Acceptance |
|---|---|---|
| `execute_dax` MCP | `studio/mcp-server.mjs` wraps `fab api groups/$WS_ID/datasets/$MODEL_ID/executeQueries` | Unit test returns known Golden 20 measure value for Aurora workspace. |
| `deploy_pbip` MCP | Imports PBIP via `fab import` after building from IR | Replaces manual Desktop first-open workaround documented in `KNOWN_GAPS.md` §2. |
| `refresh_dataset` MCP | Wraps Full refresh `fab api .../refreshes -X post` | Works against Aurora dev workspace. |
| `autofix_bindings` MCP | Parses `validate_bindings.py` output → proposes patch to visual.json → writes via PBIR tools | On synthetic broken binding, emits a valid patch that restores binding. |
| Retire duplicated scripts | Delete `tooling/pbi_validate_after_impl.ps1`, thin wrappers | No live references. |

**Exit gate Week 7:** running `studio mcp run_generator --connector fabric --use-case COM-001` followed by `deploy_pbip` produces a refreshed Aurora workspace report without opening Power BI Desktop.

---

### Week 8 — DoD Run

**Goal:** prove it end-to-end.

| Task | Files | Acceptance |
|---|---|---|
| Clean-room rebuild | `rm -rf products/fabric/powerbi/dist/`; run `.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -All -UseAuroraData` | 15 reports generated, all validators green, no manual steps. |
| End-to-end CI run | Trigger `.github/workflows/stage1.yml` on clean branch | All jobs green, including `validate_bindings`, `check_catalog_tmdl_drift`, `test_action_outcomes`. |
| Aurora walkthrough recording | `internal/project_mgmt/DOD_WALKTHROUGH.md` — step-by-step from Strategy → Forge/compose → generate → deploy → measure outcome | Reviewer can reproduce from the doc alone. |
| Retire `KNOWN_GAPS.md` items 1, 2, 5 | Mark fact tables complete, theme automated, CI wired | Doc reflects new reality. |
| Release tag | `git tag -a v1.0.0 -m "Lean Core & EcoPulse DoD"` | Pushed; GitHub release created via MCP. |

**Exit gate Week 8 (= DoD):** all six items in §0 pass in one CI run on `main`; release `v1.0.0` is published.

---

## 3. Execution Rules for Sonnet 4.6

1. **Read the audit first.** Commit `HEAD` on `claude/audit-bi-framework-pwmGJ` contains the full audit rationale — read it before touching code.
2. **Respect `.claude/hooks/`.** Never bypass `validate_tmdl_style.sh` or `validate_pbir_structure.sh`. If a hook blocks, fix the root cause.
3. **Run from the repo root.** All PowerShell and Python commands assume CWD = repo root.
4. **TMDL hard rules** (from `CLAUDE.md`): tabs only; `=` not `:=`; `/// Purpose:` comments not `description:`; numeric columns always `summarizeBy: none`; measures always `formatString`. Spaghetti layout: `_Measures` at (0,0), facts horizontal at y=0, dims vertical at x=0.
5. **Preserve bracket YAML frontmatter** (`id`, `factsheet_type: business`) and all schema-required sections.
6. **Only reference KPIs that exist in `core/kpi_catalog/`.** Do not redefine KPI meaning in brackets or TMDL.
7. **Update `KNOWN_GAPS.md`** whenever a gap is closed — do not let it rot.
8. **After every validation failure**, consult `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`; add new error classes.
9. **Prefer editing existing files** over creating new ones unless the task explicitly requires a new file.
10. **No CHANGELOG / README bloat.** Keep docs lean; retire superseded ones.

---

## 4. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Week 4 IR rewire breaks byte-identity | Golden-copy the 15 current reports before starting; diff after each task. |
| Week 5 outcome data unavailable | Ship synthetic `fact_action_outcome` Parquet as Aurora seed; flag provisional in `KNOWN_GAPS.md`. |
| Week 6 Studio regression | Playwright snapshot suite must pass before each Studio PR merges. |
| Week 7 Fabric auth flakiness | `fab auth login` in CI uses service-principal; document fallback in `CONTRIBUTING.md`. |
| Week 8 hidden flakiness | Clean-room rebuild must be run on a fresh CI runner, not local dev, before tagging `v1.0.0`. |

---

## 5. Rollback

Each weekly branch is mergeable independently; if any week's PR fails post-merge, revert with `git revert <merge-sha> -m 1` on `main` and restart the week on a fresh branch. **Never** `git reset --hard` on `main`.

---

**Ready signal:** when Week 8 exit gate passes, open `internal/project_mgmt/DOD_WALKTHROUGH.md` and tag the CDAO for sign-off. End of v1.0 scope.
