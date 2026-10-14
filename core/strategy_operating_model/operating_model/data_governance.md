# Data Governance

Data governance ensures that analytical meaning, quality, and trust are preserved across the Action-Ready Analytics Framework.

While the Golden Thread defines causal logic and the Operating Model governs its operation, data governance protects the underlying data and semantic foundations.
It does not define strategy, KPIs, or decisions.
It ensures that these remain reliable as data and systems evolve.

## 1. Role in the Framework

Data governance operationalizes trust within the analytics system.

- Strategy, KPIs, and use cases define intent.
- Semantic models and measures express this intent.
- Data governance ensures that underlying data remains consistent, secure, and interpretable.

Governance acts as a safeguard for meaning, not as a delivery control mechanism.

## 2. Governance Principles

Data governance follows a small set of binding principles.

Ownership is explicit.
Every governed asset has an accountable owner responsible for meaning, quality, and evolution.

Quality is measurable.
Data completeness, correctness, timeliness, and stability are monitored against explicit expectations.

Security is intentional.
Access follows the principle of least privilege, and sensitive data is handled explicitly.

Lineage is transparent.
KPIs and measures are traceable to their underlying data contracts and semantic models.

## 3. Scope of Governance

Governance applies to assets that influence analytical meaning and decision-making.

This includes:

- data contracts and schemas,
- semantic models and measures,
- KPI definitions and catalogs,
- and action-related signals.

Governance is not applied uniformly.
Only assets with semantic or decision impact are governed.

## 4. Normative Governance Standards

Data governance defines binding standards for how analytical assets are managed.

### 4.1. Ownership

Each governed asset has a clearly assigned owner.
Ownership is accountable and does not depend on tooling or organizational structure.

### 4.2. Data Quality

Quality expectations are defined explicitly.
Validation rules ensure referential integrity, completeness, and consistency with semantic definitions.

### 4.3. Security and Access

Access to analytical data follows least-privilege principles.
Personally identifiable and sensitive data is classified and handled explicitly.

### 4.4. Lineage and Traceability

All governed assets are traceable across layers.
Lineage supports interpretation, validation, and impact assessment.

## 5. Governance and Validation

Governance is enforced through validation rather than manual control.

Checks ensure alignment with:

- data contracts,
- semantic and measure standards,
- and governance rules.

Validation protects consistency and trust.
It does not introduce procedural overhead.

## 6. Change and Impact Awareness

Governance ensures that changes are transparent and intentional.

Changes to schemas, KPIs, access rules, or semantics are evaluated for impact.
Only affected assets are reviewed or adjusted.

This prevents silent breakage and uncontrolled drift as analytics evolves.

## 7. Artifact Design Laws

The framework enforces a small set of non-negotiable design laws across all governed artifacts.
These laws are derived from the [ActionReady Holistic Manifesto](../../../internal/archive/phase2_experiments/vision/ACTIONREADY_HOLISTIC_MANIFESTO.md) and apply uniformly.

### 7.1. Separation of Concerns

YAML artifacts are machine-readable configuration.
Markdown files are human-readable context.

Machine-readable data (KPI subscriptions, action code references, trigger logic) lives exclusively in YAML:
`UseCase_Bracket.yaml`, Action Code YAMLs, KPI Catalog entries, and Data Contracts.

Markdown factsheets provide narrative context only.
They must not duplicate machine-readable blocks that exist in YAML.

### 7.2. Single Source of Truth (SSOT)

Each governed concept has exactly one authoritative location:

| Concept | SSOT |
|---|---|
| KPI definitions | `core/kpi_catalog/KPI_Catalog.md` |
| Action logic & triggers | `core/action_codes/**/*.yaml` |
| Use case subscriptions | `core/usecases/**/UseCase_Bracket.yaml` |
| Semantic model structure | `semantic_models/` |
| Data contracts | `data_contracts/` |

Derived outputs (`master_registry.json`, `value_map.json`, measure dictionaries) are generated from these sources.
They are consumed but never hand-edited.

### 7.3. Transitive Integrity & Orphan Policy

A KPI is considered active if it is referenced by any active `UseCase_Bracket.yaml` or by any Action Code subscribed by an active bracket (transitive linkage).

An artifact that is not reachable through this transitive chain is an orphan.
Orphans are extracted and archived immediately, not deferred.

### 7.4. Roles, Not Names

Governance ownership is assigned to roles (`owner_role`, `steward_role`), not to named individuals.
This ensures accountability survives organizational change.

Every governed artifact requires both an `owner_role` (accountable for meaning and targets) and a `steward_role` (accountable for data quality and implementation).
These roles must not be identical.

### 7.5. Zero-Tolerance Gatekeeping

The Registry Engine (`tooling/ontology/registry_builder.py`) is the automated integrity gate.
It validates referential integrity, governance completeness, and transitive linkage.

In `--strict` mode, any validation failure blocks the commit (enforced via pre-commit hook).
Consistency is required; partial correctness is not accepted.

## 8. Framework Audit & Continuous Governance

The framework enforces governance through automated audit rather than manual review.

### 8.1. Registry Engine

The Registry Engine scans all governed artifacts and produces:

| Output | Purpose |
|---|---|
| `master_registry.json` | Complete object graph with resolved links and trust scores |
| `orphans_report.json` | Unreferenced KPIs, action codes, and use cases |
| `governance_gaps.json` | Missing or conflicting governance roles |
| `value_map.json` | Impact-path linkage and valuation metadata |
| `action_text_preview.txt` | Human-readable action text for Power BI panels |

These outputs are generated deterministically from governed sources.
They are never hand-edited.

### 8.2. Validation Pipeline

Governance is enforced in two stages:

**Stage 1 (CI gate):** `tooling/run_stage1_checks.ps1`
Schema validation, factsheet integrity, KPI catalog rules, action code consistency, decision spine alignment, duplicate IDs, SSOT markers, and doc references.

**Registry audit:** `tooling/ontology/registry_builder.py --strict`
Referential integrity, transitive linkage, governance gaps, strategic KPI role checks, value-driver formula validation, and causal link coverage.

Both run as pre-commit hooks for continuous governance.

### 8.3. Pre-Commit Enforcement

The versioned pre-commit hook (`.githooks/pre-commit`) runs the Registry Engine in strict mode whenever `core/` files are staged.
Activation: `git config core.hooksPath .githooks` (set by the Claude Code SessionStart hook; on Windows `tooling/git-hooks/install_precommit.ps1`).

Failed validation blocks the commit.
This ensures the repository never contains broken links or ungoverned artifacts.

## 9. Trust Signals & Data Contract Risk

Trust is quantified, not assumed.

### 9.1. Trust Score

The Registry Engine computes a `trust_score` for each KPI based on:
- validation results (`tooling/validation/results/latest_results.json`),
- data contract coverage,
- and governance completeness.

A `trust_score` of 0 means the KPI is untrusted.
Consumers (agents, reports) must flag untrusted KPIs and must not claim realized impact.

### 9.2. Data Contract Risk

If a used KPI has no linked domain contract, the registry assigns `data_contract_risk: "high"`.

This signal propagates to consumers:
- AI agents must label recommendations as "data quality at risk".
- Reports should surface a data quality warning.

Trust signals are produced automatically during registry builds and are consumed by agents and validation pipelines.

## 10. Outcome

When applied consistently, data governance ensures that:

- analytical results are trusted and explainable,
- changes do not silently alter meaning,
- governance is enforced through automation, not manual process,
- orphans and broken links are detected and resolved immediately,
- and compliance requirements are met without slowing delivery.

Data governance enables scale by protecting trust, not by enforcing control.

---

## Sources & Grounding

The governance model in this document — explicit ownership, measurable data quality,
least-privilege security, lineage/traceability, and change-impact awareness — is grounded
in the established bodies of knowledge and standards for data management and IT governance:

- **Data management framework & knowledge areas** (data governance, data quality, security,
  metadata/lineage as DAMA knowledge areas) — DAMA International, DAMA-DMBOK (Data Management
  Body of Knowledge): <https://dama.org/learning-resources/dama-data-management-body-of-knowledge-dmbok/>
- **Governance and management of enterprise IT** (governance vs. management separation,
  governance objectives) — ISACA, COBIT 2019: <https://www.isaca.org/resources/cobit>
- **Corporate governance of information technology** (board/executive accountability for IT;
  responsibility, strategy, conformance principles) — ISO/IEC 38500:2024, Governance of IT for
  the organization: <https://www.iso.org/standard/81684.html>
- **Data quality** (measurable quality expectations, completeness, accuracy) — ISO 8000-1:2022,
  Data quality — Part 1: Overview: <https://www.iso.org/standard/81745.html>
- **Personal data protection** (classification and explicit handling of personally identifiable
  and sensitive data; least-privilege access) — Regulation (EU) 2016/679 (GDPR), official
  consolidated text on EUR-Lex: <https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng>

> Governance here safeguards analytical *meaning, quality, and trust*; it does not define
> strategy or KPIs (see §1). Enforcement is automated via the Registry Engine and CI gates (§8).
