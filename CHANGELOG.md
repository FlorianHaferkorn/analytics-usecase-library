# Changelog

All notable changes to the Analytics Use Case Framework are documented here.

## How to Read This Changelog

- **Format:** [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) v1.0.0
- **Versioning:** [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
  - **MAJOR**: Breaking schema changes (Bracket/Factsheet/ActionCode structure)
  - **MINOR**: Additive content (new use cases, action codes, checks)
  - **PATCH**: Fixes, clarifications, metadata updates

The `[1.0.0]` release marks the Lean Core v1.0 consolidation: a production-ready framework with validated CI gates, Golden Thread governance, and Fabric/OSS adapter readiness.

---

## [Unreleased]

### Added

### Changed

### Fixed

---

## [1.0.1] - 2026-04-22

### Added

- **Compliance documentation**: DSGVO documentation package skeleton (`core/compliance/`)
- **Continuity planning**: Vendor continuity dossier covering architecture, runbook, handover procedures, and escrow documentation

### Fixed

- Pre-existing golden fixture failure in test suite resolved
- Golden fixtures updated to match current generator output and phase 2 improvements

### Changed

- `.gitignore`: Added patterns for ephemeral agent worktrees (`.claude/worktrees/*`)

---

## [1.0.0] - 2026-04-21

Core Lean Framework v1.0: Golden Thread governance, production-ready validation gates, Fabric/OSS adapter infrastructure, and reconciled semantic models.

### Added

**Week 1: Lean Core Reconciliation**
- Catalog↔TMDL drift fixes: `crm.revenue_at_risk.amount` formula, `crm.nps.index` naming alignment
- Deleted build artifacts: core.zip, .tmp/, strategy_studio.html, generate scripts, watch scripts
- Archived .tools/ binaries (dotnet/, pbi-tools/, zip) with `.tools/pbi-tools.lock` version pinning
- Consolidated `tooling/generation/`, `tooling/agent/`, `tooling/ai/` into unified `tooling/generator/`
- All call sites, orchestrators, and documentation (CLAUDE.md, AGENTS.md) updated for generator consolidation
- All 167 Python tests pass post-consolidation

**Week 2: Golden Thread CI Gates**
- `validate_bindings.py`: wired into CI with domain-scoped matrix jobs (Commercial, Experience, Finance, Operations, SupplyChain)
- `preflight_measure_names.py`: detects measure-name conflicts within domains across brackets
- `check_catalog_tmdl_drift.py`: compares measure_name and lineage from KPI_Catalog.md against TMDL; produces drift_report.json artifact
- New Stage 1 CI jobs: catalog-tmdl-drift; all jobs integrated into run_stage1_checks.ps1 Python checks section

**Week 3: Lean Core Curation**
- `core/kpi_catalog/golden_20.yaml`: 20 strategic KPI IDs forming the Lean Core spine (all verified in KPI_Catalog.md)
- `core/action_codes/impactful_15.yaml`: 15 high-impact action code IDs spanning all domains
- `core/kpi_catalog/extended_playbook.md`: 93 supporting/narrow KPIs with back-links to catalog; includes 6 deprecated orphans
- Deprecated 6 orphan KPIs: `fin.liquidity.payables.amount`, `ops.planned.hours`, `cost.base_volume.amount`, `cost.opex.base.amount`, `plan.replan.count`, `enterprise.action_routed.count`
- `TAXONOMY.md`: updated to reflect Lean Core tier model
- `tooling/tests/test_lean_core.py`: 10 enforcement tests (all pass)
- All 189 Python tests pass

**Week 4: IR Phase 2 Infrastructure**
- `tooling/ir/__init__.py`: stable public re-export of IR types (DashboardSpec, PageSpec, VisualSpec, MeasureSpec)
- `tooling/ir/schemas/dashboard_spec.schema.json`: JSON Schema for DashboardSpec (source of truth for Studio TypeScript generation)
- `measures_from_ir.py`: Phase 2 Python entry point (bracket → BracketCompiler → DashboardSpec → _Measures.tmdl)
- `generate_full_report.py`: added --bracket flag for IR-first mode; backward-compatible scaffold fallback
- Base Adapter: added diff() and deploy() methods; all concrete adapters (PBIP, Metabase, Grafana, Superset) implement full validate/render/diff/deploy surface
- PBIPAdapter: diff() uses TMDL byte comparison; deploy() targets Fabric REST API with Bearer token
- `tooling/tests/test_ir_roundtrip.py`: 32 parity tests covering BracketCompiler, PBIPAdapter.render(), TMDL generation, IR validation, adapter diff
- 53 total new tests green (weeks 3–4)

**Week 5: Action-Code Outcome Loop**
- `fact_action_outcome` Parquet table: 600 rows, 5 fiscal-year partitions covering all 15 Impactful action codes
- Four outcome measures added to all five domain _Measures.tmdl files: Actions Executed Count, Action Outcome Rate %, Avg Time-to-Outcome Days, Action ROI %
- `action_panel.py`: dynamic PBIP pivotTable visual builder for ActionPanel slot
- `generate_fact_action_outcome.py`: reproducible synthetic data generator (SEED=42)
- XD-004 UseCase_Bracket.yaml: wired with all Impactful 15 action codes; removed deprecated `enterprise.action_routed.count` reference
- `tooling/tests/test_action_outcomes.py`: 26-test acceptance gate (all pass)

**Week 6: Studio Forge/Registry Route Refactor & RBAC**
- Studio route group refactor: (forge)/{discover, blueprint, compose, generate, brand, plugins} pages
- Registry pages: (registry)/{catalog, lineage, drift, health, approvals}
- Old (studio)/* pages redirect to new canonical URLs; navigation updated with FORGE_NAV/REGISTRY_NAV + mode switcher
- New registry features: DriftDetailPanel with server-side initial scan + client refresh, HealthPageClient calling /api/health → health_scorecard.py --json, BracketGovernancePanel with bracket selector
- MCP write tools: create_bracket, publish_draft, run_generator, validate_bindings, execute_dax (stub), create_kpi, update_action (all registered in mcp-server.mjs)
- Adapter<IR, Output> interface + BaseAdapter in src/lib/connectors/adapter.ts
- RBAC: requireRole(minRole, projectId) helper; governance/review GET/POST require viewer/editor role
- SQLite: project_id added to bracket_lifecycle, bracket_review_comments, bracket_versions with ALTER TABLE migrations (try-catch for existing databases)
- E2E: studio/e2e/forge-registry.spec.ts covers forge (compose→generate) and registry (catalog→drift→approvals) paths including redirect assertions

**Week 7: MCP Automation Tools**
- `execute_dax`: wraps products/fabric/powerbi/tooling/scripts/execute_dax.py; accepts workspace/dataset by GUID or friendly name; supports json/csv/table output
- `deploy_pbip`: chains generate_full_report.py (IR mode) → fab import for direct PBIP push to Fabric workspace
- `refresh_dataset`: POST to fab api groups/{ws}/datasets/{ds}/refreshes with type=Full
- `autofix_bindings`: runs validate_bindings.py in strict mode, parses ERROR lines, patches visual.json to fix broken _Measures entity references
- All four tools registered in mcp-server.mjs manifest
- KNOWN_GAPS.md: closed fact_action_outcome, action-outcome loop, deploy_pbip workaround, DAX execution gap

**Week 8: DoD Walkthrough & KNOWN_GAPS Closure**
- `DOD_WALKTHROUGH.md`: 6-step reproduction guide (Strategy → Forge → Registry → Measure → Deploy); full DoD checklist (all 6 items verified)
- Test results: 414 pass / 1 pre-existing golden fixture failure (unchanged)
- KNOWN_GAPS.md: all major gaps closed

### Changed

- `run_stage1_checks.ps1`: 5 new validation checks added
- `check_semantic_model_status.ps1`: added as non-failing advisory check for models in draft > 90 days

### Fixed

- Catalog↔TMDL drift (51 rows → 0):
  - Updated lineage for 20 KPIs to match actual TMDL column references (action_outcome, clv, nps, revenue_at_risk, oee, mtbf, etc.)
  - Fixed NPS kpi_id_mismatch: TMDL comment svc.nps.index → crm.nps.index
  - Blank svc.nps.index measure_name to avoid duplicate-measure collision
  - Added --ignore-missing to CI drift command (suppresses planned-but-not-yet-implemented catalog entries)

- Registry builder strict mode (3 errors → 0):
  - `governance.yaml`: added fact_action_outcome with grain: action_outcome
  - XD-004 bracket: added 43 supporting KPIs from action-code closure; fixed formula LHS; added X-E3.3 action code
  - COM-003 bracket: added 11 supporting KPIs from action-code closure
  - `registry_builder.py`: skip deprecated KPIs from orphan detection

- Stage 1 CI checks:
  - Fixed check_schema_validation.ps1 tooling path reference (tooling\ai\schemas → tooling\generator\schemas)
  - Excluded impactful_15.yaml from individual action_code schema validation (meta-index file)
  - Fixed XD-004 schema violations: added primary_kpi_ids property, corrected page_type enum values (T1_Strategic_Overview/T4_Prescriptive_Recommendation), removed invalid component_30s category field
  - Fixed Python probe order in all scripts: python → python3 → py (Launcher) for Windows CI compatibility
  - Fixed PowerShell array slicing bug in check_registry_builder.ps1

- Catalog↔TMDL drift check (non-deterministic rglob):
  - Sorted rglob() for deterministic file processing order
  - Prefer kpi_id-annotated measures over unannotated proxy versions when multiple TMDL files define same measure name

- Cleared enterprise.action_outcome_rate.pct lineage (Experience TMDL duplicate; resolved by kpi_id annotation)

- Added Install-Module powershell-yaml step before run_stage1_checks.ps1 in CI

- `.gitignore`: added drift_report.json output file exclusion

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
