# Review: data-goblin/power-bi-agentic-development

> **Reviewed**: 2026-04-04 (initial partial) + 2026-04-04 (complete — all 6 plugins)  
> **Repo**: https://github.com/data-goblin/power-bi-agentic-development  
> **Version at review**: 0.17.1 (daily release cadence — re-check quarterly)  
> **Context**: Assessed for adoption into our PBI Generator and Architecture Generator  

---

## TL;DR

Claude Code plugin marketplace for Power BI agentic work. 6 plugins, 170 files analysed. Three are irrelevant for us; three contain high-value content we partially lack.

**Adopt now (Sprint 2)**: `rename-cascade.md`, `pbir-structure.md`, `visual-container-formatting.md`, `measures-vs-literals.md`, enhanced `validate-pbir.sh` checks, `validate-report-binding.sh` with byPath existence, 54 visual examples  
**Adopt Sprint 3**: TMDL skill delta, `fab-vs-az-cli.md`, security hooks from `useful-stuff/`  
**Skip**: tabular-editor (we don't use TE), `pbir-cli` (private beta binary), pbi-desktop (headless only), deneb/python/r-reviewer agents

---

## Plugin-by-Plugin Assessment

### ✅ ADOPT — `plugins/pbip`

Most relevant plugin. TMDL + PBIR skills, hooks, example library.

#### PBIR references — 21 documents, key gaps

| File | Gap vs our docs | Priority |
|---|---|---|
| `rename-cascade.md` | **Critical gap** — maps ALL 15+ locations updated on rename: TMDL, relationships, DAX expressions (quoted/unquoted), visual.json Entity/queryRef/nativeQueryRef, filter config Entity, bookmark filter snapshots + dataMap key strings, SparklineData metadata, semanticModelDiagramLayout.json nodeIndex, reportExtensions.json, culture files | **H** |
| `pbir-structure.md` | **Missing** — complete directory layout + required field examples for every file type (version.json, report.json, page.json, visual.json, pages.json). Includes critical note: delete reportExtensions.json entirely when empty | **H** |
| `visual-container-formatting.md` | **Missing** — `objects` vs `visualContainerObjects` distinction (schema v2.1-2.2 combined vs v2.4+ split) | **H** |
| `measures-vs-literals.md` | **Missing** — when to use Measure reference vs hardcoded Literal in visual bindings | **H** |
| `page.md` | **Missing** — complete page.json properties, displayOption MUST be string, tooltip/drillthrough page setup, canvas alignment | **M** |
| `filter-pane.md` | **Missing** — all 7 filter types, filter structure, default values, relative date, TopN, compound conditions, configuration options (only visible/expanded allowed at report level in outspacePane) | **M** |
| `sort-visuals.md` | **Missing** — sortDefinition inside query, direction must be capitalized, don't use orderBy | **M** |
| `bookmarks.md` | **Missing** — bookmarks.json + per-id.bookmark.json structure, suppressDisplay/Data/ActiveSection options, paired visibility toggling | **M** |
| `theme.md` | We have `pbir-theme.md` — compare & merge (theirs has jq temp-file pattern, filter pane complete properties table, filterCard `$id` selectors) | **M** |
| `report-extensions.md` | We have `pbir-extension-measures.md` — their version adds visual calculations placeholder pattern | **S** |
| `visual-json.md` | We have `pbir-visual-json.md` — compare & merge (theirs has SparklineData, 6 full field reference patterns with queryRef rules) | **S** |
| `textbox.md` | **Missing** — paragraphs modern array format (NOT expr.Literal.Value), multi-run styling | **S** |
| `annotations.md`, `images.md`, `enumerations.md`, `schemas.md` | **Missing** — base references | **L** |
| `version-json.md`, `platform.md`, `wallpaper.md` | Low priority | **L** |

#### 54 visual examples

`examples/visuals/default/` and `examples/visuals/formatted/` — one JSON per visual type in each variant. We have 6 templates.
New visual types we're missing examples for: bullet chart, divergent bar, lollipop, progress bar, gauge, scatter, waterfall, action button, kpi-flash, smartNarrative, image, textbox, shape — all in default + fully-formatted variants.

#### TMDL skill delta (`plugins/pbip/skills/tmdl/SKILL.md`)

More detailed than our `tmdl-advanced-features.md` in 4 areas:
- `formatStringDefinition` pattern — dynamic format strings via DAX measure
- `PBI_FormatHint` annotation — controls format display in Desktop tooltip
- Complete SpaceParts model example with 8 calculation group items (ours has 4)
- Naming conventions reference (`references/naming-conventions.md`) — SQLBI conventions: singular dims, plural facts, `#` prefix counts, `%` suffix percentages, numbered display folders

#### `rename-cascade.md` — Critical reference we're missing

This is the most operationally valuable document in the entire repo. Every time a table or column is renamed, there are 15+ locations to update. The doc provides exact before/after for each:

- TMDL: file name, `table` declaration, `ref table` in model.tmdl, partition name, relationships files
- DAX: unquoted vs single-quoted name patterns in measure expressions
- visual.json: every `Entity` field, every `queryRef`, every `nativeQueryRef`
- Filter config: `Entity` in all filter types
- Bookmark files: filter snapshot Entity values + `dataMap` key strings (double-escaped)
- SparklineData: both `relatedTable` and `metadata.selector` forms
- semanticModelDiagramLayout.json: `nodeIndex` key
- reportExtensions.json: entity names
- Culture files: `ConceptualEntity` translation keys
- DAX query files

We have zero rename guidance currently. Adopting this immediately prevents agent errors when renaming.

#### Hooks — significant differences

Their `validate-pbir.sh` does more than JSON syntax:

| Check | Their `validate-pbir.sh` | Our `validate_pbir_structure.sh` |
|---|---|---|
| JSON syntax (`jq empty`) | ✅ | ✅ |
| **Folder name spaces** | ✅ (spaces break rendering) | ❌ |
| **Required fields per schema** | ✅ (visual.json needs `$schema`, `name`, `position`+`visual` or `visualGroup`) | ❌ |
| **`$schema` URL format** | ✅ | ❌ |
| **Visual/page name format** | ✅ (word chars + hyphens only) | ❌ |

Their `validate-report-binding.sh` (new to us):

| Check | Their version | Our `validate_pbir_structure.sh` |
|---|---|---|
| `byPath` directory exists | ✅ | ❌ |
| `fab exists` for `byConnection` models | ✅ (configurable via config.yaml) | ❌ |
| Neither reference type present | Blocks agent | ❌ |

Their hook `config.yaml` toggles (8 checks on/off per local environment):
```yaml
json_syntax: true
folder_spaces: true
required_fields: true
schema_url: true
name_format: true
bypath_exists: true
fab_exists: false    # off when fab not installed
tmdl_syntax: true
```

Their `if:` filter syntax for hooks is cleaner than ours:
```json
{"type": "command", "command": "bash validate-pbir.sh", "if": "Edit(**.Report/**)"}
```

We currently fire hooks on all edits and filter internally.

---

### ✅ ADOPT — `plugins/fabric-cli`

#### `fabric-cli/SKILL.md`

Complete fab command reference (49 item types, all flags, DuckDB for querying lakehouse parquet/delta files, DataHub V2 API cross-workspace search). Our CLAUDE.md quickstart matches; their full reference has depth on:
- DuckDB patterns: `delta_scan`, `read_parquet/csv/json` for querying Gold layer data without Fabric connection
- `fab exists` check pattern before operations
- JMESPath patterns for extracting nested IDs
- Admin APIs (`--admin` flag)

#### `fabric-cli/commands/audit-context.md`

Meta-command that evaluates CLAUDE.md/AGENTS.md quality against Anthropic context engineering best practices. References 6 specific Anthropic docs. Worth running on our own CLAUDE.md periodically.

---

### ✅ ADOPT (partial) — `plugins/semantic-models`

#### `refreshing-semantic-model/SKILL.md`

Complete refresh skill (7 refresh types, Enhanced Refresh options, partition-level strategies, large model patterns). Our `fabric-api-core.md` covers basic refresh; this has incremental refresh + hybrid tables patterns we don't document.

#### `pbip-file-types.md`

`.platform` logicalId rules for forking (not currently documented in our codebase). Covers Copilot/ folder specification (removed from MS Learn on 2026-03-25 — preserved here).

---

### ❌ SKIP — `plugins/tabular-editor`

BPA rules, C# scripting, TE2/TE3 CLI. We don't use Tabular Editor.

---

### ❌ SKIP — `plugins/pbi-desktop`

TOM via PowerShell connecting to a running Desktop instance. We're headless-only.

---

### ❌ SKIP (for now) — `plugins/reports` custom visuals

`deneb-visuals`, `svg-visuals`, `python-visuals`, `r-visuals` — out of scope for our generator currently.

---

### ⚠️ NOTE — `pbir-cli`

Their `pbir-cli` skill is built around a **private beta CLI binary** (`pbir` command) from data-goblin/pbir.tools-private-beta. It has 60+ subcommands including `pbir bind`, `pbir validate`, `pbir publish`. We cannot install this. Their documentation references it extensively. The PBIR reference docs are still useful without the CLI.

---

## Hook Gap Summary — What to Add to Our `.claude/settings.json`

Three concrete additions that prevent real errors:

### 1. Folder space check (visual/page folder names)
Spaces in `definition/pages/<PageName>/` or `visuals/<VisualName>/` break rendering silently. Our generator uses speaking names with `_` (correct), but a manual edit could introduce spaces.

### 2. `validate-report-binding.sh` with byPath existence
Checks that `definition.pbir`'s `byPath` resolves to an existing directory. We just fixed a broken byPath in COM-001 — this hook would have caught it immediately.

### 3. Required fields check for `visual.json`
Every `visual.json` must have `$schema`, `name`, and either `position`+`visual` or `position`+`visualGroup`. Our validator catches queryState role errors; it doesn't check structural presence of required fields.

---

## What We Do Better

| Area | Our advantage |
|---|---|
| TMDL hard rules enforcement | Our regex hooks + CLAUDE.md hard rules are equivalently strong to their `tmdl-validate` binary for the 3 critical checks (tabs, `:=`, `description:`) |
| KPI catalog governance | Governed KPI definitions, use case brackets, lineage tracing — entirely absent from their repo |
| Star schema conventions | `TMDL_Allowed_Subset.md` naming/format/RLS policies are more prescriptive than their naming-conventions.md |
| Use case structure | `UseCase_Bracket.yaml` + factsheet system has no equivalent |
| Schema authority | `tooling/ai/schemas/` for YAML validation — their schemas are each skill-local |
| byPath/byConnection docs | Explicitly documented and implemented in `pbip_writer.py` (they document it; we implement it) |

---

## Unchanged: Risk Note

This repo ships with **daily releases and regular renaming**. Copy content locally, track their version number. Do not link raw GitHub URLs in our CLAUDE.md or skill docs.

---

*End of review — full analysis completed 2026-04-04*
