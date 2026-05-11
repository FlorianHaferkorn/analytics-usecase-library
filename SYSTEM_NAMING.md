# System Naming Conventions

Scope: scripts, checks, generators, tests, hooks, schemas, templates, and directories that make up the **tooling system** of this repo. This document is the authority for system-level naming. Content-level naming (KPI IDs, action codes, domain tags) is governed by `TAXONOMY.md`.

---

## 1  Guiding Principles

| # | Principle |
|---|---|
| 1 | **Snake_case everywhere** — all script and file names use `lower_snake_case` regardless of language (`.ps1`, `.py`, `.sh`) |
| 2 | **Verb-first for scripts** — file names start with an action verb that describes what the script does, not what it produces |
| 3 | **Role prefix for tools** — the leading verb signals the tool's role (see §3) |
| 4 | **One concern per file** — no `run_all_*.ps1` patterns inside tool subdirectories; entry-point wrappers live at the layer root |
| 5 | **Test files follow language convention** — `test_*.py` (pytest), `test_*.ps1` (Pester), all in a `tests/` subdirectory |
| 6 | **No PascalCase, no kebab-case** in script names — the only exceptions are framework-mandated files (`pre-commit` git hook) and PBIP artifact directories which follow Power BI naming rules |

---

## 2  File Naming by Type

### PowerShell (`.ps1`)
- Pattern: `lower_snake_case`
- Verb-first: `check_`, `validate_`, `generate_`, `fix_`, `run_`, `build_`, `deploy_`, `sync_`, `list_`, `map_`, `export_`, `load_`, `apply_`, `write_`, `ensure_`, `normalize_`, `test_`, `watch_`
- Libraries/dot-source helpers get a descriptive noun phrase: `load_project_env.ps1`, `map_aurora_domains.ps1`

### Python (`.py`)
- Pattern: `lower_snake_case` (already standard)
- Modules: noun phrase (`pbip_writer.py`, `config_loader.py`)
- Entry-point scripts: verb-first (`generate_page_scaffold.py`, `execute_dax.py`)
- Tests: `test_<module>.py` inside a `tests/` directory

### Shell (`.sh`)
- Pattern: `lower_snake_case`
- Same verb-first convention as PowerShell
- Claude hooks: `validate_<what>_<aspect>.sh`

### YAML / YML
- Config and contract files: `lower_snake_case.yaml`
- Template starters: `<name>.template.yaml`
- Schema descriptors: `<name>.schema.yaml`
- ID-based domain files (action codes, decision spines): keep existing `DOMAIN-ID.yaml` format — those are content identifiers, not system files

### JSON schemas
- Pattern: `<name>.schema.json` — already consistent in `tooling/generator/schemas/`
- Schemas live in `tooling/generator/schemas/` only. The old `tooling/validation/schemas/` directory has been removed.

### Markdown docs
- Root-level governance docs: `UPPER_SNAKE_CASE.md` (README, CLAUDE, CHANGELOG, TAXONOMY, etc.)
- Internal project management: `UPPER_SNAKE_CASE.md` (existing convention preserved)
- Reference documentation inside product subdirs: `kebab-case.md` (e.g. `pbir-visual-json.md`, `tmdl-advanced-features.md`)
- Narrative guides and how-tos: `lower_snake_case.md`

---

## 3  Role Prefixes for Scripts

| Prefix | Meaning | Examples |
|--------|---------|---------|
| `check_` | Fast structural/reference validation; exits non-zero on first fail | `check_tmdl_syntax.ps1`, `check_duplicate_ids.ps1` |
| `validate_` | Comprehensive validation suite; collects all errors before reporting | `validate_factsheets.ps1`, `validate_pbir_structure.sh` |
| `generate_` | Creates or scaffolds new artefacts | `generate_measures.ps1`, `generate_page_scaffold.py` |
| `fix_` | Automated repair of known issues | `fix_factsheets.ps1`, `fix_mojibake.ps1` |
| `run_` | Orchestrates/delegates to other tools | `run_fabric_checks.ps1`, `run_all_checks.ps1` |
| `build_` | Compiles or assembles artefacts | `build_alignment_map.ps1`, `build_ir.py` |
| `deploy_` | Pushes to a remote environment | `deploy.ps1`, `deploy_gate.ps1` |
| `sync_` | Bidirectional or pull-down sync | `sync_evidence_grain_note_to_factsheet.ps1` |
| `list_` | Outputs inventory/report without side effects | `list_granular_issues.ps1`, `list_project_duplicates.ps1` |
| `map_` | Transforms or translates from one structure to another | `map_aurora_domains.ps1` |
| `export_` | Writes a package/file out of the system | `export_customer_package.ps1` |
| `load_` | Dot-source library / environment initialisation | `load_project_env.ps1` |
| `apply_` | Patches an existing artefact | `apply_report_theme.ps1` |
| `normalize_` | Enforces canonical format | `normalize_tmdl_tabs.ps1` |
| `test_` | Pester / unit test entry point | `test_tmdl.ps1`, `test_ops_parse.ps1` |
| `watch_` | File-system watcher / daemon | `watch_pbi.ps1` |
| `ensure_` | Idempotent setup; creates if absent | `ensure_pbip_desktop_ready.ps1` |

---

## 4  Directory Naming

| Layer | Convention | Examples |
|-------|-----------|---------|
| Top-level | `lower_snake_case` | `core/`, `tooling/`, `products/`, `showcases/` |
| Sub-directories | `lower_snake_case` | `page_scaffold_generator/`, `project_mgmt/` |
| PBIP artifact dirs | Power BI convention (preserved) | `Commercial.SemanticModel/`, `COM-001_Sales_Performance.Report/` |
| Test directories | `tests/` (plural, lowercase) | `page_scaffold_generator/tests/` |
| Hooks | `.claude/hooks/` (already correct) | — |

---

## 5  Claude Hook Files (`.claude/hooks/`)

Hook file names follow `validate_<artefact>_<aspect>.sh`:

| File | What it checks |
|------|---------------|
| `validate_tmdl_style.sh` | Tab indentation, `:=` operator, `description:` property, `summarizeBy` presence |
| `validate_pbir_structure.sh` | JSON syntax, folder-name spaces, required fields in visual.json/page.json/definition.pbir, byPath existence, byConnection GUID |

Settings reference: `.claude/settings.json` → `hooks.PostToolUse[].hooks[].command`.

---

## 6  Deviations and Exceptions

| File | Why unchanged |
|------|--------------|
| `tooling/git-hooks/pre-commit` | Git hook file — must be named exactly `pre-commit` |
| `products/fabric/powerbi/deployment/.azure-pipelines/*.yml` | Azure DevOps pipeline names are consumed by external tooling |
| Action code YAML files (`C-M2.1.yaml`, etc.) | IDs defined by `TAXONOMY.md`; rename would break cross-references |
| `UseCase_Bracket.yaml` | Well-established cross-repo contract name; schema validators reference it |
| `dbt_project.yml` | dbt framework requirement |

---

## 7  Checklist for New Files

- [ ] Name starts with a verb from §3 (for scripts) or a noun phrase (for modules/libs)
- [ ] All lowercase, underscores only (no hyphens, no PascalCase)
- [ ] Lives in the correct layer directory
- [ ] Test file is `test_<module>.[py|ps1]` in the nearest `tests/` directory
- [ ] Schema file uses `.schema.json` or `.schema.yaml` suffix
- [ ] Template file uses `.template.<ext>` suffix

---

*Complement to `TAXONOMY.md` (content IDs) and `AGENTS.md` (agent operating rules).*
