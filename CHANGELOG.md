# Changelog

All notable changes to the Analytics Use Case Framework are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
- **MAJOR**: Breaking schema changes (Bracket/Factsheet/ActionCode structure)
- **MINOR**: Additive content (new use cases, new action codes, new checks)
- **PATCH**: Fixes, clarifications, metadata updates

---

## How to read this CHANGELOG

See the [v1.0.0 release](https://github.com/your-org/analytics-usecase-library/releases/tag/v1.0.0) for the complete Lean Core framework: 20 Golden strategic KPIs, 15 Impactful action codes, IR-first architecture, and end-to-end Fabric deployment pipeline.

---

## [Unreleased]

### Added

- (to be filled before next release)

### Changed

- (to be filled before next release)

### Fixed

- (to be filled before next release)

---

## [1.0.0] - 2026-04-21

**Lean Core v1.0 — Production-Ready Analytics Framework**

### Added

**Lean Core KPI Spine**
- `core/kpi_catalog/golden_20.yaml`: 20 strategic KPIs forming the Lean Core spine; all verified to exist in KPI_Catalog.md
- `core/kpi_catalog/extended_playbook.md`: 93 supporting/narrow KPIs with back-links to KPI_Catalog.md

**Impactful Action Codes**
- `core/action_codes/impactful_15.yaml`: 15 high-impact action codes spanning all domains; all verified to exist on disk
- fact_action_outcome Parquet (600 rows, 5 fiscal-year partitions) covering all 15 Impactful action codes with achieved/partial/not_achieved/pending outcomes

**Action-Outcome Measures & XD-004 Integration**
- Four outcome measures in `_Measures.tmdl` across all five domains: Actions Executed Count, Action Outcome Rate %, Avg Time-to-Outcome Days, Action ROI %
- XD-004 (Cross-Domain Action Readiness) UseCase_Bracket.yaml wired to all Impactful 15 action codes
- ActionPanel PBIP visual builder (`action_panel.py`) for dynamic action outcome rendering

**IR Pipeline & Fabric-First Architecture**
- `tooling/ir/__init__.py`: stable public re-export of IR types from generator_core (DashboardSpec, PageSpec, VisualSpec, MeasureSpec, etc.)
- `tooling/ir/schemas/dashboard_spec.schema.json`: JSON Schema for DashboardSpec; source of truth for Studio TypeScript type generation
- `tooling/generator/measures_from_ir.py`: Phase 2 Python entry point — bracket → BracketCompiler → DashboardSpec → _Measures.tmdl via PBIPAdapter
- `generate_full_report.py --bracket` flag activates IR-first mode with measure deduplication across multiple brackets

**Studio Route Groups & Registry Pages**
- (forge)/(discover, blueprint, compose, generate, brand, plugins) canonical page structure
- (registry)/(catalog, lineage, drift, health, approvals) pages with server-side scanning
- Drift detail panel with live client refresh
- Health scorecard integration (`health_scorecard.py --json` endpoint)
- Bracket governance panel with bracket selector sidebar

**MCP Write Tools & Automation**
- `execute_dax`: wraps fabric/powerbi/tooling/scripts/execute_dax.py; accepts workspace/dataset by GUID or friendly name; supports json/csv/table output
- `deploy_pbip`: chains generate_full_report.py (IR mode) → fab import to push PBIP directly to Fabric workspace
- `refresh_dataset`: POST to Fabric API groups/{ws}/datasets/{ds}/refreshes with type=Full
- `autofix_bindings`: runs validate_bindings.py in strict mode, parses ERROR lines, patches visual.json files to fix broken _Measures entity references
- All four tools registered in mcp-server.mjs manifest

**Catalog↔TMDL Drift CI Gate**
- `tooling/generator/check_catalog_tmdl_drift.py`: compares measure_name, lineage from KPI_Catalog.md against TMDL measures; produces drift_report.json artifact; exits non-zero on any drift row
- Wired into `run_stage1_checks.ps1` (Python checks section) and new catalog-tmdl-drift CI job
- Binding validation matrix: `tooling/generator/validate_bindings.py` with --domain filter for domain-scoped runs; wired into CI with matrix job per domain

**Measure Uniqueness Preflight**
- `tooling/generator/preflight_measure_names.py`: detects measure-name conflicts within the same domain across multiple brackets; orchestrator pre-Phase-2 gate

**Definition of Done & Framework Documentation**
- `DOD_WALKTHROUGH.md`: 6-step reproduction guide covering Strategy → Forge → Registry → Measure → Deploy path; includes full DoD checklist
- `KNOWN_GAPS.md`: v1.0.0 closure summary (fact_action_outcome, action-outcome loop, deploy_pbip manual workaround, DAX execution gap all closed)

**RBAC & SQLite Persistence**
- `src/lib/auth/require-role.ts` helper (requireRole(minRole, projectId))
- project_id added to bracket_lifecycle, bracket_review_comments, bracket_versions
- governance/review GET/POST now require viewer/editor role

### Changed

**IR Forced Through Fabric Path**
- IR is now the canonical representation for all Fabric deployments
- PBIPAdapter.render() produces _Measures.tmdl and visual.json from DashboardSpec
- All concrete adapters (PBIP, Metabase, Grafana, Superset) now implement validate/render/diff/deploy surface
- PBIPAdapter.diff() does TMDL byte comparison; deploy() targets Fabric REST API with Bearer token

**Consolidated Generator Tooling**
- Tooling structure refactored: `tooling/generation/` + `tooling/agent/` + `tooling/ai/` consolidated into `tooling/generator/`
- All call sites, orchestrators, CLAUDE.md, AGENTS.md, and docs updated
- All 167 Python tests pass after consolidation

**KPI Catalog Alignment to TMDL**
- `crm.revenue_at_risk.amount` catalog definition updated to match OTIF/FPY-based formula in Experience.SemanticModel
- `crm.nps.index` naming harmonized: catalog measure_name now uses "NPS Index" (aligned with TMDL and svc.nps.index); COM-003 factsheet updated

### Removed

**Build Artifacts & Legacy Scripts**
- core.zip (build artifact)
- .tmp/ (temporary artifacts)
- strategy_studio.html (legacy Studio markup)
- `generate_aurora_pbip.ps1` (replaced by IR-first pipeline)
- `watch_pbi.ps1` (deprecated daemon)
- `run_all_checks_transcript.txt` (build artifact)
- `tooling/generation/generate_{all,}_measures.ps1` (replaced by measures_from_ir.py)
- Duplicate measure generation scripts

**Deprecated KPIs**
- 6 orphan KPIs marked as deprecated in catalog:
  - fin.liquidity.payables.amount
  - ops.planned.hours
  - cost.base_volume.amount
  - cost.opex.base.amount
  - plan.replan.count
  - enterprise.action_routed.count

**Archived Experimental Phases**
- tooling/maintenance/* and internal/strategy/*2026-02*.md archived
- internal/vision/ACTIONREADY_HOLISTIC_MANIFESTO.md archived
- tooling/pbi_auto_fix_daemon.ps1 archived
- pbi_desktop_smoke_test.ps1 archived
- pbi_validate_after_impl.ps1 archived
- All archived to internal/archive/phase2_experiments/

**.tools/ Binaries**
- .tools/ binaries (dotnet/, pbi-tools/, zip) archived; add .tools/README.md with download flow
- pbi-tools version pinned in .tools/pbi-tools.lock
- .gitignore updated; run_fabric_checks.ps1 validates binary hash against lock file

### Fixed

**CI/CD & Validation**
- 3 CI workflow failures resolved (catalog drift 51→0, registry builder 3 errors→0)
- PyYAML Python resolution fixed on Windows

**Test Coverage**
- 53 total new tests green (weeks 3+4): 32 parity tests in test_ir_roundtrip.py covering BracketCompiler, PBIPAdapter.render(), TMDL generation, validate_ir, and adapter diff
- tooling/tests/test_catalog_drift.py: 7 unit tests; 11 total with test_measure_uniqueness.py
- tooling/tests/test_lean_core.py: 10 enforcement tests
- tooling/tests/test_action_outcomes.py: 26-test acceptance gate
- All 414 Python tests pass (1 pre-existing golden fixture failure unchanged)

---

## [2.1.0] — 2026-03-27

### Added

**Decision Spines — Production-Grade Governance**
- All 13 Decision Spines updated: differentiated confidence levels (High/Medium/Low) with explicit rationale
- Concrete `when_not_to_act` conditions (2–3 per spine) replacing generic delegation stubs
- Actual `org_roles.yaml` role IDs in `decision_owner_roles` and `governance.ownership`
- Domain-specific escalation actions per spine (SCM-INVENTORY, SCM-OTIF, XD-EXEC, XD-RESOURCE, XD-SERVICE)

**Strategy Patterns**
- Pattern-selection decision flowchart (§9): Q1 Cash-critical → Q2 Margin-below-plan → Q3 Growth
- Reference guardrails (§10): orientation thresholds for each pattern (e.g., GM% deviation > −2pp, DSO > +5 days)
- Urgency conflict resolution (§11): Cash-First > Margin-First > Growth-First; tie-break by financial impact

**Data Contracts**
- 4 new domain contracts: `esg.yaml`, `risk.yaml`, `efficiency.yaml`, `growth.yaml`
- `quality_rules` section added to all 8 existing domain contracts: freshness SLA, key nullability, value ranges, referential integrity

**Semantic Models**
- `aggregation_method` convention table added as header to Finance, Operations, SupplyChain Measure Dictionaries
- Tool-agnostic logical expressions (`expression.logical`) added to 15+ key ratio/balance measures
- Governance status updated from `draft` to `active`; `review_due: 2027-03-31` added to all active measures

**Business Factsheets**
- Section 10 "Typical Decision Scenarios" added to 6 priority factsheets: COM-001, COM-002, FIN-001, OPS-001, SCM-001, SCM-002
- Each scenario includes: Situation, Decision question, Who decides, Consequence of inaction, Action Code triggered
- Quantified financial impacts embedded (e.g., "8 DSO days = €3.3M tied up in receivables")

**Use Case Library Structure**
- `core/usecases/extended/README.md`: scope, criteria, naming convention, 10-item roadmap, promotion path
- `core/usecases/industry/README.md`: scope, criteria, 6 planned verticals, naming convention, promotion path

**CI/CD — New Stage 1 Checks**
- `check_measure_aggregation_methods.ps1`: validates all measures in Dictionaries have `aggregation_method`
- `check_data_contract_kpi_coverage.ps1`: validates required_facts in Brackets are covered by data contracts
- `check_usecase_page_types.ps1`: validates all Brackets declare valid page types (T1–T4)
- `check_extended_usecase_readmes.ps1`: validates extended/ and industry/ directories have README files
- `check_semantic_model_status.ps1`: warns (non-failing) when Dictionaries remain in draft > 90 days

**Framework Versioning**
- `VERSION` file introduced at repo root
- `CHANGELOG.md` introduced (this file)

**Framework Health Metrics**
- `core/strategy_operating_model/operating_model/framework_health_metrics.md`: 5 measurable health metrics, production-ready thresholds (>80%), calculation method per metric

**Maturity Model**
- `core/strategy_operating_model/operating_model/maturity_model_action_ready_analytics.md`: expanded with objective self-assessment rubric (Levels 1–5), scoring per dimension, effort estimates, and milestone checklists

### Changed

- `tooling/run_stage1_checks.ps1`: 5 new checks added; `check_semantic_model_status.ps1` added as non-failing advisory check

### Notes

Version 2.1.0 is fully backward-compatible with v2.0.0 artifact schemas (UseCase_Bracket.yaml, Business_Factsheet.md, ActionCode YAML, Decision Spine YAML). No breaking schema changes. Existing `build_ready` use cases remain valid.

---

## [2.0.0] — 2026-01-15

### Changed (Breaking)

- `UseCase_Bracket.yaml` schema upgraded from v1.x to v2.0: `orchestration.action_code_ids`, `data_contract_scope`, `reporting` sections added
- Action Code schema v2.0: `execution_bridge`, `impact_valuation`, `l1_trigger` / `l2_signal` / `l3_trigger` differentiation
- Decision Spine schema v1.0: introduced as governance layer above Action Codes

### Added

- 15 Core Use Cases with v2.0 Brackets across 7 domains
- 64 Action Codes in 6 domains (Commercial, Finance, Operations, Supply Chain, People, Enterprise)
- 12 Decision Spines (one per strategic domain pair)
- Stage 1 CI pipeline with 13 validation checks
- Core Constitution, Golden Thread Narrative, Operating Model documentation

---

## [1.0.0] — 2025-06-01

Initial framework release.

- 10 Core Use Cases (v1.x Bracket schema)
- 30 Action Codes
- KPI Catalog v1
- Basic CI validation (factsheet schema check only)
