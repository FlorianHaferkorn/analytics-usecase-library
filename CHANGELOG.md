# Changelog

All notable changes to the Analytics Use Case Framework are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
- **MAJOR**: Breaking schema changes (Bracket/Factsheet/ActionCode structure)
- **MINOR**: Additive content (new use cases, new action codes, new checks)
- **PATCH**: Fixes, clarifications, metadata updates

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
