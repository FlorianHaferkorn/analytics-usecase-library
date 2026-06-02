# Gap Classification — Evidence-to-Core Mapping Rules

> **Version:** 1.0  
> **Status:** Active  
> **Authority:** Framework Architect  
> **Related:** `docs/process/research-to-core-standard.md` | `docs/process/domain-evidence-pack-spec.md`

---

## Purpose

Every mismatch between domain evidence and existing Core artifacts must be classified before action is taken.
Classification determines the correct remediation path and prevents silent schema changes.

---

## 1. Gap Type Definitions

### `content_gap`

**Definition:** The Core schema can fully express the required semantics, but the content is missing or incomplete.

**Examples:**
- A KPI exists in the domain model but has no entry in `core/kpi_catalog/`
- A business question from the factsheet has no corresponding visual slot in the bracket
- An action code trigger condition is known from evidence but not written in the action code YAML

**Action:** Author adds content directly. No schema change needed. No Framework Architect approval required.

**Applies to:**
- Missing KPI entries in `core/kpi_catalog/`
- Missing action codes in `core/action_codes/`
- Missing business questions in `Business_Factsheet.md`
- Missing measures in TMDL
- Missing dimensions in `dim_*.tmdl`

---

### `mapping_gap`

**Definition:** Content exists in Core, but is wired to the wrong KPI, visual type, evidence column, action code, or grain.

**Examples:**
- A KPI is in the catalog but linked to the wrong driver in the bracket value driver model
- An existing visual slot shows the wrong dimension category
- A business question is answered by the wrong chart type (e.g., trend when a ranking is needed)
- An action code references a trigger KPI that is not the correct diagnostic KPI from domain evidence

**Action:** Author rewires the content — updates the bracket YAML, factsheet, or action code YAML.
No schema change needed. No Framework Architect approval required.

**Applies to:**
- `UseCase_Bracket.yaml` field values
- `Business_Factsheet.md` mappings
- Action code `trigger_kpi_id` / `guardrail` fields
- `evidence_columns` in `component_300s`

---

### `schema_gap`

**Definition:** The Core schema cannot express required semantics, even with correct content and correct wiring.

**Examples:**
- Domain evidence requires a "causal_chain" field in the bracket but no such field exists
- An action code needs a "delay" field (how long to wait before triggering) but the schema has no such property
- The DEP needs a cross-use-case dependency link in the bracket but `documentation` has no array field for it
- A KPI needs a "leading_indicator_for" backlink but the KPI catalog schema has no such field

**Action:** STOP. Produce a Schema Gap Report (`docs/process/schema-gap-reports/`). Get Framework Architect approval. Only then implement the minimal schema change.

**Applies to:**
- Any new property in `usecase_bracket.schema.json`
- Any new property in `kpi_definition.schema.json`
- Any new property in `action_code.schema.json`
- Any new required field in any governed schema

---

### `generator_gap`

**Definition:** Schema and content are correct, but the generator (page scaffold generator, TMDL generator, or orchestrator) does not use the field to produce the correct output.

**Examples:**
- `category_field` is set in the bracket but the generator does not pass it to the visual builder
- `decision_question` is in the bracket but the generator does not inject it as a page annotation
- `evidence_grain` is set correctly but the generator builds the detail matrix with the wrong grain

**Action:** Author fixes the generator code (Python generators in `products/fabric/powerbi/tooling/`) or orchestrator script. No schema change needed.

---

### `model_gap`

**Definition:** The semantic model (TMDL tables, measures, relationships) or the data contract lacks required facts, dimensions, measures, or grain.

**Examples:**
- `fact_ops` is missing a `downtime_minutes` column required by the driver tree
- The `dim_product` table is missing a `Category` column required by domain evidence
- A required grain (`line-shift-day`) is not available in the data contract

**Action:** Author updates TMDL files and/or the data contract YAML. No Core schema change needed.
A `model_gap` may trigger a data contract amendment, which follows the data contract governance process.

---

## 2. Evidence-to-Core Mapping Tables

### 2.1 Evidence → Business Factsheet

| Evidence Field | Factsheet Section | Gap Type if Missing |
|---------------|------------------|-------------------|
| `process_scope.description` | Section 1 Business Summary — Purpose | `content_gap` |
| `process_scope.out_of_scope` | Section 1 Business Summary — Out of Scope | `content_gap` |
| `outcome_kpis` (names and definitions) | Section 3 KPI & Action Code Overview | `content_gap` |
| `driver_kpis` (names and definitions) | Section 3 KPI & Action Code Overview | `content_gap` |
| `wrong_interpretations` | Section 9 Risks & Wrong Interpretations | `content_gap` |
| `benchmark_targets` | Section 8 Success Criteria | `content_gap` |
| `action_logic_seeds` (scenario descriptions) | Section 10 Typical Decision Scenarios | `content_gap` |
| `guardrails` | Section 9 Risks & Wrong Interpretations | `content_gap` |
| `required_data_model.required_measures` | Section 6 Data Requirements Summary | `content_gap` |
| `required_data_model.minimum_grain` | Section 6 Data Requirements Summary | `content_gap` |
| Core business questions (from canonical domain model) | Section 2 Core Business Questions | `content_gap` |

---

### 2.2 Evidence → UseCase Bracket

| Evidence Field | Bracket Field | Gap Type if Missing or Wrong |
|---------------|--------------|------------------------------|
| `outcome_kpis[0]` | `orchestration.strategic_kpi_id` | `mapping_gap` if wrong KPI |
| `driver_kpis` | `orchestration.influencing_kpi_ids` | `content_gap` if KPI missing; `mapping_gap` if wrong order/KPI |
| `diagnostic_kpis` | `orchestration.supporting_kpi_ids` | `content_gap` |
| `action_logic_seeds[*].action_code_candidate` | `orchestration.action_code_ids` | `content_gap` |
| `canonical_domain_model` causal chain | `value_driver_model.formula` | `mapping_gap` if wrong relationship expressed |
| `required_data_model.required_grain` | `page_2_execution.component_300s.evidence_grain` | `mapping_gap` |
| `canonical_domain_model` key dimensions | `page_2_execution.component_300s.evidence_columns` | `content_gap` if missing dimension |
| Business questions → visual slot alignment | `page_1_summary.component_30s[*].visual_type` | `mapping_gap` if wrong chart type |
| Driver KPI → visual slot | `page_1_summary.component_30s[*].kpi_id` | `mapping_gap` |
| `action_logic_seeds` condition → page narrative | `page_1_summary.big_idea` | `content_gap` |

---

### 2.3 Evidence → KPI Catalog

| Evidence Field | KPI Catalog Field | Gap Type if Missing |
|---------------|------------------|---------------------|
| `outcome_kpis[*].id` | KPI entry `id` | `content_gap` |
| `outcome_kpis[*].definition` | KPI entry `business_definition` | `content_gap` |
| `outcome_kpis[*].formula_seed` | KPI entry `formula` | `content_gap` |
| `driver_kpis[*]` | KPI entries with role `driver` | `content_gap` |
| `diagnostic_kpis[*]` | KPI entries with role `diagnostic` | `content_gap` |
| Driver → outcome causal link | KPI `depends_on` field | `content_gap` |

---

### 2.4 Evidence → Action Codes

| Evidence Field | Action Code Field | Gap Type if Missing |
|---------------|------------------|---------------------|
| `action_logic_seeds[*].action_code_candidate` | Action Code `id` | `content_gap` |
| `action_logic_seeds[*].trigger_condition` | Action Code `trigger.condition` | `content_gap` |
| `action_logic_seeds[*].guardrail` | Action Code `guardrail` | `content_gap` |
| `action_logic_seeds[*].expected_outcome_kpi` | Action Code `outcome_kpi_id` | `content_gap` |
| `action_logic_seeds[*].trigger_driver` | Action Code `trigger.kpi_id` | `mapping_gap` if wrong KPI |

---

### 2.5 Evidence → Semantic Model (TMDL / Data Contract)

| Evidence Field | Semantic Model Artifact | Gap Type if Missing |
|---------------|------------------------|---------------------|
| `required_data_model.required_facts[*]` | Fact table in `fact_*.tmdl` | `model_gap` |
| `required_data_model.required_dimensions[*]` | Dimension table in `dim_*.tmdl` | `model_gap` |
| `required_data_model.required_measures[*]` | Measure in `_Measures.tmdl` | `model_gap` |
| `required_data_model.preferred_grain` | Data contract `grain` field | `model_gap` |
| `diagnostic_kpis[*].formula_seed` | Measure DAX implementation | `model_gap` |

---

## 3. Gap Classification Decision Tree

```
Evidence item extracted
    │
    ▼
Does an existing schema FIELD exist to express this?
    │
    ├── NO → schema_gap (produce Schema Gap Report, stop)
    │
    └── YES
          │
          ▼
       Is the content already present in Core?
          │
          ├── NO → content_gap (add content)
          │
          └── YES
                │
                ▼
             Is the content wired to the right target (KPI/visual/action/grain)?
                │
                ├── NO → mapping_gap (rewire)
                │
                └── YES
                      │
                      ▼
                   Does the generator use the field to produce correct output?
                      │
                      ├── NO → generator_gap (fix generator)
                      │
                      └── YES
                            │
                            ▼
                         Does the semantic model have the required data?
                            │
                            ├── NO → model_gap (fix TMDL / data contract)
                            │
                            └── YES → No gap, evidence is fully expressed
```

---

## 4. Gap Severity Levels

| Severity | Description | Blocks Generation? |
|----------|-------------|-------------------|
| `critical` | Missing outcome KPI, missing strategic KPI, missing required grain | Yes |
| `high` | Missing driver KPI, wrong chart type for core question, missing action code | Yes (semantic gate) |
| `medium` | Missing diagnostic KPI, missing benchmark, wrong dimension category | Warning only |
| `low` | Missing optional context (seasonality, leading indicators) | No |

---

## 5. Gap Report Format

Each use case should produce a Gap Report as part of the Domain Evidence Pack review cycle.
The Gap Report is a section within `Domain_Evidence_Pack.yaml` under `mapping_readiness.gap_summary`.

Format for a single gap entry:

```yaml
- gap_type: content_gap        # content_gap | mapping_gap | schema_gap | generator_gap | model_gap
  severity: high               # critical | high | medium | low
  affected_artifact: ""        # e.g. core/kpi_catalog/ops.oee.pct.yaml
  field: ""                    # Specific field or section affected
  description: ""              # What is missing or wrong
  evidence_reference: ""       # Source ID or extraction field that requires this
  remediation: ""              # What action to take
  status: open                 # open | in_progress | resolved | waived
  resolved_by: ""
  resolved_date: ""
```
