# Review: data-goblin/power-bi-agentic-development

> **Reviewed**: 2026-04-04  
> **Repo**: https://github.com/data-goblin/power-bi-agentic-development  
> **Version at review**: 0.17.1 (daily release cadence — re-check quarterly)  
> **Context**: Assessed for adoption into our PBI Generator and Architecture Generator  

---

## TL;DR

The repo is a **Claude Code plugin marketplace** for Power BI agentic work. It is organised into 6 plugins. Three are irrelevant for us; three have high-value content we are partially missing.

**Adopt immediately (Sprint 2)**: PBIR references directory, visual examples library, `validate-report-binding.sh`  
**Adopt in Sprint 3**: TMDL skill refinements, fab-vs-az-cli guidance  
**Skip**: tabular-editor, pbi-desktop, deneb-visuals, python/r-reviewer agents

---

## Plugin-by-Plugin Assessment

### ✅ ADOPT — `plugins/pbip`

The most relevant plugin. Contains TMDL and PBIR authoring skills, hooks, and a large example library.

#### `plugins/pbip/skills/pbir-format/`

**Status: High value gap in our codebase**

The `references/` subfolder has 21 PBIR specification documents we don't have locally:

| File | Gap vs our docs | Priority |
|---|---|---|
| `visual-json.md` | We have `pbir-visual-json.md` — compare & merge | M |
| `theme.md` | We have `pbir-theme.md` — compare & merge | M |
| `report-extensions.md` | We have `pbir-extension-measures.md` — compare & merge | M |
| `pbir-structure.md` | **Missing** — report folder layout spec | H |
| `visual-container-formatting.md` | **Missing** — card/container header styling | H |
| `measures-vs-literals.md` | **Missing** — when to use measures vs hardcoded literals in bindings | H |
| `rename-patterns.md` | **Missing** — how to rename tables/columns without breaking visuals | H |
| `bookmarks.md` | **Missing** — conditional bookmarks for UX patterns | M |
| `filter-pane.md` | **Missing** — filter pane config (we suppress filters in report.json) | M |
| `sort-visuals.md` | **Missing** — sorting by measure/column | M |
| `annotations.md` | **Missing** | L |
| `images.md` | **Missing** | L |
| `page.md` | **Missing** — page-level properties (canvas size, display settings) | M |
| `platform.md` | **Missing** — .platform files | L |
| `enumerations.md` | **Missing** — enum values for visual properties | M |
| `schemas.md` | **Missing** — JSON schema references | L |
| `version-json.md` | We already write version.json correctly | - |
| `wallpaper.md` | **Missing** — wallpaper/background image | L |
| `textbox.md` | **Missing** — text box visual config | L |

**Also in this plugin:**
- `examples/visuals/` — 54 `visual.json` examples (default + formatted variants)
  - We currently have 6 visual templates in our page scaffold generator
  - This library covers: barChart, columnChart, lineChart, areaChart, scatter, waterfall, gauge, KPI, card, multiRowCard, tableEx (matrix), slicer, actionButton, kpi-flash, smartNarrative, shape, image, textbox — with default and fully-formatted versions each
  - **Adoption**: Add as reference examples to `products/fabric/powerbi/tooling/page_scaffold_generator/examples/`

#### `plugins/pbip/skills/tmdl/SKILL.md`

**Status: More detailed than our `tmdl-advanced-features.md` in a few areas**

Additions worth merging into our docs:
- DAX indentation depth table (measures: 1 level; complex expressions: 4-space per TMDL standard)
- `PBI_FormatHint` annotation behavior and `formatStringDefinition` pattern for measures
- Complete `SpaceParts.SemanticModel` example with 8 calculation group items (ours has 4)
- `_Measures` table as calculated table — exact TMDL syntax we don't have documented

These are targeted additions to `tmdl-advanced-features.md`, not a replacement.

#### `plugins/pbip/hooks/`

**Status: Better architecture than our current hooks**

They use `config.yaml` to toggle individual checks:
```yaml
fab_exists: false        # Skip fab-dependent validation when running locally
validate_bindings: true  # Enable/disable validate-report-binding.sh
```

Our current hooks (`.claude/settings.json`) have no toggle mechanism.

**Most relevant hook we're missing: `validate-report-binding.sh`**
- Validates that `definition.pbir` references point to an existing semantic model
- Especially relevant now that we added `byConnection` support — can catch broken/missing `dataset_id`
- Pattern: check that `pbiModelDatabaseName` in `definition.pbir` is a non-empty GUID when `byConnection` is used

---

### ✅ ADOPT — `plugins/fabric-cli`

**Status: Directly addresses our GAP-3 (fab vs az rest uncertainty)**

Contains `fab-vs-az-cli.md` decision guide:
- When to use `fab` (Fabric data plane: workspaces, items, notebooks, pipelines)
- When to use `az` (Azure control plane: capacity, networking, RBAC, resource provisioning)
- When to use `az rest` directly (LRO monitoring, advanced item operations not wrapped by fab)

Adoption: Merge key decision matrix into our `fabric-api-core.md` or as a standalone reference.

Also contains `fabric-cli.md` with `fab` command reference — we have some of this in CLAUDE.md already, but their version may be more complete.

---

### ✅ ADOPT — `plugins/semantic-models` (partial)

**Status: Python scripts worth evaluating**

Contains `create_direct_lake_model.py` — a ready Python script for Direct Lake model creation. This directly supports Sprint 2 task `PBI 1.2` (Direct Lake generation). Worth reviewing before building our own.

The `reports` plugin under semantic-models has report-rebinding patterns (`convert-legacy-to-pbir.md`) and PBIR schema patterns — relevant for our migration scenarios.

---

### ❌ SKIP — `plugins/tabular-editor`

We don't use Tabular Editor. All four subfolders (`bpa-rules`, `c-sharp-scripting`, `te-docs`, `te2-cli`) are irrelevant.

---

### ❌ SKIP — `plugins/pbi-desktop`

We work headless (PBIP files via fab CLI). The `connect-pbid` and Desktop integration patterns assume a running Desktop instance — not applicable.

---

### ❌ SKIP — `plugins/reports` (agent patterns)

`python-reviewer`, `r-reviewer`, `deneb-visuals` agents — outside our scope. Deneb (Vega-Lite) visuals are custom visuals not supported by our generator.

---

## Priority Adoption Backlog

### Sprint 2 additions (concrete, high value)

| Item | Action | Target File | Effort |
|---|---|---|---|
| `pbir-structure.md` | Adopt as-is or merge content | `products/fabric/powerbi/docs/references/pbir-structure.md` | S |
| `visual-container-formatting.md` | Adopt as-is | `products/fabric/powerbi/docs/references/` | S |
| `measures-vs-literals.md` | Adopt as-is | `products/fabric/powerbi/docs/references/` | S |
| `rename-patterns.md` | Adopt as-is | `products/fabric/powerbi/docs/references/` | S |
| 54 visual examples | Copy to our examples folder | `products/fabric/powerbi/tooling/page_scaffold_generator/examples/visuals/` | M |
| `validate-report-binding.sh` | Adapt + add to `.claude/settings.json` | `.claude/hooks/validate-report-binding.sh` | S |
| `fab-vs-az-cli.md` | Merge decision matrix into `fabric-api-core.md` | existing file | S |

### Sprint 3 additions (lower urgency)

| Item | Action | Effort |
|---|---|---|
| `tmdl/SKILL.md` delta | Merge additional TMDL syntax patterns into `tmdl-advanced-features.md` | S |
| `config.yaml` hook toggle | Refactor our hooks to support optional checks | M |
| `bookmarks.md`, `filter-pane.md`, `sort-visuals.md` | Add to references | S |
| `create_direct_lake_model.py` | Evaluate vs Sprint 2 PBI 1.2 implementation | M |

---

## What This Repo Does Better Than Us

| Area | Their approach | Our current state |
|---|---|---|
| Visual example library | 54 examples (default + formatted per visual type) | 6 templates |
| PBIR structure spec | Dedicated `pbir-structure.md` with folder layout | Scattered in `fabric-api-core.md` |
| Hook configurability | `config.yaml` toggles per check | Hardcoded in `settings.json` |
| Report binding validation | `validate-report-binding.sh` | Not implemented |
| Decision guidance (fab vs az) | Dedicated `fab-vs-az-cli.md` | Only in CLAUDE.md quick reference |
| Visual container formatting | Dedicated reference | Missing entirely |
| Rename patterns | Dedicated reference | Missing entirely |

## What We Do Better

| Area | Our advantage |
|---|---|
| Domain-specific TMDL conventions | Our `TMDL_Allowed_Subset.md` + naming/format rules are more prescriptive |
| Calculation group templates | Our page scaffold generator generates time-intelligence groups end-to-end |
| `byConnection` / `byPath` docs | Explicitly documented and implemented in `pbip_writer.py` |
| KPI catalog integration | Our generator links reports to governed KPI definitions |
| Use case structure | Star schema + 3-30-300 page templates are domain-specific |

---

## Risk Note

This repo ships with **daily releases and regular renaming**. Do not pin direct URLs from their raw GitHub files in our CLAUDE.md or skill docs — copy the content locally and track the version. Review quarterly for relevant changes.

---

*End of review*
