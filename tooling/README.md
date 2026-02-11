# Internal Tools

## Purpose
Provide all **automation, validation, linting, generation, and maintenance tools** required to operate and evolve the ActionReady Analytics Framework.  
This directory is **strictly internal** and must never be delivered to, or copied into, customer repositories.

The tools ensure:
- KPI catalog consistency  
- Use Case documentation integrity  
- Accurate and reproducible measure generation  
- Semantic model (TMDL) compliance  
- Report & DAX best‑practice enforcement  
- End‑to‑end framework quality  

---

## Scope

### Included
- Measure generation (TMDL/KPI‑driven)
- Validators for factsheets, KPIs, semantic models, PBIP
- BPA & Linter rule sets
- Maintenance & migration scripts
- Alignment map generators
- Use case scaffolding tools
- Master quality runner (`run_all_checks.ps1`)

### Not included
- Customer code  
- Customer pipelines  
- Showcase scripts (these live in `showcases/...`)  
- Framework documentation (`docs/...`)

---

# Directory Structure

```
_internal/
  tools/
    linters/
    validation/
    generation/
    maintenance/
    alignment/
    run_all_checks.ps1
```

Below is the role of each subdirectory.

---

# 1. linters/

**Purpose:** Enforce framework rules across:
- DAX  
- Semantic Models  
- Report layout  
- Text encoding

**Contains:**
- `lint.rules.yaml`
- `bpa-rules-dax.json`
- `bpa-rules-report.json`
- `bpa-rules-semanticmodel.json`
- `lint_dax.ps1`
- `lint_encoding.ps1`
- `fix_mojibake.ps1`

**Usage:**  
Run locally or in CI/CD to ensure semantic and report quality.

---

# 2. validation/

**Purpose:** Validate the consistency of all content that flows into the semantic model and reporting layer.

**Contains:**
- `validate_factsheets.ps1`
- `validate_kpi_catalog.ps1`
- `check_factsheet_vs_kpi.ps1`
- `check_spec_vs_kpi.ps1`
- (Fabric-specific: `check_measures_vs_kpi.ps1`, `check_tmdl_vs_measure_dictionary.ps1`, `check_dax_best_practices.ps1` live under `implementations/microsoft_fabric_powerbi/validation/`)
- `add_depends_on_ids.ps1`
- `list_usecase_levels.ps1`

Subfolder:
```
validation/pbip/
  validate_pbip.ps1
```

**Usage:**  
Mandatory before merging Use Cases or publishing semantic models.

---

# 3. generation/

**Purpose:** Generate or update measures & scaffolding.

**Contains:**
- `generate_tmdl_measures.ps1`
- `generate_tmdl_measures_simple.ps1`
- `generate_measures.ps1`
- `generate_all_measures.ps1`
- `new_usecase.ps1`

**Usage:**  
Run whenever KPI catalogs or factsheets change.

---

# 4. maintenance/

**Purpose:** Support long‑term evolution and consistency.

**Contains:**
- `check_docs_refs.ps1`
- `convert_kpi_catalogs.py`
- `normalize_kpi_catalogs.ps1`

**Usage:**  
Used during major framework updates or structural refactoring.

---

# 5. alignment/

**Purpose:** Generate strategic alignment maps  
(KPIs → Use Cases → Action Codes → Page Templates).

**Contains:**
- `build_alignment_map.ps1`

**Usage:**  
Whenever new use cases or strategic KPIs are added.

---

# 6. Stage 1 vs run_all_checks

**Stage 1 (CI gate):** `run_stage1_checks.ps1` — Tool-agnostic only (docs, refs, structure, KPI ↔ use case, action code map). Use for **CI and before merge**; this is the mandated check for merge. Fast, no Fabric/Power BI output required.

**Full validation:** `run_all_checks.ps1` — Runs Stage 1 plus Fabric checks (measures vs KPI, TMDL vs measure dictionary, DAX best practices, TMDL syntax). Use for **full local validation** when you have generated TMDL/measures (e.g. in `implementations/microsoft_fabric_powerbi/dist`). Use before releasing or when changing measures/TMDL.

**Fabric-only:** `implementations/microsoft_fabric_powerbi/tools/run_fabric_checks.ps1` — Fabric checks only (no Stage 1); use when you only need to validate generated TMDL/measures.

# 7. run_all_checks.ps1

**Purpose:** Execute all internal checks in correct sequence (Stage 1 + Fabric checks).

Runs:
1. KPI catalog validation  
2. Factsheet validation  
3. KPI ↔ Use Case consistency checks  
4. Measure consistency checks  
5. PBIP validation  
6. Linter/BPA rule enforcement  

**Usage:**  
Before every merge into `main` (prefer `run_stage1_checks.ps1` for CI) and before exporting templates or when validating Fabric/Power BI output.

---

# Usage Guidelines

### For Framework Maintainers
- Do not alter folder structure without updating this README.
- Add new tools only in the corresponding subfolders.
- Tools must be platform‑neutral unless explicitly scoped.

### For Delivery Teams
- Use documented tools only.
- Do not customize or fork scripts for customers; extend the framework instead.

### For Customers
- No access.  
- All results are delivered by Delivery Teams through governed pipelines.

---

# Relations

- **Operating Model:** Ensures semantic, metadata, and measure rules are enforced  
- **Use Case Library:** Validates factsheets & required KPI alignment  
- **Framework Toolkit:** Generates measures, validates catalogs, enforces ActionReady rules  
- **Showcases:** Built using these tools but do not contain tools themselves

---

**Location:**  
`_internal/tools/README.md`
