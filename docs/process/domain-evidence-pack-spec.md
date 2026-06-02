# Domain Evidence Pack — Artifact Specification

> **Version:** 1.0 (Draft — not yet enforced in Core schemas)  
> **Status:** Proposal  
> **Authority:** Framework Architect approval required before Core schema enforcement  
> **Related:** `docs/process/research-to-core-standard.md` | `docs/process/gap-classification.md`

---

## Purpose

A Domain Evidence Pack (DEP) is the single traceable record of why a use case contains what it contains.
It stores the source inventory, extracted domain knowledge, driver tree, action logic, and mapping readiness for one use case.

This document specifies the intended artifact shape. It is a proposal only. No Core schema (`usecase_bracket.schema.json`, `kpi_definition.schema.json`, `action_code.schema.json`) is changed by this document.

---

## 1. Artifact Location and Naming Convention

```
core/usecases/core/<UseCase_ID>_<Title>/
  Business_Factsheet.md          # Existing — prose business context
  UseCase_Bracket.yaml           # Existing — machine-readable SSOT
  Domain_Evidence_Pack.yaml      # New — domain research record (this artifact)
```

The DEP file **does not replace** any existing artifact. It sits alongside them.

---

## 2. Evidence Pack Schema (YAML Proposal)

```yaml
# Domain Evidence Pack
# This file records the domain evidence that justifies the content of this use case.
# It is a reference and audit artifact — not a machine-readable configuration file.
# Generated or authored; validated by the semantic quality gate.

evidence_pack_version: "1.0"
use_case_id: ""                    # e.g. OPS-001
use_case_title: ""
domain: ""                         # e.g. Operations, Commercial, Finance
authored_date: ""                  # ISO 8601 date
authored_by: ""                    # agent ID or human name
reviewed_by: ""
status: draft                      # draft | reviewed | approved

# ──────────────────────────────────────────
# 1. PROCESS SCOPE
# ──────────────────────────────────────────
process_scope:
  description: ""
  in_scope:
    - ""
  out_of_scope:
    - ""
  industry_segment: ""
  applicable_frameworks:
    - name: ""
      id: ""                       # e.g. ISO 22400, SCOR, APQC PCF

# ──────────────────────────────────────────
# 2. CANONICAL DOMAIN MODEL (DRIVER TREE)
# ──────────────────────────────────────────
canonical_domain_model:
  outcome_kpis:
    - id: ""                       # e.g. ops.oee.pct
      name: ""
      definition: ""
      unit: ""                     # %, count, days, EUR, etc.
      direction: maximize          # maximize | minimize
      benchmark_target: ""        # e.g. "85% World Class (ISO 22400)"
      benchmark_source_id: ""     # Source ID from source_inventory

  driver_kpis:                     # Second level — explain outcome movement
    - id: ""
      name: ""
      definition: ""
      unit: ""
      direction: maximize
      drives: ""                   # outcome KPI ID this driver explains
      causal_mechanism: ""
      benchmark_target: ""
      benchmark_source_id: ""

  diagnostic_kpis:                 # Third level — root cause drill-down
    - id: ""
      name: ""
      definition: ""
      unit: ""
      direction: maximize
      diagnoses: ""                # driver KPI ID this diagnostic explains
      causal_mechanism: ""

  guardrails:
    - description: ""
      condition: ""                # When this condition holds, do NOT trigger action
      affected_kpis:
        - ""

  wrong_interpretations:
    - description: ""
      why_wrong: ""
      source_id: ""

# ──────────────────────────────────────────
# 3. REQUIRED DATA MODEL
# ──────────────────────────────────────────
required_data_model:
  required_facts:
    - table: ""
      description: ""
  required_dimensions:
    - name: ""
      grain_relevance: ""          # Why this dimension is needed
  preferred_grain: ""             # e.g. line-shift-day
  minimum_grain: ""               # e.g. line-day
  minimum_history_months: 12
  required_measures:
    - name: ""
      formula_seed: ""            # Human-readable formula (not DAX)
      source_id: ""

# ──────────────────────────────────────────
# 4. ACTION LOGIC SEEDS
# ──────────────────────────────────────────
action_logic_seeds:
  - trigger_driver: ""            # Driver KPI that triggers
    trigger_diagnostic: ""        # Diagnostic KPI that confirms root cause
    trigger_condition: ""         # e.g. "Availability % < 80% for 3 consecutive shifts"
    guardrail: ""                 # Condition that blocks action
    action_description: ""
    expected_outcome_kpi: ""
    action_code_candidate: ""     # Maps to existing or proposed Action Code ID

# ──────────────────────────────────────────
# 5. SOURCE INVENTORY
# ──────────────────────────────────────────
source_inventory:
  summary:
    total_sources: 0
    portfolio_score: 0.0           # Sum of all source scores / count
    categories_covered:
      - STD
    min_threshold_met: false       # true when all sources score >= 8 and count >= 10

  sources:
    - id: SRC-001
      category: STD                # STD | ACA | PRO | BNK | IMP | RSK
      title: ""
      author: ""
      publication: ""
      year: null
      url: ""
      doi: ""
      scores:
        authority: 3               # 1–3
        recency: 3                 # 1–3
        domain_relevance: 3        # 1–3
        independence: 3            # 1–3
        content_role: 3            # 1–3
      total_score: 15              # sum of scores
      supports:
        - outcome_kpis
        - driver_kpis
        - benchmark_target
      notes: ""

# ──────────────────────────────────────────
# 6. MAPPING READINESS
# ──────────────────────────────────────────
mapping_readiness:
  kpi_catalog_coverage: pending   # pending | partial | complete
  factsheet_coverage: pending     # pending | partial | complete
  bracket_coverage: pending       # pending | partial | complete
  action_code_coverage: pending   # pending | partial | complete
  semantic_model_coverage: pending

  gap_summary:
    content_gaps: []               # List of content_gap descriptions
    mapping_gaps: []               # List of mapping_gap descriptions
    schema_gaps: []                # List — each triggers Schema Gap Report before action
    generator_gaps: []
    model_gaps: []
```

---

## 3. Schema Gap Decision Protocol

A schema gap exists when the evidence extraction produces a required semantic that **cannot be expressed** in any existing Core schema field.

### 3.1 When to Declare a Schema Gap

| Condition | Action |
|-----------|--------|
| Evidence requires a new field in `usecase_bracket.schema.json` | Schema Gap Report required |
| Evidence requires a new field in `kpi_definition.schema.json` | Schema Gap Report required |
| Evidence requires a new field in `action_code.schema.json` | Schema Gap Report required |
| Evidence can be expressed using existing schema fields but with new content | `content_gap` — no schema change needed |
| Evidence requires new content wired to a different target | `mapping_gap` — no schema change needed |
| Evidence requires a new measure/table in the semantic model | `model_gap` — handled via data contract, no Core schema change |

### 3.2 Schema Gap Report Template

```yaml
schema_gap_id: ""                  # e.g. SGR-OPS-001-001
use_case_id: ""
identified_by: ""
date: ""
status: proposed                   # proposed | under_review | approved | rejected

problem_statement: ""              # What semantics cannot be expressed

necessity:
  description: ""                  # Why is this field necessary?
  affected_use_cases:
    - ""                           # All use cases that would need this field
  alternatives_considered:
    - option: ""
      rejected_because: ""

proposed_change:
  schema_file: ""                  # Which schema file would be affected
  field_name: ""
  field_type: ""
  field_description: ""
  required: false
  example_value: ""

impact_assessment:
  generator_impact: ""             # What the generator needs to change
  validator_impact: ""             # What validators need to change
  migration_impact: ""             # What existing brackets need to update
  estimated_affected_use_cases: 0

decision:
  approved_by: ""                  # Framework Architect role
  decision_date: ""
  decision_rationale: ""
  implementation_ticket: ""        # Link to issue or plan
```

### 3.3 Escalation Path

```
Evidence Extraction
    │
    ├── content / mapping / generator / model gap?
    │       └── Author fixes directly → Core update
    │
    └── schema gap?
            └── Author produces Schema Gap Report
                    └── Framework Architect reviews
                            ├── Rejected: Author finds alternative mapping
                            └── Approved: Minimal schema change implemented
                                    └── Migration of all existing brackets
                                            └── Re-validation (Stage 1 + tests)
```

---

## 4. Evidence Pack Lifecycle

| Status | Description |
|--------|-------------|
| `draft` | Author created, not reviewed |
| `reviewed` | Reviewer checked source scores and extraction completeness |
| `approved` | Framework Architect approved; safe to use as Core update justification |

A DEP with status `draft` or `reviewed` may not be used to justify a schema change.
Only an `approved` DEP may justify Core content updates.

---

## 5. Integration Points (Non-Breaking, Current Schemas)

The DEP currently integrates with Core without requiring schema changes:

| Integration | How |
|-------------|-----|
| Bracket references DEP | Via `documentation` → `evidence_pack` optional field (requires minor schema addition, tracked as SGR-BRACKET-001) |
| Factsheet references DEP | Inline Markdown reference — no schema change |
| KPI Catalog | New KPI entries justified by DEP source citations — no schema change to KPI schema |
| Action Codes | New action codes justified by DEP action logic seeds — no action code schema change |
| Quality Gate | Semantic quality gate reads DEP to compute coverage score |

---

## 6. Pending Schema Gap Reports

| ID | Affected Schema | Field | Status |
|----|----------------|-------|--------|
| SGR-BRACKET-001 | `usecase_bracket.schema.json` | `documentation.evidence_pack` | Proposed — needs Framework Architect review |

See `docs/process/schema-gap-reports/SGR-BRACKET-001.yaml` for the full proposal.
