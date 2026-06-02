# Report Engine — Gap Analysis & Target Architecture

> **Status:** Authoritative  
> **Authority:** `PAGE_TEMPLATE_DOCTRINE.md` · `PAGE_TYPE_TAXONOMY.md` · `VISUAL_BAUKASTEN.md`  
> **Phase:** 4 — Engine Gap Analysis & Zielarchitektur

---

## 1. Current State Inventory

### 1.1 Studio Preview (TypeScript / React)

| File | Role | State |
|---|---|---|
| `studio/src/components/templates/report-templates-gallery.tsx` | Template gallery with design/production toggle | Hardcoded `TEMPLATES` array; not driven by manifest |
| `studio/src/components/templates/page-template-preview.tsx` | Per-template preview renderer | Hardcoded `TEMPLATE_META` and KPI data; visual components are fixed per template |
| `studio/src/components/dashboard/` | Dashboard sub-components (`PulseCard`, `Investigator`, `ActionMatrix`) | Well-structured but coupled to hardcoded sample data |
| `studio/src/lib/dashboard/sample-data.ts` | Sample data for previews | Static, not derived from use case or template manifest |

**Critical gap:** The Studio preview is a *demo screen*. It does not consume the template manifest, slot definitions, or visual registry. Changing a template definition requires a code edit, not a data change.

### 1.2 Core Template Authority

| File | Role | State |
|---|---|---|
| `core/templates/page_templates/page_types/T1-T4.md` | Page type contracts | Strong — decision question, slots, narrative arc, DoD |
| `core/templates/page_templates/governance/Slot_Definitions.md` | Slot semantic definitions | Strong — 9 slots with purpose and allowed templates |
| `core/templates/page_templates/governance/Visual_Whitelist.md` | Visual permission rules | Good — but lacks information block contracts and binding specs |
| `core/templates/page_templates/grid_templates/*.json` | Grid layout templates | Exists — 6 files; mixes absolute and grid coordinates; lacks page_type mapping |
| `core/templates/page_templates/visual_templates/*.json` | Visual config defaults | Thin — 6 files; missing allowed_visuals, forbidden_visuals, required_inputs, quality_rules |
| `core/templates/page_templates/Design_Spec_3_30_300.md` | Full design specification | Strong — references sources, defines grid, canvas, typography |
| `core/templates/page_templates/template_manifest.yaml` | **Single source of truth** | **Does not exist** — this is the primary gap |
| `core/templates/page_templates/visual_registry.yaml` | Machine-readable visual contracts | **Does not exist** |

### 1.3 IR-Based Generator (tool-agnostic)

| File | Role | State |
|---|---|---|
| `tooling/generator_core/ir/specs.py` | IR data classes: `DashboardSpec`, `PageSpec`, `VisualSpec` | Strong — `PageType`, `VisualType`, `PageRole` enums defined |
| `tooling/generator_core/ir/compiler.py` | Compiles IR from use case bracket | Exists; unclear if it reads from template_manifest |

**Gap:** The IR compiler likely reads from `UseCase_Bracket.yaml` directly without validating against a template manifest. This means page type constraints (allowed slots, forbidden visuals) are not enforced at compile time.

### 1.4 Fabric PBIP Generator

| File | Role | State |
|---|---|---|
| `products/fabric/powerbi/tooling/page_scaffold_generator/scaffold_generator.py` | Orchestrates PBIP generation from config | Exists; reads config via `ConfigLoader` |
| `products/fabric/powerbi/tooling/page_scaffold_generator/config_loader.py` | Loads per-use-case config | Exists; source files for config unclear — may bypass template manifest |
| `products/fabric/powerbi/tooling/page_scaffold_generator/visual_builder.py` | Builds PBIP visual JSON | Exists; visual type selection logic unclear |
| `products/fabric/powerbi/tooling/page_scaffold_generator/visual_validator.py` | Validates generated visuals | Exists; validation rules unclear — may not cross-check with Visual Whitelist |
| `products/fabric/powerbi/tooling/page_scaffold_generator/grid_calculator.py` | Computes pixel positions from grid | Exists |
| `products/fabric/powerbi/tooling/page_scaffold_generator/action_panel.py` | Generates action panel content | Exists — separate from main visual_builder |

**Gap:** The scaffold generator and the IR generator are **two separate paths** that may diverge. If the template manifest does not govern both, they will produce inconsistent output.

---

## 2. Gap Summary

| Gap | Severity | Impact |
|---|---|---|
| No `template_manifest.yaml` as single source of truth | **Critical** | Templates are defined in Markdown prose; not machine-consumable; Studio and Fabric generators operate independently |
| No `visual_registry.yaml` with information block contracts | **Critical** | Visual selection not enforced; substitutions not governed; quality rules not checkable by automation |
| Studio preview hardcoded, not manifest-driven | **High** | Template changes require code edits; preview cannot reflect actual template contracts |
| Grid templates lack page_type mapping | **High** | Generator must guess which grid template to use for each page type variant |
| Visual templates too thin (6 files, no contracts) | **High** | `visual_builder.py` cannot validate allowed/forbidden visuals per slot without richer template data |
| IR compiler may not validate against template manifest | **Medium** | T2 page could compile with T3 visual types without an error |
| Two generator paths (IR + scaffold_generator) may diverge | **Medium** | Studio preview and PBIP output could differ for the same use case |
| Schema drift between `tooling/generator/schemas` and `studio/src/lib/schemas` | **Medium** | TypeScript types and Python schemas may diverge over time |

---

## 3. Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SINGLE SOURCE OF TRUTH                               │
│                                                                               │
│   PAGE_TEMPLATE_DOCTRINE.md  ──►  template_manifest.yaml                    │
│   VISUAL_BAUKASTEN.md        ──►  visual_registry.yaml                      │
│   Slot_Definitions.md        ──►  (embedded in template_manifest)            │
│   Visual_Whitelist.md        ──►  (embedded in visual_registry)              │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                      ┌─────────────▼──────────────┐
                      │      TEMPLATE COMPILER       │
                      │   (tooling/generator_core)   │
                      │                              │
                      │  Input:                      │
                      │   UseCase_Bracket.yaml       │
                      │   + template_manifest.yaml   │
                      │   + visual_registry.yaml     │
                      │                              │
                      │  Output:                     │
                      │   DashboardSpec (IR)         │
                      │   + validation report        │
                      └──────┬────────────┬──────────┘
                             │            │
              ┌──────────────▼──┐    ┌────▼──────────────────┐
              │  STUDIO RENDERER │    │   FABRIC PBIP GENERATOR│
              │  (Next.js)       │    │   (Python)             │
              │                  │    │                        │
              │  PageTemplate    │    │  scaffold_generator.py │
              │  Preview         │    │  visual_builder.py     │
              │  (manifest-based)│    │  (manifest-constrained)│
              └──────────────────┘    └────────────────────────┘
                             │            │
                    ┌────────▼────────────▼──────────┐
                    │     VALIDATION GATES            │
                    │                                 │
                    │  - Visual allowed in slot?      │
                    │  - Required inputs bound?       │
                    │  - Quality rules satisfied?     │
                    │  - IBCS notation correct?       │
                    │  - Page type contract respected?│
                    └─────────────────────────────────┘
```

### Architecture Principles

1. **One source of truth.** `template_manifest.yaml` and `visual_registry.yaml` are the canonical runtime references. Markdown docs are the *reasoning* behind the YAML; YAML is the *executable contract*.

2. **Both renderers consume the same manifest.** Studio preview and PBIP generator must read from identical sources. Any divergence is a bug.

3. **Validation at compile time, not at runtime.** The IR compiler validates: (a) page type exists, (b) slots are allowed for that page type, (c) visuals are in the allowed list for each slot's information block, (d) required bindings are declared.

4. **Fallback principle.** Existing Fabric generator paths remain operational until the manifest-based path is validated on the pilot use case (COM-002). No breaking changes to current generator until pilot passes.

---

## 4. Implementation Sequence (Stream-by-Stream)

### Stream A — Contracts (Done: Phase 1–3)

- [x] `PAGE_TEMPLATE_DOCTRINE.md` — source-backed rules
- [x] `PAGE_TYPE_TAXONOMY.md` — T1–T4 + variants
- [x] `VISUAL_BAUKASTEN.md` — information block contracts

### Stream B — Registry & Schema

- [ ] `core/templates/page_templates/template_manifest.yaml` — machine-readable page type + variant + slot + grid template mapping
- [ ] `core/templates/page_templates/visual_registry.yaml` — machine-readable information block contracts
- [ ] Extend `tooling/generator/schemas/` with JSON Schema for `template_manifest` and `visual_registry`
- [ ] Align `studio/src/lib/schemas/` TypeScript types with Python IR specs

### Stream C — Studio Preview

- [ ] Add `useManifest` flag to `ReportTemplatesGallery` (keep hardcoded path as fallback)
- [ ] Create `studio/src/lib/studio/template-manifest-loader.ts` to read `template_manifest.yaml` and `visual_registry.yaml`
- [ ] Replace hardcoded `TEMPLATE_META` in `page-template-preview.tsx` with manifest-driven data
- [ ] `PageTemplatePreview` renders slot placeholders with allowed visual types from registry
- [ ] Sample data remains for preview purposes but is tagged as `preview_sample`, not confused with real data

### Stream D — Fabric Generator

- [ ] Add manifest validation step to `scaffold_generator.py` before PBIP write
- [ ] `config_loader.py` reads `template_manifest.yaml` for slot definitions
- [ ] `visual_builder.py` checks selected visual type against `visual_registry.yaml` allowed list
- [ ] `visual_validator.py` extended to run quality rules from the registry

### Stream E — Validation Gates

- [ ] CI gate: `template_manifest.yaml` is valid JSON/YAML (schema check)
- [ ] CI gate: Every use case variant in `UseCase_Bracket.yaml` maps to a valid template_manifest entry
- [ ] CI gate: Every visual in a generated PBIP is in the visual_registry allowed list for its slot
- [ ] CI gate: Waterfall bars reconcile (sum of drivers = actual − reference) — added to `visual_validator.py`

---

## 5. Pilot: COM-002

The first use case to run through the manifest-based path is **COM-002**, selected because:
- It requires T2 (variance) + T4 (prescriptive) — the most distinct page type combination
- It has an existing Action Code that can populate the T4 Action Panel
- Variance analysis (waterfall) is the most complex block to validate correctly
- Success on COM-002 provides high confidence for scaling

Pilot Definition of Done:
- Studio Preview renders COM-002 from manifest (not from hardcoded sample data)
- PBIP is generated with visual selection validated against registry
- Waterfall bars reconcile in the generated PBIP
- T4 Action Panel populated from Action Code YAML

---

## 6. Schema Drift Register

| Schema Location | Purpose | Drift Risk | Action |
|---|---|---|---|
| `tooling/generator/schemas/usecase_bracket.schema.json` | Validates `UseCase_Bracket.yaml` | Medium — bracket evolves | Add `ux_layout_rules.template_variant` field |
| `tooling/generator/schemas/layout_330300.schema.json` | Layout config schema | Low | Extend with `information_block` field per slot |
| `studio/src/lib/schemas/usecase-bracket.ts` | TypeScript mirror of bracket schema | High — manually maintained | Generate from JSON Schema using `json-schema-to-ts` |
| `tooling/generator_core/ir/specs.py` | Python IR data classes | Medium | Ensure `VisualType` enum matches `visual_registry.yaml` keys |

---

## 7. Definition of Done

- [ ] `template_manifest.yaml` exists and is valid against its schema
- [ ] `visual_registry.yaml` exists and is valid against its schema
- [ ] Studio Preview reads from manifest for at least COM-002
- [ ] PBIP generator validates visual selection against registry for COM-002
- [ ] CI gate rejects a bracket that references a non-existent template variant
- [ ] CI gate rejects a generated PBIP with a forbidden visual in any slot
- [ ] Schema drift between Python IR and TypeScript types is documented and tracked
