# Internal Tools

## Purpose
Provide all **automation, validation, linting, generation, governance, and maintenance tools** required to operate and evolve the ActionReady Analytics Framework.
This directory is **strictly internal** and must never be delivered to, or copied into, customer repositories.

The tools ensure:
- KPI catalog consistency
- Use Case documentation integrity
- Action Code schema compliance (v2.0)
- Accurate and reproducible measure generation
- Semantic model (TMDL) compliance
- Report & DAX best-practice enforcement
- Continuous governance via registry audit and pre-commit hooks
- Trust signal production (`trust_score`, `data_contract_risk`)
- End-to-end framework quality

---

## Directory Structure

```
tooling/
  ai/                  # AI/agent schemas (synced from validation/schemas/)
  alignment/           # Strategic alignment map generators
  generation/          # Measure & scaffolding generation
  git-hooks/           # Pre-commit hook + installer
  linters/             # DAX, semantic model, report, encoding rules
  maintenance/         # Evolution, migration, docs checks
  ontology/            # Registry engine (hard audit suite)
  validation/          # Stage 1 validators, JSON schemas
  run_stage1_checks.ps1
  run_all_checks.ps1
```

---

## 1. validation/

**Purpose:** Validate the consistency of all governed artifacts.

**Key scripts:**
- `validate_factsheets.ps1` — factsheet structure and content
- `validate_kpi_catalog.ps1` — KPI catalog rules
- `check_factsheet_vs_kpi.ps1` — factsheet KPI references vs catalog
- `check_factsheet_action_codes.ps1` — factsheet/bracket action code refs vs framework (falls back to `UseCase_Bracket.yaml`)
- `check_action_codes_vs_kpi.ps1` — action code KPI IDs vs catalog
- ~~`check_usecase_actioncode_map.ps1`~~ — archived (Lean 2.0; map deleted, see `internal/archive/lean2_cutover_2026-02/`)
- `check_decision_spines.ps1` — decision spine map alignment
- `check_duplicate_ids.ps1` — no duplicate IDs across artifacts
- `check_ssot_markers.ps1` — SSOT markers respected
- `check_schema_validation.ps1` — JSON schema validation (requires `npm ci` in `validation/`)

**Schemas:** `validation/schemas/` is the **canonical** schema directory.

**Outputs:** `validation/results/latest_results.json` — produced by `run_stage1_checks.ps1`, consumed by the registry for trust scoring.

**Setup (one-time):**
```powershell
cd tooling\validation
npm ci
```

Optional (recommended for reproducible local/CI runners):

```powershell
.\tooling\bootstrap.ps1 -InstallNodeDeps -CreateVenv -InstallPythonDeps
```

---

## 2. ontology/ (Registry Engine)

**Purpose:** Hard audit suite — builds the master object graph, detects orphans, validates governance, and produces trust signals.

**Entrypoint:**
```powershell
py -3 tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict
```

**Outputs (generated, not committed):**

| File | Purpose |
|---|---|
| `out/master_registry.json` | Complete object graph with resolved links, trust scores, data_contract_risk |
| `out/orphans_report.json` | Unreferenced KPIs, action codes, and use cases |
| `out/governance_gaps.json` | Missing/conflicting governance roles |
| `out/value_map.json` | Impact-path linkage and valuation metadata |
| `out/action_text_preview.txt` | Human-readable action text for Power BI panels |

**Supporting scripts:**
- `extract_kpi_orphans.py` — extract & purge KPI orphans from catalog
- `archive_ghosts.py` — move orphan files to `internal/archive/tooling/ghosts/`
- `preview_action_texts.py` — generate action text preview

Legacy migration script (factsheets to brackets): see `internal/archive/lean2_cutover_2026-02/refactor_usecases_to_brackets.py`.

---

## 3. git-hooks/ (Continuous Governance)

**Purpose:** Pre-commit enforcement — runs registry in strict mode before every commit.

**Install:**
```powershell
.\tooling\git-hooks\install_precommit.ps1
```

**Contents:**
- `pre-commit` — shell hook (runs `registry_builder.py --strict`)
- `install_precommit.ps1` — copies hook to `.git/hooks/`, validates Python 3

---

## 4. linters/

**Purpose:** Enforce framework rules for DAX, semantic models, report layout, and text encoding.

**Contains:**
- `lint.rules.yaml`, `bpa-rules-dax.json`, `bpa-rules-report.json`, `bpa-rules-semanticmodel.json`
- `lint_dax.ps1`, `lint_encoding.ps1`, `fix_mojibake.ps1`

---

## 5. generator/ (consolidated)

**Purpose:** All code generation — measures, model scaffolding, use case setup, agent tooling, and JSON schemas.

**Contains:**
- `generate_tmdl_measures.ps1` — TMDL measures from KPI catalog / IR
- `generate_semantic_model_from_blueprint.ps1` — model scaffold from blueprint
- `new_usecase.ps1` — use case scaffolding
- `generate_tool_configs.py` — agent tool config generator
- `check_skill_versions.py` — skill version checker
- `schemas/` — JSON schemas for factsheets, brackets, action codes, layout, data contracts
- `prompts/` — agent prompt templates
- `graph/` — knowledge graph (graph.json)

---

## 6. alignment/

**Purpose:** Generate strategic alignment maps (KPIs -> Use Cases -> Action Codes -> Page Templates).

**Contains:** `build_alignment_map.ps1`

---

## 7. ai/ (Archived)

Merged into `generator/`. See `internal/archive/phase2_experiments/` for legacy maintenance scripts.

Note: `validation/schemas/` may still hold copies; prefer `generator/schemas/` as the canonical source.

---

## 8. generator_core/ (Python IR framework)
- Edit schemas only in `validation/schemas/`.
- After any schema change, copy the updated file to `ai/schemas/` (or run a future sync script).
- Stage 1 schema validation runs against `validation/schemas/`.

---

## Quality Gates

**Stage 1 (CI gate):** `run_stage1_checks.ps1`
Tool-agnostic validation (docs, refs, structure, KPI consistency, action code map, schemas).
Produces `validation/results/latest_results.json`.
This is the mandated check before merge.

**Registry audit:** `py -3 tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict`
Referential integrity, transitive linkage, governance gaps, value-driver formulas.

**Full validation:** `run_all_checks.ps1`
Stage 1 + Fabric checks (measures vs KPI, TMDL, DAX best practices).

**Fabric-only:** `products/fabric/powerbi/tooling/run_fabric_checks.ps1`

---

## Usage Guidelines

### For Framework Maintainers
- Do not alter folder structure without updating this README.
- Add new tools only in the corresponding subfolders.
- Tools must be platform-neutral unless explicitly scoped.
- Schema changes: edit `validation/schemas/` first, then sync `ai/schemas/`.

### For Delivery Teams
- Use documented tools only.
- Do not customize or fork scripts for customers; extend the framework instead.
- For customer delivery from the monorepo, use `tooling/export_customer_package.ps1` to produce a curated package that excludes maintainer-only folders.

### For Customers
- No access.
- All results are delivered by Delivery Teams through governed pipelines.

---

## Relations

- **Operating Model:** Ensures semantic, metadata, and measure rules are enforced
- **Use Case Library:** Validates factsheets & required KPI alignment
- **Framework Toolkit:** Generates measures, validates catalogs, enforces ActionReady rules
- **Registry Engine:** Builds and validates the master object graph, trust signals, and governance gaps
- **Showcases:** Built using these tools but do not contain tools themselves

---

**Location:** `tooling/README.md`
